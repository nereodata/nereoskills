#!/usr/bin/env python3
"""Verify all manifests declared in task_config.yaml::release.manifests
match project.version.

Usage:
    python check_manifests_versions.py [--dir .]

Exits 1 with a diff if any manifest disagrees with project.version.
Exits 0 otherwise.

Manifest schema (in task_config.yaml):
    release:
      manifests:
        - path: package.json
          type: json
          key: version
        - path: services/api/pyproject.toml
          type: toml
          key: project.version
        - path: task_config.yaml
          type: yaml
          key: project.version

Supports json / toml / yaml with dotted-path keys. The expected version
is `project.version` from task_config.yaml. By convention:
  - YAML manifests keep the leading "v" (e.g. "v0.3.0").
  - JSON / TOML manifests carry the bare semver (e.g. "0.3.0").
The script normalises both sides by stripping a leading "v" before
comparing, so either form is accepted in any manifest.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from pathlib import Path

# Force UTF-8 stdout to avoid cp1252 crashes on Windows.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ImportError:
        print(
            "ERROR: PyYAML no esta instalado. Ejecuta: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(2)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_toml(path: Path):
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            print(
                "ERROR: Se necesita tomllib (Python 3.11+) o tomli para leer TOML.",
                file=sys.stderr,
            )
            sys.exit(2)
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_dotted(data, dotted_key: str):
    cur = data
    for part in dotted_key.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def normalise_version(v) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    if s.startswith("v") or s.startswith("V"):
        s = s[1:]
    return s


def read_manifest_version(root: Path, manifest: dict) -> tuple[str, str | None, str | None]:
    """Return (path, raw_value_or_None, error_or_None)."""
    rel = manifest.get("path")
    mtype = (manifest.get("type") or "").lower()
    key = manifest.get("key") or "version"

    if not rel:
        return ("<missing path>", None, "manifest entry has no 'path'")

    full = root / rel
    if not full.exists():
        return (rel, None, f"file not found: {full}")

    try:
        if mtype == "json":
            data = load_json(full)
        elif mtype == "toml":
            data = load_toml(full)
        elif mtype in ("yaml", "yml"):
            data = load_yaml(full)
        else:
            return (rel, None, f"unsupported manifest type: {mtype!r}")
    except Exception as e:
        return (rel, None, f"failed to parse: {e}")

    raw = get_dotted(data, key)
    if raw is None:
        return (rel, None, f"key {key!r} not found")
    return (rel, str(raw), None)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify declared manifests match project.version."
    )
    parser.add_argument("--dir", default=".", help="Project root (default: cwd)")
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    cfg_path = root / "task_config.yaml"
    if not cfg_path.exists():
        print(f"ERROR: no se encontro {cfg_path}", file=sys.stderr)
        return 1

    cfg = load_yaml(cfg_path) or {}
    project_version = ((cfg.get("project") or {}).get("version") or "").strip()
    if not project_version:
        print("ERROR: project.version vacio en task_config.yaml", file=sys.stderr)
        return 1

    release = cfg.get("release") or {}
    manifests = release.get("manifests") or []
    if not manifests:
        print(
            "WARN: task_config.yaml::release.manifests no esta declarado. "
            "Esta version de la skill espera la lista declarada de manifiestos. "
            "Saltando validacion."
        )
        return 0

    expected_norm = normalise_version(project_version)
    mismatches: list[str] = []
    errors: list[str] = []
    ok: list[str] = []

    for m in manifests:
        rel, raw, err = read_manifest_version(root, m)
        if err is not None:
            errors.append(f"  - {rel}: {err}")
            continue
        actual_norm = normalise_version(raw)
        if actual_norm == expected_norm:
            ok.append(f"  - {rel}: {raw}")
        else:
            mismatches.append(f"  - {rel}: found {raw!r}, expected {project_version!r}")

    print(f"project.version = {project_version}")
    if ok:
        print(f"OK ({len(ok)}):")
        for line in ok:
            print(line)
    if errors:
        print(f"ERRORES de lectura ({len(errors)}):")
        for line in errors:
            print(line)
    if mismatches:
        print(f"DESALINEADOS ({len(mismatches)}):")
        for line in mismatches:
            print(line)

    if mismatches or errors:
        print(
            "\nEjecuta /start-version o sincroniza los manifiestos manualmente "
            "antes de continuar con /release."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
