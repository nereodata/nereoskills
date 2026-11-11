"""Herramientas de validacion de lanzamiento y etiquetado para adevv."""

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple

from adevv.yaml_lite import load_yaml
from adevv.revisiones import pendientes_cierre

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None


class ReleaseValidationError(ValueError):
    """Error de validacion antes de publicar una version."""
    pass


def _get_git_env() -> dict[str, str]:
    """Variables de entorno para ejecucion no interactiva de Git."""
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"
    return env


def _read_package_version(repo_dir: Path) -> str:
    """Obtiene la version declarada en pyproject.toml del repositorio."""
    pyproject_path = repo_dir / "pyproject.toml"
    if not pyproject_path.exists():
        raise ReleaseValidationError(f"No se encontro pyproject.toml en {repo_dir}")

    content = pyproject_path.read_text(encoding="utf-8")
    if tomllib:
        try:
            data = tomllib.loads(content)
            version = data.get("project", {}).get("version")
            if version:
                return str(version).strip()
        except Exception:
            pass

    m = re.search(r'version\s*=\s*"([^"]+)"', content)
    if m:
        return m.group(1).strip()

    raise ReleaseValidationError(f"No se pudo determinar la version en {pyproject_path}")


def _get_origin_url(repo_dir: Path, explicit_origin: str | None = None) -> str:
    """Determina la URL o ruta del remoto de origen."""
    if explicit_origin:
        return explicit_origin

    res = subprocess.run(
        ["git", "-C", str(repo_dir), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        env=_get_git_env(),
    )
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()

    return "origin"


def obtener_versiones_publicadas(origin_url: str) -> List[str]:
    """Consulta las versiones publicadas (etiquetas anotadas vX.Y.Z) en el origen remoto."""
    from adevv.updater import consultar_versiones_publicadas
    versiones, _, _ = consultar_versiones_publicadas(origin_url=origin_url)
    return versiones


def _compute_next_patch(tag_str: str) -> str:
    """Calcula el siguiente numero patch vX.Y.(Z+1)."""
    clean = tag_str.lstrip("vV")
    parts = clean.split(".")
    if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        return f"v{major}.{minor}.{patch + 1}"
    return f"{tag_str}.1"


def _configuracion(repo_dir: Path, cfg: dict | None = None) -> dict:
    """Lee la configuración del proyecto salvo que el llamante ya la tenga."""
    if cfg is not None:
        return cfg
    path = repo_dir / "task_config.yaml"
    return (load_yaml(path) or {}) if path.exists() else {}


def _ejecutar(root, args, shell=False, timeout=120):
    """Ejecuta una operación no interactiva y acotada con errores visibles."""
    env = {**_get_git_env(), "GIT_MERGE_AUTOEDIT": "no"}
    result = subprocess.run(args, cwd=root, env=env, shell=shell, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr).strip() or f"Error: {args}")
    return result.stdout.strip()


def _git(root, *args):
    """Ejecuta Git en la raíz indicada con un límite de 120 segundos."""
    return _ejecutar(root, ["git", *args])


def validar_publicacion(repo_dir: Path, target_tag: str, origin_url: str | None = None,
                        *, cfg: dict | None = None) -> Tuple[bool, str]:
    """Valida versiones, manifiestos, changelog y etiquetas antes de publicar."""
    repo_dir = Path(repo_dir).resolve()
    config = _configuracion(repo_dir, cfg)
    if not re.fullmatch(r"v\d+\.\d+\.\d+", target_tag):
        raise ReleaseValidationError("La etiqueta debe tener formato vX.Y.Z.")
    norm_target = target_tag[1:]
    if (repo_dir / "pyproject.toml").exists() or not config:
        pkg_ver = _read_package_version(repo_dir)
        if pkg_ver != norm_target:
            raise ReleaseValidationError(
                f"La versión del paquete ({pkg_ver}) no coincide con {target_tag}."
            )
    declared = str((config.get("project") or {}).get("version", "")).lstrip("vV")
    if config and declared != norm_target:
        raise ReleaseValidationError("Versión desalineada del manifiesto task_config.yaml.")
    pendientes = pendientes_cierre(repo_dir, target_tag, config)
    if pendientes:
        raise ReleaseValidationError("Cierre pendiente de revisión/trabajo:\n" + "\n".join(pendientes))
    remote_origin = _get_origin_url(repo_dir, origin_url)
    try:
        remote_tags = _ejecutar(repo_dir, ["git", "ls-remote", "--tags", remote_origin], timeout=5)
    except subprocess.TimeoutExpired as error:
        raise ReleaseValidationError(f"Timeout al consultar etiquetas remotas en {remote_origin}.") from error
    except RuntimeError as error:
        raise ReleaseValidationError(f"No se pudieron consultar etiquetas remotas: {error}") from error
    refs = [line.split()[-1] for line in remote_tags.splitlines() if line.strip()]
    if f"refs/tags/{target_tag}" in refs or f"refs/tags/{target_tag}^{{}}" in refs:
        raise ReleaseValidationError(
            f"{target_tag} ya está publicada: publica {_compute_next_patch(target_tag)}."
        )
    if _git(repo_dir, "tag", "--list", target_tag):
        raise ReleaseValidationError("La etiqueta local ya existe.")
    if (repo_dir / "task_config.yaml").exists():
        script = Path(__file__).resolve().parents[1] / "skills/release/scripts/check_manifests_versions.py"
        try:
            _ejecutar(repo_dir, [sys.executable, str(script), "--dir", str(repo_dir)])
        except RuntimeError as error:
            raise ReleaseValidationError(f"Versión desalineada del manifiesto: {error}") from error
    changelog = repo_dir / "CHANGELOG.md"
    if not changelog.exists() or not re.search(
        r"^##\s+\[?v?" + re.escape(norm_target) + r"\]?(?:\s|$)",
        changelog.read_text(encoding="utf-8"), re.MULTILINE
    ):
        raise ReleaseValidationError("Falta el changelog de la versión.")
    return True, "OK"


