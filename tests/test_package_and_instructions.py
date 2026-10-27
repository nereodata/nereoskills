"""Pruebas de empaquetado por lista blanca e inspección de contenido distribuible."""

import tempfile
import unittest
import zipfile
from pathlib import Path

from adevv._build import (
    ForbiddenContentError,
    build_wheel,
    inspect_distribution_cleanliness,
)
from tests import aislamiento_telegram


class TestPackageAndInstructions(unittest.TestCase):
    """Verifica que el paquete distribuible contenga exclusivamente la lista blanca."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Estructura distribuible base
        (self.root / "adevv").mkdir()
        (self.root / "adevv" / "__init__.py").write_text("__version__ = '0.1.0'\n", encoding="utf-8")
        (self.root / "adevv" / "_build.py").write_text("# build\n", encoding="utf-8")

        (self.root / "skills" / "orquestar").mkdir(parents=True)
        (self.root / "skills" / "orquestar" / "SKILL.md").write_text("---\nname: orquestar\n---\n", encoding="utf-8")

        (self.root / "agents").mkdir()
        (self.root / "agents" / "artemisa.md").write_text("---\nname: artemisa\n---\n", encoding="utf-8")

        (self.root / "workflows").mkdir()
        (self.root / "workflows" / "wf.md").write_text("# workflow\n", encoding="utf-8")

        (self.root / "pyproject.toml").write_text(
            '[project]\nname = "adevv"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )

        # Archivos y carpetas internas que NO deben entrar en el paquete
        (self.root / ".agents").mkdir()
        (self.root / ".agents" / "internal.md").write_text("# junction data\n", encoding="utf-8")

        (self.root / "docs" / "plan").mkdir(parents=True)
        (self.root / "docs" / "plan" / "task.md").write_text("# internal plan\n", encoding="utf-8")

        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_dummy.py").write_text("# test\n", encoding="utf-8")

        (self.root / "task_config.yaml").write_text("project:\n  name: Adevv\n", encoding="utf-8")
        (self.root / "orchestration.json").write_text("{}", encoding="utf-8")
        (self.root / "orquestar.log").write_text("log data\n", encoding="utf-8")
        (self.root / "orquestar.pid").write_text("12345\n", encoding="utf-8")
        (self.root / "orquestar_metricas.jsonl").write_text("{}\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ca_f05_01_package_contains_only_whitelisted_files(self):
        """CA-M-1: El paquete distribuible solo contiene la lista blanca y pasa la inspección."""
        dist_dir = self.root / "dist"
        dist_dir.mkdir()

        wheel_res = build_wheel(str(dist_dir), config_settings={"root": str(self.root)})
        wheel_path = Path(wheel_res)
        if not wheel_path.is_absolute():
            wheel_path = dist_dir / wheel_path
        self.assertTrue(wheel_path.exists())

        with zipfile.ZipFile(wheel_path, "r") as zf:
            names = set(zf.namelist())

        # Verificar presencia obligatoria de los componentes de la lista blanca
        self.assertIn("adevv/__init__.py", names)
        self.assertIn("adevv/_build.py", names)
        self.assertIn("skills/orquestar/SKILL.md", names)
        self.assertIn("agents/artemisa.md", names)
        self.assertIn("workflows/wf.md", names)

        # Verificar que no hay archivos internos ni prohibidos
        allowed_prefixes = ("adevv/", "skills/", "agents/", "workflows/", "adevv-0.1.0.dist-info/")
        for name in names:
            self.assertTrue(
                name.startswith(allowed_prefixes),
                f"El archivo {name} no pertenece a los prefijos permitidos de la lista blanca",
            )
            self.assertFalse(name.startswith(".agents/"), f".agents/ detectado en el paquete: {name}")
            self.assertFalse(name.startswith("docs/"), f"docs/ detectado en el paquete: {name}")
            self.assertFalse(name.startswith("tests/"), f"tests/ detectado en el paquete: {name}")
            self.assertFalse(name == "task_config.yaml", f"task_config.yaml detectado en el paquete: {name}")
            self.assertFalse(name == "orchestration.json", f"orchestration.json detectado en el paquete: {name}")
            self.assertFalse(name.endswith(".log"), f"Archivo .log detectado en el paquete: {name}")
            self.assertFalse(name.endswith(".pid"), f"Archivo .pid detectado en el paquete: {name}")
            self.assertFalse(name.endswith(".jsonl"), f"Archivo .jsonl detectado en el paquete: {name}")
            self.assertNotIn("__pycache__", name, f"__pycache__ detectado en el paquete: {name}")
            self.assertFalse(name.endswith(".pyc"), f"Archivo .pyc detectado en el paquete: {name}")

        # Comprobar que la prueba de contenido del paquete pasa en limpio
        inspect_distribution_cleanliness(self.root)

    def test_ca_f05_02_detects_forbidden_content_and_fails_naming_file(self):
        """CA-M-2: La inspección falla nombrando el archivo infractor cuando hay contenido prohibido."""
        forbidden_rel = "skills/orquestar/__pycache__/orquestar.cpython-312.pyc"
        forbidden_file = self.root / forbidden_rel
        forbidden_file.parent.mkdir(parents=True, exist_ok=True)
        forbidden_file.write_bytes(b"\x00\x01\x02")

        with self.assertRaises(ForbiddenContentError) as ctx:
            inspect_distribution_cleanliness(self.root)

        msg = str(ctx.exception).replace("\\", "/")
        self.assertIn("orquestar.cpython-312.pyc", msg)
        self.assertIn("skills/orquestar/__pycache__", msg)

    def test_ca_f05_02_real_repo_distribution_is_clean(self):
        """CA-M-2 / H-04: La raíz real del repositorio pasa la inspección de contenido distribuible."""
        real_root = Path(__file__).resolve().parents[1]
        inspect_distribution_cleanliness(real_root)


if __name__ == "__main__":
    unittest.main()
