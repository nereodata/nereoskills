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
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

HARNESS = {
    'claude': ['claude', '-p', '{prompt}', '--dangerously-skip-permissions', '--output-format', 'json'],
    'codex': ['codex', 'exec', '--full-auto', '--json', '{prompt}'],
    'gemini': ['gemini', '--yolo', '-p', '{prompt}'],
    'cursor': ['cursor-agent', '-p', '--force', '{prompt}'],
}
SKILL = Path(__file__).resolve().parent / 'SKILL.md'
AGENTES = Path(__file__).resolve().parents[2] / 'agents'
CONFIG = 'orchestration.json'  # roles: development, hades, clio, cronos → harness, model, effort
METRICAS = 'orquestar_metricas.jsonl'
EVIDENCIAS = 'orquestar_evidencias.jsonl'
LOG = 'orquestar.log'
PID = 'orquestar.pid'
PARADA = 'orquestar.parar'
ESPERA = 'orquestar.espera'
PROPIOS = (METRICAS, EVIDENCIAS, LOG, PID, PARADA, ESPERA)  # ficheros del bucle, excluidos de git
RESCATES = 2  # rescates máximos por tarea tras un bloqueo
CERRADO = {'completed', 'cancelled'}
FUERA = CERRADO | {'blocked'}  # no pendientes
PROMPT = ('Lee {skill} y ejecuta en modo orquestado el paso "{paso}"{args}. '
          'Las skills que cite (/nombre) están en {skills}/<nombre>/SKILL.md. '
          'No hagas preguntas: aplica las reglas del modo orquestado.')


def git(*args, env=None):
    r = subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8', env=env)
    return r.stdout.strip()


# ---------------------------------------------------------------- backlog y dependencias

def frontmatter(path):
    m = re.match(r'---\s*\n(.*?)\n---', path.read_text(encoding='utf-8'), re.S)
    if not m:
        return {}
    try:
        import yaml
        datos = yaml.safe_load(m[1])
        if isinstance(datos, dict):
            return {k: (v if isinstance(v, list) else '' if v is None else str(v)) for k, v in datos.items()}
    except Exception:
        pass
    pares = (l.split(':', 1) for l in m[1].splitlines() if ':' in l)
    return {k.strip(): v.strip().strip('"\'') for k, v in pares}


def lista(valor):
    """IDs de un campo de lista: `[A, B]`, `A, B` o una lista YAML."""
    if isinstance(valor, list):
        return [str(x).strip() for x in valor if str(x).strip()]
    return [x.strip().strip('"\'') for x in str(valor).strip('[] ').split(',') if x.strip().strip('"\'')]


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
    """Tareas y bugs maestros con su estado, versión, peso y dependencias (None si no las declara)."""
    out = []
    for tipo, d in zip(('task-dev', 'bug-fix'), backlog_dirs(root)):
        for f in sorted(d.glob('*.md')) if d.is_dir() else []:
            fm = frontmatter(f)
            if not fm.get('id') or fm.get('parent_id'):
                continue
            peso = str(fm.get('weight', ''))
            out.append({'paso': tipo, 'id': fm['id'], 'status': fm.get('status', 'backlog'),
                        'version': fm.get('version', ''),
                        'depende_de': lista(fm['depende_de']) if 'depende_de' in fm else None,
                        'weight': int(peso) if peso.lstrip('-').isdigit() else 0})
    return out


def errores_dependencias(items):
    """IDs inexistentes y ciclos en `depende_de`."""
    ids = {i['id'] for i in items}
    deps = {i['id']: i['depende_de'] or [] for i in items}
    errores = [f'{i} depende de {d}, que no existe' for i, ds in deps.items() for d in ds if d not in ids]
    visto, pila = set(), []

    def ciclo(n):
        if n in pila:
            return pila[pila.index(n):] + [n]
        if n in visto:
            return None
        visto.add(n)
        pila.append(n)
        for d in deps.get(n, []):
            c = ciclo(d) if d in ids else None
            if c:
                return c
        pila.pop()
        return None

    for n in deps:
        c = ciclo(n)
        if c:
            errores.append('ciclo: ' + ' → '.join(c))
            break
    return errores


def pendientes_de(i, por_id):
    """Dependencias de i que aún no están completadas."""
    return [d for d in i['depende_de'] or [] if d in por_id and por_id[d]['status'] != 'completed']


