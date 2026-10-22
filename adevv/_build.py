"""Backend de empaquetado PEP 517 in-tree y validacion de lista blanca para adevv."""

import csv
import hashlib
import io
import os
import re
import stat
import subprocess
import tarfile
import zipfile
from base64 import urlsafe_b64encode
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None


WHITELIST_DIRS = ("adevv", "skills", "agents", "workflows")
WHITELIST_FILES = ("pyproject.toml", "README.md", "LICENSE")

FORBIDDEN_EXTENSIONS = (".pyc", ".pid", ".log", ".jsonl")
FORBIDDEN_DIRS = ("__pycache__",)


class ForbiddenContentError(Exception):
    """Error al detectar archivos prohibidos en el arbol distribuible."""
    pass


def _is_symlink_or_junction(path: Path) -> bool:
    """Detecta enlaces simbolicos o junctions en Windows y POSIX."""
    try:
        st = os.lstat(path)
        if stat.S_ISLNK(st.st_mode):
            return True
        if hasattr(st, "st_file_attributes"):
            file_attribute_reparse_point = 0x0400
            if bool(st.st_file_attributes & file_attribute_reparse_point):
                return True
    except OSError:
        pass
    return path.is_symlink()


def is_forbidden(rel_path: str) -> bool:
    """Indica si una ruta relativa coincide con los patrones prohibidos."""
    norm = rel_path.replace("\\", "/").strip("/")
    parts = norm.split("/")
    filename = parts[-1]

    for forbidden_dir in FORBIDDEN_DIRS:
        if forbidden_dir in parts:
            return True

    for ext in FORBIDDEN_EXTENSIONS:
        if filename.endswith(ext):
            return True

    return False


def inspect_distribution_cleanliness(root_dir: Path) -> None:
    """Inspecciona el arbol distribuible y falla si hay contenido prohibido."""
    root = root_dir.resolve()

    if (root / ".git").is_dir() or (root / ".git").is_file():
        res = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                rel_f = line.strip().replace("\\", "/")
                if not rel_f:
                    continue
                first_part = rel_f.split("/")[0]
                if first_part in WHITELIST_DIRS:
                    file_p = root / rel_f
                    if file_p.exists() and _is_symlink_or_junction(file_p):
                        raise ForbiddenContentError(f"Enlace simbolico prohibido detectado: {rel_f}")
                    if is_forbidden(rel_f):
                        raise ForbiddenContentError(f"Archivo prohibido detectado en la distribucion: {rel_f}")
            return

    for d_name in WHITELIST_DIRS:
        target_dir = root / d_name
        if not target_dir.exists():
            continue

        for dirpath, dirnames, filenames in os.walk(target_dir):
            current_path = Path(dirpath)
            for f in sorted(filenames):
                file_p = current_path / f
                rel_f = str(file_p.relative_to(root)).replace("\\", "/")
                if _is_symlink_or_junction(file_p):
                    raise ForbiddenContentError(f"Enlace simbolico prohibido detectado: {rel_f}")
                if is_forbidden(rel_f):
                    raise ForbiddenContentError(f"Archivo prohibido detectado en la distribucion: {rel_f}")

            for d in list(dirnames):
                sub_p = current_path / d
                rel_d = str(sub_p.relative_to(root)).replace("\\", "/")
                if _is_symlink_or_junction(sub_p):
                    raise ForbiddenContentError(f"Junction o enlace simbolico prohibido detectado: {rel_d}")


def collect_distribution_files(root_dir: Path) -> List[Tuple[Path, str]]:
    """Recolecta los archivos del paquete siguiendo la lista blanca estricta."""
    inspect_distribution_cleanliness(root_dir)
    root = root_dir.resolve()
    collected: List[Tuple[Path, str]] = []

    for f_name in WHITELIST_FILES:
        fp = root / f_name
        if fp.is_file() and not _is_symlink_or_junction(fp):
            collected.append((fp, f_name))

    for d_name in WHITELIST_DIRS:
        target_dir = root / d_name
        if not target_dir.is_dir():
            continue

        for dirpath, dirnames, filenames in os.walk(target_dir):
            current_path = Path(dirpath)
            for f in sorted(filenames):
                file_p = current_path / f
                if _is_symlink_or_junction(file_p):
                    continue
                rel = str(file_p.relative_to(root)).replace("\\", "/")
                if not is_forbidden(rel):
                    collected.append((file_p, rel))

    return collected


