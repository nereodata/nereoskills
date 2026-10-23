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
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    try:
        from adevv import yaml_lite as yaml
    except ImportError:
        yaml = None

HARNESS = {
    'claude': ['claude', '-p', '{prompt}', '--dangerously-skip-permissions', '--output-format', 'json'],
    'codex': ['codex', 'exec', '--full-auto', '--json', '{prompt}'],
    'gemini': ['gemini', '--yolo', '-p', '{prompt}'],
    'cursor': ['cursor-agent', '-p', '--force', '{prompt}'],
    'agy': ['agy', '-p', '{prompt}', '--dangerously-skip-permissions', '--output-format', 'json'],
}
SKILL = Path(__file__).resolve().parent / 'SKILL.md'
AGENTES = Path(__file__).resolve().parents[2] / 'agents'
CONFIG = 'orchestration.json'  # roles: atenea, artemisa, hades, clio, cronos → harness, model, effort
DESARROLLO = {'task-dev', 'bug-fix', 'revisar-tarea'}  # pasos de Artemisa; el resto (análisis y decisión), de Atenea
METRICAS = 'orquestar_metricas.jsonl'
EVIDENCIAS = 'orquestar_evidencias.jsonl'
LOG = 'orquestar.log'
PID = 'orquestar.pid'
PARADA = 'orquestar.parar'
ESPERA = 'orquestar.espera'
BUZON = 'orquestar_buzon.jsonl'  # tareas y bugs pedidos desde fuera (Telegram), por registrar
PROPIOS = (METRICAS, EVIDENCIAS, LOG, PID, PARADA, ESPERA, BUZON, BUZON + '.tmp', '.env')  # ficheros del bucle, excluidos de git
CERRADO = {'completed', 'cancelled'}
FUERA = CERRADO | {'blocked'}  # no pendientes
FIN_VERSION = ('Bloqueos en ', 'Versión ')  # paradas de una versión sin más tareas elegibles
PRODUCTO = 'docs/review/versions/{v}-producto.md'  # revisión funcional, con su tabla de decisiones
PROMPT = ('Lee {skill} y ejecuta en modo orquestado el paso "{paso}"{args}. '
          'Las skills que cite (/nombre) están en {skills}/<nombre>/SKILL.md. '
          'No hagas preguntas: aplica las reglas del modo orquestado.')


def git(*args, env=None):
    r = subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8', env=env)
    return r.stdout.strip()


def get_active_version_dir():
    """Retorna la ruta absoluta del directorio de la versión activa instalada o la raíz del repositorio."""
    try:
        from adevv.store import get_active_version_dir as _gavd
        return _gavd()
    except Exception:
        pass
    return Path(__file__).resolve().parents[2]


def es_repositorio_fuente_adevv(root):
    """Comprueba si el directorio raíz corresponde al repositorio de desarrollo de Adevv."""
    pyproject = Path(root) / "pyproject.toml"
    if pyproject.exists():
        try:
            txt = pyproject.read_text(encoding="utf-8")
            if 'name = "adevv"' in txt and (Path(root) / "adevv").is_dir():
                return True
        except Exception:
            pass
    return False


def es_carpeta_personal(path):
    """Comprueba si la ruta es la carpeta personal del usuario."""
    p = Path(path).resolve()
    sim = os.environ.get("ADEVV_SIMULATED_HOME")
    if sim and p == Path(sim).resolve():
        return True
    return p == Path.home().resolve()


def es_raiz_de_unidad(path):
    r"""Detecta si la ruta corresponde a la raíz de una unidad (ej. C:\ o /)."""
    p = Path(path).resolve()
    sim = os.environ.get("ADEVV_SIMULATED_DRIVE_ROOT")
    if sim and p == Path(sim).resolve():
        return True
    return p.parent == p


def construir_prompt_paso(root, paso, arg):
    """Construye el prompt de un paso para el arnés con rutas absolutas instaladas."""
    version_dir = get_active_version_dir()
    rol, cfg_rol = rol_de(root, paso)
    persona = version_dir / "agents" / f"{rol}.md"
    skill_file = version_dir / "skills" / "orquestar" / "SKILL.md"
    skills_dir = version_dir / "skills"

    instruccion_agente = (
        f'Lee "{persona.resolve()}" y actúa como ese agente; ignora el modelo de su frontmatter. '
        if persona.exists() else ""
    )
    args_str = f' con "{arg}"' if arg else ""
    prompt_cuerpo = (
        f'Lee "{skill_file.resolve()}" y ejecuta en modo orquestado el paso "{paso}"{args_str}. '
        f'Las skills que cite (/nombre) están en "{skills_dir.resolve()}/<nombre>/SKILL.md". '
        'No hagas preguntas: aplica las reglas del modo orquestado.'
    )
    extra = (
        ' Verifica con `adevv orquestar --verificar "<comando de pruebas>"` (reutiliza la evidencia del mismo árbol), '
        'solo con las pruebas que marque el triaje de la tarea: la suite completa la pasa el bucle al cerrar la versión.'
    )
    if config(root).get('hades') is not False:
        extra += ' Lanza las revisiones de Hades con `adevv orquestar --agente hades --prompt-file <mandato>`.'

    nota_fuente = ""
    if es_repositorio_fuente_adevv(root):
        nota_fuente = ' Los cambios se hacen en "skills/", "agents/" y "workflows/" del árbol de trabajo.'

    return instruccion_agente + prompt_cuerpo + extra + nota_fuente


