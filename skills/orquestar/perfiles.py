"""Gestión mínima de modelos, niveles de dificultad, arneses y cuotas."""

from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import time

try:
    import winreg
except ImportError:
    winreg = None

from adevv.registro_metricas import leer_registros, registrar as escribir_registro
from adevv.yaml_lite import load_yaml

ARNESES = {
    "claude": ["claude", "-p", "--dangerously-skip-permissions", "--output-format", "json"],
    "codex": ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "--json", "-"],
    "gemini": ["gemini", "--yolo", "-p", "{prompt}"],
    "cursor": ["cursor-agent", "-p", "--force", "{prompt}"],
    "agy": ["agy", "-p", "{prompt}", "--dangerously-skip-permissions", "--output-format", "json"],
}
NIVELES = ("sencilla", "media", "dificil")
DESARROLLO = {"task-dev", "bug-fix"}
REVISION = {"revisar-plataforma", "revisar-tarea", "revisar-version"}
CONFIG = "orchestration.json"
CUOTA_DEFECTO_S = 1800
VENTANA_CUOTA_S = 18000


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
            "--dangerously-skip-permissions",
            "--output-format",
            "json",
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
            "json",
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


def espera_cuota(salida: str) -> int | None:
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
    m_seg = re.search(r"(?:resets?\s+in|retry\s+after|try\s+again\s+in)\s+(\d+(?:\.\d+)?)\s*s\b", bajo)
    if m_seg:
        return max(1, math.ceil(float(m_seg.group(1))))
    m_min = re.search(r"(?:resets?\s+in|try\s+again\s+in)\s+(\d+(?:\.\d+)?)\s*m(?:in)?\b", bajo)
    if m_min:
        return max(60, math.ceil(float(m_min.group(1)) * 60))
    return CUOTA_DEFECTO_S


def fallo_cuota(root: Path, harness: str, modelo: str, salida: str) -> dict:
    espera = espera_cuota(salida) or CUOTA_DEFECTO_S
    return {
        "sin_cuota": True,
        "cuota_espera_s": int(math.ceil(espera)),
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


def _matar_arbol(pid: int) -> None:
    if pid <= 0:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except OSError:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass


def _parsear_salida_json(salida: str, harness: str) -> tuple[dict, str]:
    metricas = {"modelos": {}, "turnos": 0, "error": False}
    textos = []
    for cruda in (salida or "").splitlines():
        linea = cruda.strip()
        if not (linea.startswith("{") and linea.endswith("}")):
            continue
        try:
            d = json.loads(linea)
        except json.JSONDecodeError:
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

        # Uso multi-modelo estilo Claude / AGY
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

        # Eventos JSONL de Codex
        if d.get("type") == "item.completed" and isinstance(d.get("item"), dict):
            if d["item"].get("type") == "agent_message" and d["item"].get("text"):
                textos.append(str(d["item"]["text"]))
        if d.get("type") == "turn.completed" and isinstance(d.get("usage"), dict):
            u = d["usage"]
            mod = d.get("model") or "codex"
            dest = metricas["modelos"].setdefault(mod, {"entrada": 0, "salida": 0, "cache_leida": 0, "razonamiento": 0})
            dest["entrada"] += int(u.get("input_tokens") or 0)
            dest["salida"] += int(u.get("output_tokens") or 0)
            dest["cache_leida"] += int(u.get("cached_input_tokens") or 0)
            metricas["turnos"] += 1

        for campo in ("response", "result"):
            if isinstance(d.get(campo), str) and d[campo].strip():
                textos.append(d[campo].strip())

    limpia = "\n".join(textos).strip() if textos else (salida or "").strip()
    return metricas, limpia


def lanzar(
    cmd: list[str] | str,
    root: Path,
    harness: str = "agy",
    entrada: str | None = None,
    timeout: float | None = None,
    env: dict | None = None,
    gracia_cierre: float = 0.2,
) -> tuple[int, dict, str]:
    """Ejecuta el proceso del arnés con límite opcional de tiempo y extrae métricas."""
    if isinstance(cmd, str):
        partes = shlex.split(cmd, posix=(os.name != "nt"))
        args = [
            t[1:-1] if os.name == "nt" and len(t) >= 2 and t[0] == t[-1] and t[0] in ('"', "'") else t for t in partes
        ]
    else:
        args = list(cmd)
    t0 = time.monotonic()
    kwargs = {
        "cwd": str(root),
        "stdin": subprocess.DEVNULL if entrada is None else subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "env": env,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(args, **kwargs)
    try:
        salida, _ = proc.communicate(input=entrada, timeout=timeout)
        codigo = proc.returncode
    except subprocess.TimeoutExpired as exc:
        _matar_arbol(proc.pid)
        try:
            resto, _ = proc.communicate(timeout=max(gracia_cierre, 0.2))
        except Exception:
            proc.kill()
            resto, _ = proc.communicate()
        prev = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        parcial = prev + (resto or "")
        dur = round(time.monotonic() - t0)
        return 124, {"duracion_s": dur, "timeout": True, "error": True, "modelos": {}}, parcial

    dur = round(time.monotonic() - t0)
    metricas, limpia = _parsear_salida_json(salida, harness)
    metricas["duracion_s"] = dur
    if codigo != 0:
        metricas["error"] = True
    return codigo, metricas, limpia or salida
