#!/usr/bin/env python3
"""Bucle del orquestador: deduce la fase del disco y lanza un arnés por paso.

El estado se calcula siempre a partir de artefactos (documentos, frontmatter del
backlog, ramas git), nunca de lo que el modelo diga que ha hecho.

Salida: 0 = producto terminado, 2 = parada para el humano, 1 = error.
"""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from datetime import datetime, timedelta
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None

try:
    import yaml
except ImportError:
    try:
        from adevv import yaml_lite as yaml
    except ImportError:
        yaml = None

HARNESS = {
    'claude': ['claude', '-p', '{prompt}', '--dangerously-skip-permissions', '--output-format', 'json'],
    'codex': ['codex', 'exec', '--dangerously-bypass-approvals-and-sandbox', '--json', '{prompt}'],
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
TELEGRAM_SESIONES = 'orquestar_telegram.json'  # sesiones de conversación de usuarios en Telegram
PROMPT_FILE_DEFAULT = 'orquestar_prompt.txt'
PROPIOS = (METRICAS, EVIDENCIAS, LOG, PID, PARADA, ESPERA, BUZON, BUZON + '.tmp', '.env', TELEGRAM_SESIONES,
           PROMPT_FILE_DEFAULT, 'telegram.pid', 'telegram.log', 'telegram.parar')
CERRADO = {'completed', 'cancelled'}
FUERA = CERRADO | {'blocked'}  # no pendientes
FIN_VERSION = ('Bloqueos en ', 'Versión ')  # paradas de una versión sin más tareas elegibles
PRODUCTO = 'docs/review/versions/{v}-producto.md'  # revisión funcional, con su tabla de decisiones
PROMPT = ('Lee {skill} y ejecuta en modo orquestado el paso "{paso}"{args}. '
          'Las skills que cite (/nombre) están en {skills}/<nombre>/SKILL.md. '
          'No hagas preguntas: aplica las reglas del modo orquestado.')

try:
    from . import metricas
except ImportError:
    try:
        import metricas
    except ImportError:
        _metricas_spec = importlib.util.spec_from_file_location('adevv_metricas', Path(__file__).with_name('metricas.py'))
        metricas = importlib.util.module_from_spec(_metricas_spec)
        _metricas_spec.loader.exec_module(metricas)
vkey = metricas.clave_version_numerica


def directorio_version_almacen(script=None):
    """Resuelve una única vez el almacén y directorio versionado de un motor."""
    try:
        p = Path(script or __file__).resolve()
        home = Path(os.environ.get('ADEVV_HOME') or Path.home() / '.adevv').resolve()
        versions = home / 'versions'
        rel = p.relative_to(versions)
        version_dir = versions / rel.parts[0]
        version = version_dir.name
        if not re.fullmatch(r'v?\d+(\.\d+)*', version):
            return None
        return home, version_dir, version.lstrip('v')
    except (OSError, ValueError, IndexError, RuntimeError):
        return None


def version_de_manifiestos(script):
    """Obtiene la versión del proyecto desde pyproject.toml o task_config.yaml."""
    try:
        padres = Path(script).resolve().parents
    except (OSError, ValueError, RuntimeError):
        return None
    for padre in padres:
        manifiesto = padre / 'pyproject.toml'
        if manifiesto.is_file():
            try:
                datos = tomllib.loads(manifiesto.read_text(encoding='utf-8'))
                version = datos.get('project', {}).get('version')
            except (OSError, ValueError, TypeError, AttributeError):
                continue
            if isinstance(version, str) and version.strip():
                return version.strip().lstrip('v')
    for padre in padres:
        manifiesto = padre / 'task_config.yaml'
        if not manifiesto.is_file() or not yaml:
            continue
        try:
            if hasattr(yaml, 'safe_load'):
                datos = yaml.safe_load(manifiesto.read_text(encoding='utf-8')) or {}
            elif hasattr(yaml, 'load_yaml'):
                datos = yaml.load_yaml(manifiesto)
            else:
                continue
            version = (datos.get('project') or {}).get('version') if isinstance(datos, dict) else None
        except (OSError, ValueError, TypeError, AttributeError):
            continue
        if isinstance(version, str) and version.strip():
            return version.strip().lstrip('v')
    return None


def version_adevv(script=None):
    """Devuelve la versión de Adevv del proceso en ejecución (deducida del almacén o metadatos)."""
    try:
        version_dir = directorio_version_almacen(script)
        if version_dir:
            return version_dir[2]
    except (OSError, ValueError, RuntimeError):
        pass
    try:
        import adevv
        v = getattr(adevv, '__version__', None)
        if isinstance(v, str) and v.strip():
            return v.strip().lstrip('v')
    except Exception:
        pass
    try:
        version = version_de_manifiestos(script or __file__)
        if version:
            return version
    except Exception:
        pass
    return 'desconocida'


def tiene_firma(texto):
    """Indica si el texto ya termina con una firma de versión de Adevv."""
    if not texto or not isinstance(texto, str):
        return False
    lineas = [l.strip() for l in texto.strip().splitlines() if l.strip()]
    if not lineas:
        return False
    return bool(re.fullmatch(r'[—–-]\s*Adevv\s+v\S*(?:\s*·\s*.+)?', lineas[-1]))


def firmar(texto, extra=None, script=None):
    """Añade la firma de versión al pie de un mensaje de Telegram si no la tiene ya."""
    if not texto or not isinstance(texto, str):
        return texto
    if tiene_firma(texto):
        return texto
    ver = version_adevv(script)
    firma = f'— Adevv v{ver}'
    if extra:
        firma += f' · {extra}'
    return f'{texto.rstrip()}\n\n{firma}'


def version_activa_distinta(script):
    """Devuelve el homólogo activo solo para motores del almacén versionado."""
    try:
        ubicacion = directorio_version_almacen(script)
        if ubicacion is None:
            return None
        home, version_dir, _ = ubicacion
        script = Path(script).resolve()
        datos = json.loads((home / 'active.json').read_text(encoding='utf-8'))
        version = datos.get('version') if isinstance(datos, dict) else None
        if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
            return None
        destino = (home / 'versions' / version / script.relative_to(version_dir)).resolve()
        if destino != script and destino.is_file() and destino.is_relative_to(home / 'versions' / version):
            return destino, version
    except (OSError, ValueError, IndexError, RuntimeError):
        return None
    return None


def recargar_version(script, root, pid_file, estado_recarga, etiqueta):
    """Publica el PID del sucesor antes de cederle la ejecución entre ciclos."""
    nueva = version_activa_distinta(script)
    if nueva is None:
        return False
    destino, version = nueva
    root = root.resolve()
    pid = root / pid_file
    temporal = pid.with_suffix('.recarga.tmp')
    hijo = None
    try:
        if not es_propietario_pid(root, pid_file):
            return False
        datos = {'root': str(root), 'script': str(destino), 'estado': estado_recarga}
        env = {**os.environ, 'ADEVV_RECARGA': json.dumps(datos), 'PYTHONIOENCODING': 'utf-8'}
        argumentos = list(sys.argv[1:])
        if etiqueta == 'gateway':
            sin_root = []
            saltar = False
            for a in argumentos:
                if saltar:
                    saltar = False
                elif a == '--root':
                    saltar = True
                elif not a.startswith('--root='):
                    sin_root.append(a)
            argumentos = [*sin_root, '--root', str(root)]
        opciones = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
        registro = root / ('telegram.log' if etiqueta == 'gateway' else LOG)
        with registro.open('a', encoding='utf-8') as log:
            hijo = subprocess.Popen([sys.executable, '-u', str(destino), *argumentos], cwd=root, env=env,
                                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, **opciones)
            temporal.write_text(str(hijo.pid), encoding='utf-8')
            os.replace(temporal, pid)
            try:
                log.write(f'[{etiqueta}] recargado a versión {version}\n')
                log.flush()
            except OSError:
                pass
    except OSError as error:
        if hijo is not None:
            hijo.terminate()
            hijo.wait()
        temporal.unlink(missing_ok=True)
        print(f'[{etiqueta}] no se pudo recargar: {error}', flush=True)
        return False
    return True


def recibir_recarga(root, pid_file, script):
    """Consume el estado del padre solo tras recibir la propiedad del PID."""
    texto = os.environ.pop('ADEVV_RECARGA', None)
    if texto is None:
        return None
    datos = json.loads(texto)
    if datos['root'] != str(root.resolve()) or datos['script'] != str(Path(script).resolve()):
        raise ValueError('Transferencia de recarga destinada a otro proceso')
    for _ in range(100):
        if es_propietario_pid(root, pid_file):
            return datos['estado']
        time.sleep(0.05)
    raise RuntimeError('No se publicó el PID de la recarga')


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


def _proceso_vivo(pid):
    """Comprueba si existe un proceso, incluyendo procesos ajenos sin permiso de consulta."""
    if os.name == 'nt':
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


def pid_vivo(root, pid_file=PID):
    """Devuelve el PID registrado si sigue vivo; ignora marcas inválidas o muertas."""
    try:
        pid = int((Path(root) / pid_file).read_text(encoding='utf-8').strip())
        return pid if pid > 0 and _proceso_vivo(pid) else None
    except (OSError, ValueError, OverflowError):
        return None


def es_propietario_pid(root, pid_file=PID):
    """Indica si el archivo de PID pertenece al proceso actual."""
    try:
        return (Path(root) / pid_file).read_text(encoding='utf-8').strip() == str(os.getpid())
    except (OSError, ValueError):
        return False


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
    dif = dificultad_de(root, arg) if arg else None
    rol, cfg_rol = rol_de(root, paso, dificultad=dif)
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
        nota_fuente = ' Edita el árbol de trabajo de este repositorio, en cualquier ruta que haga falta (skills/, agents/, workflows/, adevv/, tests/, docs/…), nunca la copia instalada desde la que lees skills y agentes.'

    return instruccion_agente + prompt_cuerpo + extra + nota_fuente


def construir_prompt_agente(root, rol, prompt, reanudacion=False):
    """Construye el mandato para un rol con --agente citando la versión activa instalada."""
    version_dir = get_active_version_dir()
    paso, iid = os.environ.get("ORQUESTAR_PASO", ""), os.environ.get("ORQUESTAR_ID", "")
    dif = dificultad_de(root, iid) if iid else None
    cfg = ajustes(config(root).get(rol, {}), paso, dificultad=dif)
    instrucciones = cfg.get("instructions")
    if instrucciones:
        p_inst = Path(instrucciones)
        if not p_inst.is_absolute():
            p_inst = (root / p_inst).resolve()
        instrucciones_str = str(p_inst)
    else:
        instrucciones_str = str((version_dir / "agents" / f"{rol}.md").resolve())

    skills_dir = (version_dir / "skills").resolve()
    cabecera = ""
    if not reanudacion:
        cabecera += (
            f'Lee "{instrucciones_str}" y actúa como ese agente; ignora el modelo de su frontmatter. '
            f'Las skills están en "{skills_dir}/<nombre>/SKILL.md".\n\n'
        )
        if es_repositorio_fuente_adevv(root):
            cabecera += 'Edita el árbol de trabajo de este repositorio, en cualquier ruta que haga falta (skills/, agents/, workflows/, adevv/, tests/, docs/…), nunca la copia instalada desde la que lees skills y agentes.\n\n'
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
            dif = str(fm.get('dificultad', '')).strip().lower().replace('í', 'i')
            if dif not in ('sencilla', 'media', 'dificil'):
                dif = 'media'
            out.append({'paso': tipo, 'id': fm['id'], 'status': fm.get('status', 'backlog'),
                        'version': fm.get('version', ''), 'pendiente_de': str(fm.get('pendiente_de', '')).strip().lower(),
                        'depende_de': lista(fm['depende_de']) if 'depende_de' in fm else None,
                        'weight': int(peso) if peso.lstrip('-').isdigit() else 0,
                        'dificultad': dif})
    return out


def dificultad_de(root, iid):
    """Dificultad de una tarea o bug (normalizada a sencilla, media o dificil, por defecto media)."""
    if not iid:
        return 'media'
    for it in backlog(root):
        if it['id'] == iid:
            return it.get('dificultad', 'media')
    for d in backlog_dirs(root):
        if d.is_dir():
            for f in d.glob('*.md'):
                fm = frontmatter(f)
                if fm.get('id') == iid:
                    dif = str(fm.get('dificultad', '')).strip().lower().replace('í', 'i')
                    return dif if dif in ('sencilla', 'media', 'dificil') else 'media'
    return 'media'


def siguiente_dificultad(dif):
    """Siguiente nivel de dificultad: sencilla -> media -> dificil -> None."""
    dif = (dif or 'media').strip().lower().replace('í', 'i')
    if dif == 'sencilla':
        return 'media'
    if dif == 'media':
        return 'dificil'
    return None


def fichero_de(root, iid):
    """Ruta al fichero .md de una tarea o bug."""
    if not iid:
        return None
    for d in backlog_dirs(root):
        if d.is_dir():
            for f in d.glob('*.md'):
                if frontmatter(f).get('id') == iid:
                    return f
    return None


def actualizar_dificultad(root, iid, nueva_dif):
    """Actualiza o inserta el campo dificultad en el frontmatter de una tarea o bug."""
    f = fichero_de(root, iid)
    if not f or not f.exists():
        return False
    texto = f.read_text(encoding='utf-8')
    m = re.match(r'^(---[^\n]*\n)(.*?)\n(---[^\n]*\n.*)$', texto, re.S)
    if not m:
        return False
    cab, fm, resto = m.group(1), m.group(2), m.group(3)
    if re.search(r'^dificultad\s*:', fm, re.M):
        nuevo_fm = re.sub(r'^(dificultad\s*:\s*).*$', rf'\g<1>{nueva_dif}', fm, flags=re.M)
    else:
        nuevo_fm = fm + f'\ndificultad: {nueva_dif}'
    f.write_text(cab + nuevo_fm + '\n' + resto, encoding='utf-8')
    return True


def promover_dificultad(root, iid, motivo=''):
    """Sube la dificultad de la tarea/bug un escalón (sencilla -> media -> dificil).
    Actualiza el frontmatter, registra métrica e informa por consola."""
    actual = dificultad_de(root, iid)
    nueva = siguiente_dificultad(actual)
    if not nueva:
        return None
    if actualizar_dificultad(root, iid, nueva):
        msg_motivo = f' ({motivo})' if motivo else ''
        print(f'[orquestar] {iid}: subo dificultad de {actual} a {nueva}{msg_motivo}', flush=True)
        registrar(root, {'tipo': 'promocion', 'fecha': ahora(), 'id': iid, 'de': actual, 'dificultad': nueva})
        return nueva
    return None


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


def rol_de(root, paso, dificultad=None):
    """(rol, configuración) que ejecuta un paso del bucle: Artemisa desarrolla, Atenea analiza y decide.

    Sin la clave del rol en orchestration.json se usa `development` (y Atenea, sin ella, la de Artemisa).
    """
    cfg = config(root)
    dev = cfg.get('artemisa') or cfg.get('development', {})
    rol = 'artemisa' if paso in DESARROLLO else 'atenea'
    return rol, ajustes(dev if rol == 'artemisa' else cfg.get('atenea') or dev, paso, dificultad=dificultad)


def ajustes(cfg, paso='', dificultad=None):
    """Configuración del rol para un paso: la base más lo que fije `pasos.<paso>` (p. ej. otro `effort`)."""
    base = {k: v for k, v in cfg.items() if k not in ('pasos', 'dificultad')}
    dif_cfg = (cfg.get('dificultad') or {}).get(dificultad, {}) if dificultad else {}
    paso_cfg = (cfg.get('pasos') or {}).get(paso, {}) if paso else {}
    return {**base, **dif_cfg, **paso_cfg}


def lista_reservas(cfg_rol):
    """Devuelve la lista ordenada de configuraciones de reserva, heredando del rol los campos no redefinidos."""
    raw = cfg_rol.get('reserva')
    if not raw:
        return []
    items = [raw] if isinstance(raw, dict) else list(raw)
    base = {k: cfg_rol[k] for k in ('harness', 'model', 'effort') if k in cfg_rol}
    if 'instructions' in cfg_rol:
        base['instructions'] = cfg_rol['instructions']
    resultado = []
    for it in items:
        if isinstance(it, dict):
            resultado.append({**base, **it})
    return resultado


PASOS_ANALISIS = frozenset(('especificar', 'revisar-tarea', 'revisar-version',
                           'calcular-dependencias', 'work-plan', 'revisar-deuda', 'aplicar-producto'))


def cadena_analisis(root, paso, dificultad='media'):
    """Perfiles de recuperación finitos y efectivos, sin expandir reservas de niveles."""
    dificultad = dificultad or 'media'
    rol, inicial = rol_de(root, paso, dificultad=dificultad)
    cfg = config(root)
    dev = cfg.get('artemisa') or cfg.get('development', {})
    base = dev if rol == 'artemisa' else cfg.get('atenea') or dev
    candidatos = [inicial]
    nivel = siguiente_dificultad(dificultad)
    while nivel:
        if nivel in (base.get('dificultad') or {}):
            candidatos.append(ajustes(base, paso, dificultad=nivel))
        nivel = siguiente_dificultad(nivel)
    esc = inicial.get('escalada') or {}
    if esc:
        candidatos.append({**inicial, **{k: v for k, v in esc.items() if k != 'rechazos'}})
    candidatos.extend(lista_reservas(inicial))
    resultado, vistos = [], set()
    for candidato in candidatos:
        identidad = (candidato.get('harness') or 'claude',
                     candidato.get('model') or 'predeterminado', candidato.get('effort') or None)
        if identidad not in vistos:
            vistos.add(identidad)
            resultado.append(candidato)
    return resultado


def diagnostico_analisis(recuperacion, limite):
    """Identifica el par agotado y los perfiles probados con sus intentos."""
    perfiles = ' → '.join(
        f'{c.get("harness") or "claude"}/{c.get("model") or "predeterminado"}/'
        f'{c.get("effort") or "predeterminado"} ({limite} intentos)'
        for c in recuperacion['perfiles'])
    return (f'"{recuperacion["paso"]}" {recuperacion["arg"] or "(sin argumento)"} '
            f'sin progreso tras agotar perfiles: {perfiles}.')


def configuraciones_con_cuota(root, configuraciones):
    """Respeta reinicios reales y permite sondeos supuestos al relanzar o vencer el intervalo."""
    instante = fecha_estado(ahora())
    filas = leer_metricas(root)
    cuotas = consumo_cuotas(root, instante, filas)[1]
    marcas = marcas_cuota(root, instante, filas)
    for clave in list(cuotas):
        if marcas[clave]['tipo'] == 'supuesta':
            sondeo = SONDEOS_CUOTA.get((str(root.resolve()), clave))
            if sondeo is None or (instante - sondeo).total_seconds() >= intervalo_cuota(root):
                cuotas.pop(clave)
    disponibles = [cfg for cfg in configuraciones
                   if (cfg.get('harness', 'claude'), cfg.get('model') or 'predeterminado') not in cuotas]
    return disponibles


def cuota_descartada(root, configuraciones, seleccionadas, incluir_recuperadas=False):
    """Recupera la menor espera omitida; opcionalmente incluye perfiles ya recuperados."""
    omitidas = [cfg for cfg in configuraciones if cfg not in seleccionadas]
    if not omitidas:
        return None, None
    instante = fecha_estado(ahora())
    cuotas = consumo_cuotas(root, instante)[1]
    pendientes = []
    for cfg in omitidas:
        harness = cfg.get('harness', 'claude')
        hasta = cuotas.get((harness, cfg.get('model') or 'predeterminado'))
        plantilla = HARNESS.get(harness)
        if (hasta or incluir_recuperadas) and plantilla and buscar_ejecutable(plantilla[0]):
            pendientes.append((max((hasta - instante).total_seconds(), 0) if hasta else 0, cfg))
    return min(pendientes, key=lambda par: par[0]) if pendientes else (None, None)


def rechazos(root, iid):
    """Veredictos RECHAZADO seguidos de Hades sobre un ID, contados desde su último APROBADO o última subida."""
    n = 0
    if iid and (root / METRICAS).exists():
        for f in leer_metricas(root):
            if f.get('id') == iid and f.get('tipo') == 'promocion':
                n = 0
            elif f.get('tipo') == 'agente' and f.get('rol') == 'hades' and f.get('id') == iid and f.get('veredicto'):
                n = n + 1 if f['veredicto'] == 'RECHAZADO' else 0
    return n


def reintentos_acumulados(root, iid):
    """(ejecuciones_paso, rechazos_hades) desde la última subida o inicio."""
    pasos = 0
    rech = 0
    if not iid or not (root / METRICAS).exists():
        return 0, 0
    for linea in (root / METRICAS).read_text(encoding='utf-8').splitlines():
        if not linea.strip():
            continue
        try:
            f = json.loads(linea)
        except Exception:
            continue
        if f.get('id') != iid:
            continue
        if f.get('tipo') == 'promocion':
            pasos = 0
            rech = 0
            continue
        if f.get('tipo', 'paso') == 'paso' and not f.get('sin_cuota'):
            pasos += 1
        elif f.get('tipo') == 'agente' and f.get('rol') == 'hades' and f.get('veredicto'):
            rech = rech + 1 if f['veredicto'] == 'RECHAZADO' else 0
    return pasos, rech


def comprobar_promocion(root, iid):
    """Comprueba si un ID debe promocionar de dificultad tras reintentos o rechazos seguidos.
    Retorna (debe_promover, motivo)."""
    dif = dificultad_de(root, iid)
    if dif not in ('sencilla', 'media'):
        return False, ''
    cfg_dev = config(root).get('artemisa') or config(root).get('development') or {}
    tiene_dificultades = bool(cfg_dev.get('dificultad'))
    esc = cfg_dev.get('escalada') or {}
    tope = esc.get('rechazos', 2) if esc else (2 if tiene_dificultades else 3)
    pasos, rech = reintentos_acumulados(root, iid)
    if pasos > 2:
        return True, f'{pasos} ejecuciones de paso'
    if rech >= tope:
        return True, f'{rech} rechazos seguidos de Hades'
    return False, ''


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
        if 'resume' in cmd:
            i = cmd.index('resume') + 2
        else:
            i = cmd.index('exec') + 1
        cmd[i:i] = (['-m', rol['model']] if rol.get('model') else []) + \
                   (['-c', f'model_reasoning_effort="{rol["effort"]}"'] if rol.get('effort') else [])
    return cmd


def buscar_ejecutable(nombre):
    """Encuentra el ejecutable en el PATH o en las rutas de usuario habituales en Windows."""
    exe = shutil.which(nombre)
    if exe:
        return exe
    if os.name == 'nt':
        rutas = []
        if winreg is not None:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as k:
                    val, _ = winreg.QueryValueEx(k, 'Path')
                    if val:
                        if hasattr(winreg, 'ExpandEnvironmentStrings'):
                            val = winreg.ExpandEnvironmentStrings(val)
                        else:
                            val = os.path.expandvars(val)
                        rutas.extend(val.split(os.pathsep))
            except (OSError, ValueError):
                pass
        home = Path.home()
        rutas.append(str(home / '.local/bin'))
        appdata = os.environ.get('APPDATA')
        if appdata:
            rutas.append(str(Path(appdata) / 'npm'))
        else:
            rutas.append(str(home / 'AppData/Roaming/npm'))
        localappdata = os.environ.get('LOCALAPPDATA')
        if localappdata:
            rutas.append(str(Path(localappdata) / 'agy/bin'))
            rutas.append(str(Path(localappdata) / 'OpenAI/Codex/bin'))
        else:
            rutas.append(str(home / 'AppData/Local/agy/bin'))
            rutas.append(str(home / 'AppData/Local/OpenAI/Codex/bin'))

        path_extra = os.pathsep.join(os.path.expandvars(r) for r in rutas if r)
        exe = shutil.which(nombre, path=f"{os.environ.get('PATH', '')}{os.pathsep}{path_extra}")
        if exe:
            return exe
    return None


def arnes(a, rol):
    """Arnés de un paso: --harness o el de su rol (claude por defecto); None con --cmd."""
    return None if a.cmd else a.harness or rol.get('harness', 'claude')


class ArnesAusente(RuntimeError):
    """Señala un ejecutable ausente que permite probar otra configuración."""


def registrar_ausencia(root, tipo, posicion, cfg, **contexto):
    """Registra y avisa una omisión sin atribuir ejecución ni cuota."""
    harness = cfg.get('harness', 'claude')
    texto = f'[orquestar] no se encuentra el arnés "{harness}"; conmutando a reserva...'
    print(texto, flush=True)
    registrar(root, {'tipo': tipo, 'fecha': ahora(), **contexto,
                     'posicion': posicion, 'arnes': harness,
                     'modelo': cfg.get('model') or 'predeterminado',
                     'arnes_ausente': True, 'codigo': 127, 'modelos': {},
                     'entrada': 0, 'cache_leida': 0, 'cache_escrita': 0,
                     'salida': 0, 'razonamiento': 0, 'coste_usd': 0})
    avisar(root, 'arnes', texto)


def comando(a, prompt, root=None, rol=None, sesion=None):
    rol = rol if rol is not None else rol_de(root or Path.cwd(), 'task-dev')[1]
    harness = arnes(a, rol)
    plantilla = (shlex.split(a.cmd, posix=os.name != 'nt') if a.cmd else HARNESS[harness])
    plantilla = [p.strip('"\'') for p in plantilla]
    exe = buscar_ejecutable(plantilla[0])
    if not exe:
        if a.cmd:
            sys.exit(f'No se encuentra el arnés "{plantilla[0]}" en el PATH.')
        raise ArnesAusente(f'No se encuentra el arnés "{plantilla[0]}" en el PATH.')
    if sesion and not a.cmd:
        if harness == 'claude':
            cmd = [exe, '--resume', sesion] + [p.replace('{prompt}', prompt) for p in plantilla[1:]]
        elif harness == 'codex':
            cmd = [exe, 'exec', 'resume', sesion] + [p.replace('{prompt}', prompt) for p in plantilla[2:]]
        elif harness == 'agy':
            cmd = [exe, '--conversation', sesion] + [p.replace('{prompt}', prompt) for p in plantilla[1:]]
        else:
            cmd = [exe] + [p.replace('{prompt}', prompt) for p in plantilla[1:]]
    else:
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
        sesion_id = d.get('conversation_id') or d.get('session_id')
        m.update(turnos=d.get('num_turns'), error=d.get('status') != 'SUCCESS',
                 modelos={modelo: {'entrada': u.get('input_tokens'), 'salida': u.get('output_tokens'),
                                   'cache_leida': u.get('cache_read_tokens'),
                                   'razonamiento': u.get('thinking_tokens')}})
        if sesion_id:
            m['sesion'] = sesion_id
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
        sesion_id = d.get('session_id') or d.get('sessionId')
        m.update(turnos=d.get('num_turns'), coste_usd=d.get('total_cost_usd'),
                 subagentes=(d.get('subagent_stats') or {}).get('spawned'), error=d.get('is_error'),
                 modelos={k: {'entrada': u.get('inputTokens'), 'salida': u.get('outputTokens'),
                              'cache_leida': u.get('cacheReadInputTokens'),
                              'cache_escrita': u.get('cacheCreationInputTokens'), 'coste_usd': u.get('costUSD')}
                          for k, u in (d.get('modelUsage') or {}).items()})
        if sesion_id:
            m['sesion'] = sesion_id
        return (1 if d.get('is_error') and not r.returncode else r.returncode), m, salida
    lineas, uso, turnos = [], {}, 0
    sesion_id = None
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
            elif evento.get('type') == 'thread.started':
                sesion_id = evento.get('thread_id') or (evento.get('thread', {}).get('id') if isinstance(evento.get('thread'), dict) else None)
            elif evento.get('type') == 'item.completed' and evento.get('item', {}).get('type') == 'agent_message':
                print(evento['item'].get('text', ''), flush=True)
            elif evento.get('type') == 'turn.completed':
                turnos += 1
                for k, v in (evento.get('usage') or {}).items():
                    uso[k] = uso.get(k, 0) + (v or 0)
            elif evento.get('type') in ('error', 'turn.failed'):
                print(json.dumps(evento, ensure_ascii=False), flush=True)
    m = {'duracion_s': round(time.monotonic() - inicio)}
    if sesion_id:
        m['sesion'] = sesion_id
    if uso:
        modelo = next((cmd[i + 1] for i, x in enumerate(cmd[:-1]) if x in ('-m', '--model')), 'codex')
        entrada = max(0, (uso.get('input_tokens') or 0) - (uso.get('cached_input_tokens') or 0))
        m.update(turnos=turnos, modelos={modelo: {
            'entrada': entrada, 'salida': uso.get('output_tokens'),
            'cache_leida': uso.get('cached_input_tokens'), 'cache_escrita': uso.get('cache_write_input_tokens'),
            'razonamiento': uso.get('reasoning_output_tokens')}})
    return p.returncode, m, ''.join(lineas[-200:])


def buscar_sesion_agente(root, rol, iid, arnes):
    """Busca la sesión previa de un rol dentro del intento en curso de la tarea."""
    if not iid:
        return None
    f = root / METRICAS
    if not f.exists():
        return None
    try:
        lineas = [json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip()]
    except Exception:
        return None

    es_escalada = bool(os.environ.get('ORQUESTAR_ESCALADA'))
    for e in reversed(lineas):
        if e.get('id') and e.get('id') != iid:
            break
        if e.get('tipo') == 'paso' and e.get('paso') == 'especificar':
            break
        if e.get('tipo') == 'paso' and e.get('escalado') and not es_escalada:
            break
        if bool(e.get('escalado')) != es_escalada and e.get('tipo') in ('paso', 'agente'):
            break
        if e.get('tipo') == 'paso' and not e.get('sin_cuota'):
            break
        if (e.get('tipo') == 'agente' and e.get('rol') == rol and e.get('id') == iid
                and e.get('arnes') == arnes and e.get('sesion')):
            return e['sesion']
    return None


def buscar_sesion_paso(root, paso, iid, arnes):
    """Busca la sesión para reanudar un paso interrumpido inmediatamente antes por cuota."""
    f = root / METRICAS
    if not f.exists():
        return None
    try:
        lineas = [json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip()]
    except Exception:
        return None
    for e in reversed(lineas):
        if e.get('tipo') in ('espera', 'verificacion'):
            continue
        if e.get('tipo') == 'paso':
            if (e.get('paso') == paso and e.get('id') == iid
                    and e.get('arnes') == arnes and e.get('sin_cuota') and e.get('sesion')):
                return e['sesion']
            break
        if e.get('id') and e.get('id') != iid:
            break
    return None


def ejecutar(a, root, prompt, env=None, rol=None, sesion=None):
    """Lanza el paso con el arnés y el modelo de su rol y devuelve (código, métricas, salida)."""
    if rol is None:
        iid = (env or {}).get('ORQUESTAR_ID') or os.environ.get('ORQUESTAR_ID', '')
        paso = (env or {}).get('ORQUESTAR_PASO') or os.environ.get('ORQUESTAR_PASO', 'task-dev')
        dif = dificultad_de(root, iid) if iid else None
        rol = rol_de(root, paso, dificultad=dif)[1]
    harness = arnes(a, rol)
    if sesion:
        cmd = comando(a, prompt, root, rol, sesion=sesion)
        codigo, m, salida = lanzar(cmd, root, harness, env=env)
        if codigo != 0 and espera_cuota(salida) is None:
            cmd_fresh = comando(a, prompt, root, rol, sesion=None)
            return lanzar(cmd_fresh, root, harness, env=env)
        return codigo, m, salida
    return lanzar(comando(a, prompt, root, rol), root, harness, env=env)


def base_comando_agente(harness, prompt, sesion=None):
    if harness == 'claude':
        if sesion:
            return ['claude', '--resume', sesion, '-p', '--dangerously-skip-permissions', '--output-format', 'json']
        return ['claude', '-p', '--dangerously-skip-permissions', '--output-format', 'json']
    elif harness == 'codex':
        if sesion:
            return ['codex', 'exec', 'resume', sesion, '--json', '-c', 'approval_policy="never"',
                    '-c', 'sandbox_mode="workspace-write"', '-']
        return ['codex', 'exec', '--json', '-c', 'approval_policy="never"',
                '--sandbox', 'workspace-write', '-']
    elif harness == 'agy':
        if sesion:
            return ['agy', '--conversation', sesion, '--dangerously-skip-permissions', '--output-format', 'json', '-p', prompt]
        return ['agy', '--dangerously-skip-permissions', '--output-format', 'json', '-p', prompt]
    return None


def agente(root, rol, prompt):
    """Lanza un rol (hades, clio, cronos…) con el arnés y el modelo de orchestration.json."""
    paso, iid = os.environ.get('ORQUESTAR_PASO', ''), os.environ.get('ORQUESTAR_ID', '')
    dif = dificultad_de(root, iid) if iid else None
    cfg = ajustes(config(root).get(rol, {}), paso, dificultad=dif)
    if 'instructions' in cfg:
        p_inst = Path(cfg['instructions'])
        if not p_inst.is_absolute():
            p_inst = root / p_inst
        if not p_inst.exists():
            sys.exit(f"orchestration.json: {rol}.instructions apunta a {cfg['instructions']}, que no existe.")

    reservas = lista_reservas(cfg)
    configs_originales = [cfg] + reservas
    configs_a_probar = configuraciones_con_cuota(root, configs_originales)
    cuotas_acumuladas = []
    ultima_cuota = None
    escalado = bool(os.environ.get('ORQUESTAR_ESCALADA'))

    for idx_cfg, cfg_actual in enumerate(configs_a_probar):
        harness = cfg_actual.get('harness', 'claude')
        hay_mas_reservas = idx_cfg < len(configs_a_probar) - 1
        sesion = buscar_sesion_agente(root, rol, iid, harness)
        es_reanudacion = bool(sesion)
        prompt_texto = construir_prompt_agente(root, rol, prompt, reanudacion=es_reanudacion)
        base = base_comando_agente(harness, prompt_texto, sesion=sesion)
        if not base:
            sys.exit(f'Arnés no soportado para roles: {harness}')
        exe = buscar_ejecutable(base[0])
        if not exe:
            posicion = next(i for i, c in enumerate(configs_originales) if c is cfg_actual)
            registrar_ausencia(root, 'agente', posicion, cfg_actual, rol=rol, paso=paso, id=iid)
            continue
        cmd = con_modelo([exe] + base[1:], harness, cfg_actual)
        codigo, m, salida = lanzar(cmd, root, harness, entrada=prompt_texto)
        if es_reanudacion and codigo != 0 and espera_cuota(salida) is None:
            prompt_fresh = construir_prompt_agente(root, rol, prompt, reanudacion=False)
            base_fresh = base_comando_agente(harness, prompt_fresh, sesion=None)
            cmd_fresh = con_modelo([exe] + base_fresh[1:], harness, cfg_actual)
            codigo, m, salida = lanzar(cmd_fresh, root, harness, entrada=prompt_fresh)

        cuota = espera_cuota(salida) if codigo else None
        if cuota is not None:
            datos = fallo_cuota(root, harness, cfg_actual.get('model') or 'predeterminado', salida)
            m.update(datos)
            cuota = datos['cuota_espera_s']
            cuotas_acumuladas.append(cuota)
            if hay_mas_reservas:
                ultima_cuota = {'tipo': 'agente', 'fecha': ahora(), 'rol': rol,
                                'paso': paso, 'id': iid, 'arnes': harness, 'codigo': codigo}
                registrar(root, {'tipo': 'agente', 'fecha': ahora(), 'rol': rol, 'paso': paso, 'id': iid,
                                 'arnes': harness, 'codigo': codigo,
                                 **({'escalado': True} if escalado else {}), **m})
                print(f'[orquestar] {rol} agotó cuota ({cfg_actual.get("model") or harness}); '
                      f'conmutando a reserva...', flush=True)
                continue
            else:
                menor_cuota = min(cuotas_acumuladas)
                veredicto = re.findall(r'Veredicto\W{0,6}(APROBADO|RECHAZADO)', salida) if rol == 'hades' else []
                registrar(root, {'tipo': 'agente', 'fecha': ahora(), 'rol': rol, 'paso': paso, 'id': iid,
                                 'arnes': harness, 'codigo': codigo,
                                 **({'veredicto': veredicto[-1]} if veredicto else {}),
                                 'sin_cuota': True, 'espera_s': menor_cuota,
                                 **({'escalado': True} if escalado else {}), **m})
                print(f'[orquestar] {rol} sin cuota: termina el paso ahora mismo sin tocar estados; '
                      'el bucle esperará la cuota y reintentará.', flush=True)
                return codigo

        if not codigo:
            recuperar_cuota(root, harness, cfg_actual.get('model') or 'predeterminado')
        veredicto = re.findall(r'Veredicto\W{0,6}(APROBADO|RECHAZADO)', salida) if rol == 'hades' else []
        registrar(root, {'tipo': 'agente', 'fecha': ahora(), 'rol': rol, 'paso': paso, 'id': iid,
                         'arnes': harness, 'codigo': codigo,
                         **({'veredicto': veredicto[-1]} if veredicto else {}),
                         **({'escalado': True} if escalado else {}), **m})
        if veredicto and veredicto[-1] == 'RECHAZADO':
            print(tope_de_rechazos(root, iid), flush=True)
        return codigo

    if ultima_cuota is not None:
        registrar(root, {**ultima_cuota, 'modelos': {}, 'sin_cuota': True,
                         **({'escalado': True} if escalado else {}),
                         'espera_s': min(cuotas_acumuladas)})
        print(f'[orquestar] {rol} sin cuota; se conserva la espera del arnés disponible.', flush=True)
        return ultima_cuota['codigo']
    espera, cfg_omitida = cuota_descartada(root, [cfg] + reservas, configs_a_probar)
    if espera is not None:
        registrar(root, {'tipo': 'agente', 'fecha': ahora(), 'rol': rol, 'paso': paso, 'id': iid,
                         'arnes': cfg_omitida.get('harness', 'claude'), 'codigo': 1,
                         'modelos': {}, 'sin_cuota': True, 'espera_s': espera,
                         **({'escalado': True} if escalado else {})})
        print(f'[orquestar] {rol} sin cuota; se conserva la recuperación vigente.', flush=True)
        return 1
    mensaje = f'{rol}: ningún arnés disponible en el principal ni en las reservas.'
    print(f'[orquestar] {mensaje}', flush=True)
    avisar(root, 'error', mensaje)
    return 1


def tope_de_rechazos(root, iid):
    """Instrucción para Artemisa al llegar al tope de rechazos seguidos; '' si aún no ha llegado."""
    cfg_dev = config(root).get('artemisa') or config(root).get('development') or {}
    esc = cfg_dev.get('escalada') or {}
    tiene_dificultades = bool(cfg_dev.get('dificultad'))
    dif = dificultad_de(root, iid) if iid else 'media'
    puede_subir = tiene_dificultades and dif in ('sencilla', 'media')

    tope = esc.get('rechazos', 2) if esc else (2 if tiene_dificultades else 3)
    n = rechazos(root, iid)
    if n < tope or n % tope:
        return ''
    if puede_subir:
        return (f'[orquestar] Hades ha rechazado {iid} {n} veces seguidas: no sigas corrigiendo. Commitea lo que '
                'tengas en la rama, explica en tu salida qué falla y termina el paso sin cambiar estados: el bucle '
                'subirá la dificultad de la tarea y la relanzará con el perfil del nuevo nivel.')
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
                   r'|\b429\b|resource_exhausted|overloaded|out of credits|credit balance|insufficient_quota|billing_hard_limit', re.I)

