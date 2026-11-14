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
            # Bug va antes que tarea aunque tenga mayor weight
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

    def test_rechazo_hades_reabre_y_bloquea_tras_tope_reintentos(self):
        self.tarea("T-DEM-0001", "completed")

        def fake_invocar(root, rol, paso, iid, prompt, cmd_override=None):
            if paso == "revisar-tarea":
                self.escribir(
                    "docs/review/code_reviews/T-DEM-0001-code-review.md", "**Veredicto:** RECHAZADO\nFalta X.\n"
                )
                return 0, {"modelos": {}, "duracion_s": 2}, "RECHAZADO"
            # Artemisa vuelve a marcar completed sin arreglar
            self.tarea("T-DEM-0001", "completed")
            return 0, {"modelos": {}, "duracion_s": 2}, "Intento"

        with (
            patch.object(motor, "git", return_value="release/v0.1"),
            patch.object(motor, "_invocar_con_reservas", side_effect=fake_invocar),
            patch.object(motor, "avisar"),
        ):
            rc = motor.bucle(self.root, reintentos=1, espera_max=0)

        self.assertEqual(rc, 1)
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, "T-DEM-0001"))["status"], "blocked")

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
            self.assertEqual(
                motor.main(["--root", str(self.root), "--metrics", "--version-filtro", "v0.1"]), 0
            )
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

        # Un informe de arquitectura RECHAZADO detiene estado() en vez de dar la versión por terminada
        self.escribir("docs/review/versions/v0.1-arquitectura.md", "**Veredicto:** RECHAZADO\n")
        with patch.object(motor, "git", return_value="release/v0.1"):
            est = motor.estado(self.root)
        self.assertEqual(est[0], "PARAR")
        self.assertIn("rechazada", est[1])

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


if __name__ == "__main__":
    unittest.main()
