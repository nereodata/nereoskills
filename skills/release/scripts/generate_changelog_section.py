#!/usr/bin/env python3
"""Generate a CHANGELOG.md section in Keep a Changelog format from
backlog frontmatter.

Usage:
    python generate_changelog_section.py --version vX.Y.Z [--output -]
                                          [--dir .] [--lang es|en]

Reads task_config.yaml in the consumer project to discover backlog
paths and ID prefixes (one or more `levels.components` entries plus
`levels.master`).

Filters items by frontmatter `version` matching --version (also accepts
loose match like "v0.3" -> "v0.3.0").

Filters items by `status: completed` (cancelled / superseded / rejected
are excluded).

Groups by type (T- -> Added, B- -> Fixed) and by module (extracted from
the ID prefix segment, e.g. T-ABC-API-NNNN -> module "API"). The module
is the segment after the project / component prefix and before the
trailing numeric run.

Emits markdown sub-sections sorted by ID.

Exits 0 on success, 1 on validation errors (missing config, no items
found, schema mismatch).

Always writes UTF-8 to stdout (forces TextIOWrapper on stdout.buffer)
to avoid cp1252 crashes on Windows.

The skill does NOT modify CHANGELOG.md automatically: the generated
section is meant to be reviewed by a human and pasted in. The
"Highlights" / executive summary remains a human task.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

# Force UTF-8 stdout to avoid cp1252 crashes on Windows.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_globs(cfg: dict) -> list[str]:
    """Return a list of glob patterns to search backlog markdown items."""
    globs: list[str] = []
    levels = cfg.get("levels") or {}

    master = levels.get("master") or {}
    if master:
        base = master.get("path", "") or ""
        folders = master.get("folders") or {}
        if folders.get("tasks"):
            globs.append(base + folders["tasks"] + "*.md")
        if folders.get("bugs"):
            globs.append(base + folders["bugs"] + "*.md")

    for comp in levels.get("components") or []:
        base = (comp.get("path", "") or "").replace("{name}", "*")
        folders = comp.get("folders") or {}
        if folders.get("tasks"):
            globs.append(base + folders["tasks"] + "*.md")
        if folders.get("bugs"):
            globs.append(base + folders["bugs"] + "*.md")

    return list(dict.fromkeys(globs))  # dedupe, preserve order


def normalise_version(v: str) -> str:
    s = (v or "").strip()
    if s.startswith("v") or s.startswith("V"):
        s = s[1:]
    return s


def loose_version_match(item_v: str, target_v: str) -> bool:
    """Accept exact match plus a loose match where target is a prefix
    (e.g. target 'v0.3' matches item 'v0.3.0')."""
    a = normalise_version(item_v)
    b = normalise_version(target_v)
    if not a or not b:
        return False
    if a == b:
        return True
    # loose: 0.3 -> 0.3.0
    if "." in b and b.count(".") < 2:
        return a.startswith(b + ".")
    return False


def get_task_types(cfg: dict) -> dict[str, str]:
    """Return mapping of section_label -> letter prefix.

    Default: feature=T (Added), bug=B (Fixed). Configurable through
    task_config.yaml::task_types: { feature: T, bug: B }.
    """
    tt = cfg.get("task_types") or {}
    feature = (tt.get("feature") or "T").upper()
    bug = (tt.get("bug") or "B").upper()
    return {"feature": feature, "bug": bug}


MODULE_RE = re.compile(r"^[A-Z]+-(?:[A-Z0-9]+-)*?([A-Z0-9]+)-\d+$")


def extract_module(item_id: str) -> str:
    """Pull the module segment out of an ID like T-ABC-API-0017 -> API.

    The module is the last alphanumeric segment before the trailing
    numeric run. If we cannot infer one (e.g. master-level T-ABC-0001),
    return "General".
    """
    m = MODULE_RE.match(item_id)
    if not m:
        return "General"
    # Items at master level (no module) end up with the project prefix
    # as the captured segment; treat that as "General".
    parts = item_id.split("-")
    if len(parts) <= 3:
        return "General"
    return m.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", required=True, help="Target version (e.g. v0.3.0)")
    parser.add_argument("--dir", default=".", help="Project root (default: cwd)")
    parser.add_argument("--output", default="-", help="Output file or '-' for stdout")
    parser.add_argument(
        "--lang",
        default="es",
        choices=("es", "en"),
        help="Section labels language (default: es)",
    )
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    cfg_path = root / "task_config.yaml"
    if not cfg_path.exists():
        print(f"ERROR: no se encontro {cfg_path}", file=sys.stderr)
        return 1

    cfg = load_yaml(cfg_path)
    if cfg is None:
        print(
            "ERROR: PyYAML no esta instalado o task_config.yaml es ilegible. "
            "Ejecuta: pip install pyyaml",
            file=sys.stderr,
        )
        return 1

    types = get_task_types(cfg)
    feature_prefix = types["feature"]
    bug_prefix = types["bug"]

    globs = collect_globs(cfg)
    if not globs:
        print(
            "ERROR: no se pudieron derivar paths de backlog desde task_config.yaml",
            file=sys.stderr,
        )
        return 1

    # type letter -> module -> list[(id, title)]
    buckets: dict[str, dict[str, list[tuple[str, str]]]] = {
        feature_prefix: {},
        bug_prefix: {},
    }
    seen = 0
    matched = 0

    valid_prefix_re = re.compile(rf"^({re.escape(feature_prefix)}|{re.escape(bug_prefix)})-")

    for pat in globs:
        for path in root.glob(pat):
            if not path.is_file():
                continue
            if not valid_prefix_re.match(path.name):
                continue
            seen += 1
            try:
                with open(path, "r", encoding="utf-8") as f:
                    head = f.read(8192)
            except Exception:
                continue
            fm = parse_frontmatter(head)
            if not loose_version_match(fm.get("version", ""), args.version):
                continue
            status = (fm.get("status") or "").lower()
            if status != "completed":
                continue

            item_id = fm.get("id") or path.stem
            title = fm.get("title") or fm.get("name") or path.stem
            letter = item_id.split("-", 1)[0].upper()
            if letter not in buckets:
                continue
            module = extract_module(item_id)
            buckets[letter].setdefault(module, []).append((item_id, title))
            matched += 1

    if matched == 0:
        print(
            f"ERROR: no se encontraron items con version={args.version} "
            f"y status=completed (revisados {seen} ficheros)",
            file=sys.stderr,
        )
        return 1

    labels = {
        "es": {"added": "Añadido", "fixed": "Corregido"},
        "en": {"added": "Added", "fixed": "Fixed"},
    }[args.lang]

    today = __import__("datetime").date.today().isoformat()
    version_clean = normalise_version(args.version)

    lines: list[str] = []
    lines.append(f"## [{version_clean}] - {today}")
    lines.append("")

    def emit_group(letter: str, header: str) -> None:
        modules = buckets.get(letter) or {}
        if not modules:
            return
        lines.append(f"### {header}")
        lines.append("")
        for module in sorted(modules.keys()):
            items = sorted(modules[module], key=lambda x: x[0])
            lines.append(f"#### {module}")
            for item_id, title in items:
                lines.append(f"- **{item_id}** — {title}")
            lines.append("")

    emit_group(feature_prefix, labels["added"])
    emit_group(bug_prefix, labels["fixed"])

    output = "\n".join(lines).rstrip() + "\n"
    if args.output == "-":
        sys.stdout.write(output)
    else:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"OK: seccion escrita en {args.output} ({matched} items)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
