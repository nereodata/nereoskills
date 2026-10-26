"""Calidad del delta de una tarea, independiente de la suite de versión."""

import argparse
import base64
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

try:
    import yaml
except ImportError:
    from adevv import yaml_lite as yaml


JS = {'.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx'}
EXTENSIONES = {
    'eslint': JS,
    'prettier': JS | {'.json', '.css', '.scss', '.html', '.md', '.yaml', '.yml'},
    'ruff': {'.py', '.pyi'},
}


def _git(root, *args):
    """Consulta Git conservando nombres Unicode y separadores NUL."""
    proceso = subprocess.run(['git', *args], cwd=root, capture_output=True)
    if proceso.returncode:
        raise ValueError('No se puede calcular el delta por la base Git: ' +
                         proceso.stderr.decode('utf-8', errors='replace').strip())
    return proceso.stdout.decode('utf-8', errors='surrogateescape')


def delta(root, base):
    """Devuelve la base estable resuelta y los ficheros existentes del delta."""
    if not isinstance(base, str) or not base.strip():
        raise ValueError('Falta una base Git estable')
    sha = _git(root, 'rev-parse', '--verify', '--end-of-options', base + '^{commit}').strip()
    cambiados = _git(root, 'diff', '--name-only', '-z', '--no-renames', sha, '--').split('\0')
    nuevos = _git(root, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')
    ficheros = sorted({nombre for nombre in cambiados + nuevos if nombre and (root / nombre).is_file()})
    return sha, ficheros


def _expandir(comando, ficheros, clave):
    """Expande solo argumentos completos; ningún nombre de fichero llega al shell."""
    if '{ficheros}' not in comando:
        return comando
    try:
        argumentos = shlex.split(comando)
    except ValueError as error:
        raise ValueError(f'validation.{clave}: {error}') from error
    if any('{ficheros}' in arg and arg != '{ficheros}' for arg in argumentos):
        raise ValueError(f'validation.{clave}: {{ficheros}} debe ser un argumento completo')
    if any(arg in ('&&', '||', '|', ';', '>', '>>', '<', '&') for arg in argumentos):
        raise ValueError(f'validation.{clave}: no se admite shell con {{ficheros}}')
    if not argumentos or argumentos[0] == '{ficheros}':
        raise ValueError(f'validation.{clave}: falta el ejecutable')
    objetivos = ['./' + f if f.startswith('-') else f for f in ficheros]
    return [valor for arg in argumentos for valor in (objetivos if arg == '{ficheros}' else [arg])]


def _manifiestos(root):
    """Lee solo manifiestos conocidos; un documento no reconocible no deduce comandos."""
    scripts, ruff, motivos = {}, False, []
    paquete = root / 'package.json'
    proyecto = root / 'pyproject.toml'
    if paquete.exists():
        try:
            datos = json.loads(paquete.read_text(encoding='utf-8'))
            scripts = datos.get('scripts', {}) if isinstance(datos, dict) else {}
            if not isinstance(scripts, dict):
                scripts = {}
        except (ValueError, OSError) as error:
            motivos.append(f'package.json no reconocible: {error}')
    if proyecto.exists():
        try:
            datos = tomllib.loads(proyecto.read_text(encoding='utf-8'))
            ruff = isinstance(datos.get('tool'), dict) and isinstance(datos['tool'].get('ruff'), dict)
        except (ValueError, OSError) as error:
            motivos.append(f'pyproject.toml no reconocible: {error}')
    return scripts, ruff, motivos


def _deducir(etapa, scripts, ruff):
    """Deducción por etapa limitada a las formas aprobadas, sin wrappers."""
    script = scripts.get('format:check' if etapa == 'formato' else 'lint')
    esperado = ['prettier', '--check', '.'] if etapa == 'formato' else ['eslint', '.']
    try:
        reconocido = isinstance(script, str) and shlex.split(script) == esperado
    except ValueError:
        reconocido = False
    if reconocido:
        return esperado[:-1], (['prettier', '--write'] if etapa == 'formato' else None), esperado[0], ''
    if ruff:
        return (['ruff', 'format', '--check'] if etapa == 'formato' else ['ruff', 'check'],
                ['ruff', 'format'] if etapa == 'formato' else None, 'ruff', '')
    return None, None, None, ('script no reconocible' if script is not None else 'ausencia de herramientas')


def resolver(root, validation, ficheros):
    """Resuelve formato y lint con precedencia explícita y deducción conservadora."""
    if not isinstance(validation, dict):
        raise ValueError('validation debe ser un mapa de configuración')
    for clave in ('formato', 'lint', 'formato_escritura'):
        if clave in validation and (not isinstance(validation[clave], str) or not validation[clave].strip()):
            raise ValueError(f'validation.{clave} debe ser una cadena no vacía')
    scripts, ruff, motivos = _manifiestos(root)
    plan = {}
    for etapa in ('formato', 'lint'):
        fila = {'comando': None, 'escritura': None, 'motivo': '', 'aviso': '', 'herramienta': None}
        plan[etapa] = fila
        if etapa in validation:
            comando = _expandir(validation[etapa], ficheros, etapa)
            escritura = (_expandir(validation['formato_escritura'], ficheros, 'formato_escritura')
                         if etapa == 'formato' and 'formato_escritura' in validation else None)
            if not ficheros:
                fila['motivo'] = 'sin objetivos compatibles'
                continue
            fila.update(comando=comando, escritura=escritura)
            if isinstance(comando, str):
                fila['aviso'] = 'alcance explícito declarado, sin limitar por ficheros'
            if isinstance(escritura, str):
                fila['aviso'] += '; escritura con alcance explícito declarado, sin limitar por ficheros'
            continue
        comando, escritura, herramienta, motivo = _deducir(etapa, scripts, ruff)
        if comando is None:
            fila['motivo'] = '; '.join([motivo, *motivos])
            continue
        objetivos = [('./' + f if f.startswith('-') else f) for f in ficheros
                     if Path(f).suffix.lower() in EXTENSIONES[herramienta]]
        if not objetivos:
            fila['motivo'] = 'sin objetivos compatibles'
            continue
        fila.update(comando=comando + objetivos, escritura=escritura + objetivos if escritura else None,
                    herramienta=herramienta)
        if etapa == 'formato' and 'formato_escritura' in validation:
            fila['escritura'] = _expandir(validation['formato_escritura'], ficheros, 'formato_escritura')
            if isinstance(fila['escritura'], str):
                fila['aviso'] = 'escritura con alcance explícito declarado, sin limitar por ficheros'
    return plan


def _config(root):
    """Lee la configuración usando el mismo parser disponible para el motor."""
    fichero = root / 'task_config.yaml'
    if not fichero.exists():
        return {}
    if hasattr(yaml, 'safe_load'):
        cfg = yaml.safe_load(fichero.read_text(encoding='utf-8'))
    else:
        cfg = yaml.load_yaml(fichero)
    if cfg is None:
        return {}
    if not isinstance(cfg, dict):
        raise ValueError('task_config.yaml debe ser un mapa')
    validation = cfg.get('validation', {})
    return {} if validation is None else validation


def _lanzar(root, comando, herramienta=None):
    """Ejecuta argumentos sin shell; los comandos explícitos globales conservan su shell."""
    try:
        if isinstance(comando, str):
            return subprocess.run(comando, cwd=root, shell=True).returncode
        argumentos = list(comando)
        if herramienta in ('prettier', 'eslint'):
            candidatos = ([root / 'node_modules/prettier/bin/prettier.cjs',
                           root / 'node_modules/prettier/bin/prettier.mjs',
                           root / 'node_modules/prettier/bin-prettier.js'] if herramienta == 'prettier'
                          else [root / 'node_modules/eslint/bin/eslint.js'])
            local = next((p for p in candidatos if p.is_file()), None)
            if local:
                argumentos = ['node', str(local), *argumentos[1:]]
        ejecutable = shutil.which(argumentos[0])
        if os.name == 'nt' and ejecutable and Path(ejecutable).suffix.lower() in ('.cmd', '.bat'):
            raise ValueError('Se requiere un ejecutable sin shell para preservar los argumentos; '
                             'declara node con su script o instala el paquete local')
        return subprocess.run(argumentos, cwd=root, shell=False).returncode
    except (OSError, ValueError) as error:
        print(f'[calidad] fallo de comando: {error}', flush=True)
        return 1


def _almacen(root):
    """Localiza las cargas útiles fuera del árbol observado, también en worktrees."""
    return Path(_git(root, 'rev-parse', '--absolute-git-dir').strip()) / 'adevv-calidad'


def _comando_verificable(root, sha, ficheros, etapa, fila):
    """Guarda los argumentos por hash y mantiene corta la orden del verificador."""
    datos = {'base': sha, 'ficheros': ficheros, 'etapa': etapa,
             'comando': fila['comando'], 'herramienta': fila['herramienta']}
    payload = json.dumps(datos, ensure_ascii=True).encode('utf-8')
    identidad = hashlib.sha256(payload).hexdigest()
    almacen = _almacen(root)
    almacen.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=almacen, delete=False) as temporal:
        ruta_temporal = Path(temporal.name)
        temporal.write(payload)
    try:
        os.replace(ruta_temporal, almacen / (identidad + '.json'))
    finally:
        ruta_temporal.unlink(missing_ok=True)
    ruta = base64.b64encode(str(Path(__file__).resolve()).encode('utf-8')).decode()
    codigo = f"import base64,runpy;runpy.run_path(base64.b64decode('{ruta}').decode('utf-8'),run_name='__main__')"
    args = [sys.executable, '-c', codigo, '--ejecutar', identidad]
    return subprocess.list2cmdline(args) if os.name == 'nt' else shlex.join(args)