def raices(iid, por_id, visto=None):
    """Dependencias no completadas que ya no avanzan solas (bloqueadas, canceladas o fuera de versión)."""
    visto = visto if visto is not None else set()
    out = []
    for d in pendientes_de(por_id[iid], por_id):
        if d in visto:
            continue
        visto.add(d)
        dep = por_id[d]
        if dep['status'] in FUERA or pendientes_de(dep, por_id) == []:
            out.append(d)
        out += raices(d, por_id, visto)
    return sorted(set(out))


def desbloquea(items):
    """Cuántas tareas dependen, directa o indirectamente, de cada ID."""
    hijos = {i['id']: [] for i in items}
    for i in items:
        for d in i['depende_de'] or []:
            hijos.setdefault(d, []).append(i['id'])

    def alcance(n, visto):
        for h in hijos.get(n, []):
            if h not in visto:
                visto.add(h)
                alcance(h, visto)
        return visto

    return {n: len(alcance(n, set())) for n in hijos}


def en_espera(items):
    """Pendientes que esperan a otra tarea, con las dependencias que las retienen."""
    por_id = {i['id']: i for i in items}
    return {i['id']: pendientes_de(i, por_id) for i in items
            if i['status'] not in FUERA and pendientes_de(i, por_id)}


# ---------------------------------------------------------------- estado

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
    if any(i['paso'] == 'task-dev' and i['status'] not in CERRADO and i['depende_de'] is None for i in items):
        return ('PASO', 'calcular-dependencias', '', None)
    errores = errores_dependencias(items)
    if errores:
        return ('PARAR', 'Dependencias inválidas en el backlog: ' + '; '.join(errores))

    por_id = {i['id']: i for i in items}
    alcance = desbloquea(items)
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
        bloqueadas = sorted((i for i in suyas if i['status'] == 'blocked'), key=lambda i: -alcance.get(i['id'], 0))
        for i in bloqueadas:  # primero la causa raíz que más tareas retiene
            hechos, rescates = analisis(root, i['id'])
            if hechos == rescates and rescates < RESCATES:
                return ('PASO', 'analizar-bloqueo', i['id'], rama)
        pend = [i for i in suyas if i['status'] not in FUERA]
        elegibles = [i for i in pend if not pendientes_de(i, por_id)]
        if elegibles:
            i = min(elegibles, key=lambda i: (i['status'] != 'in_progress', -alcance.get(i['id'], 0), i['weight']))
            return ('PASO', i['paso'], i['id'], rama)
        if not (root / f'docs/review/versions/{v}-arquitectura.md').exists():
            return ('PASO', 'revisar-version', v, rama)
        if bloqueadas or pend:
            partes = ([f'bloqueadas {", ".join(i["id"] for i in bloqueadas)}'] if bloqueadas else []) + \
                     ([f'en espera {i["id"]} (por {", ".join(raices(i["id"], por_id))})' for i in pend])
            return ('PARAR', f'Bloqueos en {v}: ' + '; '.join(partes)
                             + f'. Revisa docs/review/versions/{v}-revision.md y docs/review/bloqueos/: '
                               'desbloquea, mueve de versión o cancela, y relanza.')
        return ('PARAR', f'Versión {v} terminada. Revisa docs/review/versions/{v}-revision.md'
                         ': registra defectos con /bug-add o cierra con /release, y relanza.')
    if not pendientes:
        mejoras = len(deuda(items))
        return ('FIN', 'Todas las tareas con versión están cerradas'
                       + (f'; quedan {mejoras} mejoras registradas como deuda.' if mejoras else '.'))
    v = min(vkey(i['version']) for i in pendientes)
    return ('PASO', 'start-version', f'v{v[0]}.{v[1]}', None)


def firma(root, docs):
    return (estado(root, docs), git('rev-parse', 'HEAD'), git('status', '--porcelain'),
            tuple((i['id'], i['status']) for i in backlog(root)))


# ---------------------------------------------------------------- arneses y roles

def config(root):
    """Roles del proyecto (orchestration.json): harness, model y effort por rol."""
    f = root / CONFIG
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}


def con_modelo(cmd, harness, rol):
    """Añade el modelo y el esfuerzo del rol, si no vienen ya en el comando."""
    cmd = list(cmd)
    if harness == 'claude' and '--model' not in cmd:
        cmd += (['--model', rol['model']] if rol.get('model') else []) + \
               (['--effort', rol['effort']] if rol.get('effort') else [])
    elif harness == 'codex' and '--model' not in cmd and '-m' not in cmd:
        i = cmd.index('exec') + 1
        cmd[i:i] = (['-m', rol['model']] if rol.get('model') else []) + \
                   (['-c', f'model_reasoning_effort="{rol["effort"]}"'] if rol.get('effort') else [])
    return cmd