def _read_project_metadata(root: Path) -> Dict[str, str]:
    """Extrae name y version de pyproject.toml."""
    pyproject_path = root / "pyproject.toml"
    name = "adevv"
    version = "0.1.0"

    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        if tomllib:
            try:
                data = tomllib.loads(content)
                proj = data.get("project", {})
                name = proj.get("name", name)
                version = proj.get("version", version)
            except Exception:
                pass
        else:
            m_name = re.search(r'name\s*=\s*"([^"]+)"', content)
            m_ver = re.search(r'version\s*=\s*"([^"]+)"', content)
            if m_name:
                name = m_name.group(1)
            if m_ver:
                version = m_ver.group(1)

    return {"name": name, "version": version}


def _sha256_record(data: bytes) -> str:
    """Calcula el hash sha256 base64url para el archivo RECORD."""
    digest = hashlib.sha256(data).digest()
    encoded = urlsafe_b64encode(digest).decode("latin1").rstrip("=")
    return f"sha256={encoded}"


def build_wheel(wheel_directory: str, config_settings=None, metadata_directory=None) -> str:
    """Construye un wheel PEP 517 conteniendo unicamente la lista blanca."""
    root_str = (config_settings or {}).get("root") if config_settings else None
    root = Path(root_str).resolve() if root_str else Path.cwd()
    meta = _read_project_metadata(root)
    name = meta["name"]
    version = meta["version"]

    dist_info = f"{name}-{version}.dist-info"
    wheel_filename = f"{name}-{version}-py3-none-any.whl"
    out_dir = Path(wheel_directory).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    wheel_path = out_dir / wheel_filename

    metadata_text = (
        "Metadata-Version: 2.1\n"
        f"Name: {name}\n"
        f"Version: {version}\n"
        "Summary: Herramienta global para desarrollo orquestado multi-arnés\n"
        "Requires-Python: >=3.11\n"
    )

    wheel_text = (
        "Wheel-Version: 1.0\n"
        f"Generator: adevv._build ({version})\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    )

    entry_points_text = (
        "[console_scripts]\n"
        "adevv = adevv.cli:main\n"
    )

    records: List[Tuple[str, str, int]] = []
    files_to_pack = collect_distribution_files(root)

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for full_path, arcname in files_to_pack:
            if not any(arcname.startswith(f"{d}/") for d in WHITELIST_DIRS):
                continue
            data = full_path.read_bytes()
            zf.writestr(arcname, data)
            records.append((arcname, _sha256_record(data), len(data)))

        meta_bytes = metadata_text.encode("utf-8")
        zf.writestr(f"{dist_info}/METADATA", meta_bytes)
        records.append((f"{dist_info}/METADATA", _sha256_record(meta_bytes), len(meta_bytes)))

        wheel_bytes = wheel_text.encode("utf-8")
        zf.writestr(f"{dist_info}/WHEEL", wheel_bytes)
        records.append((f"{dist_info}/WHEEL", _sha256_record(wheel_bytes), len(wheel_bytes)))

        ep_bytes = entry_points_text.encode("utf-8")
        zf.writestr(f"{dist_info}/entry_points.txt", ep_bytes)
        records.append((f"{dist_info}/entry_points.txt", _sha256_record(ep_bytes), len(ep_bytes)))

        record_io = io.StringIO()
        writer = csv.writer(record_io, lineterminator="\n")
        for r_name, r_hash, r_len in records:
            writer.writerow([r_name, r_hash, r_len])
        writer.writerow([f"{dist_info}/RECORD", "", ""])
        zf.writestr(f"{dist_info}/RECORD", record_io.getvalue().encode("utf-8"))

    return wheel_filename


def build_sdist(sdist_directory: str, config_settings=None) -> str:
    """Construye un sdist conteniendo unicamente la lista blanca."""
    root_str = (config_settings or {}).get("root") if config_settings else None
    root = Path(root_str).resolve() if root_str else Path.cwd()
    meta = _read_project_metadata(root)
    name = meta["name"]
    version = meta["version"]

    sdist_filename = f"{name}-{version}.tar.gz"
    out_dir = Path(sdist_directory).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    sdist_path = out_dir / sdist_filename

    prefix = f"{name}-{version}"
    files_to_pack = collect_distribution_files(root)

    with tarfile.open(sdist_path, "w:gz") as tar:
        for full_path, arcname in files_to_pack:
            tar.add(full_path, arcname=f"{prefix}/{arcname}")

    return sdist_filename


def get_requires_for_build_wheel(config_settings=None) -> List[str]:
    return []


def get_requires_for_build_sdist(config_settings=None) -> List[str]:
    return []
