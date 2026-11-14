#!/usr/bin/env python3
"""Orquestador ligero de Adevv: estado desde disco, modelos con reserva, métricas y revisión directa."""

import argparse
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace
import unicodedata
import urllib.parse
import urllib.request

# Soporte de importación tanto desde paquete instalado como desde ejecución directa del script
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path and (_REPO_ROOT / "adevv").is_dir():
    sys.path.insert(0, str(_REPO_ROOT))

from adevv import contexto_ejecucion, registro_metricas, yaml_lite  # noqa: E402
from adevv.revisiones import (  # noqa: E402
    EVIDENCIAS,
    carpetas_maestras,
    clave_version,
    declaracion,
    diagnostico_revision,
    evidencia_vigente,
    huella_producto,
    motivo_informe,
    motivo_revision,
    nombre_version,
    registrar_evidencia,
)
from adevv import store as _adevv_store  # noqa: E402


def get_active_version_dir() -> Path:
    return _adevv_store.get_active_version_dir()


def _cargar_hermano(nombre: str):
    spec = importlib.util.spec_from_file_location(f"adevv_{nombre}", Path(__file__).with_name(f"{nombre}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


metricas = _cargar_hermano("metricas")
perfiles = _cargar_hermano("perfiles")
intervencion = _cargar_hermano("intervencion")

yaml = yaml_lite
winreg = perfiles.winreg
ARNESES = perfiles.ARNESES
ArnesAusente = perfiles.ArnesAusente
ahora = perfiles.ahora
fecha_estado = perfiles.fecha_estado
config = perfiles.config
lista_reservas = perfiles.lista_reservas
ajustes = perfiles.ajustes
con_modelo = perfiles.con_modelo
base_comando_agente = perfiles.base_comando_agente
acceso_suscripcion_denegado = perfiles.acceso_suscripcion_denegado
espera_cuota = perfiles.espera_cuota
fallo_cuota = perfiles.fallo_cuota
recuperar_cuota = perfiles.recuperar_cuota
reset_cuotas = perfiles.reset_cuotas
consumo_cuotas = perfiles.consumo_cuotas
configuraciones_con_cuota = perfiles.configuraciones_con_cuota
informe_agentes = perfiles.informe_agentes
extraer_perfil = perfiles.extraer_perfil
lanzar = perfiles.lanzar

SKILL = Path(__file__).resolve().with_name("SKILL.md")
METRICAS = registro_metricas.ARCHIVO
LOG = "orquestar.log"
PID = "orquestar.pid"
PARADA = "orquestar.parar"
ESPERA = "orquestar.espera"
BUZON = "orquestar_buzon.jsonl"
TELEGRAM_SESIONES = "orquestar_telegram.json"
PROMPT_FILE_DEFAULT = "orquestar_prompt.txt"
PRODUCTO = "docs/review/versions/{v}-producto.md"
_GATEWAY_SOLO_AVISOS = "las credenciales globales solo se usan para avisos; configura .env en el proyecto para escuchar"
CERRADO = {"completed", "cancelled", "superseded", "rejected"}
FUERA = CERRADO | {"blocked"}
PROPIOS = (
    METRICAS,
    EVIDENCIAS,
    LOG,
    PID,
    PARADA,
    ESPERA,
    BUZON,
    TELEGRAM_SESIONES,
    PROMPT_FILE_DEFAULT,
    "telegram.pid",
    "telegram.log",
    "telegram.parar",
    intervencion.ARCHIVO,
    ".adevv-metricas/",
    ".env",
)


def buscar_ejecutable(nombre: str) -> str | None:
    return perfiles.buscar_ejecutable(nombre, winreg_mod=winreg)


def registrar(root: Path, datos: dict) -> None:
    registro_metricas.registrar(Path(root), datos)


def leer_metricas(root: Path, tolerar_ultima: bool = True) -> list[dict]:
    return registro_metricas.leer_registros(Path(root), tolerar_ultima=tolerar_ultima)


def registrar_ausencia(root: Path, paso: str, posicion: int, cfg_rol: dict) -> None:
    registrar(
        root,
        {
            "tipo": "arnes_ausente",
            "fecha": ahora(),
            "paso": paso,
            "posicion": posicion,
            "arnes": cfg_rol.get("harness", ""),
            "modelo": cfg_rol.get("model") or "predeterminado",
        },
    )


# ------------------------------------------------------------------ git y archivos


def _git_env() -> dict:
    return {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}


def git(*args: str, cwd: Path | None = None) -> str:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=str(cwd or Path.cwd()),
            env=_git_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except OSError:
        return ""


def excluir(root: Path) -> None:
    excl = Path(root) / ".git" / "info" / "exclude"
    if not excl.parent.is_dir():
        return
    actual = excl.read_text(encoding="utf-8", errors="replace") if excl.exists() else ""
    faltan = [p for p in PROPIOS if p not in actual.splitlines()]
    if faltan:
        excl.write_text((actual.rstrip() + "\n" + "\n".join(faltan) + "\n").lstrip("\n"), encoding="utf-8")


def pid_vivo(root: Path, pid_file: str = PID) -> int | None:
    p = Path(root) / pid_file
    if not p.is_file():
        return None
    try:
        pid = int(p.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    if pid <= 0:
        return None
    if os.name == "nt":
        try:
            import ctypes

            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not h:
                return None
            codigo = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(codigo))
            ctypes.windll.kernel32.CloseHandle(h)
            return pid if (ok and codigo.value == 259) else None
        except Exception:
            return None
    try:
        os.kill(pid, 0)
        return pid
    except OSError:
        return None


def es_propietario_pid(root: Path, pid_file: str = PID) -> bool:
    p = Path(root) / pid_file
    try:
        return p.is_file() and int(p.read_text(encoding="utf-8").strip()) == os.getpid()
    except (OSError, ValueError):
        return False


def _version_activa_distinta(script: Path) -> tuple[Path, str] | None:
    try:
        p = Path(script).resolve()
        home = Path(os.environ.get("ADEVV_HOME") or Path.home() / ".adevv").resolve()
        versions = home / "versions"
        rel = p.relative_to(versions)
        version_dir = versions / rel.parts[0]
        datos = json.loads((home / "active.json").read_text(encoding="utf-8"))
        version = datos.get("version") if isinstance(datos, dict) else None
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
            return None
        destino = (versions / version / p.relative_to(version_dir)).resolve()
        if destino != p and destino.is_file() and destino.is_relative_to(versions / version):
            return destino, version
    except (OSError, ValueError, IndexError, RuntimeError):
        return None
    return None


def recargar_version(script: Path, root: Path, pid_file: str, estado_recarga: dict, etiqueta: str) -> bool:
    nueva = _version_activa_distinta(script)
    if nueva is None:
        return False
    destino, version = nueva
    if tuple(int(n) for n in version.split(".")) < (0, 5, 0):
        return False
    root = Path(root).resolve()
    if not es_propietario_pid(root, pid_file):
        return False
    argumentos = list(sys.argv[1:])
    try:
        texto = destino.read_text(encoding="utf-8")
    except OSError:
        return False
    for a in argumentos:
        op = a.split("=", 1)[0]
        if op.startswith("--") and f"'{op}'" not in texto and f'"{op}"' not in texto:
            return False
    pid = root / pid_file
    temporal = pid.with_suffix(".recarga.tmp")
    datos = {"root": str(root), "script": str(destino), "estado": estado_recarga}
    env = {**os.environ, "ADEVV_RECARGA": json.dumps(datos), "PYTHONIOENCODING": "utf-8"}
    opciones = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    registro = root / ("telegram.log" if etiqueta == "gateway" else LOG)
    hijo = None
    try:
        with registro.open("a", encoding="utf-8") as log:
            hijo = subprocess.Popen(
                [sys.executable, "-u", str(destino), *argumentos],
                cwd=root,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                **opciones,
            )
            temporal.write_text(str(hijo.pid), encoding="utf-8")
            os.replace(temporal, pid)
    except OSError:
        if hijo is not None:
            hijo.terminate()
            hijo.wait()
        temporal.unlink(missing_ok=True)
        return False
    return True


def recibir_recarga(root: Path, pid_file: str, script: Path):
    texto = os.environ.pop("ADEVV_RECARGA", None)
    if texto is None:
        return None
    datos = json.loads(texto)
    if datos["root"] != str(Path(root).resolve()) or datos["script"] != str(Path(script).resolve()):
        raise ValueError("Transferencia de recarga destinada a otro proceso")
    for _ in range(100):
        if es_propietario_pid(root, pid_file):
            return datos["estado"]
        time.sleep(0.05)
    raise RuntimeError("No se publicó el PID de la recarga")


# ------------------------------------------------------------------ backlog y estado


def vkey(valor):
    return clave_version(valor)


def frontmatter(path: Path | None) -> dict:
    return perfiles.frontmatter_ficha(path)


def backlog_dirs(root: Path) -> tuple[Path, Path]:
    return carpetas_maestras(Path(root))


def fichero_de(root: Path, iid: str) -> Path | None:
    if not iid:
        return None
    patron = re.compile(rf"^{re.escape(iid)}(?:[-.]|$)")
    for carpeta in backlog_dirs(root):
        if not carpeta.is_dir():
            continue
        for f in sorted(carpeta.glob("*.md")):
            if patron.match(f.stem) or str(frontmatter(f).get("id") or "") == iid:
                return f
    return None


def backlog(root: Path) -> list[dict]:
    root = Path(root)
    tasks_dir, bugs_dir = backlog_dirs(root)
    items = []
    for carpeta, paso_def in ((bugs_dir, "bug-fix"), (tasks_dir, "task-dev")):
        if not carpeta.is_dir():
            continue
        for f in sorted(carpeta.glob("*.md")):
            fm = frontmatter(f)
            iid = str(fm.get("id") or "").strip()
            if not iid or fm.get("parent_id"):
                continue
            deps = fm.get("depende_de")
            if isinstance(deps, str):
                deps = [deps] if deps.strip() else []
            elif not isinstance(deps, list):
                deps = []
            try:
                peso = int(fm.get("weight", 100))
            except (TypeError, ValueError):
                peso = 100
            items.append(
                {
                    "id": iid,
                    "title": str(fm.get("title") or iid),
                    "version": str(fm.get("version") or "").strip(),
                    "status": str(fm.get("status") or "backlog").strip().lower(),
                    "paso": "bug-fix" if iid.startswith("B-") else paso_def,
                    "dificultad": str(fm.get("dificultad") or "media").strip().lower(),
                    "weight": peso,
                    "depende_de": [str(d).strip() for d in deps if str(d).strip()],
                    "pendiente_de": str(fm.get("pendiente_de") or "").strip(),
                    "path": f,
                }
            )
    return items


def errores_dependencias(items: list[dict]) -> list[str]:
    por_id = {i["id"]: i for i in items}
    errores = []
    for item in items:
        if item.get("status") in CERRADO:
            continue
        vk_i = vkey(item.get("version"))
        for dep in item.get("depende_de") or ():
            if dep not in por_id:
                errores.append(f"{item['id']} depende de {dep}, que no existe")
                continue
            vk_d = vkey(por_id[dep].get("version"))
            if vk_i and vk_d and vk_d > vk_i:
                errores.append(
                    f"{item['id']} ({item['version']}) depende de {dep} en versión posterior ({por_id[dep]['version']})"
                )
    # Ciclos simples
    visitados = {}

    def dfs(nid: str) -> bool:
        est = visitados.get(nid, 0)
        if est == 1:
            return True
        if est == 2 or nid not in por_id:
            return False
        visitados[nid] = 1
        for d in por_id[nid].get("depende_de") or ():
            if dfs(d):
                return True
        visitados[nid] = 2
        return False

    for i in items:
        if dfs(i["id"]):
            errores.append(f"Ciclo de dependencias detectado en {i['id']}")
            break
    return errores


def revisada(root: Path, iid: str) -> bool:
    root = Path(root)
    return motivo_revision(root, iid, fichero_de(root, iid), backlog_dirs(root)) == ""


def decision_producto(path: Path) -> str:
    if not Path(path).is_file():
        return ""
    for linea in Path(path).read_text(encoding="utf-8", errors="replace").splitlines()[:10]:
        m = re.search(r"Decisi[oó]n\s*:\**\s*(PENDIENTE|APLICAR|APLICADA)\b", linea, re.I)
        if m:
            return m.group(1).upper()
    return ""


def _producto_activa(root: Path, version: str) -> bool:
    prod = config(root).get("producto")
    if prod is True:
        return True
    if isinstance(prod, list):
        return any(vkey(x) == vkey(version) for x in prod)
    return False


def estado(root: Path, docs: str = "docs/requirements") -> tuple:
    """Deduce del disco la siguiente acción sin efectos secundarios."""
    root = Path(root)
    try:
        contexto_ejecucion.cargar_politica(root)
    except ValueError as exc:
        return ("PARAR", f"Política de ejecución inválida: {exc}")

    if not (root / "task_config.yaml").is_file():
        return ("PARAR", "Falta task_config.yaml en la raíz del proyecto.")

    docs_dir = root / docs
    if (docs_dir / "requirements.md").is_file():
        if not (docs_dir / "req_analysis.md").is_file():
            return ("PASO", "ciclo-requisitos", None)
        if not (docs_dir / "platform_plan.md").is_file():
            return ("PASO", "platform-plan", None)
        rev_plat = docs_dir / "platform_review.md"
        if not rev_plat.is_file() or motivo_informe(rev_plat) not in ("",):
            if rev_plat.is_file() and motivo_informe(rev_plat) == "informe rechazado":
                return ("PARAR", f"Revisión de plataforma rechazada en {rev_plat.relative_to(root).as_posix()}.")
            return ("PASO", "revisar-plataforma", None)
        if not (docs_dir / "work_plan.md").is_file():
            return ("PASO", "work-plan", None)

    items = backlog(root)
    if (docs_dir / "requirements.md").is_file() and not items:
        return ("PASO", "work-plan", None)
    errs = errores_dependencias(items)
    if errs:
        return ("PARAR", f"Dependencias inválidas en el backlog: {'; '.join(errs)}")

    abiertas = sorted({vkey(i["version"]) for i in items if vkey(i["version"]) and i["status"] not in CERRADO})
    rama_actual = git("branch", "--show-current", cwd=root)
    if rama_actual.startswith(("release/", "hotfix/")):
        vk_rama = vkey(rama_actual.split("/", 1)[1])
        if vk_rama and any(vkey(i["version"]) == vk_rama for i in items) and (not abiertas or vk_rama <= abiertas[0]):
            abiertas = [vk_rama, *[x for x in abiertas if x != vk_rama]]

    if not abiertas:
        return ("FIN", "No quedan tareas con versión pendientes.")

    vk = abiertas[0]
    v = nombre_version(vk)
    prefijos_validos = (f"release/{v}", f"hotfix/{v}", f"release/v{vk[0]}.{vk[1]}")
    if not rama_actual or not any(rama_actual == p for p in prefijos_validos):
        return ("PASO", "start-version", v)

    suyas = [i for i in items if vkey(i["version"]) == vk]
    por_id = {i["id"]: i for i in items}

    # 1. Revisiones pendientes sobre ítems ya completados (solo superficies críticas o con informe rechazado)
    for item in suyas:
        if item["status"] == "completed" and not revisada(root, item["id"]):
            return ("PASO", "revisar-tarea", item["id"], rama_actual)

    # 2. Siguiente tarea o bug elegible (bugs primero, luego por weight)
    elegibles = [
        i
        for i in suyas
        if i["status"] in ("in_progress", "planned")
        and all(por_id.get(d, {}).get("status") == "completed" for d in i["depende_de"])
    ]
    if elegibles:
        elegibles.sort(
            key=lambda i: (
                0 if i["paso"] == "bug-fix" else 1,
                0 if i["status"] == "in_progress" else 1,
                i["weight"],
                i["id"],
            )
        )
        sig = elegibles[0]
        return ("PASO", sig["paso"], sig["id"], rama_actual)

    # 3. Sin tareas elegibles: comprobar bloqueos antes del cierre
    bloqueadas = [i["id"] for i in suyas if i["status"] == "blocked"]
    en_espera = [i["id"] for i in suyas if i["status"] not in FUERA]
    if bloqueadas or en_espera:
        partes = []
        if bloqueadas:
            partes.append(f"bloqueadas {', '.join(bloqueadas)}")
        if en_espera:
            partes.append(f"en espera {', '.join(en_espera)}")
        return ("PARAR", f"Bloqueos en {v}: {'; '.join(partes)}.")

    # 4. Cierre de versión: revisión transversal y producto opcional
    arq = root / f"docs/review/versions/{v}-arquitectura.md"
    if not arq.is_file():
        return ("PASO", "revisar-version", v, rama_actual)
    mot_arq = motivo_informe(arq)
    if mot_arq == "informe rechazado":
        return ("PARAR", f"Revisión de versión {v} rechazada en docs/review/versions/{v}-arquitectura.md.")
    if mot_arq:
        return ("PASO", "revisar-version", v, rama_actual)

    informe_prod = root / PRODUCTO.format(v=v)
    if _producto_activa(root, v) and not informe_prod.is_file():
        return ("PASO", "revisar-producto", v, rama_actual)
    dec_prod = decision_producto(informe_prod)
    if dec_prod == "APLICAR":
        return ("PASO", "aplicar-producto", v, rama_actual)
    if dec_prod == "PENDIENTE":
        return (
            "PARAR",
            f"Versión {v} terminada. Revisa docs/review/versions/{v}-revision.md y decide {PRODUCTO.format(v=v)}.",
        )

    return (
        "PARAR",
        f"Versión {v} terminada. Revisa docs/review/versions/{v}-revision.md: registra defectos con /bug-add o cierra con /release, y relanza.",
    )


# ------------------------------------------------------------------ prompts y verificación


def es_repositorio_fuente_adevv(root: Path) -> bool:
    root = Path(root)
    return (root / "adevv" / "_build.py").is_file() and (root / "skills" / "orquestar" / "SKILL.md").is_file()


def es_carpeta_personal(root: Path) -> bool:
    sim = os.environ.get("ADEVV_SIMULATED_HOME")
    if sim and Path(sim).resolve() == Path(root).resolve():
        return True
    return Path(root).resolve() == Path.home().resolve()


def es_raiz_de_unidad(root: Path) -> bool:
    sim = os.environ.get("ADEVV_SIMULATED_DRIVE_ROOT")
    if sim and Path(sim).resolve() == Path(root).resolve():
        return True
    p = Path(root).resolve()
    return p.parent == p


def construir_prompt_paso(root: Path, paso: str, arg: str | None) -> str:
    """Construye el mandato directo para un paso citando rutas absolutas instaladas."""
    root = Path(root)
    version_dir = get_active_version_dir()
    dif = perfiles.dificultad_de(root, arg, fichero_de)
    rol, _ = perfiles.rol_de(root, paso, dificultad=dif, iid=arg, fichero_fn=fichero_de)
    persona = (version_dir / "agents" / f"{rol}.md").resolve()
    skill_orquestar = (version_dir / "skills" / "orquestar" / "SKILL.md").resolve()
    skills_dir = (version_dir / "skills").resolve()
    politica = contexto_ejecucion.cargar_politica(root)

    cabecera = (
        f'Lee "{persona}" y actúa como ese agente; ignora el modelo de su frontmatter. ' if persona.is_file() else ""
    )
    args_str = f' con "{arg}"' if arg else ""
    cuerpo = (
        f'Lee "{skill_orquestar}" y ejecuta en modo orquestado el paso "{paso}"{args_str}. '
        f'Las skills que cite (/nombre) están en "{skills_dir}/<nombre>/SKILL.md". '
        'No hagas preguntas salvo bloqueo real externo (`adevv orquestar --preguntar <ID> "<pregunta>"`). '
        'Verifica con `adevv orquestar --verificar "<comando de pruebas>"` y, si necesitas invocar a Hades manualmente, usa `adevv orquestar --agente hades`.'
    )
    aviso_fuente = (
        "\nEdita el árbol de trabajo de este repositorio, en cualquier ruta que haga falta "
        "(skills/, agents/, workflows/, adevv/, tests/, docs/…), nunca la copia instalada desde la que lees skills y agentes."
        if es_repositorio_fuente_adevv(root)
        else ""
    )
    contexto_extra = ""
    if arg and paso in ("task-dev", "bug-fix"):
        rev = root / "docs" / "review" / "code_reviews" / f"{arg}-code-review.md"
        if rev.is_file() and motivo_informe(rev) == "informe rechazado":
            contexto_extra = (
                f"\n\nCorrige los hallazgos pendientes en `{rev.relative_to(root).as_posix()}` antes de cerrar."
            )
    return f"{cabecera}{cuerpo}{aviso_fuente}\n\nPolítica activa ({politica['path']}):\n{politica['text'].strip()}{contexto_extra}"


def construir_prompt_agente(root: Path, rol: str, prompt: str) -> str:
    """Construye el prompt para un rol específico (--agente o revisión directa)."""
    root = Path(root)
    version_dir = get_active_version_dir()
    paso = os.environ.get("ORQUESTAR_PASO", "")
    iid = os.environ.get("ORQUESTAR_ID", "")
    dif = perfiles.dificultad_de(root, iid, fichero_de) if iid else "media"
    cfg = ajustes(config(root).get(rol, {}), paso, dificultad=dif)
    inst = cfg.get("instructions")
    if inst:
        p_inst = Path(inst) if Path(inst).is_absolute() else (root / inst).resolve()
        instrucciones_str = str(p_inst)
    else:
        instrucciones_str = str((version_dir / "agents" / f"{rol}.md").resolve())
    skills_dir = (version_dir / "skills").resolve()
    cabecera = (
        f'Lee "{instrucciones_str}" y actúa como ese agente; ignora el modelo de su frontmatter. '
        f'Las skills están en "{skills_dir}/<nombre>/SKILL.md".\n\n'
    )
    if es_repositorio_fuente_adevv(root):
        cabecera += (
            "Edita el árbol de trabajo de este repositorio, en cualquier ruta que haga falta "
            "(skills/, agents/, workflows/, adevv/, tests/, docs/…), nunca la copia instalada desde la que lees skills y agentes.\n\n"
        )
    return cabecera + prompt.strip()


def verificar(root: Path, comando: str, iid: str = "") -> int:
    """Ejecuta un comando de verificación reutilizando evidencias de la misma huella de producto."""
    root = Path(root)
    excluir(root)
    huella = huella_producto(root)
    if evidencia_vigente(root, huella, comando):
        registrar(
            root,
            {
                "tipo": "verificacion",
                "fecha": ahora(),
                "id": iid or os.environ.get("ORQUESTAR_ID", ""),
                "comando": comando,
                "arbol": huella,
                "reutilizada": True,
                "codigo": 0,
            },
        )
        print(f"[orquestar] verificación reutilizada en verde ({comando})", flush=True)
        return 0

    t0 = time.monotonic()
    res = subprocess.run(comando, cwd=str(root), shell=True)
    dur = round(time.monotonic() - t0)
    registrar_evidencia(root, huella, comando, res.returncode, dur)
    registrar(
        root,
        {
            "tipo": "verificacion",
            "fecha": ahora(),
            "id": iid or os.environ.get("ORQUESTAR_ID", ""),
            "comando": comando,
            "arbol": huella,
            "reutilizada": False,
            "codigo": res.returncode,
            "duracion_s": dur,
        },
    )
    return res.returncode


# ------------------------------------------------------------------ invocación de roles y pasos directos


def _invocar_con_reservas(
    root: Path, rol: str, paso: str, iid: str, prompt_final: str, cmd_override: str | None = None
) -> tuple[int, dict, str]:
    """Ejecuta un rol probando reservas ante cuota agotada, acceso denegado o arnés ausente."""
    dif = perfiles.dificultad_de(root, iid, fichero_de)
    _, cfg_base = perfiles.rol_de(root, paso, dificultad=dif, iid=iid, fichero_fn=fichero_de, rol_explicito=rol)
    if cmd_override:
        codigo, m, salida = lanzar(cmd_override, root, "custom")
        return codigo, {**m, "arnes": "custom", "modelo": "custom"}, salida

    candidatos = [cfg_base] + lista_reservas(cfg_base)
    disponibles = configuraciones_con_cuota(root, candidatos)
    if not disponibles:
        return 75, {"sin_cuota": True, "modelos": {}}, "Todos los candidatos del rol están en espera de cuota."

    ultimo_error = (1, {"modelos": {}}, "Sin candidatos ejecutables.")
    for idx, cand in enumerate(disponibles):
        harness = cand.get("harness", "agy")
        modelo = cand.get("model") or "predeterminado"
        plantilla = (
            base_comando_agente(harness, "{prompt}")
            if rol in ("hades", "clio", "cronos")
            else None
        ) or ARNESES.get(harness)
        if not plantilla:
            continue
        exe = buscar_ejecutable(plantilla[0])
        if not exe:
            registrar_ausencia(root, paso, idx, cand)
            ultimo_error = (127, {"modelos": {}}, f"Arnés ausente: {plantilla[0]}")
            continue

        base_cmd = [exe] + [(prompt_final if tok == "{prompt}" else tok) for tok in plantilla[1:]]
        cmd = con_modelo(base_cmd, harness, cand)
        entrada = None if "{prompt}" in plantilla[1:] else prompt_final
        env = os.environ.copy()
        env["ORQUESTAR_PASO"] = paso
        env["ORQUESTAR_ID"] = iid or ""
        if harness == "codex" and os.name == "nt":
            env.pop("CODEX_WINDOWS_REGISTERED_CORE", None)
        timeout = float(cand["timeout_s"]) if cand.get("timeout_s") else None

        codigo, m, salida = lanzar(cmd, root, harness, entrada=entrada, timeout=timeout, env=env)
        m["arnes"] = harness
        m["modelo"] = modelo

        if codigo == 124:
            return codigo, m, salida
        if codigo and acceso_suscripcion_denegado(harness, salida):
            ultimo_error = (codigo, {**m, "acceso_denegado": True}, salida)
            continue
        if codigo and espera_cuota(salida) is not None:
            datos_cuota = fallo_cuota(root, harness, modelo, salida)
            m.update(datos_cuota)
            registrar(
                root,
                {
                    **m,
                    "tipo": "agente" if rol == "hades" else "paso",
                    "fecha": ahora(),
                    "rol": rol,
                    "paso": paso,
                    "id": iid,
                    "codigo": codigo,
                },
            )
            ultimo_error = (75, m, salida)
            continue

        if codigo == 0:
            recuperar_cuota(root, harness, modelo)
        return codigo, m, salida

    return ultimo_error


def agente(root: Path, rol: str, prompt: str) -> int:
    """Invoca un rol (p. ej. hades) directamente desde CLI y registra sus métricas."""
    root = Path(root)
    excluir(root)
    paso = os.environ.get("ORQUESTAR_PASO", "manual")
    iid = os.environ.get("ORQUESTAR_ID", "")
    mandato = construir_prompt_agente(root, rol, prompt)
    codigo, m, salida = _invocar_con_reservas(root, rol, paso, iid, mandato)
    veredicto, _ = declaracion(salida)
    if not veredicto and iid and rol == "hades":
        inf = root / "docs" / "review" / "code_reviews" / f"{iid}-code-review.md"
        if inf.is_file():
            veredicto, _ = declaracion(inf.read_text(encoding="utf-8", errors="replace"))
    if not m.get("sin_cuota"):
        registrar(
            root,
            {
                **m,
                "tipo": "agente",
                "fecha": ahora(),
                "rol": rol,
                "paso": paso,
                "id": iid,
                "codigo": codigo,
                **({"veredicto": veredicto} if veredicto else {}),
            },
        )
    if salida:
        print(salida, flush=True)
    return codigo


def _sellar_y_commitear_informe(
    root: Path, ruta_informe: Path, mensaje_commit: str, extras: list[Path] | None = None
) -> str:
    """Asegura huella de producto en el informe de Hades y realiza commit directo desde Python."""
    if not ruta_informe.is_file():
        return ""
    texto = ruta_informe.read_text(encoding="utf-8", errors="replace")
    veredicto, huella_existente = declaracion(texto)
    if not veredicto:
        return ""
    huella = huella_producto(root)
    if not huella_existente:
        lineas = texto.splitlines()
        lineas.insert(1, f"Producto revisado: {huella}")
        ruta_informe.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    if (root / ".git").exists():
        rutas_git = [str(ruta_informe.relative_to(root))]
        for ex in extras or ():
            if ex.is_file():
                rutas_git.append(str(ex.relative_to(root)))
        subprocess.run(["git", "add", *rutas_git], cwd=root, env=_git_env(), check=False)
        subprocess.run(
            ["git", "commit", "-qm", mensaje_commit],
            cwd=root,
            env=_git_env(),
            check=False,
        )
    return veredicto


def _asegurar_revision_version(root: Path, version: str) -> Path:
    rev_path = root / f"docs/review/versions/{version}-revision.md"
    if not rev_path.is_file():
        rev_path.parent.mkdir(parents=True, exist_ok=True)
        cerrados = [
            f"- **{i['id']}**: {i['title']}"
            for i in backlog(root)
            if vkey(i["version"]) == vkey(version) and i["status"] == "completed"
        ]
        cuerpo = "\n".join(cerrados) or "- Sin tareas adicionales registradas."
        rev_path.write_text(
            f"# Revisión final {version}\n\n## Tareas completadas\n{cuerpo}\n\n"
            f"## Validación funcional\n- Revisión transversal aprobada en `docs/review/versions/{version}-arquitectura.md`.\n",
            encoding="utf-8",
        )
    return rev_path


def _ejecutar_revision_directa(
    root: Path, paso: str, arg: str | None, rama: str, cmd_override: str | None = None
) -> tuple[str, dict]:
    """Invoca directamente a Hades desde Python sin agente secretario intermedio."""
    version_dir = get_active_version_dir()
    skills_dir = (version_dir / "skills").resolve()
    if paso == "revisar-plataforma":
        destino = root / "docs/requirements/platform_review.md"
        prompt = (
            f'Lee "{skills_dir}/review-design/SKILL.md" y revisa `docs/requirements/platform_plan.md` '
            f"frente a `docs/requirements/requirements.md`. Escribe el informe en `{destino.relative_to(root).as_posix()}`."
        )
        msg = "docs(review): registrar revision de plataforma de Hades"
    elif paso == "revisar-tarea":
        destino = root / f"docs/review/code_reviews/{arg}-code-review.md"
        ficha = fichero_de(root, arg)
        rel_ficha = ficha.relative_to(root).as_posix() if ficha else arg
        prompt = (
            f'Lee "{skills_dir}/review-code/SKILL.md" y revisa los cambios de `{arg}` (`{rel_ficha}`). '
            f"Escribe el informe conciso en `{destino.relative_to(root).as_posix()}` empezando con `**Veredicto:** APROBADO` o `**Veredicto:** RECHAZADO`."
        )
        msg = f"docs(review): [{arg}] - registrar revision de codigo de Hades"
    else:  # revisar-version
        destino = root / f"docs/review/versions/{arg}-arquitectura.md"
        prompt = (
            f'Lee "{skills_dir}/review-code/SKILL.md" y revisa transversalmente `git diff main...{rama}` '
            f"(solo duplicados entre tareas, incoherencias de capas o defectos reales). "
            f"Escribe el informe en `{destino.relative_to(root).as_posix()}` empezando con `**Veredicto:** APROBADO` o `**Veredicto:** RECHAZADO`."
        )
        msg = f"docs(review): revisar-version {arg}"

    bytes_antes = destino.read_bytes() if destino.is_file() else None
    mandato = construir_prompt_agente(root, "hades", prompt)
    codigo, m, salida = _invocar_con_reservas(root, "hades", paso, arg or "", mandato, cmd_override=cmd_override)
    if m.get("sin_cuota"):
        return "CUOTA", m

    v_out, _ = declaracion(salida) if salida else ("", None)
    archivo_cambio = destino.is_file() and destino.read_bytes() != bytes_antes
    if not archivo_cambio:
        if v_out:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(salida.strip() + "\n", encoding="utf-8")
            archivo_cambio = True
        elif bytes_antes is not None and codigo != 0:
            registrar(
                root,
                {
                    **m,
                    "tipo": "agente",
                    "fecha": ahora(),
                    "rol": "hades",
                    "paso": paso,
                    "id": arg or "",
                    "rama": rama,
                    "codigo": codigo,
                },
            )
            return "SIN_PROGRESO", m

    extras = [_asegurar_revision_version(root, str(arg))] if paso == "revisar-version" and arg else []
    veredicto = _sellar_y_commitear_informe(root, destino, msg, extras=extras)
    registrar(
        root,
        {
            **m,
            "tipo": "agente",
            "fecha": ahora(),
            "rol": "hades",
            "paso": paso,
            "id": arg or "",
            "rama": rama,
            "codigo": codigo,
            **({"veredicto": veredicto} if veredicto else {}),
        },
    )
    if veredicto == "APROBADO":
        return "OK", m
    if veredicto == "RECHAZADO":
        return "RECHAZADO", m
    return "SIN_PROGRESO", m


def _validar_puerta_python(root: Path) -> str:
    """Comprobación determinista rápida tras desarrollo: árbol limpio y ruff en .py tocados."""
    if not (root / ".git").exists():
        return ""
    sucio = git("status", "--porcelain", cwd=root)
    lineas_sucias = [l for l in sucio.splitlines() if l.strip() and not any(p in l for p in PROPIOS)]
    if lineas_sucias:
        return f"árbol Git sucio tras el paso ({lineas_sucias[0].strip()})"
    cambiados = [
        f
        for f in git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD", cwd=root).splitlines()
        if f.endswith(".py") and (root / f).is_file()
    ]
    if cambiados and shutil.which("ruff"):
        r = subprocess.run(
            [sys.executable, "-m", "ruff", "check", *cambiados], cwd=root, capture_output=True, text=True
        )
        if r.returncode != 0:
            return f"ruff check en rojo sobre {', '.join(cambiados[:3])}"
    return ""


# ------------------------------------------------------------------ Telegram y buzón


class Credenciales(tuple):
    origen = "proyecto"


def credenciales(root: Path) -> Credenciales:
    env_file = Path(root) / ".env"
    local = {}
    if env_file.is_file():
        for l in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
            l = l.strip()
            if l and not l.startswith("#") and "=" in l:
                k, v = l.split("=", 1)
                local[k.strip()] = v.strip().strip('"').strip("'")
    tok = local.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    ids_raw = local.get("TELEGRAM_ALLOWED_USER_IDS") or os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "")
    ids = [x.strip() for x in ids_raw.split(",") if x.strip()]
    res = Credenciales((tok, ids))
    res.origen = "proyecto" if "TELEGRAM_BOT_TOKEN" in local else "entorno"
    return res


def firmar(texto: str, extra: str = "") -> str:
    sufijo = f" · {extra}" if extra else ""
    return f"{texto.strip()}\n— adevv{sufijo}"


def enviar(token: str, chat_id, texto: str, markdown: bool = False) -> bool:
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": str(chat_id), "text": texto[:4000]}
    if markdown:
        payload["parse_mode"] = "Markdown"
    try:
        datos = urllib.parse.urlencode(payload).encode("utf-8")
        with urllib.request.urlopen(url, data=datos, timeout=10):
            return True
    except Exception:
        if markdown:
            return enviar(token, chat_id, texto, markdown=False)
        return False


def avisar(root: Path, evento: str, mensaje: str) -> None:
    cfg_tg = config(root).get("telegram")
    if cfg_tg is False:
        return
    if isinstance(cfg_tg, dict) and isinstance(cfg_tg.get("eventos"), list) and evento not in cfg_tg["eventos"]:
        return
    tok, ids = credenciales(root)
    if tok and ids:
        for uid in ids:
            enviar(tok, uid, firmar(f"[{Path(root).name}] {mensaje}"))


def _slug(texto: str) -> str:
    norm = unicodedata.normalize("NFD", texto.lower())
    limpio = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", limpio).strip("-")[:50] or "item"


def apuntar(root: Path, tipo: str, titulo: str, usuario: str, perfil: dict | None = None) -> None:
    root = Path(root)
    excluir(root)
    fila = {"fecha": ahora(), "tipo": tipo, "titulo": titulo.strip(), "usuario": str(usuario)}
    if perfil:
        fila["perfil"] = perfil
    with (root / BUZON).open("a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def ingerir(root: Path) -> list[tuple[str, str]]:
    root = Path(root)
    buzon = root / BUZON
    if not buzon.is_file():
        return []
    lineas = [l for l in buzon.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lineas:
        buzon.unlink(missing_ok=True)
        return []
    cfg_path = root / "task_config.yaml"
    cfg = (yaml_lite.load_yaml(cfg_path) or {}) if cfg_path.is_file() else {}
    prefijo = ((cfg.get("project") or {}).get("prefix") or cfg.get("prefix") or "PRJ").strip()
    tasks_dir, bugs_dir = backlog_dirs(root)
    creados = []
    rutas_creadas = []
    hoy = datetime.now().strftime("%Y-%m-%d")

    for l in lineas:
        d = json.loads(l)
        es_bug = d.get("tipo") == "bug"
        letra = "B" if es_bug else "T"
        destino_dir = bugs_dir if es_bug else tasks_dir
        destino_dir.mkdir(parents=True, exist_ok=True)
        existentes = [
            int(m.group(1))
            for p in (
                *(tasks_dir.glob("*.md") if tasks_dir.is_dir() else ()),
                *(bugs_dir.glob("*.md") if bugs_dir.is_dir() else ()),
            )
            if (m := re.match(rf"^{letra}-{re.escape(prefijo)}-(\d+)\b", p.stem))
        ]
        num = max(existentes, default=0) + 1
        iid = f"{letra}-{prefijo}-{num:04d}"
        ruta = destino_dir / f"{iid}-{_slug(d['titulo'])}.md"
        linea_perfil = f"perfil: {json.dumps(d['perfil'])}\n" if d.get("perfil") else ""
        ruta.write_text(
            f'---\nid: {iid}\ntitle: "{d["titulo"].replace(chr(34), chr(39))}"\n'
            f"type: {'bug' if es_bug else 'funcional'}\nweight: 100\ndificultad: media\n"
            f'{linea_perfil}version: ""\nstatus: backlog\ndepende_de: []\n'
            f"created_at: {hoy}\nupdated_at: {hoy}\n---\n\n# {iid}: {d['titulo']}\n",
            encoding="utf-8",
        )
        creados.append((iid, d["titulo"]))
        rutas_creadas.append(ruta)

    buzon.unlink(missing_ok=True)
    if rutas_creadas and (root / ".git").exists():
        rels = [str(r.relative_to(root)) for r in rutas_creadas]
        subprocess.run(["git", "add", *rels], cwd=root, env=_git_env(), check=False)
        ids_txt = ", ".join(i for i, _ in creados)
        subprocess.run(
            ["git", "commit", "-qm", f"docs(plan): registrar desde buzon ({ids_txt})"],
            cwd=root,
            env=_git_env(),
            check=False,
        )
    return creados


def _proxy_motor():
    return SimpleNamespace(fichero_de=fichero_de, frontmatter=frontmatter, consumo_cuotas=consumo_cuotas, vkey=vkey)


def responder_pregunta(root: Path, usuario: str, argumento: str, autorizados=None) -> str:
    qid, _, texto = (argumento or "").strip().partition(" ")
    ok, msg = intervencion.responder(Path(root), _proxy_motor(), qid, texto, usuario=str(usuario))
    if ok and (Path(root) / ".git").exists():
        ficha = fichero_de(Path(root), qid)
        if not ficha:
            for it in backlog(Path(root)):
                if it["id"] in msg:
                    ficha = it["path"]
                    break
        if ficha:
            subprocess.run(["git", "add", str(ficha.relative_to(root))], cwd=root, env=_git_env(), check=False)
            subprocess.run(
                ["git", "commit", "-qm", f"docs(plan): responder {qid}"], cwd=root, env=_git_env(), check=False
            )
    return msg


def cargar_cierre_version():
    ruta = Path(__file__).resolve().parents[1] / "telegram_gateway" / "cierre_version.py"
    spec = importlib.util.spec_from_file_location("cierre_version", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def leer_espera(root: Path) -> tuple[datetime | None, str]:
    p = Path(root) / ESPERA
    if not p.is_file():
        return None, ""
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return fecha_estado(d["hasta"]), d.get("motivo", "cuota")
    except Exception:
        return None, ""


def parte(root: Path, docs: str = "docs/requirements") -> str:
    """Resumen breve para CLI y Telegram (/estado)."""
    root = Path(root)
    hasta, motivo = leer_espera(root)
    if hasta and hasta > fecha_estado(ahora()):
        marcha = f"esperando ({motivo}) hasta {hasta:%H:%M}"
    else:
        marcha = "en marcha" if pid_vivo(root) else "parado"
    e = estado(root, docs)
    lineas = [f"*{root.name}* · bucle {marcha}", f"*Fase:* {e[0]} " + " ".join(str(x) for x in e[1:3] if x)]
    if e[0] == "PASO" and e[1] == "revisar-tarea":
        diag = diagnostico_revision(root, e[2], fichero_de(root, e[2]), backlog_dirs(root))
        if diag:
            lineas.append(diag)
    items = backlog(root)
    abiertas = sorted({vkey(i["version"]) for i in items if vkey(i["version"]) and i["status"] not in CERRADO})
    for vk in abiertas[:1]:
        suyas = [
            i for i in items if vkey(i["version"]) == vk and i["status"] not in {"cancelled", "superseded", "rejected"}
        ]
        v = max((i["version"] for i in suyas if i.get("version")), key=len, default=f"v{vk[0]}.{vk[1]}")
        tareas = [i for i in suyas if i["paso"] == "task-dev"]
        bugs = [i for i in suyas if i["paso"] == "bug-fix"]
        ct = lambda *s: [i["id"] for i in tareas if i["status"] in s]
        cb = lambda *s: [i["id"] for i in bugs if i["status"] in s]
        ca = lambda *s: [i["id"] for i in suyas if i["status"] in s]
        lineas.append(
            f"*{v}:* {len(ct('completed'))}/{len(tareas)} tareas cerradas, "
            f"{len(cb('completed'))}/{len(bugs)} bugs cerrados"
            + (f" · en curso {', '.join(ca('in_progress'))}" if ca("in_progress") else "")
            + (f" · bloqueadas {', '.join(ca('blocked'))}" if ca("blocked") else "")
        )
    sin_version = [i for i in items if not vkey(i["version"]) and i["status"] not in FUERA]
    lineas.append(f"*Backlog sin versión:* {len(sin_version)}")
    if (root / BUZON).is_file():
        pend = sum(1 for l in (root / BUZON).read_text(encoding="utf-8").splitlines() if l.strip())
        if pend:
            lineas.append(f"*Por registrar:* {pend}")
    return "\n".join(lineas)


# ------------------------------------------------------------------ validación de arranque y bucle


def validar_lanzamiento_bucle(root: Path, docs: str = "docs/requirements") -> None:
    root = Path(root).resolve()
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root,
            env=_git_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if r.returncode == 0 and r.stdout.strip():
            top = Path(r.stdout.strip()).resolve()
            if not os.path.samefile(top, root):
                sys.exit(f"Estás en una subcarpeta de {top}: lanza /orquestar desde la raíz.")
    except OSError:
        pass

    if not (root / "task_config.yaml").is_file():
        reqs = root / docs / "requirements.md"
        if not es_carpeta_personal(root) and not es_raiz_de_unidad(root) and reqs.is_file():
            norm = unicodedata.normalize("NFD", root.name)
            letras = "".join(c for c in norm if unicodedata.category(c) != "Mn" and c.isalpha()).upper()
            prefijo = letras[:3] if len(letras) >= 3 else "PRJ"
            if not (root / ".git").is_dir():
                subprocess.run(["git", "init", "-q"], cwd=root, env=_git_env(), check=True)
            (root / "task_config.yaml").write_text(
                f'project:\n  name: {root.name}\n  prefix: "{prefijo}"\n  version: "v0.0.0"\n\n'
                f"levels:\n  master:\n    path: docs/plan/\n    folders:\n      tasks: tasks/\n      bugs: bugs/\n"
                f'    tasks: tasks/\n    bugs: bugs/\n    id_prefix: "{prefijo}"\n',
                encoding="utf-8",
            )
            gi = root / ".gitignore"
            if not gi.exists():
                gi.write_text(
                    "orquestar.log\norquestar.pid\norquestar.parar\norquestar.espera\n"
                    "orquestar_metricas.jsonl\norquestar_evidencias.jsonl\norquestar_buzon.jsonl*\n"
                    ".env\n__pycache__/\n",
                    encoding="utf-8",
                )
            subprocess.run(["git", "add", "task_config.yaml", ".gitignore"], cwd=root, env=_git_env(), check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Adevv",
                    "-c",
                    "user.email=adevv@local",
                    "commit",
                    "-qm",
                    "chore: inicializar proyecto",
                ],
                cwd=root,
                env=_git_env(),
                check=True,
            )
            print(f"[orquestar] inicializado repositorio Git y task_config.yaml (prefijo: {prefijo})", flush=True)

    cfg = config(root)
    for rol_k, rol_v in cfg.items():
        if isinstance(rol_v, dict) and "instructions" in rol_v:
            inst = rol_v["instructions"]
            p_inst = Path(inst) if Path(inst).is_absolute() else root / inst
            if not p_inst.exists():
                sys.exit(f"orchestration.json: {rol_k}.instructions apunta a {inst}, que no existe.")

    if not es_repositorio_fuente_adevv(root):
        gm = root / ".gitmodules"
        usa_agents = (root / ".agents").exists() or (
            gm.is_file() and ".agents" in gm.read_text(encoding="utf-8", errors="replace")
        )
        if usa_agents:
            sys.exit("Este proyecto aún usa el submódulo .agents: sigue los pasos de migración del README.")

    version_dir = get_active_version_dir()
    nombres_dist = set()
    if (version_dir / "skills").is_dir():
        nombres_dist.update(
            d.name for d in (version_dir / "skills").iterdir() if d.is_dir() and not d.name.startswith(".")
        )
    if (version_dir / "agents").is_dir():
        nombres_dist.update(
            f.stem for f in (version_dir / "agents").rglob("*") if f.is_file() and f.suffix in (".md", ".toml")
        )
    if (version_dir / "workflows").is_dir():
        nombres_dist.update(f.stem for f in (version_dir / "workflows").iterdir() if f.is_file() and f.suffix == ".md")
    if "telegram_gateway" in nombres_dist:
        nombres_dist.add("telegram-gateway")

    ocultan = []
    for c_dir, es_dir in (
        (root / ".claude" / "skills", True),
        (root / ".claude" / "agents", False),
        (root / ".codex" / "skills", True),
        (root / ".codex" / "agents", False),
        (root / ".agent" / "skills", True),
        (root / ".agent" / "workflows", False),
    ):
        if c_dir.exists():
            for item in c_dir.iterdir():
                if (item.name if es_dir else item.stem) in nombres_dist:
                    ocultan.append(os.path.relpath(item, root).replace("\\", "/"))
    if ocultan:
        sys.exit(
            f"Este proyecto tiene skills, agentes o workflows propios que ocultan los de Adevv: {', '.join(sorted(ocultan))}. Bórralos o renómbralos."
        )


def en_fondo(root: Path, argumentos: list[str] | None = None) -> int:
    root = Path(root).resolve()
    validar_lanzamiento_bucle(root)
    vivo = pid_vivo(root)
    if vivo:
        sys.exit(f"Ya hay un bucle en marcha (pid {vivo}).")
    excluir(root)
    (root / PARADA).unlink(missing_ok=True)
    args_extra = [a for a in (argumentos or []) if a != "--fondo"]
    opciones = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    with (root / LOG).open("a", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [sys.executable, "-u", str(Path(__file__).resolve()), *args_extra],
            cwd=str(root),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            **opciones,
        )
    (root / PID).write_text(str(proc.pid), encoding="utf-8")
    print(f"[orquestar] lanzado en segundo plano (pid {proc.pid}); salida en {LOG}", flush=True)
    return 0


def _esperar_cuota_si_procede(root: Path, espera_max: int) -> bool:
    _, bloqueos = consumo_cuotas(root)
    if not bloqueos or espera_max <= 0:
        return False
    proximo = min(bloqueos.values())
    segundos = max(1, int((proximo - fecha_estado(ahora())).total_seconds()))
    if segundos > espera_max:
        return False
    (root / ESPERA).write_text(json.dumps({"hasta": proximo.isoformat(), "motivo": "cuota"}), encoding="utf-8")
    print(f"[orquestar] esperando cuota {segundos}s (hasta {proximo:%H:%M})...", flush=True)
    fin = time.monotonic() + segundos
    while time.monotonic() < fin:
        if (root / PARADA).exists():
            break
        time.sleep(min(5.0, fin - time.monotonic()))
    (root / ESPERA).unlink(missing_ok=True)
    return not (root / PARADA).exists()


def _comando_suite_version(root: Path, test_cli: str | None) -> str:
    if test_cli:
        return test_cli
    cfg_path = root / "task_config.yaml"
    cfg = (yaml_lite.load_yaml(cfg_path) or {}) if cfg_path.is_file() else {}
    return str(((cfg.get("validation") or {}).get("command") or "")).strip()


def bucle(
    root: Path,
    docs: str = "docs/requirements",
    test_cmd: str | None = None,
    max_pasos: int | None = None,
    reintentos: int = 2,
    espera_max: int = 18000,
    cmd_override: str | None = None,
) -> int:
    root = Path(root).resolve()
    validar_lanzamiento_bucle(root, docs=docs)
    if max_pasos == 0:
        return 0
    estado_recibido = recibir_recarga(root, PID, Path(__file__))
    if estado_recibido is None:
        vivo = pid_vivo(root)
        if vivo and vivo != os.getpid():
            sys.exit(f"Ya hay un bucle en marcha (pid {vivo}).")
        excluir(root)
        (root / PID).write_text(str(os.getpid()), encoding="utf-8")
    else:
        excluir(root)
    (root / PARADA).unlink(missing_ok=True)

    fallos_par: dict[tuple, int] = {}
    pasos_hechos = int((estado_recibido or {}).get("pasos", 0))
    suite_cmd = _comando_suite_version(root, test_cmd)

    try:
        while True:
            if (root / PARADA).exists():
                (root / PARADA).unlink(missing_ok=True)
                print("[orquestar] PARAR: detenido a petición (--parar).", flush=True)
                return 0
            if recargar_version(Path(__file__), root, PID, {"pasos": pasos_hechos}, "orquestar"):
                return 0

            ingerir(root)
            est = estado(root, docs)

            # Pasar suite completa de versión una sola vez por huella de producto antes de revisar-version / cerrar
            if est[0] in ("PASO", "PARAR") and suite_cmd:
                es_cierre_version = (est[0] == "PASO" and est[1] == "revisar-version") or (
                    est[0] == "PARAR" and str(est[1]).startswith("Versión ")
                )
                if es_cierre_version and verificar(root, suite_cmd) != 0:
                    msg = "Suite de versión en rojo al cerrar; corrige los fallos o regístralos con /bug-add."
                    print(f"[orquestar] PARAR: {msg}", flush=True)
                    avisar(root, "error", msg)
                    return 1

            if est[0] == "FIN":
                print(f"[orquestar] FIN: {est[1]}", flush=True)
                avisar(root, "fin", est[1])
                return 0
            if est[0] == "PARAR":
                print(f"[orquestar] PARAR: {est[1]}", flush=True)
                avisar(root, "version" if str(est[1]).startswith("Versión ") else "bloqueo", est[1])
                return 1 if not str(est[1]).startswith("Versión ") else 0

            if max_pasos is not None and pasos_hechos >= max_pasos:
                print(f"[orquestar] PARAR: alcanzado --max-pasos={max_pasos}.", flush=True)
                return 0

            paso = est[1]
            arg = est[2] if len(est) > 2 else None
            rama = est[3] if len(est) > 3 else git("branch", "--show-current", cwd=root)
            pasos_hechos += 1
            etiqueta = " ".join(str(x) for x in (paso, arg, rama) if x)
            print(f"\n[orquestar] {pasos_hechos}. PASO: {etiqueta}", flush=True)

            # Pasos de revisión: Hades directo sin agente secretario
            if paso in perfiles.REVISION:
                res_rev, _ = _ejecutar_revision_directa(root, paso, arg, rama, cmd_override=cmd_override)
                if res_rev == "CUOTA":
                    if _esperar_cuota_si_procede(root, espera_max):
                        continue
                    print(f"[orquestar] PARAR: Hades sin cuota en {etiqueta}.", flush=True)
                    return 1
                if res_rev == "OK":
                    fallos_par.pop((paso, arg), None)
                    continue
                if res_rev == "RECHAZADO" and paso == "revisar-tarea" and arg:
                    n = fallos_par.get(("rechazo", arg), 0) + 1
                    fallos_par[("rechazo", arg)] = n
                    ficha = fichero_de(root, arg)
                    if n > reintentos:
                        intervencion._actualizar_estado_ficha(
                            ficha, "blocked", "humano", f"Bloqueado tras {n} rechazos de Hades."
                        )
                        avisar(root, "bloqueo", f"{arg} bloqueada tras {n} rechazos de Hades.")
                    else:
                        intervencion._actualizar_estado_ficha(ficha, "in_progress")
                    if (root / ".git").exists() and ficha:
                        subprocess.run(
                            ["git", "add", str(ficha.relative_to(root))], cwd=root, env=_git_env(), check=False
                        )
                        subprocess.run(
                            ["git", "commit", "-qm", f"docs(plan): reabrir {arg} tras revision"],
                            cwd=root,
                            env=_git_env(),
                            check=False,
                        )
                    continue
                if res_rev == "RECHAZADO" and paso == "revisar-version":
                    msg = f"Hades rechazó revisar-version {arg}; revisa docs/review/versions/{arg}-arquitectura.md."
                    print(f"[orquestar] PARAR: {msg}", flush=True)
                    avisar(root, "bloqueo", msg)
                    return 1

            else:
                huella_antes = (
                    huella_producto(root),
                    tuple((i["id"], i["status"]) for i in backlog(root)),
                    git("branch", "--show-current", cwd=root),
                )
                prompt = construir_prompt_paso(root, paso, arg)
                rol_paso = "artemisa" if paso in perfiles.DESARROLLO else "atenea"
                dif = perfiles.dificultad_de(root, arg, fichero_de)
                codigo, m, salida = _invocar_con_reservas(
                    root, rol_paso, paso, arg or "", prompt, cmd_override=cmd_override
                )
                if salida:
                    print(salida, flush=True)
                if m.get("sin_cuota"):
                    if _esperar_cuota_si_procede(root, espera_max):
                        continue
                    print(f"[orquestar] PARAR: {rol_paso} sin cuota en {etiqueta}.", flush=True)
                    return 1

                error_puerta = _validar_puerta_python(root) if paso in perfiles.DESARROLLO else ""
                huella_despues = (
                    huella_producto(root),
                    tuple((i["id"], i["status"]) for i in backlog(root)),
                    git("branch", "--show-current", cwd=root),
                )
                progreso = huella_despues != huella_antes and not error_puerta
                registrar(
                    root,
                    {
                        **m,
                        "tipo": "paso",
                        "fecha": ahora(),
                        "paso": paso,
                        "id": arg or "",
                        "rama": rama,
                        "rol": rol_paso,
                        "dificultad": dif,
                        "codigo": codigo,
                        "progreso": progreso,
                    },
                )
                if error_puerta and arg:
                    print(f"[orquestar] puerta determinista en rojo para {arg}: {error_puerta}", flush=True)
                    ficha = fichero_de(root, arg)
                    if ficha and frontmatter(ficha).get("status") == "completed":
                        intervencion._actualizar_estado_ficha(
                            ficha, "in_progress", nota=f"Puerta determinista: {error_puerta}"
                        )
                if progreso:
                    fallos_par.pop((paso, arg), None)
                    continue

            # Gestión uniforme de falta de progreso con tope corto
            n_sin = fallos_par.get((paso, arg), 0) + 1
            fallos_par[(paso, arg)] = n_sin
            print(f"[orquestar] {etiqueta}: sin progreso ({n_sin}/{reintentos})", flush=True)
            if n_sin >= reintentos:
                if arg and paso in perfiles.DESARROLLO:
                    ficha = fichero_de(root, arg)
                    intervencion._actualizar_estado_ficha(
                        ficha, "blocked", "humano", f"Bloqueado tras {n_sin} intentos sin progreso."
                    )
                    if (root / ".git").exists() and ficha:
                        subprocess.run(
                            ["git", "add", str(ficha.relative_to(root))], cwd=root, env=_git_env(), check=False
                        )
                        subprocess.run(
                            ["git", "commit", "-qm", f"docs(plan): bloquear {arg} por falta de progreso"],
                            cwd=root,
                            env=_git_env(),
                            check=False,
                        )
                    avisar(root, "bloqueo", f"{arg} bloqueada tras {n_sin} intentos sin progreso.")
                    continue
                msg = f"{etiqueta} detenido tras {n_sin} intentos sin progreso."
                print(f"[orquestar] PARAR: {msg}", flush=True)
                avisar(root, "error", msg)
                return 1
    finally:
        if es_propietario_pid(root):
            (root / PID).unlink(missing_ok=True)
            (root / ESPERA).unlink(missing_ok=True)


# ------------------------------------------------------------------ CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Orquestador ligero de Adevv.")
    ap.add_argument("--root", type=Path, default=Path.cwd(), help="raíz del proyecto")
    ap.add_argument("--docs", default="docs/requirements", help="directorio de documentos de requisitos")
    ap.add_argument("--estado", action="store_true", help="muestra el estado actual y sale")
    ap.add_argument("--parar", action="store_true", help="pide parar al terminar el paso en curso")
    ap.add_argument("--fondo", action="store_true", help="ejecuta el bucle en segundo plano")
    ap.add_argument("--agentes", "--agents", action="store_true", help="muestra agentes configurados y estado de cuotas")
    ap.add_argument("--metricas", "--metrics", nargs="?", const="ultima", help="consulta métricas (ultima, todas, vX.Y)")
    ap.add_argument("--version-filtro", help=argparse.SUPPRESS)
    ap.add_argument("--csv", nargs="?", const="-", help="exporta métricas en CSV")
    ap.add_argument("--verificar", metavar="CMD", help="ejecuta comando con caché por huella de producto")
    ap.add_argument(
        "--agente", choices=("atenea", "artemisa", "hades", "clio", "cronos"), help="invoca directamente a un rol"
    )
    ap.add_argument("--revision", help=argparse.SUPPRESS)
    ap.add_argument("--prompt", help="texto del prompt para --agente")
    ap.add_argument("--prompt-file", type=Path, help="fichero con el prompt para --agente")
    ap.add_argument("--preguntas", action="store_true", help="lista preguntas humanas pendientes")
    ap.add_argument("--preguntar", nargs=2, metavar=("ID", "PREGUNTA"), help="registra bloqueo con pregunta humana")
    ap.add_argument("--responder", nargs=2, metavar=("Q_ID", "RESPUESTA"), help="responde una pregunta humana")
    ap.add_argument("--test", help="comando de suite completa al cerrar versión")
    ap.add_argument("--max-pasos", type=int, help="máximo de pasos a ejecutar")
    ap.add_argument("--reintentos", type=int, default=2, help="intentos máximos sin progreso por ítem")
    ap.add_argument("--espera-max", type=int, default=18000, help="segundos máximos de espera de cuota")
    ap.add_argument("--cmd", help=argparse.SUPPRESS)

    raw_args = list(sys.argv[1:] if argv is None else argv)
    a = ap.parse_args(raw_args)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = a.root.resolve()

    if a.estado:
        est = estado(root, a.docs)
        print(f"[orquestar] {est[0]}: " + " ".join(str(x) for x in est[1:] if x))
        return 0
    if a.parar:
        if pid_vivo(root):
            excluir(root)
            (root / PARADA).touch()
            print("[orquestar] parará al terminar el paso en curso.")
        else:
            (root / PID).unlink(missing_ok=True)
            (root / PARADA).unlink(missing_ok=True)
            print("[orquestar] no hay ningún bucle en marcha.")
        return 0
    if a.agentes:
        print(informe_agentes(root))
        return 0
    if a.metricas is not None:
        alcance = a.version_filtro or a.metricas
        return metricas.mostrar(root, backlog(root), alcance, a.csv, sys.stdout)
    if a.verificar:
        return verificar(root, a.verificar)
    if a.preguntas:
        print(intervencion.consulta(root))
        return 0
    if a.preguntar:
        qid = intervencion.solicitar(
            root, _proxy_motor(), a.preguntar[0], a.preguntar[1], git("branch", "--show-current", cwd=root)
        )
        ficha = fichero_de(root, a.preguntar[0])
        if ficha and (root / ".git").exists():
            subprocess.run(["git", "add", str(ficha.relative_to(root))], cwd=root, env=_git_env(), check=False)
            subprocess.run(
                ["git", "commit", "-qm", f"docs(plan): bloquear {a.preguntar[0]} por pregunta {qid}"],
                cwd=root,
                env=_git_env(),
                check=False,
            )
        print(f"[orquestar] pregunta registrada ({qid}) para {a.preguntar[0]}.")
        return 0
    if a.responder:
        msg = responder_pregunta(root, "cli", f"{a.responder[0]} {a.responder[1]}")
        print(msg)
        return 0
    if a.agente:
        texto = a.prompt or (a.prompt_file.read_text(encoding="utf-8") if a.prompt_file else sys.stdin.read())
        return agente(root, a.agente, texto)
    if a.fondo:
        return en_fondo(root, raw_args)

    return bucle(
        root,
        docs=a.docs,
        test_cmd=a.test,
        max_pasos=a.max_pasos,
        reintentos=a.reintentos,
        espera_max=a.espera_max,
        cmd_override=a.cmd,
    )


if __name__ == "__main__":
    sys.exit(main())
