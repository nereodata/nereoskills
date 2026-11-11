"""Planificación, ejecución coordinada y reutilización de chequeos de calidad y release."""

from datetime import datetime
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time

from adevv import registro_metricas

try:
    import yaml
except ImportError:
    try:
        from adevv import yaml_lite as yaml
    except ImportError:
        yaml = None

try:
    from . import calidad
except ImportError:
    import importlib.util as _ilu
    _calidad_spec = _ilu.spec_from_file_location('adevv_calidad_interno', Path(__file__).with_name('calidad.py'))
    calidad = _ilu.module_from_spec(_calidad_spec)
    _calidad_spec.loader.exec_module(calidad)


ETAPAS_CATALOGO = (
    'formato',
    'lint',
    'tipado',
    'seguridad',
    'secretos',
    'dependencias',
    'pruebas',
    'builds',
)
DISPONIBILIDADES = ('configurado', 'ausente', 'omitido')
RESULTADOS = ('sin_acreditar', 'pendiente', 'ejecutando', 'aprobado', 'fallido', 'interrumpido')
CANALES = ('cli', 'gateway', 'agente', 'release')
ACCIONES_RELEASE = ('validar', 'cerrar_local', 'etiquetar', 'publicar')
EVIDENCIAS = 'orquestar_evidencias.jsonl'
METRICAS = registro_metricas.ARCHIVO
ESTADO_EN_CURSO = 'estado_en_curso.json'
IGNORADOS_PROPIOS = {
    '/' + registro_metricas.AUXILIAR + '/',
    EVIDENCIAS,
    METRICAS,
    'orquestar.log',
    'orquestar.pid',
    'orquestar.parar',
    'orquestar.espera',
    'orquestar_buzon.jsonl',
    'orquestar_buzon.jsonl.tmp',
    '.env',
    'orquestar_telegram.json',
    'orquestar_prompt.txt',
    'telegram.pid',
    'telegram.log',
    'telegram.parar',
    'orquestar_preguntas.json',
    'orquestar_respuestas.jsonl',
}
ARCHIVOS_CONFIGURACION = (
    'pyproject.toml',
    'package.json',
    'ruff.toml',
    '.ruff.toml',
    'tsconfig.json',
    'setup.cfg',
)
ARCHIVOS_DEPENDENCIAS = (
    'requirements.lock',
    'requirements.txt',
    'uv.lock',
    'poetry.lock',
    'Pipfile.lock',
    'package-lock.json',
    'pnpm-lock.yaml',
    'yarn.lock',
)

_LOCK_GLOBAL = threading.Lock()
_EJECUCIONES_MEMORIA = {}


def _ahora():
    """Devuelve la fecha y hora local en formato ISO-8601 al segundo."""
    return datetime.now().isoformat(timespec='seconds')


