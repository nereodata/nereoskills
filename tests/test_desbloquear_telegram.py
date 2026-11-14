"""Pruebas directas de T-ADV-0038: /desbloquear en Telegram y diagnóstico sin pregunta humana."""

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from adevv import contexto_ejecucion, decision_item
from tests import aislamiento_telegram  # noqa: F401
from tests.test_telegram_gateway import gateway


motor = gateway.motor
AUTORIZADOS = {"111", "222"}


class DesbloquearTelegramTests(unittest.TestCase):
    """Verifica /desbloquear, recuperación del planificador y conservación de esperas técnicas/cuota."""

    def setUp(self):
        self.enterContext(patch.object(motor, "iniciar_gateway"))
        self.enterContext(patch.object(motor, "avisar", return_value=False))
        self.enterContext(patch.object(motor, "telegram", return_value=None))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "ProyectoDesbloqueo"
        self.root.mkdir(parents=True, exist_ok=True)
        self.inicializar_repo()
        self.enterContext(patch.object(motor, "git", side_effect=lambda *args, **kw: self.git(*args)))

    def git(self, *args):
        env = {
            **os.environ,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
        }
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout.strip()

    def inicializar_repo(self):
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        archivos = {
            "task_config.yaml": (
                'project:\n  name: ProyectoDesbloqueo\n  prefix: ADV\n  version: "v1.2.0"\n'
                "levels:\n  master:\n    id_prefix: ADV\n    path: docs/plan/\n"
                "    folders:\n      tasks: tasks/\n      bugs: bugs/\n"
            ),
            "docs/requirements/requirements.md": "# Idea\n",
            "docs/requirements/req_analysis.md": "**Estado:** APROBADO\n",
            "docs/requirements/platform_plan.md": "# Plan\n",
            "docs/requirements/platform_review.md": "**Veredicto:** APROBADO\n",
            "docs/requirements/work_plan.md": "# Work plan\n",
            "docs/review/versions/v1.2-revision.md": "# Revisión de versión v1.2\n",
        }
        for rel, contenido in archivos.items():
            ruta = self.root / rel
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(contenido, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "chore: init")
        self.git("checkout", "-qb", "release/v1.2")

    def crear_ficha(self, iid, status="planned", depende_de=None, weight=10, extra_fm="", cuerpo=""):
        es_bug = iid.startswith("B-")
        carpeta = "bugs" if es_bug else "tasks"
        tipo = "bug" if es_bug else "funcional"
        deps = json.dumps(depende_de or [])
        ruta = self.root / f"docs/plan/{carpeta}/{iid}.md"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        extra = (extra_fm.strip() + "\n") if extra_fm.strip() else ""
        ruta.write_text(
            f'---\nid: {iid}\ntitle: "Ficha {iid}"\ntype: {tipo}\nweight: {weight}\n'
            f'dificultad: media\nversion: "v1.2.0"\nstatus: {status}\ndepende_de: {deps}\n{extra}---\n\n'
            f"# {iid}\n\n{cuerpo or 'Descripción.'}\n",
            encoding="utf-8",
        )
        return ruta

    def args_bucle(self, max_pasos=6, espera_max=0):
        return motor.argparse.Namespace(
            idea=None,
            docs="docs/requirements",
            test=None,
            harness="claude",
            estado=False,
            max_pasos=max_pasos,
            reintentos=2,
            reintentos_arnes=0,
            espera_max=espera_max,
            cmd=None,
            presupuesto=None,
            recarga=None,
        )

    def tg(self, texto, usuario="111"):
        return gateway.responder(self.root, usuario, texto, AUTORIZADOS)

    def test_ayuda_muestra_sintaxis_de_desbloquear_y_firma(self):
        """CA-M-1: /ayuda, /help y /start documentan /desbloquear <Q-ID> <respuesta>."""
        for cmd in ("/ayuda", "/help", "/start"):
            with self.subTest(cmd=cmd):
                resp = self.tg(cmd)
                self.assertIn("/desbloquear <Q-ID> <respuesta>", resp)
                self.assertIn("/responder <Q-ID> <respuesta>", resp)
                self.assertIn("— Adevv v", resp)

    def test_desbloquear_aplica_autorizacion_validacion_persistencia_e_idempotencia(self):
        """CA-M-1: /desbloquear comparte reglas con /responder y repetir el mensaje no duplica incorporación."""
        ficha_1 = self.crear_ficha("T-ADV-0101", weight=10)
        self.crear_ficha("T-ADV-0102", weight=20)
        self.git("add", ".")
        self.git("commit", "-qm", "chore: tareas base")

        q1 = motor.solicitar_intervencion(self.root, "T-ADV-0101", "¿Proveedor OAuth?", contexto="Auth")
        q2 = motor.solicitar_intervencion(self.root, "T-ADV-0101", "¿Dominio público?", contexto="Red")
        q3 = motor.solicitar_intervencion(self.root, "T-ADV-0102", "¿Motor SQL?", contexto="Datos")
        self.assertEqual((q1["id"], q2["id"], q3["id"]), ("Q-ADV-0001", "Q-ADV-0002", "Q-ADV-0003"))

        registro = self.root / motor.intervencion.PREGUNTAS
        snap_inicial = registro.read_bytes()

        # Autorización: remitente no autorizado se ignora sin tocar disco
        self.assertIsNone(self.tg("/desbloquear Q-ADV-0001 Usar interno", usuario="999"))
        self.assertEqual(registro.read_bytes(), snap_inicial)

        # Validaciones equivalentes a /responder
        self.assertIn("no pertenece a este proyecto", self.tg("/desbloquear Q-OTRO-0001 dato"))
        self.assertIn("no pertenece a este proyecto", self.tg("/desbloquear T-OTRO-0001 dato"))
        self.assertIn("no existe", self.tg("/desbloquear Q-ADV-9999 dato"))
        self.assertIn("no existe", self.tg("/desbloquear T-ADV-9999 dato"))
        self.assertIn("Falta la respuesta", self.tg("/desbloquear Q-ADV-0001    "))
        self.assertIn("ambigua", self.tg("/desbloquear T-ADV-0101 dato").lower())
        self.assertIn("ambigua", self.tg("/desbloquear dato").lower())
        self.assertEqual(registro.read_bytes(), snap_inicial)

        # Con bucle vivo: encola sin tocar Git y deduplica repeticiones (/desbloquear y /responder)
        (self.root / motor.PID).write_text(str(os.getpid()), encoding="utf-8")
        head_antes = self.git("rev-parse", "HEAD")
        dato_seguro = "$(touch inyectado); Usar Postgres 16"
        r_alta = self.tg(f"/desbloquear@MiBot Q-ADV-0003 {dato_seguro}")
        self.assertIn("recibida", r_alta.lower())
        self.assertEqual(self.git("rev-parse", "HEAD"), head_antes)
        self.assertFalse((self.root / "inyectado").exists())

        for repetido in (
            f"/desbloquear Q-ADV-0003 {dato_seguro}",
            f"/unblock Q-ADV-0003 {dato_seguro}",
            f"/responder Q-ADV-0003 {dato_seguro}",
        ):
            self.assertIn("duplicada", self.tg(repetido).lower())

        preguntas = json.loads(registro.read_text(encoding="utf-8"))
        q3_guardada = next(x for x in preguntas if x["id"] == "Q-ADV-0003")
        self.assertEqual(len(q3_guardada["cola"]), 1)

        # Incorporación entre pasos: única vez, y repetir tras cerrar no duplica ni relanza
        (self.root / motor.PID).unlink(missing_ok=True)
        inc_1 = motor.incorporar_respuestas(self.root)
        self.assertEqual([x["id"] for x in inc_1], ["Q-ADV-0003"])
        head_tras_inc = self.git("rev-parse", "HEAD")

        with patch.object(motor, "en_fondo") as mock_fondo:
            r_cerrada = self.tg(f"/desbloquear Q-ADV-0003 {dato_seguro}")
            self.assertIn("cerrada", r_cerrada.lower())
            mock_fondo.assert_not_called()
        self.assertEqual(motor.incorporar_respuestas(self.root), [])
        self.assertEqual(self.git("rev-parse", "HEAD"), head_tras_inc)

        # Respuestas insuficientes conservan el bloqueo
        with patch.object(motor, "en_fondo") as mock_fondo:
            r_pend = self.tg("/desbloquear Q-ADV-0001 PENDIENTE: falta acordar proveedor")
            self.assertIn("falta acordar proveedor", r_pend)
            mock_fondo.assert_not_called()
        self.assertEqual(motor.frontmatter(ficha_1)["status"], "blocked")

    def test_planificador_recupera_tarea_respetando_dependencias_y_wip(self):
        """CA-M-2: Tras incorporar por /desbloquear, el planificador respeta dependencias y restaura WIP."""
        self.crear_ficha("T-ADV-0100", weight=10, depende_de=[])
        self.crear_ficha("T-ADV-0101", weight=20, depende_de=["T-ADV-0100"])
        self.git("add", ".")
        self.git("commit", "-qm", "chore: tareas con dependencia")

        # T-ADV-0100 bloqueada por Q-ADV-0001; T-ADV-0101 con WIP aislado y bloqueada por Q-ADV-0002
        q_dep = motor.solicitar_intervencion(self.root, "T-ADV-0100", "¿Región primaria?", contexto="Infra")
        wip_file = self.root / "app" / "servicio.py"
        wip_file.parent.mkdir(parents=True, exist_ok=True)
        wip_file.write_text('MODO = "borrador_wip"\n', encoding="utf-8")
        q_hija = motor.solicitar_intervencion(self.root, "T-ADV-0101", "¿Timeout HTTP?", contexto="Cliente")
        self.assertFalse(wip_file.exists())

        # Desbloquear primero la tarea dependiente T-ADV-0101: se incorpora pero espera a T-ADV-0100
        with patch.object(motor, "en_fondo", return_value=0) as mock_fondo:
            r_hija = self.tg(f"/desbloquear {q_hija['id']} 30 segundos")
        self.assertIn("dependencias", r_hija.lower())
        self.assertIn("T-ADV-0100", r_hija)
        mock_fondo.assert_not_called()
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, "T-ADV-0101"))["status"], "planned")
        estado_intermedio = motor.estado(self.root, "docs/requirements")
        self.assertEqual(estado_intermedio[0], "PARAR")
        self.assertIn("Q-ADV-0001", estado_intermedio[1])

        # Desbloquear ahora la raíz T-ADV-0100: reanuda en fondo y el planificador elige T-ADV-0100 primero
        with patch.object(motor, "en_fondo", return_value=0) as mock_fondo:
            r_dep = self.tg(f"/desbloquear {q_dep['id']} eu-south-2")
        self.assertIn("reanudada", r_dep.lower())
        mock_fondo.assert_called_once_with(self.root, argumentos=[])
        self.assertEqual(
            motor.estado(self.root, "docs/requirements"),
            ("PASO", "task-dev", "T-ADV-0100", "release/v1.2"),
        )

        ejecutadas = []
        prompts_recibidos = {}

        def simular_paso(a, root, prompt, **kwargs):
            iid = kwargs["env"]["ORQUESTAR_ID"]
            ejecutadas.append(iid)
            prompts_recibidos[iid] = prompt
            if iid == "T-ADV-0101":
                self.assertTrue((root / "app" / "servicio.py").exists())
                self.assertIn("borrador_wip", (root / "app" / "servicio.py").read_text(encoding="utf-8"))
            entregable = root / "app" / f"{iid.lower()}.py"
            entregable.parent.mkdir(parents=True, exist_ok=True)
            entregable.write_text("LISTO = True\n", encoding="utf-8")
            ficha = motor.fichero_de(root, iid)
            ficha.write_text(
                ficha.read_text(encoding="utf-8").replace("status: planned", "status: completed"),
                encoding="utf-8",
            )
            (root / "docs/review/versions/v1.2-arquitectura.md").write_text(
                "**Veredicto:** APROBADO\n", encoding="utf-8"
            )
            self.git("add", ".")
            self.git("commit", "-qm", f"feat: [{iid}] - completada")
            return 0, {}, "ok"

        with patch.object(motor, "ejecutar", side_effect=simular_paso), redirect_stdout(io.StringIO()):
            motor.bucle(self.args_bucle(max_pasos=5, espera_max=0), self.root)

        self.assertEqual(ejecutadas, ["T-ADV-0100", "T-ADV-0101"])
        self.assertIn("eu-south-2", prompts_recibidos["T-ADV-0100"])
        self.assertIn("30 segundos", prompts_recibidos["T-ADV-0101"])

    def test_parada_manual_impide_relanzar_y_recupera_al_levantar_parada(self):
        """CA-M-2: /desbloquear respeta orquestar.parar sin relanzar; al retirar la parada, el planificador la retoma."""
        self.crear_ficha("T-ADV-0101", weight=10)
        self.git("add", ".")
        self.git("commit", "-qm", "chore: tarea")
        q = motor.solicitar_intervencion(self.root, "T-ADV-0101", "¿Modo caché?", contexto="Rendimiento")

        senal_parada = self.root / motor.PARADA
        senal_parada.write_text("parada manual", encoding="utf-8")
        with patch.object(motor, "en_fondo", return_value=0) as mock_fondo:
            resp = self.tg(f"/desbloquear {q['id']} Redis local")
        self.assertIn("parada manual", resp.lower())
        mock_fondo.assert_not_called()
        self.assertTrue(senal_parada.exists())
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, "T-ADV-0101"))["status"], "planned")

        # Mientras exista orquestar.parar, el bucle no ejecuta pasos
        with patch.object(motor, "ejecutar") as mock_ejecutar, redirect_stdout(io.StringIO()):
            self.assertEqual(motor.bucle(self.args_bucle(max_pasos=2), self.root), 2)
            mock_ejecutar.assert_not_called()

        # Al retirar la señal manual, el planificador selecciona directamente la tarea ya desbloqueada
        senal_parada.unlink()
        self.assertEqual(
            motor.estado(self.root, "docs/requirements"),
            ("PASO", "task-dev", "T-ADV-0101", "release/v1.2"),
        )

    def test_espera_de_cuota_sin_pregunta_explica_motivo_y_conserva_estado(self):
        """CA-M-2: Una espera de cuota (por ítem o global del bucle) explica el motivo y conserva intacto su estado."""
        ficha = self.crear_ficha("T-ADV-0101", weight=10)
        self.git("add", ".")
        self.git("commit", "-qm", "chore: tarea en cuota")
        base_sha = self.git("rev-parse", "HEAD")

        # 1) Espera de cuota registrada en decision_item (p. ej. revisión de Hades sin cuota) + WIP aislado
        (self.root / "src_wip.py").write_text("X = 1\n", encoding="utf-8")
        wip_rama = decision_item.aislar_wip(self.root, motor, "T-ADV-0101", base_sha)
        reg_dec = decision_item.guardar(
            self.root,
            "release/v1.2",
            "T-ADV-0101",
            {
                "tipo": "espera",
                "causa": "cuota",
                "situacion": "espera de cuota",
                "paso": "task-dev",
                "rol": "hades",
                "objetivo": "code",
                "condicion": "capacidad recuperada del rol requerido",
                "wip_rama": wip_rama,
                "base_commit": base_sha,
                "wip_en_arbol": False,
            },
        )
        self.assertEqual(reg_dec["causa"], "cuota")
        motor.registrar(
            self.root,
            {
                "tipo": "agente",
                "rol": "hades",
                "id": "T-ADV-0101",
                "fecha": motor.ahora(),
                "arnes": "claude",
                "modelo_cuota": "claude-opus",
                "cuota_espera_s": 1800,
                "cuota_tipo": "real",
                "cuota_origen": "hora en la respuesta",
            },
        )
        metricas_antes = (self.root / motor.METRICAS).read_bytes()
        ficha_antes = ficha.read_bytes()
        dec_antes = decision_item.leer(self.root, "release/v1.2", "T-ADV-0101")
        wip_sha_antes = self.git("rev-parse", wip_rama)

        with patch.object(motor, "en_fondo") as mock_fondo:
            for orden in ("/desbloquear T-ADV-0101 reintentar", "/desbloquear T-ADV-0101", "/desbloquear"):
                with self.subTest(orden=orden):
                    salida = self.tg(orden)
                    self.assertIn("espera de cuota", salida.lower())
                    self.assertIn("claude/claude-opus", salida)
                    self.assertIn("conserva", salida.lower())
            mock_fondo.assert_not_called()

        self.assertFalse((self.root / motor.intervencion.PREGUNTAS).exists())
        self.assertEqual((self.root / motor.METRICAS).read_bytes(), metricas_antes)
        self.assertEqual(ficha.read_bytes(), ficha_antes)
        self.assertEqual(decision_item.leer(self.root, "release/v1.2", "T-ADV-0101"), dec_antes)
        self.assertEqual(self.git("rev-parse", wip_rama), wip_sha_antes)
        self.assertEqual(self.git("rev-parse", "HEAD"), base_sha)
        self.assertEqual(self.git("status", "--porcelain"), "")

        # 2) Espera global del bucle en orquestar.espera sin decision_item
        decision_item.borrar(self.root, "release/v1.2", "T-ADV-0101")
        hasta = (motor.fecha_estado(motor.ahora()) + timedelta(minutes=25)).strftime("%Y-%m-%dT%H:%M")
        espera_file = self.root / motor.ESPERA
        espera_file.write_text(f"{hasta}\nsin cuota", encoding="utf-8")
        espera_bytes = espera_file.read_bytes()

        for orden in ("/desbloquear", "/desbloquear continuar", "/desbloquear T-ADV-0101"):
            salida = self.tg(orden)
            self.assertIn("cuota", salida.lower())
            self.assertIn("conserva", salida.lower())
        self.assertEqual(espera_file.read_bytes(), espera_bytes)

    def test_intervencion_tecnica_sin_pregunta_explica_motivo_y_conserva_estado(self):
        """CA-M-2: Las intervenciones o esperas técnicas sin pregunta explican su motivo y conservan su estado."""
        t_esp = self.crear_ficha("T-ADV-0101", weight=10)
        b_suite = self.crear_ficha(
            "B-ADV-0201",
            status="blocked",
            weight=5,
            extra_fm='pendiente_de: intervencion_tecnica\nsuite_cierre: "true"\nsuite_accion: resuelta',
            cuerpo="## Conclusión del diagnóstico\nFallo determinista en migraciones.\n",
        )
        t_pausa = self.crear_ficha("T-ADV-0103", weight=30)
        self.git("add", ".")
        self.git("commit", "-qm", "chore: fichas con intervenciones técnicas")

        # 1) Enrutado al especificador (status: blocked, pendiente_de: especificador)
        motor.enrutar_hallazgo(self.root, "T-ADV-0101", "especificador", contexto="Contradicción entre CA-1 y CA-2")
        self.git("add", ".")
        self.git("commit", "-qm", "docs: enrutar T-ADV-0101 a especificador")
        head_base = self.git("rev-parse", "HEAD")
        bytes_t_esp = t_esp.read_bytes()
        bytes_b_suite = b_suite.read_bytes()
        bytes_t_pausa = t_pausa.read_bytes()

        # 2) Asignación técnica en decision_item y pausa técnica por presupuesto agotado en T-ADV-0103
        decision_item.guardar(
            self.root,
            "release/v1.2",
            "T-ADV-0103",
            {
                "tipo": "espera",
                "causa": "suscripcion",
                "situacion": "espera técnica",
                "paso": "task-dev",
                "rol": "hades",
                "objetivo": "code",
                "impedimento": "suscripción de Claude deshabilitada en perfiles autorizados",
                "condicion": "recuperar acceso de un perfil autorizado",
            },
        )
        for i in range(3):
            contexto_ejecucion.registrar_intento(self.root, "T-ADV-0103", progreso=False, invocacion=f"np-{i}")
        dec_antes = decision_item.leer(self.root, "release/v1.2", "T-ADV-0103")
        ctx_antes = contexto_ejecucion.consultar(self.root, "T-ADV-0103")
        self.assertEqual(ctx_antes["action"], "pausa_tecnica")

        with patch.object(motor, "en_fondo") as mock_fondo:
            r_esp = self.tg("/desbloquear T-ADV-0101 forzar")
            self.assertIn("especificador", r_esp.lower())
            self.assertIn("Contradicción entre CA-1 y CA-2", r_esp)
            self.assertIn("conserva", r_esp.lower())

            r_suite = self.tg("/desbloquear B-ADV-0201 continuar")
            self.assertIn("intervención técnica", r_suite.lower())
            self.assertIn("conserva", r_suite.lower())

            r_pausa = self.tg("/desbloquear T-ADV-0103 reintentar")
            self.assertIn("espera técnica", r_pausa.lower())
            self.assertIn("pausa técnica", r_pausa.lower())
            self.assertIn("conserva", r_pausa.lower())

            r_global = self.tg("/desbloquear")
            self.assertIn("no hay preguntas humanas pendientes", r_global.lower())
            self.assertIn("especificador", r_global.lower())
            self.assertIn("intervención técnica", r_global.lower())
            self.assertIn("espera técnica", r_global.lower())
            mock_fondo.assert_not_called()

        # Verificar que ningún estado en disco ni Git ha cambiado
        self.assertFalse((self.root / motor.intervencion.PREGUNTAS).exists())
        self.assertEqual(t_esp.read_bytes(), bytes_t_esp)
        self.assertEqual(b_suite.read_bytes(), bytes_b_suite)
        self.assertEqual(t_pausa.read_bytes(), bytes_t_pausa)
        self.assertEqual(decision_item.leer(self.root, "release/v1.2", "T-ADV-0103"), dec_antes)
        self.assertEqual(contexto_ejecucion.consultar(self.root, "T-ADV-0103")["revision"], ctx_antes["revision"])
        self.assertEqual(self.git("rev-parse", "HEAD"), head_base)
        self.assertEqual(self.git("status", "--porcelain"), "")


if __name__ == "__main__":
    unittest.main()
