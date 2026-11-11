"""Cierre de releases confirmado por Telegram y publicación atómica."""

import os
import re
import subprocess
from adevv import release_tools
from adevv.revisiones import pendientes_cierre, clave_version, nombre_version

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
    if not re.fullmatch(r'v\d+\.\d+(?:\.\d+)?', version):
        raise ValueError('Uso: /cerrar vX.Y [confirmo]')
    if motor.pid_vivo(root):
        raise ValueError('Existe un bucle vivo; espera su parada.')
    clave = clave_version(version)
    version = nombre_version(clave)
    rama = git(root, 'branch', '--show-current')
    if rama not in ('release/' + version, 'hotfix/' + version):
        raise ValueError(f'La versión solicitada no coincide con la revisión final o la rama activa no es release/{version} ni hotfix/{version}.')
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
    pendientes = pendientes_cierre(root, version)
    if pendientes:
        raise ValueError('Cierre pendiente de revisión:\n' + '\n'.join(pendientes))
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
    coordinador = release_tools._chequeos()
    for accion_req in ('validar', 'cerrar_local', 'etiquetar', 'publicar'):
        coordinador.verificar_restriccion_release(root, 'gateway', accion_req, cfg=cfg)
    tag = str(cfg.get('project', {}).get('version', ''))
    tag = 'v' + tag.removeprefix('v')
    if clave_version(tag) != clave or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Versión del proyecto desalineada con la release.')
    try:
        release_tools.validar_publicacion(root, tag, cfg=cfg)
    except release_tools.ReleaseValidationError as error:
        raise ValueError(f'Validación de manifiestos/publicación: {error}') from error
    return rama, tag, cfg


def publicar(root, rama, tag, cfg):
    """Publica con la transacción común y elimina la rama cerrada tras el éxito."""
    release_tools.publicar_version(root, tag, rama=rama, cfg=cfg)
    try:
        git(root, 'branch', '-d', rama)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f'{tag} publicada; falta completar el cierre local: {error}') from error


def cerrar(root, argumento, motor):
    """Atiende una orden ya autorizada y diferencia publicación y relanzamiento."""
    partes = argumento.split()
    if not partes or len(partes) > 2 or (len(partes) == 2 and partes[1] != 'confirmo'):
        return 'Uso: /cerrar vX.Y [confirmo]'
    version = partes[0]
    if not re.fullmatch(r'v\d+\.\d+(?:\.\d+)?', version):
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
