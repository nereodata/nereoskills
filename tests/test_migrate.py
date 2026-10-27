"""Pruebas unitarias para el diagnóstico de migración de proyectos con submódulo a Adevv."""

import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adevv import cli
from adevv.migrate import (
    diagnosticar_migracion,
    ejecutar_migrar,
    formatear_diagnostico,
)
from tests import aislamiento_telegram


class TestMigrate(unittest.TestCase):
    """Verifica el diagnóstico de migración de solo lectura y sus criterios de aceptación."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_diagnostico_submodulo_y_adaptadores(self):
        """CA-M-1 / @CA-F04-01: Diagnóstico de proyecto con submódulo y adaptadores."""
        # 1. .gitmodules con entrada .agents
        gitmodules = self.root / ".gitmodules"
        gitmodules.write_text('[submodule ".agents"]\n\tpath = .agents\n\turl = https://example.com/repo.git\n', encoding="utf-8")

        # 2. Carpeta .agents
        agents_dir = self.root / ".agents"
        agents_dir.mkdir()
        (agents_dir / "dummy.txt").write_text("submodulo interno", encoding="utf-8")

        # 3. AGENTS.md con 6 líneas que citan .agents/
        agents_md = self.root / "AGENTS.md"
        lineas_agents = [
            "# Configuración de agentes",
            "Usa .agents/skills/orquestar para ejecutar.",
            "Revisa .agents/agents/artemisa.md para detalles.",
            "Línea sin cita.",
            "Ruta .agents/agents/hades.md requerida.",
            "Otra línea con .agents/skills/task-dev en el proyecto.",
            "Y .agents/skills/bug-fix para errores.",
            "Finalmente .agents/workflows/task-dev.md proxy.",
        ]
        agents_md.write_text("\n".join(lineas_agents), encoding="utf-8")

        # 4. orchestration.json con instructions a .agents/agents/hades.md
        orch_json = self.root / "orchestration.json"
        orch_json.write_text(
            '{\n  "hades": {\n    "instructions": ".agents/agents/hades.md"\n  }\n}\n',
            encoding="utf-8",
        )

        # 5. 300 citas a .agents/ en 120 archivos de docs/review/evidence/
        evidence_dir = self.root / "docs" / "review" / "evidence"
        evidence_dir.mkdir(parents=True)
        citas_creadas = 0
        for i in range(120):
            f = evidence_dir / f"ev_{i}.txt"
            num_citas = 3 if i < 60 else 2
            lineas = [f"Evidencia {i} linea {j}: cita a .agents/skills/algo" for j in range(num_citas)]
            f.write_text("\n".join(lineas), encoding="utf-8")
            citas_creadas += num_citas
        self.assertEqual(citas_creadas, 300)

        # Capturar hashes previos para verificar que ningún archivo cambia
        mtimes_before = {p: p.stat().st_mtime_ns for p in self.root.rglob("*") if p.is_file()}

        out = io.StringIO()
        err = io.StringIO()
        code = ejecutar_migrar(self.root, out, err)
        self.assertEqual(code, 0)
        salida = out.getvalue()

        # Verificar pendientes: .gitmodules, .agents, 6 líneas de AGENTS.md, orchestration.json
        self.assertIn(".gitmodules", salida)
        self.assertIn(".agents", salida)
        self.assertIn("AGENTS.md", salida)
        self.assertIn("orchestration.json", salida)

        # Verificar que termina con "9 pendientes."
        self.assertTrue(salida.strip().endswith("9 pendientes."))

        # Verificar que ningún archivo de evidence aparece como pendiente
        self.assertNotIn("docs/review/evidence", salida)

        # Verificar que ningún archivo del proyecto ha cambiado
        mtimes_after = {p: p.stat().st_mtime_ns for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(mtimes_before, mtimes_after)

    def test_deteccion_adaptadores_enlaces_y_copias_sin_recorrer(self):
        """CA-M-1 / @CA-F04-02: Detecta adaptadores, enlaces y copias sin recorrer enlaces."""
        # 1. scripts/orchestrate.py citando literalmente .agents/skills/orquestar/orquestar.py
        scripts_dir = self.root / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "orchestrate.py").write_text(
            '# Adaptador de orquestación\n'
            'MOTOR = ".agents/skills/orquestar/orquestar.py"\n',
            encoding="utf-8",
        )

        # 2. Carpeta real .agents/skills con archivo interno con citas
        target_skills = self.root / ".agents" / "skills"
        secreto_dir = target_skills / "secreto"
        secreto_dir.mkdir(parents=True)
        (secreto_dir / "SKILL.md").write_text(
            '---\nname: secreto\n---\nCita interna: .agents/skills/secreto\n',
            encoding="utf-8",
        )

        # Crear enlace o junction real .claude/skills hacia .agents/skills
        claude_dir = self.root / ".claude"
        claude_dir.mkdir()
        link_path = claude_dir / "skills"

        if os.name == "nt":
            subprocess.run(["cmd", "/c", "mklink", "/J", str(link_path), str(target_skills)], check=True, capture_output=True)
        else:
            os.symlink(target_skills, link_path)

        # 3. Carpeta de copia de Adevv: .orchestration/copia/skills/orquestar/SKILL.md
        copia_dir = self.root / ".orchestration" / "copia"
        copia_skill = copia_dir / "skills" / "orquestar"
        copia_skill.mkdir(parents=True)
        (copia_skill / "SKILL.md").write_text("---\nname: orquestar\n---\n", encoding="utf-8")

        out = io.StringIO()
        err = io.StringIO()
        code = ejecutar_migrar(self.root, out, err)
        self.assertEqual(code, 0)
        salida = out.getvalue()

        # Verificar que aparecen la línea de scripts/orchestrate.py, el enlace/junction y la copia
        self.assertIn("scripts/orchestrate.py", salida)
        self.assertIn(".agents/skills/orquestar/orquestar.py", salida)
        self.assertTrue(".claude/skills →" in salida and ".agents/skills" in salida)
        self.assertIn(".orchestration/copia", salida)

        # Verificar que el interior de .agents/skills no se recorre ni aparece en la salida
        self.assertNotIn("secreto", salida)
        self.assertNotIn(".orchestration/copia/skills/orquestar/SKILL.md", salida)

    def test_proyecto_migrado_con_citas_historicas(self):
        """CA-M-1 / @CA-F04-03: Proyecto migrado con citas históricas."""
        # Sin submódulo ni adaptadores
        code_reviews = self.root / "docs" / "review" / "code_reviews"
        code_reviews.mkdir(parents=True)
        (code_reviews / "rev1.md").write_text("Línea 1 sin cita\nLínea 2 cita .agents/skills/x\n", encoding="utf-8")
        (code_reviews / "rev2.md").write_text("Cita .agents/a\nOtra cita .agents/b\nFin\n", encoding="utf-8")

        out = io.StringIO()
        err = io.StringIO()
        code = ejecutar_migrar(self.root, out, err)
        self.assertEqual(code, 0)
        salida = out.getvalue().strip()
        self.assertTrue(salida.endswith("Sin pendientes (3 citas históricas)."))

    def test_migracion_repositorio_fuente_adevv_junction(self):
        """CA-M-2 / @CA-F04-04: El repositorio fuente de Adevv se puede migrar a sí mismo."""
        # Configurar como repo fuente de Adevv
        pyproject = self.root / "pyproject.toml"
        pyproject.write_text('[project]\nname = "adevv"\nversion = "0.1.0"\n', encoding="utf-8")
        (self.root / "adevv").mkdir()

        # README.md que documenta la migración (incluyendo citas a .agents/)
        readme = self.root / "README.md"
        readme.write_text(
            "# Adevv\n"
            "Migración: usa `git submodule deinit -f .agents`.\n"
            "Consulta .agents/ para la copia previa en versiones anteriores.\n",
            encoding="utf-8",
        )

        # Destino congelado simulado
        congelado_dir = self.root / "congelado_simulado"
        congelado_dir.mkdir()
        (congelado_dir / "archivo_congelado.txt").write_text("intacto", encoding="utf-8")

        agents_junction = self.root / ".agents"
        dest_str = str(congelado_dir)

        # 1. Con la junction
        subprocess.run(["cmd", "/c", "mklink", "/J", str(agents_junction), dest_str], check=True, capture_output=True)

        out1 = io.StringIO()
        err1 = io.StringIO()
        code1 = ejecutar_migrar(self.root, out1, err1)
        self.assertEqual(code1, 0)
        salida1 = out1.getvalue()
        self.assertIn(f".agents → {dest_str} (junction)", salida1)
        self.assertTrue(salida1.strip().endswith("1 pendientes."))

        # 2. Quitar junction sin seguirla (cmd /c rmdir en Windows)
        subprocess.run(["cmd", "/c", "rmdir", str(agents_junction)], check=True, capture_output=True)
        self.assertFalse(agents_junction.exists())

        # Verificar que el contenido de congelado sigue intacto
        self.assertTrue((congelado_dir / "archivo_congelado.txt").exists())

        # 3. Repetir migrar: debe dar Sin pendientes (README.md se ignora)
        out2 = io.StringIO()
        err2 = io.StringIO()
        code2 = ejecutar_migrar(self.root, out2, err2)
        self.assertEqual(code2, 0)
        salida2 = out2.getvalue().strip()
        self.assertEqual(salida2, "Sin pendientes")

    def test_salida_acotada_20_pendientes(self):
        """CA-M-1 / @CA-F04-05: Salida acotada con 35 pendientes."""
        # Crear archivo en uso con 35 líneas con cita a .agents/
        agents_file = self.root / "CLAUDE.md"
        lineas = [f"Línea {i:02d} con cita a .agents/skill_{i}" for i in range(1, 36)]
        agents_file.write_text("\n".join(lineas), encoding="utf-8")

        out = io.StringIO()
        err = io.StringIO()
        code = ejecutar_migrar(self.root, out, err)
        self.assertEqual(code, 0)
        salida = out.getvalue()

        # Verificar que se muestran exactamente las primeras 20 líneas y no las posteriores
        self.assertIn("Línea 20 con cita a .agents/skill_20", salida)
        self.assertNotIn("Línea 21 con cita a .agents/skill_21", salida)

        self.assertIn("… y 15 más (total 35).", salida)
        self.assertTrue(salida.strip().endswith("35 pendientes."))

    def test_elementos_locales_que_ocultan(self):
        """RF-F02-07 / RF-F04-02: Elementos locales que ocultan instalados se listan."""
        local_skill = self.root / ".claude" / "skills" / "orquestar"
        local_skill.mkdir(parents=True)
        (local_skill / "SKILL.md").write_text("local", encoding="utf-8")

        res = diagnosticar_migracion(self.root)
        rutas = [p.ruta for p in res.pendientes]
        self.assertIn(".claude/skills/orquestar", rutas)

    def test_cli_migrar_dispatch(self):
        """Verifica despacho de subcomando adevv migrar."""
        out = io.StringIO()
        err = io.StringIO()
        with patch("adevv.cli.Path.cwd", return_value=self.root):
            code = cli.main_cli(["migrar"], out=out, err=err)
            self.assertEqual(code, 0)
            self.assertIn("Sin pendientes", out.getvalue())


if __name__ == "__main__":
    unittest.main()
