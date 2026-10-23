"""Herramientas de validacion de lanzamiento y etiquetado para adevv."""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None


class ReleaseValidationError(Exception):
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


def validar_publicacion(repo_dir: Path, target_tag: str, origin_url: str | None = None) -> Tuple[bool, str]:
    """Valida que la version del paquete coincida con target_tag y que no este publicada en origin."""
    pkg_ver = _read_package_version(repo_dir)
    norm_target = target_tag.lstrip("vV")

    if pkg_ver != norm_target:
        raise ReleaseValidationError(
            f"La versión del paquete ({pkg_ver}) no coincide con {target_tag}."
        )

    remote_origin = _get_origin_url(repo_dir, origin_url)
    try:
        res = subprocess.run(
            ["git", "ls-remote", "--tags", remote_origin],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=_get_git_env(),
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise ReleaseValidationError(f"Timeout al consultar etiquetas remotas en {remote_origin}.")

    if res.returncode == 0:
        tag_refs = [line.strip().split()[-1] for line in res.stdout.splitlines() if line.strip()]
        exact_ref = f"refs/tags/{target_tag}"
        peeled_ref = f"refs/tags/{target_tag}^{{}}"

        if exact_ref in tag_refs or peeled_ref in tag_refs:
            next_tag = _compute_next_patch(target_tag)
            raise ReleaseValidationError(
                f"{target_tag} ya está publicada: publica {next_tag}."
            )

    return True, "OK"


def publicar_version(repo_dir: Path, target_tag: str, origin_url: str | None = None) -> None:
    """Ejecuta las validaciones de release y crea la etiqueta anotada en origin/main."""
    validar_publicacion(repo_dir, target_tag, origin_url)

    curr_branch = subprocess.run(
        ["git", "-C", str(repo_dir), "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    if curr_branch != "main":
        subprocess.run(
            ["git", "-C", str(repo_dir), "checkout", "main"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(repo_dir), "merge", "--no-ff", curr_branch, "-m", f"chore(release): {target_tag}"],
            capture_output=True,
            check=True,
        )

    subprocess.run(
        ["git", "-C", str(repo_dir), "tag", "-a", target_tag, "-m", f"Release {target_tag}"],
        capture_output=True,
        check=True,
    )

    target_remote = origin_url or "origin"
    subprocess.run(
        ["git", "-C", str(repo_dir), "push", target_remote, "main", "--follow-tags"],
        capture_output=True,
        check=True,
        env=_get_git_env(),
    )