CREDITOS = re.compile(r'out of credits|credit balance|billing_hard_limit', re.I)
SONDEOS_CUOTA = {}


def intervalo_cuota(root):
    """Intervalo positivo finito de las comprobaciones de cuota supuesta."""
    valor = config(root).get('cuota_reintento_s')
    return valor if numero_cuota(valor) and valor > 0 else 300


def marcas_cuota(root, instante, filas=None):
    """Pliega agotamientos y recuperaciones sin reescribir el histórico ni los tokens."""
    marcas = {}
    for fila in leer_metricas(root) if filas is None else filas:
        fecha = fecha_estado(fila.get('fecha'))
        if fecha is None or fecha > instante:
            continue
        arnes = fila.get('arnes') or 'desconocido'
        modelo = fila.get('modelo_cuota')
        if fila.get('tipo') == 'cuota_recuperada':
            marcas.pop((arnes, modelo), None)
            continue
        segundos = fila.get('cuota_espera_s')
        if segundos is None and fila.get('sin_cuota'):
            segundos = fila.get('espera_s')
            modelos = fila.get('modelos') or {}
            modelo = modelo or (next(iter(modelos)) if len(modelos) == 1 else None)
        if not modelo or not numero_cuota(segundos) or segundos < 0:
            continue
        try:
            hasta = fecha + timedelta(seconds=segundos)
        except OverflowError:
            continue
        tipo = fila.get('cuota_tipo') or ('supuesta' if segundos == 1800 else 'real')
        origen = fila.get('cuota_origen') or ('sin hora en la respuesta' if tipo == 'supuesta'
                                             else 'recuperación histórica registrada')
        clave = (arnes, modelo)
        anterior = marcas.get(clave)
        if anterior and anterior['tipo'] == tipo == 'real' and anterior['hasta'] > hasta:
            continue
        marcas[clave] = dict(hasta=hasta, tipo=tipo, origen=origen)
    return marcas