def comando(a, prompt, root=None):
    plantilla = a.cmd.split() if a.cmd else HARNESS[a.harness]
    exe = shutil.which(plantilla[0])
    if not exe:
        sys.exit(f'No se encuentra el arnés "{plantilla[0]}" en el PATH.')
    cmd = [exe] + [p.replace('{prompt}', prompt) for p in plantilla[1:]]
    dev = config(root or Path.cwd()).get('development', {})
    if not a.cmd and dev.get('harness', a.harness) == a.harness:
        cmd = con_modelo(cmd, a.harness, dev)
    if a.presupuesto and json_claude(a):
        cmd += ['--max-budget-usd', str(a.presupuesto)]
    return cmd


def json_claude(a):
    return a.harness == 'claude' and not a.cmd


def lanzar(cmd, root, harness, entrada=None, env=None):
    """Ejecuta un arnés y devuelve (código, métricas, salida). Lee el uso de claude y codex."""
    inicio = time.monotonic()
    if harness == 'claude' and '--output-format' in cmd:
        r = subprocess.run(cmd, cwd=root, input=entrada, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', env=env)
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
    lineas, uso, turnos = [], {}, 0
    with subprocess.Popen(cmd, cwd=root, stdin=subprocess.PIPE if entrada else subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          encoding='utf-8', errors='replace', env=env) as p:
        if entrada:
            p.stdin.write(entrada)
            p.stdin.close()
        for linea in p.stdout:
            lineas.append(linea)
            evento = None
            if harness == 'codex' and linea.lstrip().startswith('{'):
                try:
                    evento = json.loads(linea)
                except ValueError:
                    pass
            if evento is None:
                print(linea, end='', flush=True)
            elif evento.get('type') == 'item.completed' and evento.get('item', {}).get('type') == 'agent_message':
                print(evento['item'].get('text', ''), flush=True)
            elif evento.get('type') == 'turn.completed':
                turnos += 1
                for k, v in (evento.get('usage') or {}).items():
                    uso[k] = uso.get(k, 0) + (v or 0)
            elif evento.get('type') in ('error', 'turn.failed'):
                print(json.dumps(evento, ensure_ascii=False), flush=True)
    m = {'duracion_s': round(time.monotonic() - inicio)}
    if uso:
        modelo = next((cmd[i + 1] for i, x in enumerate(cmd[:-1]) if x in ('-m', '--model')), 'codex')
        m.update(turnos=turnos, modelos={modelo: {
            'entrada': uso.get('input_tokens'), 'salida': uso.get('output_tokens'),
            'cache_leida': uso.get('cached_input_tokens'), 'cache_escrita': uso.get('cache_write_input_tokens'),
            'razonamiento': uso.get('reasoning_output_tokens')}})
    return p.returncode, m, ''.join(lineas[-200:])


def ejecutar(a, root, prompt, env=None):
    """Lanza el paso y devuelve (código, métricas, salida)."""
    return lanzar(comando(a, prompt, root), root, None if a.cmd else a.harness, env=env)


def agente(root, rol, prompt):
    """Lanza un rol (hades, clio, cronos…) con el arnés y el modelo de orchestration.json."""
    cfg = config(root).get(rol, {})
    harness = cfg.get('harness', 'claude')
    instrucciones = cfg.get('instructions') or os.path.relpath(AGENTES / f'{rol}.md', root).replace('\\', '/')
    prompt = (f'Lee {instrucciones} y actúa como ese agente; ignora el modelo de su frontmatter. '
              'Las skills están en ' + os.path.relpath(SKILL.parents[1], root).replace('\\', '/')
              + '/<nombre>/SKILL.md.\n\n' + prompt)
    if harness == 'claude':
        base = ['claude', '-p', '--dangerously-skip-permissions', '--output-format', 'json']
    elif harness == 'codex':
        base = ['codex', 'exec', '--ephemeral', '--json', '-c', 'approval_policy="never"',
                '--sandbox', 'workspace-write', '-']
    else:
        sys.exit(f'Arnés no soportado para roles: {harness}')
    exe = shutil.which(base[0])
    if not exe:
        sys.exit(f'No se encuentra el arnés "{base[0]}" en el PATH.')
    cmd = con_modelo([exe] + base[1:], harness, cfg)
    codigo, m, salida = lanzar(cmd, root, harness, entrada=prompt)
    registrar(root, {'tipo': 'agente', 'fecha': ahora(), 'rol': rol, 'paso': os.environ.get('ORQUESTAR_PASO', ''),
                     'id': os.environ.get('ORQUESTAR_ID', ''), 'arnes': harness, 'codigo': codigo, **m})
    return codigo


# ---------------------------------------------------------------- cuota

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


# ---------------------------------------------------------------- evidencia de verificación

def arbol(root):
    """Hash del contenido exacto del árbol de trabajo (incluye cambios sin commitear y no ignorados)."""
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(tmp) / 'index')}
        subprocess.run(['git', 'add', '-A', '.'], cwd=root, env=env, capture_output=True)
        return subprocess.run(['git', 'write-tree'], cwd=root, env=env, capture_output=True,
                              text=True).stdout.strip()


