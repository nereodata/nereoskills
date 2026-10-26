"""Cierre de releases confirmado por Telegram y publicación atómica."""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

def resumen(root, version):
    """Resume la revisión y conserva siempre la orden de confirmación."""
    path = root / f'docs/review/versions/{version}-revision.md'
    texto = path.read_text(encoding='utf-8') if path.exists() else 'Revisión de versión ausente.'
    categorias = []
    for nombre, patron in (('Tareas', r'^## .*'), ('Bloqueos', r'^.*bloque.*$'),
                           ('Validaciones funcionales', r'^.*validaci[oó]n funcional.*$')):
        filas = re.findall(patron, texto, re.MULTILINE | re.IGNORECASE)
        categorias.append(nombre + ':\n' + ('\n'.join(filas)[:850] or 'Sin entradas en la revisión.'))
    return '\n'.join(categorias) + f'\nPara cerrar: /cerrar {version} confirmo\n/estado · /lanzar'


def ejecutar(root, args, shell=False, timeout=120):
    """Ejecuta una operación no interactiva, acotada y con errores visibles."""
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'never',
           'GIT_MERGE_AUTOEDIT': 'no'}
    result = subprocess.run(args, cwd=root, env=env, shell=shell, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=timeout)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr).strip() or f'Error: {args}')
    return result.stdout.strip()


def git(root, *args):
    """Ejecuta Git en la raíz indicada."""
    return ejecutar(root, ['git', *args])


def validar(root, version, motor):
    """Rechaza toda precondición incumplida antes de preparar la publicación."""
    if not re.fullmatch(r'v\d+\.\d+', version):
        raise ValueError('Uso: /cerrar vX.Y [confirmo]')
    if (root / motor.PID).exists():
        raise ValueError('Existe un PID del bucle; espera su parada.')
    rama = 'release/' + version
    if git(root, 'branch', '--show-current') != rama:
        raise ValueError(f'La versión solicitada no coincide con la revisión final o la rama activa no es {rama}.')
    if (root / motor.PARADA).exists():
        raise ValueError('La parada no corresponde a revisión final: petición manual.')
    log = root / motor.LOG
    if log.exists():
        paradas = re.findall(r'\[orquestar\] PARAR: (.*)', log.read_text(encoding='utf-8', errors='replace'))
        if paradas and not paradas[-1].startswith(f'Versión {version} terminada.'):
            raise ValueError('La parada no corresponde a revisión final de la versión solicitada.')
    items = [i for i in motor.backlog(root) if motor.vkey(i['version']) == motor.vkey(version)]
    if not items:
        raise ValueError('No hay ítems de la versión solicitada.')
    for item in items:
        if item['status'] not in ('completed', 'cancelled'):
            motivo = 'bloqueo' if item['status'] == 'blocked' else 'trabajo pendiente'
            raise ValueError(f"{motivo}: {item['id']} ({item['status']}).")
    review = root / f'docs/review/versions/{version}-revision.md'
    if not review.exists():
        raise ValueError('Falta la revisión final de versión.')
    if not (root / f'docs/review/versions/{version}-arquitectura.md').exists():
        raise ValueError('Falta la revisión de arquitectura.')
    product = root / motor.PRODUCTO.format(v=version)
    decision = motor.decision_producto(product)
    if product.exists() and decision != 'APLICADA':
        raise ValueError('Falta aplicar las decisiones de producto.' if decision == 'APLICAR'
                         else 'Quedan decisiones de producto pendientes.')
    state = motor.estado(root, 'docs/requirements')
    if state[0] != 'PARAR' or not state[1].startswith(f'Versión {version} terminada.'):
        raise ValueError('La parada no corresponde a revisión final de la versión solicitada.')
    if git(root, 'status', '--porcelain'):
        raise ValueError('El árbol está sucio.')
    if motor.yaml is None:
        raise ValueError('No hay parser YAML disponible para validar el cierre.')
    config_path = root / 'task_config.yaml'
    cfg = (motor.yaml.safe_load(config_path.read_text(encoding='utf-8'))
           if hasattr(motor.yaml, 'safe_load') else motor.yaml.load_yaml(config_path))
    tag = str(cfg.get('project', {}).get('version', ''))
    tag = 'v' + tag.removeprefix('v')
    if not re.fullmatch(re.escape(version) + r'\.\d+', tag):
        raise ValueError('Versión del proyecto desalineada con la release.')
    scripts = Path(__file__).resolve().parents[1] / 'release/scripts'
    try:
        ejecutar(root, [sys.executable, str(scripts / 'check_manifests_versions.py'), '--dir', str(root)])
    except RuntimeError as error:
        raise ValueError(f'Versión desalineada del manifiesto: {error}') from error
    changelog = root / 'CHANGELOG.md'
    if not changelog.exists() or not re.search(r'^##\s+\[?v?' + re.escape(tag[1:]) + r'\]?(?:\s|$)', changelog.read_text(encoding='utf-8'), re.MULTILINE):
        raise ValueError('Falta el changelog de la versión.')
    if git(root, 'tag', '--list', tag):
        raise ValueError('La etiqueta local ya existe.')
    if git(root, 'ls-remote', '--tags', 'origin', f'refs/tags/{tag}'):
        raise ValueError('La etiqueta remota ya existe.')
    return rama, tag, cfg


