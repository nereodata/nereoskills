"""Gestión mínima de modelos, niveles de dificultad, arneses y cuotas."""

from contextlib import contextmanager
import ctypes
from datetime import datetime, timedelta
import io
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import threading
import time

try:
    import winreg
except ImportError:
    winreg = None

from adevv.registro_metricas import leer_registros, registrar as escribir_registro
from adevv.yaml_lite import load_yaml

ARNESES = {
    "claude": ["claude", "-p", "--verbose", "--dangerously-skip-permissions", "--output-format", "stream-json"],
    "codex": ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "--json", "-"],
    "gemini": ["gemini", "--yolo", "-p", "{prompt}"],
    "cursor": ["cursor-agent", "-p", "--force", "{prompt}"],
    "agy": ["agy", "-p", "{prompt}", "--dangerously-skip-permissions", "--output-format", "stream-json"],
}
NIVELES = ("sencilla", "media", "dificil")
DESARROLLO = {"task-dev", "bug-fix", "resolver-version"}
REVISION = {"revisar-plataforma", "revisar-tarea", "revisar-version"}
CONFIG = "orchestration.json"
CUOTA_DEFECTO_S = 300
CUOTA_REINTENTO_S = 300
VENTANA_CUOTA_S = 18000
TIMEOUT_PASO_S = 2700
INACTIVIDAD_PASO_S = 900
GRACIA_CIERRE_JSON_S = 10.0
_SUBPROCESS_POPEN = subprocess.Popen
_SUBPROCESS_RUN = subprocess.run


class ArnesAusente(RuntimeError):
    """El binario del arnés configurado no existe en PATH."""


def ahora() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def fecha_estado(iso_str: str) -> datetime:
    try:
        dt = datetime.fromisoformat(iso_str)
    except ValueError:
        dt = datetime.now().astimezone()
    return dt if dt.tzinfo else dt.astimezone()


def config(root: Path) -> dict:
    p = Path(root) / CONFIG
    if not p.is_file():
        return {}
    try:
        datos = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{CONFIG} inválido: {exc}") from exc
    return datos if isinstance(datos, dict) else {}


def buscar_ejecutable(nombre: str, winreg_mod=None) -> str | None:
    hallado = shutil.which(nombre)
    if hallado:
        return hallado
    wreg = winreg_mod if winreg_mod is not None else winreg
    candidatos_dir = [
        Path.home() / ".local" / "bin",
        Path.home() / "AppData" / "Roaming" / "npm",
        Path.home() / "AppData" / "Local" / "agy" / "bin",
    ]
    if wreg is not None:
        try:
            with wreg.OpenKey(wreg.HKEY_CURRENT_USER, "Environment") as clave:
                valor, _ = wreg.QueryValueEx(clave, "Path")
                exp = (
                    wreg.ExpandEnvironmentStrings(valor)
                    if hasattr(wreg, "ExpandEnvironmentStrings")
                    else os.path.expandvars(valor)
                )
                candidatos_dir.extend(Path(p) for p in exp.split(os.pathsep) if p.strip())
        except Exception:
            pass
    ruta_extra = os.pathsep.join(str(p) for p in candidatos_dir if p.is_dir())
    return shutil.which(nombre, path=ruta_extra) if ruta_extra else None


def lista_reservas(cfg: dict) -> list[dict]:
    res = cfg.get("reserva") if isinstance(cfg, dict) else None
    return [dict(r) for r in res if isinstance(r, dict)] if isinstance(res, list) else []


def ajustes(base: dict, paso: str = "", dificultad: str | None = None) -> dict:
    if not isinstance(base, dict):
        return {"harness": "agy", "model": "gemini-4-carbon", "effort": "medium"}
    res = {k: v for k, v in base.items() if k not in ("dificultad", "pasos")}
    dif_map = base.get("dificultad")
    if dificultad and isinstance(dif_map, dict) and isinstance(dif_map.get(dificultad), dict):
        sub = dif_map[dificultad]
        res.update({k: v for k, v in sub.items() if k != "dificultad"})
    pasos_map = base.get("pasos")
    if paso and isinstance(pasos_map, dict) and isinstance(pasos_map.get(paso), dict):
        res.update(pasos_map[paso])
    res.setdefault("harness", "agy")
    return res