def recuperar_cuota(root, harness, modelo):
    """Añade una recuperación para un par conocido, conservando el consumo histórico."""
    if (harness, modelo) in marcas_cuota(root, fecha_estado(ahora())):
        registrar(root, dict(tipo='cuota_recuperada', fecha=ahora(), arnes=harness, modelo_cuota=modelo))
    SONDEOS_CUOTA.pop((str(root.resolve()), (harness, modelo)), None)


def reset_cuotas(root, selector=''):
    """Recupera únicamente los pares del selector arnés/modelo, arnés o global."""
    pares = marcas_cuota(root, fecha_estado(ahora()))
    seleccionados = [par for par in pares if not selector or selector == par[0]
                     or selector == '/'.join(par)]
    for harness, modelo in seleccionados:
        recuperar_cuota(root, harness, modelo)
    return len(seleccionados)


def fallo_cuota(root, harness, modelo, salida):
    """Clasifica el fallo, limita los sondeos y avisa de créditos una vez por episodio."""
    creditos = bool(CREDITOS.search(salida))
    segundos = espera_cuota(salida, sin_hora=None)
    tipo = 'supuesta' if creditos or segundos is None else 'real'
    origen = 'sin créditos' if creditos else ('hora en la respuesta' if tipo == 'real'
                                            else 'sin hora en la respuesta')
    if creditos:
        anterior = marcas_cuota(root, fecha_estado(ahora())).get((harness, modelo))
        if not anterior or anterior['origen'] != 'sin créditos':
            avisar(root, 'cuota', f'Sin créditos en {harness}: recarga y el bucle lo reintentará')
    if tipo == 'supuesta':
        segundos = intervalo_cuota(root)
        SONDEOS_CUOTA[(str(root.resolve()), (harness, modelo))] = fecha_estado(ahora())
    return dict(modelo_cuota=modelo, cuota_espera_s=segundos, cuota_tipo=tipo, cuota_origen=origen)


