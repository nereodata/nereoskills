"""Actualizador automático de versiones publicadas de Adevv.

Gestiona la consulta y descarga de versiones publicadas, conmutación atómica de active.json,
resincronización de arneses y evaluación de la ventana de actualización según F-03.
"""

import datetime
import importlib.util
import io
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from adevv import __version__, processes
from adevv.store import (
    get_active_info,
    get_adevv_home,
    get_config,
    get_update_state,
    set_active_info,
    set_config,
    set_update_state,
)
from adevv.sync import EstadoDestino, sincronizacion_bloqueada, sincronizar_destinos


def hay_bucles_en_marcha() -> List[Dict[str, Any]]:
    """Consulta procesos bucle delegando a processes.hay_bucles_en_marcha."""
    return processes.hay_bucles_en_marcha()


def detectar_procesos_adevv() -> List[Dict[str, Any]]:
    """Consulta procesos vivos delegando a processes.detectar_procesos_adevv."""
    return processes.detectar_procesos_adevv()


def formatear_proceso_ui(proc: Dict[str, Any]) -> str:
    """Formatea representación de un proceso delegando a processes.formatear_proceso_ui."""
    return processes.formatear_proceso_ui(proc)


class ResultadoActualizacion:
    """Resultados posibles de la evaluación de actualización según requirements §4."""
    DESACTIVADA = "DESACTIVADA"
    DENTRO_DE_ORQUESTACION = "DENTRO_DE_ORQUESTACION"
    DESARROLLO = "DESARROLLO"
    ESPERA = "ESPERA"
    SIN_RED = "SIN_RED"
    AL_DIA = "AL_DIA"
    APLAZADA = "APLAZADA"
    APLICADA = "APLICADA"
    FALLIDA = "FALLIDA"


class TipoFalloInstalacion:
    """Clasificación de fallos durante la instalación."""
    OK = "OK"
    RED = "RED"
    FALLO = "FALLO"


def _version_es_mayor(v1: str, v2: str) -> bool:
    """Compara si la versión v1 es numéricamente mayor que v2."""
    try:
        p1 = [int(x) for x in v1.split(".") if x.isdigit()]
        p2 = [int(x) for x in v2.split(".") if x.isdigit()]
        return p1 > p2
    except ValueError:
        return v1 > v2


def _get_git_env() -> Dict[str, str]:
    """Variables de entorno para llamadas a Git no interactivas sin prompts de credenciales."""
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"
    env["GIT_ASKPASS"] = "echo"
    return env


def _horas_transcurridas(fecha_iso: Optional[str], ahora_dt: datetime.datetime) -> float:
    """Calcula las horas transcurridas desde una fecha ISO hasta ahora."""
    if not fecha_iso:
        return float("inf")
    try:
        dt = datetime.datetime.fromisoformat(fecha_iso)
        diff = (ahora_dt - dt).total_seconds() / 3600.0
        return diff if diff >= 0 else float("inf")
    except Exception:
        return float("inf")


def _read_package_version_from_dir(directory: Path) -> Optional[str]:
    """Lee la versión declarada en pyproject.toml o adevv/__init__.py de un directorio."""
    pyproject_path = directory / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        m = re.search(r'version\s*=\s*"([^"]+)"', content)
        if m:
            return m.group(1).strip()

    init_path = directory / "adevv" / "__init__.py"
    if init_path.exists():
        content = init_path.read_text(encoding="utf-8")
        m = re.search(r'__version__\s*=\s*"([^"]+)"', content)
        if m:
            return m.group(1).strip()

    return None


