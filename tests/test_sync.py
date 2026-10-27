"""Pruebas unitarias y de integración para el almacén y la sincronización con arneses."""

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from adevv.store import (
    get_adevv_home,
    get_active_info,
    set_active_info,
    get_config,
    set_config,
    get_update_state,
    set_update_state,
    get_sync_registry,
    set_sync_registry,
    read_json,
    write_json_atomic,
)
from adevv.sync import (
    DESTINOS,
    calcular_sha256,
    obtener_estado_destino,
    planificar_sincronizacion,
    resolver_rutas_contenido,
    sincronizar_destinos,
    EstadoDestino,
)
from tests import aislamiento_telegram


class TestStore(unittest.TestCase):
    """Verifica el comportamiento del almacén de usuario ~/.adevv/ y la persistencia atómica."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.adevv_home = Path(self.temp_dir.name) / ".adevv"
        os.environ["ADEVV_HOME"] = str(self.adevv_home)

    def tearDown(self):
        os.environ.pop("ADEVV_HOME", None)
        self.temp_dir.cleanup()

    def test_atomic_write_and_read(self):
        target_file = self.adevv_home / "test.json"
        data = {"version": "0.1.0", "status": "ok"}
        write_json_atomic(target_file, data)

        read_data = read_json(target_file)
        self.assertEqual(read_data, data)

    def test_corrupted_json_returns_default(self):
        target_file = self.adevv_home / "corrupted.json"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("{este no es un json valido", encoding="utf-8")

        result = read_json(target_file, default={"default": True})
        self.assertEqual(result, {"default": True})

    def test_store_helpers_default_and_persistence(self):
        # Config por defecto
        cfg = get_config()
        self.assertTrue(cfg.get("auto_update", True))
        self.assertEqual(cfg.get("disabled_targets", []), [])

        # Actualizar config
        set_config({"auto_update": False, "disabled_targets": ["codex"]})
        updated_cfg = get_config()
        self.assertFalse(updated_cfg["auto_update"])
        self.assertIn("codex", updated_cfg["disabled_targets"])

        # Active info
        self.assertIsNone(get_active_info())
        set_active_info({"version": "0.1.0", "origen": "desarrollo"})
        self.assertEqual(get_active_info().get("version"), "0.1.0")

        # Update state
        self.assertEqual(get_update_state(), {})
        set_update_state({"last_applied_version": "0.1.0"})
        self.assertEqual(get_update_state().get("last_applied_version"), "0.1.0")

        # Sync registry
        self.assertIsNone(get_sync_registry("claude"))
        set_sync_registry("claude", {"version": "0.1.0", "files": {"skills/test/SKILL.md": "abc"}})
        reg = get_sync_registry("claude")
        self.assertEqual(reg.get("version"), "0.1.0")
        self.assertEqual(reg.get("files", {}).get("skills/test/SKILL.md"), "abc")


class TestSyncEngine(unittest.TestCase):
    """Verifica los casos de aceptación y reglas de sincronización en los arneses."""

    def setUp(self):
        entorno = patch.dict(os.environ)
        entorno.start()
        self.addCleanup(entorno.stop)
        os.environ.pop("ORQUESTAR_PASO", None)
        detector = patch("adevv.processes.hay_bucles_en_marcha", return_value=[])
        self.bucles = detector.start()
        self.addCleanup(detector.stop)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.adevv_home = self.root / ".adevv"
        os.environ["ADEVV_HOME"] = str(self.adevv_home)

        self.claude_home = self.root / ".claude"
        self.codex_home = self.root / ".codex"
        self.agy_home = self.root / ".gemini" / "config"

        os.environ["CLAUDE_HOME"] = str(self.claude_home)
        os.environ["CODEX_HOME"] = str(self.codex_home)
        os.environ["AGY_HOME"] = str(self.agy_home)

        # Crear versión ficticia instalada
        self.version_dir = self.adevv_home / "versions" / "0.1.0"
        self.version_dir.mkdir(parents=True, exist_ok=True)
        set_active_info({"version": "0.1.0", "origen": "publicada", "id": "0.1.0"})

        # Estructura de contenido en versión
        skills_dir = self.version_dir / "skills"
        agents_dir = self.version_dir / "agents"
        workflows_dir = self.version_dir / "workflows"

        skills_dir.mkdir()
        agents_dir.mkdir()
        workflows_dir.mkdir()

        # Skill commit y orquestar
        (skills_dir / "commit").mkdir()
        (skills_dir / "commit" / "SKILL.md").write_text("# Skill Commit\n", encoding="utf-8")

        (skills_dir / "orquestar").mkdir()
        (skills_dir / "orquestar" / "SKILL.md").write_text("# Skill Orquestar\n", encoding="utf-8")
        # Subdirectorio scripts y código que no debe sincronizarse
        (skills_dir / "orquestar" / "scripts").mkdir()
        (skills_dir / "orquestar" / "scripts" / "tool.py").write_text("print('code')\n", encoding="utf-8")
        (skills_dir / "orquestar" / "orquestar.py").write_text("print('engine')\n", encoding="utf-8")

        # Agente claude
        (agents_dir / "artemisa.md").write_text("# Artemisa\n", encoding="utf-8")

        # Agente codex con rutas relativas a resolver
        (agents_dir / "codex").mkdir()
        (agents_dir / "codex" / "hades.toml").write_text(
            'developer_instructions = """\n'
            "Lee .agents/agents/hades.md y actua.\n"
            "Las skills que cite estan en .agents/skills/<nombre>/SKILL.md.\n"
            '"""\n',
            encoding="utf-8",
        )

        # Workflow antigravity con rutas relativas a resolver
        (workflows_dir / "orquestar.md").write_text(
            "Usa la herramienta view_file en `../skills/orquestar/SKILL.md`.\n",
            encoding="utf-8",
        )

    def test_bucle_impide_escrituras_borrados_y_registro_incluso_forzando(self):
        """RF-F01-11: la guarda protege todos los archivos y registros compartidos."""
        self.claude_home.mkdir(parents=True)
        sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")
        destino = self.claude_home / "skills/commit/SKILL.md"
        registro = get_sync_registry("claude")
        anterior = destino.read_bytes()
        archivo_cambiado = self.claude_home / "skills/orquestar/SKILL.md"
        contenido_anterior = archivo_cambiado.read_bytes()
        (self.version_dir / "skills/commit/SKILL.md").unlink()
        (self.version_dir / "skills/orquestar/SKILL.md").write_text("nuevo", encoding="utf-8")
        self.bucles.return_value = [{"tipo": "bucle", "pid": 456, "cwd": "otro"}]
        for forzar in (False, True):
            with self.subTest(forzar=forzar):
                resultado = sincronizar_destinos(origen_dir=self.version_dir, version="0.2.0", forzar=forzar)["claude"]
                self.assertEqual(resultado["estado"], EstadoDestino.DESFASADO)
                self.assertEqual((resultado["escritos"], resultado["borrados"]), (0, 0))
                self.assertIn("bucles", resultado["detalle"])
                self.assertEqual(destino.read_bytes(), anterior)
                self.assertEqual(archivo_cambiado.read_bytes(), contenido_anterior)
                self.assertEqual(get_sync_registry("claude"), registro)
        self.bucles.return_value = []
        sincronizar_destinos(origen_dir=self.version_dir, version="0.2.0")
        self.assertFalse(destino.exists())
        self.assertEqual(archivo_cambiado.read_text(encoding="utf-8"), "nuevo")
        self.assertEqual(get_sync_registry("claude")["version"], "0.2.0")

    def test_paso_ancestro_no_detectado_tampoco_permite_copiar(self):
        """La variable del paso protege al bucle excluido por la enumeración."""
        self.claude_home.mkdir(parents=True)
        sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")
        destino = self.claude_home / "skills/commit/SKILL.md"
        anterior = destino.read_bytes()
        registro = get_sync_registry("claude")
        (self.version_dir / "skills/commit/SKILL.md").write_text("nuevo", encoding="utf-8")
        with patch.dict(os.environ, {"ORQUESTAR_PASO": "bug-fix"}):
            sincronizar_destinos(origen_dir=self.version_dir, version="0.2.0", forzar=True)
        self.assertEqual(destino.read_bytes(), anterior)
        self.assertEqual(get_sync_registry("claude"), registro)

    def tearDown(self):
        os.environ.pop("ADEVV_HOME", None)
        os.environ.pop("CLAUDE_HOME", None)
        os.environ.pop("CODEX_HOME", None)
        os.environ.pop("AGY_HOME", None)
        self.temp_dir.cleanup()

    def test_ca_f01_02_destino_sin_carpetas_confirmadas(self):
        """CA-F01-02 / RF-F01-03: Si existe la carpeta base pero no tiene carpetas confirmadas, no crea nada y reporta sin confirmar."""
        # Creamos base de Antigravity
        self.agy_home.mkdir(parents=True, exist_ok=True)

        # Simulamos que Antigravity no tiene carpetas confirmadas en esta versión
        import adevv.sync as sync_mod
        orig_dest = sync_mod.DESTINOS["agy"]["carpetas"]
        try:
            sync_mod.DESTINOS["agy"]["carpetas"] = {}
            res = sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")

            self.assertEqual(res["agy"]["estado"], EstadoDestino.NO_DETECTADO)
            self.assertEqual(res["agy"]["detalle"], "sin confirmar")
            # Comprobar que no se creó ninguna subcarpeta dentro de agy_home
            self.assertEqual(list(self.agy_home.iterdir()), [])
        finally:
            sync_mod.DESTINOS["agy"]["carpetas"] = orig_dest

    def test_ca_f01_03_rutas_absolutas_en_destinos_sin_relativas_prohibidas(self):
        """CA-F01-03 / RF-F01-04: Adaptadores y workflows resuelven rutas absolutas sin .agents/ ni ../."""
        self.claude_home.mkdir(parents=True, exist_ok=True)
        self.codex_home.mkdir(parents=True, exist_ok=True)
        self.agy_home.mkdir(parents=True, exist_ok=True)

        res = sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")
        self.assertEqual(res["claude"]["estado"], EstadoDestino.SINCRONIZADO)
        self.assertEqual(res["codex"]["estado"], EstadoDestino.SINCRONIZADO)
        self.assertEqual(res["agy"]["estado"], EstadoDestino.SINCRONIZADO)

        # Verificar adaptadores de Codex
        codex_hades = self.codex_home / "agents" / "hades.toml"
        self.assertTrue(codex_hades.exists())
        content_codex = codex_hades.read_text(encoding="utf-8")
        self.assertNotIn(".agents/", content_codex)
        self.assertNotIn("../", content_codex)
        # Debe contener la ruta absoluta a la versión instalada
        expected_agent_path = (self.version_dir / "agents" / "hades.md").as_posix()
        self.assertIn(expected_agent_path, content_codex)

        # Verificar workflow de Antigravity
        agy_wf = self.agy_home / "workflows" / "orquestar.md"
        self.assertTrue(agy_wf.exists())
        content_wf = agy_wf.read_text(encoding="utf-8")
        self.assertNotIn(".agents/", content_wf)
        self.assertNotIn("../", content_wf)
        expected_skill_path = (self.version_dir / "skills" / "orquestar" / "SKILL.md").as_posix()
        self.assertIn(expected_skill_path, content_wf)

        # Verificar que no se sincronizó código ni scripts/
        self.assertFalse((self.claude_home / "skills" / "orquestar" / "scripts").exists())
        self.assertFalse((self.claude_home / "skills" / "orquestar" / "orquestar.py").exists())

    def test_h01_resolver_rutas_contenido_formato_limpio_codex_y_workflows(self):
        """H-01 / CA-F01-03: Rutas como agents/hades.md o skills/task-dev/SKILL.md se resuelven a absolutas sin duplicar."""
        version_dir = Path("/tmp/adevv/versions/0.1.0")
        contenido_codex = b'developer_instructions = """\nLee agents/hades.md y actua.\nLas skills estan en skills/<nombre>/SKILL.md.\n"""'
        res_codex = resolver_rutas_contenido("agents/codex/hades.toml", contenido_codex, version_dir).decode("utf-8")
        self.assertIn("Lee /tmp/adevv/versions/0.1.0/agents/hades.md", res_codex)
        self.assertIn("skills estan en /tmp/adevv/versions/0.1.0/skills/<nombre>/SKILL.md", res_codex)
        self.assertEqual(res_codex.count("/tmp/adevv/versions/0.1.0"), 2)

        contenido_wf = b"Ejecuta solo los pasos definidos en `skills/task-dev/SKILL.md`.\n"
        res_wf = resolver_rutas_contenido("workflows/task-dev.md", contenido_wf, version_dir).decode("utf-8")
        self.assertIn("`/tmp/adevv/versions/0.1.0/skills/task-dev/SKILL.md`", res_wf)
        self.assertEqual(res_wf.count("/tmp/adevv/versions/0.1.0"), 1)

        # Probar que con prefijo .agents/ o ruta ya absoluta no se duplica el prefijo
        contenido_mixto = (
            b'Lee .agents/agents/hades.md y actua.\n'
            b'O lee /tmp/adevv/versions/0.1.0/agents/hades.md directamente.\n'
            b'Y `../skills/orquestar/SKILL.md` tambien.\n'
        )
        res_mixto = resolver_rutas_contenido("agents/codex/hades.toml", contenido_mixto, version_dir).decode("utf-8")
        self.assertNotIn("/tmp/adevv/versions/0.1.0/tmp/adevv/versions/0.1.0", res_mixto)
        self.assertNotIn("/tmp/adevv/versions/0.1.0/.agents", res_mixto)
        self.assertEqual(res_mixto.count("/tmp/adevv/versions/0.1.0"), 3)

    def test_ca_f01_04_skill_ajena_no_se_sobrescribe_y_deja_incompleto(self):
        """CA-F01-04 / RF-F01-05 / RF-F01-06 / RF-F01-13: Skill ajena produce conflicto alien, no se toca y destino queda INCOMPLETO."""
        self.claude_home.mkdir(parents=True, exist_ok=True)
        alien_skill = self.claude_home / "skills" / "commit" / "SKILL.md"
        alien_skill.parent.mkdir(parents=True, exist_ok=True)
        alien_skill.write_text("# Mi skill commit ajena\n", encoding="utf-8")

        res = sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")

        self.assertEqual(res["claude"]["estado"], EstadoDestino.INCOMPLETO)
        self.assertIn("skills/commit/SKILL.md", res["claude"]["conflictos"])
        # No se ha modificado la ajena
        self.assertEqual(alien_skill.read_text(encoding="utf-8"), "# Mi skill commit ajena\n")
        # El resto de skills sí se escribieron
        self.assertTrue((self.claude_home / "skills" / "orquestar" / "SKILL.md").exists())

    def test_ca_f01_05_archivo_editado_a_mano_y_opcion_forzar(self):
        """CA-F01-05 / RF-F01-06: Archivo editado a mano queda INCOMPLETO, y con --forzar se recupera a SINCRONIZADO."""
        self.claude_home.mkdir(parents=True, exist_ok=True)

        # Primera sincronización limpia
        sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")

        # Modificación a mano de la skill orquestar
        orq_dest = self.claude_home / "skills" / "orquestar" / "SKILL.md"
        orq_dest.write_text("# Editado a mano por el usuario\n", encoding="utf-8")

        # Sincronización normal -> detecta conflicto
        res1 = sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0", forzar=False)
        self.assertEqual(res1["claude"]["estado"], EstadoDestino.INCOMPLETO)
        self.assertEqual(orq_dest.read_text(encoding="utf-8"), "# Editado a mano por el usuario\n")

        # Sincronización con forzar=True -> sobrescribe archivo de Adevv
        res2 = sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0", forzar=True)
        self.assertEqual(res2["claude"]["estado"], EstadoDestino.SINCRONIZADO)
        self.assertEqual(orq_dest.read_text(encoding="utf-8"), "# Skill Orquestar\n")

    def test_ca_f01_06_carpetas_ajenas_y_ocultas_no_se_tocan(self):
        """CA-F01-06 / RF-F01-05: Carpetas ajenas y ocultas (.system, synced) permanecen inalteradas."""
        self.claude_home.mkdir(parents=True, exist_ok=True)
        self.codex_home.mkdir(parents=True, exist_ok=True)

        synced_file = self.claude_home / "skills" / "synced" / "data.txt"
        synced_file.parent.mkdir(parents=True, exist_ok=True)
        synced_file.write_text("datos de synced\n", encoding="utf-8")

        system_file = self.codex_home / "skills" / ".system" / "core.json"
        system_file.parent.mkdir(parents=True, exist_ok=True)
        system_file.write_text("{\"system\": true}\n", encoding="utf-8")

        sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")

        self.assertTrue(synced_file.exists())
        self.assertEqual(synced_file.read_text(encoding="utf-8"), "datos de synced\n")
        self.assertTrue(system_file.exists())
        self.assertEqual(system_file.read_text(encoding="utf-8"), "{\"system\": true}\n")

    def test_ca_f01_07_ruta_de_registro_fuera_del_destino_se_ignora(self):
        """CA-F01-07 / RF-F01-05: Una ruta en el registro que resuelva fuera del destino se ignora y no borra nada."""
        self.codex_home.mkdir(parents=True, exist_ok=True)

        nota_externa = self.root / "nota.md"
        nota_externa.write_text("mi nota importante fuera del destino\n", encoding="utf-8")

        # Inyectar registro malicioso o corrupto en codex
        set_sync_registry("codex", {
            "version": "0.0.9",
            "files": {
                "../../nota.md": calcular_sha256(nota_externa.read_bytes()),
            }
        })

        res = sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")
        self.assertTrue(nota_externa.exists())
        self.assertEqual(nota_externa.read_text(encoding="utf-8"), "mi nota importante fuera del destino\n")
        self.assertTrue(len(res["codex"]["rutas_ignoradas"]) > 0)

    def test_ca_f01_08_borrado_de_skill_retirada_no_recursivo(self):
        """CA-F01-08 / RF-F01-07: Se borran los archivos de una skill retirada, pero la carpeta con archivos de usuario se conserva."""
        self.claude_home.mkdir(parents=True, exist_ok=True)

        # Versión 0.1.0 previa con seo-audit
        seo_skill_file = self.claude_home / "skills" / "seo-audit" / "SKILL.md"
        seo_skill_file.parent.mkdir(parents=True, exist_ok=True)
        seo_content = b"# Skill SEO Audit\n"
        seo_skill_file.write_bytes(seo_content)
        seo_sha = calcular_sha256(seo_content)

        # Nota del usuario dentro de la carpeta
        user_notes = self.claude_home / "skills" / "seo-audit" / "notas.txt"
        user_notes.write_text("mis notas de seo\n", encoding="utf-8")

        set_sync_registry("claude", {
            "version": "0.1.0",
            "files": {
                "skills/seo-audit/SKILL.md": seo_sha,
            }
        })

        # Ahora sincronizamos la versión actual (que NO tiene seo-audit)
        sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")

        # El archivo de la skill fue retirado
        self.assertFalse(seo_skill_file.exists())
        # Pero la carpeta y el archivo del usuario continúan
        self.assertTrue(user_notes.exists())
        self.assertEqual(user_notes.read_text(encoding="utf-8"), "mis notas de seo\n")

    def test_ca_f01_09_destino_sin_registro_o_corrupto_adopta_identicos(self):
        """CA-F01-09 / RF-F01-09: Destino sin registro adopta archivos con huella idéntica y marca conflicto en los distintos."""
        self.codex_home.mkdir(parents=True, exist_ok=True)

        # Creamos en codex copia idéntica de commit y distinta de orquestar
        commit_dest = self.codex_home / "skills" / "commit" / "SKILL.md"
        commit_dest.parent.mkdir(parents=True, exist_ok=True)
        commit_dest.write_text("# Skill Commit\n", encoding="utf-8")  # Identica

        orq_dest = self.codex_home / "skills" / "orquestar" / "SKILL.md"
        orq_dest.parent.mkdir(parents=True, exist_ok=True)
        orq_dest.write_text("# Skill Orquestar Diferente\n", encoding="utf-8")  # Distinta

        # Registro no existe
        res = sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")
        self.assertEqual(res["codex"]["estado"], EstadoDestino.INCOMPLETO)
        self.assertIn("skills/orquestar/SKILL.md", res["codex"]["conflictos"])
        self.assertNotIn("skills/commit/SKILL.md", res["codex"]["conflictos"])

        # Registro guardado adopta la huella de commit
        reg = get_sync_registry("codex")
        self.assertIn("skills/commit/SKILL.md", reg["files"])
        self.assertNotIn("skills/orquestar/SKILL.md", reg["files"])

    def test_ca_f01_13_sincronizar_dos_veces_informa_sin_cambios(self):
        """CA-F01-13 / RF-F01-03: La segunda sincronización consecutiva informa sin cambios."""
        self.claude_home.mkdir(parents=True, exist_ok=True)
        self.codex_home.mkdir(parents=True, exist_ok=True)

        res1 = sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")
        self.assertFalse(res1["claude"]["sin_cambios"])

        res2 = sincronizar_destinos(origen_dir=self.version_dir, version="0.1.0")
        self.assertTrue(res2["claude"]["sin_cambios"])
        self.assertTrue(res2["codex"]["sin_cambios"])


if __name__ == "__main__":
    unittest.main()
