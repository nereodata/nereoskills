"""Pruebas unitarias e integradas para el actualizador automático de Adevv."""

import datetime
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from adevv.cli import main_cli
from adevv.store import (
    get_active_info,
    get_adevv_home,
    get_config,
    get_update_state,
    set_active_info,
    set_config,
    set_update_state,
    write_json_atomic,
)
from adevv.updater import (
    ResultadoActualizacion,
    _version_es_mayor,
    consultar_versiones_publicadas,
    evaluar_comprobacion_actualizacion,
    instalar_version_publicada,
    limpiar_versiones_antiguas,
)


class TestUpdaterUnit(unittest.TestCase):
    """Verifica la lógica pura del actualizador, tabla de 9 resultados y casos E1-E13."""

    def setUp(self):
        os.environ.pop("ORQUESTAR_PASO", None)
        os.environ.pop("ADEVV_BOOTSTRAPPED", None)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.adevv_home = Path(self.temp_dir.name) / ".adevv"
        os.environ["ADEVV_HOME"] = str(self.adevv_home)
        self.claude_home = Path(self.temp_dir.name) / ".claude"
        self.codex_home = Path(self.temp_dir.name) / ".codex"
        self.agy_home = Path(self.temp_dir.name) / ".gemini"
        os.environ["CLAUDE_HOME"] = str(self.claude_home)
        os.environ["CODEX_HOME"] = str(self.codex_home)
        os.environ["AGY_HOME"] = str(self.agy_home)

        self.patch_bucles = patch("adevv.processes.hay_bucles_en_marcha", return_value=[])
        self.mock_bucles = self.patch_bucles.start()

        set_active_info({
            "version": "0.1.0",
            "id": "0.1.0",
            "origen": "publicada",
        })
        set_config({
            "auto_update": True,
            "disabled_targets": [],
        })
        set_update_state({})

    def tearDown(self):
        self.patch_bucles.stop()
        os.environ.pop("ADEVV_HOME", None)
        os.environ.pop("CLAUDE_HOME", None)
        os.environ.pop("CODEX_HOME", None)
        os.environ.pop("AGY_HOME", None)
        self.temp_dir.cleanup()

    def test_version_es_mayor(self):
        self.assertTrue(_version_es_mayor("0.2.0", "0.1.0"))
        self.assertTrue(_version_es_mayor("0.10.0", "0.9.3"))
        self.assertTrue(_version_es_mayor("1.0.0", "0.10.5"))
        self.assertFalse(_version_es_mayor("0.1.0", "0.1.0"))
        self.assertFalse(_version_es_mayor("0.9.3", "0.10.0"))

    def test_h04_evaluar_tabla_pura(self):
        """H-04 / Regla 1: evaluar_tabla es una función pura que no toca disco ni red."""
        from adevv.updater import evaluar_tabla, ResultadoActualizacion
        ahora = datetime.datetime(2026, 10, 22, 12, 0, 0)
        # Desactivada por config
        res = evaluar_tabla(state={}, config={"auto_update": False}, active_info={}, ahora=ahora)
        self.assertEqual(res["resultado"], ResultadoActualizacion.DESACTIVADA)

        # Dentro de orquestacion cuando no es forzada ni es_instalar
        res = evaluar_tabla(state={}, config={}, active_info={}, ahora=ahora, dentro_orquestacion=True)
        self.assertEqual(res["resultado"], ResultadoActualizacion.DENTRO_DE_ORQUESTACION)

        # Si es_instalar=True, dentro_orquestacion no bloquea
        res = evaluar_tabla(state={}, config={}, active_info={}, ahora=ahora, dentro_orquestacion=True, es_instalar=True)
        self.assertNotEqual(res["resultado"], ResultadoActualizacion.DENTRO_DE_ORQUESTACION)

        # Origen desarrollo
        res_des = evaluar_tabla(state={}, config={}, active_info={"origen": "desarrollo"}, ahora=ahora)
        self.assertEqual(res_des["resultado"], ResultadoActualizacion.DESARROLLO)

        # Espera < 24 h desde last_checked_at
        hace_2h = (ahora - datetime.timedelta(hours=2)).isoformat()
        res_esp24 = evaluar_tabla(state={"last_checked_at": hace_2h}, config={}, active_info={}, ahora=ahora)
        self.assertEqual(res_esp24["resultado"], ResultadoActualizacion.ESPERA)

        # Espera < 1 h desde last_sin_red_at
        hace_30m = (ahora - datetime.timedelta(minutes=30)).isoformat()
        res_esp1 = evaluar_tabla(state={"last_sin_red_at": hace_30m}, config={}, active_info={}, ahora=ahora)
        self.assertEqual(res_esp1["resultado"], ResultadoActualizacion.ESPERA)

        # Aplazada previa
        res_apl = evaluar_tabla(state={"aplazada": "0.3.0"}, config={}, active_info={}, ahora=ahora)
        self.assertEqual(res_apl["resultado"], ResultadoActualizacion.APLAZADA)
        self.assertEqual(res_apl["target_version"], "0.3.0")

    def test_consultar_versiones_publicadas_filtro_etiquetas(self):
        salida_git = (
            "hash1       refs/tags/v0.1.0\n"
            "peeled1     refs/tags/v0.1.0^{}\n"
            "hash2       refs/tags/v0.2.0-rc1\n"
            "peeled2     refs/tags/v0.2.0-rc1^{}\n"
            "hash3       refs/tags/v0.3.0\n"  # Ligera: sin ^{}
            "hash4       refs/tags/v0.2.1\n"
            "peeled4     refs/tags/v0.2.1^{}\n"
            "hash5       refs/heads/main\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=salida_git,
                stderr="",
            )
            versiones, mapa_commits, err = consultar_versiones_publicadas("dummy_origin")
            self.assertIsNone(err)
            self.assertEqual(versiones, ["0.1.0", "0.2.1"])
            self.assertEqual(mapa_commits["0.2.1"], "peeled4")
            self.assertNotIn("0.3.0", versiones)
            self.assertNotIn("0.2.0-rc1", versiones)

    def test_consultar_versiones_publicadas_timeout_y_credenciales(self):
        # H-03: verificar timeout=5 y variables de entorno no interactivas
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
            versiones, mapa, err = consultar_versiones_publicadas("dummy_origin")
            self.assertEqual(versiones, [])
            self.assertIn("timeout", err.lower())

            args, kwargs = mock_run.call_args
            self.assertEqual(kwargs.get("timeout"), 5)
            env = kwargs.get("env", {})
            self.assertEqual(env.get("GIT_TERMINAL_PROMPT"), "0")
            self.assertEqual(env.get("GCM_INTERACTIVE"), "never")
            self.assertEqual(env.get("GIT_ASKPASS"), "echo")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=128,
                stdout="",
                stderr="fatal: could not read Username for 'https://github.com': terminal prompts disabled",
            )
            versiones, mapa, err = consultar_versiones_publicadas("dummy_origin")
            self.assertEqual(versiones, [])
            self.assertIn("credenciales", err.lower())

        # @CA-F03-06: comprobar que adevv orquestar --estado continúa con versión actual tras fallo de red
        out = io.StringIO()
        err = io.StringIO()
        with patch("adevv.updater.consultar_versiones_publicadas", return_value=([], {}, "timeout de 5 s")), \
             patch("adevv.cli._despachar_script", return_value=0) as mock_dispatch:
            code = main_cli(["orquestar", "--estado"], out=out, err=err)
            self.assertEqual(code, 0)
            mock_dispatch.assert_called_once()
            # En primer fallo de red automático no se emite aviso a stderr
            self.assertEqual(err.getvalue(), "")

    def test_fila_1_desactivada(self):
        set_config({"auto_update": False})
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query:
            res, msg, ver = evaluar_comprobacion_actualizacion()
            self.assertEqual(res, ResultadoActualizacion.DESACTIVADA)
            self.assertIsNone(msg)
            mock_query.assert_not_called()

    def test_fila_2_dentro_de_orquestacion(self):
        os.environ["ORQUESTAR_PASO"] = "task-dev"
        try:
            with patch("adevv.updater.consultar_versiones_publicadas") as mock_query:
                res, msg, ver = evaluar_comprobacion_actualizacion()
                self.assertEqual(res, ResultadoActualizacion.DENTRO_DE_ORQUESTACION)
                self.assertIsNone(msg)
                mock_query.assert_not_called()
        finally:
            os.environ.pop("ORQUESTAR_PASO", None)

    def test_fila_3_desarrollo(self):
        set_active_info({"version": "0.1.0", "origen": "desarrollo"})
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query:
            res, msg, ver = evaluar_comprobacion_actualizacion()
            self.assertEqual(res, ResultadoActualizacion.DESARROLLO)
            self.assertIsNone(msg)
            mock_query.assert_not_called()

    # Pruebas de los ejemplos E1 a E13
    def test_ejemplos_e1_e2_ventana_24h(self):
        base = datetime.datetime(2026, 10, 19, 9, 0, 0)
        set_update_state({"last_checked_at": base.isoformat()})

        # E1: última contada lun 09:00, ahora mar 08:59 -> ESPERA
        ahora_e1 = base + datetime.timedelta(hours=23, minutes=59)
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query:
            res, msg, _ = evaluar_comprobacion_actualizacion(ahora=ahora_e1)
            self.assertEqual(res, ResultadoActualizacion.ESPERA)
            mock_query.assert_not_called()

        # E2: última contada lun 09:00, ahora mar 09:00 -> APLICADA
        ahora_e2 = base + datetime.timedelta(hours=24)
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query, \
             patch("adevv.updater.instalar_version_publicada") as mock_inst, \
             patch("adevv.updater.hay_bucles_en_marcha", return_value=[]):
            mock_query.return_value = (["0.1.0", "0.2.0"], {"0.2.0": "commit2"}, None)
            mock_inst.return_value = (True, "OK", [])
            res, msg, ver = evaluar_comprobacion_actualizacion(ahora=ahora_e2)
            self.assertEqual(res, ResultadoActualizacion.APLICADA)
            self.assertEqual(ver, "0.2.0")
            self.assertIn("Adevv actualizado de 0.1.0 a 0.2.0.", msg)

    def test_ejemplos_e3_e4_ventana_sin_red(self):
        dom_09 = datetime.datetime(2026, 10, 18, 9, 0, 0)
        lun_10 = datetime.datetime(2026, 10, 19, 10, 0, 0)
        set_update_state({
            "last_checked_at": dom_09.isoformat(),
            "last_sin_red_at": lun_10.isoformat(),
        })

        # E3: lun 10:59 -> ESPERA (59 min < 1h)
        ahora_e3 = lun_10 + datetime.timedelta(minutes=59)
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query:
            res, msg, _ = evaluar_comprobacion_actualizacion(ahora=ahora_e3)
            self.assertEqual(res, ResultadoActualizacion.ESPERA)
            mock_query.assert_not_called()

        # E4: ahora lun 11:00 -> APLICADA (1h no es < 1h; 26h >= 24h)
        ahora_e4 = lun_10 + datetime.timedelta(hours=1)
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query, \
             patch("adevv.updater.instalar_version_publicada") as mock_inst, \
             patch("adevv.updater.hay_bucles_en_marcha", return_value=[]):
            mock_query.return_value = (["0.1.0", "0.2.0"], {"0.2.0": "commit2"}, None)
            mock_inst.return_value = (True, "OK", [])
            res, msg, ver = evaluar_comprobacion_actualizacion(ahora=ahora_e4)
            self.assertEqual(res, ResultadoActualizacion.APLICADA)

    def test_ejemplos_e5_e6_e7_fallida(self):
        lun_10 = datetime.datetime(2026, 10, 19, 10, 0, 0)
        set_update_state({
            "last_checked_at": lun_10.isoformat(),
            "fallida": "0.2.0",
        })
        # E5: fallida 0.2.0, última contada lun 10:00, ahora lun 15:59 -> ESPERA
        ahora_e5 = lun_10 + datetime.timedelta(hours=5, minutes=59)
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query:
            res, _, _ = evaluar_comprobacion_actualizacion(ahora=ahora_e5)
            self.assertEqual(res, ResultadoActualizacion.ESPERA)

        # E6: ahora mar 10:00 (24h), publicada 0.2.0 -> AL_DIA (0.2.0 <= fallida)
        ahora_e6 = lun_10 + datetime.timedelta(hours=24)
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query:
            mock_query.return_value = (["0.1.0", "0.2.0"], {"0.2.0": "commit2"}, None)
            res, msg, _ = evaluar_comprobacion_actualizacion(ahora=ahora_e6)
            self.assertEqual(res, ResultadoActualizacion.AL_DIA)

        # E7: ahora mar 10:00, publicada 0.2.1 -> APLICADA (0.2.1 > fallida 0.2.0)
        set_update_state({
            "last_checked_at": lun_10.isoformat(),
            "fallida": "0.2.0",
        })
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query, \
             patch("adevv.updater.instalar_version_publicada") as mock_inst, \
             patch("adevv.updater.hay_bucles_en_marcha", return_value=[]):
            mock_query.return_value = (["0.1.0", "0.2.0", "0.2.1"], {"0.2.1": "commit21"}, None)
            mock_inst.return_value = (True, "OK", [])
            res, msg, ver = evaluar_comprobacion_actualizacion(ahora=ahora_e6)
            self.assertEqual(res, ResultadoActualizacion.APLICADA)
            self.assertEqual(ver, "0.2.1")

    def test_ejemplos_e8_e9_e10_e11_aplazada(self):
        # E8: aplazada 0.2.0, aviso lun 09:00, ahora lun 12:00, bucle vivo -> APLAZADA sin aviso (3h < 24h)
        lun_09 = datetime.datetime(2026, 10, 19, 9, 0, 0)
        set_update_state({
            "aplazada": "0.2.0",
            "last_notice_aplazada_at": lun_09.isoformat(),
        })
        ahora_e8 = lun_09 + datetime.timedelta(hours=3)
        bucle_proc = [{"pid": 999, "tipo": "bucle", "cwd": "C:\\SW\\Afinn", "cmd": "adevv orquestar"}]

        with patch("adevv.updater.hay_bucles_en_marcha", return_value=bucle_proc), \
             patch("adevv.updater.consultar_versiones_publicadas") as mock_query:
            res, msg, ver = evaluar_comprobacion_actualizacion(ahora=ahora_e8)
            self.assertEqual(res, ResultadoActualizacion.APLAZADA)
            self.assertIsNone(msg)
            mock_query.assert_not_called()

        # E9: ahora lun 12:00, sin bucles -> APLICADA (aplazada no espera 24h)
        set_update_state({
            "aplazada": "0.2.0",
            "last_notice_aplazada_at": lun_09.isoformat(),
        })
        with patch("adevv.updater.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.instalar_version_publicada") as mock_inst:
            mock_inst.return_value = (True, "OK", [])
            res, msg, ver = evaluar_comprobacion_actualizacion(ahora=ahora_e8)
            self.assertEqual(res, ResultadoActualizacion.APLICADA)
            self.assertEqual(ver, "0.2.0")

        # E10: ahora mar 09:00 (24h), bucle vivo -> APLAZADA con aviso
        set_update_state({
            "aplazada": "0.2.0",
            "last_notice_aplazada_at": lun_09.isoformat(),
        })
        ahora_e10 = lun_09 + datetime.timedelta(hours=24)
        with patch("adevv.updater.hay_bucles_en_marcha", return_value=bucle_proc):
            res, msg, ver = evaluar_comprobacion_actualizacion(ahora=ahora_e10)
            self.assertEqual(res, ResultadoActualizacion.APLAZADA)
            self.assertIsNotNone(msg)
            self.assertIn("Adevv 0.2.0 disponible; se aplicará cuando no haya bucles en marcha: bucle en C:\\SW\\Afinn.", msg)

        # E11: aplazada 0.2.0, ahora lun 12:00, solo gateway vivo -> APLICADA + reinicio gateway
        set_update_state({
            "aplazada": "0.2.0",
            "last_notice_aplazada_at": lun_09.isoformat(),
        })
        gateway_proc = [{"pid": 888, "tipo": "gateway", "cwd": "C:\\SW\\Adevv", "cmd": "adevv telegram"}]
        with patch("adevv.updater.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.detectar_procesos_adevv", return_value=gateway_proc), \
             patch("adevv.updater.instalar_version_publicada") as mock_inst:
            mock_inst.return_value = (True, "OK", [])
            res, msg, ver = evaluar_comprobacion_actualizacion(ahora=ahora_e8)
            self.assertEqual(res, ResultadoActualizacion.APLICADA)
            self.assertIn("Reinicia el gateway en C:\\SW\\Adevv.", msg)

    def test_ejemplo_e12_aplazada_sin_red(self):
        lun_09 = datetime.datetime(2026, 10, 19, 9, 0, 0)
        set_update_state({"aplazada": "0.2.0"})
        ahora = lun_09 + datetime.timedelta(hours=3)
        with patch("adevv.updater.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.instalar_version_publicada") as mock_inst:
            mock_inst.return_value = (False, "error de red al descargar", [])
            res, msg, ver = evaluar_comprobacion_actualizacion(ahora=ahora)
            self.assertEqual(res, ResultadoActualizacion.SIN_RED)

    def test_ejemplo_e13_sin_red_prolongado_con_aviso(self):
        ahora = datetime.datetime(2026, 10, 22, 12, 0, 0)
        ocho_dias = ahora - datetime.timedelta(days=8)
        dos_horas = ahora - datetime.timedelta(hours=2)
        hace_25h = ahora - datetime.timedelta(hours=25)

        set_update_state({
            "last_checked_at": ocho_dias.isoformat(),
            "last_sin_red_at": dos_horas.isoformat(),
            "last_notice_sin_red_at": hace_25h.isoformat(),
        })

        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query:
            mock_query.return_value = ([], {}, "error de conexión")
            res, msg, _ = evaluar_comprobacion_actualizacion(ahora=ahora)
            self.assertEqual(res, ResultadoActualizacion.SIN_RED)
            self.assertIsNotNone(msg)
            self.assertIn("No se ha podido comprobar actualizaciones desde", msg)