def construir_prompt_agente(root, rol, prompt):
    """Construye el mandato para un rol con --agente citando la versión activa instalada."""
    version_dir = get_active_version_dir()
    paso = os.environ.get("ORQUESTAR_PASO", "")
    cfg = ajustes(config(root).get(rol, {}), paso)
    instrucciones = cfg.get("instructions")
    if instrucciones:
        p_inst = Path(instrucciones)
        if not p_inst.is_absolute():
            p_inst = (root / p_inst).resolve()
        instrucciones_str = str(p_inst)
    else:
        instrucciones_str = str((version_dir / "agents" / f"{rol}.md").resolve())

    skills_dir = (version_dir / "skills").resolve()
    cabecera = (
        f'Lee "{instrucciones_str}" y actúa como ese agente; ignora el modelo de su frontmatter. '
        f'Las skills están en "{skills_dir}/<nombre>/SKILL.md".\n\n'
    )
    if es_repositorio_fuente_adevv(root):
        cabecera += 'Los cambios se hacen en "skills/", "agents/" y "workflows/" del árbol de trabajo.\n\n'
    f_ev = Path(root) / EVIDENCIAS
    if f_ev.exists():
        try:
            clave = arbol(root)
            cmds = list(dict.fromkeys(
                e['comando'] for l in f_ev.read_text(encoding='utf-8').splitlines() if l.strip()
                for e in (json.loads(l),) if e.get('arbol') == clave and e.get('codigo') == 0
            ))
            if cmds:
                cabecera += (f'Verificado en verde sobre este árbol ({clave[:10]}): '
                             f'{", ".join(f"`{c}`" for c in cmds)}. No los relances.\n\n')
        except Exception:
            pass
    return cabecera + prompt


def validar_lanzamiento_bucle(root, a):
    """Valida precondiciones antes de lanzar el bucle e inicializa proyectos si procede."""
    # 1. Comprobar si estamos en subcarpeta de otro repo git
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            top_level = Path(r.stdout.strip()).resolve()
            if not os.path.samefile(top_level, root):
                sys.exit(f"Estás en una subcarpeta de {top_level}: lanza /orquestar desde la raíz.")
    except (FileNotFoundError, OSError):
        pass

    # 2. Inicialización de proyecto nuevo si procede
    if not (root / "task_config.yaml").exists():
        es_home = es_carpeta_personal(root)
        es_raiz = es_raiz_de_unidad(root)
        docs_dir = getattr(a, "docs", "docs/requirements") or "docs/requirements"
        reqs = root / docs_dir / "requirements.md"
        if not es_home and not es_raiz and reqs.exists():
            import unicodedata
            norm = unicodedata.normalize('NFD', root.name)
            sin_diacriticos = ''.join(c for c in norm if unicodedata.category(c) != 'Mn')
            letras = ''.join(c for c in sin_diacriticos if c.isalpha()).upper()
            prefijo = letras[:3] if len(letras) >= 3 else "PRJ"

            if not (root / ".git").is_dir():
                subprocess.run(["git", "init", "-q"], cwd=root, check=True)

            task_cfg_content = (
                f'project:\n  name: {root.name}\n  prefix: "{prefijo}"\n  version: "v0.0.0"\n\n'
                f'levels:\n  master:\n    path: docs/plan/\n    folders:\n      tasks: tasks/\n      bugs: bugs/\n'
                f'    tasks: tasks/\n    bugs: bugs/\n    id_prefix: "{prefijo}"\n'
            )
            (root / "task_config.yaml").write_text(task_cfg_content, encoding="utf-8")

            gitignore_path = root / ".gitignore"
            if not gitignore_path.exists():
                gitignore_path.write_text(
                    "orquestar.log\norquestar.pid\norquestar.parar\norquestar.espera\n"
                    "orquestar_metricas.jsonl\norquestar_evidencias.jsonl\norquestar_buzon.jsonl*\n"
                    ".env\n__pycache__/\n",
                    encoding="utf-8",
                )

            subprocess.run(["git", "add", "task_config.yaml", ".gitignore"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Adevv", "-c", "user.email=adevv@local", "commit", "-m", "chore: inicializar proyecto"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            print(f"[orquestar] inicializado repositorio Git y task_config.yaml (prefijo: {prefijo})", flush=True)

    # 3. Validar orchestration.json: instructions de cada rol
    cfg = config(root)
    for rol_k, rol_v in cfg.items():
        if isinstance(rol_v, dict) and "instructions" in rol_v:
            inst = rol_v["instructions"]
            p_inst = Path(inst)
            if not p_inst.is_absolute():
                p_inst = root / p_inst
            if not p_inst.exists():
                sys.exit(f"orchestration.json: {rol_k}.instructions apunta a {inst}, que no existe.")

    # 4. Validar submódulo .agents (solo en proyectos consumidores)
    if not es_repositorio_fuente_adevv(root):
        gitmodules = root / ".gitmodules"
        tiene_gm_agents = False
        if gitmodules.exists():
            try:
                tiene_gm_agents = ".agents" in gitmodules.read_text(encoding="utf-8")
            except Exception:
                pass
        if (root / ".agents").exists() or tiene_gm_agents:
            sys.exit("Este proyecto aún usa el submódulo .agents: sigue los pasos de migración del README.")

    # 5. Validar elementos locales que ocultan
    version_dir = get_active_version_dir()
    nombres_distribuidos = set()
    skills_dist = version_dir / "skills"
    if skills_dist.is_dir():
        for d in skills_dist.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                nombres_distribuidos.add(d.name)
    agents_dist = version_dir / "agents"
    if agents_dist.is_dir():
        for f in agents_dist.iterdir():
            if f.is_file() and f.suffix in (".md", ".toml"):
                nombres_distribuidos.add(f.stem)
        codex_dist = agents_dist / "codex"
        if codex_dist.is_dir():
            for f in codex_dist.iterdir():
                if f.is_file() and f.suffix == ".toml":
                    nombres_distribuidos.add(f.stem)
    wf_dist = version_dir / "workflows"
    if wf_dist.is_dir():
        for f in wf_dist.iterdir():
            if f.is_file() and f.suffix == ".md":
                nombres_distribuidos.add(f.stem)
    if "telegram_gateway" in nombres_distribuidos:
        nombres_distribuidos.add("telegram-gateway")

    rutas_ocultan = []
    rutas_candidatas = [
        (root / ".claude" / "skills", True),
        (root / ".claude" / "agents", False),
        (root / ".codex" / "skills", True),
        (root / ".codex" / "agents", False),
        (root / ".agents" / "skills", True),
        (root / ".agent" / "skills", True),
        (root / ".agent" / "workflows", False),
    ]
    for c_dir, es_dir in rutas_candidatas:
        if c_dir.exists():
            for item in c_dir.iterdir():
                nombre = item.name if es_dir else item.stem
                if nombre in nombres_distribuidos:
                    rutas_ocultan.append(os.path.relpath(item, root).replace("\\", "/"))

    if rutas_ocultan:
        sys.exit(
            f"Este proyecto tiene skills, agentes o workflows propios que ocultan los de Adevv: "
            f"{', '.join(sorted(rutas_ocultan))}. Bórralos o renómbralos."
        )


# ---------------------------------------------------------------- backlog y dependencias

def frontmatter(path):
    m = re.match(r'---\s*\n(.*?)\n---', path.read_text(encoding='utf-8'), re.S)
    if not m:
        return {}
    try:
        if yaml and hasattr(yaml, 'safe_load'):
            datos = yaml.safe_load(m[1])
        elif yaml and hasattr(yaml, 'load_yaml'):
            datos = yaml.load_yaml(m[1])
        else:
            datos = None
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
        if yaml and hasattr(yaml, 'safe_load'):
            m = yaml.safe_load((root / 'task_config.yaml').read_text(encoding='utf-8'))['levels']['master']
        elif yaml and hasattr(yaml, 'load_yaml'):
            m = yaml.load_yaml((root / 'task_config.yaml'))['levels']['master']
        else:
            m = {}
        folders = m.get('folders', {})
        base = m.get('path', 'docs/plan/')
        tareas = folders.get('tasks', m.get('tasks', 'tasks/'))
        bugs = folders.get('bugs', m.get('bugs', 'bugs/'))
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
                        'version': fm.get('version', ''), 'pendiente_de': str(fm.get('pendiente_de', '')).strip().lower(),
                        'depende_de': lista(fm['depende_de']) if 'depende_de' in fm else None,
                        'weight': int(peso) if peso.lstrip('-').isdigit() else 0})
    return out


