"""Detección y clasificación de procesos de Adevv en marcha.

Identifica procesos vivos de bucle y gateway mediante inspección del sistema operativo
sin dependencias de librerías externas.
"""

import os
import re
import subprocess
import sys
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


def detectar_procesos_adevv() -> List[Dict[str, Any]]:
    """Detecta y clasifica procesos de Adevv vivos en el sistema operativo."""
    actual_pid = os.getpid()
    parent_pid = os.getppid() if hasattr(os, "getppid") else None

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
                import json
                try:
                    data = json.loads(stdout)
                    if isinstance(data, dict):
                        data = [data]
                    for item in data:
                        pid = item.get("ProcessId")
                        ppid = item.get("ParentProcessId")
                        cmd = item.get("CommandLine") or ""
                        if not pid or pid == actual_pid or (parent_pid and pid == parent_pid):
                            continue
                        tipo = _clasificar_linea_comandos(cmd)
                        if tipo:
                            # Intentar inferir carpeta de trabajo desde la línea de órdenes
                            cwd = None
                            match_cwd = re.search(r'--cwd\s+["\']?([^"\']+)["\']?', cmd)
                            if match_cwd:
                                cwd = match_cwd.group(1)
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
                for line in res.stdout.splitlines()[1:]:
                    parts = line.strip().split(None, 2)
                    if len(parts) >= 3:
                        pid_str, ppid_str, cmd = parts[0], parts[1], parts[2]
                        try:
                            pid = int(pid_str)
                            ppid = int(ppid_str)
                        except ValueError:
                            continue
                        if pid == actual_pid or (parent_pid and pid == parent_pid):
                            continue
                        tipo = _clasificar_linea_comandos(cmd)
                        if tipo:
                            procesos.append({"pid": pid, "tipo": tipo, "cwd": None, "cmd": cmd})
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