def suite(root, a=None):
    """Comando de la suite: --test o validation.command de task_config.yaml."""
    if a is not None and getattr(a, 'test', None):
        return a.test
    try:
        import yaml
        return (yaml.safe_load((root / 'task_config.yaml').read_text(encoding='utf-8')).get('validation')
                or {}).get('command')
    except Exception:
        return None


def verificar(root, cmd):
    """Ejecuta cmd sobre el árbol actual, o reutiliza su resultado en verde para ese mismo árbol."""
    excluir(root)
    clave = arbol(root)
    f = root / EVIDENCIAS
    previas = [json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip()] if f.exists() else []
    if any(e['arbol'] == clave and e['comando'] == cmd and e['codigo'] == 0 for e in previas):
        print(f'[orquestar] verificación reutilizada: {cmd} ya pasó sobre este mismo árbol ({clave[:10]}).')
        registrar(root, {'tipo': 'verificacion', 'fecha': ahora(), 'comando': cmd, 'arbol': clave,
                         'reutilizada': True, 'codigo': 0, 'id': os.environ.get('ORQUESTAR_ID', '')})
        return 0
    inicio = time.monotonic()
    codigo = subprocess.run(cmd, shell=True, cwd=root).returncode
    fila = {'fecha': ahora(), 'comando': cmd, 'arbol': clave, 'codigo': codigo,
            'duracion_s': round(time.monotonic() - inicio)}
    with f.open('a', encoding='utf-8') as out:
        out.write(json.dumps(fila, ensure_ascii=False) + '\n')
    registrar(root, {'tipo': 'verificacion', 'reutilizada': False, 'id': os.environ.get('ORQUESTAR_ID', ''), **fila})
    return codigo


# ---------------------------------------------------------------- ficheros del bucle y métricas

def ahora():
    return datetime.now().isoformat(timespec='seconds')


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
    """Añade una línea al registro común de métricas (pasos, agentes, esperas y verificaciones)."""
    excluir(root)
    fila.setdefault('tipo', 'paso')
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
    if not (root / METRICAS).exists():
        return
    filas = [json.loads(l) for l in (root / METRICAS).read_text(encoding='utf-8').splitlines() if l.strip()]
    tipo = lambda t: [f for f in filas if f.get('tipo', 'paso') == t]
    coste = sum(f.get('coste_usd') or 0 for f in filas)
    horas = sum(f.get('duracion_s') or 0 for f in tipo('paso') + tipo('espera')) / 3600
    verif = tipo('verificacion')
    print(f'[orquestar] {len(tipo("paso"))} pasos, {len(tipo("agente"))} ejecuciones de roles, '
          f'{len(tipo("espera"))} esperas de cuota, {len(verif)} verificaciones '
          f'({sum(1 for f in verif if f.get("reutilizada"))} reutilizadas); '
          f'{horas:.1f} h y {coste:.2f} USD a precio de lista (solo arneses que lo informan)')
    por_tarea = {}
    for f in filas:
        if f.get('id'):
            t = por_tarea.setdefault(f['id'], [0, 0])
            t[0] += f.get('duracion_s') or 0
            t[1] += f.get('coste_usd') or 0
    for iid, (seg, usd) in sorted(por_tarea.items(), key=lambda x: -x[1][0])[:5]:
        print(f'[orquestar]   {iid}: {seg / 60:.0f} min, {usd:.2f} USD')
    ultima = tipo('paso')[-1] if tipo('paso') else {}
    print(f'[orquestar] último paso: {ultima.get("paso", "")} {ultima.get("id", "")} ({ultima.get("fecha", "")})')


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


# ---------------------------------------------------------------- entrada

