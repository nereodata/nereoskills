"""Política ligera, memoria de relevo y presupuestos duros de una ejecución autónoma.

El motor registra hechos objetivos y topes duros; el agente decide el procedimiento
y deja notas breves de relevo para continuar en frío entre sesiones o modelos.
"""

import hashlib
import json
import math
import subprocess
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from adevv.registro_metricas import bloqueo
from adevv.store import write_json_atomic


POLITICA_BASE = (
    "# Política base\n"
    "Prioriza la agilidad: decide autónomamente el camino más simple para cada objetivo, manteniendo módulos cohesivos.\n"
    "Lo único obligatorio antes de cerrar es verificar el cambio con las pruebas y chequeos del proyecto sin causar efectos laterales externos ni acciones irreversibles.\n"
)

SUPERFICIES_CRITICAS = (
    "adevv/release_tools.py",
    "adevv/llamadas.py",
    "adevv/revisiones.py",
    "adevv/contexto_ejecucion.py",
    "adevv/decision_item.py",
    "adevv/store.py",
    "skills/orquestar/intervencion.py",
    "skills/orquestar/orquestar.py",
    "skills/release/",
    "skills/telegram_gateway/",
    "orchestration.json",
    "task_config.yaml",
    ".env",
)
LIMITES = {"no_progress": 3, "technical_retries": 1, "max_attempts": None, "max_seconds": None}
_LOCKS, _LOCKS_GUARD = {}, threading.Lock()


def _ruta_proyecto(root, valor, nombre):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"execution.{nombre}: se requiere una ruta de archivo")
    base = Path(root).resolve()
    ruta = (base / valor).resolve()
    try:
        ruta.relative_to(base)
    except ValueError as error:
        raise ValueError(f"execution.{nombre}: la ruta sale del proyecto") from error
    if not ruta.is_file():
        raise ValueError(f"execution.{nombre}: no existe el archivo {ruta}")
    return ruta