def espera_cuota(salida, ahora=None, sin_hora=1800):
    """Segundos hasta poder reintentar si la salida indica falta de cuota; None si es otro error.

    Reconoce la hora de recuperación en los formatos habituales (marca de tiempo tras «|»,
    «try again in 2h 13m», «resets in 56h48m9s», «resets at 5pm»); si no la hay, propone 30 minutos.
    """
    if not CUOTA.search(salida):
        return None
    ahora = ahora or datetime.now()
    margen = 120
    m = re.search(r'\|(\d{10})\b', salida)
    if m:
        return max(int(m[1]) - int(ahora.timestamp()), 0) + margen
    m = re.search(r'(?:try again|retry|resets?) in\s+(?:(\d+)\s*(?:days?|d)(?![a-z]))?\s*'
                  r'(?:(\d+)\s*(?:hours?|hrs?|h)(?![a-z]))?\s*(?:(\d+)\s*(?:minutes?|mins?|m)(?![a-z]))?\s*'
                  r'(?:(\d+)\s*(?:seconds?|secs?|s)(?![a-z]))?', salida, re.I)
    if m and any(m.groups()):
        d, h, mi, sg = (int(g or 0) for g in m.groups())
        return d * 86400 + h * 3600 + mi * 60 + sg + margen
    m = re.search(r'(?:try again|resets?)\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', salida, re.I)
    if m:
        h = int(m[1]) % 12 + (12 if m[3].lower() == 'pm' else 0)
        objetivo = ahora.replace(hour=h, minute=int(m[2] or 0), second=0, microsecond=0)
        if objetivo <= ahora:
            objetivo += timedelta(days=1)
        return int((objetivo - ahora).total_seconds()) + margen
    return sin_hora