def frontmatter_ficha(path: Path | None) -> dict:
    if not path or not Path(path).is_file():
        return {}
    texto = Path(path).read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---", texto, re.S)
    return (load_yaml(m[1]) or {}) if m else {}


def dificultad_de(root: Path, iid: str | None, fichero_fn=None) -> str:
    if not iid:
        return "media"
    ficha = fichero_fn(root, iid) if fichero_fn else None
    dif = str(frontmatter_ficha(ficha).get("dificultad") or "media").strip().lower()
    return dif if dif in NIVELES else "media"


def rol_de(
    root: Path,
    paso: str,
    dificultad: str | None = None,
    iid: str | None = None,
    fichero_fn=None,
    rol_explicito: str | None = None,
) -> tuple[str, dict]:
    cfg = config(root)
    rol = rol_explicito or ("hades" if paso in REVISION else ("artemisa" if paso in DESARROLLO else "atenea"))
    base = cfg.get(rol) or cfg.get("atenea") or {"harness": "agy", "model": "gemini-4-carbon", "effort": "medium"}
    elegido = ajustes(base, paso, dificultad or "media")
    if iid and fichero_fn:
        fm = frontmatter_ficha(fichero_fn(root, iid))
        perf = fm.get("perfil")
        if isinstance(perf, dict):
            override = (
                perf.get(rol)
                if isinstance(perf.get(rol), dict)
                else (perf if "harness" in perf or "model" in perf else None)
            )
            if isinstance(override, dict):
                elegido = {**elegido, **override}
    return rol, elegido


def extraer_perfil(texto: str) -> tuple[str, dict | None, str | None]:
    """Extrae '@perfil harness/modelo[:esfuerzo]' opcional al final de /tarea o /bug."""
    m = re.search(r"(?:^|\s)@perfil\s+(\S+)\s*$", texto or "")
    if not m:
        return (texto or "").strip(), None, None
    limpio = (texto[: m.start()] or "").strip()
    espec = m.group(1)
    if "/" not in espec:
        return limpio, None, "usa formato arnes/modelo[:esfuerzo]"
    harness, resto = espec.split("/", 1)
    modelo, _, esfuerzo = resto.partition(":")
    if harness not in ARNESES or not modelo:
        return limpio, None, f"arnés o modelo inválido ({espec})"
    perfil = {"harness": harness, "model": modelo}
    if esfuerzo:
        if esfuerzo not in ("low", "medium", "high"):
            return limpio, None, f"esfuerzo inválido ({esfuerzo})"
        perfil["effort"] = esfuerzo
    return limpio, perfil, None


def con_modelo(cmd: list[str], harness: str, cfg: dict, sesion: str | None = None) -> list[str]:
    res = list(cmd)
    modelo = cfg.get("model")
    esfuerzo = cfg.get("effort")
    if sesion:
        if harness == "claude" and "--resume" not in res:
            res.extend(["--resume", sesion])
        elif harness == "agy" and "--conversation" not in res:
            res.extend(["--conversation", sesion])
        elif harness == "codex" and "resume" not in res:
            idx = res.index("exec") + 1 if "exec" in res else 1
            res[idx:idx] = ["resume", sesion]
    if modelo and "--model" not in res and "-m" not in res:
        if harness == "codex":
            res[1:1] = ["-m", str(modelo)]
        else:
            res.extend(["--model", str(modelo)])
    if esfuerzo:
        if harness == "codex":
            res[1:1] = ["-c", f'model_reasoning_effort="{esfuerzo}"']
        elif harness in ("claude", "agy") and "--effort" not in res:
            res.extend(["--effort", str(esfuerzo)])
    return res


def base_comando_agente(harness: str, prompt: str, sesion: str | None = None) -> list[str] | None:
    if harness == "claude":
        return [
            "claude",
            *(["--resume", sesion] if sesion else []),
            "-p",
            "--verbose",
            "--dangerously-skip-permissions",
            "--output-format",
            "stream-json",
        ]
    if harness == "codex":
        if sesion:
            return [
                "codex",
                "exec",
                "resume",
                sesion,
                "--json",
                "-c",
                'approval_policy="never"',
                "-c",
                'sandbox_mode="workspace-write"',
                "-",
            ]
        return ["codex", "exec", "--json", "-c", 'approval_policy="never"', "--sandbox", "workspace-write", "-"]
    if harness == "agy":
        return [
            "agy",
            *(["--conversation", sesion] if sesion else []),
            "--dangerously-skip-permissions",
            "--output-format",
            "stream-json",
            "-p",
            prompt,
        ]
    return None


