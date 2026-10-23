"""Detección y clasificación de procesos de Adevv en marcha.

Identifica procesos vivos de bucle y gateway mediante inspección del sistema operativo
sin dependencias de librerías externas.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _clasificar_linea_comandos(cmdline: str) -> Optional[str]:
    """Clasifica un proceso según su línea de órdenes: bucle, gateway u otro."""
    if not cmdline:
        return None

    cmd_lower = cmdline.lower()
    es_adevv = "adevv" in cmd_lower or "orquestar.py" in cmd_lower or "gateway.py" in cmd_lower
    if not es_adevv:
        return None

    if "gateway.py" in cmd_lower or "adevv telegram" in cmd_lower:
        return "gateway"

    if "orquestar.py" in cmd_lower or "adevv orquestar" in cmd_lower:
        subcomandos_no_bucle = ["--estado", "--verificar", "--agente", "--parar", "--aviso-prueba"]
        for sub in subcomandos_no_bucle:
            if sub in cmd_lower:
                return "otro"
        return "bucle"

    return "otro"


def _inferir_cwd_proceso(pid: int, cmd: str) -> Optional[str]:
    """Infiere la carpeta de trabajo de un proceso desde runtime JSON o su línea de órdenes."""
    adevv_home_str = os.environ.get("ADEVV_HOME")
    home_dir = Path(adevv_home_str) if adevv_home_str else (Path.home() / ".adevv")
    runtime_file = home_dir / "runtime" / f"{pid}.json"
    if runtime_file.exists():
        try:
            info = json.loads(runtime_file.read_text(encoding="utf-8"))
            if isinstance(info, dict) and info.get("cwd"):
                return str(info["cwd"])
        except Exception:
            pass

    match_root = re.search(r'--root\s+["\']?([^"\']+)["\']?', cmd)
    if match_root:
        return match_root.group(1).rstrip("/\\")

    match_cwd = re.search(r'--cwd\s+["\']?([^"\']+)["\']?', cmd)
    if match_cwd:
        return match_cwd.group(1).rstrip("/\\")

    match_script_win = re.search(r'["\']?([A-Za-z]:\\[^"\'\r\n]+?)\\(?:\.agents[\\/])?(?:skills|workflows)[\\/]', cmd, re.IGNORECASE)
    if match_script_win:
        return match_script_win.group(1).rstrip("/\\")

    match_script_posix = re.search(r'["\']?(/[^"\'\r\n]+?)/(?:\.agents/)?(?:skills|workflows)/', cmd)
    if match_script_posix:
        return match_script_posix.group(1).rstrip("/\\")

    return None


def detectar_procesos_adevv() -> List[Dict[str, Any]]:
    """Detecta y clasifica procesos de Adevv vivos en el sistema operativo excluyendo ancestros."""
    actual_pid = os.getpid()

    procesos: List[Dict[str, Any]] = []

    if sys.platform == "win32":
        ps_script = (
            "Get-CimInstance Win32_Process | "
            "Select-Object ProcessId, ParentProcessId, CommandLine | "
            "ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                timeout=10,
                check=False,
            )
            stdout = res.stdout.decode("utf-8", errors="replace") if res.stdout else ""
            if res.returncode == 0 and stdout.strip():
                try:
                    data = json.loads(stdout)
                    if isinstance(data, dict):
                        data = [data]

                    parent_map: Dict[int, int] = {}
                    for item in data:
                        p_id = item.get("ProcessId")
                        pp_id = item.get("ParentProcessId")
                        if p_id is not None and pp_id is not None:
                            parent_map[p_id] = pp_id

                    ancestor_pids = set()
                    curr_ancestor = actual_pid
                    while curr_ancestor in parent_map and parent_map[curr_ancestor]:
                        p_next = parent_map[curr_ancestor]
                        if p_next in ancestor_pids or p_next == 0:
                            break
                        ancestor_pids.add(p_next)
                        curr_ancestor = p_next

                    for item in data:
                        pid = item.get("ProcessId")
                        cmd = item.get("CommandLine") or ""
                        if not pid or pid == actual_pid or pid in ancestor_pids:
                            continue
                        tipo = _clasificar_linea_comandos(cmd)
                        if tipo:
                            cwd = _inferir_cwd_proceso(pid, cmd)
                            procesos.append({"pid": pid, "tipo": tipo, "cwd": cwd, "cmd": cmd})
                except Exception:
                    pass
        except Exception:
            pass
    else:
        try:
            res = subprocess.run(
                ["ps", "-eo", "pid,ppid,args"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
                check=False,
            )
            if res.returncode == 0:
                lines = res.stdout.splitlines()[1:]
                parent_map_posix: Dict[int, int] = {}
                entries = []
                for line in lines:
                    parts = line.strip().split(None, 2)
                    if len(parts) >= 3:
                        try:
                            p_id = int(parts[0])
                            pp_id = int(parts[1])
                            cmd = parts[2]
                            parent_map_posix[p_id] = pp_id
                            entries.append((p_id, cmd))
                        except ValueError:
                            continue

                ancestor_pids_posix = set()
                curr_ancestor = actual_pid
                while curr_ancestor in parent_map_posix and parent_map_posix[curr_ancestor]:
                    p_next = parent_map_posix[curr_ancestor]
                    if p_next in ancestor_pids_posix or p_next <= 1:
                        break
                    ancestor_pids_posix.add(p_next)
                    curr_ancestor = p_next

                for pid, cmd in entries:
                    if pid == actual_pid or pid in ancestor_pids_posix:
                        continue
                    tipo = _clasificar_linea_comandos(cmd)
                    if tipo:
                        cwd = _inferir_cwd_proceso(pid, cmd)
                        procesos.append({"pid": pid, "tipo": tipo, "cwd": cwd, "cmd": cmd})
        except Exception:
            pass

    return procesos


def hay_bucles_en_marcha() -> List[Dict[str, Any]]:
    """Devuelve la lista de procesos activos clasificados como bucle."""
    return [p for p in detectar_procesos_adevv() if p.get("tipo") == "bucle"]


def formatear_proceso_ui(proc: Dict[str, Any]) -> str:
    """Formatea la representación textual de un proceso para mensajes de usuario."""
    tipo = proc.get("tipo", "proceso")
    cwd = proc.get("cwd")
    pid = proc.get("pid")
    if cwd:
        return f"{tipo} en {cwd}"
    return f"{tipo} (proceso {pid})"
