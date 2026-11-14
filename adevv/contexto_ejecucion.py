"""Política ligera de proyecto y detección de superficies críticas."""

from fnmatch import fnmatch
import json
from pathlib import Path

POLITICA_BASE = (
    "# Política base\n"
    "Prioriza la agilidad: decide autónomamente el camino más simple para cada objetivo, manteniendo módulos cohesivos.\n"
    "Lo único obligatorio antes de cerrar es verificar el cambio con las pruebas y chequeos del proyecto sin causar efectos laterales externos ni acciones irreversibles.\n"
)

SUPERFICIES_CRITICAS = (
    "adevv/release_tools.py",
    "adevv/revisiones.py",
    "adevv/contexto_ejecucion.py",
    "adevv/store.py",
    "skills/orquestar/",
    "skills/release/",
    "skills/telegram_gateway/",
    "orchestration.json",
    "task_config.yaml",
    ".env",
)


def _leer_cfg_ejecucion(root: Path) -> dict:
    cfg_path = root / "orchestration.json"
    if not cfg_path.is_file():
        return {}
    try:
        datos = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"orchestration.json inválido: {exc}") from exc
    ejecucion = datos.get("execution")
    if ejecucion is None:
        return {}
    if not isinstance(ejecucion, dict):
        raise ValueError("orchestration.json: 'execution' debe ser un objeto.")
    return ejecucion


def cargar_politica(root: Path) -> dict:
    """Carga PROJECT.md (o la ruta configurada) o usa POLITICA_BASE por defecto."""
    root = Path(root).resolve()
    ejecucion = _leer_cfg_ejecucion(root)
    rel = ejecucion.get("policy")
    if rel is not None:
        if not isinstance(rel, str) or not rel.strip():
            raise ValueError("execution.policy debe ser una ruta relativa no vacía.")
        destino = (root / rel).resolve()
        if not destino.is_relative_to(root) or not destino.is_file():
            raise ValueError(f"execution.policy inválido o inexistente: {rel}")
        return {"path": destino.relative_to(root).as_posix(), "text": destino.read_text(encoding="utf-8")}
    local = root / "PROJECT.md"
    if local.is_file():
        return {"path": "PROJECT.md", "text": local.read_text(encoding="utf-8")}
    return {"path": "<builtin:default>", "text": POLITICA_BASE}


def superficies_criticas(root: Path) -> tuple[str, ...]:
    """Devuelve los prefijos/patrones considerados superficie crítica en el repositorio."""
    ejecucion = _leer_cfg_ejecucion(Path(root).resolve())
    custom = ejecucion.get("critical_paths")
    if isinstance(custom, list) and all(isinstance(x, str) and x.strip() for x in custom):
        return tuple(x.strip().replace("\\", "/") for x in custom)
    return SUPERFICIES_CRITICAS


def toca_superficie_critica(root: Path, rutas) -> list[str]:
    """Filtra las rutas que tocan alguna superficie crítica."""
    patrones = superficies_criticas(root)
    tocadas = []
    for ruta in rutas or ():
        norm = str(ruta).strip().replace("\\", "/").lstrip("./")
        if not norm:
            continue
        if any(norm == p.rstrip("/") or norm.startswith(p.rstrip("/") + "/") or fnmatch(norm, p) for p in patrones):
            tocadas.append(norm)
    return tocadas