def acceso_suscripcion_denegado(harness: str, salida: str) -> bool:
    texto = (salida or "").lower()
    return any(
        p in texto
        for p in (
            "disabled claude subscription access",
            "subscription access for claude code",
            "organization has disabled",
            "not authorized to use",
        )
    )


def espera_cuota(salida: str, por_defecto: int = CUOTA_REINTENTO_S) -> int | None:
    texto = salida or ""
    bajo = texto.lower()
    patrones_cuota = (
        "rate limit",
        "usage limit",
        "quota exceeded",
        "resource_exhausted",
        "out of credits",
        "insufficient_quota",
        "too many requests",
        "hit your limit",
        "429",
    )
    if not any(p in bajo for p in patrones_cuota):
        return None
    for m_comp in re.finditer(
        r"(?:resets?\s+in|retry\s+after|try\s+again\s+in)\s+(?=\d)"
        r"(?:(\d+(?:\.\d+)?)\s*h\s*)?(?:(\d+(?:\.\d+)?)\s*m(?:in)?\s*)?(?:(\d+(?:\.\d+)?)\s*s)?\b",
        bajo,
    ):
        if any(m_comp.groups()):
            h = float(m_comp.group(1) or 0)
            m = float(m_comp.group(2) or 0)
            s = float(m_comp.group(3) or 0)
            total = h * 3600 + m * 60 + s
            if total > 0:
                return max(1, math.ceil(total))
    return por_defecto


def _cuota_reintento_config(root: Path) -> int:
    try:
        bruto = config(root).get("cuota_reintento_s")
    except Exception:
        bruto = None
    plazo = resolver_plazo(bruto, CUOTA_REINTENTO_S)
    return max(1, math.ceil(plazo)) if plazo else CUOTA_REINTENTO_S


def fallo_cuota(root: Path, harness: str, modelo: str, salida: str) -> dict:
    reintento_cfg = _cuota_reintento_config(root)
    explicita = espera_cuota(salida, por_defecto=0)
    supuesta = not explicita
    espera = explicita or reintento_cfg
    return {
        "sin_cuota": True,
        "cuota_espera_s": int(math.ceil(espera)),
        "cuota_supuesta": supuesta,
        "modelo": modelo or "predeterminado",
    }


def recuperar_cuota(root: Path, harness: str, modelo: str) -> None:
    escribir_registro(
        root,
        {
            "tipo": "cuota_recuperada",
            "fecha": ahora(),
            "arnes": harness,
            "modelo": modelo or "predeterminado",
        },
    )


def reset_cuotas(root: Path) -> None:
    escribir_registro(root, {"tipo": "cuota_reset", "fecha": ahora()})


def consumo_cuotas(root: Path, instante: datetime | None = None) -> tuple[dict, dict]:
    """Devuelve (tokens_ventana_por_par, bloqueado_hasta_por_par)."""
    instante = instante or fecha_estado(ahora())
    tokens = {}
    bloqueos = {}
    inicio_ventana = instante - timedelta(seconds=VENTANA_CUOTA_S)
    for r in leer_registros(root, tolerar_ultima=True):
        if r.get("tipo") == "cuota_reset":
            bloqueos.clear()
            continue
        f_str = r.get("fecha")
        if not f_str:
            continue
        dt = fecha_estado(f_str)
        arnes = r.get("arnes") or ""
        if r.get("tipo") == "cuota_recuperada":
            bloqueos.pop((arnes, r.get("modelo") or "predeterminado"), None)
            continue
        if r.get("sin_cuota") or r.get("cuota_espera_s"):
            mod = r.get("modelo") or next(iter((r.get("modelos") or {}).keys()), "predeterminado")
            hasta = dt + timedelta(seconds=int(math.ceil(float(r.get("cuota_espera_s") or CUOTA_DEFECTO_S))))
            if hasta > instante:
                bloqueos[(arnes, mod)] = hasta
        if dt >= inicio_ventana:
            for mod, uso in (r.get("modelos") or {}).items():
                par = (arnes, mod)
                tokens[par] = tokens.get(par, 0) + int(uso.get("entrada") or 0) + int(uso.get("salida") or 0)
    return tokens, bloqueos


