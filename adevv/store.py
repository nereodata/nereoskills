"""Almacén local de Adevv (~/.adevv/ o $ADEVV_HOME).

Gestiona la persistencia atómica de configuraciones, estado de actualización,
puntero de versión activa y registros de sincronización de arneses.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


def get_adevv_home() -> Path:
    """Retorna la ruta raíz del almacén de usuario ~/.adevv/ o $ADEVV_HOME."""
    env_home = os.environ.get("ADEVV_HOME")
    if env_home:
        return Path(env_home).resolve()
    return (Path.home() / ".adevv").resolve()


def write_json_atomic(path: Path, data: Any, indent: int = 2) -> None:
    """Escribe un documento JSON de forma atómica mediante archivo temporal y os.replace."""
    target_path = Path(path).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=str(target_path.parent),
            delete=False,
            encoding="utf-8",
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)
            json.dump(data, tmp_file, indent=indent, ensure_ascii=False)
            tmp_file.write("\n")
            tmp_file.flush()
            os.fsync(tmp_file.fileno())

        os.replace(str(tmp_path), str(target_path))
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def read_json(path: Path, default: Any = None) -> Any:
    """Lee un documento JSON de disco; devuelve default si no existe o está corrupto."""
    target_path = Path(path).resolve()
    if not target_path.exists():
        return default

    try:
        content = target_path.read_text(encoding="utf-8")
        return json.loads(content)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return default


def get_active_info() -> Optional[Dict[str, Any]]:
    """Lee el puntero de la versión activa de active.json."""
    return read_json(get_adevv_home() / "active.json", default=None)


def set_active_info(data: Dict[str, Any]) -> None:
    """Guarda atómicamente el puntero de la versión activa en active.json."""
    write_json_atomic(get_adevv_home() / "active.json", data)


def get_config() -> Dict[str, Any]:
    """Obtiene la configuración de usuario desde config.json con valores por defecto."""
    default_config: Dict[str, Any] = {"auto_update": True, "disabled_targets": []}
    loaded = read_json(get_adevv_home() / "config.json", default=default_config)
    if not isinstance(loaded, dict):
        return default_config
    loaded.setdefault("auto_update", True)
    loaded.setdefault("disabled_targets", [])
    return loaded


def set_config(data: Dict[str, Any]) -> None:
    """Guarda atómicamente la configuración de usuario en config.json."""
    write_json_atomic(get_adevv_home() / "config.json", data)


def get_update_state() -> Dict[str, Any]:
    """Obtiene el estado de actualización desde update_state.json."""
    loaded = read_json(get_adevv_home() / "update_state.json", default={})
    return loaded if isinstance(loaded, dict) else {}


def set_update_state(data: Dict[str, Any]) -> None:
    """Guarda atómicamente el estado de actualización en update_state.json."""
    write_json_atomic(get_adevv_home() / "update_state.json", data)


def get_sync_registry(target: str) -> Optional[Dict[str, Any]]:
    """Obtiene el registro de sincronización de un arnés desde sync/<target>.json."""
    return read_json(get_adevv_home() / "sync" / f"{target}.json", default=None)


def set_sync_registry(target: str, data: Dict[str, Any]) -> None:
    """Guarda atómicamente el registro de sincronización de un arnés en sync/<target>.json."""
    write_json_atomic(get_adevv_home() / "sync" / f"{target}.json", data)


def get_active_version_dir() -> Path:
    """Determina la ruta de la versión activa instalada o la raíz del paquete/repositorio."""
    active_info = get_active_info()
    if active_info and "version" in active_info:
        version_name = active_info["version"]
        candidate = get_adevv_home() / "versions" / version_name
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()

    return Path(__file__).resolve().parents[1]
