"""Pruebas de validación de lanzamiento y alineación de manifiestos."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from adevv.release_tools import (
    ReleaseValidationError,
    obtener_versiones_publicadas,
    publicar_version,
    validar_publicacion,
)


class TestInstallAndRelease(unittest.TestCase):
    """Verifica las reglas de publicación de etiquetas y alineación de versiones."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.origin_dir = self.root / "origin.git"
        subprocess.run(["git", "init", "--bare", str(self.origin_dir)], check=True, capture_output=True)

        self.repo_dir = self.root / "work"
        subprocess.run(["git", "init", str(self.repo_dir)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.repo_dir), "config", "user.name", "Adevv Test"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_dir), "config", "user.email", "test@adevv.local"],
            check=True,
            capture_output=True,
        )

        (self.repo_dir / "pyproject.toml").write_text(
            '[project]\nname = "adevv"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        (self.repo_dir / "task_config.yaml").write_text(
            'project:\n  name: Adevv\n  version: "v0.1.0"\nrelease:\n  manifests:\n'
            '    - path: task_config.yaml\n      type: yaml\n      key: project.version\n'
            '    - path: pyproject.toml\n      type: toml\n      key: project.version\n',
            encoding="utf-8",
        )

        subprocess.run(["git", "-C", str(self.repo_dir), "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.repo_dir), "commit", "-m", "chore: initial commit"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_dir), "branch", "-M", "main"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_dir), "remote", "add", "origin", str(self.origin_dir)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_dir), "push", "origin", "main"],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ca_f05_03_version_mismatch_fails_with_exact_message(self):
        """CA-M-3 / H-03: Falla si la versión no coincide y no se crea ninguna etiqueta."""
        with self.assertRaises(ReleaseValidationError) as ctx:
            validar_publicacion(self.repo_dir, "v0.2.0", origin_url=str(self.origin_dir))

        self.assertEqual(
            str(ctx.exception),
            "La versión del paquete (0.1.0) no coincide con v0.2.0.",
        )

        # Comprobar que no se ha creado ninguna etiqueta
        local_tags = subprocess.run(
            ["git", "-C", str(self.repo_dir), "tag", "-l"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        origin_tags = subprocess.run(
            ["git", "-C", str(self.origin_dir), "tag", "-l"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        self.assertEqual(local_tags, [])
        self.assertEqual(origin_tags, [])

    def test_ca_f05_04_already_published_tag_fails_with_exact_message(self):
        """CA-M-4: Falla si la etiqueta ya existe publicada en el origen remoto."""
        subprocess.run(
            ["git", "-C", str(self.repo_dir), "tag", "-a", "v0.1.0", "-m", "Release v0.1.0"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_dir), "push", "origin", "v0.1.0"],
            check=True,
            capture_output=True,
        )

        with self.assertRaises(ReleaseValidationError) as ctx:
            validar_publicacion(self.repo_dir, "v0.1.0", origin_url=str(self.origin_dir))

        self.assertEqual(
            str(ctx.exception),
            "v0.1.0 ya está publicada: publica v0.1.1.",
        )

    def test_ca_f05_05_publicacion_correcta_y_etiqueta_anotada(self):
        """CA-M-5 / H-01: Publicación completa en release/v0.1, etiqueta anotada en origin y versión publicada."""
        # 1. Simular apertura de release/v0.1
        subprocess.run(
            ["git", "-C", str(self.repo_dir), "checkout", "-b", "release/v0.1"],
            check=True,
            capture_output=True,
        )

        # 2. Validar que los manifiestos coinciden automáticamente en 0.1.0
        checker_script = Path(__file__).resolve().parents[1] / "skills" / "release" / "scripts" / "check_manifests_versions.py"
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        current_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{current_pp}" if current_pp else str(repo_root)

        res = subprocess.run(
            [sys.executable, str(checker_script), "--dir", str(self.repo_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        self.assertEqual(res.returncode, 0, f"check_manifests_versions fallo: {res.stderr}\n{res.stdout}")

        # 3. Publicar versión con release_tools
        publicar_version(self.repo_dir, "v0.1.0", origin_url=str(self.origin_dir))

        # 4. Verificar versión de pyproject.toml y project.version
        import tomllib
        from adevv.yaml_lite import load_yaml

        with open(self.repo_dir / "pyproject.toml", "rb") as f:
            pyproject_data = tomllib.load(f)
        cfg_data = load_yaml(self.repo_dir / "task_config.yaml")

        self.assertEqual(pyproject_data.get("project", {}).get("version"), "0.1.0")
        self.assertEqual(cfg_data.get("project", {}).get("version"), "v0.1.0")

        # 5. Comprobar que en origin existe la etiqueta anotada v0.1.0
        tag_type = subprocess.run(
            ["git", "-C", str(self.origin_dir), "cat-file", "-t", "v0.1.0"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(tag_type, "tag", "La etiqueta v0.1.0 debe ser anotada (tipo 'tag')")

        # 6. Comprobar que el tag es alcanzable desde main en origin
        tag_commit = subprocess.run(
            ["git", "-C", str(self.origin_dir), "rev-parse", "v0.1.0^{commit}"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        main_commits = subprocess.run(
            ["git", "-C", str(self.origin_dir), "rev-list", "main"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        self.assertIn(tag_commit, main_commits, "El commit del tag debe ser alcanzable desde main en origin")

        # 7. Comprobar que Adevv considera v0.1.0 como versión publicada
        versiones = obtener_versiones_publicadas(str(self.origin_dir))
        self.assertIn("0.1.0", versiones)


if __name__ == "__main__":
    unittest.main()
