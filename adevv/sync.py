"""Sincronización de skills, agentes y workflows en los arneses globales.

Mantiene las carpetas confirmadas de Claude Code, Codex y Antigravity sincronizadas
con la versión activa de Adevv, registrando huellas SHA-256 y protegiendo
archivos ajenos o editados a mano.
"""

import hashlib
import os
import re
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from adevv import __version__, processes
from adevv._build import is_symlink_or_junction
from adevv.store import (
    get_active_info,
    get_active_version_dir,
    get_config,
    get_sync_registry,
    set_sync_registry,
)


class EstadoDestino(str, Enum):
    NO_DETECTADO = "NO_DETECTADO"
    DESACTIVADO = "DESACTIVADO"
    DESFASADO = "DESFASADO"
    INCOMPLETO = "INCOMPLETO"
    SINCRONIZADO = "SINCRONIZADO"


def get_target_base(target: str) -> Path:
    """Retorna la carpeta base de un arnés respetando variables de entorno."""
    if target == "claude":
        env_val = os.environ.get("CLAUDE_HOME")
        return Path(env_val).resolve() if env_val else (Path.home() / ".claude").resolve()
    elif target == "codex":
        env_val = os.environ.get("CODEX_HOME")
        return Path(env_val).resolve() if env_val else (Path.home() / ".codex").resolve()
    elif target == "agy":
        env_val = os.environ.get("AGY_HOME")
        return Path(env_val).resolve() if env_val else (Path.home() / ".gemini" / "config").resolve()
    raise ValueError(f"Destino no soportado: {target}")


DESTINOS: Dict[str, Dict[str, Any]] = {
    "claude": {
        "nombre": "Claude Code",
        "base": lambda: get_target_base("claude"),
        "carpetas": {"skills": "skills", "agents": "agents"},
    },
    "codex": {
        "nombre": "Codex",
        "base": lambda: get_target_base("codex"),
        "carpetas": {"skills": "skills", "agents": "agents"},
    },
    "agy": {
        "nombre": "Antigravity",
        "base": lambda: get_target_base("agy"),
        "carpetas": {"skills": "skills", "workflows": "workflows"},
    },
}


def calcular_sha256(content: bytes) -> str:
    """Calcula la huella SHA-256 en formato hexadecimal."""
    return hashlib.sha256(content).hexdigest()


def es_enlace(path: Path) -> bool:
    """Verifica si la ruta es un enlace simbólico o un reparse point en NTFS."""
    return is_symlink_or_junction(path)


def ruta_segura_dentro_de(base_dir: Path, rel_path: str) -> Optional[Path]:
    """Valida que rel_path resuelva estrictamente dentro de base_dir sin traversal."""
    try:
        norm = os.path.normpath(rel_path)
        if norm.startswith("..") or os.path.isabs(norm):
            return None
        candidate = (base_dir / norm).resolve()
        base_resolved = base_dir.resolve()
        candidate.relative_to(base_resolved)
        return candidate
    except (ValueError, OSError):
        return None


def resolver_rutas_contenido(rel_path: str, content: bytes, version_dir: Path) -> bytes:
    """Reemplaza rutas relativas prohibidas por rutas absolutas a la versión instalada."""
    posix_root = version_dir.as_posix()
    text = content.decode("utf-8", errors="replace")

    if rel_path.startswith("agents/codex/") or rel_path.startswith("agents/"):
        text = re.sub(
            r"\.agents/agents/([a-zA-Z0-9_\-]+)\.md",
            rf"{posix_root}/agents/\1.md",
            text,
        )
        text = re.sub(
            r"\.agents/skills/([a-zA-Z0-9_\-]+)/SKILL\.md",
            rf"{posix_root}/skills/\1/SKILL.md",
            text,
        )
        text = re.sub(r"\.agents/skills/", f"{posix_root}/skills/", text)
        text = re.sub(r"\.agents/", f"{posix_root}/", text)
        text = re.sub(r"\.\./skills/", f"{posix_root}/skills/", text)

        text = re.sub(
            r"(?<![/\w.-])agents/([a-zA-Z0-9_\-]+)\.md",
            rf"{posix_root}/agents/\1.md",
            text,
        )
        text = re.sub(
            r"(?<![/\w.-])skills/([a-zA-Z0-9_\-]+)/SKILL\.md",
            rf"{posix_root}/skills/\1/SKILL.md",
            text,
        )
        text = re.sub(
            r"(?<![/\w.-])skills/<nombre>/SKILL\.md",
            rf"{posix_root}/skills/<nombre>/SKILL.md",
            text,
        )

    elif rel_path.startswith("workflows/"):
        text = re.sub(
            r"\.\./skills/([a-zA-Z0-9_\-]+)/SKILL\.md",
            rf"{posix_root}/skills/\1/SKILL.md",
            text,
        )
        text = re.sub(
            r"\.agents/skills/([a-zA-Z0-9_\-]+)/SKILL\.md",
            rf"{posix_root}/skills/\1/SKILL.md",
            text,
        )
        text = re.sub(r"\.agents/", f"{posix_root}/", text)
        text = re.sub(r"\.\./skills/", f"{posix_root}/skills/", text)

        text = re.sub(
            r"(?<![/\w.-])skills/([a-zA-Z0-9_\-]+)/SKILL\.md",
            rf"{posix_root}/skills/\1/SKILL.md",
            text,
        )

    return text.encode("utf-8")