def consultar_versiones_publicadas(origin_url: Optional[str] = None, timeout: int = 5) -> Tuple[List[str], Dict[str, str], Optional[str]]:
    """Consulta versiones publicadas (etiquetas anotadas vX.Y.Z^{}) en el origen remoto."""
    remote = origin_url or os.environ.get("ADEVV_ORIGIN_URL") or "https://github.com/nereodata/nereoskills.git"

    cmd = ["git", "ls-remote", "--tags", remote]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=_get_git_env(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return [], {}, f"Timeout de {timeout} s al consultar {remote}"
    except Exception as exc:
        return [], {}, f"Error al ejecutar git ls-remote: {exc}"

    if res.returncode != 0:
        err_lower = (res.stderr or "").lower()
        if "terminal prompt" in err_lower or "username" in err_lower or "could not read" in err_lower:
            return [], {}, f"Error de credenciales al consultar {remote}"
        return [], {}, f"No se pudo consultar {remote}: {res.stderr.strip() or 'error remoto'}"

    mapa_commits: Dict[str, str] = {}
    peeled_regex = re.compile(r"^(\S+)\s+refs/tags/v(\d+\.\d+\.\d+)\^\{\}$")

    for line in res.stdout.splitlines():
        line = line.strip()
        match = peeled_regex.match(line)
        if match:
            commit_hash = match.group(1)
            version_str = match.group(2)
            mapa_commits[version_str] = commit_hash

    versiones_ordenadas = sorted(
        list(mapa_commits.keys()),
        key=lambda v: [int(x) for x in v.split(".") if x.isdigit()],
    )
    return versiones_ordenadas, mapa_commits, None


def limpiar_versiones_antiguas() -> None:
    """Limpia versiones antiguas en versions/ que no sean la activa ni estén en uso por procesos."""
    versions_dir = get_adevv_home() / "versions"
    if not versions_dir.exists() or not versions_dir.is_dir():
        return

    act = get_active_info()
    version_activa = act.get("version") if act else None
    if not any(i.is_dir() and i.name != version_activa and not i.name.startswith(".staging-") for i in versions_dir.iterdir()):
        return
    if sincronizacion_bloqueada():
        return

    procesos = detectar_procesos_adevv()

    for item in versions_dir.iterdir():
        if not item.is_dir():
            continue
        v_name = item.name
        if v_name == version_activa or v_name.startswith(".staging-"):
            continue

        item_path_str = str(item.resolve()).replace("/", "\\").lower()
        v_name_lower = v_name.lower()
        en_uso = False
        for p in procesos:
            cmd = (p.get("cmd") or "").replace("/", "\\").lower()
            cwd = (p.get("cwd") or "").replace("/", "\\").lower()
            if item_path_str in cmd or item_path_str in cwd:
                en_uso = True
                break
            if f"versions\\{v_name_lower}" in cmd or f"versions\\{v_name_lower}" in cwd:
                en_uso = True
                break
            if f"versions/{v_name_lower}" in cmd or f"versions/{v_name_lower}" in cwd:
                en_uso = True
                break

        if not en_uso:
            shutil.rmtree(item, ignore_errors=True)


def filtrar_por_lista_blanca(directory: Path) -> None:
    """Conserva únicamente archivos de la lista blanca y elimina contenido prohibido."""
    from adevv._build import WHITELIST_DIRS, WHITELIST_FILES, is_forbidden

    for item in list(directory.iterdir()):
        if item.is_dir():
            if item.name not in WHITELIST_DIRS:
                shutil.rmtree(item, ignore_errors=True)
        else:
            if item.name not in WHITELIST_FILES:
                try:
                    item.unlink()
                except OSError:
                    pass

    for root, dirs, files in os.walk(str(directory), topdown=False):
        root_path = Path(root)
        for d in list(dirs):
            dir_path = root_path / d
            rel = dir_path.relative_to(directory).as_posix()
            if is_forbidden(rel):
                shutil.rmtree(dir_path, ignore_errors=True)
                dirs.remove(d)
        for f in files:
            file_path = root_path / f
            rel = file_path.relative_to(directory).as_posix()
            if is_forbidden(rel):
                try:
                    file_path.unlink()
                except OSError:
                    pass


def materializar_version_local(version: str) -> Path:
    """Materializa la versión local activa filtrada por lista blanca en ~/.adevv/versions/<V>/."""
    from adevv._build import WHITELIST_DIRS, WHITELIST_FILES

    adevv_home = get_adevv_home()
    versions_parent = adevv_home / "versions"
    versions_parent.mkdir(parents=True, exist_ok=True)
    target_dir = versions_parent / version

    if target_dir.exists():
        if _read_package_version_from_dir(target_dir) != version:
            raise ValueError(f"la versión instalada no es {version}")
        set_active_info({
            "version": version,
            "id": version,
            "origen": "publicada",
            "commit": "",
        })
        return target_dir

    source_dir = Path(__file__).resolve().parents[1]
    staging_dir = versions_parent / f".staging-local-{version}-{os.getpid()}"
    if staging_dir.exists():
        shutil.rmtree(staging_dir, ignore_errors=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    try:
        for d_name in WHITELIST_DIRS:
            s_d = source_dir / d_name
            if s_d.is_dir():
                shutil.copytree(s_d, staging_dir / d_name, dirs_exist_ok=True)
        for f_name in WHITELIST_FILES:
            s_f = source_dir / f_name
            if s_f.is_file():
                shutil.copy2(s_f, staging_dir / f_name)

        filtrar_por_lista_blanca(staging_dir)

        os.rename(str(staging_dir), str(target_dir))

        set_active_info({
            "version": version,
            "id": version,
            "origen": "publicada",
            "commit": "",
        })
        return target_dir
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


def instalar_version_publicada(
    target_version: str,
    commit_hash: Optional[str] = None,
    origin_url: Optional[str] = None,
    timeout: int = 180,
) -> Tuple[bool, str, List[str]]:
    """Descarga e instala una versión publicada en staging y conmuta de forma atómica."""
    adevv_home = get_adevv_home()
    versions_parent = adevv_home / "versions"
    versions_parent.mkdir(parents=True, exist_ok=True)
    target_dir = versions_parent / target_version
    if target_dir.exists():
        if _read_package_version_from_dir(target_dir) != target_version:
            return False, f"la versión instalada no es {target_version}", []
        return _activar_version_publicada(target_dir, target_version, commit_hash)

    staging_dir = versions_parent / f".staging-{target_version}-{os.getpid()}"
    if staging_dir.exists():
        shutil.rmtree(staging_dir, ignore_errors=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    remote = origin_url or os.environ.get("ADEVV_ORIGIN_URL") or "https://github.com/nereodata/nereoskills.git"
    tag_name = f"v{target_version}"
    ref_a_extraer = commit_hash or tag_name

    try:
        if Path(remote).is_dir():
            res = subprocess.run(
                ["git", "archive", "--format=tar", ref_a_extraer],
                cwd=str(remote),
                capture_output=True,
                check=True,
                timeout=timeout,
            )
            with tarfile.open(fileobj=io.BytesIO(res.stdout), mode="r:") as tar:
                if hasattr(tarfile, "data_filter"):
                    tar.extractall(path=staging_dir, filter="data")
                else:
                    tar.extractall(path=staging_dir)
        else:
            with tempfile.TemporaryDirectory() as tmp_clone:
                clone_cmd = [
                    "git", "clone", "--depth", "1", "--branch", tag_name,
                    remote, tmp_clone,
                ]
                subprocess.run(
                    clone_cmd,
                    capture_output=True,
                    check=True,
                    env=_get_git_env(),
                    timeout=timeout,
                )
                if commit_hash:
                    rev_res = subprocess.run(
                        ["git", "-C", tmp_clone, "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    cloned_head = rev_res.stdout.strip()
                    if cloned_head != commit_hash:
                        shutil.rmtree(staging_dir, ignore_errors=True)
                        return False, f"el commit clonado ({cloned_head}) no coincide con el consultado ({commit_hash})", []

                for item in Path(tmp_clone).iterdir():
                    if item.name == ".git":
                        continue
                    dest = staging_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)
    except subprocess.TimeoutExpired:
        shutil.rmtree(staging_dir, ignore_errors=True)
        return False, "la instalación no terminó en 180 s", []
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(staging_dir, ignore_errors=True)
        err_msg = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr or "")
        return False, f"error de red al descargar: {err_msg.strip() or 'fallo de conexión'}", []
    except Exception as exc:
        shutil.rmtree(staging_dir, ignore_errors=True)
        return False, f"Error al descargar e instalar {tag_name}: {exc}", []

    pkg_ver = _read_package_version_from_dir(staging_dir)
    if pkg_ver != target_version:
        shutil.rmtree(staging_dir, ignore_errors=True)
        return False, f"la versión instalada no es {target_version}", []

    filtrar_por_lista_blanca(staging_dir)

    try:
        os.rename(str(staging_dir), str(target_dir))
    except OSError as exc:
        shutil.rmtree(staging_dir, ignore_errors=True)
        return False, f"no se pudo guardar la versión {target_version}: {exc}", []

    return _activar_version_publicada(target_dir, target_version, commit_hash)


def _activar_version_publicada(
    target_dir: Path, target_version: str, commit_hash: Optional[str],
) -> Tuple[bool, str, List[str]]:
    """Conmuta el puntero y sincroniza solo si las copias globales son seguras."""

    set_active_info({
        "version": target_version,
        "id": target_version,
        "origen": "publicada",
        "commit": commit_hash or "",
    })

    sync_module_path = target_dir / "adevv" / "sync.py"
    if sync_module_path.exists() and not sincronizacion_bloqueada():
        try:
            spec = importlib.util.spec_from_file_location("adevv_incoming_sync", str(sync_module_path))
            if spec and spec.loader:
                incoming_sync = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(incoming_sync)
                res_sync = incoming_sync.sincronizar_destinos(origen_dir=target_dir, version=target_version)
            else:
                res_sync = sincronizar_destinos(origen_dir=target_dir, version=target_version)
        except Exception:
            res_sync = sincronizar_destinos(origen_dir=target_dir, version=target_version)
    else:
        res_sync = sincronizar_destinos(origen_dir=target_dir, version=target_version)

    desfasados = []
    for t_key, r in res_sync.items():
        if r.get("estado") in (EstadoDestino.DESFASADO, EstadoDestino.INCOMPLETO):
            desfasados.append(f"{r.get('nombre', t_key)}: {r.get('detalle') or 'archivo de agente bloqueado'}")

    limpiar_versiones_antiguas()
    return True, "OK", desfasados


VERSION_MINIMA_RECARGA = "0.5.0"


def mensaje_actualizacion(version_anterior: str, version_nueva: str, desfasados: List[str]) -> str:
    """Describe instalación, copias pendientes y adopción cooperativa o manual."""
    msg = f"Adevv actualizado de {version_anterior} a {version_nueva}."
    if desfasados:
        msg += " Reinicia las sesiones abiertas de los arneses cuando sus copias estén sincronizadas."
    else:
        msg += " Reinicia las sesiones abiertas de los arneses para usar las skills nuevas."
    bucles = hay_bucles_en_marcha()
    gateways = [p for p in detectar_procesos_adevv() if p.get("tipo") == "gateway"]
    procesos = [*bucles, *gateways]
    if procesos:
        lista = ", ".join(formatear_proceso_ui(p) for p in procesos)
        if _version_es_mayor(VERSION_MINIMA_RECARGA, version_nueva):
            msg += (
                f" La {version_nueva} no admite recarga: reinicia a mano los bucles y gateways en marcha para usarla;"
                " los de v0.5.0 a v0.6.1 se detendrán al terminar su paso o respuesta actual."
            )
        else:
            msg += (
                " Los motores desde v0.5.0 tomarán la versión activa al terminar su paso o respuesta actual"
                " si admite sus opciones; si no, siguen con su versión y lo avisan (desde v1.0.0)."
                " Los anteriores requieren reinicio manual."
            )
        msg += f" En marcha: {lista}."
    if desfasados:
        msg += f" Arneses sin sincronizar: {', '.join(desfasados)}."
    return msg


def evaluar_tabla(
    state: Dict[str, Any],
    config: Dict[str, Any],
    active_info: Optional[Dict[str, Any]],
    ahora: datetime.datetime,
    forzada: bool = False,
    es_instalar: bool = False,
    dentro_orquestacion: bool = False,
) -> Dict[str, Any]:
    """Evalúa la tabla de actualización de forma pura sin efectos secundarios de E/S."""
    version_actual = active_info.get("version", __version__) if active_info else __version__
    origen_tipo = active_info.get("origen", "publicada") if active_info else "publicada"

    if not forzada and not config.get("auto_update", True):
        return {
            "resultado": ResultadoActualizacion.DESACTIVADA,
            "mensaje": None,
            "target_version": None,
            "consultar_remoto": False,
        }

    if (not forzada and not es_instalar) and dentro_orquestacion:
        return {
            "resultado": ResultadoActualizacion.DENTRO_DE_ORQUESTACION,
            "mensaje": None,
            "target_version": None,
            "consultar_remoto": False,
        }

    if not forzada and origen_tipo == "desarrollo":
        return {
            "resultado": ResultadoActualizacion.DESARROLLO,
            "mensaje": None,
            "target_version": None,
            "consultar_remoto": False,
        }

    if not forzada and not es_instalar:
        if _horas_transcurridas(state.get("last_sin_red_at"), ahora) < 1.0:
            return {
                "resultado": ResultadoActualizacion.ESPERA,
                "mensaje": None,
                "target_version": None,
                "consultar_remoto": False,
            }
        if not state.get("aplazada"):
            if _horas_transcurridas(state.get("last_checked_at"), ahora) < 24.0:
                return {
                    "resultado": ResultadoActualizacion.ESPERA,
                    "mensaje": None,
                    "target_version": None,
                    "consultar_remoto": False,
                }

    if state.get("aplazada") and not forzada:
        target_version = state.get("aplazada")
        return {
            "resultado": ResultadoActualizacion.APLAZADA,
            "mensaje": None,
            "target_version": target_version,
            "consultar_remoto": False,
        }

    return {
        "resultado": None,
        "mensaje": None,
        "target_version": None,
        "consultar_remoto": True,
    }


def evaluar_comprobacion_actualizacion(
    forzada: bool = False,
    ahora: Optional[datetime.datetime] = None,
    origin_url: Optional[str] = None,
    es_instalar: bool = False,
) -> Tuple[str, Optional[str], Optional[str]]:
    """Evalúa la tabla de resultados de actualización según requirements §4."""
    ahora_dt = ahora or datetime.datetime.now()
    cfg = get_config()
    act = get_active_info()
    version_actual = act.get("version", __version__) if act else __version__
    state = get_update_state()
    dentro_orquestacion = bool(os.environ.get("ORQUESTAR_PASO") or os.environ.get("ADEVV_BOOTSTRAPPED"))

    decision = evaluar_tabla(
        state=state,
        config=cfg,
        active_info=act,
        ahora=ahora_dt,
        forzada=forzada,
        es_instalar=es_instalar,
        dentro_orquestacion=dentro_orquestacion,
    )

    if not decision["consultar_remoto"]:
        if decision["resultado"] != ResultadoActualizacion.APLAZADA:
            return decision["resultado"], decision["mensaje"], decision["target_version"]

        target_version = decision["target_version"]
        ok, causa, desfasados = instalar_version_publicada(target_version=target_version, origin_url=origin_url)
        if not ok:
            causa_l = causa.lower()
            es_error_red = "red" in causa_l or "conexión" in causa_l or "could not read" in causa_l
            if es_error_red:
                state["last_sin_red_at"] = ahora_dt.isoformat()
                state["last_sin_red_cause"] = causa
                set_update_state(state)
                msg = f"No se pudo consultar {origin_url or 'el origen'}: {causa}. Sigues con la {version_actual}." if (forzada or es_instalar) else None
                return ResultadoActualizacion.SIN_RED, msg, target_version
            else:
                state.pop("aplazada", None)
                state["last_checked_at"] = ahora_dt.isoformat()
                state["last_checked_status"] = ResultadoActualizacion.FALLIDA
                state["fallida"] = target_version
                state["fallida_causa"] = causa
                state["last_failed_at"] = ahora_dt.isoformat()
                set_update_state(state)
                msg = f"No se pudo actualizar a {target_version}: {causa}. Sigues con la {version_actual}. Reintenta con `adevv actualizar`."
                return ResultadoActualizacion.FALLIDA, msg, target_version
        else:
            state.pop("aplazada", None)
            state.pop("fallida", None)
            state["last_checked_at"] = ahora_dt.isoformat()
            state["last_checked_status"] = ResultadoActualizacion.APLICADA
            state["last_applied_at"] = ahora_dt.isoformat()
            state["last_applied_version"] = target_version
            set_update_state(state)
            msg = mensaje_actualizacion(version_actual, target_version, desfasados)
            return ResultadoActualizacion.APLICADA, msg, target_version

    versiones, mapa_commits, err = consultar_versiones_publicadas(origin_url=origin_url)
    if err:
        state["last_sin_red_at"] = ahora_dt.isoformat()
        state["last_sin_red_cause"] = err
        set_update_state(state)
        if forzada or es_instalar:
            msg = f"No se pudo consultar {origin_url or 'el origen'}: {err}. Sigues con la {version_actual}."
        else:
            last_checked = state.get("last_checked_at")
            if last_checked:
                horas_contada = _horas_transcurridas(last_checked, ahora_dt)
                horas_aviso = _horas_transcurridas(state.get("last_notice_sin_red_at"), ahora_dt)
                if horas_contada >= 24 * 7 and horas_aviso >= 24.0:
                    msg = f"No se ha podido comprobar actualizaciones desde {last_checked}: {err}."
                    state["last_notice_sin_red_at"] = ahora_dt.isoformat()
                    set_update_state(state)
                else:
                    msg = None
            else:
                msg = None
        return ResultadoActualizacion.SIN_RED, msg, None

    candidatas = [v for v in versiones if _version_es_mayor(v, version_actual)]
    fallida = state.get("fallida")
    if not forzada and fallida:
        candidatas = [v for v in candidatas if _version_es_mayor(v, fallida)]

    if not candidatas:
        state["last_checked_at"] = ahora_dt.isoformat()
        state["last_checked_status"] = ResultadoActualizacion.AL_DIA
        set_update_state(state)
        msg = f"Adevv {version_actual} está al día." if forzada else None
        return ResultadoActualizacion.AL_DIA, msg, None

    nueva_version = candidatas[-1]
    commit_hash = mapa_commits.get(nueva_version)
    ok, causa, desfasados = instalar_version_publicada(
        target_version=nueva_version,
        commit_hash=commit_hash,
        origin_url=origin_url,
    )
    if not ok:
        causa_l = causa.lower()
        es_error_red = "red" in causa_l or "conexión" in causa_l or "could not read" in causa_l
        if es_error_red:
            state["last_sin_red_at"] = ahora_dt.isoformat()
            state["last_sin_red_cause"] = causa
            set_update_state(state)
            msg = f"No se pudo consultar {origin_url or 'el origen'}: {causa}. Sigues con la {version_actual}." if (forzada or es_instalar) else None
            return ResultadoActualizacion.SIN_RED, msg, nueva_version
        else:
            state["last_checked_at"] = ahora_dt.isoformat()
            state["last_checked_status"] = ResultadoActualizacion.FALLIDA
            state["fallida"] = nueva_version
            state["fallida_causa"] = causa
            state["last_failed_at"] = ahora_dt.isoformat()
            state.pop("aplazada", None)
            set_update_state(state)
            msg = f"No se pudo actualizar a {nueva_version}: {causa}. Sigues con la {version_actual}. Reintenta con `adevv actualizar`."
            return ResultadoActualizacion.FALLIDA, msg, nueva_version

    state.pop("aplazada", None)
    state.pop("fallida", None)
    state["last_checked_at"] = ahora_dt.isoformat()
    state["last_checked_status"] = ResultadoActualizacion.APLICADA
    state["last_applied_at"] = ahora_dt.isoformat()
    state["last_applied_version"] = nueva_version
    set_update_state(state)

    msg = mensaje_actualizacion(version_actual, nueva_version, desfasados)
    return ResultadoActualizacion.APLICADA, msg, nueva_version
