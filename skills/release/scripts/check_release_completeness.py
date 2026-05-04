#!/usr/bin/env python3
"""Verify all backlog items targeted at a given version are closed.

Usage:
    python check_release_completeness.py --version vX.Y.Z [--dir .]

Reads task_config.yaml to determine where backlog items live (master +
components). For every item file whose frontmatter `version` matches
the requested version, checks that `status` is one of:
    completed | cancelled | superseded | rejected

Exits 1 listing any open items, 0 otherwise.

Notes:
- Forces UTF-8 stdout to survive titles with unicode on Windows.
- Warns explicitly when N=0 files were verified — this almost always
  means the configured backlog paths are wrong (or the heuristic
  fallback kicked in and missed everything).
- The task-letter prefixes (T- / B-) are configurable via
  task_config.yaml::task_types: { feature: T, bug: B }. Defaults to T/B.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
from pathlib import Path

# Force UTF-8 stdout to avoid cp1252 crashes on Windows when item
# titles contain unicode characters.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def parse_frontmatter(content: str) -> dict:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip().strip('"').strip("'")
    return metadata


def load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_task_letters(cfg) -> tuple[str, str]:
    """Return (feature_letter, bug_letter). Defaults: T, B."""
    if not cfg:
        return ("T", "B")
    tt = cfg.get("task_types") or {}
    return (
        (tt.get("feature") or "T").upper(),
        (tt.get("bug") or "B").upper(),
    )


def get_search_globs(config_path: Path):
    """Parse task_config.yaml to determine where to look for tasks and bugs.

    Returns (globs, cfg_or_None). Falls back to a heuristic regex parse
    if PyYAML is missing.
    """
    cfg = load_yaml(config_path)
    if cfg is not None:
        globs: list[str] = []
        levels = cfg.get("levels") or {}

        master = levels.get("master") or {}
        if master:
            base_path = master.get("path", "") or ""
            folders = master.get("folders") or {}
            if folders.get("tasks"):
                globs.append(base_path + folders["tasks"] + "*.md")
            if folders.get("bugs"):
                globs.append(base_path + folders["bugs"] + "*.md")

        for comp in levels.get("components") or []:
            base_path = (comp.get("path", "") or "").replace("{name}", "*")
            folders = comp.get("folders") or {}
            if folders.get("tasks"):
                globs.append(base_path + folders["tasks"] + "*.md")
            if folders.get("bugs"):
                globs.append(base_path + folders["bugs"] + "*.md")

        return list(dict.fromkeys(globs)), cfg

    # Fallback when PyYAML is not available.
    print(
        "WARN: PyYAML no instalado. Usando busqueda heuristica (fallback).",
        file=sys.stderr,
    )
    print(
        "      Ejecuta: pip install pyyaml para mejor precision.",
        file=sys.stderr,
    )
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    paths = re.findall(r"path:\s*(.*?)\n", content)
    globs: list[str] = []
    for p in paths:
        p = p.strip().strip("\"'").replace("{name}", "*")
        globs.append(p + "tasks/*.md")
        globs.append(p + "bugs/*.md")
    return list(dict.fromkeys(globs)), None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica que todas las tareas y bugs de una release esten cerradas."
    )
    parser.add_argument("--version", required=True, help="Version target (ej. v1.2.0)")
    parser.add_argument("--dir", default=".", help="Directorio raiz del proyecto")
    args = parser.parse_args()

    root_dir = Path(args.dir)
    config_path = root_dir / "task_config.yaml"

    if not config_path.exists():
        print(
            f"ERROR: no se encontro {config_path}. "
            "Ejecuta este script desde la raiz del proyecto.",
            file=sys.stderr,
        )
        return 1

    search_globs, cfg = get_search_globs(config_path)
    feature_letter, bug_letter = get_task_letters(cfg)
    valid_prefix_re = re.compile(
        rf"^({re.escape(feature_letter)}|{re.escape(bug_letter)})-"
    )

    incomplete: list[dict] = []
    verified_files = 0

    for glob_pattern in search_globs:
        for path in root_dir.glob(glob_pattern):
            if not path.is_file():
                continue

            if not valid_prefix_re.match(path.name):
                continue

            verified_files += 1
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read(4096)
                fm = parse_frontmatter(content)
            except Exception:
                continue

            task_ver = fm.get("version", "")
            if task_ver == args.version:
                status = (fm.get("status") or "").lower()
                if status not in {"completed", "cancelled", "superseded", "rejected"}:
                    incomplete.append(
                        {
                            "id": fm.get("id", path.stem),
                            "status": status or "(vacio)",
                            "path": str(path.relative_to(root_dir)),
                        }
                    )

    if verified_files == 0:
        print(
            "WARN: 0 ficheros verificados. Casi seguro que los paths de "
            "task_config.yaml::levels no apuntan a backlog real, o el fallback "
            "heuristico esta activo. Revisa la configuracion.",
            file=sys.stderr,
        )

    if incomplete:
        print(
            f"ERROR: encontradas tareas/bugs asignadas a {args.version} sin completar:"
        )
        for t in incomplete:
            print(f"  - [{t['id']}] (estado: {t['status']}) -> {t['path']}")
        return 1

    print(
        f"OK: todas las anotaciones para {args.version} estan completadas "
        f"(verificados {verified_files} archivos)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