def publicar(root, rama, tag, cfg):
    """Prepara en un worktree aislado y publica main y tag en una transacción."""
    original = git(root, 'rev-parse', 'refs/heads/main')
    release = git(root, 'rev-parse', rama)
    remoto = git(root, 'ls-remote', 'origin', 'refs/heads/main').split()
    if not remoto:
        raise ValueError('No existe main en el remoto.')
    git(root, 'fetch', '--no-tags', '--no-write-fetch-head', 'origin', remoto[0])
    published = False
    created_tag = False
    with tempfile.TemporaryDirectory(prefix='adevv-cierre-') as tmp:
        worktree = Path(tmp).resolve() / 'release'
        try:
            git(root, 'worktree', 'add', '--detach', str(worktree), original)
            git(worktree, 'merge', '--ff-only', remoto[0])
            git(worktree, 'merge', '--no-ff', release, '-m', f'chore(release): {tag}')
            timeout = (cfg.get('release') or {}).get('preflight_timeout', 600)
            if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout < float('inf'):
                raise ValueError('release.preflight_timeout debe ser positivo y finito (segundos).')
            for command in (cfg.get('release') or {}).get('preflight', []):
                try:
                    ejecutar(worktree, command, shell=True, timeout=timeout)
                except (RuntimeError, subprocess.TimeoutExpired) as error:
                    raise RuntimeError(f'Fallo de preflight: {error}') from error
            if git(worktree, 'status', '--porcelain'):
                raise RuntimeError('El preflight dejó el árbol sucio.')
            git(worktree, 'tag', '-a', tag, '-m', f'Release {tag}')
            created_tag = True
            commit = git(worktree, 'rev-parse', 'HEAD')
            git(worktree, 'push', '--atomic', 'origin', f'{commit}:refs/heads/main', f'refs/tags/{tag}:refs/tags/{tag}')
            published = True
        finally:
            if worktree.exists():
                git(root, 'worktree', 'remove', '--force', str(worktree))
            if created_tag and not published:
                git(root, 'tag', '-d', tag)
    try:
        git(root, 'update-ref', 'refs/heads/main', commit, original)
        git(root, 'checkout', 'main')
        git(root, 'branch', '-d', rama)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f'{tag} publicada; falta completar el cierre local: {error}') from error


def cerrar(root, argumento, motor):
    """Atiende una orden ya autorizada y diferencia publicación y relanzamiento."""
    partes = argumento.split()
    if not partes or len(partes) > 2 or (len(partes) == 2 and partes[1] != 'confirmo'):
        return 'Uso: /cerrar vX.Y [confirmo]'
    version = partes[0]
    if not re.fullmatch(r'v\d+\.\d+', version):
        return 'Uso: /cerrar vX.Y [confirmo]'
    if len(partes) == 1:
        return resumen(root, version)
    try:
        rama, tag, cfg = validar(root, version, motor)
        publicar(root, rama, tag, cfg)
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        return f'No se completó el cierre: {error}'
    pendientes = [i for i in motor.backlog(root) if i['status'] not in ('completed', 'cancelled') and motor.vkey(i['version'])]
    if not pendientes:
        return f'{tag} publicada. FIN: no quedan tareas con versión pendientes.'
    try:
        motor.en_fondo(root, argumentos=[])
    except (OSError, RuntimeError, SystemExit) as error:
        return f'{tag} publicada; relanzamiento pendiente: {error}. Reintenta con /lanzar.'
    return f'{tag} publicada. Lanzamiento solicitado en segundo plano.'