def main():
    ap = argparse.ArgumentParser(description='Orquestador: de la idea al producto, paso a paso.')
    ap.add_argument('--harness', choices=HARNESS, default=None,
                    help=f'arnés de desarrollo (por defecto, el de {CONFIG} o claude)')
    ap.add_argument('--cmd', help='plantilla propia del arnés, con {prompt} (sustituye a --harness)')
    ap.add_argument('--docs', default='docs/requirements', help='carpeta de requisitos y planes')
    ap.add_argument('--test', help='comando de la suite (por defecto, validation.command de task_config.yaml)')
    ap.add_argument('--idea', help='texto de la idea; crea <docs>/requirements.md si no existe')
    ap.add_argument('--max-pasos', type=int, default=100)
    ap.add_argument('--presupuesto', type=float, help='gasto máximo por paso en USD (solo claude)')
    ap.add_argument('--reintentos', type=int, default=2, help='pasos seguidos sin progreso antes de parar')
    ap.add_argument('--espera-max', type=float, default=12,
                    help='horas máximas esperando cuota seguidas antes de parar (0 = no esperar)')
    ap.add_argument('--estado', action='store_true', help='muestra el estado y el consumo, y sale')
    ap.add_argument('--fondo', action='store_true', help=f'lanza el bucle desacoplado, con la salida en {LOG}')
    ap.add_argument('--parar', action='store_true', help='pide al bucle en marcha que pare tras el paso en curso')
    ap.add_argument('--agente', metavar='ROL', help=f'lanza un rol (hades, clio, cronos) según {CONFIG}')
    ap.add_argument('--prompt-file', type=Path, help='mandato para --agente (si no, por la entrada estándar)')
    ap.add_argument('--verificar', nargs='?', const='suite', metavar='CMD',
                    help='ejecuta la suite (o CMD) o reutiliza su resultado en verde para el mismo árbol')
    a = ap.parse_args()
    root = Path.cwd()
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    a.harness = a.harness or config(root).get('development', {}).get('harness', 'claude')

    if a.agente:
        prompt = a.prompt_file.read_text(encoding='utf-8') if a.prompt_file else sys.stdin.read()
        if not prompt.strip():
            sys.exit('Falta el mandato: --prompt-file o entrada estándar.')
        return agente(root, a.agente, prompt)
    if a.verificar:
        cmd = suite(root, a) if a.verificar == 'suite' else a.verificar
        if not cmd:
            sys.exit('Sin suite: usa --test o define validation.command en task_config.yaml.')
        return verificar(root, cmd)
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

    script = os.path.relpath(Path(__file__).resolve(), root).replace('\\', '/')
    skill = os.path.relpath(SKILL, root).replace('\\', '/')
    extra = (f' Verifica con `python {script} --verificar` (suite completa, reutiliza la evidencia del mismo árbol)'
             f' o `--verificar "<comando de pruebas relevantes>"`.')
    if 'hades' in config(root):
        extra += f' Lanza las revisiones de Hades con `python {script} --agente hades --prompt-file <mandato>`.'
    cmd_suite = suite(root, a)
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
                               paso=paso, args=f' con "{arg}"' if arg else '') + extra
        env = {**os.environ, 'ORQUESTAR_PASO': paso, 'ORQUESTAR_ID': arg or ''}
        codigo, m, salida = ejecutar(a, root, prompt, env=env)
        cuota = espera_cuota(salida) if codigo else None
        registrar(root, {'fecha': ahora(), 'paso': paso, 'id': arg, 'rama': git('branch', '--show-current'),
                         'arnes': a.cmd or a.harness, 'codigo': codigo, **m,
                         **({'sin_cuota': True} if cuota else {})})
        if cuota is not None and esperado + cuota <= a.espera_max * 3600:
            esperado += cuota
            inicio = time.monotonic()
            seguir = esperar(root, cuota)
            registrar(root, {'tipo': 'espera', 'fecha': ahora(), 'paso': paso, 'id': arg,
                             'duracion_s': round(time.monotonic() - inicio)})
            if not seguir:
                print('[orquestar] PARAR: detenido a petición (--parar). Relanza para seguir.', flush=True)
                return 2
            continue
        if codigo:
            motivo = (f'sin cuota tras esperar {esperado // 3600} h (--espera-max)' if cuota is not None
                      else '¿autenticación, red?')
            print(f'[orquestar] PARAR: el arnés terminó con código {codigo} ({motivo}). Relanza cuando se resuelva.')
            return 2
        esperado = 0

        if cmd_suite and any(i['status'] in CERRADO and i['id'] not in cerradas for i in backlog(root)):
            if verificar(root, cmd_suite):
                print(f'[orquestar] PARAR: {arg} se ha cerrado pero la suite falla ({cmd_suite}).')
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
