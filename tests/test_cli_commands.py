"""Pruebas de despacho CLI adevv, validaciones y auto-inicialización de proyectos.

Verifica:
- CA-M-1 (@CA-F02-01, @CA-F02-02, @CA-F02-05, @RF-F02-01)
- CA-M-2 (@CA-F02-03, @CA-F02-10, @RF-F02-03, @RF-F02-09)
- CA-M-4 (@CA-F02-06, @CA-F02-07, @RF-F02-06, @RF-F02-07)
- CA-M-5 (@CA-F02-08, @CA-F02-09, @RF-F02-08)
"""

import importlib.util
import io
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from adevv.cli import main_cli
from adevv.store import set_config


def _pid_is_alive(pid: int) -> bool:
    """Comprueba si un proceso sigue activo en Windows o POSIX."""
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _kill_pid_tree(pid: int) -> None:
    """Termina de forma forzada un proceso y sus hijos para evitar bloqueos."""
    if not _pid_is_alive(pid):
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


class TestCliCommands(unittest.TestCase):
    """Pruebas completas de despacho CLI, validaciones y auto-inicialización."""

    def setUp(self):
        isolated_environment = patch.dict(os.environ)
        isolated_environment.start()
        self.addCleanup(isolated_environment.stop)
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ.pop("TELEGRAM_ALLOWED_USER_IDS", None)
        os.environ.pop("ORQUESTAR_PASO", None)
        os.environ.pop("ADEVV_BOOTSTRAPPED", None)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()
        self.repo_root = Path(__file__).resolve().parents[1]
        self.adevv_home = self.root / ".adevv"
        self.claude_home = self.root / ".claude"
        self.codex_home = self.root / ".codex"
        self.agy_home = self.root / ".gemini"
        os.environ["ADEVV_HOME"] = str(self.adevv_home)
        os.environ["CLAUDE_HOME"] = str(self.claude_home)
        os.environ["CODEX_HOME"] = str(self.codex_home)
        os.environ["AGY_HOME"] = str(self.agy_home)
        set_config({"auto_update": False})

    def tearDown(self):
        os.environ.pop("ADEVV_HOME", None)
        os.environ.pop("CLAUDE_HOME", None)
        os.environ.pop("CODEX_HOME", None)
        os.environ.pop("AGY_HOME", None)
        self.temp_dir.cleanup()

    def _init_dummy_project(self, folder: Path, prefix="PRJ", version="v0.1.0"):
        subprocess.run(["git", "init", "-q", str(folder)], check=True)
        subprocess.run(["git", "-C", str(folder), "config", "user.name", "Tester"], check=True)
        subprocess.run(["git", "-C", str(folder), "config", "user.email", "tester@adevv.local"], check=True)
        (folder / "task_config.yaml").write_text(
            f'project:\n  name: TestProj\n  prefix: "{prefix}"\n  version: "{version}"\n'
            f'levels:\n  master:\n    path: docs/plan/\n    tasks: tasks/\n    bugs: bugs/\n    id_prefix: "{prefix}"\n'
            f'validation:\n  command: "python -m unittest"\n'
            f'release:\n  manifests:\n    - path: task_config.yaml\n      type: yaml\n      key: project.version\n',
            encoding="utf-8",
        )
        (folder / "docs" / "requirements").mkdir(parents=True, exist_ok=True)
        (folder / "docs" / "requirements" / "requirements.md").write_text("# Requisitos\n", encoding="utf-8")
        (folder / "docs" / "requirements" / "req_analysis.md").write_text("# Analisis\n", encoding="utf-8")
        (folder / "docs" / "requirements" / "platform_plan.md").write_text("# Platform Plan\n", encoding="utf-8")
        (folder / "docs" / "requirements" / "platform_review.md").write_text("**Veredicto:** APROBADO\n", encoding="utf-8")
        (folder / "docs" / "requirements" / "work_plan.md").write_text("# Work Plan\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(folder), "add", "."], check=True)
        subprocess.run(["git", "-C", str(folder), "commit", "-m", "init"], check=True)

    def _ejecutar_cli(self, args, cwd: Path):
        """Ejecuta main_cli capturando código, stdout, stderr y SystemExit."""
        out = io.StringIO()
        err = io.StringIO()
        old_cwd = Path.cwd()
        try:
            os.chdir(cwd)
            code = main_cli(args, out=out, err=err)
            return code, out.getvalue(), err.getvalue()
        except SystemExit as ex:
            msg = str(ex.code) if ex.code is not None else ""
            return (ex.code if isinstance(ex.code, int) else 1), out.getvalue(), (err.getvalue() + "\n" + msg).strip()
        finally:
            os.chdir(old_cwd)

    def test_ca_f02_01_adevv_orquestar_estado_matches_orquestar_py(self):
        """CA-M-1: adevv orquestar --estado despacha y obtiene el mismo código y salida que orquestar.py."""
        project = self.root / "proj_estado"
        project.mkdir()
        self._init_dummy_project(project)

        code_adevv, out_adevv, err_adevv = self._ejecutar_cli(["orquestar", "--estado"], project)

        # Ejecución directa del script original
        script_orquestar = self.repo_root / "skills" / "orquestar" / "orquestar.py"
        res_orig = subprocess.run(
            [sys.executable, str(script_orquestar), "--estado"],
            cwd=project,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(code_adevv, res_orig.returncode)
        self.assertEqual(out_adevv.strip(), res_orig.stdout.strip())
        self.assertIn("[orquestar]", out_adevv)

    def test_ca_f02_02_adevv_orquestar_fondo(self):
        """CA-M-1 / @CA-F02-02: adevv orquestar --fondo desacoplado, orquestar.pid vivo a 5s, sin errores de args."""
        project = self.root / "proj_fondo"
        project.mkdir()
        self._init_dummy_project(project)

        dummy_harness = project / "dummy_harness.py"
        dummy_harness.write_text("import time\ntime.sleep(10)\n", encoding="utf-8")

        env = {**os.environ, "PYTHONPATH": str(self.repo_root)}
        proc = subprocess.run(
            [sys.executable, "-m", "adevv.cli", "orquestar", "--fondo", "--cmd", f'"{sys.executable}" "{dummy_harness}"'],
            cwd=project,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        self.assertEqual(proc.returncode, 0, f"Error arrancando --fondo: {proc.stderr}")

        pid_file = project / "orquestar.pid"
        log_file = project / "orquestar.log"
        child_pid = None

        try:
            # Esperar a los 5 segundos tal como exige @CA-F02-02
            time.sleep(5)
            self.assertTrue(pid_file.exists(), "orquestar.pid no existe a los 5 segundos")
            child_pid = int(pid_file.read_text(encoding="utf-8").strip())
            self.assertTrue(_pid_is_alive(child_pid), f"El proceso en segundo plano (PID {child_pid}) no sigue vivo")

            self.assertTrue(log_file.exists(), "orquestar.log no existe")
            log_content = log_file.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn("unrecognized arguments", log_content)
            self.assertNotIn("invalid choice: 'orquestar'", log_content)
        finally:
            if child_pid:
                _kill_pid_tree(child_pid)
                time.sleep(0.5)
            if pid_file.exists():
                try:
                    pid_file.unlink()
                except OSError:
                    pass

    def test_ca_f02_05_adevv_release_subcommands_and_telegram(self):
        """CA-M-1 / @CA-F02-05: adevv release y telegram producen mismos códigos y salidas que los scripts."""
        project = self.root / "proj_rel"
        project.mkdir()
        self._init_dummy_project(project)

        # 1. release manifiestos
        code_man, out_man, _ = self._ejecutar_cli(["release", "manifiestos"], project)
        script_man = self.repo_root / "skills" / "release" / "scripts" / "check_manifests_versions.py"
        res_man = subprocess.run([sys.executable, str(script_man)], cwd=project, capture_output=True, text=True)
        self.assertEqual(code_man, res_man.returncode)
        self.assertEqual(out_man.strip(), res_man.stdout.strip())

        # 2. release completitud
        code_comp, out_comp, _ = self._ejecutar_cli(["release", "completitud", "--version", "v0.1.0"], project)
        script_comp = self.repo_root / "skills" / "release" / "scripts" / "check_release_completeness.py"
        res_comp = subprocess.run([sys.executable, str(script_comp), "--version", "v0.1.0"], cwd=project, capture_output=True, text=True)
        self.assertEqual(code_comp, res_comp.returncode)
        self.assertEqual(out_comp.strip(), res_comp.stdout.strip())

        # 3. release changelog
        code_ch, out_ch, _ = self._ejecutar_cli(["release", "changelog", "--version", "v0.1.0"], project)
        script_ch = self.repo_root / "skills" / "release" / "scripts" / "generate_changelog_section.py"
        res_ch = subprocess.run([sys.executable, str(script_ch), "--version", "v0.1.0"], cwd=project, capture_output=True, text=True)
        self.assertEqual(code_ch, res_ch.returncode)
        self.assertEqual(out_ch.strip(), res_ch.stdout.strip())

        # 4. telegram --estado
        code_tg, out_tg, _ = self._ejecutar_cli(["telegram", "--estado"], project)
        script_tg = self.repo_root / "skills" / "telegram_gateway" / "gateway.py"
        res_tg = subprocess.run([sys.executable, str(script_tg), "--estado"], cwd=project, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(code_tg, res_tg.returncode)
        self.assertEqual(out_tg.strip(), res_tg.stdout.strip())

    def test_ca_f02_06_role_instructions_nonexistent_stops_before_harness(self):
        """CA-M-4 / @CA-F02-06: orchestration.json con rol.instructions inexistente para antes del arnés."""
        project = self.root / "proj_orch"
        project.mkdir()
        self._init_dummy_project(project)
        (project / "orchestration.json").write_text(
            '{"hades": {"instructions": ".agents/agents/hades.md"}}\n',
            encoding="utf-8",
        )

        code, out, err = self._ejecutar_cli(["orquestar"], project)
        self.assertNotEqual(code, 0)
        combined = out + "\n" + err
        self.assertIn("orchestration.json: hades.instructions apunta a .agents/agents/hades.md, que no existe.", combined)

    def test_ca_f02_07_local_elements_shadowing_or_submodule_stops_launch_not_estado(self):
        """CA-M-4 / @CA-F02-07: elementos locales que ocultan o .agents/.gitmodules impiden lanzar pero no estado."""
        casos_elementos = [
            (".claude/skills/orquestar", True),
            (".codex/agents/hades.toml", False),
            (".claude/skills/telegram-gateway", True),
            (".agents", True),
        ]

        for elem_rel, is_dir in casos_elementos:
            proj = self.root / f"proj_shadow_{elem_rel.replace('/', '_').replace('.', '')}"
            proj.mkdir()
            self._init_dummy_project(proj)

            elem_path = proj / elem_rel
            if is_dir:
                elem_path.mkdir(parents=True)
            else:
                elem_path.parent.mkdir(parents=True, exist_ok=True)
                elem_path.write_text("dummy", encoding="utf-8")

            # --estado debe responder normalmente
            code_est, out_est, _ = self._ejecutar_cli(["orquestar", "--estado"], proj)
            self.assertEqual(code_est, 0)
            self.assertIn("[orquestar]", out_est)

            # Lanzar bucle debe detenerse con el mensaje esperado
            code_run, out_run, err_run = self._ejecutar_cli(["orquestar"], proj)
            self.assertNotEqual(code_run, 0)
            combined = out_run + "\n" + err_run
            if elem_rel == ".agents":
                self.assertIn("Este proyecto aún usa el submódulo .agents: sigue los pasos de migración del README.", combined)
            else:
                self.assertIn("Este proyecto tiene skills, agentes o workflows propios que ocultan los de Adevv", combined)
                self.assertIn(elem_rel, combined.replace("\\", "/"))

        # Caso .gitmodules con entrada .agents
        proj_gm = self.root / "proj_gm"
        proj_gm.mkdir()
        self._init_dummy_project(proj_gm)
        (proj_gm / ".gitmodules").write_text('[submodule ".agents"]\n\tpath = .agents\n', encoding="utf-8")

        code_gm, out_gm, err_gm = self._ejecutar_cli(["orquestar"], proj_gm)
        self.assertNotEqual(code_gm, 0)
        self.assertIn("Este proyecto aún usa el submódulo .agents: sigue los pasos de migración del README.", out_gm + "\n" + err_gm)

    def test_ca_f02_08_new_project_auto_initialization(self):
        """CA-M-5 / @CA-F02-08: auto-inicialización con commit mínimo y mensaje informativo."""
        casos = [
            ("Mi app", "MIA"),
            ("Q1", "PRJ"),
            ("Ñandú", "NAN"),
        ]

        for folder_name, expected_prefix in casos:
            folder = self.root / folder_name
            folder.mkdir()
            reqs = folder / "docs" / "requirements" / "requirements.md"
            reqs.parent.mkdir(parents=True)
            reqs.write_text("# Ideas\n", encoding="utf-8")

            # Se lanza orquestar con max-pasos 0 o detención tras inicializar
            code, out, err = self._ejecutar_cli(["orquestar", "--max-pasos", "0"], folder)

            # Verificar git y archivos creados
            self.assertTrue((folder / ".git").is_dir(), f".git no creado en {folder_name}")
            cfg_path = folder / "task_config.yaml"
            self.assertTrue(cfg_path.is_file(), f"task_config.yaml no creado en {folder_name}")
            gitignore_path = folder / ".gitignore"
            self.assertTrue(gitignore_path.is_file(), f".gitignore no creado en {folder_name}")

            content = cfg_path.read_text(encoding="utf-8")
            self.assertIn(f'prefix: "{expected_prefix}"', content)
            self.assertIn(f'id_prefix: "{expected_prefix}"', content)

            # Verificar mensaje en una línea mostrado
            self.assertIn(f"inicializado repositorio Git y task_config.yaml (prefijo: {expected_prefix})", out + "\n" + err)

            # Verificar que el commit inicial solo lleva task_config.yaml y .gitignore
            proc_files = subprocess.run(
                ["git", "-C", str(folder), "show", "--name-only", "--pretty=format:"],
                capture_output=True,
                text=True,
                check=True,
            )
            committed_files = [f.strip() for f in proc_files.stdout.splitlines() if f.strip()]
            self.assertEqual(sorted(committed_files), sorted([".gitignore", "task_config.yaml"]))

    def test_ca_f02_09_folders_where_nothing_is_created(self):
        """CA-M-5 / @CA-F02-09: carpetas donde no se crea nada (subcarpeta, home, raíz o sin reqs)."""
        # 1. Subcarpeta de otro repo git
        outer_repo = self.root / "outer"
        outer_repo.mkdir()
        self._init_dummy_project(outer_repo)
        subfolder = outer_repo / "sub" / "docs"
        subfolder.mkdir(parents=True)
        (subfolder / "docs" / "requirements").mkdir(parents=True)
        (subfolder / "docs" / "requirements" / "requirements.md").write_text("# R\n", encoding="utf-8")

        code_sub, out_sub, err_sub = self._ejecutar_cli(["orquestar"], subfolder)
        self.assertNotEqual(code_sub, 0)
        comb_sub = out_sub + "\n" + err_sub
        self.assertIn("Estás en una subcarpeta de", comb_sub)
        self.assertIn("lanza /orquestar desde la raíz", comb_sub)

        # 2. Sin requirements.md: no crea nada y para por falta de configuración
        empty_folder = self.root / "empty"
        empty_folder.mkdir()
        code_emp, out_emp, err_emp = self._ejecutar_cli(["orquestar"], empty_folder)
        self.assertNotEqual(code_emp, 0)
        self.assertFalse((empty_folder / ".git").exists())
        self.assertFalse((empty_folder / "task_config.yaml").exists())
        self.assertIn("Falta task_config.yaml", out_emp + "\n" + err_emp)

        # 3. Carpeta personal simulada con requirements.md
        home_folder = self.root / "simulated_home"
        home_folder.mkdir()
        (home_folder / "docs" / "requirements").mkdir(parents=True)
        (home_folder / "docs" / "requirements" / "requirements.md").write_text("# Home\n", encoding="utf-8")
        with patch.dict(os.environ, {"ADEVV_SIMULATED_HOME": str(home_folder)}):
            code_home, out_home, err_home = self._ejecutar_cli(["orquestar"], home_folder)
            self.assertNotEqual(code_home, 0)
            self.assertFalse((home_folder / ".git").exists())
            self.assertFalse((home_folder / "task_config.yaml").exists())
            self.assertIn("Falta task_config.yaml", out_home + "\n" + err_home)

        # 4. Raíz de unidad simulada
        drive_folder = self.root / "drive_root"
        drive_folder.mkdir()
        (drive_folder / "docs" / "requirements").mkdir(parents=True)
        (drive_folder / "docs" / "requirements" / "requirements.md").write_text("# Root\n", encoding="utf-8")
        with patch.dict(os.environ, {"ADEVV_SIMULATED_DRIVE_ROOT": str(drive_folder)}):
            code_drv, out_drv, err_drv = self._ejecutar_cli(["orquestar"], drive_folder)
            self.assertNotEqual(code_drv, 0)
            self.assertFalse((drive_folder / ".git").exists())
            self.assertFalse((drive_folder / "task_config.yaml").exists())
            self.assertIn("Falta task_config.yaml", out_drv + "\n" + err_drv)

    def test_ca_f02_03_and_10_prompt_construction(self):
        """CA-M-2 / @CA-F02-03 / @CA-F02-10: rutas absolutas instaladas, otra unidad D:, --agente y repo fuente."""
        spec = importlib.util.spec_from_file_location(
            "orquestar", self.repo_root / "skills" / "orquestar" / "orquestar.py"
        )
        motor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(motor)

        mock_installed = (self.root / "installed_0.1.0").resolve()
        (mock_installed / "skills" / "orquestar").mkdir(parents=True)
        (mock_installed / "skills" / "orquestar" / "SKILL.md").write_text("# SKILL\n", encoding="utf-8")
        (mock_installed / "agents").mkdir()
        (mock_installed / "agents" / "atenea.md").write_text("# ATENEA\n", encoding="utf-8")
        (mock_installed / "agents" / "hades.md").write_text("# HADES\n", encoding="utf-8")

        with patch("adevv.store.get_active_version_dir", return_value=mock_installed), \
             patch("skills.orquestar.orquestar.get_active_version_dir", return_value=mock_installed, create=True):

            # Caso C: proyecto estándar
            proj_c = self.root / "proj_c"
            proj_c.mkdir()
            self._init_dummy_project(proj_c)
            prompt_c = motor.construir_prompt_paso(proj_c, "ciclo-requisitos", None)

            # Rutas absolutas entrecomilladas
            expected_skill = f'"{mock_installed / "skills" / "orquestar" / "SKILL.md"}"'.replace("\\", "/")
            expected_agent = f'"{mock_installed / "agents" / "atenea.md"}"'.replace("\\", "/")
            self.assertIn(expected_skill, prompt_c.replace("\\", "/"))
            self.assertIn(expected_agent, prompt_c.replace("\\", "/"))
            self.assertIn("adevv orquestar --verificar", prompt_c)
            self.assertIn("adevv orquestar --agente hades", prompt_c)
            self.assertNotIn("orquestar.py", prompt_c)

            # Caso D: proyecto en otra unidad simulada (D:/proyectos/Nuevo)
            proj_d = Path("D:/proyectos/Nuevo")
            prompt_d = motor.construir_prompt_paso(proj_d, "ciclo-requisitos", None)
            self.assertIn(expected_skill, prompt_d.replace("\\", "/"))
            self.assertIn(expected_agent, prompt_d.replace("\\", "/"))
            self.assertIn("adevv orquestar --verificar", prompt_d)

            # Caso --agente
            prompt_agente = motor.construir_prompt_agente(proj_c, "hades", "Revisa X")
            expected_hades = f'"{mock_installed / "agents" / "hades.md"}"'.replace("\\", "/")
            self.assertIn(expected_hades, prompt_agente.replace("\\", "/"))
            self.assertIn(f'"{mock_installed / "skills"}/<nombre>/SKILL.md"'.replace("\\", "/"), prompt_agente.replace("\\", "/"))

            # Caso repositorio fuente de Adevv (@CA-F02-10)
            prompt_fuente = motor.construir_prompt_paso(self.repo_root, "ciclo-requisitos", None)
            self.assertIn(expected_skill, prompt_fuente.replace("\\", "/"))
            self.assertIn('Edita el árbol de trabajo de este repositorio, en cualquier ruta que haga falta', prompt_fuente)
            self.assertIn('nunca la copia instalada', prompt_fuente)

    def test_h02_version_es_consulta_pura_sin_efectos_secundarios(self):
        """H-02: adevv --version no invoca evaluar_comprobacion_actualizacion."""
        with patch("adevv.updater.evaluar_comprobacion_actualizacion") as mock_update:
            code, out, err = self._ejecutar_cli(["--version"], self.root)
            self.assertEqual(code, 0)
            mock_update.assert_not_called()


class TestCliEnvironment(unittest.TestCase):
    """Regresiones del aislamiento de credenciales en el fixture CLI."""

    def test_telegram_environment_is_isolated_and_restored(self):
        """El fixture y sus hijos omiten Telegram y restauran el entorno al salir."""
        keys = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USER_IDS")
        for present in ((), keys[:1], keys[1:], keys):
            with self.subTest(present=present), patch.dict(os.environ):
                for key in keys:
                    os.environ.pop(key, None)
                for key in present:
                    os.environ[key] = "dummy-test-value"
                expected = {key: os.environ.get(key) for key in keys}
                fixture = TestCliCommands("test_h02_version_es_consulta_pura_sin_efectos_secundarios")
                try:
                    fixture.setUp()
                    self.assertTrue(all(key not in os.environ for key in keys))
                    child = subprocess.run(
                        [sys.executable, "-c",
                         "import os; print(any(k in os.environ for k in "
                         "('TELEGRAM_BOT_TOKEN', 'TELEGRAM_ALLOWED_USER_IDS')))"],
                        capture_output=True, text=True, check=True, timeout=10,
                    )
                    self.assertEqual(child.stdout.strip(), "False")
                finally:
                    try:
                        fixture.tearDown()
                    finally:
                        fixture.doCleanups()
                self.assertEqual({key: os.environ.get(key) for key in keys}, expected)


if __name__ == "__main__":
    unittest.main()