def errores_dependencias(items):
    """IDs inexistentes, ciclos y dependencias a versiones posteriores."""
    ids = {i['id'] for i in items}
    deps = {i['id']: i['depende_de'] or [] for i in items}
    errores = [f'{i} depende de {d}, que no existe' for i, ds in deps.items() for d in ds if d not in ids]
    por_id = {i['id']: i for i in items}
    for i in items:
        version = vkey(i.get('version', ''))
        for d in deps[i['id']]:
            destino = vkey(por_id[d].get('version', '')) if d in por_id else None
            if version and destino and destino > version:
                errores.append(f"{i['id']} depende de {d}, de una versión posterior")
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


# ---------------------------------------------------------------- buzón: altas desde fuera del bucle

def prefijo(root):
    """Prefijo del proyecto en los IDs: `prefix` de task_config.yaml, el de los IDs existentes o PRJ."""
    try:
        m = re.search(r'^\s*prefix:\s*["\']?([A-Za-z0-9]+)', (root / 'task_config.yaml').read_text(encoding='utf-8'), re.M)
        if m:
            return m[1]
    except OSError:
        pass
    vistos = [m[1] for d in backlog_dirs(root) if d.is_dir() for f in d.glob('*.md')
              for m in [re.match(r'[TB]-([A-Za-z0-9]+)-\d+', f.name)] if m]
    return max(set(vistos), key=vistos.count) if vistos else 'PRJ'


def siguiente_id(root, letra):
    """Siguiente ID maestro libre (T- o B-) según los ficheros del backlog."""
    pre = f'{letra}-{prefijo(root)}-'
    d = backlog_dirs(root)[letra == 'B']
    nums = [int(m[1]) for f in (d.glob('*.md') if d.is_dir() else []) for m in [re.match(re.escape(pre) + r'(\d+)', f.name)] if m]
    return f'{pre}{max(nums, default=0) + 1:04d}'


def slug(texto):
    import unicodedata
    plano = ''.join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '-', plano.lower()).strip('-')[:60].strip('-')


def alta(root, tipo, titulo, autor=''):
    """Crea una tarea o un bug maestro sin versión (`backlog`): el bucle no lo trabaja hasta que alguien le pone versión.

    Las tareas van sin `depende_de`: se calculan cuando entren en una versión.
    """
    titulo = ' '.join(titulo.split())
    letra = 'B' if tipo == 'bug' else 'T'
    d = backlog_dirs(root)[letra == 'B']
    d.mkdir(parents=True, exist_ok=True)
    iid = siguiente_id(root, letra)
    hoy = datetime.now().strftime('%Y-%m-%d')
    origen = f'Telegram{f" (usuario {autor})" if autor else ""}, {hoy}'
    cabecera = (f'---\nid: {iid}\ntitle: {json.dumps(titulo, ensure_ascii=False)}\n'
                f'type: {"bug" if letra == "B" else "funcional"}\nweight: 100\nversion: ""\nstatus: backlog\n'
                f'created_at: {hoy}\nupdated_at: {hoy}\n---\n\n# {iid}: {titulo}\n\n')
    cuerpo = (f'## 🎯 Descripción del Fallo\n{titulo}\n\n## 📋 Reproducir\n1. Por detallar.\n\n'
              f'## 📋 Evidencias\n- Registrado desde {origen}.\n') if letra == 'B' else \
             (f'## 🎯 Objetivo de Negocio\n{titulo}\n\n## 📋 Criterios de Aceptación (Nivel Máster)\n'
              f'- [ ] **CA-M-1:** Por concretar (registrada desde {origen}).\n')
    f = d / (f'{iid}-{slug(titulo)}.md' if slug(titulo) else f'{iid}.md')
    f.write_text(cabecera + cuerpo, encoding='utf-8')
    return iid, f