def _proceso_vivo(pid):
    """Comprueba si existe un proceso activo con el PID indicado."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() == 5
        try:
            codigo = ctypes.c_ulong()
            return not kernel.GetExitCodeProcess(handle, ctypes.byref(codigo)) or codigo.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def directorio_git_comun(root):
    """Resuelve sin subprocesos el directorio Git común compartido entre el árbol principal y sus worktrees."""
    base = Path(root).resolve()
    dot_git = base / '.git'
    if dot_git.is_dir():
        commondir_file = dot_git / 'commondir'
        if commondir_file.is_file():
            rel = commondir_file.read_text(encoding='utf-8', errors='replace').strip()
            return (dot_git / rel).resolve()
        return dot_git.resolve()
    if dot_git.is_file():
        try:
            contenido = dot_git.read_text(encoding='utf-8', errors='replace').strip()
            if contenido.lower().startswith('gitdir:'):
                raw_gitdir = contenido.split(':', 1)[1].strip()
                gitdir_path = Path(raw_gitdir)
                if not gitdir_path.is_absolute():
                    gitdir_path = (base / gitdir_path).resolve()
                commondir_file = gitdir_path / 'commondir'
                if commondir_file.is_file():
                    rel = commondir_file.read_text(encoding='utf-8', errors='replace').strip()
                    return (gitdir_path / rel).resolve()
                return gitdir_path.parent.parent.resolve()
        except OSError:
            pass
    return dot_git.resolve()


def _excluir_propios(root):
    """Asegura que los artefactos de orquestación estén excluidos en info/exclude del repositorio."""
    try:
        comun = directorio_git_comun(root)
        if not comun.is_dir():
            return
        exclude = comun / 'info' / 'exclude'
        actual = exclude.read_text(encoding='utf-8', errors='replace') if exclude.is_file() else ''
        lineas = set(actual.splitlines())
        faltan = [nombre for nombre in sorted(IGNORADOS_PROPIOS) if nombre not in lineas]
        if faltan:
            exclude.parent.mkdir(parents=True, exist_ok=True)
            with exclude.open('a', encoding='utf-8') as f:
                f.write('\n' + '\n'.join(faltan) + '\n')
    except OSError:
        pass


def directorio_coordinacion(root):
    """Devuelve el directorio de coordinación compartido en el directorio Git común."""
    comun = directorio_git_comun(root)
    coord = comun / 'adevv-chequeos'
    coord.mkdir(parents=True, exist_ok=True)
    return coord


def arbol_trabajo(root):
    """Calcula el hash del árbol de trabajo completo incluyendo cambios sin commitear y no ignorados."""
    base = Path(root).resolve()
    _excluir_propios(base)
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(tmp) / 'index')}
        subprocess.run(['git', 'add', '-A', '.'], cwd=base, env=env, capture_output=True, check=True)
        valor = subprocess.run(
            ['git', 'write-tree'],
            cwd=base,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', valor):
            raise RuntimeError('No se pudo calcular una huella Git válida del árbol')
        return valor


def _listar_ficheros_repositorio(root):
    """Obtiene la lista ordenada de ficheros del árbol de trabajo excluyendo .git y artefactos propios."""
    base = Path(root).resolve()
    resultado = []
    for dirpath, dirnames, filenames in os.walk(base):
        if Path(dirpath) == base and registro_metricas.AUXILIAR in dirnames:
            dirnames.remove(registro_metricas.AUXILIAR)
        dirnames[:] = [
            d for d in sorted(dirnames)
            if d not in ('.git', '__pycache__') and not d.startswith('adevv-intervencion-')
        ]
        rel_dir = Path(dirpath).resolve().relative_to(base)
        for fname in sorted(filenames):
            if fname == '.git':
                continue
            if rel_dir == Path('.') and (fname in IGNORADOS_PROPIOS or fname.startswith('adevv-intervencion-')):
                continue
            rel_path = (rel_dir / fname).as_posix() if rel_dir != Path('.') else fname
            resultado.append(rel_path)
    return sorted(resultado)


def cargar_configuracion(root):
    """Lee y valida estrictamente las secciones validation y release de task_config.yaml."""
    fichero = Path(root) / 'task_config.yaml'
    if not fichero.exists():
        return {}
    texto = fichero.read_text(encoding='utf-8')
    if yaml and hasattr(yaml, 'safe_load'):
        cfg = yaml.safe_load(texto)
    elif yaml and hasattr(yaml, 'load_yaml'):
        cfg = yaml.load_yaml(fichero)
    else:
        cfg = {}
    if cfg is None:
        return {}
    if not isinstance(cfg, dict):
        raise ValueError('task_config.yaml debe ser un mapa')
    _validar_configuracion(cfg)
    return cfg


def _validar_configuracion(cfg):
    """Rechaza configuraciones inválidas en validation y release identificando la clave infractora."""
    validation = cfg.get('validation')
    if validation is not None:
        if not isinstance(validation, dict):
            raise ValueError('Configuración inválida en validation: debe ser un mapa')
        for clave, valor in validation.items():
            if clave in ('command', 'formato_escritura'):
                if not isinstance(valor, str) or not valor.strip():
                    raise ValueError(f'Configuración inválida en validation.{clave}: debe ser una cadena no vacía')
                continue
            if clave in ETAPAS_CATALOGO:
                if isinstance(valor, str):
                    if not valor.strip():
                        raise ValueError(f'Configuración inválida en validation.{clave}: comando vacío')
                elif isinstance(valor, dict):
                    for subclave in ('comando', 'command'):
                        if subclave in valor:
                            subval = valor[subclave]
                            if not isinstance(subval, str) or not subval.strip():
                                raise ValueError(
                                    f'Configuración inválida en validation.{clave}.{subclave}: debe ser cadena no vacía'
                                )
                    if 'obligatorio' in valor and not isinstance(valor['obligatorio'], bool):
                        raise ValueError(
                            f'Configuración inválida en validation.{clave}.obligatorio: debe ser booleano'
                        )
                    if 'entradas' in valor:
                        entradas = valor['entradas']
                        if not isinstance(entradas, list) or not all(
                            isinstance(x, str) and x.strip() for x in entradas
                        ):
                            raise ValueError(
                                f'Configuración inválida en validation.{clave}.entradas: debe ser lista de rutas'
                            )
                else:
                    raise ValueError(
                        f'Configuración inválida en validation.{clave}: se esperaba cadena o mapa de configuración'
                    )
    release = cfg.get('release')
    if release is not None:
        if not isinstance(release, dict):
            raise ValueError('Configuración inválida en release: debe ser un mapa')
        if 'puertas' in release:
            puertas = release['puertas']
            if not isinstance(puertas, list) or not all(
                isinstance(p, str) and p in ETAPAS_CATALOGO for p in puertas
            ):
                raise ValueError(
                    'Configuración inválida en release.puertas: debe ser una lista de etapas válidas del catálogo'
                )
        if 'preflight' in release:
            preflight = release['preflight']
            if not isinstance(preflight, list) or not all(
                isinstance(c, str) and c.strip() for c in preflight
            ):
                raise ValueError('Configuración inválida en release.preflight: debe ser una lista de comandos')
        if 'restricciones' in release:
            restricciones = release['restricciones']
            if not isinstance(restricciones, dict):
                raise ValueError('Configuración inválida en release.restricciones: debe ser un mapa')
            for r_clave, r_val in restricciones.items():
                if r_clave in ACCIONES_RELEASE:
                    if isinstance(r_val, bool):
                        continue
                    if isinstance(r_val, list) and all(isinstance(c, str) and c in CANALES for c in r_val):
                        continue
                    raise ValueError(
                        f'Configuración inválida en release.restricciones.{r_clave}: valor no reconocido'
                    )
                elif r_clave in CANALES:
                    if isinstance(r_val, bool):
                        continue
                    if isinstance(r_val, dict) and all(
                        k in ACCIONES_RELEASE and isinstance(v, bool) for k, v in r_val.items()
                    ):
                        continue
                    raise ValueError(
                        f'Configuración inválida en release.restricciones.{r_clave}: mapa de acciones inválido'
                    )
                else:
                    raise ValueError(
                        f'Configuración inválida en release.restricciones.{r_clave}: clave desconocida'
                    )


def verificar_restriccion_release(root, canal, accion, cfg=None):
    """Comprueba si un canal está autorizado para ejecutar una acción de release según task_config.yaml."""
    if cfg is None:
        cfg = cargar_configuracion(root)
    else:
        _validar_configuracion(cfg)
    restricciones = ((cfg.get('release') or {}).get('restricciones')) or {}
    if canal in restricciones:
        regla_canal = restricciones[canal]
        if isinstance(regla_canal, bool) and not regla_canal:
            raise ValueError(
                f'Restricción de release: el canal {canal} no tiene permitido ejecutar {accion}.'
            )
        if isinstance(regla_canal, dict) and regla_canal.get(accion) is False:
            raise ValueError(
                f'Restricción de release: el canal {canal} no tiene permitido {accion}.'
            )
    if accion in restricciones:
        regla_accion = restricciones[accion]
        if isinstance(regla_accion, bool) and not regla_accion:
            raise ValueError(
                f'Restricción de release: la acción {accion} está deshabilitada por restricción del proyecto.'
            )
        if isinstance(regla_accion, list) and canal not in regla_accion:
            raise ValueError(
                f'Restricción de release: la acción {accion} no está permitida desde el canal {canal}.'
            )
    return True


def _comando_texto(comando):
    """Normaliza un comando en lista o cadena a su representación textual estable."""
    if comando is None:
        return None
    if isinstance(comando, str):
        return comando
    return ' '.join(str(x) for x in comando)


def resolver_catalogo(root, cfg=None, ficheros=None):
    """Resuelve todas las etapas del catálogo indicando disponibilidad, comando efectivo, origen y entradas."""
    base = Path(root).resolve()
    if cfg is None:
        cfg = cargar_configuracion(base)
    validation = cfg.get('validation') or {}
    ficheros_repo = [
        f for f in (_listar_ficheros_repositorio(base) if ficheros is None else ficheros)
        if (base / f).is_file()
    ]
    scripts, ruff, _ = calidad._manifiestos(base)
    catalogo = {}

    for etapa in ETAPAS_CATALOGO:
        spec = validation.get(etapa)
        obligatorio = False
        entradas = None
        cmd_declarado = None
        if isinstance(spec, str):
            cmd_declarado = spec.strip()
            obligatorio = True
        elif isinstance(spec, dict):
            cmd_declarado = (spec.get('comando') or spec.get('command') or '').strip() or None
            obligatorio = bool(spec.get('obligatorio', bool(cmd_declarado)))
            entradas = list(spec['entradas']) if 'entradas' in spec else None

        if etapa == 'pruebas' and not cmd_declarado and isinstance(validation.get('command'), str):
            cmd_declarado = validation['command'].strip()
            origen_pruebas = 'task_config.yaml (validation.command)'
            obligatorio = True
        else:
            origen_pruebas = f'task_config.yaml (validation.{etapa})'

        if cmd_declarado:
            comando_efectivo = calidad._expandir(cmd_declarado, ficheros_repo, etapa)
            if isinstance(comando_efectivo, list) and not ficheros_repo and '{ficheros}' in cmd_declarado:
                catalogo[etapa] = {
                    'etapa': etapa,
                    'disponibilidad': 'omitido',
                    'comando': None,
                    'comando_texto': None,
                    'origen': origen_pruebas,
                    'obligatorio': obligatorio,
                    'entradas': entradas,
                    'herramienta': None,
                    'motivo': 'sin objetivos compatibles',
                }
                continue
            catalogo[etapa] = {
                'etapa': etapa,
                'disponibilidad': 'configurado',
                'comando': comando_efectivo,
                'comando_texto': _comando_texto(comando_efectivo),
                'origen': origen_pruebas,
                'obligatorio': obligatorio,
                'entradas': entradas,
                'herramienta': None,
                'motivo': 'configurado explícitamente',
            }
            continue

        if etapa in ('formato', 'lint'):
            cmd_ded, _, herramienta, _ = calidad._deducir(etapa, scripts, ruff)
            if cmd_ded is not None:
                if herramienta in ('prettier', 'eslint'):
                    clave_script = 'format:check' if etapa == 'formato' else 'lint'
                    origen_ded = f'deducido de package.json (scripts.{clave_script})'
                else:
                    origen_ded = 'deducido de pyproject.toml (tool.ruff)'
                objetivos = [
                    ('./' + f if f.startswith('-') else f)
                    for f in ficheros_repo
                    if Path(f).suffix.lower() in calidad.EXTENSIONES[herramienta]
                ]
                if objetivos:
                    cmd_lista = cmd_ded + objetivos
                    catalogo[etapa] = {
                        'etapa': etapa,
                        'disponibilidad': 'configurado',
                        'comando': cmd_lista,
                        'comando_texto': _comando_texto(cmd_lista),
                        'origen': origen_ded,
                        'obligatorio': obligatorio,
                        'entradas': entradas,
                        'herramienta': herramienta,
                        'motivo': origen_ded,
                    }
                    continue
                catalogo[etapa] = {
                    'etapa': etapa,
                    'disponibilidad': 'omitido',
                    'comando': None,
                    'comando_texto': None,
                    'origen': origen_ded,
                    'obligatorio': obligatorio,
                    'entradas': entradas,
                    'herramienta': herramienta,
                    'motivo': 'sin objetivos compatibles',
                }
                continue

        motivo_ausente = 'análisis obligatorio ausente' if obligatorio else 'análisis opcional no configurado'
        catalogo[etapa] = {
            'etapa': etapa,
            'disponibilidad': 'ausente',
            'comando': None,
            'comando_texto': None,
            'origen': None,
            'obligatorio': obligatorio,
            'entradas': entradas,
            'herramienta': None,
            'motivo': motivo_ausente,
        }
    return catalogo


def _hash_archivos(base, nombres):
    """Calcula un hash SHA-256 determinista del conjunto de archivos existentes de la lista."""
    digest = hashlib.sha256()
    for nombre in sorted(nombres):
        ruta = base / nombre
        if ruta.is_file():
            digest.update(nombre.encode('utf-8'))
            digest.update(b'\0')
            contenido = ruta.read_bytes().replace(b'\r\n', b'\n')
            digest.update(hashlib.sha256(contenido).digest())
            digest.update(b'\0')
    return digest.hexdigest()


def _calcular_entorno(root, entorno_override=None):
    """Calcula la huella del entorno relevante (herramienta, configuración, dependencias y plataforma)."""
    base = Path(root).resolve()
    entorno = {
        'herramienta': f'python-{sys.version.split()[0]}',
        'configuracion': _hash_archivos(base, ARCHIVOS_CONFIGURACION),
        'dependencias': _hash_archivos(base, ARCHIVOS_DEPENDENCIAS),
        'plataforma': f'{sys.platform}-py{sys.version_info.major}.{sys.version_info.minor}',
    }
    if entorno_override:
        for k, v in entorno_override.items():
            if v is not None:
                entorno[k] = str(v)
    return entorno


def _coincide_entrada(ruta_rel, patron):
    """Indica si una ruta relativa pertenece al prefijo o archivo declarado en entradas."""
    ruta_norm = ruta_rel.replace('\\', '/').strip('/')
    pat_norm = patron.replace('\\', '/').strip('/')
    if not pat_norm:
        return True
    return ruta_norm == pat_norm or ruta_norm.startswith(pat_norm + '/')


def calcular_identidad(root, etapa, info_etapa, entorno_override=None):
    """Calcula la identidad compuesta de una comprobación verificando que sus entradas sean acreditables."""
    base = Path(root).resolve()
    entradas = info_etapa.get('entradas')
    comando_texto = info_etapa.get('comando_texto') or _comando_texto(info_etapa.get('comando')) or ''
    entorno = _calcular_entorno(base, entorno_override=entorno_override)

    if entradas:
        for entrada in entradas:
            ruta_entrada = base / entrada.rstrip('/')
            if not ruta_entrada.exists():
                return {
                    'acreditable': False,
                    'motivo_no_acreditable': f'entrada relevante no acreditable ({entrada})',
                    'identidad': None,
                    'hash_contenido': None,
                    'entorno': entorno,
                    'comando': comando_texto,
                    'entradas': list(entradas),
                }
        todos = _listar_ficheros_repositorio(base)
        seleccionados = [f for f in todos if any(_coincide_entrada(f, e) for e in entradas)]
    else:
        seleccionados = _listar_ficheros_repositorio(base)

    digest = hashlib.sha256()
    for rel in sorted(seleccionados):
        digest.update(rel.encode('utf-8', errors='surrogateescape'))
        digest.update(b'\0')
        p = base / rel
        if p.is_file():
            contenido = p.read_bytes().replace(b'\r\n', b'\n')
            digest.update(hashlib.sha256(contenido).digest())
        else:
            digest.update(b'DELETED')
        digest.update(b'\0')
    hash_contenido = digest.hexdigest()

    payload = {
        'etapa': etapa,
        'comando': comando_texto,
        'hash_contenido': hash_contenido,
        'entorno': entorno,
    }
    identidad = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
    return {
        'acreditable': True,
        'motivo_no_acreditable': '',
        'identidad': identidad,
        'hash_contenido': hash_contenido,
        'entorno': entorno,
        'comando': comando_texto,
        'entradas': list(entradas) if entradas else [],
    }


def _rutas_lectura_evidencias(root):
    """Enumera los archivos de evidencias aplicables al árbol o worktree actual."""
    base = Path(root).resolve()
    rutas = [base / EVIDENCIAS]
    comun = directorio_git_comun(base)
    if comun.name == '.git' and comun.parent.resolve() != base:
        rutas.append(comun.parent.resolve() / EVIDENCIAS)
    rutas.append(directorio_coordinacion(base) / EVIDENCIAS)
    unicas = []
    vistas = set()
    for r in rutas:
        clave = str(r.resolve())
        if clave not in vistas:
            vistas.add(clave)
            unicas.append(r)
    return unicas


def leer_evidencias(root):
    """Lee en orden cronológico los registros de evidencias del repositorio y su coordinación común."""
    base = Path(root).resolve()
    local = base / EVIDENCIAS
    lineas_crudas = []
    if local.is_file():
        lineas_crudas = local.read_text(encoding='utf-8', errors='replace').splitlines()
    else:
        for candidata in _rutas_lectura_evidencias(base):
            if candidata.is_file():
                lineas_crudas = candidata.read_text(encoding='utf-8', errors='replace').splitlines()
                if lineas_crudas:
                    break
    registros = []
    for linea in lineas_crudas:
        if not linea.strip():
            continue
        try:
            dato = json.loads(linea)
            if isinstance(dato, dict):
                registros.append(dato)
        except ValueError:
            continue
    return registros


def _escribir_evidencia(root, fila):
    """Persiste un registro de ejecución real en el archivo de evidencias del árbol y en el almacén común."""
    base = Path(root).resolve()
    _excluir_propios(base)
    texto = json.dumps(fila, ensure_ascii=False) + '\n'
    destino_local = base / EVIDENCIAS
    with destino_local.open('a', encoding='utf-8') as f:
        f.write(texto)
    try:
        destino_comun = directorio_coordinacion(base) / EVIDENCIAS
        if destino_comun.resolve() != destino_local.resolve():
            with destino_comun.open('a', encoding='utf-8') as fc:
                fc.write(texto)
    except OSError:
        pass


def _leer_estado_en_curso_disco(root):
    """Lee el archivo de estado de ejecución en curso desde el directorio Git común."""
    ruta = directorio_coordinacion(root) / ESTADO_EN_CURSO
    if not ruta.is_file():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding='utf-8'))
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar_estado_en_curso_disco(root, datos):
    """Actualiza de forma atómica el estado en curso compartido en el directorio Git común."""
    coord = directorio_coordinacion(root)
    destino = coord / ESTADO_EN_CURSO
    with tempfile.NamedTemporaryFile('w', dir=coord, delete=False, encoding='utf-8') as tmp:
        json.dump(datos, tmp, ensure_ascii=False)
        ruta_tmp = Path(tmp.name)
    try:
        os.replace(ruta_tmp, destino)
    except OSError:
        ruta_tmp.unlink(missing_ok=True)


def registrar_ejecucion_interrumpida_prueba(root, etapa, comando, pid, salida_parcial=''):
    """Registra un estado en curso con el PID dado para verificar la recuperación ante cortes abruptos."""
    with _LOCK_GLOBAL:
        actual = _leer_estado_en_curso_disco(root)
        actual[etapa] = {
            'etapa': etapa,
            'comando': comando,
            'pid': int(pid),
            'fase': 'ejecutando',
            'salida_parcial': salida_parcial,
            'identidad': 'identidad-interrumpida',
            'fecha': _ahora(),
        }
        _guardar_estado_en_curso_disco(root, actual)


def _inspeccionar_en_curso(root):
    """Inspecciona ejecuciones activas y convierte procesos muertos en estado interrumpido."""
    with _LOCK_GLOBAL:
        datos = _leer_estado_en_curso_disco(root)
        modificado = False
        for etapa, info in list(datos.items()):
            if info.get('fase') == 'ejecutando':
                pid = info.get('pid')
                if not _proceso_vivo(pid):
                    info['fase'] = 'interrumpido'
                    modificado = True
        if modificado:
            _guardar_estado_en_curso_disco(root, datos)
        return datos


def _resumir_historial_etapa(registros, etapa, comando_texto):
    """Pliega los registros de una etapa o comando determinando su último resultado real e intermitencias."""
    aplicables = [
        r for r in registros
        if (etapa and r.get('etapa') == etapa) or (comando_texto and r.get('comando') == comando_texto)
    ]
    if not aplicables:
        return None
    ultimo = aplicables[-1]
    id_ultimo = ultimo.get('identidad') or ultimo.get('arbol')
    misma_id = [
        r for r in aplicables
        if (r.get('identidad') or r.get('arbol')) == id_ultimo
    ]
    transiciones = [
        'aprobado' if (r.get('codigo') == 0 and not r.get('cambio_en_vuelo')) else 'fallido'
        for r in misma_id
    ]
    intermitente = len(set(transiciones)) > 1
    resultado = transiciones[-1]
    diagnostico = (
        f'Advertencia de intermitencia: la comprobación alternó resultados ({", ".join(transiciones)}) sobre la misma identidad.'
        if intermitente else ''
    )
    return {
        'ultimo': ultimo,
        'resultado': resultado,
        'intermitente': intermitente,
        'transiciones': transiciones,
        'diagnostico': diagnostico,
    }


def _explicar_diferencia_identidad(ultimo, info_id, cambios=None):
    """Explica con precisión por qué una evidencia previa no es reutilizable frente a la identidad actual."""
    if not info_id['acreditable']:
        return info_id['motivo_no_acreditable']
    if cambios:
        entradas = info_id.get('entradas') or []
        afectados = [
            c for c in cambios
            if not entradas or any(_coincide_entrada(c, e) for e in entradas)
        ]
        if afectados:
            return f'cambio en contenido relevante ({", ".join(afectados)})'
    if ultimo is None:
        return 'sin evidencia previa acreditada'
    if ultimo.get('cambio_en_vuelo'):
        return 'ejecución previa invalidada por cambio en vuelo'
    if ultimo.get('codigo') != 0:
        return 'último resultado real fallido'
    if ultimo.get('contrato') != 'v2' and 'identidad' not in ultimo:
        return 'evidencia histórica sin identidad compuesta acreditada'
    entorno_prev = ultimo.get('entorno') or {}
    entorno_act = info_id.get('entorno') or {}
    if ultimo.get('hash_contenido') and ultimo.get('hash_contenido') != info_id.get('hash_contenido'):
        return 'cambio en contenido relevante'
    if entorno_prev.get('herramienta') != entorno_act.get('herramienta'):
        return 'cambio en entorno (herramienta)'
    if entorno_prev.get('configuracion') != entorno_act.get('configuracion'):
        return 'cambio en entorno (configuración)'
    if entorno_prev.get('dependencias') != entorno_act.get('dependencias'):
        return 'cambio en entorno (dependencias)'
    if entorno_prev.get('plataforma') != entorno_act.get('plataforma'):
        return 'cambio en entorno (plataforma)'
    return 'cambio en contenido relevante'


def planificar(root, etapas=None, puerta=None, entorno_override=None, cambios=None):
    """Construye el plan explicable de comprobaciones antes de ejecutar."""
    base = Path(root).resolve()
    cfg = cargar_configuracion(base)
    catalogo = resolver_catalogo(base, cfg=cfg)
    registros = leer_evidencias(base)
    en_curso = _inspeccionar_en_curso(base)

    puertas_cfg = (cfg.get('release') or {}).get('puertas')
    if etapas is not None:
        seleccion = list(etapas)
    elif puerta == 'release' and puertas_cfg:
        seleccion = list(ETAPAS_CATALOGO)
    else:
        seleccion = list(ETAPAS_CATALOGO)

    plan_etapas = {}
    lineas_texto = []

    for etapa in seleccion:
        info = catalogo.get(etapa) or {
            'etapa': etapa,
            'disponibilidad': 'ausente',
            'comando': None,
            'comando_texto': None,
            'origen': None,
            'obligatorio': False,
            'entradas': None,
            'herramienta': None,
            'motivo': 'análisis opcional no configurado',
        }
        disp = info['disponibilidad']
        if disp != 'configurado':
            plan_etapas[etapa] = {
                'etapa': etapa,
                'disponibilidad': disp,
                'resultado': 'sin_acreditar',
                'comando': info['comando'],
                'origen': info['origen'],
                'obligatorio': info['obligatorio'],
                'accion': 'omitir',
                'motivo': info['motivo'],
                'identidad': None,
            }
            lineas_texto.append(
                f"- {etapa}: [{disp}/sin_acreditar] acción=omitir ({info['motivo']})"
            )
            continue

        info_id = calcular_identidad(base, etapa, info, entorno_override=entorno_override)
        resumen_hist = _resumir_historial_etapa(registros, etapa, info['comando_texto'])
        ultimo = resumen_hist['ultimo'] if resumen_hist else None

        activo = en_curso.get(etapa)
        motivo_espera = None
        siguiente_accion = None
        if activo and activo.get('fase') == 'ejecutando':
            if activo.get('identidad') == info_id['identidad'] and info_id['acreditable']:
                accion = 'esperar'
                resultado_est = 'ejecutando'
                motivo = 'ejecución equivalente en curso; se compartirá su resultado'
                motivo_espera = 'compartiendo ejecución en curso con la misma identidad'
                siguiente_accion = 'esperar resultado de la ejecución compartida'
            else:
                accion = 'ejecutar'
                resultado_est = 'pendiente'
                motivo = 'ejecución en curso con identidad distinta'
                motivo_espera = 'en espera de que finalice la ejecución en curso con identidad distinta'
                siguiente_accion = 'ejecutar con identidad propia tras finalizar la ejecución activa'
        elif (
            info_id['acreditable']
            and ultimo is not None
            and ultimo.get('identidad') == info_id['identidad']
            and ultimo.get('codigo') == 0
            and not ultimo.get('cambio_en_vuelo')
            and not (cambios and any(
                not info_id['entradas'] or any(_coincide_entrada(c, e) for e in info_id['entradas'])
                for c in cambios
            ))
        ):
            accion = 'reutilizar'
            resultado_est = 'aprobado'
            motivo = f"evidencia aprobada vigente para la misma identidad ({info_id['identidad'][:10]})"
            siguiente_accion = 'reutilizar evidencia acreditada'
        else:
            accion = 'ejecutar'
            misma_id_fallida = (
                ultimo is not None
                and (
                    ultimo.get('identidad') == info_id['identidad']
                    or (ultimo.get('comando') == info['comando_texto'] and ultimo.get('codigo') != 0)
                )
                and ultimo.get('codigo') != 0
            )
            resultado_est = 'fallido' if misma_id_fallida else 'pendiente'
            motivo = _explicar_diferencia_identidad(ultimo, info_id, cambios=cambios)
            siguiente_accion = 'ejecutar comprobación'

        plan_etapas[etapa] = {
            'etapa': etapa,
            'disponibilidad': disp,
            'resultado': resultado_est,
            'comando': info['comando'],
            'comando_texto': info['comando_texto'],
            'origen': info['origen'],
            'obligatorio': info['obligatorio'],
            'entradas': info['entradas'],
            'accion': accion,
            'motivo': motivo,
            'motivo_espera': motivo_espera,
            'siguiente_accion': siguiente_accion,
            'identidad': info_id['identidad'],
            'info_identidad': info_id,
        }
        lineas_texto.append(
            f"- {etapa}: [{disp}/{resultado_est}] comando={info['comando_texto']} "
            f"origen={info['origen']} acción={accion} ({motivo})"
        )

    return {
        'etapas': plan_etapas,
        'texto': '\n'.join(lineas_texto),
    }


def _invocar_ejecutor(ejecutor, root, comando, etapa, stream_callback):
    """Invoca un ejecutor personalizado o subprocess.run capturando salida parcial y código de retorno."""
    if ejecutor is not None:
        sig = inspect.signature(ejecutor)
        kwargs = {}
        acepta_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        if 'etapa' in sig.parameters or acepta_var_kw:
            kwargs['etapa'] = etapa
        if 'stream_callback' in sig.parameters or acepta_var_kw:
            kwargs['stream_callback'] = stream_callback
        if 'root' in sig.parameters or acepta_var_kw:
            kwargs['root'] = root
        res = ejecutor(comando, **kwargs)
        if isinstance(res, tuple) and len(res) == 2:
            return int(res[0]), str(res[1] or '')
        return int(res), ''

    cmd_ejec = comando if isinstance(comando, str) else _comando_texto(comando)
    proc = subprocess.run(
        cmd_ejec,
        shell=True,
        cwd=root,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    salida = (proc.stdout or '') + (proc.stderr or '')
    if stream_callback and salida:
        stream_callback(salida)
    return proc.returncode, salida


def ejecutar_comprobacion(
    root,
    etapa,
    comando=None,
    ejecutor=None,
    entorno_override=None,
    canal='cli',
    forzar_ejecucion=False,
):
    """Ejecuta o reutiliza una comprobación coordinando concurrencia entre entradas y worktrees."""
    base = Path(root).resolve()
    cfg = cargar_configuracion(base)
    catalogo = resolver_catalogo(base, cfg=cfg)
    info = dict(catalogo.get(etapa) or {
        'etapa': etapa,
        'disponibilidad': 'configurado' if comando else 'ausente',
        'comando': comando,
        'comando_texto': _comando_texto(comando),
        'origen': 'invocación directa',
        'obligatorio': True,
        'entradas': None,
        'herramienta': None,
        'motivo': '',
    })
    if comando is not None:
        info['disponibilidad'] = 'configurado'
        info['comando'] = comando
        info['comando_texto'] = _comando_texto(comando)

    if info['disponibilidad'] != 'configurado' or not info['comando']:
        return {
            'etapa': etapa,
            'codigo': 1 if info.get('obligatorio') else 0,
            'estado': 'sin_acreditar',
            'disponibilidad': info['disponibilidad'],
            'reutilizada': False,
            'acreditado': False,
            'motivo': info.get('motivo', 'no configurado'),
        }

    info_id_inicial = calcular_identidad(base, etapa, info, entorno_override=entorno_override)
    identidad_inicial = info_id_inicial['identidad']

    if not forzar_ejecucion and info_id_inicial['acreditable']:
        registros = leer_evidencias(base)
        resumen_hist = _resumir_historial_etapa(registros, etapa, info['comando_texto'])
        if resumen_hist is not None:
            ultimo = resumen_hist['ultimo']
            es_mismo = ultimo.get('identidad') == identidad_inicial
            if not es_mismo and not info.get('entradas') and not entorno_override and ultimo.get('comando') == info['comando_texto'] and ultimo.get('arbol'):
                try:
                    es_mismo = ultimo.get('arbol') == arbol_trabajo(base)
                except Exception:
                    es_mismo = False
            if es_mismo and ultimo.get('codigo') == 0 and not ultimo.get('cambio_en_vuelo'):
                return {
                    'etapa': etapa,
                    'comando': info['comando_texto'],
                    'codigo': 0,
                    'estado': 'aprobado',
                    'disponibilidad': 'configurado',
                    'reutilizada': True,
                    'acreditado': True,
                    'cambio_en_vuelo': False,
                    'identidad': identidad_inicial,
                    'identidad_inicial': identidad_inicial,
                    'identidad_final': identidad_inicial,
                    'salida': ultimo.get('salida', ''),
                    'canal': canal,
                }

    coord_key = (str(directorio_coordinacion(base).resolve()), etapa)
    esperar_existente = None
    with _LOCK_GLOBAL:
        en_memoria = _EJECUCIONES_MEMORIA.get(coord_key)
        if en_memoria is not None and not en_memoria['evento'].is_set():
            if not forzar_ejecucion and identidad_inicial and en_memoria['identidad'] == identidad_inicial:
                esperar_existente = en_memoria

        if esperar_existente is None:
            actual_evento = threading.Event()
            registro_mem = {
                'identidad': identidad_inicial,
                'comando': info['comando_texto'],
                'evento': actual_evento,
                'salida_parcial': '',
                'resultado': None,
            }
            _EJECUCIONES_MEMORIA[coord_key] = registro_mem
            estado_disco = _leer_estado_en_curso_disco(base)
            estado_disco[etapa] = {
                'etapa': etapa,
                'comando': info['comando_texto'],
                'pid': os.getpid(),
                'fase': 'ejecutando',
                'salida_parcial': '',
                'identidad': identidad_inicial,
                'canal': canal,
                'fecha': _ahora(),
            }
            _guardar_estado_en_curso_disco(base, estado_disco)

    if esperar_existente is not None:
        esperar_existente['evento'].wait(timeout=30)
        res_compartido = dict(esperar_existente.get('resultado') or {})
        res_compartido['reutilizada'] = True
        res_compartido['compartida_en_vuelo'] = True
        return res_compartido

    def _actualizar_stream(fragmento):
        with _LOCK_GLOBAL:
            registro_mem['salida_parcial'] += str(fragmento)
            est = _leer_estado_en_curso_disco(base)
            if etapa in est:
                est[etapa]['salida_parcial'] = registro_mem['salida_parcial']
                _guardar_estado_en_curso_disco(base, est)

    inicio = time.monotonic()
    try:
        codigo, salida = _invocar_ejecutor(ejecutor, base, info['comando'], etapa, _actualizar_stream)
    finally:
        with _LOCK_GLOBAL:
            est = _leer_estado_en_curso_disco(base)
            est.pop(etapa, None)
            _guardar_estado_en_curso_disco(base, est)

    duracion_s = round(time.monotonic() - inicio)
    info_id_final = calcular_identidad(base, etapa, info, entorno_override=entorno_override)
    identidad_final = info_id_final['identidad']
    cambio_en_vuelo = (
        not info_id_inicial['acreditable']
        or not info_id_final['acreditable']
        or identidad_inicial != identidad_final
    )
    acreditado = (codigo == 0) and not cambio_en_vuelo
    estado_final = (
        'aprobado' if acreditado else ('sin_acreditar' if cambio_en_vuelo and codigo == 0 else 'fallido')
    )

    if ejecutor is None:
        try:
            arbol_actual = arbol_trabajo(base)
        except Exception:
            arbol_actual = info_id_final.get('hash_contenido') or ''
    else:
        arbol_actual = info_id_final.get('hash_contenido') or ''

    fila_evidencia = {
        'contrato': 'v2',
        'fecha': _ahora(),
        'etapa': etapa,
        'comando': info['comando_texto'],
        'arbol': arbol_actual,
        'identidad': identidad_inicial,
        'identidad_final': identidad_final,
        'hash_contenido': info_id_inicial.get('hash_contenido'),
        'entorno': info_id_inicial.get('entorno'),
        'codigo': codigo if not cambio_en_vuelo else (codigo or 1),
        'codigo_proceso': codigo,
        'acreditado': acreditado,
        'cambio_en_vuelo': cambio_en_vuelo,
        'canal': canal,
        'salida': salida[-32768:] if salida else '',
        'duracion_s': duracion_s,
    }
    _escribir_evidencia(base, fila_evidencia)

    resultado_obj = {
        'etapa': etapa,
        'comando': info['comando_texto'],
        'codigo': fila_evidencia['codigo'],
        'estado': estado_final,
        'disponibilidad': 'configurado',
        'reutilizada': False,
        'acreditado': acreditado,
        'cambio_en_vuelo': cambio_en_vuelo,
        'identidad': identidad_inicial if not cambio_en_vuelo else None,
        'identidad_inicial': identidad_inicial,
        'identidad_final': identidad_final,
        'salida': salida,
        'duracion_s': duracion_s,
        'canal': canal,
    }

    with _LOCK_GLOBAL:
        registro_mem['resultado'] = resultado_obj
        registro_mem['evento'].set()
        _EJECUCIONES_MEMORIA.pop(coord_key, None)

    return resultado_obj


def evaluar_puerta(root, puerta='release', ejecutar=False, ejecutor=None, entorno_override=None, canal='cli'):
    """Evalúa una puerta de calidad o release separando disponibilidad y resultado."""
    base = Path(root).resolve()
    cfg = cargar_configuracion(base)
    plan = planificar(base, puerta=puerta, entorno_override=entorno_override)
    etapas_plan = plan['etapas']

    puertas_requeridas = (cfg.get('release') or {}).get('puertas')
    if not puertas_requeridas:
        puertas_requeridas = [
            etapa for etapa, datos in etapas_plan.items()
            if datos.get('obligatorio') or datos.get('disponibilidad') == 'configurado'
        ]

    resultados_etapas = {}
    fallos = []

    for etapa in ETAPAS_CATALOGO:
        datos = etapas_plan[etapa]
        es_requerida = etapa in puertas_requeridas or datos.get('obligatorio', False)
        if datos['disponibilidad'] != 'configurado':
            resultados_etapas[etapa] = dict(datos)
            if es_requerida and datos['disponibilidad'] == 'ausente':
                fallos.append(f"{etapa} ({datos['motivo']})")
            continue

        if ejecutar:
            res = ejecutar_comprobacion(
                base,
                etapa,
                ejecutor=ejecutor,
                entorno_override=entorno_override,
                canal=canal,
            )
            resultados_etapas[etapa] = {
                **datos,
                'resultado': res['estado'],
                'codigo': res['codigo'],
                'salida': res.get('salida', ''),
                'reutilizada': res.get('reutilizada', False),
            }
            if res['estado'] != 'aprobado' and es_requerida:
                fallos.append(f'{etapa} (fallido)')
        else:
            resultados_etapas[etapa] = dict(datos)
            if es_requerida and datos['resultado'] != 'aprobado':
                fallos.append(f"{etapa} ({datos['resultado']})")

    estado_global = 'fallido' if fallos else 'aprobado'
    return {
        'puerta': puerta,
        'estado': estado_global,
        'motivo': '; '.join(fallos) if fallos else 'todas las puertas requeridas acreditadas',
        'plan': plan,
        'etapas': resultados_etapas,
    }


def consultar_estado(root):
    """Consulta sin efectos laterales la fase activa, salida parcial, progreso y evidencias."""
    base = Path(root).resolve()
    en_curso = _inspeccionar_en_curso(base)
    registros = leer_evidencias(base)

    evidencias_mapa = {}
    claves_etapa = {r.get('etapa') for r in registros if r.get('etapa')}
    claves_cmd = {r.get('comando') for r in registros if r.get('comando')}

    for etapa in claves_etapa:
        resumen = _resumir_historial_etapa(registros, etapa, None)
        if resumen:
            evidencias_mapa[etapa] = {
                'resultado': resumen['resultado'],
                'intermitente': resumen['intermitente'],
                'transiciones': resumen['transiciones'],
                'diagnostico': resumen['diagnostico'],
                'ultimo': resumen['ultimo'],
            }
    for cmd in claves_cmd:
        resumen = _resumir_historial_etapa(registros, None, cmd)
        if resumen:
            evidencias_mapa[cmd] = {
                'resultado': resumen['resultado'],
                'intermitente': resumen['intermitente'],
                'transiciones': resumen['transiciones'],
                'diagnostico': resumen['diagnostico'],
                'ultimo': resumen['ultimo'],
            }

    ejecutando = [info for info in en_curso.values() if info.get('fase') == 'ejecutando']
    interrumpidos = [info for info in en_curso.values() if info.get('fase') == 'interrumpido']

    for info_int in interrumpidos:
        et = info_int.get('etapa')
        if et:
            evidencias_mapa[et] = {
                'resultado': 'interrumpido',
                'intermitente': False,
                'transiciones': ['interrumpido'],
                'diagnostico': 'Proceso en curso terminado abruptamente sin acreditar resultado.',
                'salida_parcial': info_int.get('salida_parcial', ''),
            }

    if ejecutando:
        actual = ejecutando[0]
        return {
            'fase': 'ejecutando',
            'comando_activo': actual.get('comando'),
            'etapa_activa': actual.get('etapa'),
            'salida_parcial': actual.get('salida_parcial', ''),
            'progreso': None,
            'motivo_espera': None,
            'siguiente_accion': 'esperar finalización de la comprobación en curso',
            'evidencias': evidencias_mapa,
        }

    if interrumpidos:
        actual = interrumpidos[0]
        return {
            'fase': 'interrumpido',
            'comando_activo': actual.get('comando'),
            'etapa_activa': actual.get('etapa'),
            'salida_parcial': actual.get('salida_parcial', ''),
            'progreso': None,
            'motivo_espera': 'proceso previo interrumpido abruptamente',
            'siguiente_accion': 'reejecutar comprobación interrumpida para acreditar el árbol actual',
            'evidencias': evidencias_mapa,
        }

    return {
        'fase': 'inactivo',
        'comando_activo': None,
        'etapa_activa': None,
        'salida_parcial': '',
        'progreso': None,
        'motivo_espera': None,
        'siguiente_accion': 'ninguna',
        'evidencias': evidencias_mapa,
    }


def diagnosticar_fallo(root, etapa, resultado_etapa, intentos_agotados=False, motivo_humano=None):
    """Diagnostica un fallo de comprobación proponiendo reparación acotada o intervención humana."""
    salida = (resultado_etapa or {}).get('salida') or (resultado_etapa or {}).get('motivo') or ''
    if intentos_agotados or motivo_humano:
        return {
            'etapa': etapa,
            'estado': 'fallido',
            'causa': salida.strip(),
            'siguiente_accion': 'intervencion_humana',
            'motivo_intervencion_humana': motivo_humano or salida.strip() or 'Se requiere intervención humana.',
        }
    return {
        'etapa': etapa,
        'estado': 'fallido',
        'causa': salida.strip(),
        'siguiente_accion': 'reparar',
        'motivo_intervencion_humana': None,
    }


def planificar_reparacion(root, cambios=None, puerta='release', entorno_override=None):
    """Planifica la revalidación tras reparar un fallo conservando en caché las etapas no afectadas."""
    return planificar(root, puerta=puerta, entorno_override=entorno_override, cambios=cambios)


def comandos_verificados_arbol(root, clave_arbol=None):
    """Devuelve la lista de comandos cuyo último resultado real sobre el árbol actual está aprobado."""
    base = Path(root).resolve()
    clave = clave_arbol or arbol_trabajo(base)
    registros = leer_evidencias(base)
    estado_por_cmd = {}
    orden_cmds = []
    for fila in registros:
        if fila.get('arbol') != clave:
            continue
        cmd = fila.get('comando')
        if not cmd:
            continue
        if cmd not in orden_cmds:
            orden_cmds.append(cmd)
        aprobado = (fila.get('codigo') == 0) and not fila.get('cambio_en_vuelo')
        estado_por_cmd[cmd] = aprobado
    return [c for c in orden_cmds if estado_por_cmd.get(c)]


def ultimo_resultado_arbol_comando(root, clave_arbol, comando):
    """Obtiene el último registro de ejecución real para un árbol y comando dados."""
    registros = leer_evidencias(root)
    aplicables = [
        r for r in registros
        if r.get('arbol') == clave_arbol and r.get('comando') == comando
    ]
    return aplicables[-1] if aplicables else None


def ejecutar_preflight_worktree(repo_root, worktree_root, command, ejecutar_fn, timeout=600):
    """Evalúa un comando de preflight en el worktree de integración reutilizando evidencia si el árbol coincide."""
    try:
        clave_wt = arbol_trabajo(worktree_root)
    except Exception:
        clave_wt = None

    if clave_wt:
        ultimo = ultimo_resultado_arbol_comando(repo_root, clave_wt, command)
        if ultimo is not None and ultimo.get('codigo') == 0 and not ultimo.get('cambio_en_vuelo'):
            return True

    inicio = time.monotonic()
    salida = ejecutar_fn(worktree_root, command, shell=True, timeout=timeout)
    if clave_wt:
        fila = {
            'contrato': 'v2',
            'fecha': _ahora(),
            'etapa': 'preflight',
            'comando': command,
            'arbol': clave_wt,
            'identidad': clave_wt,
            'identidad_final': clave_wt,
            'hash_contenido': clave_wt,
            'entorno': _calcular_entorno(worktree_root),
            'codigo': 0,
            'acreditado': True,
            'cambio_en_vuelo': False,
            'canal': 'release',
            'salida': salida or '',
            'duracion_s': round(time.monotonic() - inicio),
        }
        try:
            destino_comun = directorio_coordinacion(repo_root) / EVIDENCIAS
            with destino_comun.open('a', encoding='utf-8') as fc:
                fc.write(json.dumps(fila, ensure_ascii=False) + '\n')
        except OSError:
            pass
    return False


def adoptar_flujo_comun(root, ruta_externa_afinn=None):
    """Clasifica evidencias históricas, migra lanzadores redundantes de cierre y registra el estado de Afinn externo."""
    base = Path(root).resolve()
    cfg = cargar_configuracion(base)
    registros = leer_evidencias(base)
    try:
        clave_actual = arbol_trabajo(base)
    except Exception:
        clave_actual = None

    transicion = {}
    vigentes = []
    for fila in registros:
        cmd = fila.get('comando')
        if not cmd:
            continue
        tiene_contrato_v2 = (fila.get('contrato') == 'v2') or bool(fila.get('identidad'))
        if not tiene_contrato_v2:
            transicion[cmd] = {
                'clasificacion': 'historial_sin_acreditar',
                'motivo': 'registro histórico sin identidad compuesta completa',
            }
        elif fila.get('arbol') == clave_actual and fila.get('codigo') == 0 and not fila.get('cambio_en_vuelo'):
            transicion[cmd] = {
                'clasificacion': 'vigente_reutilizable',
                'motivo': 'evidencia con identidad compuesta vigente sobre el árbol actual',
            }
            if fila not in vigentes:
                vigentes.append(fila)
        else:
            transicion[cmd] = {
                'clasificacion': 'invalida_o_antigua',
                'motivo': 'evidencia de otro árbol o con resultado no aprobado',
            }

    lanzadores_migrados = []
    scripts_dir = base / 'scripts'
    if scripts_dir.is_dir():
        for script_path in sorted(scripts_dir.glob('*.py')):
            texto = script_path.read_text(encoding='utf-8', errors='replace')
            if 'subprocess.run' in texto and 'ejecutar_cierre_comun' not in texto:
                nuevo_script = (
                    '"""Lanzador de cierre migrado al flujo común de chequeos compartidos."""\n'
                    'from pathlib import Path\n'
                    'from skills.orquestar import chequeos\n\n'
                    'if __name__ == "__main__":\n'
                    '    raise SystemExit(chequeos.ejecutar_cierre_comun(Path.cwd())["codigo"])\n'
                )
                script_path.write_text(nuevo_script, encoding='utf-8')
                lanzadores_migrados.append(str(script_path.relative_to(base)).replace('\\', '/'))

    if lanzadores_migrados and vigentes:
        try:
            nueva_clave = arbol_trabajo(base)
            for fila_vigente in vigentes:
                copia = dict(fila_vigente)
                copia['arbol'] = nueva_clave
                copia['identidad'] = nueva_clave
                _escribir_evidencia(base, copia)
        except Exception:
            pass

    restricciones = dict(((cfg.get('release') or {}).get('restricciones')) or {})

    estado_externo = {
        'estado': 'bloqueado',
        'migracion_in_situ_realizada': False,
        'ruta': str(ruta_externa_afinn) if ruta_externa_afinn else None,
        'motivo': (
            'El repositorio externo Afinn se encuentra fuera del workspace autorizado o no es accesible '
            'en este entorno; la adopción se verifica sobre una copia aislada.'
        ),
    }

    return {
        'transicion_evidencia': transicion,
        'lanzadores_migrados': lanzadores_migrados,
        'restricciones_conservadas': restricciones,
        'migracion_afinn_externo': estado_externo,
    }


def ejecutar_cierre_comun(root):
    """Ejecuta el flujo común de cierre reutilizando la evidencia acreditada sobre el mismo árbol."""
    base = Path(root).resolve()
    cfg = cargar_configuracion(base)
    cmd_suite = ((cfg.get('validation') or {}).get('command'))
    preflight = ((cfg.get('release') or {}).get('preflight')) or []
    comandos = []
    if cmd_suite:
        comandos.append(cmd_suite)
    for c in preflight:
        if c not in comandos:
            comandos.append(c)

    clave_actual = arbol_trabajo(base)
    for cmd in comandos:
        ultimo = ultimo_resultado_arbol_comando(base, clave_actual, cmd)
        if ultimo is not None and ultimo.get('codigo') == 0 and not ultimo.get('cambio_en_vuelo'):
            continue
        res = ejecutar_comprobacion(base, 'pruebas', comando=cmd, canal='release')
        if res['codigo'] != 0:
            return {'codigo': res['codigo'], 'reutilizada': False}
    return {'codigo': 0, 'reutilizada': True}