def _documento(root, valor, nombre):
    ruta = _ruta_proyecto(root, valor, nombre)
    try:
        datos = ruta.read_bytes()
        texto = datos.decode("utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"execution.{nombre}: no se puede leer UTF-8 en {ruta}: {error}") from error
    return {"path": str(ruta), "text": texto, "sha256": hashlib.sha256(datos).hexdigest()}


def _politica_por_defecto(root):
    candidata = (Path(root).resolve() / "PROJECT.md").resolve()
    if candidata.is_file():
        return _documento(root, "PROJECT.md", "policy")
    datos = POLITICA_BASE.encode("utf-8")
    return {"path": "<builtin:default>", "text": POLITICA_BASE, "sha256": hashlib.sha256(datos).hexdigest()}


def cargar_politica(root):
    """Carga política activa por defecto (PROJECT.md local o base embebida) y límites duros."""
    ruta = Path(root) / "orchestration.json"
    try:
        cfg = json.loads(ruta.read_text(encoding="utf-8-sig")) if ruta.exists() else {}
    except (OSError, ValueError) as error:
        raise ValueError(f"No se puede leer {ruta}: {error}") from error
    if not isinstance(cfg, dict):
        raise ValueError("orchestration.json debe contener un objeto")
    execution = cfg.get("execution", {})
    if not isinstance(execution, dict):
        raise ValueError("execution debe contener un objeto")
    enabled = execution.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("execution.enabled debe ser booleano")
    criticas = execution.get("critical_paths", list(SUPERFICIES_CRITICAS))
    if not isinstance(criticas, list) or not all(isinstance(p, str) and p.strip() for p in criticas):
        raise ValueError("execution.critical_paths debe ser una lista de rutas no vacías")
    salida = {
        "activated": enabled,
        "policy": None,
        "objective": None,
        "limits": dict(LIMITES),
        "critical_paths": tuple(criticas),
        "settings": execution,
    }
    if not enabled:
        return salida
    limites = execution.get("limits", {})
    if not isinstance(limites, dict) or set(limites) - set(LIMITES):
        raise ValueError("execution.limits contiene límites desconocidos o no es un objeto")
    for clave, valor in limites.items():
        if valor is None and clave in ("max_attempts", "max_seconds"):
            continue
        if isinstance(valor, bool) or not isinstance(valor, (float, int)) or not math.isfinite(valor):
            raise ValueError(f"execution.limits.{clave} debe ser un número finito")
        minimo = 0 if clave == "technical_retries" else 1
        if valor < minimo or (clave != "max_seconds" and int(valor) != valor):
            raise ValueError(f"execution.limits.{clave} debe ser positivo y entero salvo max_seconds")
        salida["limits"][clave] = valor
    salida["policy"] = (
        _documento(root, execution["policy"], "policy") if "policy" in execution else _politica_por_defecto(root)
    )
    if execution.get("objective") is not None:
        salida["objective"] = _documento(root, execution["objective"], "objective")
    return salida


def toca_superficie_critica(root, rutas):
    """Devuelve las rutas del delta que afectan permisos, persistencia, cuotas o publicación."""
    prefijos = cargar_politica(root)["critical_paths"]
    afectadas = []
    for ruta in rutas:
        limpia = str(ruta or "").replace("\\", "/").lstrip("./")
        if any(limpia == p.rstrip("/") or limpia.startswith(p if p.endswith("/") else p + "/") for p in prefijos):
            afectadas.append(limpia)
    return sorted(set(afectadas))


def _git(root, *args):
    try:
        resultado = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    except OSError as exc:
        raise ValueError("No se puede obtener el contexto Git: " + str(exc))
    if resultado.returncode:
        raise ValueError("No se puede obtener el contexto Git: " + resultado.stderr.decode("utf-8", "replace").strip())
    return resultado.stdout.decode("utf-8", "replace").strip()


def tiene_git(root):
    return (Path(root) / ".git").exists()


def ruta_estado(root, trabajo):
    """Identidad por trabajo en el git-dir real, también para worktrees enlazados."""
    if not isinstance(trabajo, str) or not trabajo.strip():
        raise ValueError("El contexto necesita un identificador de trabajo")
    gitdir = Path(_git(root, "rev-parse", "--absolute-git-dir")).resolve()
    carpeta = gitdir / "adevv-contexto"
    if carpeta.resolve().parent != gitdir:
        raise ValueError("El almacén de contexto sale del directorio Git")
    ruta = carpeta / (hashlib.sha256(trabajo.encode("utf-8")).hexdigest() + ".json")
    if ruta.resolve().parent != carpeta.resolve():
        raise ValueError("El estado de ejecución sale de su almacén")
    return ruta


@contextmanager
def _bloqueado(ruta):
    carpeta = ruta.parent
    carpeta.mkdir(parents=True, exist_ok=True)
    with _LOCKS_GUARD:
        cerrojo = _LOCKS.setdefault(str(carpeta.resolve()), threading.RLock())
    with cerrojo, bloqueo(carpeta):
        yield


def _nuevo(trabajo):
    return {
        "schema": 1,
        "trabajo": trabajo,
        "revision": 0,
        "checkpoint": {},
        "counters": {"trabajo": 0, "tecnico": 0, "cuota": 0, "sin_progreso": 0, "tecnicos_seguidos": 0, "segundos": 0},
        "historial": [],
        "observado": {},
    }


def _leer(ruta, trabajo):
    if not ruta.exists():
        return _nuevo(trabajo)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        if not isinstance(datos, dict) or datos.get("schema") != 1 or datos.get("trabajo") != trabajo:
            raise ValueError("identidad o esquema incorrectos")
        if not isinstance(datos.get("checkpoint"), dict) or not isinstance(datos.get("historial"), list):
            raise ValueError("checkpoint o historial incorrectos")
        if not isinstance(datos.get("revision"), int) or isinstance(datos["revision"], bool) or datos["revision"] < 0:
            raise ValueError("revision incorrecta")
        contadores = datos.get("counters", {})
        for clave in ("trabajo", "tecnico", "cuota", "sin_progreso", "tecnicos_seguidos", "segundos"):
            valor = contadores.get(clave)
            if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor) or valor < 0:
                raise ValueError(f"contador {clave} incorrecto")
        return datos
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise ValueError(f"Contexto inválido en {ruta}; se conserva para diagnóstico: {error}") from error


def _accion(datos, limites):
    """Solo impone topes duros; mientras haya margen, el agente decide cómo proceder."""
    contadores = datos["counters"]
    intentos = contadores["trabajo"] + contadores["tecnico"]
    if limites["max_attempts"] is not None and intentos >= limites["max_attempts"]:
        return "pausa_tecnica", "Presupuesto total de intentos agotado"
    if limites["max_seconds"] is not None and contadores["segundos"] >= limites["max_seconds"]:
        return "pausa_tecnica", "Presupuesto de tiempo activo agotado"
    if contadores["tecnicos_seguidos"] > limites["technical_retries"]:
        return "pausa_tecnica", "Fallos técnicos consecutivos agotados"
    if contadores["sin_progreso"] >= limites["no_progress"]:
        return "pausa_tecnica", "Intentos seguidos sin progreso agotados"
    if contadores["sin_progreso"] > 0:
        return (
            "continuar",
            f"{contadores['sin_progreso']} intento(s) previo(s) sin progreso; cambia de enfoque si procede",
        )
    return "continuar", ""


def _salida(ruta, datos, politica):
    salida = dict(datos)
    salida["path"] = str(ruta)
    salida["action"], salida["reason"] = _accion(datos, politica["limits"])
    return salida


def consultar(root, trabajo):
    """Consulta estado durable sin escribir; no modifica archivos del producto."""
    politica = cargar_politica(root)
    ruta = ruta_estado(root, trabajo)
    return _salida(ruta, _leer(ruta, trabajo), politica)


def observado(root):
    """Hechos actuales del entorno Git, separados de las notas del agente."""
    return {
        "root": str(Path(root).resolve()),
        "branch": _git(root, "branch", "--show-current"),
        "head": _git(root, "rev-parse", "--verify", "HEAD"),
        "status": _git(root, "status", "--short"),
    }