def configuraciones_con_cuota(root: Path, candidatos: list[dict]) -> list[dict]:
    _, bloqueos = consumo_cuotas(root)
    libres = []
    vistos = set()
    for c in candidatos:
        if not isinstance(c, dict):
            continue
        par = (c.get("harness", "agy"), c.get("model") or "predeterminado")
        clave = (*par, c.get("effort") or "")
        if clave in vistos:
            continue
        vistos.add(clave)
        if par not in bloqueos:
            libres.append(c)
    return libres


def informe_agentes(root: Path) -> str:
    cfg = config(root)
    instante = fecha_estado(ahora())
    tokens, bloqueos = consumo_cuotas(root, instante)
    lineas = ["*Agentes configurados:*"]
    for rol in ("atenea", "artemisa", "hades"):
        base = cfg.get(rol)
        if not isinstance(base, dict):
            continue
        h = base.get("harness", "agy")
        m = base.get("model") or "predeterminado"
        hasta = bloqueos.get((h, m))
        estado = f"sin cuota hasta {hasta:%H:%M}" if hasta else "disponible"
        tok = tokens.get((h, m), 0)
        lineas.append(f"- *{rol}*: `{h}/{m}` ({estado}, ~{tok} tok 5h)")
    return "\n".join(lineas) if len(lineas) > 1 else "Sin roles configurados en orchestration.json."


def resolver_plazo(valor, por_defecto: float | None) -> float | None:
    """Normaliza un plazo en segundos: None usa por_defecto, <= 0 finito lo desactiva y NaN/inf usa por_defecto."""
    if valor is None or valor == "":
        return por_defecto
    if isinstance(valor, bool):
        return por_defecto if valor else None
    try:
        num = float(valor)
    except (TypeError, ValueError):
        return por_defecto
    if not math.isfinite(num):
        return por_defecto
    return num if num > 0 else None