def esperar(root, segundos, motivo='sin cuota', cuotas_esperadas=None):
    """Duerme hasta la hora indicada, atento a --parar. Devuelve False si se pidió parar."""
    hasta = datetime.now() + timedelta(seconds=segundos)
    pendientes = set(marcas_cuota(root, fecha_estado(ahora()))) if motivo == 'sin cuota' else set()
    (root / ESPERA).write_text(hasta.isoformat(timespec='minutes'), encoding='utf-8')
    print(f'[orquestar] {motivo}: espero hasta las {hasta:%H:%M} y reintento el paso.', flush=True)
    try:
        while datetime.now() < hasta:
            if (root / PARADA).exists():
                return False
            if motivo == 'sin cuota':
                filas = leer_metricas(root)
                if cuotas_esperadas is not None:
                    nuevas = filas[cuotas_esperadas['desde']:]
                    pares = set(cuotas_esperadas['pares']) | {
                        (f.get('arnes'), f['modelo_cuota']) for f in nuevas
                        if f.get('modelo_cuota') and f.get('cuota_espera_s') is not None}
                    if any(f.get('tipo') == 'cuota_recuperada'
                           and (f.get('arnes'), f.get('modelo_cuota')) in pares for f in nuevas):
                        return True
                if pendientes and pendientes - set(marcas_cuota(root, fecha_estado(ahora()), filas)):
                    return True
            time.sleep(min(30, max((hasta - datetime.now()).total_seconds(), 0)))
        return True
    finally:
        (root / ESPERA).unlink(missing_ok=True)


# ---------------------------------------------------------------- avisos por Telegram

EVENTOS = ('version', 'cuota', 'respuesta', 'error', 'arnes')


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


class CredencialesTelegram:
    """Credenciales efectivas y procedencia del token de Telegram."""

    def __init__(self, token, usuarios, origen):
        self.token = token
        self.usuarios = usuarios
        self.origen = origen

    def __iter__(self):
        """Conserva el desempaquetado histórico de token y usuarios."""
        yield self.token
        yield self.usuarios


def credenciales(root=None):
    """Devuelve las credenciales efectivas y el origen del token."""
    base = Path(root) if root else Path.cwd()
    env = leer_env(base / '.env')
    token_local = env.get('TELEGRAM_BOT_TOKEN', '').strip()
    token_entorno = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    token = token_local or token_entorno
    origen = 'proyecto' if token_local else 'entorno' if token_entorno else 'ninguno'
    ids_locales = env.get('TELEGRAM_ALLOWED_USER_IDS', '').strip()
    raw_usr = ids_locales or os.environ.get('TELEGRAM_ALLOWED_USER_IDS', '').strip()
    usuarios = [u.strip() for u in str(raw_usr).split(',') if u.strip()]
    return CredencialesTelegram(token, usuarios, origen)


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
    texto = firmar(texto)
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