def apuntar(root, tipo, titulo, autor=''):
    """Deja en el buzón una tarea o un bug pedido desde fuera; el bucle lo registra entre pasos."""
    excluir(root)
    with (root / BUZON).open('a', encoding='utf-8') as f:
        f.write(json.dumps({'tipo': tipo, 'titulo': titulo, 'autor': autor, 'fecha': ahora()}, ensure_ascii=False) + '\n')


def ingerir(root):
    """Registra el buzón en el backlog y commitea solo esos ficheros. Devuelve [(id, título)] registrados."""
    f, tmp = root / BUZON, root / (BUZON + '.tmp')
    try:
        if not tmp.exists():  # si existe, quedó de una ingesta interrumpida
            f.replace(tmp)
    except OSError:  # no hay buzón, o el gateway lo está escribiendo: a la siguiente
        return []
    hechos = []
    for linea in tmp.read_text(encoding='utf-8').splitlines():
        if linea.strip():
            e = json.loads(linea)
            iid, fichero = alta(root, e['tipo'], e['titulo'], e.get('autor', ''))
            hechos.append((iid, e['titulo'], fichero))
    if hechos:
        rutas = [str(x[2].relative_to(root)) for x in hechos]
        subprocess.run(['git', 'add', '--', *rutas], cwd=root, capture_output=True)
        subprocess.run(['git', 'commit', '-q', '-m', 'docs(plan): altas desde Telegram (' + ', '.join(x[0] for x in hechos) + ')',
                        '--', *rutas], cwd=root, capture_output=True)
    tmp.unlink()
    return [(iid, titulo) for iid, titulo, _ in hechos]


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


def producto_activa(root, v):
    """Revisión de producto al cerrar v según orchestration.json: `producto` true o lista de versiones."""
    cfg = config(root).get('producto')
    if isinstance(cfg, list):
        return vkey(v) in {vkey(str(x)) for x in cfg}
    return cfg is True


def decision_producto(informe):
    """PENDIENTE | APLICAR | APLICADA según la primera línea del informe ('' si no existe)."""
    m = re.search(r'Decisi[oó]n:\*\*\s*(\w+)', primera_linea(informe)) if informe.exists() else None
    return m[1].upper() if m else ''


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
    if any(i['paso'] == 'task-dev' and i['status'] not in CERRADO and i['depende_de'] is None and vkey(i['version'])
           for i in items):
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
            if i['pendiente_de'] == 'especificador':
                return ('PASO', 'especificar', i['id'], rama)
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
            return ('PARAR', f'{FIN_VERSION[0]}{v}: ' + '; '.join(partes)
                             + f'. Revisa docs/review/versions/{v}-revision.md: '
                               'responde a las preguntas de las bloqueadas, mueve de versión o cancela, y relanza.')
        informe = root / PRODUCTO.format(v=v)
        if producto_activa(root, v) and not informe.exists():
            return ('PASO', 'revisar-producto', v, rama)
        if decision_producto(informe) == 'APLICAR':
            return ('PASO', 'aplicar-producto', v, rama)
        if decision_producto(informe) == 'PENDIENTE':
            return ('PARAR', f'{FIN_VERSION[1]}{v} terminada. Revisa docs/review/versions/{v}-revision.md y decide '
                             f'las propuestas de {PRODUCTO.format(v=v)}: ajusta destinos, marca APLICAR y relanza '
                             '(el bucle crea las tareas); registra defectos con /bug-add o cierra con /release.')
        return ('PARAR', f'{FIN_VERSION[1]}{v} terminada. Revisa docs/review/versions/{v}-revision.md'
                         ': registra defectos con /bug-add o cierra con /release, y relanza.')
    versiones = root / 'docs/review/versions'
    for informe in sorted(versiones.glob('*-producto.md')) if versiones.is_dir() else []:
        v = informe.name.split('-')[0]
        if decision_producto(informe) == 'APLICAR':
            return ('PASO', 'aplicar-producto', v, None)
        if decision_producto(informe) == 'PENDIENTE':
            return ('PARAR', f'Decisiones de producto pendientes en {PRODUCTO.format(v=v)}: ajusta destinos, '
                             'marca APLICAR y relanza. No abro otra versión hasta entonces.')
    if not pendientes:
        mejoras = len(deuda(items))
        return ('FIN', 'Todas las tareas con versión están cerradas'
                       + (f'; quedan {mejoras} mejoras registradas como deuda.' if mejoras else '.'))
    v = min(vkey(i['version']) for i in pendientes)
    return ('PASO', 'start-version', f'v{v[0]}.{v[1]}', None)


def firma(root, docs):
    return (estado(root, docs), git('rev-parse', 'HEAD'), git('status', '--porcelain'),
            tuple((i['id'], i['status']) for i in backlog(root)), arbol(root))


# ---------------------------------------------------------------- arneses y roles

def config(root):
    """Roles del proyecto (orchestration.json): harness, model y effort por rol."""
    f = root / CONFIG
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}


