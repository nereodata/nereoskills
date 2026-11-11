"""Identidad operativa de versiones y acreditación de revisiones de cierre."""

import hashlib
import re
import subprocess
from pathlib import Path

from adevv.registro_metricas import leer_registros
from adevv.yaml_lite import load_yaml


def clave_version(valor):
    """Devuelve mayor, menor y parche; la omisión del parche equivale a cero."""
    m = re.fullmatch(r'v?(\d+)\.(\d+)(?:\.(\d+))?', str(valor or '').strip())
    return (int(m[1]), int(m[2]), int(m[3] or 0)) if m else None


def nombre_version(clave):
    """Conserva parches positivos y la ruta histórica del parche cero."""
    return f'v{clave[0]}.{clave[1]}' + (f'.{clave[2]}' if clave[2] else '')


def carpetas_maestras(root, cfg):
    """Directorios configurados de tareas y bugs maestros."""
    master = (cfg.get('levels') or {}).get('master') or {}
    base = root / master.get('path', 'docs/plan/')
    folders = master.get('folders') or {}
    return tuple(base / folders.get(tipo, master.get(tipo, tipo + '/')) for tipo in ('tasks', 'bugs'))


def huella_producto(root, arbol, carpetas):
    """Identifica rutas, modos y objetos Git del producto sin los documentos de seguimiento."""
    excluidos = tuple(p.relative_to(root).as_posix().encode() + b'/' for p in carpetas) + (b'docs/review/',)
    entradas = subprocess.check_output(['git', 'ls-tree', '-rz', '--full-tree', arbol], cwd=root)
    producto = hashlib.sha256()
    for entrada in entradas.split(b'\0'):
        if entrada and not entrada.split(b'\t', 1)[1].startswith(excluidos):
            producto.update(entrada + b'\0')
    return producto.hexdigest()


def declaracion(texto):
    """Extrae el primer veredicto formal y la huella de producto declarada por el revisor."""
    for line in texto.splitlines():
        line = line.strip().replace('**', '')
        formal = re.match(r'^(?:[-#]+\s*)?Veredicto(?: final)?:\s*(?:✅\s*)?(APROBADO|RECHAZADO|N/A)(?=$|[\s.,;—(])', line, re.I)
        simple = re.fullmatch(r'(APROBADO|RECHAZADO|N/A)[.]?', line, re.I)
        if formal or simple:
            huella = re.search(r'(?im)^Producto revisado:[ \t]*([^\r\n]*)$', texto)
            return (formal or simple)[1].upper(), huella[1].strip() if huella else None
    return '', None


def config_maestras(root):
    """Obtiene las carpetas para consultas independientes de la CLI."""
    path = root / 'task_config.yaml'
    cfg = load_yaml(path) if path.exists() else {}
    return carpetas_maestras(root, cfg or {})


def maestro_por_id(iid, carpetas):
    """Localiza una ficha histórica cuyo nombre de archivo puede diferir del ID."""
    for carpeta in carpetas:
        for path in carpeta.glob('*.md'):
            cabecera = re.match(r'^---\s*\n(.*?)\n---', path.read_text(encoding='utf-8'), re.S)
            if cabecera and (load_yaml(cabecera[1]) or {}).get('id') == iid:
                return path
    return None


