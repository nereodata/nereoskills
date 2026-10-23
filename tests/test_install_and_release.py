"""Pruebas de validación de lanzamiento y alineación de manifiestos."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from adevv.release_tools import (
    ReleaseValidationError,
    obtener_versiones_publicadas,
    publicar_version,
    validar_publicacion,
)


class TestInstallAndRelease(unittest.TestCase):
    """Verifica las reglas de publicación de etiquetas y alineación de versiones."""

    def setUp(self):
        os.environ.pop("ORQUESTAR_PASO", None)
        os.environ.pop("ADEVV_BOOTSTRAPPED", None)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.adevv_home = self.root / ".adevv"
        self.claude_home = self.root / ".claude"
        self.codex_home = self.root / ".codex"
        self.agy_home = self.root / ".gemini"
        os.environ["ADEVV_HOME"] = str(self.adevv_home)
        os.environ["CLAUDE_HOME"] = str(self.claude_home)
        os.environ["CODEX_HOME"] = str(self.codex_home)
        os.environ["AGY_HOME"] = str(self.agy_home)

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
        os.environ.pop("ADEVV_HOME", None)
        os.environ.pop("CLAUDE_HOME", None)
        os.environ.pop("CODEX_HOME", None)
        os.environ.pop("AGY_HOME", None)
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

    def test_h04_obtener_versiones_publicadas_filtro_y_orden_semver(self):
        """H-04 / RF-F03-02: obtener_versiones_publicadas ignora etiquetas ligeras/pre-releases y ordena por semver."""
        subprocess.run(["git", "-C", str(self.repo_dir), "tag", "-a", "v0.2.0", "-m", "v0.2.0"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_dir), "tag", "-a", "v0.10.0", "-m", "v0.10.0"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_dir), "tag", "v0.9.0"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_dir), "tag", "-a", "v0.3.0-rc1", "-m", "rc"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_dir), "push", "origin", "--tags"], check=True, capture_output=True)

        versiones = obtener_versiones_publicadas(str(self.origin_dir))
        self.assertIn("0.2.0", versiones)
        self.assertIn("0.10.0", versiones)
        self.assertNotIn("0.9.0", versiones)
        self.assertNotIn("0.3.0-rc1", versiones)
        idx_02 = versiones.index("0.2.0")
        idx_10 = versiones.index("0.10.0")
        self.assertLess(idx_02, idx_10)

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

    def test_ca_f01_01_primera_instalacion_actualiza_y_sincroniza(self):
        """CA-F01-01 / RF-F01-01 / RF-F01-03: Primera instalación actualiza a la última versión publicada y sincroniza destinos detectados."""
        from adevv.cli import main_cli

        # 1. Configurar origen remoto con v0.1.0 y v0.1.1
        # Ya tenemos el commit inicial. Etiquetar v0.1.0
        subprocess.run(["git", "-C", str(self.repo_dir), "tag", "-a", "v0.1.0", "-m", "v0.1.0"], check=True)
        subprocess.run(["git", "-C", str(self.repo_dir), "push", "origin", "v0.1.0"], check=True)

        # Crear commit v0.1.1
        (self.repo_dir / "pyproject.toml").write_text('[project]\nname = "adevv"\nversion = "0.1.1"\n', encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo_dir), "commit", "-am", "feat: bump v0.1.1"], check=True)
        subprocess.run(["git", "-C", str(self.repo_dir), "tag", "-a", "v0.1.1", "-m", "v0.1.1"], check=True)
        subprocess.run(["git", "-C", str(self.repo_dir), "push", "origin", "main", "v0.1.1"], check=True)

        # 2. Entorno limpio sin Adevv, con Claude y Codex, sin Antigravity
        adevv_home = self.root / ".adevv_user"
        claude_home = self.root / ".claude_user"
        codex_home = self.root / ".codex_user"
        agy_home = self.root / ".gemini" / "config"

        claude_home.mkdir(parents=True, exist_ok=True)
        codex_home.mkdir(parents=True, exist_ok=True)

        env = {
            "ADEVV_HOME": str(adevv_home),
            "CLAUDE_HOME": str(claude_home),
            "CODEX_HOME": str(codex_home),
            "AGY_HOME": str(agy_home),
            "ADEVV_ORIGIN_URL": str(self.origin_dir),
        }

        # Simular instalación del paquete en 0.1.0
        # Ejecutar `adevv instalar`
        import io

        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.dict(os.environ, env),
            mock.patch("adevv.processes.detectar_procesos_adevv", return_value=[]),
            mock.patch("adevv.updater.__version__", "0.1.0"),
            mock.patch("adevv.cli.__version__", "0.1.0"),
        ):
            ret = main_cli(["instalar"], out=out, err=err)
            self.assertEqual(ret, 0)

            # Ejecutar `adevv --version`
            out_ver = io.StringIO()
            err_ver = io.StringIO()
            ret_ver = main_cli(["--version"], out=out_ver, err=err_ver)
            self.assertEqual(ret_ver, 0)

        version_output = out_ver.getvalue()
        self.assertIn("0.1.1", version_output)
        self.assertIn("Claude Code 0.1.1", version_output)
        self.assertIn("Codex 0.1.1", version_output)
        self.assertIn("Antigravity: no detectado", version_output)

        # Verificar que la carpeta de Antigravity no fue creada
        self.assertFalse(agy_home.exists())

    def test_ca_f01_10_resincronizacion_al_desfasarse_sin_bucles(self):
        """CA-F01-10 / RF-F01-11: Resincronización al arrancar sin bucles en marcha."""
        from adevv.cli import main_cli
        from adevv.store import set_active_info, set_config, set_sync_registry

        adevv_home = self.root / ".adevv_ca10"
        claude_home = self.root / ".claude_ca10"
        claude_home.mkdir(parents=True, exist_ok=True)

        env = {
            "ADEVV_HOME": str(adevv_home),
            "CLAUDE_HOME": str(claude_home),
            "CODEX_HOME": str(self.root / ".no_codex"),
            "AGY_HOME": str(self.root / ".no_agy"),
            "ORQUESTAR_PASO": "",
        }

        with mock.patch.dict(os.environ, env), mock.patch("adevv.processes.detectar_procesos_adevv", return_value=[]):
            # Versión activa 0.1.0
            set_active_info({"version": "0.1.0", "origen": "publicada"})
            set_config({"auto_update": False})
            # Registro en Claude con 0.2.0 (desfasado respecto a activa 0.1.0)
            set_sync_registry("claude", {"version": "0.2.0", "files": {}})

            import io
            out = io.StringIO()
            err = io.StringIO()
            ret = main_cli(["--version"], out=out, err=err)
            self.assertEqual(ret, 0)

        # Se debe resincronizar antes de la orden
        combined = out.getvalue() + err.getvalue()
        self.assertIn("Claude Code sincronizado con la 0.1.0.", combined)

    def test_ca_f01_11_no_resincroniza_con_bucle_en_marcha(self):
        """CA-F01-11 / RF-F01-11: Con bucle en marcha no resincroniza y avisa."""
        from adevv.cli import main_cli
        from adevv.store import set_active_info, set_sync_registry

        adevv_home = self.root / ".adevv_ca11"
        claude_home = self.root / ".claude_ca11"
        claude_home.mkdir(parents=True, exist_ok=True)

        env = {
            "ADEVV_HOME": str(adevv_home),
            "CLAUDE_HOME": str(claude_home),
            "CODEX_HOME": str(self.root / ".no_codex"),
            "AGY_HOME": str(self.root / ".no_agy"),
            "ORQUESTAR_PASO": "",
        }

        with mock.patch.dict(os.environ, env):
            set_active_info({"version": "0.1.0", "origen": "publicada"})
            set_sync_registry("claude", {"version": "0.2.0", "files": {}})

            # Simulamos detección de bucle vivo en C:\SW\Afinn
            with mock.patch("adevv.processes.detectar_procesos_adevv") as mock_proc:
                mock_proc.return_value = [
                    {"pid": 1234, "tipo": "bucle", "cwd": r"C:\SW\Afinn"}
                ]
                import io
                out = io.StringIO()
                err = io.StringIO()
                ret = main_cli(["--version"], out=out, err=err)
                self.assertEqual(ret, 0)

        combined = out.getvalue() + err.getvalue()
        self.assertIn(
            r"Claude Code sigue con la 0.2.0; se sincronizará cuando no haya bucles en marcha: bucle en C:\SW\Afinn.",
            combined,
        )

    def test_ca_f01_12_ver_que_version_hay_en_cada_arnes(self):
        """CA-F01-12 / RF-F01-12: adevv --version muestra detalle completo de versión, destinos y auto-update."""
        from adevv.cli import main_cli
        from adevv.store import set_active_info, set_config, set_sync_registry, set_update_state

        adevv_home = self.root / ".adevv_ca12"
        claude_home = self.root / ".claude_ca12"
        codex_home = self.root / ".codex_ca12"
        claude_home.mkdir(parents=True, exist_ok=True)
        codex_home.mkdir(parents=True, exist_ok=True)

        env = {
            "ADEVV_HOME": str(adevv_home),
            "CLAUDE_HOME": str(claude_home),
            "CODEX_HOME": str(codex_home),
            "AGY_HOME": str(self.root / ".no_agy"),
        }

        with mock.patch.dict(os.environ, env):
            set_active_info({"version": "0.2.0", "origen": "publicada"})
            set_config({"auto_update": True})
            set_sync_registry("claude", {"version": "0.2.0", "files": {}})
            set_sync_registry("codex", {"version": "0.2.0", "files": {}})
            set_update_state({
                "last_checked_at": "hace 3 h",
                "last_checked_status": "al día",
                "last_applied_at": "el día 20",
                "last_applied_version": "0.2.0",
            })

            import io
            out = io.StringIO()
            err = io.StringIO()
            ret = main_cli(["--version"], out=out, err=err)
            self.assertEqual(ret, 0)

        output = out.getvalue()
        self.assertIn("Adevv 0.2.0", output)
        self.assertIn("Claude Code 0.2.0", output)
        self.assertIn("Codex 0.2.0", output)
        self.assertIn("Antigravity: no detectado", output)
        self.assertIn("actualización automática: sí", output)
        self.assertIn("última comprobación: hace 3 h (al día)", output)
        self.assertIn("actualizado a 0.2.0 el día 20", output)


if __name__ == "__main__":
    unittest.main()
