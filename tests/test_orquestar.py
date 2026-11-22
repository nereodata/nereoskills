"""Pruebas rápidas y completas del núcleo ligero de orquestación (v1.3)."""

import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests import aislamiento_telegram  # noqa: F401

SPEC = importlib.util.spec_from_file_location(
    "orquestar", Path(__file__).resolve().parents[1] / "skills" / "orquestar" / "orquestar.py"
)
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


class OrquestadorLigeroTests(unittest.TestCase):
    """Verifica selección de estado, revisión directa sin secretarios, modelos/cuotas, métricas y preguntas."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.escribir("task_config.yaml", 'project:\n  name: Demo\n  prefix: "DEM"\n  version: "v0.1.0"\n')
        for doc in ("requirements.md", "req_analysis.md", "platform_plan.md", "work_plan.md"):
            self.escribir(f"docs/requirements/{doc}", "# ok\n")
        self.escribir("docs/requirements/platform_review.md", "**Veredicto:** APROBADO\n")

    def escribir(self, rel: str, texto: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")
        return p

    def tarea(
        self,
        iid: str,
        status: str = "planned",
        version: str = "v0.1.0",
        dif: str = "media",
        deps=(),
        weight: int = 100,
        extra: str = "",
    ):
        carpeta = "bugs" if iid.startswith("B-") else "tasks"
        deps_txt = json.dumps(list(deps))
        return self.escribir(
            f"docs/plan/{carpeta}/{iid}.md",
            f'---\nid: {iid}\ntitle: "{iid}"\nversion: "{version}"\nstatus: {status}\n'
            f"dificultad: {dif}\nweight: {weight}\ndepende_de: {deps_txt}\n{extra}---\n\n# {iid}\n",
        )

    def test_selector_prioriza_bugs_respeta_dependencias_y_cierra_version(self):
        self.tarea("T-DEM-0001", "planned", weight=10)
        self.tarea("T-DEM-0002", "planned", deps=("T-DEM-0001",), weight=5)
        self.tarea("B-DEM-0001", "planned", weight=50)
        self.tarea("T-DEM-0010", "planned", version="v0.2.0", weight=10)

        with patch.object(motor, "git", return_value="main"):
            self.assertEqual(motor.estado(self.root), ("PASO", "start-version", "v0.1"))

        with patch.object(motor, "git", return_value="release/v0.1"):
            # Bug va antes que tarea aunque tenga mayor weight cuando ambos están planned
            self.assertEqual(motor.estado(self.root), ("PASO", "bug-fix", "B-DEM-0001", "release/v0.1"))

            # Una tarea in_progress tiene prioridad sobre un bug planned
            self.tarea("T-DEM-0001", "in_progress", weight=10)
            self.assertEqual(motor.estado(self.root), ("PASO", "task-dev", "T-DEM-0001", "release/v0.1"))
            self.tarea("T-DEM-0001", "planned", weight=10)
            self.assertEqual(motor.estado(self.root), ("PASO", "bug-fix", "B-DEM-0001", "release/v0.1"))

            # Completar bug y aprobar revisión -> pasa a T-DEM-0001 (T-DEM-0002 depende de T-DEM-0001)
            self.tarea("B-DEM-0001", "completed")
            self.escribir("docs/review/code_reviews/B-DEM-0001-code-review.md", "**Veredicto:** APROBADO\n")
            self.assertEqual(motor.estado(self.root), ("PASO", "task-dev", "T-DEM-0001", "release/v0.1"))

            self.tarea("T-DEM-0001", "completed")
            self.escribir("docs/review/code_reviews/T-DEM-0001-code-review.md", "**Veredicto:** APROBADO\n")
            self.assertEqual(motor.estado(self.root), ("PASO", "task-dev", "T-DEM-0002", "release/v0.1"))

            self.tarea("T-DEM-0002", "completed")
            self.escribir("docs/review/code_reviews/T-DEM-0002-code-review.md", "**Veredicto:** APROBADO\n")
            self.assertEqual(motor.estado(self.root), ("PASO", "revisar-version", "v0.1", "release/v0.1"))

            self.escribir("docs/review/versions/v0.1-arquitectura.md", "**Veredicto:** APROBADO\n")
            est = motor.estado(self.root)
            self.assertEqual(est[0], "PARAR")
            self.assertTrue(est[1].startswith("Versión v0.1 terminada."))

    def test_cache_verificacion_por_huella_producto_ignora_cambios_en_docs_plan_y_review(self):
        self.escribir("app.py", "X = 1\n")
        ejecuciones = []

        def fake_run(cmd, **kw):
            ejecuciones.append(cmd)
            return motor.subprocess.CompletedProcess(cmd, 0)

        with patch.object(motor.subprocess, "run", side_effect=fake_run):
            self.assertEqual(motor.verificar(self.root, "python -m unittest"), 0)
            self.assertEqual(len(ejecuciones), 1)

            # Editar backlog o informes de revisión NO invalida la huella de producto
            self.escribir("docs/review/versions/v0.1-arquitectura.md", "**Veredicto:** APROBADO\n")
            self.tarea("T-DEM-0099", "backlog", version="")
            self.assertEqual(motor.verificar(self.root, "python -m unittest"), 0)
            self.assertEqual(len(ejecuciones), 1)

            # Editar código de producto SÍ reejecuta la verificación
            self.escribir("app.py", "X = 2\n")
            self.assertEqual(motor.verificar(self.root, "python -m unittest"), 0)
            self.assertEqual(len(ejecuciones), 2)

    def test_modelos_dificultad_perfil_cuota_y_conmutacion_a_reserva(self):
        cfg = {
            "artemisa": {
                "harness": "codex",
                "model": "gpt-6.1-sol",
                "dificultad": {
                    "sencilla": {"harness": "agy", "model": "gemini-3.8-flash", "effort": "low"},
                    "dificil": {
                        "harness": "claude",
                        "model": "claude-opus-5-5",
                        "effort": "high",
                        "reserva": [{"harness": "agy", "model": "gemini-4-carbon", "effort": "medium"}],
                    },
                },
            }
        }
        self.escribir("orchestration.json", json.dumps(cfg))
        self.tarea("T-DEM-0001", "planned", dif="sencilla")
        self.tarea("T-DEM-0002", "planned", dif="dificil")
        self.tarea("T-DEM-0003", "planned", dif="media", extra='perfil: {"harness": "agy", "model": "custom-m"}\n')

        self.assertEqual(
            motor.perfiles.rol_de(self.root, "task-dev", "sencilla", "T-DEM-0001", motor.fichero_de)[1]["model"],
            "gemini-3.8-flash",
        )
        self.assertEqual(
            motor.perfiles.rol_de(self.root, "task-dev", "media", "T-DEM-0003", motor.fichero_de)[1]["model"],
            "custom-m",
        )

        # Redondeo math.ceil en espera de cuota (ej. 299.2s -> 300s)
        self.assertEqual(motor.espera_cuota("429 rate limit exceeded, resets in 299.2s"), 300)

        # Conmutación inmediata de claude (sin cuota) a reserva agy/gemini-4-carbon
        invocados = []

        def fake_lanzar(cmd, root, harness, **kw):
            invocados.append((harness, cmd))
            if harness == "claude":
                return 1, {"modelos": {}, "duracion_s": 1}, "Error: rate limit exceeded, try again in 120s"
            return (
                0,
                {
                    "modelos": {
                        "gemini-4-carbon": {"entrada": 100, "salida": 40, "cache_leida": 200, "razonamiento": 10}
                    },
                    "duracion_s": 5,
                },
                "Hecho",
            )

        with (
            patch.object(motor, "buscar_ejecutable", side_effect=lambda x: x),
            patch.object(motor, "lanzar", side_effect=fake_lanzar),
        ):
            cod, m, sal = motor._invocar_con_reservas(self.root, "artemisa", "task-dev", "T-DEM-0002", "haz T2")

        self.assertEqual(cod, 0)
        self.assertEqual([h for h, _ in invocados], ["claude", "agy"])
        self.assertEqual(m["modelo"], "gemini-4-carbon")
        # Claude queda registrado como bloqueado por cuota en consumo_cuotas
        _, bloqueos = motor.consumo_cuotas(self.root)
        self.assertIn(("claude", "claude-opus-5-5"), bloqueos)

    def test_bucle_ejecuta_hades_directo_sin_secretario_y_no_repite_suite_al_commitear_arquitectura(self):
        self.escribir("app.py", "OK = True\n")
        self.tarea("T-DEM-0001", "completed")
        llamadas_rol = []
        ejecuciones_suite = []

        def fake_invocar(root, rol, paso, iid, prompt, cmd_override=None):
            llamadas_rol.append((rol, paso, iid))
            if paso == "revisar-tarea":
                self.escribir(
                    "docs/review/code_reviews/T-DEM-0001-code-review.md", "**Veredicto:** APROBADO\nTodo bien.\n"
                )
            elif paso == "revisar-version":
                self.escribir("docs/review/versions/v0.1-arquitectura.md", "**Veredicto:** APROBADO\nSin hallazgos.\n")
            return (
                0,
                {
                    "modelos": {
                        "gemini-4-carbon": {"entrada": 500, "salida": 80, "cache_leida": 1000, "razonamiento": 20}
                    },
                    "duracion_s": 4,
                },
                "APROBADO",
            )

        def fake_run(cmd, **kw):
            if cmd == "suite-falsa":
                ejecuciones_suite.append(cmd)
            return motor.subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(motor, "_invocar_con_reservas", side_effect=fake_invocar),
            patch.object(motor.subprocess, "run", side_effect=fake_run),
            patch.object(motor, "avisar"),
        ):
            rc = motor.bucle(self.root, test_cmd="suite-falsa", espera_max=0)

        self.assertEqual(rc, 0)
        # Hades invocado directamente sin ningún paso intermedio de Artemisa/Atenea
        self.assertEqual(llamadas_rol, [("hades", "revisar-tarea", "T-DEM-0001"), ("hades", "revisar-version", "v0.1")])
        # Suite ejecutada UNA SOLA VEZ aunque revisar-version escribió v0.1-arquitectura.md
        self.assertEqual(len(ejecuciones_suite), 1)
        # Huella sellada automáticamente
        self.assertIn(
            "Producto revisado:",
            (self.root / "docs/review/code_reviews/T-DEM-0001-code-review.md").read_text(encoding="utf-8"),
        )

        # Métricas consultables sin errores
        buf = io.StringIO()
        self.assertEqual(motor.metricas.mostrar(self.root, motor.backlog(self.root), "ultima", None, buf), 0)
        self.assertIn("T-DEM-0001", buf.getvalue())

    def test_rechazo_hades_escala_dificultad_sin_bloquear_y_reintenta(self):
        self.tarea("T-DEM-0001", "completed", dif="sencilla")
        dificultades_dev = []
        rechazos = 0

        def fake_invocar(root, rol, paso, iid, prompt, cmd_override=None):
            nonlocal rechazos
            if paso == "revisar-tarea":
                rechazos += 1
                if rechazos <= 5:
                    self.escribir(
                        "docs/review/code_reviews/T-DEM-0001-code-review.md",
                        "**Veredicto:** RECHAZADO\n- 🔴 **CRÍTICO** (para: desarrollador): Falta X.\n",
                    )
                    return 0, {"modelos": {}, "duracion_s": 2}, "RECHAZADO"
                self.escribir("docs/review/code_reviews/T-DEM-0001-code-review.md", "**Veredicto:** APROBADO\n")
                return 0, {"modelos": {}, "duracion_s": 2}, "APROBADO"
            if paso == "revisar-version":
                self.escribir("docs/review/versions/v0.1-arquitectura.md", "**Veredicto:** APROBADO\n")
                return 0, {"modelos": {}, "duracion_s": 2}, "APROBADO"
            dif_actual = motor.perfiles.dificultad_de(root, iid, motor.fichero_de)
            dificultades_dev.append(dif_actual)
            self.tarea("T-DEM-0001", "completed", dif=dif_actual)
            return 0, {"modelos": {}, "duracion_s": 2}, "Intento"

        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(motor, "_invocar_con_reservas", side_effect=fake_invocar),
            patch.object(motor, "avisar"),
        ):
            rc = motor.bucle(self.root, reintentos=1, espera_max=0)

        self.assertEqual(rc, 0)
        fm = motor.frontmatter(motor.fichero_de(self.root, "T-DEM-0001"))
        self.assertEqual(fm["status"], "completed")
        self.assertEqual(fm["dificultad"], "dificil")
        self.assertEqual(dificultades_dev, ["sencilla", "media", "media", "dificil", "dificil"])

    def test_rechazo_hades_bloquea_si_pide_humano_explicitamente(self):
        self.tarea("T-DEM-0001", "completed")

        def fake_invocar(root, rol, paso, iid, prompt, cmd_override=None):
            self.escribir(
                "docs/review/code_reviews/T-DEM-0001-code-review.md",
                "**Veredicto:** RECHAZADO\n- 🔴 **CRÍTICO** (para: humano): Falta credencial externa.\n",
            )
            return 0, {"modelos": {}, "duracion_s": 2}, "RECHAZADO"

        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(motor, "_invocar_con_reservas", side_effect=fake_invocar),
            patch.object(motor, "avisar"),
        ):
            rc = motor.bucle(self.root, reintentos=2, espera_max=0)

        self.assertEqual(rc, 1)
        fm = motor.frontmatter(motor.fichero_de(self.root, "T-DEM-0001"))
        self.assertEqual(fm["status"], "blocked")
        self.assertEqual(fm["pendiente_de"], "humano")

    def test_pide_humano_detecta_solo_solicitud_explicita(self):
        self.assertTrue(motor.pide_humano("**Veredicto:** RECHAZADO\n- 🔴 (para: humano): Falta token.\n"))
        self.assertTrue(motor.pide_humano("**para:** humano\n"))
        self.assertFalse(motor.pide_humano("**Veredicto:** RECHAZADO\n- 🔴 (para: desarrollador): Falla test.\n"))
        self.assertFalse(motor.pide_humano("para: desarrollador|especificador|humano\n"))
        self.assertFalse(motor.pide_humano("```\npara: humano\n```\n"))

    def test_preguntas_y_respuestas_humanas(self):
        self.tarea("T-DEM-0001", "in_progress")
        qid = motor.intervencion.solicitar(self.root, motor, "T-DEM-0001", "¿Usamos SQLite o Postgres?", "release/v0.1")
        self.assertEqual(qid, "Q-0001")
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, "T-DEM-0001"))["status"], "blocked")
        self.assertIn("Q-0001", motor.intervencion.consulta(self.root))

        msg = motor.responder_pregunta(self.root, "123", "Q-0001 SQLite")
        self.assertIn("vuelve a planned", msg)
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, "T-DEM-0001"))["status"], "planned")
        # Idempotencia al repetir respuesta
        self.assertIn("ya estaba respondida", motor.responder_pregunta(self.root, "123", "Q-0001 SQLite"))

    def test_preguntas_legacy_con_tarea_id_son_retrocompatibles(self):
        self.tarea("T-AFN-0006", "blocked")
        (self.root / "orquestar_preguntas.json").write_text(
            json.dumps(
                [
                    {
                        "id": "Q-AFN-0006",
                        "tarea_id": "T-AFN-0006",
                        "pregunta": "¿Confirmas el despliegue?",
                        "rama": "release/v1.0",
                        "estado": "pendiente",
                    }
                ]
            ),
            encoding="utf-8",
        )
        listado = motor.intervencion.consulta(self.root)
        self.assertIn("Q-AFN-0006", listado)
        self.assertIn("T-AFN-0006", listado)
        self.assertEqual(
            motor.intervencion.solicitar(self.root, motor, "T-AFN-0006", "Otra"),
            "Q-AFN-0006",
        )
        ok, msg = motor.intervencion.responder(self.root, motor, "Q-AFN-0006", "Sí, adelante", "123")
        self.assertTrue(ok, msg)
        self.assertIn("T-AFN-0006 vuelve a planned", msg)
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, "T-AFN-0006"))["status"], "planned")

    def test_lanzar_timeout_devuelve_124_y_corta_proceso(self):
        cmd = [sys.executable, "-c", "import time; print('inicio', flush=True); time.sleep(30)"]
        cod, m, sal = motor.lanzar(cmd, self.root, "agy", timeout=0.4, gracia_cierre=0.05)
        self.assertEqual(cod, 124)
        self.assertTrue(m.get("timeout"))
        self.assertIn("inicio", sal)

    def test_huella_producto_detecta_cambios_en_skills_orquestar_e_ignora_estado_raiz(self):
        self.escribir("skills/orquestar/orquestar.py", "V = 1\n")
        h1 = motor.huella_producto(self.root)
        # Archivos efímeros de estado en raíz NO alteran la huella
        self.escribir("orquestar.log", "linea\n")
        self.escribir("orquestar_metricas.jsonl", "{}\n")
        self.assertEqual(motor.huella_producto(self.root), h1)
        # Editar skills/orquestar/orquestar.py SÍ altera la huella
        self.escribir("skills/orquestar/orquestar.py", "V = 2\n")
        self.assertNotEqual(motor.huella_producto(self.root), h1)

    def test_cli_agentes_metricas_version_filtro_y_rol_explicito_hades(self):
        self.escribir(
            "orchestration.json",
            json.dumps(
                {
                    "atenea": {"harness": "agy", "model": "m-atenea"},
                    "hades": {"harness": "codex", "model": "m-hades"},
                }
            ),
        )
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            self.assertEqual(motor.main(["--root", str(self.root), "--agentes"]), 0)
            self.assertEqual(motor.main(["--root", str(self.root), "--metrics", "--version-filtro", "v0.1"]), 0)
        self.assertIn("m-hades", out.getvalue())

        # --agente hades usa el perfil de hades incluso si ORQUESTAR_PASO=task-dev
        captura = {}

        def fake_lanzar(cmd, root, harness, **kw):
            captura["cmd"] = cmd
            captura["harness"] = harness
            captura["entrada"] = kw.get("entrada")
            return 0, {"modelos": {}, "duracion_s": 1}, "**Veredicto:** APROBADO"

        with (
            patch.dict(motor.os.environ, {"ORQUESTAR_PASO": "task-dev"}, clear=False),
            patch.object(motor, "buscar_ejecutable", return_value="codex-bin"),
            patch.object(motor, "lanzar", side_effect=fake_lanzar),
        ):
            self.assertEqual(motor.agente(self.root, "hades", "Revisa T-DEM-0001"), 0)
        self.assertEqual(captura["harness"], "codex")
        self.assertIn("m-hades", captura["cmd"])
        self.assertIn("Revisa T-DEM-0001", captura["entrada"])

    def test_revisar_version_crea_revision_md_y_detecta_arquitectura_rechazada(self):
        self.tarea("T-DEM-0001", "completed")
        self.escribir("docs/review/code_reviews/T-DEM-0001-code-review.md", "**Veredicto:** APROBADO\n")

        # Un informe de arquitectura RECHAZADO pasa a resolver-version en vez de parar en seco
        self.escribir("docs/review/versions/v0.1-arquitectura.md", "**Veredicto:** RECHAZADO\n")
        with patch.object(motor, "git", return_value="release/v0.1"):
            est = motor.estado(self.root)
        self.assertEqual(est, ("PASO", "resolver-version", "v0.1", "release/v0.1"))

        # Al aprobar revisar-version, se genera automáticamente v0.1-revision.md
        (self.root / "docs/review/versions/v0.1-arquitectura.md").unlink()
        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(
                motor,
                "_invocar_con_reservas",
                return_value=(0, {"modelos": {}, "duracion_s": 1}, "**Veredicto:** APROBADO\nTodo limpio.\n"),
            ),
            patch.object(motor, "avisar"),
        ):
            self.assertEqual(motor.bucle(self.root, espera_max=0), 0)
        self.assertTrue((self.root / "docs/review/versions/v0.1-revision.md").is_file())

    def test_revisar_version_rechazada_resuelve_autonomamente_y_registra_deuda(self):
        self.escribir("app.py", "V = 1\n")
        self.tarea("T-DEM-0001", "completed")
        self.escribir("docs/review/code_reviews/T-DEM-0001-code-review.md", "**Veredicto:** APROBADO\n")
        pasos = []

        def fake_invocar(root, rol, paso, iid, prompt, cmd_override=None):
            pasos.append((rol, paso, iid))
            if paso == "revisar-version" and len([p for p in pasos if p[1] == "revisar-version"]) == 1:
                self.escribir(
                    "docs/review/versions/v0.1-arquitectura.md",
                    "**Veredicto:** RECHAZADO\n\n"
                    "### 🟠 H-01 · Falta validación en app.py\n"
                    "- **para:** desarrollador\n"
                    "- **destino:** resolver\n\n"
                    "### 🟡 H-02 · Refactorizar helper secundario\n"
                    "- **Severidad:** 🟡 MEDIA · `destino: registrar`\n"
                    "- **Detalle:** Conviene extraer helper en otro ciclo.\n\n"
                    "### 🔵 H-03 · Detalle tipográfico menor\n"
                    "- **Severidad:** 🔵 BAJA · `destino: descartar`\n",
                )
                return 0, {"modelos": {}, "duracion_s": 1}, "RECHAZADO"
            if paso == "resolver-version":
                self.escribir("app.py", "V = 2\n")
                return 0, {"modelos": {}, "duracion_s": 1}, "Resuelto"
            self.escribir("docs/review/versions/v0.1-arquitectura.md", "**Veredicto:** APROBADO\nSin hallazgos.\n")
            return 0, {"modelos": {}, "duracion_s": 1}, "APROBADO"

        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(motor, "_invocar_con_reservas", side_effect=fake_invocar),
            patch.object(motor, "avisar"),
        ):
            rc = motor.bucle(self.root, espera_max=0)

        self.assertEqual(rc, 0)
        self.assertEqual(
            pasos,
            [
                ("hades", "revisar-version", "v0.1"),
                ("artemisa", "resolver-version", "v0.1"),
                ("hades", "revisar-version", "v0.1"),
            ],
        )
        # Solo H-02 (destino: registrar) genera deuda en backlog sin versión; H-03 se descarta
        bugs = [i for i in motor.backlog(self.root) if i["id"].startswith("B-")]
        self.assertEqual(len(bugs), 1)
        self.assertEqual(bugs[0]["status"], "backlog")
        self.assertEqual(bugs[0]["version"], "")
        self.assertIn("Refactorizar helper secundario", bugs[0]["title"])

    def test_revisar_version_escala_con_preguntar_y_reanuda_tras_respuesta(self):
        self.escribir("app.py", "V = 1\n")
        self.tarea("T-DEM-0001", "completed")
        self.escribir("docs/review/code_reviews/T-DEM-0001-code-review.md", "**Veredicto:** APROBADO\n")

        def invocar_con_pregunta(root, rol, paso, iid, prompt, cmd_override=None):
            if paso == "revisar-version":
                self.escribir(
                    "docs/review/versions/v0.1-arquitectura.md",
                    "**Veredicto:** RECHAZADO\n- 🟠 (para: desarrollador): Definir política de compatibilidad.\n",
                )
                return 0, {"modelos": {}, "duracion_s": 1}, "RECHAZADO"
            if paso == "resolver-version":
                motor.intervencion.solicitar(
                    self.root, motor, "v0.1", "¿Mantenemos compatibilidad con v0?", "release/v0.1"
                )
                return 0, {"modelos": {}, "duracion_s": 1}, "Pregunta registrada"
            return 0, {"modelos": {}, "duracion_s": 1}, "OK"

        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(motor, "_invocar_con_reservas", side_effect=invocar_con_pregunta),
            patch.object(motor, "avisar"),
        ):
            rc = motor.bucle(self.root, espera_max=0)

        self.assertEqual(rc, 1)
        self.assertIn("Q-0001", motor.intervencion.consulta(self.root))
        with patch.object(motor, "git", return_value="release/v0.1"):
            self.assertEqual(motor.estado(self.root)[0], "PARAR")

        # Al responder, se desbloquea y el prompt de resolver-version incluye la decisión humana
        msg = motor.responder_pregunta(self.root, "123", "Q-0001 Sí, mantener compatibilidad")
        self.assertIn("Q-0001", msg)
        with patch.object(motor, "git", return_value="release/v0.1"):
            self.assertEqual(motor.estado(self.root), ("PASO", "resolver-version", "v0.1", "release/v0.1"))
        self.assertIn("Sí, mantener compatibilidad", motor.construir_prompt_paso(self.root, "resolver-version", "v0.1"))

        def invocar_tras_respuesta(root, rol, paso, iid, prompt, cmd_override=None):
            if paso == "resolver-version":
                self.escribir("app.py", "V = 2\n")
                return 0, {"modelos": {}, "duracion_s": 1}, "Aplicada decisión"
            self.escribir("docs/review/versions/v0.1-arquitectura.md", "**Veredicto:** APROBADO\n")
            return 0, {"modelos": {}, "duracion_s": 1}, "APROBADO"

        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(motor, "_invocar_con_reservas", side_effect=invocar_tras_respuesta),
            patch.object(motor, "avisar"),
        ):
            self.assertEqual(motor.bucle(self.root, espera_max=0), 0)

    def test_revisar_version_respeta_limite_de_rondas(self):
        self.escribir("app.py", "V = 1\n")
        self.tarea("T-DEM-0001", "completed")
        self.escribir("docs/review/code_reviews/T-DEM-0001-code-review.md", "**Veredicto:** APROBADO\n")
        contador = {"rev": 0, "res": 0}

        def invocar_siempre_rechaza(root, rol, paso, iid, prompt, cmd_override=None):
            if paso == "revisar-version":
                contador["rev"] += 1
                self.escribir(
                    "docs/review/versions/v0.1-arquitectura.md",
                    f"**Veredicto:** RECHAZADO\n- 🔴 (para: desarrollador): Fallo ronda {contador['rev']}.\n",
                )
                return 0, {"modelos": {}, "duracion_s": 1}, "RECHAZADO"
            contador["res"] += 1
            self.escribir("app.py", f"V = {contador['res'] + 1}\n")
            return 0, {"modelos": {}, "duracion_s": 1}, "Intento"

        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(motor, "_invocar_con_reservas", side_effect=invocar_siempre_rechaza),
            patch.object(motor, "avisar"),
        ):
            rc = motor.bucle(self.root, espera_max=0, max_rondas_version=2)

        self.assertEqual(rc, 1)
        self.assertEqual(contador["res"], 2)
        self.assertEqual(contador["rev"], 3)

    def test_bucle_primer_plano_escribe_orquestar_log_sin_duplicar_si_ya_redirigido(self):
        import contextlib

        self.tarea("T-DEM-0001", "completed")
        buf = io.StringIO()
        with (
            patch.object(motor, "git", return_value="main"),
            patch.object(motor, "avisar"),
            contextlib.redirect_stdout(buf),
        ):
            rc = motor.bucle(self.root, espera_max=0)
            self.assertIs(sys.stdout, buf)
        self.assertEqual(rc, 0)
        self.assertIn("[orquestar] FIN:", buf.getvalue())
        log_path = self.root / motor.LOG
        self.assertTrue(log_path.is_file())
        self.assertIn("[orquestar] FIN:", log_path.read_text(encoding="utf-8"))

        # Si stdout ya apunta a orquestar.log (como en --fondo), no se duplica la salida
        log_path.write_text("", encoding="utf-8")
        with log_path.open("a", encoding="utf-8") as fh, contextlib.redirect_stdout(fh):
            with motor._salida_con_log(self.root):
                print("linea-unica", flush=True)
            self.assertIs(sys.stdout, fh)
        self.assertEqual(log_path.read_text(encoding="utf-8").splitlines(), ["linea-unica"])

        # Si el pipe stdout se cierra o falla al codificar, _DuplicadorSalida sigue escribiendo en orquestar.log
        class PipeRoto:
            def write(self, _):
                raise BrokenPipeError("pipe cerrado")

            def flush(self):
                raise BrokenPipeError("pipe cerrado")

        log_path.write_text("", encoding="utf-8")
        roto = PipeRoto()
        with contextlib.redirect_stdout(roto):
            with motor._salida_con_log(self.root):
                print("sobrevive-pipe-roto 🚀", flush=True)
            self.assertIs(sys.stdout, roto)
        self.assertIn("sobrevive-pipe-roto 🚀", log_path.read_text(encoding="utf-8"))

    def test_pid_huerfano_se_diagnostica_en_parte_y_estado_y_excepcion_avisa(self):
        import contextlib

        (self.root / motor.PID).write_text("99999999", encoding="utf-8")
        (self.root / motor.ESPERA).write_text(
            '{"hasta": "2099-01-01T00:00:00+00:00", "motivo": "cuota"}', encoding="utf-8"
        )
        with patch.object(motor, "pid_vivo", return_value=None):
            resumen = motor.parte(self.root)
            self.assertIn("caído (pid 99999999 terminó inesperadamente)", resumen)
            self.assertNotIn("esperando", resumen)

            salida_cli = io.StringIO()
            with contextlib.redirect_stdout(salida_cli):
                rc = motor.main(["--root", str(self.root), "--estado"])
            self.assertEqual(rc, 0)
            self.assertIn("AVISO: bucle caído (pid 99999999 terminó inesperadamente)", salida_cli.getvalue())

        (self.root / motor.PID).unlink(missing_ok=True)
        (self.root / motor.ESPERA).unlink(missing_ok=True)

        # Excepción inesperada en bucle() avisa por canal 'error' incluso con stdout roto y limpia orquestar.pid
        class StdoutRoto:
            def write(self, _):
                raise OSError("broken stdout")

            def flush(self):
                raise OSError("broken stdout")

        with (
            patch.object(motor, "estado", side_effect=RuntimeError("boom")),
            patch.object(motor, "avisar") as mock_avisar,
            contextlib.redirect_stdout(StdoutRoto()),
        ):
            with self.assertRaisesRegex(RuntimeError, "boom"):
                motor.bucle(self.root, espera_max=0)
        mock_avisar.assert_called_once()
        self.assertEqual(mock_avisar.call_args.args[1], "error")
        self.assertIn("boom", mock_avisar.call_args.args[2])
        self.assertFalse((self.root / motor.PID).exists())

    def test_skill_orquestar_instruye_demonio_sin_fondo_para_agentes_ia(self):
        skill_txt = motor.SKILL.read_text(encoding="utf-8")
        self.assertIn("sin `--fondo`", skill_txt)
        self.assertIn("IsDaemon", skill_txt)
        self.assertIn("run_in_background", skill_txt)

    def test_stream_json_tres_arneses_y_gracia_post_json_con_nieto_heredando_stdout(self):
        import time

        self.assertIn("stream-json", motor.ARNESES["claude"])
        self.assertIn("--verbose", motor.ARNESES["claude"])
        self.assertIn("stream-json", motor.ARNESES["agy"])
        self.assertIn("stream-json", motor.base_comando_agente("claude", "x"))
        self.assertIn("stream-json", motor.base_comando_agente("agy", "x"))

        # AGY stream-json: no duplica tokens de step_update y extrae resultado + sesión
        salida_agy = "\n".join(
            [
                '{"event":"init","conversation_id":"conv-agy-1"}',
                '{"event":"step_update","step_update":{"usage":{"input_tokens":500,"output_tokens":10}}}',
                '{"event":"result","result":{"conversation_id":"conv-agy-1","status":"SUCCESS","response":"Hecho AGY","num_turns":2,"usage":{"input_tokens":500,"output_tokens":10,"thinking_tokens":5,"cache_read_tokens":100}}}',
            ]
        )
        m_agy, txt_agy = motor.perfiles._parsear_salida_json(salida_agy, "agy", modelo_hint="gemini-4-carbon")
        self.assertEqual(txt_agy, "Hecho AGY")
        self.assertEqual(m_agy["sesion"], "conv-agy-1")
        self.assertEqual(m_agy["turnos"], 2)
        self.assertEqual(
            m_agy["modelos"]["gemini-4-carbon"],
            {"entrada": 500, "salida": 10, "cache_leida": 100, "razonamiento": 5},
        )

        # Claude stream-json: toma el texto final de type=result sin duplicar bloques assistant intermedios
        salida_claude = "\n".join(
            [
                '{"type":"system","subtype":"init","session_id":"sess-cl-1"}',
                '{"type":"assistant","message":{"content":[{"type":"text","text":"Pensando..."}]}}',
                '{"type":"result","is_error":false,"result":"Hecho Claude","session_id":"sess-cl-1","num_turns":1,"modelUsage":{"claude-opus":{"inputTokens":200,"outputTokens":30}}}',
            ]
        )
        m_cl, txt_cl = motor.perfiles._parsear_salida_json(salida_claude, "claude")
        self.assertEqual(txt_cl, "Hecho Claude")
        self.assertEqual(m_cl["sesion"], "sess-cl-1")
        self.assertEqual(m_cl["modelos"]["claude-opus"]["entrada"], 200)

        # Codex turn.failed extrae mensaje de error para detección de cuota
        salida_err = '{"type":"turn.failed","error":{"message":"429 rate limit, resets in 45s"}}'
        m_err, txt_err = motor.perfiles._parsear_salida_json(salida_err, "codex")
        self.assertTrue(m_err["error"])
        self.assertEqual(motor.espera_cuota(txt_err), 45)

        # Subproceso real que emite turn.completed de Codex, lanza un nieto que hereda stdout y sale:
        # lanzar() debe retornar éxito tras gracia corta y terminar al nieto (Job Object / grupo)
        pid_nieto_file = self.root / "nieto.pid"
        script_padre = self.root / "padre_codex.py"
        script_padre.write_text(
            "import pathlib, subprocess, sys\n"
            f"nieto = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])  # hereda stdout\n"
            f"pathlib.Path({str(pid_nieto_file)!r}).write_text(str(nieto.pid), encoding='utf-8')\n"
            'print(\'{"type":"item.completed","item":{"type":"agent_message","text":"Tarea lista"}}\', flush=True)\n'
            'print(\'{"type":"turn.completed","usage":{"input_tokens":120,"output_tokens":40,"cached_input_tokens":10}}\', flush=True)\n',
            encoding="utf-8",
        )
        t0 = time.monotonic()
        cod, m, sal = motor.lanzar(
            [sys.executable, str(script_padre)], self.root, "codex", timeout=5.0, gracia_cierre=0.15, modelo="gpt-6.1"
        )
        transcurrido = time.monotonic() - t0
        self.assertEqual(cod, 0)
        self.assertLess(transcurrido, 4.0)
        self.assertTrue(m.get("cierre_forzado"))
        self.assertEqual(sal, "Tarea lista")
        self.assertEqual(m["modelos"]["gpt-6.1"]["entrada"], 120)
        # Verificar que el nieto ya no está vivo
        self.assertIsNone(motor.pid_vivo(self.root, "nieto.pid"))

    def test_watchdog_inactividad_corta_silencio_y_conmuta_a_reserva_salvo_completada(self):
        import time

        self.assertEqual(motor.resolver_plazo(None, 900), 900)
        self.assertIsNone(motor.resolver_plazo(0, 900))
        self.assertIsNone(motor.resolver_plazo(-5, 900))
        self.assertEqual(motor.resolver_plazo("nan", 900), 900)
        self.assertEqual(motor.resolver_plazo("inf", 900), 900)

        # Subproceso que emite un evento inicial y queda congelado en silencio
        cmd = [
            sys.executable,
            "-c",
            'import time; print(\'{"type":"turn.started"}\', flush=True); time.sleep(30)',
        ]
        t0 = time.monotonic()
        cod, m, _ = motor.lanzar(cmd, self.root, "codex", timeout=10.0, inactividad=0.25, gracia_cierre=0.05)
        self.assertEqual(cod, 124)
        self.assertLess(time.monotonic() - t0, 4.0)
        self.assertTrue(m.get("timeout"))
        self.assertTrue(m.get("inactividad"))

        # _invocar_con_reservas conmuta de codex (colgado 124) a reserva agy
        self.escribir(
            "orchestration.json",
            json.dumps(
                {
                    "artemisa": {
                        "harness": "codex",
                        "model": "gpt-colgado",
                        "reserva": [{"harness": "agy", "model": "gemini-rescate"}],
                    }
                }
            ),
        )
        self.tarea("T-DEM-0001", "planned")
        intentos = []

        def fake_lanzar(cmd_arg, root_arg, harness_arg, **kw):
            intentos.append((harness_arg, kw.get("timeout"), kw.get("inactividad")))
            if harness_arg == "codex":
                return 124, {"duracion_s": 5, "timeout": True, "inactividad": True, "modelos": {}}, ""
            return 0, {"duracion_s": 3, "modelos": {"gemini-rescate": {"entrada": 50, "salida": 10}}}, "Resuelto"

        with (
            patch.object(motor, "buscar_ejecutable", side_effect=lambda x: x),
            patch.object(motor, "lanzar", side_effect=fake_lanzar),
        ):
            cod_r, m_r, sal_r = motor._invocar_con_reservas(self.root, "artemisa", "task-dev", "T-DEM-0001", "haz T1")

        self.assertEqual(cod_r, 0)
        self.assertEqual([x[0] for x in intentos], ["codex", "agy"])
        self.assertEqual(intentos[0][1], motor.TIMEOUT_PASO_S)
        self.assertEqual(intentos[0][2], motor.INACTIVIDAD_PASO_S)
        self.assertEqual(m_r["modelo"], "gemini-rescate")
        self.assertEqual(sal_r, "Resuelto")
        filas = motor.leer_metricas(self.root)
        self.assertTrue(
            any(f.get("arnes") == "codex" and f.get("codigo") == 124 and f.get("inactividad") for f in filas)
        )

        # Si el agente colgado ya dejó la ficha en status: completed antes del timeout, no relanza la reserva
        intentos.clear()

        def fake_lanzar_completada(cmd_arg, root_arg, harness_arg, **kw):
            intentos.append(harness_arg)
            self.tarea("T-DEM-0001", "completed")
            return 124, {"duracion_s": 5, "timeout": True, "modelos": {}}, ""

        with (
            patch.object(motor, "buscar_ejecutable", side_effect=lambda x: x),
            patch.object(motor, "lanzar", side_effect=fake_lanzar_completada),
        ):
            cod_ok, _, _ = motor._invocar_con_reservas(self.root, "artemisa", "task-dev", "T-DEM-0001", "haz T1")
        self.assertEqual(cod_ok, 0)
        self.assertEqual(intentos, ["codex"])

    def test_cuota_sin_hora_usa_sondeo_300s_configurable_y_formato_compuesto_hms(self):
        self.assertEqual(motor.espera_cuota("429 rate limit: Resets in 56h48m9s"), 56 * 3600 + 48 * 60 + 9)
        self.assertEqual(motor.espera_cuota("429 retry after soon, resets in 45s"), 45)
        self.assertEqual(motor.espera_cuota("Your workspace is out of credits."), 300)

        d_def = motor.fallo_cuota(self.root, "codex", "gpt-6.1", "429 usage limit reached")
        self.assertEqual(d_def["cuota_espera_s"], 300)
        self.assertTrue(d_def["cuota_supuesta"])

        self.escribir("orchestration.json", json.dumps({"cuota_reintento_s": 120}))
        d_cfg = motor.fallo_cuota(self.root, "codex", "gpt-6.1", "429 usage limit reached")
        self.assertEqual(d_cfg["cuota_espera_s"], 120)
        self.assertTrue(d_cfg["cuota_supuesta"])

        d_real = motor.fallo_cuota(self.root, "codex", "gpt-6.1", "429 resets in 10m")
        self.assertEqual(d_real["cuota_espera_s"], 600)
        self.assertFalse(d_real["cuota_supuesta"])

    def test_fallo_tecnico_prueba_reservas_y_bucle_reintenta_periodicamente_sin_bloquear_ficha(self):
        # 1. Cualquier fallo técnico (p. ej. 503 red) en _invocar_con_reservas prueba la reserva
        self.escribir(
            "orchestration.json",
            json.dumps(
                {
                    "esperas_reintento_s": [1, 2],
                    "artemisa": {
                        "harness": "codex",
                        "model": "gpt-primario",
                        "reserva": [{"harness": "agy", "model": "gemini-reserva"}],
                    },
                }
            ),
        )
        self.tarea("T-DEM-0001", "planned")
        llamados = []

        def fake_lanzar_503(cmd, root, harness, **kw):
            llamados.append(harness)
            if harness == "codex":
                return 1, {"duracion_s": 1, "modelos": {}}, "HTTP 503 Service Unavailable"
            return 0, {"duracion_s": 2, "modelos": {"gemini-reserva": {"entrada": 10, "salida": 5}}}, "Hecho"

        with (
            patch.object(motor, "buscar_ejecutable", side_effect=lambda x: x),
            patch.object(motor, "lanzar", side_effect=fake_lanzar_503),
        ):
            cod, m, _ = motor._invocar_con_reservas(self.root, "artemisa", "task-dev", "T-DEM-0001", "haz T1")
        self.assertEqual(cod, 0)
        self.assertEqual(llamados, ["codex", "agy"])
        self.assertEqual(m["modelo"], "gemini-reserva")

        # 2. En bucle(): dos caídas técnicas en task-dev y una en revisar-version esperan (1s, 2s y 1s),
        # NO bloquean la ficha, NO ensucian {v}-revision.md y NO queman max_pasos=3 (exactamente 3 pasos reales)
        esperas_registradas = []
        ronda = {"dev": 0, "rev_ver": 0}

        def fake_dormir(root, seg, motivo):
            esperas_registradas.append((seg, motivo))
            return True

        def fake_invocar_transitorio(root, rol, paso, iid, prompt, cmd_override=None):
            if paso == "task-dev":
                ronda["dev"] += 1
                if ronda["dev"] <= 2:
                    return 1, {"modelos": {}, "duracion_s": 1, "fallo_arnes": True}, "Error de red temporal 502"
                self.tarea("T-DEM-0001", "completed")
                return 0, {"modelos": {}, "duracion_s": 2}, "Completada al recuperar red"
            if paso == "revisar-tarea":
                self.escribir("docs/review/code_reviews/T-DEM-0001-code-review.md", "**Veredicto:** APROBADO\n")
                return 0, {"modelos": {}, "duracion_s": 1}, "APROBADO"
            ronda["rev_ver"] += 1
            if ronda["rev_ver"] == 1:
                return 1, {"modelos": {}, "duracion_s": 1, "fallo_arnes": True}, "Hades 503 transitorio"
            self.assertFalse((root / "docs/review/versions/v0.1-revision.md").exists())
            self.escribir("docs/review/versions/v0.1-arquitectura.md", "**Veredicto:** APROBADO\n")
            return 0, {"modelos": {}, "duracion_s": 1}, "APROBADO"

        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(motor, "_invocar_con_reservas", side_effect=fake_invocar_transitorio),
            patch.object(motor, "_dormir_con_espera", side_effect=fake_dormir),
            patch.object(motor, "avisar"),
        ):
            rc = motor.bucle(self.root, reintentos=1, max_pasos=3, espera_max=0, reintentos_arnes=3)

        self.assertEqual(rc, 0)
        self.assertEqual(
            esperas_registradas,
            [
                (1, "reintento técnico 1/3"),
                (2, "reintento técnico 2/3"),
                (1, "reintento técnico 1/3"),
            ],
        )
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, "T-DEM-0001"))["status"], "completed")

        # 3. [primario 503, reserva 429] no duplica métricas; [429, acceso_denegado] es simétrico -> 75;
        # y estricto: true no conmuta a reserva ante fallo técnico != 124
        (self.root / motor.METRICAS).unlink(missing_ok=True)
        self.tarea("T-DEM-0003", "planned")

        def fake_503_429(cmd, root, harness, **kw):
            if harness == "codex":
                return 1, {"duracion_s": 1, "modelos": {"gpt-primario": {"entrada": 77, "salida": 11}}}, "HTTP 503"
            return 1, {"duracion_s": 1, "modelos": {}}, "429 rate limit resets in 60s"

        with (
            patch.object(motor, "buscar_ejecutable", side_effect=lambda x: x),
            patch.object(motor, "lanzar", side_effect=fake_503_429),
        ):
            self.assertEqual(motor.agente(self.root, "artemisa", "prueba metricas"), 1)
        filas_503 = [f for f in motor.leer_metricas(self.root) if f.get("arnes") == "codex"]
        self.assertEqual(len(filas_503), 1)

        (self.root / motor.METRICAS).unlink(missing_ok=True)
        self.escribir(
            "orchestration.json",
            json.dumps(
                {
                    "artemisa": {
                        "harness": "codex",
                        "model": "gpt-cuota",
                        "reserva": [{"harness": "claude", "model": "claude-den"}],
                    }
                }
            ),
        )

        def fake_cuota_den(cmd, root, harness, **kw):
            if harness == "codex":
                return 1, {"duracion_s": 1, "modelos": {}}, "429 rate limit resets in 90s"
            return 1, {"duracion_s": 1, "modelos": {}}, "Your organization has disabled Claude subscription access"

        with (
            patch.object(motor, "buscar_ejecutable", side_effect=lambda x: x),
            patch.object(motor, "lanzar", side_effect=fake_cuota_den),
        ):
            cod_sim, m_sim, _ = motor._invocar_con_reservas(self.root, "artemisa", "task-dev", "T-DEM-0003", "haz")
        self.assertEqual(cod_sim, 75)
        self.assertTrue(m_sim.get("sin_cuota"))

        self.tarea(
            "T-DEM-0004",
            "planned",
            extra='perfil: {"harness": "codex", "model": "gpt-fijo", "estricto": true}\n',
        )
        invocados_estricto = []
        with (
            patch.object(motor, "buscar_ejecutable", side_effect=lambda x: x),
            patch.object(
                motor,
                "lanzar",
                side_effect=lambda c, r, h, **kw: invocados_estricto.append(h) or (1, {"modelos": {}}, "HTTP 500"),
            ),
        ):
            cod_est, _, _ = motor._invocar_con_reservas(self.root, "artemisa", "task-dev", "T-DEM-0004", "haz")
        self.assertEqual(cod_est, 1)
        self.assertEqual(invocados_estricto, ["codex"])

        # 4. Parada cooperativa con orquestar.parar durante _dormir_con_espera termina con código 0
        (self.root / motor.PARADA).touch()
        self.assertFalse(motor._dormir_con_espera(self.root, 30, "reintento técnico 1/3"))
        self.assertFalse((self.root / motor.ESPERA).exists())
        (self.root / motor.PARADA).unlink(missing_ok=True)

        # 5. Si agota reintentos_arnes, para con código 1, incluye cola de error en avisar y NO bloquea la ficha
        self.tarea("T-DEM-0002", "planned")
        avisos = []
        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(
                motor,
                "_invocar_con_reservas",
                return_value=(1, {"modelos": {}, "duracion_s": 1}, "401 token caducado"),
            ),
            patch.object(motor, "_dormir_con_espera", return_value=True),
            patch.object(motor, "avisar", side_effect=lambda r, ev, msg: avisos.append((ev, msg))),
        ):
            rc_fin = motor.bucle(self.root, reintentos=1, espera_max=0, reintentos_arnes=1)

        self.assertEqual(rc_fin, 1)
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, "T-DEM-0002"))["status"], "planned")
        self.assertTrue(any(ev == "error" and "401 token caducado" in msg for ev, msg in avisos))


if __name__ == "__main__":
    unittest.main()