def rol_de(root, paso):
    """(rol, configuración) que ejecuta un paso del bucle: Artemisa desarrolla, Atenea analiza y decide.

    Sin la clave del rol en orchestration.json se usa `development` (y Atenea, sin ella, la de Artemisa).
    """
    cfg = config(root)
    dev = cfg.get('artemisa') or cfg.get('development', {})
    rol = 'artemisa' if paso in DESARROLLO else 'atenea'
    return rol, ajustes(dev if rol == 'artemisa' else cfg.get('atenea') or dev, paso)


def ajustes(cfg, paso):
    """Configuración del rol para un paso: la base más lo que fije `pasos.<paso>` (p. ej. otro `effort`)."""
    return {**{k: v for k, v in cfg.items() if k != 'pasos'}, **(cfg.get('pasos') or {}).get(paso, {})}


def rechazos(root, iid):
    """Veredictos RECHAZADO seguidos de Hades sobre un ID, contados desde su último APROBADO."""
    n = 0
    if iid and (root / METRICAS).exists():
        for linea in (root / METRICAS).read_text(encoding='utf-8').splitlines():
            f = json.loads(linea) if linea.strip() else {}
            if f.get('tipo') == 'agente' and f.get('rol') == 'hades' and f.get('id') == iid and f.get('veredicto'):
                n = n + 1 if f['veredicto'] == 'RECHAZADO' else 0
    return n


def escalada(root, rol, cfg, iid):
    """(configuración, escalado): Artemisa sube a `escalada` tras `escalada.rechazos` rechazos seguidos de Hades."""
    esc = cfg.get('escalada') or {}
    if rol != 'artemisa' or not esc or rechazos(root, iid) < esc.get('rechazos', 2):
        return cfg, False
    return {**{k: v for k, v in cfg.items() if k != 'escalada'},
            **{k: v for k, v in esc.items() if k != 'rechazos'}}, True


def con_modelo(cmd, harness, rol):
    """Añade el modelo y el esfuerzo del rol, si no vienen ya en el comando."""
    cmd = list(cmd)
    if harness == 'claude' and '--model' not in cmd:
        cmd += (['--model', rol['model']] if rol.get('model') else []) + \
               (['--effort', rol['effort']] if rol.get('effort') else [])
    elif harness in ('gemini', 'agy') and '--model' not in cmd and '-m' not in cmd:
        cmd += (['--model', rol['model']] if rol.get('model') else []) + \
               (['--effort', rol['effort']] if harness == 'agy' and rol.get('effort') else [])
    elif harness == 'codex' and '--model' not in cmd and '-m' not in cmd:
        i = cmd.index('exec') + 1
        cmd[i:i] = (['-m', rol['model']] if rol.get('model') else []) + \
                   (['-c', f'model_reasoning_effort="{rol["effort"]}"'] if rol.get('effort') else [])
    return cmd


def arnes(a, rol):
    """Arnés de un paso: --harness o el de su rol (claude por defecto); None con --cmd."""
    return None if a.cmd else a.harness or rol.get('harness', 'claude')


def comando(a, prompt, root=None, rol=None):
    rol = rol if rol is not None else rol_de(root or Path.cwd(), 'task-dev')[1]
    harness = arnes(a, rol)
    plantilla = (shlex.split(a.cmd, posix=os.name != 'nt') if a.cmd else HARNESS[harness])
    plantilla = [p.strip('"\'') for p in plantilla]
    exe = shutil.which(plantilla[0])
    if not exe:
        sys.exit(f'No se encuentra el arnés "{plantilla[0]}" en el PATH.')
    cmd = [exe] + [p.replace('{prompt}', prompt) for p in plantilla[1:]]
    if harness and rol.get('harness', harness) == harness:
        cmd = con_modelo(cmd, harness, rol)
    if a.presupuesto and harness == 'claude':
        cmd += ['--max-budget-usd', str(a.presupuesto)]
    return cmd