def cargar_cierre_version():
    """Carga el soporte de cierre solo al atender el comando o su aviso final."""
    spec = importlib.util.spec_from_file_location(
        'cierre_version', Path(__file__).resolve().parents[1] / 'telegram_gateway/cierre_version.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def avisar(root, evento, texto):
    """Envía el aviso a los usuarios autorizados si el evento está activo (None: siempre). Un fallo nunca para el bucle."""
    cfg = telegram(root)
    if not cfg or (evento and evento not in cfg[2]):
        return False
    token, usuarios, _ = cfg
    version_final = re.search(r'Versión (v\d+\.\d+) terminada\.', texto)
    if evento == 'version' and version_final:
        texto += '\n' + cargar_cierre_version().resumen(root, version_final[1])
    texto_firmado = firmar(f'[{root.name}] {texto}')
    return all([enviar(token, u, texto_firmado) for u in usuarios])


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
    with tempfile.TemporaryFile() as captura:
        codigo = subprocess.run(cmd, shell=True, cwd=root, stdout=captura, stderr=subprocess.STDOUT).returncode
        captura.seek(0, os.SEEK_END)
        captura.seek(max(0, captura.tell() - 32768))
        salida = captura.read().decode('utf-8', errors='replace')
    if salida:
        print(salida, end='' if salida.endswith('\n') else '\n', flush=True)
    fila = {'fecha': ahora(), 'comando': cmd, 'arbol': clave, 'codigo': codigo,
            'salida': salida, 'duracion_s': round(time.monotonic() - inicio)}
    with f.open('a', encoding='utf-8') as out:
        out.write(json.dumps(fila, ensure_ascii=False) + '\n')
    registrar(root, {'tipo': 'verificacion', 'reutilizada': False, 'id': os.environ.get('ORQUESTAR_ID', ''), **fila})
    return codigo


def bloquear_sin_progreso(root, iid, intentos, salida, contexto=''):
    """Bloquea para el humano y persiste el motivo en tarea y revisión de versión."""
    fichero = fichero_de(root, iid)
    version = vkey(frontmatter(fichero).get('version'))
    dificultad = dificultad_de(root, iid)
    hoy = datetime.now().strftime('%Y-%m-%d')
    cola = (salida or '(el arnés no produjo salida)')[-2000:]
    detalle = '\n'.join('    ' + linea for linea in cola.splitlines())
    motivo = ((f'- {contexto}\n' if contexto else '')
              + f'- {iid} bloqueada para el humano: {intentos} intentos sin progreso en {dificultad}; fecha: {ahora()}\n'
              f'- Cola de la última salida:\n\n{detalle}\n')
    cabecera, cuerpo = re.split(r'\n---[ \t]*(?:\n|$)', fichero.read_text(encoding='utf-8'), maxsplit=1)
    for clave, valor in {'status': 'blocked', 'pendiente_de': 'humano', 'updated_at': hoy}.items():
        if re.search(rf'^{clave}:', cabecera, re.M):
            cabecera = re.sub(rf'^{clave}:.*$', f'{clave}: {valor}', cabecera, flags=re.M)
        else:
            cabecera += f'\n{clave}: {valor}'
    cuerpo = re.sub(r'\n## Bloqueo sin progreso\n.*?(?=\n## |\Z)', '', cuerpo, flags=re.S)
    fichero.write_text(cabecera + '\n---\n' + cuerpo.rstrip('\n') + '\n\n## Bloqueo sin progreso\n' + motivo,
                       encoding='utf-8')
    rutas = [str(fichero.relative_to(root))]
    if version:
        revision = root / f'docs/review/versions/v{version[0]}.{version[1]}-revision.md'
        revision.parent.mkdir(parents=True, exist_ok=True)
        previo = revision.read_text(encoding='utf-8') if revision.exists() else ''
        revision.write_text(previo.rstrip('\n') + f'\n\n## {iid} · Bloqueo sin progreso\n' + motivo, encoding='utf-8')
        rutas.append(str(revision.relative_to(root)))
    subprocess.run(['git', 'add', '--', *rutas], cwd=root, capture_output=True, check=True)
    subprocess.run(['git', 'commit', '-q', '-m', f'fix({iid}): bloquear tarea sin progreso', '--', *rutas],
                   cwd=root, capture_output=True, check=True)
    avisar(root, 'respuesta', (f'{contexto}\n' if contexto else '')
           + f'⏸ {iid} bloqueada tras {intentos} intentos sin progreso en {dificultad}; '
                              f'el bucle sigue con las demás.\nCola de la última salida:\n{cola}')


def registrar_fallo_suite(root, version, cmd):
    """Registra o reabre el bug de cierre y devuelve (ID, motivo de parada o vacío)."""
    evidencia = root / EVIDENCIAS
    filas = [json.loads(l) for l in evidencia.read_text(encoding='utf-8').splitlines() if l.strip()]
    ultima = next(f for f in reversed(filas) if f['comando'] == cmd and f['codigo'])
    salida = ultima.get('salida') or '(el comando no produjo salida)'
    cola_aviso = salida[-1200:]
    clave_comando = hashlib.sha256(cmd.encode('utf-8')).hexdigest()
    directorio = backlog_dirs(root)[1]
    fichero = next((f for f in sorted(directorio.glob('*.md'))
                    if frontmatter(f).get('suite_cierre', '').lower() == 'true'
                    and vkey(frontmatter(f).get('version')) == vkey(version)
                    and frontmatter(f).get('suite_clave') == clave_comando), None)
    hoy = datetime.now().strftime('%Y-%m-%d')
    if fichero:
        fm = frontmatter(fichero)
        iid = fm['id']
        if fm.get('status') in ('blocked', 'cancelled'):
            return iid, f'{iid}: el bug de cierre está {fm["status"]}; no se reabre. Cola de la última salida:\n{cola_aviso}'
        texto = fichero.read_text(encoding='utf-8')
    else:
        directorio.mkdir(parents=True, exist_ok=True)
        iid = siguiente_id(root, 'B')
        fichero = directorio / f'{iid}-suite-roja-al-cerrar-version.md'
        titulo = 'La suite falla al cerrar la versión'
        texto = (f'---\nid: {iid}\ntitle: {json.dumps(titulo, ensure_ascii=False)}\n'
                 f'type: bug\nweight: 10\ndificultad: media\nversion: {json.dumps(version)}\n'
                 f'status: planned\ndepende_de: []\ncreated_at: {hoy}\n'
                 f'suite_cierre: true\nsuite_clave: {clave_comando}\n'
                 f'---\n\n# {iid}: {titulo}\n\n## Descripción del fallo\n'
                 'La suite completa de cierre devuelve un código distinto de cero. '
                 'Debe pasar antes de revisar o cerrar la versión.\n\n'
                 '## Reproducir\nEjecutar el comando indicado en la evidencia desde la raíz del proyecto.\n')
        fichero.write_text(texto, encoding='utf-8')
        fm = frontmatter(fichero)
    dificultad = dificultad_de(root, iid)
    intentos = int(fm.get('suite_intentos', '0')) if fm.get('suite_dificultad') == dificultad else 0
    if fm.get('status') == 'completed':
        intentos += 1
    motivo = ''
    if intentos >= 3:
        nueva = promover_dificultad(root, iid, motivo=f'{intentos} arreglos tras los que la suite sigue roja')
        if nueva:
            dificultad, intentos = nueva, 0
            texto = fichero.read_text(encoding='utf-8')
        else:
            motivo = (f'{iid}: la suite sigue fallando tras 3 intentos en dificil. '
                      f'Cola de la última salida (completa en el bug):\n{cola_aviso}')
    cambios = {'status': 'blocked' if motivo else 'planned', 'updated_at': hoy,
               'suite_dificultad': dificultad, 'suite_intentos': str(intentos)}
    if motivo:
        cambios['pendiente_de'] = 'humano'
    cabecera, cuerpo = texto.split('\n---\n', 1)
    for clave, valor in cambios.items():
        if re.search(rf'^{clave}:', cabecera, re.M):
            cabecera = re.sub(rf'^{clave}:.*$', f'{clave}: {valor}', cabecera, flags=re.M)
        else:
            cabecera += f'\n{clave}: {valor}'
    cuerpo = re.sub(r'\n## Último fallo de suite\n.*?(?=\n## |\Z)', '', cuerpo, flags=re.S)
    detalle = '\n'.join('    ' + linea for linea in salida.splitlines())
    cuerpo += (f'\n## Último fallo de suite\n- Comando: {json.dumps(cmd, ensure_ascii=False)}\n'
               f'- Código: {ultima["codigo"]}; árbol: {ultima["arbol"]}; fecha: {ahora()}\n\n{detalle}\n')
    fichero.write_text(cabecera + '\n---\n' + cuerpo, encoding='utf-8')
    ruta = str(fichero.relative_to(root))
    subprocess.run(['git', 'add', '--', ruta], cwd=root, capture_output=True, check=True)
    subprocess.run(['git', 'commit', '-q', '-m', f'fix({iid}): registrar fallo de suite al cierre',
                    '--', ruta], cwd=root, capture_output=True, check=True)
    print(f'[orquestar] {iid}: suite roja registrada para {version} ({intentos} intentos en {dificultad}).', flush=True)
    return iid, motivo


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


def es_fichero_rastreado_git(root, ruta):
    """Comprueba si un fichero está bajo seguimiento en git."""
    try:
        p = Path(ruta)
        try:
            rel = p.relative_to(Path(root).resolve())
            arg_ruta = str(rel).replace('\\', '/')
        except ValueError:
            arg_ruta = p.name
        res = subprocess.run(
            ['git', 'ls-files', '--error-unmatch', '--', arg_ruta],
            cwd=root,
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
            return True
        if res.returncode == 1 and 'did not match any file' in (res.stderr or ''):
            return False
        return True
    except Exception:
        return True


def registrar(root, fila):
    """Añade una línea al registro común de métricas (pasos, agentes, esperas y verificaciones)."""
    excluir(root)
    fila.setdefault('tipo', 'paso')
    with (root / METRICAS).open('a', encoding='utf-8') as f:
        f.write(json.dumps(fila, ensure_ascii=False) + '\n')



def leer_metricas(root):
    """Lee registros completos; tolera una última línea aún en escritura."""
    return metricas.leer_registros(root, tolerar_ultima=True)


def fecha_estado(valor):
    """Convierte ISO local o con offset en un instante comparable con zona."""
    try:
        return datetime.fromisoformat(str(valor)).astimezone()
    except (ValueError, TypeError, OverflowError):
        return None


def perfil_estado(cfg):
    """Describe un perfil efectivo sin resolver de nuevo sus ajustes."""
    return (f'{cfg.get("harness") or "claude"}/{cfg.get("model") or "predeterminado"}'
            + (f' ({cfg["effort"]})' if cfg.get('effort') else ''))


def perfiles_agentes(root):
    """Enumera perfiles declarados y reservas con su configuración heredada."""
    resultado = []
    cfg = config(root)
    for rol in ('artemisa', 'hades', 'atenea', 'clio', 'cronos', 'development'):
        base = cfg.get(rol)
        if not isinstance(base, dict):
            continue
        variantes = [('base', ajustes(base))]
        for dificultad in base.get('dificultad', {}):
            variantes.append((f'dificultad {dificultad}', ajustes(base, dificultad=dificultad)))
        for paso in base.get('pasos', {}):
            variantes.append((f'paso {paso}', ajustes(base, paso)))
            for dificultad in base.get('dificultad', {}):
                variantes.append((f'dificultad {dificultad}, paso {paso}',
                                  ajustes(base, paso, dificultad)))
        if isinstance(base.get('escalada'), dict):
            variantes.append(('escalada', {**ajustes(base), **base['escalada']}))
        for etiqueta, perfil in variantes:
            resultado.append((rol, etiqueta, perfil))
            for numero, reserva in enumerate(lista_reservas(perfil), 1):
                resultado.append((rol, f'{etiqueta}, reserva {numero}',
                                  {**perfil, **reserva}))
    return resultado


def numero_cuota(valor):
    """Admite únicamente números reales finitos, excluyendo booleanos."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(valor)


def limite_cuota(perfil):
    """Límite configurable o referencia ilustrativa de tokens por familia."""
    limite = perfil.get('cuota_tokens_5h')
    if numero_cuota(limite) and limite > 0:
        return limite
    modelo = str(perfil.get('model') or '').lower()
    if 'flash' in modelo:
        return 20_000_000
    if any(familia in modelo for familia in ('argon', 'pro', 'opus', 'sonnet')):
        return 5_000_000
    return 10_000_000


def cuota_codex(instante):
    """Última cuota primaria vigente de la cuenta, leída sin modificar sesiones."""
    sesiones = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex') / 'sessions'
    ultima = None
    try:
        for ruta in sesiones.rglob('*.jsonl'):
            try:
                with ruta.open(encoding='utf-8') as archivo:
                    for linea in archivo:
                        try:
                            evento = json.loads(linea)
                            if not isinstance(evento, dict):
                                continue
                            payload = evento.get('payload')
                            if not isinstance(payload, dict) or payload.get('type') != 'token_count':
                                continue
                            primary = (payload.get('rate_limits') or {}).get('primary') or {}
                            porcentaje, reset = primary.get('used_percent'), primary.get('resets_at')
                            fecha = fecha_estado(evento.get('timestamp'))
                            if not (numero_cuota(porcentaje) and 0 <= porcentaje <= 100 and numero_cuota(reset)):
                                continue
                            hasta = datetime.fromtimestamp(reset).astimezone()
                            if (fecha and instante - timedelta(hours=5) <= fecha <= instante < hasta
                                    and (ultima is None or fecha > ultima[0])):
                                ultima = (fecha, porcentaje, hasta)
                        except (ValueError, TypeError, AttributeError, OverflowError, OSError):
                            continue
            except (OSError, UnicodeError):
                continue
    except OSError:
        pass
    return ultima


def consumo_cuotas(root, instante, filas=None):
    """Suma la ventana de tokens y conserva todo agotamiento todavía vigente."""
    uso = {}
    filas = leer_metricas(root) if filas is None else filas
    marcas = marcas_cuota(root, instante, filas)
    cuotas = {clave: marca['hasta'] for clave, marca in marcas.items() if marca['hasta'] > instante}
    for clave in cuotas:
        uso[clave] = 0
    for fila in filas:
        fecha = fecha_estado(fila.get('fecha'))
        if fecha is None or fecha > instante:
            continue
        arnes = fila.get('arnes') or 'desconocido'
        modelos = fila.get('modelos') or {}
        if instante - timedelta(hours=5) <= fecha:
            for modelo, tokens in modelos.items():
                clave = (arnes, modelo)
                uso[clave] = uso.get(clave, 0) + sum(tokens.get(c) or 0 for c in
                                                     ('entrada', 'cache_leida', 'cache_escrita', 'salida'))
    return uso, cuotas


def detalle_marca(marca, instante):
    """Texto compartido de agotamiento, certeza y origen para estado y agentes."""
    hasta = marca['hasta']
    minutos = math.ceil((hasta - instante).total_seconds() / 60)
    etiqueta = 'supuesto' if marca['tipo'] == 'supuesta' else 'real'
    return (f'100.0% consumido (agotado hasta {hasta:%H:%M %z}, faltan {minutos} min)'
            f' · {etiqueta}: {marca["origen"]}')


def informe_agentes(root, docs='docs/requirements'):
    """Informe de roles y porcentaje consumido para CLI y Telegram."""
    e = estado(root, docs)
    instante = fecha_estado(ahora())
    perfiles = perfiles_agentes(root)
    lineas = ['Agentes configurados:']
    for rol, etiqueta, perfil in perfiles:
        lineas.append(f'{rol}: {perfil_estado(perfil)} [{etiqueta}]')
    if not perfiles:
        lineas.append('Sin roles definidos en orchestration.json')
    if e[0] == 'PASO':
        paso, iid = e[1:3]
        dificultad = dificultad_de(root, iid) if iid else None
        rol, perfil = rol_de(root, paso, dificultad=dificultad)
        perfil, escalado = escalada(root, rol, perfil, iid)
        hades = ajustes(config(root).get('hades', {}), paso, dificultad=dificultad)
        lineas.append(f'Agentes para {paso} {iid or ""} (dificultad: {dificultad or "no aplica"}):')
        for nombre, efectivo in ((rol, perfil), ('hades', hades)):
            lineas.append(f'{nombre}: {perfil_estado(efectivo)}'
                          + (' [escalada]' if nombre == rol and escalado else ''))
    limites = {}
    for _, _, perfil in perfiles:
        clave = (perfil.get('harness') or 'claude', perfil.get('model') or 'predeterminado')
        limite = limite_cuota(perfil)
        limites[clave] = min(limites.get(clave, limite), limite)
    filas = leer_metricas(root)
    uso, cuotas = consumo_cuotas(root, instante, filas)
    marcas = marcas_cuota(root, instante, filas)
    nativo = cuota_codex(instante) if any(h == 'codex' for h, _ in limites) else None
    lineas.append('Cuota por modelo (referencia local cuando no hay dato nativo):')
    for clave, limite in sorted(limites.items()):
        tokens = uso.get(clave, 0)
        hasta = cuotas.get(clave)
        if hasta:
            detalle = detalle_marca(marcas[clave], instante)
        elif clave[0] == 'codex' and nativo:
            detalle = f'{nativo[1]:.1f}% consumido · resetea {nativo[2]:%H:%M %z}'
        else:
            porcentaje = min(100.0, round(tokens * 100.0 / limite, 1))
            detalle = f'{porcentaje:.1f}% consumido ({tokens} / {limite} tokens en 5 h)'
        lineas.append(f'{clave[0]}/{clave[1]}: {detalle}')
    espera = root / ESPERA
    hasta = fecha_estado(espera.read_text(encoding='utf-8').strip()) if espera.exists() else None
    if hasta and hasta > instante:
        lineas.append(f'Espera global: hasta {hasta:%H:%M %z} '
                      f'({math.ceil((hasta - instante).total_seconds() / 60)} min restantes)')
    return '\n'.join(lineas)


def resumen(root):
    """Si hay un bucle en marcha y qué lleva consumido, según los ficheros del bucle."""
    vivo = pid_vivo(root)
    if vivo:
        print(f'[orquestar] en marcha (pid {vivo}); salida en {LOG}')
    else:
        print('[orquestar] no hay ningún bucle en marcha')
    if not (root / METRICAS).exists():
        return
    instante = fecha_estado(ahora())
    for (harness, modelo), marca in sorted(marcas_cuota(root, instante).items()):
        if marca['hasta'] > instante:
            print(f'[orquestar] {harness}/{modelo}: {detalle_marca(marca, instante)}')
    filas = leer_metricas(root)
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
    hasta = fecha_estado((root / ESPERA).read_text(encoding='utf-8').strip()) if (root / ESPERA).exists() else None
    if hasta and hasta > fecha_estado(ahora()):
        marcha = f'esperando cuota hasta {hasta:%H:%M}'
    else:
        marcha = 'en marcha' if pid_vivo(root) else 'parado'
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
        pasos = [f for f in leer_metricas(root) if f.get('tipo', 'paso') == 'paso']
        if pasos:
            lineas.append(f'*Último paso:* {pasos[-1].get("paso", "")} {pasos[-1].get("id") or ""} ({pasos[-1].get("fecha", "")[:16]})')
    return '\n'.join(lineas)


_gateway_aviso_entorno = set()
_GATEWAY_SOLO_AVISOS = 'token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto'


def iniciar_gateway(root, informar=True):
    """Solicita el gateway opcional sin abortar el bucle si falla su lanzador."""
    try:
        cfg = telegram(root)
        if not cfg:
            return
        if credenciales(root).origen == 'entorno':
            clave = str(Path(root).resolve())
            if informar and clave not in _gateway_aviso_entorno:
                _gateway_aviso_entorno.add(clave)
                print(f'[orquestar] {_GATEWAY_SOLO_AVISOS}', flush=True)
            return
        resultado = subprocess.run(
            [sys.executable, str(SKILL.parent.parent / 'telegram_gateway' / 'gateway.py'),
             '--root', str(root), '--fondo'], cwd=root, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10,
            **({'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}))
        if resultado.returncode:
            print('[orquestar] gateway no iniciado (ya activo o fallo; consulta telegram.log)', flush=True)
    except Exception as error:
        print(f'[orquestar] gateway no iniciado ({type(error).__name__}); el bucle continúa', flush=True)


def en_fondo(root, argumentos=None):
    """Relanza con argumentos explícitos o los de la CLI y salida en LOG."""
    vivo = pid_vivo(root)
    if vivo:
        sys.exit(f'Ya hay un bucle en marcha (pid {vivo}). '
                 f'Si no es así, borra {PID}.')
    (root / PID).unlink(missing_ok=True)
    excluir(root)
    iniciar_gateway(root, informar=False)
    args = [x for x in (sys.argv[1:] if argumentos is None else argumentos) if x != '--fondo']
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
    ap.add_argument('--reintentos-arnes', type=int, default=3,
                    help='reintentos por perfil ante errores sin cuota (>= 0; esperas 60, 300, 900 segundos)')
    ap.add_argument('--espera-max', type=float, default=12,
                    help='horas máximas esperando cuota seguidas antes de parar (0 = no esperar)')
    ap.add_argument('--estado', action='store_true', help='muestra el estado y el consumo, y sale')
    ap.add_argument('--agentes', '--agents', action='store_true', help='consulta roles, modelos y porcentaje de cuota')
    ap.add_argument('--cuota-reset', nargs='?', const='', metavar='ARNES[/MODELO]',
                    help='recupera marcas de cuota del selector, o todas si se omite')
    ap.add_argument('--metricas', '--metrics', nargs='?', const='todas', metavar='FILTRO',
                    help='consulta métricas por versión (todas, ultima, ultimas:N o vX.Y,vX.Y)')
    ap.add_argument('--version-filtro', metavar='FILTRO', help='filtro alternativo para --metricas')
    ap.add_argument('--csv', nargs='?', const='-', metavar='RUTA',
                    help='exporta métricas CSV a stdout (-) o a un fichero UTF-8')
    ap.add_argument('--fondo', action='store_true', help=f'lanza el bucle desacoplado, con la salida en {LOG}')
    ap.add_argument('--parar', action='store_true', help='pide al bucle en marcha que pare tras el paso en curso')
    ap.add_argument('--agente', metavar='ROL', help=f'lanza un rol (hades, clio, cronos) según {CONFIG}')
    ap.add_argument('--prompt', help='mandato directo para --agente')
    ap.add_argument('--prompt-file', type=Path, help='mandato para --agente (si no, por la entrada estándar)')
    ap.add_argument('--verificar', nargs='?', const='suite', metavar='CMD',
                    help='ejecuta la suite (o CMD) o reutiliza su resultado en verde para el mismo árbol')
    ap.add_argument('--calidad', action='store_true', help='comprueba formato y lint del delta de una tarea')
    ap.add_argument('--base', help='base Git estable de la tarea para --calidad')
    ap.add_argument('--aplicar', action='store_true', help='aplica formato en escritura antes de --calidad')
    ap.add_argument('--aviso-prueba', action='store_true', help=f'envía un aviso de prueba a Telegram ({CONFIG})')
    a = ap.parse_args()
    if a.reintentos_arnes < 0:
        ap.error('--reintentos-arnes debe ser un entero no negativo')
    root = Path.cwd()
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    if a.cuota_reset is not None:
        print(f'[orquestar] {reset_cuotas(root, a.cuota_reset)} marcas de cuota recuperadas.')
        return 0

    if a.calidad:
        if not a.base:
            ap.error('--calidad requiere --base con la base Git estable de la tarea')
        spec = importlib.util.spec_from_file_location('adevv_calidad', SKILL.with_name('calidad.py'))
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo.ejecutar(root, a.base, a.aplicar, verificar)
    if a.base is not None or a.aplicar:
        ap.error('--base y --aplicar requieren --calidad')

    if a.agentes:
        print(informe_agentes(root, a.docs))
        return 0

    if a.metricas is not None:
        spec = importlib.util.spec_from_file_location('adevv_metricas', SKILL.with_name('metricas.py'))
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        try:
            return modulo.mostrar(root, backlog(root), a.version_filtro or a.metricas, a.csv, sys.stdout)
        except (ValueError, OSError) as error:
            ap.error(str(error))
    if a.csv is not None or a.version_filtro is not None:
        ap.error('--csv y --version-filtro requieren --metricas / --metrics.')

    if a.agente:
        borrar_prompt_file = False
        ruta_prompt_file = None
        prompt = None
        if a.prompt is not None:
            prompt = a.prompt
        elif a.prompt_file is not None:
            ruta_prompt_file = (root / a.prompt_file).resolve()
            if not ruta_prompt_file.exists():
                sys.exit(f'No existe el fichero de prompt: {a.prompt_file}')
            prompt = ruta_prompt_file.read_text(encoding='utf-8')
            if ruta_prompt_file.parent == root.resolve() and not es_fichero_rastreado_git(root, ruta_prompt_file):
                borrar_prompt_file = True
        else:
            prompt = sys.stdin.read()

        try:
            if not prompt or not prompt.strip():
                sys.exit('Falta el mandato: --prompt, --prompt-file o entrada estándar.')
            return agente(root, a.agente, prompt)
        finally:
            if borrar_prompt_file and ruta_prompt_file and ruta_prompt_file.exists():
                try:
                    ruta_prompt_file.unlink()
                except OSError:
                    pass
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
        vivo = pid_vivo(root)
        if not vivo:
            (root / PID).unlink(missing_ok=True)
            (root / PARADA).unlink(missing_ok=True)
            print('[orquestar] no hay ningún bucle en marcha')
            return 0
        excluir(root)
        (root / PARADA).touch()
        print('[orquestar] parará al terminar el paso en curso')
        return 0
    a.recarga = recibir_recarga(root, PID, __file__)
    if a.recarga is None and not a.estado and not a.parar and not a.verificar and not a.agente and not a.aviso_prueba:
        validar_lanzamiento_bucle(root, a)
    if a.fondo:
        return en_fondo(root)
    if a.estado:
        resumen(root)
    elif a.recarga is not None:
        pass
    elif (vivo := pid_vivo(root)):
        sys.exit(f'Ya hay un bucle en marcha (pid {vivo}). Si no es así, borra {PID}.')
    else:
        (root / PID).unlink(missing_ok=True)
        excluir(root)
        (root / PID).write_text(str(os.getpid()), encoding='utf-8')
    try:
        return bucle(a, root)
    finally:
        if not a.estado and es_propietario_pid(root):
            for f in (PID, PARADA, ESPERA):
                (root / f).unlink(missing_ok=True)


def cierre_de_version(e):
    """La versión abierta no tiene más tareas elegibles: toca la suite completa."""
    return (e[0] == 'PASO' and e[1] == 'revisar-version') or (e[0] == 'PARAR' and e[1].startswith(FIN_VERSION))


def bucle(a, root):
    _gateway_aviso_entorno.discard(str(Path(root).resolve()))
    if not a.estado:
        iniciar_gateway(root)
    if a.idea and not (root / a.docs / 'requirements.md').exists():
        (root / a.docs).mkdir(parents=True, exist_ok=True)
        (root / a.docs / 'requirements.md').write_text(a.idea + '\n', encoding='utf-8')

    cmd_suite = suite(root, a)
    recarga = getattr(a, 'recarga', None) or {}
    sin_progreso = recarga.get('sin_progreso', 0)
    esperado = recarga.get('esperado', 0)
    recuperaciones_analisis = {(r['paso'], r['arg']): r
                              for r in recarga.get('recuperaciones_analisis', [])}
    for n in range(recarga.get('n', 1), a.max_pasos + 1):
        if (root / PARADA).exists():
            print('\n[orquestar] PARAR: detenido a petición (--parar). Relanza para seguir.', flush=True)
            return 2
        if not a.estado and recargar_version(__file__, root, PID,
                                             {'n': n, 'sin_progreso': sin_progreso, 'esperado': esperado,
                                              'recuperaciones_analisis': list(recuperaciones_analisis.values())}, 'orquestar'):
            return 0
        if not a.estado:
            for iid, titulo in ingerir(root):
                print(f'[orquestar] alta desde Telegram: {iid} {titulo}', flush=True)
                avisar(root, None, f'📝 Registrada {iid}: {titulo} (backlog, sin versión).')
        e = estado(root, a.docs)
        print(f'\n[orquestar] {n}. {e[0]}: ' + ' '.join(str(x) for x in e[1:] if x), flush=True)
        if not a.estado and cmd_suite and cierre_de_version(e):
            version = e[2] if e[0] == 'PASO' else re.search(r'\bv\d+\.\d+(?:\.\d+)?', e[1])[0]
            rama_cierre = e[3] if e[0] == 'PASO' else f'release/{version}'
            if rama_cierre and git('branch', '--show-current') != rama_cierre:
                if git('status', '--porcelain'):
                    return parar(root, 'error', f'cambios sin commitear; no puedo cambiar a {rama_cierre}.')
                subprocess.run(['git', 'checkout', '-q', rama_cierre], cwd=root, check=True)
            if verificar(root, cmd_suite):
                iid, motivo = registrar_fallo_suite(root, version, cmd_suite)
                if motivo:
                    return parar(root, 'version', motivo)
                e = estado(root, a.docs)
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

        dif = dificultad_de(root, arg) if arg else None
        if paso in ('task-dev', 'bug-fix') and arg:
            debe, motivo = comprobar_promocion(root, arg)
            if debe:
                nueva_dif = promover_dificultad(root, arg, motivo=motivo)
                if nueva_dif:
                    dif = nueva_dif
        antes = firma(root, a.docs)
        rol, cfg_rol = rol_de(root, paso, dificultad=dif)
        escalado = False
        if paso not in PASOS_ANALISIS:
            cfg_rol, escalado = escalada(root, rol, cfg_rol, arg)
        if escalado:
            print(f'[orquestar] {arg}: {rechazos(root, arg)} rechazos seguidos de Hades; '
                  f'escalo a {cfg_rol.get("model") or cfg_rol.get("harness")}', flush=True)
        clave_analisis = (paso, arg or '')
        recuperacion = None
        if paso in PASOS_ANALISIS:
            if clave_analisis not in recuperaciones_analisis:
                recuperaciones_analisis[clave_analisis] = {
                    'paso': paso, 'arg': arg or '', 'indice': 0, 'intentos': 0,
                    'perfiles': cadena_analisis(root, paso, dif)}
            recuperacion = recuperaciones_analisis[clave_analisis]
            cfg_rol = recuperacion['perfiles'][recuperacion['indice']]
        prompt = construir_prompt_paso(root, paso, arg)
        env = {**os.environ, 'ORQUESTAR_PASO': paso, 'ORQUESTAR_ID': arg or ''}
        env.pop('ORQUESTAR_ESCALADA', None)
        if escalado:
            env['ORQUESTAR_ESCALADA'] = '1'
        reservas = lista_reservas(cfg_rol)
        configs_originales = [cfg_rol] + reservas
        contexto_cuota = {'desde': len(leer_metricas(root)), 'pares': {
            (cfg.get('harness', 'claude'), cfg.get('model') or 'predeterminado')
            for cfg in configs_originales}}
        configs_a_probar = configs_originales
        if not a.cmd and not a.harness:
            configs_a_probar = configuraciones_con_cuota(root, configs_a_probar)
        cuotas_paso = []
        recuperaciones_paso = []
        sesion_anterior = None
        arnes_anterior = None
        codigo = 1
        m = {}
        salida = ''
        cuota = None
        cfg_usada = cfg_rol
        hubo_ejecucion = False
        pendiente_cuota = False
        paso_completado = False
        ultimo_registrado = False

        for idx_cfg, cfg_actual in enumerate(configs_a_probar):
            arnes_paso = a.cmd or arnes(a, cfg_actual)
            if idx_cfg == 0:
                nueva_sesion = (recuperacion and recuperacion['indice'] > 0
                                and not recuperacion.get('perfil_iniciado', False))
                sesion_paso = None if nueva_sesion else buscar_sesion_paso(root, paso, arg, arnes_paso)
            elif arnes_paso == arnes_anterior:
                sesion_paso = sesion_anterior
            else:
                sesion_paso = None

            ausente = False
            for intento in range(getattr(a, 'reintentos_arnes', 3) + 1):
                if (root / PARADA).exists():
                    return 2
                f_met = root / METRICAS
                n_met = len(f_met.read_text(encoding='utf-8').splitlines()) if f_met.exists() else 0
                try:
                    if recuperacion is not None:
                        recuperacion['perfil_iniciado'] = True
                    if sesion_paso:
                        resultado = ejecutar(a, root, prompt, env=env, rol=cfg_actual, sesion=sesion_paso)
                    else:
                        resultado = ejecutar(a, root, prompt, env=env, rol=cfg_actual)
                except ArnesAusente:
                    posicion = next(i for i, c in enumerate(configs_originales) if c is cfg_actual)
                    registrar_ausencia(root, 'paso', posicion,
                                       {**cfg_actual, 'harness': arnes_paso}, rol=rol, paso=paso, id=arg)
                    ausente = True
                    break
                codigo, m, salida = resultado
                ultimo_registrado = False
                hubo_ejecucion = True
                pendiente_cuota = False
                cfg_usada = cfg_actual
                cuota = espera_cuota(salida) if codigo else None
                if cuota is None and f_met.exists():
                    nuevas = [json.loads(l) for l in f_met.read_text(encoding='utf-8').splitlines()[n_met:] if l.strip()]
                    cuota = next((f.get('espera_s', 1800) for f in reversed(nuevas)
                                  if f.get('tipo') == 'agente' and f.get('sin_cuota')), None)
                if not codigo or cuota is not None:
                    break
                if firma(root, a.docs) != antes and not git('status', '--porcelain'):
                    paso_completado = True
                    break
                if intento == getattr(a, 'reintentos_arnes', 3):
                    break
                registrar(root, {'fecha': ahora(), 'paso': paso, 'id': arg,
                                 'rama': git('branch', '--show-current'), 'rol': rol,
                                 'arnes': arnes_paso, 'modelo': cfg_actual.get('model') or 'predeterminado',
                                 'codigo': codigo, **m,
                                 **({'escalado': True} if escalado else {})})
                demora = (60, 300, 900)[min(intento, 2)]
                inicio = time.monotonic()
                seguir = esperar(root, demora, motivo='fallo del arnés')
                registrar(root, {'tipo': 'espera', 'fecha': ahora(), 'paso': paso, 'id': arg,
                                 'motivo': 'fallo_arnes', 'duracion_s': round(time.monotonic() - inicio)})
                if not seguir:
                    print('[orquestar] PARAR: detenido a petición (--parar). Relanza para seguir.', flush=True)
                    return 2
                sesion_paso = None
            if ausente:
                continue

            if codigo and cuota is None and not paso_completado and idx_cfg == len(configs_a_probar) - 1:
                restante, recuperada = cuota_descartada(root, configs_originales, configs_a_probar,
                                                       incluir_recuperadas=True)
                if restante == 0:
                    configs_a_probar.append(recuperada)
            cuota_propia = espera_cuota(salida) if codigo else None
            hay_mas_reservas = idx_cfg < len(configs_a_probar) - 1

            if codigo and cuota_propia is not None:
                datos = fallo_cuota(root, arnes_paso, cfg_actual.get('model') or 'predeterminado', salida)
                m.update(datos)
                cuota_propia = datos['cuota_espera_s']
                cuotas_paso.append(cuota_propia)
                recuperaciones_paso.append((time.monotonic() + cuota_propia, cfg_actual))
                if hay_mas_reservas:
                    registrar(root, {'fecha': ahora(), 'paso': paso, 'id': arg,
                                     'rama': git('branch', '--show-current'),
                                     'rol': rol, 'arnes': arnes_paso, 'modelo': cfg_actual.get('model') or 'predeterminado',
                                 'codigo': codigo, **m,
                                     **({'escalado': True} if escalado else {}),
                                     'sin_cuota': True})
                    print(f'[orquestar] sin cuota en {rol} ({cfg_actual.get("model") or arnes_paso}); '
                          f'conmutando a reserva...', flush=True)
                    arnes_anterior = arnes_paso
                    sesion_anterior = m.get('sesion')
                    pendiente_cuota = True
                    continue
                else:
                    cuota = min(cuotas_paso)
                    break
            elif codigo and cuota is None and not paso_completado and hay_mas_reservas:
                registrar(root, {'fecha': ahora(), 'paso': paso, 'id': arg,
                                 'rama': git('branch', '--show-current'), 'rol': rol,
                                 'arnes': arnes_paso, 'modelo': cfg_actual.get('model') or 'predeterminado',
                                 'codigo': codigo, **m,
                                 **({'escalado': True} if escalado else {})})
                ultimo_registrado = True
                print(f'[orquestar] fallo persistente en {rol} ({cfg_actual.get("model") or arnes_paso}); '
                      'conmutando a reserva...', flush=True)
                arnes_anterior = None
                sesion_anterior = None
                continue
            else:
                break

        if not hubo_ejecucion:
            cuota, cfg_omitida = cuota_descartada(root, [cfg_rol] + reservas, configs_a_probar)
            if cuota is None:
                return parar(root, 'error', f'{paso}: ningún arnés disponible en el principal ni en las reservas.')
            cfg_usada = cfg_omitida
            m = {'modelos': {}}
        if pendiente_cuota:
            cuota = min(cuotas_paso)
            m = {}
        if codigo and not paso_completado and (cuota is None or cuotas_paso):
            cuota_omitida, cfg_omitida = cuota_descartada(root, configs_originales, configs_a_probar)
            pendientes = [(max(hasta - time.monotonic(), 0), cfg) for hasta, cfg in recuperaciones_paso]
            if cuota_omitida is not None:
                pendientes.append((cuota_omitida, cfg_omitida))
            if pendientes:
                cuota, cfg_recuperable = min(pendientes, key=lambda par: par[0])
                if cfg_recuperable is not cfg_usada:
                    if not ultimo_registrado:
                        registrar(root, {'fecha': ahora(), 'paso': paso, 'id': arg,
                                         'rama': git('branch', '--show-current'), 'rol': rol,
                                         'arnes': a.cmd or arnes(a, cfg_usada),
                                         'modelo': cfg_usada.get('model') or 'predeterminado',
                                         'codigo': codigo, **m,
                                         **({'sin_cuota': True} if 'cuota_espera_s' in m else {}),
                                         **({'escalado': True} if escalado else {})})
                    cfg_usada = cfg_recuperable
                    m = {'modelos': {}}
        if not codigo:
            recuperar_cuota(root, arnes(a, cfg_usada), cfg_usada.get('model') or 'predeterminado')
        if not ultimo_registrado or cuota is not None:
            registrar(root, {'fecha': ahora(), 'paso': paso, 'id': arg, 'rama': git('branch', '--show-current'),
                             'rol': rol, 'arnes': a.cmd or arnes(a, cfg_usada),
                             'modelo': cfg_usada.get('model') or 'predeterminado', 'codigo': codigo, **m,
                             **({'escalado': True} if escalado else {}),
                             **({'sin_cuota': True, 'espera_s': cuota} if cuota else {})})
        if paso_completado:
            print(f'[orquestar] paso completado en disco a pesar del retorno {codigo} del arnés; continúo.', flush=True)
            sin_progreso = 0
            esperado = 0
            recuperaciones_analisis.pop(clave_analisis, None)
            continue
        if cuota is not None and esperado + cuota <= a.espera_max * 3600:
            esperado += cuota
            marcas = marcas_cuota(root, fecha_estado(ahora()))
            clave = (arnes(a, cfg_usada), cfg_usada.get('model') or 'predeterminado')
            causas = [marcas[clave]] if clave in marcas else []
            nuevas = leer_metricas(root)[contexto_cuota['desde']:]
            for fila in nuevas:
                if (fila.get('tipo') == 'agente' and fila.get('cuota_espera_s') is not None
                        and fila.get('cuota_espera_s') == cuota):
                    marca = marcas.get((fila.get('arnes'), fila.get('modelo_cuota')))
                    if marca:
                        causas.append(marca)
            if not any(marca['origen'] == 'sin créditos' and marca['hasta'] > fecha_estado(ahora())
                       for marca in causas):
                avisar(root, 'cuota', f'⏳ Sin cuota en "{paso}" {arg or ""}: espero hasta las '
                                      f'{datetime.now() + timedelta(seconds=cuota):%H:%M} y reintento.')
            inicio = time.monotonic()
            seguir = esperar(root, cuota, cuotas_esperadas=contexto_cuota)
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
                recuperaciones_analisis.pop(clave_analisis, None)
                continue
            motivo = (f'sin cuota tras esperar {esperado // 3600} h (--espera-max)' if cuota is not None
                      else '¿autenticación, red?')
            return parar(root, 'cuota' if cuota is not None else 'error',
                         f'el arnés terminó con código {codigo or 1} ({motivo}). Relanza cuando se resuelva.'
                         + (f'\nÚltima salida del arnés:\n{salida[-2000:]}' if cuota is None else ''))
        esperado = 0

        if firma(root, a.docs) == antes:
            if recuperacion is not None:
                recuperacion['intentos'] += 1
                print(f'[orquestar] {paso} {arg or ""}: sin progreso '
                      f'({recuperacion["intentos"]}/{a.reintentos})', flush=True)
                if recuperacion['intentos'] >= a.reintentos:
                    if recuperacion['indice'] + 1 < len(recuperacion['perfiles']):
                        recuperacion['indice'] += 1
                        recuperacion['intentos'] = 0
                        recuperacion['perfil_iniciado'] = False
                    else:
                        diagnostico = diagnostico_analisis(recuperacion, a.reintentos)
                        if paso in ('especificar', 'revisar-tarea') and arg:
                            print(f'[orquestar] {diagnostico}', flush=True)
                            bloquear_sin_progreso(root, arg, a.reintentos, salida, contexto=diagnostico)
                            recuperaciones_analisis.pop(clave_analisis, None)
                        else:
                            return parar(root, 'error', diagnostico)
                continue
            sin_progreso += 1
            print(f'[orquestar] sin progreso ({sin_progreso}/{a.reintentos})')
            if sin_progreso >= a.reintentos:
                if paso in ('task-dev', 'bug-fix') and arg:
                    dif_actual = dificultad_de(root, arg)
                    if dif_actual in ('sencilla', 'media'):
                        nueva_dif = promover_dificultad(root, arg, motivo=f'tras {sin_progreso} intentos sin progreso')
                        if nueva_dif:
                            sin_progreso = 0
                            continue
                    bloquear_sin_progreso(root, arg, sin_progreso, salida)
                    sin_progreso = 0
                    continue
                return parar(root, 'error', f'"{paso}" no avanza tras {a.reintentos} intentos.')
        else:
            sin_progreso = 0
            recuperaciones_analisis.pop(clave_analisis, None)
    return parar(root, 'error', f'alcanzado --max-pasos={a.max_pasos}.')


if __name__ == '__main__':
    sys.exit(main())