def motivo_revision(root, iid, ficha=None, carpetas=None, objetivo=None):
    """Contrasta la aprobación con el producto del cierre del ID, también tras relanzar."""
    root = Path(root)
    informe = root / 'docs/review/code_reviews' / f'{iid}-code-review.md'
    motivo = motivo_informe(informe)
    if motivo or not (root / '.git').exists():
        return motivo
    carpetas = carpetas or config_maestras(root)
    ficha = ficha or maestro_por_id(iid, carpetas)
    if not ficha:
        return 'falta la ficha del producto revisado'
    ruta = informe.relative_to(root).as_posix()
    actual = declaracion(informe.read_text(encoding='utf-8'))
    confirmar = objetivo is not None
    try:
        historial = subprocess.check_output(['git', 'log', '--format=%H', '--', ruta], cwd=root).splitlines()
        emision = None
        for sha in historial:
            commit = sha.decode('ascii')
            blob = subprocess.run(['git', 'show', f'{commit}:{ruta}'], cwd=root, capture_output=True)
            if blob.returncode:
                break
            previo = declaracion(blob.stdout.decode('utf-8'))
            if previo[0] != actual[0] or (actual[1] is not None and previo[1] != actual[1]):
                break
            emision = commit
        if objetivo is None:
            cierre = subprocess.check_output(['git', 'log', '-1', '--format=%H', '-G',
                """^status:[[:space:]]*['"]?completed['"]?([[:space:]]|$)""", '--', ficha.relative_to(root).as_posix()],
                cwd=root, text=True).strip()
            objetivo = cierre or 'HEAD'
            if emision and subprocess.run(['git', 'merge-base', '--is-ancestor', objetivo, emision],
                                          cwd=root).returncode == 0:
                objetivo = emision
        if actual[1] is not None:
            vigente = actual[1] == huella_producto(root, objetivo, carpetas)
        elif emision:
            vigente = (emision == objetivo or
                       huella_producto(root, emision, carpetas) == huella_producto(root, objetivo, carpetas))
        else:
            vigente = not confirmar
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        return 'no se pudo acreditar el producto revisado'
    return '' if vigente else 'informe anterior al cambio de producto'


def motivo_informe(path):
    """Interpreta el dictamen formal de un informe de revisión."""
    try:
        texto = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return 'informe ausente'
    except (OSError, UnicodeError):
        return 'informe ilegible'
    veredicto, _ = declaracion(texto)
    if veredicto.upper() == 'APROBADO':
        return ''
    if veredicto.upper() == 'RECHAZADO':
        return 'informe rechazado'
    if veredicto.upper() == 'N/A':
        if re.search(r'(?im)^\s*Motivo:\s*[^\n]*(?:sin cambios de c[oó]digo|sin c[oó]digo|no hay cambios de c[oó]digo)', texto):
            return ''
        return 'N/A sin justificación de ausencia de código'
    return 'informe sin veredicto formal'


def diagnostico_revision(root, iid, ficha=None, carpetas=None):
    """Añade la última causa de cuota y la vía de recuperación sin invocar modelos."""
    motivo = motivo_revision(root, iid, ficha, carpetas)
    if not motivo:
        return ''
    ultimo = None
    for dato in leer_registros(root, tolerar_ultima=True):
        if dato.get('tipo') == 'agente' and dato.get('rol') == 'hades' and dato.get('id') == iid:
            ultimo = dato
    if ultimo and (ultimo.get('sin_cuota') or ultimo.get('cuota_espera_s')):
        motivo += '; Hades sin cuota: recuperar disponibilidad de Hades'
    return f'{iid}: {motivo}; obtener revisión con revisar-tarea y volver a validar el cierre.'


def pendientes_cierre(root, version, cfg=None):
    """Enumera maestros abiertos o completados sin revisión válida de este parche."""
    root = Path(root)
    if cfg is None:
        path = root / 'task_config.yaml'
        cfg = (load_yaml(path) or {}) if path.exists() else {}
    carpetas = carpetas_maestras(root, cfg)
    pendientes = []
    for carpeta in carpetas:
        for path in sorted(carpeta.glob('*.md')):
            texto = path.read_text(encoding='utf-8')
            m = re.match(r'^---\s*\n(.*?)\n---', texto, re.S)
            fm = (load_yaml(m[1]) or {}) if m else {}
            if not fm.get('id') or fm.get('parent_id') or clave_version(fm.get('version')) != clave_version(version):
                continue
            iid, status = str(fm['id']), str(fm.get('status', '')).lower()
            if status == 'completed':
                mensaje = diagnostico_revision(root, iid, path, carpetas)
                if mensaje:
                    pendientes.append(mensaje)
            elif status not in {'cancelled', 'superseded', 'rejected'}:
                pendientes.append(f'{iid}: trabajo pendiente ({status or "sin estado"}).')
    return pendientes