def lanzar(cmd, root, harness, entrada=None, env=None):
    """Ejecuta un arnés y devuelve (código, métricas, salida). Lee el uso de claude, agy y codex."""
    inicio = time.monotonic()
    if harness == 'agy' and '--output-format' in cmd:
        r = subprocess.run(cmd, cwd=root, input=entrada, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', env=env)
        m = {'duracion_s': round(time.monotonic() - inicio)}
        salida = r.stdout + '\n' + r.stderr
        try:
            d = json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            print(salida, flush=True)
            return r.returncode, m, salida
        print(d.get('response', ''), flush=True)
        u = d.get('usage') or {}
        modelo = next((cmd[i + 1] for i, x in enumerate(cmd[:-1]) if x == '--model'), 'agy')
        if d.get('status') != 'SUCCESS':
            print(f"[orquestar] agy status: {d.get('status')} (returncode: {r.returncode})", flush=True)
        m.update(turnos=d.get('num_turns'), error=d.get('status') != 'SUCCESS',
                 modelos={modelo: {'entrada': u.get('input_tokens'), 'salida': u.get('output_tokens'),
                                   'cache_leida': u.get('cache_read_tokens'),
                                   'razonamiento': u.get('thinking_tokens')}})
        return (1 if m['error'] and not r.returncode else r.returncode), m, salida
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


def ejecutar(a, root, prompt, env=None, rol=None):
    """Lanza el paso con el arnés y el modelo de su rol y devuelve (código, métricas, salida)."""
    rol = rol if rol is not None else rol_de(root, 'task-dev')[1]
    return lanzar(comando(a, prompt, root, rol), root, arnes(a, rol), env=env)


def agente(root, rol, prompt):
    """Lanza un rol (hades, clio, cronos…) con el arnés y el modelo de orchestration.json."""
    paso, iid = os.environ.get('ORQUESTAR_PASO', ''), os.environ.get('ORQUESTAR_ID', '')
    cfg = ajustes(config(root).get(rol, {}), paso)
    if 'instructions' in cfg:
        p_inst = Path(cfg['instructions'])
        if not p_inst.is_absolute():
            p_inst = root / p_inst
        if not p_inst.exists():
            sys.exit(f"orchestration.json: {rol}.instructions apunta a {cfg['instructions']}, que no existe.")
    harness = cfg.get('harness', 'claude')
    prompt = construir_prompt_agente(root, rol, prompt)
    if harness == 'claude':
        base = ['claude', '-p', '--dangerously-skip-permissions', '--output-format', 'json']
    elif harness == 'codex':
        base = ['codex', 'exec', '--ephemeral', '--json', '-c', 'approval_policy="never"',
                '--sandbox', 'workspace-write', '-']
    elif harness == 'agy':
        base = ['agy', '--dangerously-skip-permissions', '--output-format', 'json', '-p', prompt]
    else:
        sys.exit(f'Arnés no soportado para roles: {harness}')
    exe = shutil.which(base[0])
    if not exe:
        sys.exit(f'No se encuentra el arnés "{base[0]}" en el PATH.')
    cmd = con_modelo([exe] + base[1:], harness, cfg)
    codigo, m, salida = lanzar(cmd, root, harness, entrada=prompt)
    cuota = espera_cuota(salida) if codigo else None
    veredicto = re.findall(r'Veredicto\W{0,6}(APROBADO|RECHAZADO)', salida) if rol == 'hades' else []
    registrar(root, {'tipo': 'agente', 'fecha': ahora(), 'rol': rol, 'paso': paso, 'id': iid, 'arnes': harness,
                     'codigo': codigo, **({'veredicto': veredicto[-1]} if veredicto else {}),
                     **({'sin_cuota': True, 'espera_s': cuota} if cuota is not None else {}), **m})
    if cuota is not None:
        print(f'[orquestar] {rol} sin cuota: termina el paso ahora mismo sin tocar estados; '
              'el bucle esperará la cuota y reintentará.', flush=True)
    elif veredicto and veredicto[-1] == 'RECHAZADO':
        print(tope_de_rechazos(root, iid), flush=True)
    return codigo


def tope_de_rechazos(root, iid):
    """Instrucción para Artemisa al llegar al tope de rechazos seguidos; '' si aún no ha llegado."""
    esc = rol_de(root, 'task-dev')[1].get('escalada') or {}
    tope, n = (esc.get('rechazos', 2) if esc else 3), rechazos(root, iid)
    if n < tope or n % tope:
        return ''
    if not esc or os.environ.get('ORQUESTAR_ESCALADA'):
        tras = ', también tras la escalada' if esc else ''
        return (f'[orquestar] Hades ha rechazado {iid} {n} veces seguidas{tras}: '
                'no sigas corrigiendo; aplica la regla 5 del modo orquestado (bloquea la tarea con '
                '`pendiente_de: especificador`, o `humano` si falta un recurso externo) y termina el paso.')
    return (f'[orquestar] Hades ha rechazado {iid} {n} veces seguidas: no sigas corrigiendo. Commitea lo que '
            'tengas en la rama, explica en tu salida qué falla y termina el paso sin cambiar estados: el bucle '
            'relanzará la tarea con un modelo superior.')


# ---------------------------------------------------------------- cuota

CUOTA = re.compile(r'usage limit|rate.?limit|quota|limit reached|hit your .{0,20}limit|too many requests'
                   r'|\b429\b|overloaded|out of credits|credit balance|insufficient_quota|billing_hard_limit', re.I)


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


# ---------------------------------------------------------------- avisos por Telegram

EVENTOS = ('version', 'cuota', 'respuesta', 'error')  # fin de versión/producto, sin cuota, te toca, fallo


def leer_env(ruta):
    """Lee un fichero clave=valor (.env) sin dependencias externas."""
    valores = {}
    p = Path(ruta)
    if p.is_file():
        try:
            for linea in p.read_text(encoding='utf-8', errors='replace').splitlines():
                linea = linea.strip()
                if not linea or linea.startswith('#'):
                    continue
                if '=' in linea:
                    k, _, v = linea.partition('=')
                    k, v = k.strip(), v.strip()
                    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
                        v = v[1:-1]
                    valores[k] = v
        except OSError:
            pass
    return valores


def credenciales(root=None):
    """(token, usuarios autorizados) de .env (en root o CWD) o del entorno de ejecución."""
    base = Path(root) if root else Path.cwd()
    env = leer_env(base / '.env')
    token = env.get('TELEGRAM_BOT_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN', '')
    raw_usr = env.get('TELEGRAM_ALLOWED_USER_IDS') or os.environ.get('TELEGRAM_ALLOWED_USER_IDS', '')
    usuarios = [u.strip() for u in str(raw_usr).split(',') if u.strip()]
    return token.strip(), usuarios


def telegram(root):
    """(token, usuarios, eventos) para los avisos; None sin credenciales o con `"telegram": false`.

    Los avisos van a los mismos usuarios que atiende el gateway. La clave `telegram` de orchestration.json
    solo elige los eventos (`{"eventos": [...]}`); sin ella se avisan todos.
    """
    cfg = config(root).get('telegram', {})
    token, usuarios = credenciales(root)
    if cfg is False or not token or not usuarios:
        return None
    return token, usuarios, set((cfg if isinstance(cfg, dict) else {}).get('eventos') or EVENTOS)


def enviar(token, chat, texto, markdown=False):
    """Envía un mensaje; si Telegram rechaza el Markdown, lo reintenta en texto plano. Nunca lanza."""
    import urllib.parse
    import urllib.request
    error = None
    for modo in ('Markdown', None) if markdown else (None,):
        campos = {'chat_id': chat, 'text': texto, 'disable_web_page_preview': 'true', **({'parse_mode': modo} if modo else {})}
        try:
            with urllib.request.urlopen(f'https://api.telegram.org/bot{token}/sendMessage',
                                        urllib.parse.urlencode(campos).encode(), timeout=15) as r:
                return r.status == 200
        except Exception as ex:  # sin red, token malo…: se informa y se sigue
            error = ex
            if not (modo and getattr(ex, 'code', None) == 400):
                break
    print(f'[orquestar] mensaje de Telegram no enviado ({type(error).__name__})', flush=True)
    return False


def avisar(root, evento, texto):
    """Envía el aviso a los usuarios autorizados si el evento está activo (None: siempre). Un fallo nunca para el bucle."""
    cfg = telegram(root)
    if not cfg or (evento and evento not in cfg[2]):
        return False
    token, usuarios, _ = cfg
    return all([enviar(token, u, f'[{root.name}] {texto}') for u in usuarios])


def parar(root, evento, texto):
    """Para el bucle para el humano: lo escribe en la salida y lo avisa."""
    print(f'[orquestar] PARAR: {texto}', flush=True)
    avisar(root, evento, f'⏸ {texto}')
    return 2


def evento_de(e):
    """Evento de aviso de un estado final: cierre de versión o producto terminado, o respuesta del humano."""
    return 'version' if e[0] == 'FIN' or cierre_de_version(e) else 'respuesta'


# ---------------------------------------------------------------- evidencia de verificación

def arbol(root):
    """Hash del contenido exacto del árbol de trabajo (incluye cambios sin commitear y no ignorados)."""
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(tmp) / 'index')}
        subprocess.run(['git', 'add', '-A', '.'], cwd=root, env=env, capture_output=True, check=True)
        valor = subprocess.run(['git', 'write-tree'], cwd=root, env=env, capture_output=True,
                               text=True, check=True).stdout.strip()
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', valor):
            raise RuntimeError('No se pudo calcular una huella Git válida del árbol')
        return valor


