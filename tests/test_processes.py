"""Pruebas unitarias para la detección y clasificación de procesos de Adevv."""

import os
import unittest
from unittest.mock import MagicMock, patch

from adevv.processes import (
    _clasificar_linea_comandos,
    detectar_procesos_adevv,
    formatear_proceso_ui,
    hay_bucles_en_marcha,
)


class TestProcesses(unittest.TestCase):
    """Verifica la clasificación de líneas de órdenes y detección de procesos."""

    def test_clasificar_linea_comandos(self):
        # Bucles anteriores a la migración
        self.assertEqual(
            _clasificar_linea_comandos("python .agents/skills/orquestar/orquestar.py"),
            "bucle",
        )
        self.assertEqual(
            _clasificar_linea_comandos("python skills/orquestar/orquestar.py"),
            "bucle",
        )
        self.assertEqual(
            _clasificar_linea_comandos('python "C:\\SW\\Afinn\\.agents\\skills\\orquestar\\orquestar.py"'),
            "bucle",
        )

        # Bucles vía adevv
        self.assertEqual(
            _clasificar_linea_comandos("adevv orquestar --fondo --harness claude"),
            "bucle",
        )
        self.assertEqual(
            _clasificar_linea_comandos("adevv orquestar"),
            "bucle",
        )

        # Subcomandos de orquestar que NO son bucles
        self.assertEqual(
            _clasificar_linea_comandos("adevv orquestar --estado"),
            "otro",
        )
        self.assertEqual(
            _clasificar_linea_comandos("python skills/orquestar/orquestar.py --estado"),
            "otro",
        )
        self.assertEqual(
            _clasificar_linea_comandos('adevv orquestar --verificar "python -m unittest"'),
            "otro",
        )
        self.assertEqual(
            _clasificar_linea_comandos("adevv orquestar --agente hades --prompt-file cmd.txt"),
            "otro",
        )
        self.assertEqual(
            _clasificar_linea_comandos("adevv orquestar --parar"),
            "otro",
        )
        self.assertEqual(
            _clasificar_linea_comandos("adevv orquestar --aviso-prueba"),
            "otro",
        )

        # Gateways
        self.assertEqual(
            _clasificar_linea_comandos("python skills/telegram_gateway/gateway.py"),
            "gateway",
        )
        self.assertEqual(
            _clasificar_linea_comandos("python .agents/skills/telegram_gateway/gateway.py"),
            "gateway",
        )
        self.assertEqual(
            _clasificar_linea_comandos("adevv telegram"),
            "gateway",
        )

        # Otros comandos de adevv
        self.assertEqual(
            _clasificar_linea_comandos("adevv --version"),
            "otro",
        )
        self.assertEqual(
            _clasificar_linea_comandos("adevv instalar"),
            "otro",
        )

        # Procesos ajenos
        self.assertIsNone(_clasificar_linea_comandos("python manage.py runserver"))
        self.assertIsNone(_clasificar_linea_comandos("git status"))
        self.assertIsNone(_clasificar_linea_comandos(""))

    def test_formatear_proceso_ui(self):
        proc_con_cwd = {
            "pid": 1234,
            "tipo": "bucle",
            "cwd": "C:\\SW\\Afinn",
            "cmd": "adevv orquestar",
        }
        self.assertEqual(
            formatear_proceso_ui(proc_con_cwd),
            "bucle en C:\\SW\\Afinn",
        )

        proc_sin_cwd = {
            "pid": 5678,
            "tipo": "gateway",
            "cwd": None,
            "cmd": "adevv telegram",
        }
        self.assertEqual(
            formatear_proceso_ui(proc_sin_cwd),
            "gateway (proceso 5678)",
        )

    def test_filtro_proceso_actual_y_padre(self):
        curr_pid = os.getpid()
        parent_pid = os.getppid() if hasattr(os, "getppid") else 999999
        bucle_pid = 44444
        gateway_pid = 55555
        notepad_pid = 66666

        simulated_processes = [
            {"ProcessId": curr_pid, "ParentProcessId": parent_pid, "CommandLine": "python -m unittest tests/test_processes.py"},
            {"ProcessId": parent_pid, "ParentProcessId": 1, "CommandLine": "powershell.exe"},
            {"ProcessId": bucle_pid, "ParentProcessId": 1, "CommandLine": 'python "C:\\SW\\Afinn\\.agents\\skills\\orquestar\\orquestar.py"'},
            {"ProcessId": gateway_pid, "ParentProcessId": 1, "CommandLine": 'adevv telegram --cwd "C:\\SW\\Adevv"'},
            {"ProcessId": notepad_pid, "ParentProcessId": 1, "CommandLine": "notepad.exe"},
        ]

        import json
        stdout_json = json.dumps(simulated_processes)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=stdout_json.encode("utf-8"), stderr=b"")
            procesos = detectar_procesos_adevv()

            pids_detectados = [p["pid"] for p in procesos]
            self.assertNotIn(curr_pid, pids_detectados)
            self.assertNotIn(parent_pid, pids_detectados)
            self.assertNotIn(notepad_pid, pids_detectados)
            self.assertIn(bucle_pid, pids_detectados)
            self.assertIn(gateway_pid, pids_detectados)

            proc_bucle = next(p for p in procesos if p["pid"] == bucle_pid)
            self.assertEqual(proc_bucle["tipo"], "bucle")

            proc_gw = next(p for p in procesos if p["pid"] == gateway_pid)
            self.assertEqual(proc_gw["tipo"], "gateway")
            self.assertEqual(proc_gw["cwd"], "C:\\SW\\Adevv")


if __name__ == "__main__":
    unittest.main()
