"""Parser y emisor ligero de YAML con fallback a stdlib si PyYAML no esta instalado."""

import re
from pathlib import Path
from typing import Any, Dict, List, Union


def _parse_scalar(val_str: str) -> Any:
    """Convierte un escalar de texto en su tipo Python correspondiente."""
    s = val_str.strip()
    if not s:
        return ""
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if s.lower() in ("null", "none", "~"):
        return None
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        return s[1:-1]
    if s.startswith("'") and s.endswith("'") and len(s) >= 2:
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        items = [x.strip() for x in s[1:-1].split(",") if x.strip()]
        return [_parse_scalar(x) for x in items]
    try:
        if "." in s or "e" in s.lower():
            return float(s)
        return int(s)
    except ValueError:
        return s


def _parse_lines(lines: List[str], start_idx: int = 0, base_indent: int = 0) -> tuple[Any, int]:
    """Analiza recursivamente lineas con indentacion para formar dicts o listas."""
    idx = start_idx
    total = len(lines)
    dict_res: Dict[str, Any] = {}
    list_res: List[Any] = []
    is_list = False
    is_dict = False

    while idx < total:
        raw_line = lines[idx]
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            idx += 1
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent < base_indent:
            break

        if stripped.startswith("- "):
            is_list = True
            item_text = stripped[2:].strip()
            if not item_text:
                sub_val, next_idx = _parse_lines(lines, idx + 1, indent + 2)
                list_res.append(sub_val)
                idx = next_idx
                continue
            if ":" in item_text:
                lines_copy = list(lines)
                indent_spaces = " " * (indent + 2)
                lines_copy[idx] = indent_spaces + item_text
                sub_val, next_idx = _parse_lines(lines_copy, idx, indent + 2)
                list_res.append(sub_val)
                idx = next_idx
                continue
            list_res.append(_parse_scalar(item_text))
            idx += 1
            continue

        if ":" in stripped:
            is_dict = True
            key_part, val_part = stripped.split(":", 1)
            key = key_part.strip().strip("'\"")
            val_part = val_part.strip()

            if not val_part:
                sub_val, next_idx = _parse_lines(lines, idx + 1, indent + 2)
                dict_res[key] = sub_val
                idx = next_idx
                continue
            dict_res[key] = _parse_scalar(val_part)
            idx += 1
            continue

        idx += 1

    if is_list and not is_dict:
        return list_res, idx
    return dict_res, idx


def load_yaml(source: Union[str, Path]) -> Any:
    """Carga YAML desde un archivo o cadena de texto, usando PyYAML si esta presente."""
    try:
        import yaml
        if isinstance(source, Path):
            with open(source, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return yaml.safe_load(str(source))
    except ImportError:
        pass

    if isinstance(source, Path):
        content = source.read_text(encoding="utf-8")
    else:
        content = str(source)

    lines = content.splitlines()
    res, _ = _parse_lines(lines, 0, 0)
    return res


def dump_yaml(data: Any, path: Path | None = None) -> str:
    """Serializa un objeto Python a formato YAML minimalista."""
    try:
        import yaml
        dumped = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        if path:
            path.write_text(dumped, encoding="utf-8")
        return dumped
    except ImportError:
        pass

    def _serialize(obj: Any, indent: int = 0) -> List[str]:
        prefix = " " * indent
        out: List[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    out.append(f"{prefix}{k}:")
                    out.extend(_serialize(v, indent + 2))
                else:
                    out.append(f"{prefix}{k}: {_scalar_to_str(v)}")
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    keys = list(item.keys())
                    if not keys:
                        out.append(f"{prefix}- {{}}")
                    else:
                        first_k = keys[0]
                        first_v = item[first_k]
                        if isinstance(first_v, (dict, list)):
                            out.append(f"{prefix}- {first_k}:")
                            out.extend(_serialize(first_v, indent + 4))
                        else:
                            out.append(f"{prefix}- {first_k}: {_scalar_to_str(first_v)}")
                        for k in keys[1:]:
                            v = item[k]
                            if isinstance(v, (dict, list)):
                                out.append(f"{prefix}  {k}:")
                                out.extend(_serialize(v, indent + 4))
                            else:
                                out.append(f"{prefix}  {k}: {_scalar_to_str(v)}")
                elif isinstance(item, list):
                    out.append(f"{prefix}-")
                    out.extend(_serialize(item, indent + 2))
                else:
                    out.append(f"{prefix}- {_scalar_to_str(item)}")
        else:
            out.append(f"{prefix}{_scalar_to_str(obj)}")
        return out

    def _scalar_to_str(val: Any) -> str:
        if val is None:
            return "null"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        s = str(val)
        if any(c in s for c in ":#[]{},") or s == "":
            return f'"{s}"'
        return s

    lines = _serialize(data, 0)
    result = "\n".join(lines) + "\n"
    if path:
        path.write_text(result, encoding="utf-8")
    return result