class _TrabajoWindows:
    """Job Object de Windows con KILL_ON_JOB_CLOSE para terminar descendientes aunque salga el padre."""

    def __init__(self):
        class Limites(ctypes.Structure):
            _fields_ = [
                ("tiempo_proceso", ctypes.c_int64),
                ("tiempo_job", ctypes.c_int64),
                ("flags", ctypes.c_ulong),
                ("minimo", ctypes.c_size_t),
                ("maximo", ctypes.c_size_t),
                ("procesos", ctypes.c_ulong),
                ("afinidad", ctypes.c_size_t),
                ("prioridad", ctypes.c_ulong),
                ("planificacion", ctypes.c_ulong),
            ]

        class LimitesExtendidos(ctypes.Structure):
            _fields_ = [
                ("basicos", Limites),
                ("io", ctypes.c_uint64 * 6),
                ("memoria_proceso", ctypes.c_size_t),
                ("memoria_job", ctypes.c_size_t),
                ("pico_proceso", ctypes.c_size_t),
                ("pico_job", ctypes.c_size_t),
            ]

        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        firmas = {
            "CreateJobObjectW": ([ctypes.c_void_p, ctypes.c_wchar_p], ctypes.c_void_p),
            "SetInformationJobObject": ([ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong], ctypes.c_int),
            "AssignProcessToJobObject": ([ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
            "TerminateJobObject": ([ctypes.c_void_p, ctypes.c_uint], ctypes.c_int),
            "CloseHandle": ([ctypes.c_void_p], ctypes.c_int),
            "CreateToolhelp32Snapshot": ([ctypes.c_ulong, ctypes.c_ulong], ctypes.c_void_p),
            "Thread32First": ([ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
            "Thread32Next": ([ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
            "OpenThread": ([ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong], ctypes.c_void_p),
            "ResumeThread": ([ctypes.c_void_p], ctypes.c_ulong),
        }
        for nombre, (t_args, t_res) in firmas.items():
            fn = getattr(self.kernel, nombre)
            fn.argtypes, fn.restype = t_args, t_res
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limites = LimitesExtendidos()
        limites.basicos.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limites), ctypes.sizeof(limites)):
            err = ctypes.WinError(ctypes.get_last_error())
            self.cerrar()
            raise err

    def reanudar_hilo_principal(self, pid: int) -> None:
        class EntradaHilo(ctypes.Structure):
            _fields_ = [
                ("tamano", ctypes.c_ulong),
                ("usos", ctypes.c_ulong),
                ("tid", ctypes.c_ulong),
                ("pid", ctypes.c_ulong),
                ("prioridad", ctypes.c_long),
                ("delta", ctypes.c_long),
                ("flags", ctypes.c_ulong),
            ]

        snapshot = self.kernel.CreateToolhelp32Snapshot(4, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entrada = EntradaHilo()
            entrada.tamano = ctypes.sizeof(entrada)
            existe = self.kernel.Thread32First(snapshot, ctypes.byref(entrada))
            while existe:
                if entrada.pid == pid:
                    hilo = self.kernel.OpenThread(2, False, entrada.tid)
                    if not hilo:
                        raise ctypes.WinError(ctypes.get_last_error())
                    try:
                        if self.kernel.ResumeThread(hilo) == 0xFFFFFFFF:
                            raise ctypes.WinError(ctypes.get_last_error())
                        return
                    finally:
                        self.kernel.CloseHandle(hilo)
                entrada.tamano = ctypes.sizeof(entrada)
                existe = self.kernel.Thread32Next(snapshot, ctypes.byref(entrada))
            raise OSError("No se encontró el hilo inicial del proceso suspendido")
        finally:
            self.kernel.CloseHandle(snapshot)

    def asignar_y_reanudar(self, proceso) -> bool:
        asignado = bool(self.kernel.AssignProcessToJobObject(self.handle, int(proceso._handle)))
        self.reanudar_hilo_principal(proceso.pid)
        return asignado

    def terminar(self) -> None:
        if self.handle:
            self.kernel.TerminateJobObject(self.handle, 124)

    def cerrar(self) -> None:
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def _matar_arbol(pid: int) -> None:
    if pid <= 0:
        return
    if os.name == "nt":
        try:
            _SUBPROCESS_RUN(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=5)
        except Exception:
            pass
    else:
        for fn in (lambda: os.killpg(pid, signal.SIGKILL), lambda: os.kill(pid, signal.SIGKILL)):
            try:
                fn()
                break
            except OSError:
                pass


def _terminar_arbol_proceso(proc) -> None:
    trabajo = getattr(proc, "_orquestar_trabajo", None)
    if isinstance(trabajo, _TrabajoWindows):
        trabajo.terminar()
    pid = getattr(proc, "pid", 0) or 0
    if pid > 0:
        _matar_arbol(pid)
    try:
        proc.kill()
    except Exception:
        pass


@contextmanager
def _proceso_agrupado(args, **kwargs):
    trabajo = None
    proc = None
    suspendido = False
    if os.name == "nt" and subprocess.Popen is _SUBPROCESS_POPEN:
        try:
            trabajo = _TrabajoWindows()
            kwargs["creationflags"] = kwargs.get("creationflags", 0) | subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000004
            suspendido = True
        except OSError:
            trabajo = None
            kwargs["creationflags"] = kwargs.get("creationflags", 0) | subprocess.CREATE_NEW_PROCESS_GROUP
    elif os.name == "nt":
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen(args, **kwargs)
        if trabajo is not None and suspendido:
            try:
                if trabajo.asignar_y_reanudar(proc):
                    proc._orquestar_trabajo = trabajo
                else:
                    trabajo.cerrar()
                    trabajo = None
            except BaseException:
                proc.kill()
                proc.wait(timeout=2)
                raise
        yield proc
    finally:
        if trabajo is not None:
            trabajo.cerrar()
        if proc is not None:
            try:
                proc.__exit__(None, None, None)
            except Exception:
                pass


def _estado_cierre_json(harness: str, texto: str) -> tuple[bool, bool]:
    """Devuelve (hay_evento_final, es_error) inspeccionando líneas JSON completas."""
    for cruda in reversed((texto or "").splitlines()):
        linea = cruda.strip()
        if not (linea.startswith("{") and linea.endswith("}")):
            continue
        try:
            d = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if not isinstance(d, dict):
            continue
        if harness == "codex":
            if d.get("type") == "turn.completed":
                return True, False
            if d.get("type") == "turn.failed":
                return True, True
        elif harness == "agy":
            if d.get("event") == "result" and isinstance(d.get("result"), dict):
                st = str(d["result"].get("status", "SUCCESS")).upper()
                return True, st not in ("SUCCESS", "OK", "COMPLETED")
            if d.get("event") not in ("init", "step_update") and (
                isinstance(d.get("response"), str) or isinstance(d.get("result"), str)
            ):
                return True, bool(d.get("is_error"))
        elif harness == "claude":
            if d.get("type") == "result":
                return True, bool(d.get("is_error"))
            if d.get("type") not in ("system", "assistant", "user", "rate_limit_event") and (
                isinstance(d.get("result"), str) or isinstance(d.get("response"), str)
            ):
                return True, bool(d.get("is_error"))
    return False, False


def _parsear_salida_json(salida: str, harness: str, modelo_hint: str = "") -> tuple[dict, str]:
    metricas = {"modelos": {}, "turnos": 0, "error": False}
    textos = []
    textos_parciales = []
    for cruda in (salida or "").splitlines():
        linea = cruda.strip()
        if not (linea.startswith("{") and linea.endswith("}")):
            continue
        try:
            d = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if not isinstance(d, dict):
            continue
        sesion = d.get("conversation_id") or d.get("session_id") or d.get("sessionId") or d.get("thread_id")
        if sesion:
            metricas["sesion"] = sesion
        if d.get("num_turns"):
            metricas["turnos"] = int(d["num_turns"])
        if d.get("total_cost_usd"):
            metricas["coste_usd"] = float(d["total_cost_usd"])
        if d.get("is_error") is True:
            metricas["error"] = True

        # Uso multi-modelo estilo Claude / AGY json
        for k_map in ("modelUsage", "models"):
            if isinstance(d.get(k_map), dict):
                for mod, u in d[k_map].items():
                    if not isinstance(u, dict):
                        continue
                    tok = u.get("tokens") if isinstance(u.get("tokens"), dict) else u
                    dest = metricas["modelos"].setdefault(
                        mod, {"entrada": 0, "salida": 0, "cache_leida": 0, "razonamiento": 0}
                    )
                    dest["entrada"] += int(tok.get("input") or tok.get("inputTokens") or tok.get("prompt") or 0)
                    dest["salida"] += int(tok.get("output") or tok.get("outputTokens") or tok.get("candidates") or 0)
                    dest["cache_leida"] += int(tok.get("cached") or tok.get("cacheReadInputTokens") or 0)
                    dest["razonamiento"] += int(tok.get("thoughts") or tok.get("reasoningTokens") or 0)

        # Evento final stream-json de AGY: {"event": "result", "result": {...}}
        if d.get("event") == "result" and isinstance(d.get("result"), dict):
            res_obj = d["result"]
            if res_obj.get("conversation_id"):
                metricas["sesion"] = res_obj["conversation_id"]
            if res_obj.get("num_turns"):
                metricas["turnos"] = int(res_obj["num_turns"])
            if str(res_obj.get("status", "SUCCESS")).upper() not in ("SUCCESS", "OK", "COMPLETED"):
                metricas["error"] = True
            for k_txt in ("response", "error"):
                if isinstance(res_obj.get(k_txt), str) and res_obj[k_txt].strip():
                    textos.append(res_obj[k_txt].strip())
            if isinstance(res_obj.get("usage"), dict) and not isinstance(d.get("models"), dict):
                u = res_obj["usage"]
                mod = res_obj.get("model") or d.get("model") or modelo_hint or "agy"
                dest = metricas["modelos"].setdefault(
                    mod, {"entrada": 0, "salida": 0, "cache_leida": 0, "razonamiento": 0}
                )
                dest["entrada"] += int(u.get("input_tokens") or 0)
                dest["salida"] += int(u.get("output_tokens") or 0)
                dest["cache_leida"] += int(u.get("cache_read_tokens") or u.get("cached_input_tokens") or 0)
                dest["razonamiento"] += int(u.get("thinking_tokens") or u.get("reasoning_tokens") or 0)

        # Mensajes intermedios de Claude stream-json (respaldo si cae antes del type: result)
        if d.get("type") == "assistant" and isinstance(d.get("message"), dict):
            for bloque in d["message"].get("content") or ():
                if isinstance(bloque, dict) and bloque.get("type") == "text" and isinstance(bloque.get("text"), str):
                    if bloque["text"].strip():
                        textos_parciales.append(bloque["text"].strip())

        # Eventos JSONL de Codex
        if d.get("type") == "item.completed" and isinstance(d.get("item"), dict):
            if d["item"].get("type") == "agent_message" and d["item"].get("text"):
                textos.append(str(d["item"]["text"]))
        if d.get("type") == "turn.completed" and isinstance(d.get("usage"), dict):
            u = d["usage"]
            mod = d.get("model") or modelo_hint or "codex"
            dest = metricas["modelos"].setdefault(mod, {"entrada": 0, "salida": 0, "cache_leida": 0, "razonamiento": 0})
            dest["entrada"] += int(u.get("input_tokens") or 0)
            dest["salida"] += int(u.get("output_tokens") or 0)
            dest["cache_leida"] += int(u.get("cached_input_tokens") or 0)
            detalles_sal = u.get("output_tokens_details") if isinstance(u.get("output_tokens_details"), dict) else {}
            dest["razonamiento"] += int(u.get("reasoning_tokens") or detalles_sal.get("reasoning_tokens") or 0)
            metricas["turnos"] += 1
        if d.get("type") in ("turn.failed", "error"):
            metricas["error"] = True
            err_obj = d.get("error")
            msg_err = err_obj.get("message") if isinstance(err_obj, dict) else (err_obj or d.get("message"))
            if isinstance(msg_err, str) and msg_err.strip():
                textos.append(msg_err.strip())

        for campo in ("response", "result"):
            if isinstance(d.get(campo), str) and d[campo].strip():
                textos.append(d[campo].strip())

    elegidos = textos or textos_parciales
    limpia = "\n".join(elegidos).strip() if elegidos else (salida or "").strip()
    return metricas, limpia


def lanzar(
    cmd: list[str] | str,
    root: Path,
    harness: str = "agy",
    entrada: str | None = None,
    timeout: float | None = None,
    env: dict | None = None,
    gracia_cierre: float = GRACIA_CIERRE_JSON_S,
    inactividad: float | None = None,
    modelo: str = "",
) -> tuple[int, dict, str]:
    """Ejecuta el proceso del arnés en streaming con vigilancia de inactividad, gracia tras JSON y tope total."""
    if isinstance(cmd, str):
        partes = shlex.split(cmd, posix=(os.name != "nt"))
        args = [
            t[1:-1] if os.name == "nt" and len(t) >= 2 and t[0] == t[-1] and t[0] in ('"', "'") else t for t in partes
        ]
    else:
        args = list(cmd)

    timeout_ef = resolver_plazo(timeout, None)
    inact_ef = resolver_plazo(inactividad, None)
    gracia_ef = max(0.05, float(gracia_cierre)) if gracia_cierre is not None else GRACIA_CIERRE_JSON_S
    t0 = time.monotonic()

    with _proceso_agrupado(
        args,
        cwd=str(root),
        stdin=subprocess.DEVNULL if entrada is None else subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    ) as proc:
        if entrada is not None and proc.stdin is not None:
            datos_in = entrada.encode("utf-8", errors="replace") if isinstance(entrada, str) else entrada

            def _escribir_stdin() -> None:
                try:
                    proc.stdin.write(datos_in)
                except Exception:
                    pass
                finally:
                    try:
                        proc.stdin.close()
                    except Exception:
                        pass

            threading.Thread(target=_escribir_stdin, daemon=True).start()

        chunks_out: list[bytes] = []
        chunks_err: list[bytes] = []
        ultimo_latido = [t0]
        cierre_json: list[tuple[float, bool] | None] = [None]

        def _leer_stream(stream, destino: list[bytes], es_stdout: bool) -> None:
            if stream is None:
                return
            try:
                fd = stream.fileno() if hasattr(stream, "fileno") else None
                if not isinstance(fd, int):
                    fd = None
            except (OSError, ValueError, io.UnsupportedOperation):
                fd = None
            try:
                while True:
                    if fd is not None:
                        bloque = os.read(fd, 4096)
                    else:
                        crudo = stream.read(4096)
                        bloque = crudo.encode("utf-8", errors="replace") if isinstance(crudo, str) else crudo
                    if not bloque:
                        break
                    ultimo_latido[0] = time.monotonic()
                    destino.append(bloque)
                    if es_stdout and cierre_json[0] is None and b"\n" in bloque:
                        parcial = b"".join(destino).decode("utf-8", errors="replace")
                        hay_fin, es_err = _estado_cierre_json(harness, parcial)
                        if hay_fin:
                            cierre_json[0] = (ultimo_latido[0], es_err)
            except (OSError, ValueError):
                pass

        t_out = threading.Thread(target=_leer_stream, args=(proc.stdout, chunks_out, True), daemon=True)
        t_err = threading.Thread(target=_leer_stream, args=(proc.stderr, chunks_err, False), daemon=True)
        t_out.start()
        t_err.start()

        por_timeout = False
        por_inactividad = False
        cierre_forzado = False
        instante_salida: float | None = None

        while True:
            terminado = proc.poll() is not None
            if terminado and not t_out.is_alive() and not t_err.is_alive():
                break
            ahora_m = time.monotonic()
            if terminado and instante_salida is None:
                instante_salida = ahora_m
            if cierre_json[0] is not None and (ahora_m - cierre_json[0][0]) >= gracia_ef:
                cierre_forzado = True
                _terminar_arbol_proceso(proc)
                break
            if instante_salida is not None and (ahora_m - instante_salida) >= gracia_ef:
                cierre_forzado = cierre_json[0] is not None
                _terminar_arbol_proceso(proc)
                break
            if inact_ef is not None and cierre_json[0] is None and (ahora_m - ultimo_latido[0]) >= inact_ef:
                por_inactividad = True
                por_timeout = True
                _terminar_arbol_proceso(proc)
                break
            if timeout_ef is not None and (ahora_m - t0) >= timeout_ef:
                por_timeout = True
                _terminar_arbol_proceso(proc)
                break
            time.sleep(0.02)

        espera_hilos = 0.3 if (cierre_forzado or por_timeout or instante_salida is not None) else 1.5
        t_out.join(timeout=espera_hilos)
        t_err.join(timeout=espera_hilos)
        for st in (proc.stdout, proc.stderr):
            if st is not None:
                try:
                    st.close()
                except Exception:
                    pass

        out_txt = b"".join(chunks_out).decode("utf-8", errors="replace")
        err_txt = b"".join(chunks_err).decode("utf-8", errors="replace")
        combinada = (out_txt + ("\n" + err_txt if err_txt.strip() else "")) if out_txt else err_txt

        hay_fin_final, es_err_final = _estado_cierre_json(harness, out_txt)
        if por_timeout and hay_fin_final:
            por_timeout = False
            por_inactividad = False
            cierre_forzado = True

        dur = round(time.monotonic() - t0)
        if por_timeout:
            metricas_t, limpia_t = _parsear_salida_json(combinada, harness, modelo_hint=modelo)
            metricas_t.update(
                {
                    "duracion_s": dur,
                    "timeout": True,
                    "error": True,
                    **({"inactividad": True} if por_inactividad else {}),
                }
            )
            return 124, metricas_t, limpia_t or combinada

        if cierre_forzado and hay_fin_final:
            codigo = (proc.returncode or 1) if es_err_final else 0
        else:
            codigo = proc.returncode if proc.returncode is not None else 1

        metricas, limpia = _parsear_salida_json(combinada, harness, modelo_hint=modelo)
        metricas["duracion_s"] = dur
        if cierre_forzado:
            metricas["cierre_forzado"] = True
        if codigo != 0 or es_err_final:
            metricas["error"] = True
        return codigo, metricas, limpia or combinada