def suite(root, a=None):
    """Comando de la suite: --test o validation.command de task_config.yaml."""
    if a is not None and getattr(a, 'test', None):
        return a.test
    try:
        if yaml and hasattr(yaml, 'safe_load'):
            cfg = yaml.safe_load((root / 'task_config.yaml').read_text(encoding='utf-8'))
        elif yaml and hasattr(yaml, 'load_yaml'):
            cfg = yaml.load_yaml((root / 'task_config.yaml'))
        else:
            cfg = {}
        return (cfg.get('validation') or {}).get('command')
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
    res = git('rev-parse', '--git-path', 'info/exclude')
    if not res:
        return
    exclude = Path(res)
    exclude = exclude if exclude.is_absolute() else root / exclude
    if exclude.is_dir():
        return
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


def parte(root, docs='docs/requirements'):
    """Resumen breve para Telegram: bucle, fase, versión abierta y backlog, deducidos del disco."""
    if (root / ESPERA).exists():
        marcha = f'esperando cuota hasta {(root / ESPERA).read_text().strip()[-5:]}'
    else:
        marcha = 'en marcha' if (root / PID).exists() else 'parado'
    e = estado(root, docs)
    lineas = [f'*{root.name}* · bucle {marcha}', f'*Fase:* {e[0]} ' + ' '.join(str(x) for x in e[1:3] if x)]
    items = backlog(root)
    abiertas = sorted({i['version'] for i in items if vkey(i['version']) and i['status'] not in CERRADO}, key=vkey)
    for v in abiertas[:1]:
        suyas = [i for i in items if i['version'] == v]
        cuenta = lambda *s: [i['id'] for i in suyas if i['status'] in s]
        lineas.append(f'*{v}:* {len(cuenta("completed"))}/{len(suyas)} cerradas'
                      + (f' · en curso {", ".join(cuenta("in_progress"))}' if cuenta('in_progress') else '')
                      + (f' · bloqueadas {", ".join(cuenta("blocked"))}' if cuenta('blocked') else ''))
    sin_version = [i for i in items if not vkey(i['version']) and i['status'] not in FUERA]
    lineas.append(f'*Backlog sin versión:* {len(sin_version)}')
    if (root / BUZON).exists():
        pendientes = sum(1 for l in (root / BUZON).read_text(encoding='utf-8').splitlines() if l.strip())
        lineas.append(f'*Por registrar:* {pendientes} (entre pasos del bucle)')
    if (root / METRICAS).exists():
        pasos = [json.loads(l) for l in (root / METRICAS).read_text(encoding='utf-8').splitlines()
                 if l.strip() and json.loads(l).get('tipo', 'paso') == 'paso']
        if pasos:
            lineas.append(f'*Último paso:* {pasos[-1].get("paso", "")} {pasos[-1].get("id") or ""} ({pasos[-1].get("fecha", "")[:16]})')
    return '\n'.join(lineas)


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
                    help=f'arnés de todos los pasos (por defecto, el de cada rol en {CONFIG}, o claude)')
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
    ap.add_argument('--aviso-prueba', action='store_true', help=f'envía un aviso de prueba a Telegram ({CONFIG})')
    a = ap.parse_args()
    root = Path.cwd()
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

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
    if a.aviso_prueba:
        if not telegram(root):
            sys.exit('Telegram sin configurar: define TELEGRAM_BOT_TOKEN y TELEGRAM_ALLOWED_USER_IDS '
                     f'(y que "telegram" no sea false en {CONFIG}).')
        ok = avisar(root, None, '🔔 Aviso de prueba del orquestador.')
        print('[orquestar] aviso enviado' if ok else '[orquestar] el aviso no se pudo enviar')
        return 0 if ok else 1
    if a.parar:
        if not (root / PID).exists():
            print('[orquestar] no hay ningún bucle en marcha')
            return 0
        excluir(root)
        (root / PARADA).touch()
        print('[orquestar] parará al terminar el paso en curso')
        return 0
    if not a.estado and not a.parar and not a.verificar and not a.agente and not a.aviso_prueba:
        validar_lanzamiento_bucle(root, a)
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


