"""Identidad operativa de versiones y acreditación de revisiones de cierre."""

import json
import re
from pathlib import Path

from adevv.yaml_lite import load_yaml


def clave_version(valor):
    """Devuelve mayor, menor y parche; la omisión del parche equivale a cero."""
    m = re.fullmatch(r'v?(\d+)\.(\d+)(?:\.(\d+))?', str(valor or '').strip())
    return (int(m[1]), int(m[2]), int(m[3] or 0)) if m else None


def nombre_version(clave):
    """Conserva parches positivos y la ruta histórica del parche cero."""
    return f'v{clave[0]}.{clave[1]}' + (f'.{clave[2]}' if clave[2] else '')


def motivo_revision(root, iid):
    """Diagnostica el informe canónico del ID; vacío significa revisión válida."""
    path = Path(root) / 'docs/review/code_reviews' / f'{iid}-code-review.md'
    try:
        texto = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return 'informe ausente'
    except (OSError, UnicodeError):
        return 'informe ilegible'
    lineas = [line.strip().replace('**', '') for line in texto.splitlines()]
    veredicto = ''
    for line in lineas:
        formal = re.match(r'^(?:[-#]+\s*)?Veredicto(?: final)?:\s*(?:✅\s*)?(APROBADO|RECHAZADO|N/A)(?=$|[\s.,;—(])', line, re.I)
        simple = re.fullmatch(r'(APROBADO|RECHAZADO|N/A)[.]?', line, re.I)
        if formal or simple:
            veredicto = (formal or simple)[1]
            break
    if veredicto.upper() == 'APROBADO':
        return ''
    if veredicto.upper() == 'RECHAZADO':
        return 'informe rechazado'
    if veredicto.upper() == 'N/A':
        if re.search(r'(?im)^\s*Motivo:\s*[^\n]*(?:sin cambios de c[oó]digo|sin c[oó]digo|no hay cambios de c[oó]digo)', texto):
            return ''
        return 'N/A sin justificación de ausencia de código'
    return 'informe sin veredicto formal'


def diagnostico_revision(root, iid):
    """Añade la última causa de cuota y la vía de recuperación sin invocar modelos."""
    motivo = motivo_revision(root, iid)
    if not motivo:
        return ''
    ultimo = None
    path = Path(root) / 'orquestar_metricas.jsonl'
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                dato = json.loads(line)
            except ValueError:
                continue
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
    master = (cfg.get('levels') or {}).get('master') or {}
    base = root / master.get('path', 'docs/plan/')
    folders = master.get('folders') or {}
    pendientes = []
    for tipo in ('tasks', 'bugs'):
        carpeta = base / folders.get(tipo, master.get(tipo, tipo + '/'))
        for path in sorted(carpeta.glob('*.md')):
            texto = path.read_text(encoding='utf-8')
            m = re.match(r'^---\s*\n(.*?)\n---', texto, re.S)
            fm = (load_yaml(m[1]) or {}) if m else {}
            if not fm.get('id') or fm.get('parent_id') or clave_version(fm.get('version')) != clave_version(version):
                continue
            iid, status = str(fm['id']), str(fm.get('status', '')).lower()
            if status == 'completed':
                mensaje = diagnostico_revision(root, iid)
                if mensaje:
                    pendientes.append(mensaje)
            elif status not in {'cancelled', 'superseded', 'rejected'}:
                pendientes.append(f'{iid}: trabajo pendiente ({status or "sin estado"}).')
    return pendientes
