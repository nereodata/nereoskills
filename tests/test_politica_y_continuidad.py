"""Pruebas directas de T-ADV-0041: política activa por defecto, contexto portable y revisión proporcional."""

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import chdir, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from adevv import contexto_ejecucion, revisiones
from tests import aislamiento_telegram  # noqa: F401
from tests.test_orquestar import motor


class PoliticaYContinuidadTests(unittest.TestCase):
    """Ejercita política, relevo entre sesiones/modelos y revisión proporcional sobre Git real."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        self.escribir(
            "task_config.yaml",
            (
                'project:\n  name: Demo\n  prefix: DEMO\n  version: "v1.2.0"\n'
                "levels:\n  master:\n    id_prefix: DEMO\n    path: docs/plan/\n"
                "    folders:\n      tasks: tasks/\n      bugs: bugs/\n"
            ),
        )
        for doc in ("requirements", "req_analysis", "platform_plan", "platform_review", "work_plan"):
            self.escribir(f"docs/requirements/{doc}.md", "APROBADO\n")
        self.escribir(
            "docs/plan/tasks/T-DEMO-0001.md",
            (
                '---\nid: T-DEMO-0001\ntitle: Demo\nversion: "v1.2.0"\n'
                "status: in_progress\ndepende_de: []\n---\n# Demo\n"
            ),
        )
        self.git("add", ".")
        self.git("commit", "-qm", "chore: init")
        self.git("checkout", "-qb", "release/v1.2")

    def git(self, *args):
        env = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "NUL" if sys.platform == "win32" else "/dev/null"}
        import os

        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            env={**os.environ, **env},
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout.strip()

    def escribir(self, rel, texto):
        ruta = self.root / rel
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8")
        return ruta

    def test_politica_base_por_defecto_local_y_rechazo_de_config_invalida(self):
        base = contexto_ejecucion.cargar_politica(self.root)
        self.assertTrue(base["activated"])
        self.assertEqual(base["policy"]["path"], "<builtin:default>")

        self.escribir("PROJECT.md", "# Política local\nAutonomía total.\n")
        local = contexto_ejecucion.cargar_politica(self.root)
        self.assertTrue(local["policy"]["path"].endswith("PROJECT.md"))
        self.assertIn("Autonomía total", local["policy"]["text"])

        for cfg_invalida in (
            {"execution": {"policy": "../fuera.md"}},
            {"execution": {"policy": "no-existe.md"}},
            {"execution": {"limits": {"inventado": 2}}},
            {"execution": {"enabled": "si"}},
        ):
            self.escribir("orchestration.json", json.dumps(cfg_invalida))
            with self.assertRaises(ValueError):
                contexto_ejecucion.cargar_politica(self.root)
            estado = motor.estado(self.root, "docs/requirements")
            self.assertEqual(estado[0], "PARAR")
            self.assertIn("Política de ejecución inválida", estado[1])

    def test_checkpoint_cli_y_presupuestos_separan_cuota_de_progreso(self):
        self.escribir("PROJECT.md", "# Política Demo\n")
        salida = io.StringIO()
        salida.reconfigure = lambda **kw: None
        with (
            chdir(self.root),
            patch.object(
                sys,
                "argv",
                [
                    "orquestar",
                    "--checkpoint",
                    "T-DEMO-0001",
                    "--resumen",
                    "Módulo base creado",
                    "--siguiente",
                    "Conectar selector y probar",
                    "--decision",
                    "Usar unittest directo",
                ],
            ),
            redirect_stdout(salida),
        ):
            self.assertEqual(motor.main(), 0)
        self.assertIn("checkpoint guardado para T-DEMO-0001", salida.getvalue())

        prompt = motor.construir_prompt_paso(self.root, "task-dev", "T-DEMO-0001")
        self.assertIn("PROJECT.md", prompt)
        self.assertIn("Módulo base creado", prompt)
        self.assertIn("Conectar selector y probar", prompt)

        for i in range(5):
            r = contexto_ejecucion.registrar_intento(
                self.root, "T-DEMO-0001", progreso=False, tipo="cuota", invocacion=f"q-{i}"
            )
            self.assertEqual(r["action"], "continuar")
            self.assertEqual(r["counters"]["sin_progreso"], 0)

        r1 = contexto_ejecucion.registrar_intento(self.root, "T-DEMO-0001", progreso=False, invocacion="w-1")
        self.assertEqual((r1["action"], r1["counters"]["sin_progreso"]), ("continuar", 1))
        self.assertIn("sin progreso", r1["reason"])

        r2 = contexto_ejecucion.registrar_intento(self.root, "T-DEMO-0001", progreso=True, invocacion="w-2")
        self.assertEqual((r2["action"], r2["counters"]["sin_progreso"]), ("continuar", 0))

        for i in range(3):
            ultimo = contexto_ejecucion.registrar_intento(
                self.root, "T-DEMO-0001", progreso=False, invocacion=f"np-{i}"
            )
        self.assertEqual(ultimo["action"], "pausa_tecnica")

    def test_revision_proporcional_admite_na_fuera_de_superficies_criticas_y_rechaza_en_criticas(self):
        self.escribir("app/calculadora.py", "def suma(a, b):\n    return a + b\n")
        self.escribir(
            "docs/plan/tasks/T-DEMO-0001.md",
            ('---\nid: T-DEMO-0001\ntitle: Demo\nversion: "v1.2.0"\nstatus: completed\ndepende_de: []\n---\n# Demo\n'),
        )
        self.escribir(
            "docs/review/code_reviews/T-DEMO-0001-code-review.md",
            ("**Veredicto:** N/A\nMotivo: cambio acotado fuera de superficies críticas; verificado con unittest.\n"),
        )
        self.git("add", ".")
        self.git("commit", "-qm", "feat: calculadora acotada")
        self.assertEqual(revisiones.motivo_revision(self.root, "T-DEMO-0001"), "")

        self.escribir("adevv/release_tools.py", "# cambio en superficie crítica de publicación\n")
        self.escribir(
            "docs/plan/tasks/T-DEMO-0002.md",
            (
                '---\nid: T-DEMO-0002\ntitle: Critica\nversion: "v1.2.0"\n'
                "status: completed\ndepende_de: []\n---\n# Critica\n"
            ),
        )
        self.escribir(
            "docs/review/code_reviews/T-DEMO-0002-code-review.md",
            ("**Veredicto:** N/A\nMotivo: fuera de superficies críticas.\n"),
        )
        self.git("add", ".")
        self.git("commit", "-qm", "feat: toca release_tools")
        self.assertIn("superficies críticas", revisiones.motivo_revision(self.root, "T-DEMO-0002"))

    def test_modularidad_y_lint_de_modulos_nuevos(self):
        raiz_repo = Path(__file__).resolve().parents[1]
        for rel in ("adevv/contexto_ejecucion.py", "adevv/decision_item.py"):
            lineas = (raiz_repo / rel).read_text(encoding="utf-8").splitlines()
            self.assertLessEqual(len(lineas), 350, f"{rel} supera el tope de modularidad (350 líneas)")


if __name__ == "__main__":
    unittest.main()