def recopilar_archivos_destino(destino_key: str, origen_dir: Path) -> Dict[str, bytes]:
    """Recopila todos los archivos que deben escribirse en el destino dado."""
    archivos: Dict[str, bytes] = {}
    skills_src = origen_dir / "skills"
    agents_src = origen_dir / "agents"
    workflows_src = origen_dir / "workflows"

    def es_ruta_distribuible_skill(path: Path) -> bool:
        rel_partes = path.relative_to(skills_src).parts
        if any(p.startswith(".") for p in rel_partes):
            return False
        if "scripts" in rel_partes or "__pycache__" in rel_partes:
            return False
        if path.suffix.lower() in [".py", ".pyc"]:
            return False
        return True

    if skills_src.exists() and skills_src.is_dir():
        for root, dirs, files in os.walk(skills_src):
            dirs[:] = [d for d in dirs if d != "scripts" and d != "__pycache__" and not d.startswith(".")]
            for f in files:
                full_p = Path(root) / f
                if es_ruta_distribuible_skill(full_p):
                    rel = full_p.relative_to(origen_dir).as_posix()
                    archivos[rel] = full_p.read_bytes()

    if destino_key == "claude":
        if agents_src.exists() and agents_src.is_dir():
            for f in agents_src.iterdir():
                if f.is_file() and f.suffix.lower() == ".md" and not f.name.startswith("."):
                    rel = f.relative_to(origen_dir).as_posix()
                    archivos[rel] = f.read_bytes()

    elif destino_key == "codex":
        codex_agents = agents_src / "codex"
        if codex_agents.exists() and codex_agents.is_dir():
            for f in codex_agents.iterdir():
                if f.is_file() and f.suffix.lower() == ".toml" and not f.name.startswith("."):
                    rel_in_dest = f"agents/{f.name}"
                    raw_content = f.read_bytes()
                    resolved = resolver_rutas_contenido(f"agents/codex/{f.name}", raw_content, origen_dir)
                    archivos[rel_in_dest] = resolved

    elif destino_key == "agy":
        if workflows_src.exists() and workflows_src.is_dir():
            for f in workflows_src.iterdir():
                if f.is_file() and f.suffix.lower() == ".md" and not f.name.startswith("."):
                    rel = f.relative_to(origen_dir).as_posix()
                    raw_content = f.read_bytes()
                    resolved = resolver_rutas_contenido(rel, raw_content, origen_dir)
                    archivos[rel] = resolved

    return archivos