def _chequeos():
    """Carga el coordinador compartido de chequeos de calidad y release."""
    ruta = Path(__file__).resolve().parents[1] / "skills" / "orquestar" / "chequeos.py"
    spec = importlib.util.spec_from_file_location("adevv_chequeos_release", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def publicar_version(repo_dir: Path, target_tag: str, origin_url: str | None = None,
                     *, rama: str | None = None, cfg: dict | None = None) -> None:
    """Prepara en aislamiento y publica main y etiqueta en una transacción atómica."""
    root = Path(repo_dir).resolve()
    config = _configuracion(root, cfg)
    validar_publicacion(root, target_tag, origin_url, cfg=config)
    if _git(root, "status", "--porcelain"):
        raise ReleaseValidationError("El árbol está sucio.")
    rama = rama or _git(root, "branch", "--show-current")
    original = _git(root, "rev-parse", "refs/heads/main")
    release = _git(root, "rev-parse", rama)
    remote = origin_url or "origin"
    remoto = _git(root, "ls-remote", remote, "refs/heads/main").split()
    if not remoto:
        raise ReleaseValidationError("No existe main en el remoto.")
    _git(root, "fetch", "--no-tags", "--no-write-fetch-head", remote, remoto[0])
    published = False
    created_tag = False
    with tempfile.TemporaryDirectory(prefix="adevv-release-") as tmp:
        worktree = Path(tmp).resolve() / "release"
        try:
            _git(root, "worktree", "add", "--detach", str(worktree), original)
            _git(worktree, "merge", "--ff-only", remoto[0])
            _git(worktree, "merge", "--no-ff", release, "-m", f"chore(release): {target_tag}")
            validar_publicacion(worktree, target_tag, origin_url)
            config = _configuracion(worktree, cfg)
            timeout = (config.get("release") or {}).get("preflight_timeout", 600)
            if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout < float("inf"):
                raise ReleaseValidationError("release.preflight_timeout debe ser positivo y finito (segundos).")
            for command in (config.get("release") or {}).get("preflight", []):
                try:
                    _chequeos().ejecutar_preflight_worktree(root, worktree, command, _ejecutar, timeout=timeout)
                except (RuntimeError, subprocess.TimeoutExpired) as error:
                    raise RuntimeError(f"Fallo de preflight: {error}") from error
            if _git(worktree, "status", "--porcelain"):
                raise RuntimeError("El preflight dejó el árbol sucio.")
            _git(worktree, "tag", "-a", target_tag, "-m", f"Release {target_tag}")
            created_tag = True
            commit = _git(worktree, "rev-parse", "HEAD")
            _git(worktree, "push", "--atomic", remote, f"{commit}:refs/heads/main",
                 f"refs/tags/{target_tag}:refs/tags/{target_tag}")
            published = True
        finally:
            if worktree.exists():
                _git(root, "worktree", "remove", "--force", str(worktree))
            if created_tag and not published:
                _git(root, "tag", "-d", target_tag)
    try:
        _git(root, "update-ref", "refs/heads/main", commit, original)
        _git(root, "checkout", "main")
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"{target_tag} publicada; falta completar el cierre local: {error}") from error