def cierre_de_version(e):
    """La versión abierta no tiene más tareas elegibles: toca la suite completa."""
    return (e[0] == 'PASO' and e[1] == 'revisar-version') or (e[0] == 'PARAR' and e[1].startswith(FIN_VERSION))


def bucle(a, root):
    if a.idea and not (root / a.docs / 'requirements.md').exists():
        (root / a.docs).mkdir(parents=True, exist_ok=True)
        (root / a.docs / 'requirements.md').write_text(a.idea + '\n', encoding='utf-8')

    cmd_suite = suite(root, a)
    sin_progreso = esperado = 0
    for n in range(1, a.max_pasos + 1):
        if (root / PARADA).exists():
            print('\n[orquestar] PARAR: detenido a petición (--parar). Relanza para seguir.', flush=True)
            return 2
        if not a.estado:
            for iid, titulo in ingerir(root):
                print(f'[orquestar] alta desde Telegram: {iid} {titulo}', flush=True)
                avisar(root, None, f'📝 Registrada {iid}: {titulo} (backlog, sin versión).')
        e = estado(root, a.docs)
        print(f'\n[orquestar] {n}. {e[0]}: ' + ' '.join(str(x) for x in e[1:] if x), flush=True)
        if not a.estado and cmd_suite and cierre_de_version(e) and verificar(root, cmd_suite):
            return parar(root, 'version', f'la versión no tiene más tareas elegibles pero la suite falla ({cmd_suite}).')
        if a.estado:
            return 0 if e[0] in ('FIN', 'PASO') else 2
        if e[0] == 'FIN':
            avisar(root, 'version', f'✅ Producto terminado: {e[1]}')
            return 0
        if e[0] == 'PARAR':
            return parar(root, evento_de(e), e[1])
        _, paso, arg, rama = e
        if rama and git('branch', '--show-current') != rama:
            if git('status', '--porcelain'):
                return parar(root, 'error', f'cambios sin commitear; no puedo cambiar a {rama}.')
            git('checkout', '-q', rama)

        antes = firma(root, a.docs)
        rol, cfg_rol = rol_de(root, paso)
        cfg_rol, escalado = escalada(root, rol, cfg_rol, arg)
        if escalado:
            print(f'[orquestar] {arg}: {rechazos(root, arg)} rechazos seguidos de Hades; '
                  f'escalo a {cfg_rol.get("model") or cfg_rol.get("harness")}', flush=True)
        prompt = construir_prompt_paso(root, paso, arg)
        env = {**os.environ, 'ORQUESTAR_PASO': paso, 'ORQUESTAR_ID': arg or ''}
        env.pop('ORQUESTAR_ESCALADA', None)
        if escalado:
            env['ORQUESTAR_ESCALADA'] = '1'
        f_met = root / METRICAS
        n_met = sum(1 for _ in f_met.read_text(encoding='utf-8').splitlines()) if f_met.exists() else 0
        codigo, m, salida = ejecutar(a, root, prompt, env=env, rol=cfg_rol)
        cuota = espera_cuota(salida) if codigo else None
        if cuota is None and f_met.exists():
            nuevas = [json.loads(l) for l in f_met.read_text(encoding='utf-8').splitlines()[n_met:] if l.strip()]
            cuota = next((f.get('espera_s', 1800) for f in reversed(nuevas)
                          if f.get('tipo') == 'agente' and f.get('sin_cuota')), None)
        registrar(root, {'fecha': ahora(), 'paso': paso, 'id': arg, 'rama': git('branch', '--show-current'),
                         'rol': rol, 'arnes': a.cmd or arnes(a, cfg_rol), 'codigo': codigo, **m,
                         **({'escalado': True} if escalado else {}),
                         **({'sin_cuota': True} if cuota else {})})
        if cuota is not None and esperado + cuota <= a.espera_max * 3600:
            esperado += cuota
            avisar(root, 'cuota', f'⏳ Sin cuota en "{paso}" {arg or ""}: espero hasta las '
                                  f'{datetime.now() + timedelta(seconds=cuota):%H:%M} y reintento.')
            inicio = time.monotonic()
            seguir = esperar(root, cuota)
            registrar(root, {'tipo': 'espera', 'fecha': ahora(), 'paso': paso, 'id': arg,
                             'duracion_s': round(time.monotonic() - inicio)})
            if not seguir:
                print('[orquestar] PARAR: detenido a petición (--parar). Relanza para seguir.', flush=True)
                return 2
            continue
        if codigo or cuota is not None:
            if firma(root, a.docs) != antes and not git('status', '--porcelain'):
                print(f'[orquestar] paso completado en disco a pesar del retorno {codigo} del arnés; continúo.', flush=True)
                sin_progreso = 0
                continue
            motivo = (f'sin cuota tras esperar {esperado // 3600} h (--espera-max)' if cuota is not None
                      else '¿autenticación, red?')
            return parar(root, 'cuota' if cuota is not None else 'error',
                         f'el arnés terminó con código {codigo or 1} ({motivo}). Relanza cuando se resuelva.')
        esperado = 0

        if firma(root, a.docs) == antes:
            sin_progreso += 1
            print(f'[orquestar] sin progreso ({sin_progreso}/{a.reintentos})')
            if sin_progreso >= a.reintentos:
                return parar(root, 'error', f'"{paso}" no avanza tras {a.reintentos} intentos.')
        else:
            sin_progreso = 0
    return parar(root, 'error', f'alcanzado --max-pasos={a.max_pasos}.')


if __name__ == '__main__':
    sys.exit(main())