def planificar_sincronizacion(
    destino_key: str,
    origen_dir: Path,
    version: str,
    forzar: bool = False,
) -> Dict[str, Any]:
    """Evalúa las acciones necesarias para sincronizar un destino sin ejecutar escrituras."""
    cfg_destino = DESTINOS.get(destino_key, {})
    nombre_ui = cfg_destino.get("nombre", destino_key)
    carpetas_confirmadas = cfg_destino.get("carpetas", {})

    get_base: Callable[[], Path] = cfg_destino.get("base", lambda: Path.home() / f".{destino_key}")
    base_dir = get_base()

    config = get_config()
    if destino_key in config.get("disabled_targets", []):
        return {
            "estado": EstadoDestino.DESACTIVADO,
            "nombre": nombre_ui,
            "detalle": "desactivado",
            "acciones_escribir": {},
            "acciones_borrar": [],
            "conflictos": [],
            "rutas_ignoradas": [],
            "sin_cambios": True,
        }

    if not base_dir.exists():
        return {
            "estado": EstadoDestino.NO_DETECTADO,
            "nombre": nombre_ui,
            "detalle": "no detectado",
            "acciones_escribir": {},
            "acciones_borrar": [],
            "conflictos": [],
            "rutas_ignoradas": [],
            "sin_cambios": True,
        }

    if not carpetas_confirmadas:
        return {
            "estado": EstadoDestino.NO_DETECTADO,
            "nombre": nombre_ui,
            "detalle": "sin confirmar",
            "acciones_escribir": {},
            "acciones_borrar": [],
            "conflictos": [],
            "rutas_ignoradas": [],
            "sin_cambios": True,
        }

    registro = get_sync_registry(destino_key)
    registro_valido = isinstance(registro, dict) and isinstance(registro.get("files"), dict)
    archivos_registrados: Dict[str, str] = registro.get("files", {}) if registro_valido else {}
    version_registrada = registro.get("version") if registro_valido else None

    contenido_fuente = recopilar_archivos_destino(destino_key, origen_dir)

    acciones_escribir: Dict[str, Tuple[Path, bytes, str]] = {}
    conflictos: List[str] = []
    adopciones: Dict[str, str] = {}
    rutas_ignoradas: List[str] = []
    archivos_sin_cambio: int = 0

    for rel_path, content_bytes in contenido_fuente.items():
        dest_path = ruta_segura_dentro_de(base_dir, rel_path)
        if dest_path is None:
            rutas_ignoradas.append(rel_path)
            continue

        nueva_huella = calcular_sha256(content_bytes)

        if dest_path.exists():
            if es_enlace(dest_path):
                conflictos.append(rel_path)
                continue

            try:
                huella_disco = calcular_sha256(dest_path.read_bytes())
            except OSError:
                conflictos.append(rel_path)
                continue

            if not registro_valido:
                if huella_disco == nueva_huella:
                    adopciones[rel_path] = nueva_huella
                    archivos_sin_cambio += 1
                else:
                    conflictos.append(rel_path)
            else:
                if rel_path not in archivos_registrados:
                    conflictos.append(rel_path)
                else:
                    huella_registrada = archivos_registrados[rel_path]
                    if huella_disco == huella_registrada:
                        if huella_disco == nueva_huella:
                            archivos_sin_cambio += 1
                        else:
                            acciones_escribir[rel_path] = (dest_path, content_bytes, nueva_huella)
                    else:
                        if forzar:
                            acciones_escribir[rel_path] = (dest_path, content_bytes, nueva_huella)
                        else:
                            conflictos.append(rel_path)
        else:
            acciones_escribir[rel_path] = (dest_path, content_bytes, nueva_huella)

    acciones_borrar: List[Tuple[str, Path]] = []
    if registro_valido:
        for rel_path, huella_registrada in archivos_registrados.items():
            if rel_path not in contenido_fuente:
                dest_path = ruta_segura_dentro_de(base_dir, rel_path)
                if dest_path is None:
                    rutas_ignoradas.append(rel_path)
                    continue

                if dest_path.exists():
                    if not es_enlace(dest_path):
                        try:
                            huella_disco = calcular_sha256(dest_path.read_bytes())
                            if huella_disco == huella_registrada:
                                acciones_borrar.append((rel_path, dest_path))
                        except OSError:
                            pass

    sin_cambios = (
        len(acciones_escribir) == 0
        and len(acciones_borrar) == 0
        and len(conflictos) == 0
        and version_registrada == version
    )

    if conflictos:
        estado = EstadoDestino.INCOMPLETO
    elif version_registrada != version or not registro_valido:
        estado = EstadoDestino.DESFASADO
    else:
        estado = EstadoDestino.SINCRONIZADO

    return {
        "estado": estado,
        "nombre": nombre_ui,
        "base_dir": base_dir,
        "detalle": None,
        "acciones_escribir": acciones_escribir,
        "acciones_borrar": acciones_borrar,
        "adopciones": adopciones,
        "conflictos": conflictos,
        "rutas_ignoradas": rutas_ignoradas,
        "sin_cambios": sin_cambios,
        "archivos_sin_cambio": archivos_sin_cambio,
        "registro_anterior": archivos_registrados,
    }