class TestUpdaterIntegrationAndCli(unittest.TestCase):
    """Verifica la instalación real en ~/.adevv/versions/, comandos CLI y cobertura de F-03."""

    def setUp(self):
        os.environ.pop("ORQUESTAR_PASO", None)
        os.environ.pop("ADEVV_BOOTSTRAPPED", None)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.adevv_home = Path(self.temp_dir.name) / ".adevv"
        os.environ["ADEVV_HOME"] = str(self.adevv_home)
        self.claude_home = Path(self.temp_dir.name) / ".claude"
        self.codex_home = Path(self.temp_dir.name) / ".codex"
        self.agy_home = Path(self.temp_dir.name) / ".gemini"
        os.environ["CLAUDE_HOME"] = str(self.claude_home)
        os.environ["CODEX_HOME"] = str(self.codex_home)
        os.environ["AGY_HOME"] = str(self.agy_home)

        # Crear instalación base 0.1.0
        self.v010_dir = self.adevv_home / "versions" / "0.1.0"
        self.v010_dir.mkdir(parents=True, exist_ok=True)
        (self.v010_dir / "pyproject.toml").write_text('[project]\nname = "adevv"\nversion = "0.1.0"\n', encoding="utf-8")
        (self.v010_dir / "skills").mkdir()

        set_active_info({
            "version": "0.1.0",
            "id": "0.1.0",
            "origen": "publicada",
        })
        set_config({"auto_update": True, "disabled_targets": []})
        set_update_state({})

        self.patch_bucles = patch("adevv.processes.hay_bucles_en_marcha", return_value=[])
        self.mock_bucles = self.patch_bucles.start()

    def tearDown(self):
        self.patch_bucles.stop()
        os.environ.pop("ADEVV_HOME", None)
        os.environ.pop("CLAUDE_HOME", None)
        os.environ.pop("CODEX_HOME", None)
        os.environ.pop("AGY_HOME", None)
        self.temp_dir.cleanup()

    def test_h03_instalar_version_publicada_filtra_lista_blanca(self):
        """H-03 / RF-F05-01: instalar_version_publicada elimina docs/, tests/ y archivos no permitidos."""
        repo_origen = Path(self.temp_dir.name) / "repo_origen"
        repo_origen.mkdir()
        subprocess.run(["git", "init", str(repo_origen)], check=True, capture_output=True)
        (repo_origen / "pyproject.toml").write_text('[project]\nname = "adevv"\nversion = "0.2.0"\n', encoding="utf-8")
        (repo_origen / "README.md").write_text("# Adevv\n", encoding="utf-8")
        (repo_origen / "skills" / "demo").mkdir(parents=True)
        (repo_origen / "skills" / "demo" / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
        (repo_origen / "docs").mkdir()
        (repo_origen / "docs" / "secret.md").write_text("# Secret\n", encoding="utf-8")
        (repo_origen / "tests").mkdir()
        (repo_origen / "tests" / "test_dummy.py").write_text("# test\n", encoding="utf-8")
        (repo_origen / "task_config.yaml").write_text("project: {}\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo_origen), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(repo_origen), "config", "user.email", "t@a.com"], check=True)
        subprocess.run(["git", "-C", str(repo_origen), "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo_origen), "commit", "-m", "v0.2.0"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo_origen), "tag", "-a", "v0.2.0", "-m", "v0.2.0"], check=True, capture_output=True)

        ok, msg, desfasados = instalar_version_publicada("0.2.0", origin_url=str(repo_origen))
        self.assertTrue(ok, msg)
        target_dir = self.adevv_home / "versions" / "0.2.0"
        self.assertTrue((target_dir / "pyproject.toml").exists())
        self.assertTrue((target_dir / "skills" / "demo" / "SKILL.md").exists())
        self.assertFalse((target_dir / "docs").exists())
        self.assertFalse((target_dir / "tests").exists())
        self.assertFalse((target_dir / "task_config.yaml").exists())

    def test_h03_adevv_instalar_materializa_version_local_cuando_esta_al_dia(self):
        """H-03 / §2: adevv instalar sin versión remota superior materializa ~/.adevv/versions/<V>/ y active.json."""
        from adevv.cli import main_cli
        active_file = self.adevv_home / "active.json"
        if active_file.exists():
            active_file.unlink()
        versions_dir = self.adevv_home / "versions"
        if versions_dir.exists():
            shutil.rmtree(versions_dir, ignore_errors=True)

        set_config({"auto_update": False})
        out = io.StringIO()
        err = io.StringIO()
        code = main_cli(["instalar"], out=out, err=err)
        self.assertEqual(code, 0)
        self.assertTrue(active_file.exists())
        act = get_active_info()
        self.assertIsNotNone(act)
        v = act.get("version")
        self.assertTrue(v)
        v_dir = versions_dir / v
        self.assertTrue(v_dir.exists())
        self.assertTrue((v_dir / "pyproject.toml").exists())
        self.assertTrue((v_dir / "skills").exists())
        self.assertFalse((v_dir / "docs").exists())
        self.assertFalse((v_dir / "tests").exists())

    def test_instalar_version_publicada_exito_y_limpieza(self):
        # Crear versión vieja 0.0.9 para comprobar su limpieza
        v009_dir = self.adevv_home / "versions" / "0.0.9"
        v009_dir.mkdir(parents=True, exist_ok=True)

        # Simular repositorio git local con etiqueta v0.2.0 anotada
        repo_dir = Path(self.temp_dir.name) / "remote_repo"
        repo_dir.mkdir()
        subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(repo_dir), check=True)

        (repo_dir / "pyproject.toml").write_text('[project]\nname = "adevv"\nversion = "0.2.0"\n', encoding="utf-8")
        (repo_dir / "adevv").mkdir()
        (repo_dir / "adevv" / "__init__.py").write_text('__version__ = "0.2.0"\n', encoding="utf-8")
        (repo_dir / "skills").mkdir()
        (repo_dir / "skills" / "demo").mkdir()
        (repo_dir / "skills" / "demo" / "SKILL.md").write_text("# Demo\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "commit", "-m", "v0.2.0"], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "tag", "-a", "v0.2.0", "-m", "Release v0.2.0"], cwd=str(repo_dir), check=True)

        # Simular que un proceso gateway está usando la versión 0.1.0 (para verificar que NO se borra)
        proc_gw = [{"pid": 7777, "tipo": "gateway", "cwd": "C:\\SW\\Adevv", "cmd": f'python "{self.v010_dir}\\gateway.py"'}]
        with patch("adevv.updater.detectar_procesos_adevv", return_value=proc_gw):
            ok, causa, desfasados = instalar_version_publicada(
                target_version="0.2.0",
                origin_url=str(repo_dir),
            )
            self.assertTrue(ok)
            self.assertEqual(causa, "OK")

        # Verificar que active.json conmuta a 0.2.0
        act = get_active_info()
        self.assertEqual(act["version"], "0.2.0")

        # Verificar que la versión antigua no usada 0.0.9 fue limpiada
        self.assertFalse(v009_dir.exists())

        # Verificar que 0.1.0 sigue existiendo porque el gateway la usa
        self.assertTrue((self.adevv_home / "versions" / "0.1.0").exists())

    def test_instalar_version_falla_si_paquete_no_coincide(self):
        # Repositorio donde la etiqueta es v0.3.0 pero el paquete dice 0.2.9
        repo_dir = Path(self.temp_dir.name) / "bad_repo"
        repo_dir.mkdir()
        subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(repo_dir), check=True)

        (repo_dir / "pyproject.toml").write_text('[project]\nname = "adevv"\nversion = "0.2.9"\n', encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "commit", "-m", "mismatch"], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "tag", "-a", "v0.3.0", "-m", "Release v0.3.0"], cwd=str(repo_dir), check=True)

        ok, causa, _ = instalar_version_publicada(
            target_version="0.3.0",
            origin_url=str(repo_dir),
        )
        self.assertFalse(ok)
        self.assertIn("la versión instalada no es 0.3.0", causa)
        # La versión activa sigue siendo 0.1.0 intacta
        self.assertEqual(get_active_info()["version"], "0.1.0")

    # H-01: Cobertura de @CA-F03-08 (Fallo de instalación durante comprobación automática)
    def test_ca_f03_08_fallo_instalacion_durante_comprobacion_automatica(self):
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query, \
             patch("adevv.updater.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.instalar_version_publicada") as mock_inst:
            mock_query.return_value = (["0.1.0", "0.2.0"], {"0.2.0": "commit2"}, None)
            mock_inst.return_value = (False, "fallo de extracción en disco", [])

            res, msg, ver = evaluar_comprobacion_actualizacion()
            self.assertEqual(res, ResultadoActualizacion.FALLIDA)
            self.assertEqual(ver, "0.2.0")
            self.assertEqual(
                msg,
                "No se pudo actualizar a 0.2.0: fallo de extracción en disco. Sigues con la 0.1.0. Reintenta con `adevv actualizar`.",
            )

            # Persistencia en update_state
            state = get_update_state()
            self.assertEqual(state.get("fallida"), "0.2.0")
            self.assertEqual(state.get("fallida_causa"), "fallo de extracción en disco")
            self.assertIsNotNone(state.get("last_failed_at"))

        # Comprobar en CLI con adevv orquestar --fondo que se emite a stderr y continúa con 0.1.0
        out = io.StringIO()
        err = io.StringIO()
        with patch("adevv.updater.evaluar_comprobacion_actualizacion") as mock_eval, \
             patch("adevv.cli._despachar_script", return_value=0) as mock_dispatch:
            mock_eval.return_value = (
                ResultadoActualizacion.FALLIDA,
                "No se pudo actualizar a 0.2.0: fallo de red. Sigues con la 0.1.0. Reintenta con `adevv actualizar`.",
                "0.2.0",
            )
            code = main_cli(["orquestar", "--fondo"], out=out, err=err)
            self.assertEqual(code, 0)
            self.assertIn("No se pudo actualizar a 0.2.0", err.getvalue())
            self.assertEqual(get_active_info()["version"], "0.1.0")
            mock_dispatch.assert_called_once()

    # H-01: Cobertura de @CA-F03-10 (Actualización aplicada pero un arnés sin sincronizar)
    def test_ca_f03_10_actualizacion_aplicada_con_arnes_desfasado(self):
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query, \
             patch("adevv.updater.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.instalar_version_publicada") as mock_inst:
            mock_query.return_value = (["0.1.0", "0.2.0"], {"0.2.0": "commit2"}, None)
            mock_inst.return_value = (True, "OK", ["Codex: archivo de agente bloqueado"])

            res, msg, ver = evaluar_comprobacion_actualizacion()
            self.assertEqual(res, ResultadoActualizacion.APLICADA)
            self.assertEqual(ver, "0.2.0")
            self.assertIn("Adevv actualizado de 0.1.0 a 0.2.0.", msg)
            self.assertIn("Arneses sin sincronizar: Codex: archivo de agente bloqueado.", msg)

    # H-02: Cobertura de @CA-F03-02 (Actualización aplicada al lanzar y despacho con nueva versión)
    def test_ca_f03_02_actualizacion_aplicada_al_lanzar(self):
        out = io.StringIO()
        err = io.StringIO()

        # Simular instalación exitosa de 0.2.0 durante adevv orquestar --estado
        v020_dir = self.adevv_home / "versions" / "0.2.0"
        v020_dir.mkdir(parents=True, exist_ok=True)
        (v020_dir / "pyproject.toml").write_text('[project]\nname = "adevv"\nversion = "0.2.0"\n', encoding="utf-8")
        (v020_dir / "skills" / "orquestar").mkdir(parents=True, exist_ok=True)
        (v020_dir / "skills" / "orquestar" / "orquestar.py").write_text("# 0.2.0\n", encoding="utf-8")

        def mock_inst(target_version, **kwargs):
            set_active_info({"version": target_version, "id": target_version, "origen": "publicada"})
            return (True, "OK", [])

        with patch("adevv.updater.consultar_versiones_publicadas", return_value=(["0.1.0", "0.2.0"], {"0.2.0": "c2"}, None)), \
             patch("adevv.updater.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.instalar_version_publicada", side_effect=mock_inst), \
             patch("adevv.cli._despachar_script", return_value=0) as mock_dispatch:

            code = main_cli(["orquestar", "--estado"], out=out, err=err)
            self.assertEqual(code, 0)
            self.assertIn("Adevv actualizado de 0.1.0 a 0.2.0. Reinicia las sesiones abiertas de los arneses para usar las skills nuevas.", err.getvalue())

            # Comprobar que el script despachado corresponde a la versión 0.2.0 activada
            script_llamado = mock_dispatch.call_args[0][0]
            self.assertIn("0.2.0", str(script_llamado))

        # Comprobar que adevv --version informa 0.2.0
        out_v = io.StringIO()
        code_v = main_cli(["--version"], out=out_v)
        self.assertEqual(code_v, 0)
        self.assertIn("Adevv 0.2.0", out_v.getvalue())

    # H-02: Cobertura de @CA-F03-03 (Transición inicial a APLAZADA al detectar bucle en otro proyecto)
    def test_ca_f03_03_transicion_inicial_a_aplazada(self):
        bucle_proc = [{"pid": 4321, "tipo": "bucle", "cwd": "C:\\SW\\Afinn", "cmd": "adevv orquestar"}]

        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query, \
             patch("adevv.updater.hay_bucles_en_marcha", return_value=bucle_proc), \
             patch("adevv.updater.instalar_version_publicada") as mock_inst:
            mock_query.return_value = (["0.1.0", "0.2.0"], {"0.2.0": "c2"}, None)

            res, msg, ver = evaluar_comprobacion_actualizacion()
            self.assertEqual(res, ResultadoActualizacion.APLAZADA)
            self.assertEqual(ver, "0.2.0")
            self.assertEqual(msg, "Adevv 0.2.0 disponible; se aplicará cuando no haya bucles en marcha: bucle en C:\\SW\\Afinn.")
            mock_inst.assert_not_called()

            # Se guardó como aplazada en el estado
            self.assertEqual(get_update_state().get("aplazada"), "0.2.0")

        # Cuando el bucle de Afinn termina, la siguiente orden aplica 0.2.0 sin esperar 24h
        with patch("adevv.updater.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.instalar_version_publicada", return_value=(True, "OK", [])) as mock_inst2:
            res2, msg2, ver2 = evaluar_comprobacion_actualizacion()
            self.assertEqual(res2, ResultadoActualizacion.APLICADA)
            self.assertEqual(ver2, "0.2.0")
            mock_inst2.assert_called_once()

    # H-02: Cobertura de @CA-F03-04 y @CA-F03-05 (adevv actualizar sin argumentos frente a bucle previo y gateway)
    def test_ca_f03_04_y_05_adevv_actualizar_sin_argumentos_bucle_y_gateway(self):
        # @CA-F03-04: bucle anterior a la migración bloquea adevv actualizar
        out = io.StringIO()
        err = io.StringIO()
        bucle_previo = [{
            "pid": 6543,
            "tipo": "bucle",
            "cwd": "C:\\SW\\Aprexx",
            "cmd": 'python .agents/skills/orquestar/orquestar.py',
        }]
        with patch("adevv.updater.consultar_versiones_publicadas", return_value=(["0.1.0", "0.2.0"], {"0.2.0": "c2"}, None)), \
             patch("adevv.updater.hay_bucles_en_marcha", return_value=bucle_previo), \
             patch("adevv.updater.instalar_version_publicada") as mock_inst:
            code = main_cli(["actualizar"], out=out, err=err)
            self.assertEqual(code, 1)
            mock_inst.assert_not_called()
            self.assertIn("Adevv 0.2.0 disponible; se aplicará cuando no haya bucles en marcha: bucle en C:\\SW\\Aprexx.", err.getvalue())

        # @CA-F03-05: gateway en marcha no bloquea adevv actualizar, actualiza a 0.2.0 y pide reiniciar gateway
        out = io.StringIO()
        err = io.StringIO()
        gateway_proc = [{
            "pid": 7654,
            "tipo": "gateway",
            "cwd": "C:\\SW\\Adevv",
            "cmd": "adevv telegram",
        }]
        with patch("adevv.updater.consultar_versiones_publicadas", return_value=(["0.1.0", "0.2.0"], {"0.2.0": "c2"}, None)), \
             patch("adevv.updater.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.detectar_procesos_adevv", return_value=gateway_proc), \
             patch("adevv.updater.instalar_version_publicada", return_value=(True, "OK", [])) as mock_inst:
            code = main_cli(["actualizar"], out=out, err=err)
            self.assertEqual(code, 0)
            mock_inst.assert_called_once()
            self.assertIn("Reinicia el gateway en C:\\SW\\Adevv.", out.getvalue())

    # H-02: Cobertura de @CA-F03-12 (Volver atrás a 0.2.1 desactiva auto_update y adevv actualizar a 0.3.1 la reactiva)
    def test_ca_f03_12_volver_atras_y_reactivar(self):
        set_active_info({"version": "0.3.0", "id": "0.3.0", "origen": "publicada"})

        # Volver atrás a 0.2.1
        out = io.StringIO()
        err = io.StringIO()
        with patch("adevv.updater.consultar_versiones_publicadas", return_value=(["0.2.1", "0.3.0"], {"0.2.1": "c21", "0.3.0": "c30"}, None)), \
             patch("adevv.processes.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.instalar_version_publicada", return_value=(True, "OK", [])) as mock_inst:
            code = main_cli(["actualizar", "0.2.1"], out=out, err=err)
            self.assertEqual(code, 0)
            mock_inst.assert_called_once_with(target_version="0.2.1", commit_hash="c21")
            self.assertIn("Actualización automática desactivada; `adevv actualizar` la reactiva.", out.getvalue())
            self.assertFalse(get_config()["auto_update"])

        # 24 horas después una orden adevv no consulta la red
        ahora_24h = datetime.datetime.now() + datetime.timedelta(hours=24)
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_query, \
             patch("adevv.cli._despachar_script", return_value=0):
            main_cli(["orquestar", "--estado"])
            mock_query.assert_not_called()

        # Se publica la 0.3.1 y ejecuto adevv actualizar
        out_reactivar = io.StringIO()
        err_reactivar = io.StringIO()
        with patch("adevv.updater.consultar_versiones_publicadas", return_value=(["0.2.1", "0.3.0", "0.3.1"], {"0.3.1": "c31"}, None)), \
             patch("adevv.processes.hay_bucles_en_marcha", return_value=[]), \
             patch("adevv.updater.instalar_version_publicada", return_value=(True, "OK", [])) as mock_inst_31:
            code = main_cli(["actualizar"], out=out_reactivar, err=err_reactivar)
            self.assertEqual(code, 0)
            mock_inst_31.assert_called_once_with(target_version="0.3.1", commit_hash="c31", origin_url=None)
            self.assertTrue(get_config()["auto_update"])
            self.assertIn("Actualización automática reactivada.", out_reactivar.getvalue())

    def test_adevv_actualizar_cli_comandos(self):
        # 1. adevv actualizar X.Y.Z con versión inexistente
        out = io.StringIO()
        err = io.StringIO()
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_q:
            mock_q.return_value = (["0.1.0", "0.2.0"], {"0.1.0": "c1", "0.2.0": "c2"}, None)
            code = main_cli(["actualizar", "0.9.0"], out=out, err=err)
            self.assertEqual(code, 1)
            self.assertIn("0.9.0 no es una versión publicada. Publicadas: 0.2.0, 0.1.0.", err.getvalue())

        # 2. adevv actualizar X.Y.Z ya instalada
        out = io.StringIO()
        err = io.StringIO()
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_q:
            mock_q.return_value = (["0.1.0", "0.2.0"], {"0.1.0": "c1", "0.2.0": "c2"}, None)
            code = main_cli(["actualizar", "0.1.0"], out=out, err=err)
            self.assertEqual(code, 0)
            self.assertIn("Adevv 0.1.0 ya está instalado.", out.getvalue())

        # 3. adevv actualizar X.Y.Z con bucles en marcha
        out = io.StringIO()
        err = io.StringIO()
        bucle_proc = [{"pid": 1234, "tipo": "bucle", "cwd": "C:\\SW\\Afinn", "cmd": "adevv orquestar"}]
        self.mock_bucles.return_value = bucle_proc
        with patch("adevv.updater.consultar_versiones_publicadas") as mock_q:
            mock_q.return_value = (["0.1.0", "0.2.0"], {"0.1.0": "c1", "0.2.0": "c2"}, None)
            code = main_cli(["actualizar", "0.2.0"], out=out, err=err)
            self.assertEqual(code, 1)
            self.assertIn("No se puede instalar 0.2.0 con bucles en marcha: bucle en C:\\SW\\Afinn.", err.getvalue())


if __name__ == "__main__":
    unittest.main()
