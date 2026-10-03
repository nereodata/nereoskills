#!/usr/bin/env python3
"""Bucle del orquestador: deduce la fase del disco y lanza un arnés por paso.

El estado se calcula siempre a partir de artefactos (documentos, frontmatter del
backlog, ramas git), nunca de lo que el modelo diga que ha hecho.

Salida: 0 = producto terminado, 2 = parada para el humano, 1 = error.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HARNESS = {
    'claude': ['claude', '-p', '{prompt}', '--dangerously-skip-permissions', '--output-format', 'json'],
    'codex': ['codex', 'exec', '--full-auto', '{prompt}'],
    'gemini': ['gemini', '--yolo', '-p', '{prompt}'],
    'cursor': ['cursor-agent', '-p', '--force', '{prompt}'],
}
SKILL = Path(__file__).resolve().parent / 'SKILL.md'
METRICAS = 'orquestar_metricas.jsonl'
LOG = 'orquestar.log'
PID = 'orquestar.pid'
PARADA = 'orquestar.parar'
ESPERA = 'orquestar.espera'
PROPIOS = (METRICAS, LOG, PID, PARADA, ESPERA)  # ficheros del bucle, excluidos de git
RESCATES = 2  # rescates máximos por tarea tras un bloqueo
CERRADO = {'completed', 'cancelled'}
FUERA = CERRADO | {'blocked'}  # no pendientes
PROMPT = ('Lee {skill} y ejecuta en modo orquestado el paso "{paso}"{args}. '
          'Las skills que cite (/nombre) están en {skills}/<nombre>/SKILL.md. '
          'No hagas preguntas: aplica las reglas del modo orquestado.')


def git(*args):
    r = subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8')
    return r.stdout.strip()


def frontmatter(path):
    m = re.match(r'---\s*\n(.*?)\n---', path.read_text(encoding='utf-8'), re.S)
    if not m:
        return {}
    pares = (l.split(':', 1) for l in m[1].splitlines() if ':' in l)
    return {k.strip(): v.strip().strip('"\'') for k, v in pares}


def backlog_dirs(root):
    base, tareas, bugs = 'docs/plan/', 'tasks/', 'bugs/'
    try:
        import yaml
        m = yaml.safe_load((root / 'task_config.yaml').read_text(encoding='utf-8'))['levels']['master']
        base, tareas, bugs = m['path'], m['folders']['tasks'], m['folders']['bugs']
    except Exception:
        pass
    return root / base / tareas, root / base / bugs


def backlog(root):
    """Tareas y bugs maestros con su estado, versión y peso."""
    out = []
    for tipo, d in zip(('task-dev', 'bug-fix'), backlog_dirs(root)):
        for f in sorted(d.glob('*.md')) if d.is_dir() else []:
            fm = frontmatter(f)
            if not fm.get('id') or fm.get('parent_id'):
                continue
            peso = fm.get('weight', '')
            out.append({'paso': tipo, 'id': fm['id'], 'status': fm.get('status', 'backlog'),
                        'version': fm.get('version', ''), 'bloqueada_por': fm.get('bloqueada_por', ''),
                        'weight': int(peso) if peso.lstrip('-').isdigit() else 0})
    return out


def deuda(items):
    """Deuda registrada: bugs pendientes sin versión, fuera del bucle hasta que se incluyan."""
    return [i for i in items if i['paso'] == 'bug-fix' and i['status'] not in FUERA and not vkey(i['version'])]


def vkey(v):
    m = re.match(r'v?(\d+)\.(\d+)', v or '')
    return (int(m[1]), int(m[2])) if m else None


def primera_linea(path):
    lineas = path.read_text(encoding='utf-8').splitlines()
    return lineas[0] if lineas else ''


def revisada(root, iid):
    """Hades solo escribe el reporte de review-code si aprueba (o N/A sin código)."""
    d = root / 'docs/review/code_reviews'
    return d.is_dir() and any(d.glob(f'{iid}*'))


def analisis(root, iid):
    """(análisis de bloqueo hechos, cuántos acabaron en rescate) de un ID."""
    d = root / 'docs/review/bloqueos'
    hechos = sorted(d.glob(f'{iid}-*.md')) if d.is_dir() else []
    return len(hechos), sum('RESCATE' in primera_linea(f) for f in hechos)


def estado(root, docs):
    """Devuelve ('PASO', paso, arg, rama) | ('PARAR', motivo) | ('FIN', motivo)."""
    d = root / docs
    if not (root / 'task_config.yaml').exists():
        return ('PARAR', 'Falta task_config.yaml en la raíz del proyecto.')
    if not (d / 'requirements.md').exists():
        return ('PARAR', f'Falta la idea: escríbela en {docs}/requirements.md o usa --idea.')
    if not (d / 'req_analysis.md').exists():
        return ('PASO', 'ciclo-requisitos', '', None)
    if 'REQUIERE_ACLARACION' in primera_linea(d / 'req_analysis.md'):
        return ('PARAR', f'Requisitos con preguntas sin valor por defecto seguro: revisa {docs}/req_analysis.md.')
    if not (d / 'platform_plan.md').exists():
        return ('PASO', 'platform-plan', '', None)
    if not (d / 'platform_review.md').exists():
        return ('PASO', 'revisar-plataforma', '', None)
    if 'RECHAZADO' in primera_linea(d / 'platform_review.md'):
        return ('PARAR', f'Plataforma rechazada por Hades: revisa {docs}/platform_review.md.')
    items = backlog(root)
    if not (d / 'work_plan.md').exists() or not items:
        return ('PASO', 'work-plan', '', None)

    pendientes = [i for i in items if i['status'] not in FUERA and vkey(i['version'])]
    abiertas = [b.lstrip('* ').strip() for b in git('branch', '--list', 'release/v*').splitlines()]
    for rama in sorted(abiertas, key=lambda b: vkey(b.split('/')[1]) or (0, 0)):
        v = rama.split('/')[1]
        suyas = [i for i in items if vkey(i['version']) == vkey(v)]
        recien_abierta = all(i['status'] in ('backlog', 'planned') for i in suyas)
        if recien_abierta and deuda(items) and not (root / f'docs/review/versions/{v}-deuda.md').exists():
            return ('PASO', 'revisar-deuda', v, rama)
        sin_revisar = [i for i in suyas if i['status'] == 'completed' and not revisada(root, i['id'])]
        if sin_revisar:
            return ('PASO', 'revisar-tarea', sin_revisar[0]['id'], rama)
        for i in suyas:
            hechos, rescates = analisis(root, i['id'])
            if (i['status'] == 'blocked' and not i['bloqueada_por']
                    and hechos == rescates and rescates < RESCATES):
                return ('PASO', 'analizar-bloqueo', i['id'], rama)
        pend = [i for i in suyas if i['status'] not in FUERA]
        if pend:
            i = min(pend, key=lambda i: (i['status'] != 'in_progress', i['weight']))
            return ('PASO', i['paso'], i['id'], rama)
        if not (root / f'docs/review/versions/{v}-arquitectura.md').exists():
            return ('PASO', 'revisar-version', v, rama)
        bloqueadas = [i['id'] for i in suyas if i['status'] == 'blocked']
        return ('PARAR', f'Versión {v} terminada. Revisa docs/review/versions/{v}-revision.md'
                         + (f' (bloqueadas: {", ".join(bloqueadas)})' if bloqueadas else '')
                         + ': registra defectos con /bug-add o cierra con /release, y relanza.')
    if not pendientes:
        mejoras = len(deuda(items))
        return ('FIN', 'Todas las tareas con versión están cerradas'
                       + (f'; quedan {mejoras} mejoras registradas como deuda.' if mejoras else '.'))
    v = min(vkey(i['version']) for i in pendientes)
    return ('PASO', 'start-version', f'v{v[0]}.{v[1]}', None)


def firma(root, docs):
    return (estado(root, docs), git('rev-parse', 'HEAD'), git('status', '--porcelain'),
            tuple((i['id'], i['status']) for i in backlog(root)))


def comando(a, prompt):
    plantilla = a.cmd.split() if a.cmd else HARNESS[a.harness]
    exe = shutil.which(plantilla[0])
    if not exe:
        sys.exit(f'No se encuentra el arnés "{plantilla[0]}" en el PATH.')
    cmd = [exe] + [p.replace('{prompt}', prompt) for p in plantilla[1:]]
    if a.presupuesto and json_claude(a):
        cmd += ['--max-budget-usd', str(a.presupuesto)]
    return cmd


def json_claude(a):
    return a.harness == 'claude' and not a.cmd


def ejecutar(a, root, prompt):
    """Lanza el paso y devuelve (código, métricas, salida). Con claude, lee el JSON final."""
    inicio = time.monotonic()
    if not json_claude(a):
        lineas = []
        with subprocess.Popen(comando(a, prompt), cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, encoding='utf-8', errors='replace') as p:
            for linea in p.stdout:
                print(linea, end='', flush=True)
                lineas.append(linea)
        return p.returncode, {'duracion_s': round(time.monotonic() - inicio)}, ''.join(lineas[-200:])
    r = subprocess.run(comando(a, prompt), cwd=root, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    m = {'duracion_s': round(time.monotonic() - inicio)}
    salida = r.stdout + '\n' + r.stderr
    try:
        d = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        print(salida, flush=True)
        return r.returncode, m, salida
    print(d.get('result', ''), flush=True)
    m.update(turnos=d.get('num_turns'), coste_usd=d.get('total_cost_usd'),
             subagentes=(d.get('subagent_stats') or {}).get('spawned'), error=d.get('is_error'),
             modelos={k: {'entrada': u.get('inputTokens'), 'salida': u.get('outputTokens'),
                          'cache_leida': u.get('cacheReadInputTokens'),
                          'cache_escrita': u.get('cacheCreationInputTokens'), 'coste_usd': u.get('costUSD')}
                      for k, u in (d.get('modelUsage') or {}).items()})
    return (1 if d.get('is_error') and not r.returncode else r.returncode), m, salida


CUOTA = re.compile(r'usage limit|rate.?limit|quota|limit reached|hit your .{0,20}limit|too many requests'
                   r'|\b429\b|overloaded', re.I)


def espera_cuota(salida, ahora=None):
    """Segundos hasta poder reintentar si la salida indica falta de cuota; None si es otro error.

    Reconoce la hora de recuperación en los formatos habituales (marca de tiempo tras «|»,
    «try again in 2h 13m», «resets at 5pm»); si no la hay, propone 30 minutos.
    """
    if not CUOTA.search(salida):
        return None
    ahora = ahora or datetime.now()
    margen = 120
    m = re.search(r'\|(\d{10})\b', salida)
    if m:
        return max(int(m[1]) - int(ahora.timestamp()), 0) + margen
    m = re.search(r'(?:try again|retry|resets?) in\s+(?:(\d+)\s*(?:hours?|hrs?|h)\b)?\s*'
                  r'(?:(\d+)\s*(?:minutes?|mins?|m)\b)?', salida, re.I)
    if m and (m[1] or m[2]):
        return int(m[1] or 0) * 3600 + int(m[2] or 0) * 60 + margen
    m = re.search(r'(?:try again|resets?)\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', salida, re.I)
    if m:
        h = int(m[1]) % 12 + (12 if m[3].lower() == 'pm' else 0)
        objetivo = ahora.replace(hour=h, minute=int(m[2] or 0), second=0, microsecond=0)
        if objetivo <= ahora:
            objetivo += timedelta(days=1)
        return int((objetivo - ahora).total_seconds()) + margen
    return 1800


def esperar(root, segundos):
    """Duerme hasta la hora indicada, atento a --parar. Devuelve False si se pidió parar."""
    hasta = datetime.now() + timedelta(seconds=segundos)
    (root / ESPERA).write_text(hasta.isoformat(timespec='minutes'), encoding='utf-8')
    print(f'[orquestar] sin cuota: espero hasta las {hasta:%H:%M} y reintento el paso.', flush=True)
    try:
        while datetime.now() < hasta:
            if (root / PARADA).exists():
                return False
            time.sleep(min(30, max((hasta - datetime.now()).total_seconds(), 0)))
        return True
    finally:
        (root / ESPERA).unlink(missing_ok=True)


def excluir(root):
    """Excluye de git los ficheros del bucle, para no ensuciar el árbol."""
    exclude = Path(git('rev-parse', '--git-path', 'info/exclude'))
    exclude = exclude if exclude.is_absolute() else root / exclude
    actual = exclude.read_text(encoding='utf-8') if exclude.exists() else ''
    faltan = [f for f in PROPIOS if f not in actual.splitlines()]
    if faltan:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open('a', encoding='utf-8') as f:
            f.write('\n' + '\n'.join(faltan) + '\n')


def registrar(root, fila):
    """Añade una línea de métricas."""
    excluir(root)
    with (root / METRICAS).open('a', encoding='utf-8') as f:
        f.write(json.dumps(fila, ensure_ascii=False) + '\n')


def resumen(root):
    """Si hay un bucle en marcha y qué lleva consumido, según los ficheros del bucle."""
    if (root / PID).exists():
        print(f'[orquestar] en marcha (pid {(root / PID).read_text().strip()}); salida en {LOG}')
        if (root / ESPERA).exists():
            print(f'[orquestar] esperando cuota hasta {(root / ESPERA).read_text().strip()}')
    else:
        print('[orquestar] no hay ningún bucle en marcha')
    if (root / METRICAS).exists():
        filas = [json.loads(l) for l in (root / METRICAS).read_text(encoding='utf-8').splitlines() if l.strip()]
        coste = sum(f.get('coste_usd') or 0 for f in filas)
        ultima = filas[-1] if filas else {}
        print(f'[orquestar] {len(filas)} pasos registrados, {coste:.2f} USD a precio de lista; '
              f'último: {ultima.get("paso", "")} {ultima.get("id", "")} ({ultima.get("fecha", "")})')


def en_fondo(root):
    """Relanza el bucle desacoplado, con la salida en LOG, y vuelve enseguida."""
    if (root / PID).exists():
        sys.exit(f'Ya hay un bucle en marcha (pid {(root / PID).read_text().strip()}). '
                 f'Si no es así, borra {PID}.')
    excluir(root)
    args = [x for x in sys.argv[1:] if x != '--fondo']
    opciones = {'start_new_session': True}
    if os.name == 'nt':
        opciones = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW}
    with (root / LOG).open('a', encoding='utf-8') as log:
        p = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()), *args], cwd=root,
                             stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, **opciones)
    print(f'[orquestar] lanzado en segundo plano (pid {p.pid}); salida en {LOG}')
    return 0


def main():
    ap = argparse.ArgumentParser(description='Orquestador: de la idea al producto, paso a paso.')
    ap.add_argument('--harness', choices=HARNESS, default='claude')
    ap.add_argument('--cmd', help='plantilla propia del arnés, con {prompt} (sustituye a --harness)')
    ap.add_argument('--docs', default='docs/requirements', help='carpeta de requisitos y planes')
    ap.add_argument('--test', help='comando de la suite; debe pasar al cerrar cada tarea')
    ap.add_argument('--idea', help='texto de la idea; crea <docs>/requirements.md si no existe')
    ap.add_argument('--max-pasos', type=int, default=100)
    ap.add_argument('--presupuesto', type=float, help='gasto máximo por paso en USD (solo claude)')
    ap.add_argument('--reintentos', type=int, default=2, help='pasos seguidos sin progreso antes de parar')
    ap.add_argument('--espera-max', type=float, default=12,
                    help='horas máximas esperando cuota seguidas antes de parar (0 = no esperar)')
    ap.add_argument('--estado', action='store_true', help='muestra el estado y sale')
    ap.add_argument('--fondo', action='store_true', help=f'lanza el bucle desacoplado, con la salida en {LOG}')
    ap.add_argument('--parar', action='store_true', help='pide al bucle en marcha que pare tras el paso en curso')
    a = ap.parse_args()
    root = Path.cwd()
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    if a.parar:
        if not (root / PID).exists():
            print('[orquestar] no hay ningún bucle en marcha')
            return 0
        excluir(root)
        (root / PARADA).touch()
        print('[orquestar] parará al terminar el paso en curso')
        return 0
    if a.fondo:
        return en_fondo(root)
    if a.estado:
        resumen(root)
    elif (root / PID).exists():
        sys.exit(f'Ya hay un bucle en marcha (pid {(root / PID).read_text().strip()}). Si no es así, borra {PID}.')
    else:
        excluir(root)
        (root / PID).write_text(str(os.getpid()), encoding='utf-8')
    try:
        return bucle(a, root)
    finally:
        if not a.estado:
            for f in (PID, PARADA, ESPERA):
                (root / f).unlink(missing_ok=True)


def bucle(a, root):
    if a.idea and not (root / a.docs / 'requirements.md').exists():
        (root / a.docs).mkdir(parents=True, exist_ok=True)
        (root / a.docs / 'requirements.md').write_text(a.idea + '\n', encoding='utf-8')

    skill = os.path.relpath(SKILL, root).replace('\\', '/')
    sin_progreso = esperado = 0
    for n in range(1, a.max_pasos + 1):
        if (root / PARADA).exists():
            print('\n[orquestar] PARAR: detenido a petición (--parar). Relanza para seguir.', flush=True)
            return 2
        e = estado(root, a.docs)
        print(f'\n[orquestar] {n}. {e[0]}: ' + ' '.join(str(x) for x in e[1:] if x), flush=True)
        if a.estado or e[0] != 'PASO':
            return 0 if e[0] in ('FIN', 'PASO') else 2
        _, paso, arg, rama = e
        if rama and git('branch', '--show-current') != rama:
            if git('status', '--porcelain'):
                print(f'[orquestar] PARAR: cambios sin commitear; no puedo cambiar a {rama}.')
                return 2
            git('checkout', '-q', rama)

        antes = firma(root, a.docs)
        cerradas = {i['id'] for i in backlog(root) if i['status'] in CERRADO}
        prompt = PROMPT.format(skill=skill, skills=os.path.dirname(os.path.dirname(skill)) or '.',
                               paso=paso, args=f' con "{arg}"' if arg else '')
        codigo, m, salida = ejecutar(a, root, prompt)
        cuota = espera_cuota(salida) if codigo else None
        registrar(root, {'fecha': datetime.now().isoformat(timespec='seconds'), 'paso': paso, 'id': arg,
                         'rama': git('branch', '--show-current'), 'arnes': a.cmd or a.harness,
                         'codigo': codigo, **m, **({'sin_cuota': True} if cuota else {})})
        if cuota is not None and esperado + cuota <= a.espera_max * 3600:
            esperado += cuota
            if not esperar(root, cuota):
                print('[orquestar] PARAR: detenido a petición (--parar). Relanza para seguir.', flush=True)
                return 2
            continue
        if codigo:
            motivo = (f'sin cuota tras esperar {esperado // 3600} h (--espera-max)' if cuota is not None
                      else '¿autenticación, red?')
            print(f'[orquestar] PARAR: el arnés terminó con código {codigo} ({motivo}). Relanza cuando se resuelva.')
            return 2
        esperado = 0

        if a.test and any(i['status'] in CERRADO and i['id'] not in cerradas for i in backlog(root)):
            if subprocess.run(a.test, shell=True, cwd=root).returncode:
                print(f'[orquestar] PARAR: {arg} se ha cerrado pero la suite falla ({a.test}).')
                return 2
        if firma(root, a.docs) == antes:
            sin_progreso += 1
            print(f'[orquestar] sin progreso ({sin_progreso}/{a.reintentos})')
            if sin_progreso >= a.reintentos:
                print(f'[orquestar] PARAR: "{paso}" no avanza tras {a.reintentos} intentos.')
                return 2
        else:
            sin_progreso = 0
    print(f'[orquestar] PARAR: alcanzado --max-pasos={a.max_pasos}.')
    return 2


if __name__ == '__main__':
    sys.exit(main())