def obtener_estado_destino(destino_key: str, version_activa: str) -> Dict[str, Any]:
    """Calcula y devuelve el estado actual de un destino sin ejecutar escrituras."""
    origen_dir = get_active_version_dir()
    plan = planificar_sincronizacion(destino_key, origen_dir, version_activa)
    return {
        "estado": plan["estado"],
        "nombre": plan["nombre"],
        "detalle": plan.get("detalle"),
        "conflictos": plan.get("conflictos", []),
    }


def sincronizacion_bloqueada() -> bool:
    """Protege copias globales también si el bucle ancestro no se enumera."""
    return bool(os.environ.get("ORQUESTAR_PASO") or processes.hay_bucles_en_marcha())


def sincronizar_destinos(
    origen_dir: Optional[Path] = None,
    version: Optional[str] = None,
    forzar: bool = False,
) -> Dict[str, Any]:
    """Aplica la sincronización completa sobre los destinos detectados."""
    if origen_dir is None:
        origen_dir = get_active_version_dir()

    if version is None:
        act = get_active_info()
        version = act.get("version", __version__) if act else __version__

    resultados: Dict[str, Any] = {}
    bloqueada = sincronizacion_bloqueada()

    for destino_key in DESTINOS.keys():
        plan = planificar_sincronizacion(destino_key, origen_dir, version, forzar=forzar)
        estado = plan["estado"]

        if estado in (EstadoDestino.NO_DETECTADO, EstadoDestino.DESACTIVADO):
            resultados[destino_key] = {
                "estado": estado,
                "nombre": plan["nombre"],
                "detalle": plan.get("detalle"),
                "sin_cambios": plan.get("sin_cambios", True),
                "escritos": 0,
                "borrados": 0,
                "conflictos": [],
                "rutas_ignoradas": [],
            }
            continue

        if bloqueada:
            sin_cambios = plan.get("sin_cambios", False)
            resultados[destino_key] = {
                "estado": estado if sin_cambios else EstadoDestino.DESFASADO,
                "nombre": plan["nombre"],
                "detalle": None if sin_cambios else "copias pendientes mientras haya bucles o pasos en marcha",
                "sin_cambios": sin_cambios,
                "escritos": 0,
                "borrados": 0,
                "conflictos": plan.get("conflictos", []),
                "rutas_ignoradas": plan.get("rutas_ignoradas", []),
            }
            continue

        base_dir: Path = plan["base_dir"]
        base_dir.mkdir(parents=True, exist_ok=True)

        nuevo_registro_archivos: Dict[str, str] = dict(plan["registro_anterior"])
        nuevo_registro_archivos.update(plan.get("adopciones", {}))

        escritos = 0
        for rel_path, (dest_p, content_bytes, huella) in plan["acciones_escribir"].items():
            dest_p.parent.mkdir(parents=True, exist_ok=True)
            dest_p.write_bytes(content_bytes)
            nuevo_registro_archivos[rel_path] = huella
            escritos += 1

        borrados = 0
        for rel_path, dest_p in plan["acciones_borrar"]:
            try:
                dest_p.unlink()
                borrados += 1
                nuevo_registro_archivos.pop(rel_path, None)

                # Intentar limpiar directorios padre si quedan vacíos
                parent = dest_p.parent
                base_res = base_dir.resolve()
                while parent.resolve() != base_res and parent.resolve().is_relative_to(base_res):
                    if any(parent.iterdir()):
                        break
                    parent.rmdir()
                    parent = parent.parent
            except OSError:
                pass

        conflictos = plan.get("conflictos", [])
        estado_final = EstadoDestino.INCOMPLETO if conflictos else EstadoDestino.SINCRONIZADO

        nuevo_registro: Dict[str, Any] = {
            "version": version,
            "files": nuevo_registro_archivos,
        }
        set_sync_registry(destino_key, nuevo_registro)

        resultados[destino_key] = {
            "estado": estado_final,
            "nombre": plan["nombre"],
            "detalle": plan.get("detalle"),
            "sin_cambios": plan.get("sin_cambios", False) and escritos == 0 and borrados == 0,
            "escritos": escritos,
            "borrados": borrados,
            "conflictos": conflictos,
            "rutas_ignoradas": plan.get("rutas_ignoradas", []),
        }

    return resultados