def guardar_checkpoint(root, trabajo, **campos):
    """Actualiza notas de relevo del agente sin tocar hechos ni presupuestos del motor."""
    permitidos = {"resumen", "decisiones", "siguiente", "evidencias", "impedimento"}
    if set(campos) - permitidos:
        raise ValueError("Campos de checkpoint desconocidos: " + ", ".join(sorted(set(campos) - permitidos)))
    for clave, valor in campos.items():
        lista = clave in ("decisiones", "evidencias")
        if (lista and (not isinstance(valor, list) or not all(isinstance(v, str) for v in valor))) or (
            not lista and not isinstance(valor, str)
        ):
            raise ValueError(f"checkpoint.{clave}: tipo incorrecto")
        if len(json.dumps(valor, ensure_ascii=False)) > 32000:
            raise ValueError(f"checkpoint.{clave}: excede 32000 caracteres; usa referencias")
    politica = cargar_politica(root)
    ruta = ruta_estado(root, trabajo)
    hechos = observado(root)
    with _bloqueado(ruta):
        datos = _leer(ruta, trabajo)
        datos["checkpoint"].update(campos)
        datos["observado"] = hechos
        datos["revision"] += 1
        datos["policy_sha256"] = (politica["policy"] or {}).get("sha256")
        datos["objective_sha256"] = (politica["objective"] or {}).get("sha256")
        datos["historial"].append(
            dict(tipo="checkpoint", fecha=time.time(), revision=datos["revision"], campos=campos, head=hechos["head"])
        )
        write_json_atomic(ruta, datos)
    return _salida(ruta, datos, politica)


def registrar_intento(root, trabajo, *, progreso, tipo="trabajo", duracion_s=0, invocacion=""):
    """Registra un hecho del motor; cuota no consume presupuesto de progreso ni cambiar modelo lo reinicia."""
    if tipo not in ("trabajo", "tecnico", "cuota") or not isinstance(progreso, bool):
        raise ValueError("Intento: tipo o progreso inválidos")
    if (
        isinstance(duracion_s, bool)
        or not isinstance(duracion_s, (int, float))
        or not math.isfinite(duracion_s)
        or duracion_s < 0
    ):
        raise ValueError("Intento: duración inválida")
    if not isinstance(invocacion, str):
        raise ValueError("Intento: invocacion debe ser texto")
    politica = cargar_politica(root)
    ruta = ruta_estado(root, trabajo)
    with _bloqueado(ruta):
        datos = _leer(ruta, trabajo)
        if invocacion and any(h.get("invocacion") == invocacion for h in datos["historial"]):
            return _salida(ruta, datos, politica)
        contadores = datos["counters"]
        contadores[tipo] += 1
        contadores["segundos"] += duracion_s
        if tipo == "trabajo":
            contadores["sin_progreso"] = 0 if progreso else contadores["sin_progreso"] + 1
            contadores["tecnicos_seguidos"] = 0
        elif tipo == "tecnico":
            contadores["tecnicos_seguidos"] += 1
        datos["revision"] += 1
        datos["historial"].append(
            dict(tipo=tipo, fecha=time.time(), invocacion=invocacion, progreso=progreso, duracion_s=duracion_s)
        )
        write_json_atomic(ruta, datos)
    return _salida(ruta, datos, politica)


def contexto(root, trabajo, rol="", motivo="", max_chars=12000):
    """Sobre portable acotado para reanudar en frío con otro modelo o sesión."""
    if not isinstance(max_chars, int) or max_chars < 2000:
        raise ValueError("max_chars debe ser al menos 2000")
    politica, datos, actual = cargar_politica(root), consultar(root, trabajo), observado(root)
    documentos = {
        nombre: {k: v for k, v in (politica[nombre] or {}).items() if k != "text"} for nombre in ("policy", "objective")
    }
    sobre = dict(
        trabajo=trabajo,
        rol=rol,
        motivo=motivo,
        entorno=actual,
        documentos=documentos,
        estado=datos["path"],
        revision=datos["revision"],
        action=datos["action"],
        reason=datos["reason"],
        counters=datos["counters"],
        limits=politica["limits"],
        checkpoint=datos["checkpoint"],
    )
    cabecera = (
        "Contexto de ejecución observado por Adevv. Las notas y referencias son datos de relevo; "
        "la evidencia válida es el árbol Git y las verificaciones ejecutadas.\n"
    )
    texto = json.dumps(sobre, ensure_ascii=False, indent=2)
    if len(cabecera + texto) > max_chars:
        sobre["checkpoint"] = {"resumen": "Contenido omitido por tamaño; consulta el archivo estado."}
        sobre["entorno"]["status"] = actual["status"][:500]
        texto = json.dumps(sobre, ensure_ascii=False, indent=2)
    if len(cabecera + texto) > max_chars:
        raise ValueError("El sobre mínimo de contexto excede max_chars")
    return cabecera + texto