def ejecutar(root, base, aplicar, verificar):
    """Aplica escritura opcional y verifica ambas etapas sobre el árbol resultante."""
    try:
        sha, ficheros = delta(root, base)
        plan = resolver(root, _config(root), ficheros)
        codigo = 0
        if aplicar and plan['formato']['escritura']:
            fila = plan['formato']
            if fila['aviso']:
                print(f"[calidad] {fila['aviso']}", flush=True)
            codigo = _lanzar(root, fila['escritura'], fila['herramienta'])
            sha, ficheros = delta(root, sha)
            plan = resolver(root, _config(root), ficheros)
        for etapa, fila in plan.items():
            if fila['comando'] is None:
                print(f"[calidad] {etapa} omitido: {fila['motivo']}", flush=True)
                continue
            if fila['aviso']:
                print(f"[calidad] {etapa}: {fila['aviso']}", flush=True)
            resultado = verificar(root, _comando_verificable(root, sha, ficheros, etapa, fila))
            if resultado:
                print(f'[calidad] fallo de {etapa}; no se permite completed', flush=True)
                codigo = resultado
        return codigo
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'[calidad] error: {error}; no se permite completed', flush=True)
        return 1


def main():
    """Ejecuta la carga útil identificada por hash sin interpolar sus argumentos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ejecutar', required=True)
    args = parser.parse_args()
    identidad = args.ejecutar
    if len(identidad) != 64 or any(c not in '0123456789abcdef' for c in identidad):
        parser.error('identidad de calidad inválida')
    payload = (_almacen(Path.cwd()) / (identidad + '.json')).read_bytes()
    if hashlib.sha256(payload).hexdigest() != identidad:
        parser.error('carga útil de calidad alterada')
    datos = json.loads(payload)
    return _lanzar(Path.cwd(), datos['comando'], datos['herramienta'])


if __name__ == '__main__':
    sys.exit(main())
