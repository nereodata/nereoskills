"""Identidad operativa de versiones y acreditación de revisiones de cierre."""

import hashlib
import os
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


def huella_producto(root, arbol, carpetas, mandato_temporal=None):
    """Identifica rutas, modos y objetos Git del producto sin los documentos de seguimiento."""
    excluidos = tuple(p.relative_to(root).as_posix().encode() + b'/' for p in carpetas) + (b'docs/review/',)
    entradas = subprocess.check_output(['git', 'ls-tree', '-rz', '--full-tree', arbol], cwd=root)
    producto = hashlib.sha256()
    temporal = os.fsencode(mandato_temporal) if mandato_temporal is not None else None
    for entrada in entradas.split(b'\0'):
        ruta = entrada.partition(b'\t')[2]
        if entrada and ruta != temporal and not ruta.startswith(excluidos):
            producto.update(entrada + b'\0')
    return producto.hexdigest()


def lineas_del_informe(texto):
    """Conserva las declaraciones del informe fuera de citas y ejemplos de código."""
    lineas = texto.strip('\r\n').splitlines()
    cerco = r' {0,3}(`{3,}|~{3,})'
    def cierra(linea, marca):
        """CommonMark permite cerrar con el mismo signo y longitud igual o mayor."""
        return re.fullmatch(r' {0,3}' + marca + marca[0] + r'*[ \t]*', linea)

    if len(lineas) >= 3 and (inicio := re.fullmatch(cerco + r'(?:markdown|md)?\s*', lineas[0], re.I)):
        if cierra(lineas[-1], inicio[1]) and not any(cierra(l, inicio[1]) for l in lineas[1:-1]):
            lineas = lineas[1:-1]
    abierto = ''
    parrafo_citado = False
    citas_html = 0
    for linea in lineas:
        marca = re.match(cerco, linea)
        contenido = linea.strip()
        if abierto:
            if cierra(linea, abierto):
                abierto = ''
        elif citas_html or (contenido.startswith('<') and re.search(r'<blockquote\b', contenido, re.I)):
            for etiqueta in re.finditer(r'<(/?)blockquote\b[^>]*>', linea, re.I):
                citas_html = max(0, citas_html + (-1 if etiqueta[1] else 1))
            parrafo_citado = False
        elif marca:
            abierto = marca[1]
            parrafo_citado = False
        elif contenido.startswith('>'):
            parrafo_citado = bool(contenido.lstrip('> ').strip())
        elif parrafo_citado and contenido and not re.match(r' {0,3}(?:#{1,6}|[-+*]|\d+[.)])\s', linea):
            yield None
            continue
        else:
            parrafo_citado = False
            yield None if linea.startswith(('    ', '\t')) else contenido.replace('**', '')
            continue
        yield None


def declaracion(texto):
    """Lee el veredicto y la huella opcional que lo acompaña en la cabecera."""
    lineas = iter(lineas_del_informe(texto))
    for line in lineas:
        if not line:
            continue
        formal = re.match(r'^(?:[-#]+\s*)?Veredicto(?: final)?:\s*(?:✅\s*)?(APROBADO|RECHAZADO|N/A)(?=$|[\s.,;—(])', line, re.I)
        simple = re.fullmatch(r'(APROBADO|RECHAZADO|N/A)[.]?', line, re.I)
        if formal or simple:
            siguiente = next((l for l in lineas if l != ''), None)
            huella = re.fullmatch(r'Producto revisado:\s*(.*)', siguiente or '', re.I)
            return (formal or simple)[1].upper(), huella[1] if huella else None
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


def commit_del_intento(root, iid):
    """Recupera el último HEAD atribuido al ID que pertenece a la historia actual."""
    for fila in reversed(leer_registros(root, tolerar_ultima=True)):
        commit = fila.get('commit_producto')
        if (fila.get('tipo') == 'paso' and fila.get('id') == iid and isinstance(commit, str)
                and re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', commit)
                and subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'],
                                   cwd=root, capture_output=True).returncode == 0):
            return commit
    return None


def acreditacion_anterior(root, ruta, historial, actual):
    """Recupera la emisión y su huella a través de ediciones de seguimiento."""
    veredicto, huella = actual
    emision = None
    misma_emision = True
    for sha in historial:
        commit = sha.decode('ascii')
        blob = subprocess.run(['git', 'show', f'{commit}:{ruta}'], cwd=root, capture_output=True)
        if blob.returncode:
            misma_emision = False
            continue
        previo, anterior = declaracion(blob.stdout.decode('utf-8'))
        if previo == 'RECHAZADO':
            origen = (['rev-parse', f'{emision}:{ruta}'] if emision else ['hash-object', '--', ruta])
            objeto = subprocess.check_output(['git', *origen], cwd=root, text=True).strip()
            restaurado = subprocess.check_output(
                ['git', 'log', '-1', '--format=%H', f'--find-object={objeto}', commit, '--', ruta], cwd=root)
            return emision, huella, bool(restaurado.strip())
        misma_emision = misma_emision and previo == veredicto and (huella is None or anterior == huella)
        if misma_emision:
            emision = commit
            huella = anterior
    return emision, huella, False


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
        emision, huella, restaurado = acreditacion_anterior(root, ruta, historial, actual)
        if restaurado:
            return 'aprobación restaurada anterior al rechazo'
        if objetivo is None:
            cierre = subprocess.check_output(['git', 'log', '-1', '--format=%H', '-G',
                """^status:[[:space:]]*['"]?completed['"]?([[:space:]]|$)""", '--', ficha.relative_to(root).as_posix()],
                cwd=root, text=True).strip()
            objetivo = cierre or 'HEAD'
            referencia_informe = emision or (historial[0].decode('ascii') if historial else None)
            for posterior in (referencia_informe, commit_del_intento(root, iid)):
                if posterior and subprocess.run(['git', 'merge-base', '--is-ancestor', objetivo, posterior],
                                               cwd=root).returncode == 0:
                    objetivo = posterior
        if huella is not None:
            vigente = huella == huella_producto(root, objetivo, carpetas)
        elif emision:
            vigente = (emision == objetivo or
                       huella_producto(root, emision, carpetas) == huella_producto(root, objetivo, carpetas))
        else:
            vigente = not confirmar and not historial
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
        if any(re.match(r'Motivo:\s*.*(?:sin cambios de c[oó]digo|sin c[oó]digo|no hay cambios de c[oó]digo)',
                        linea or '', re.I) for linea in lineas_del_informe(texto)):
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
