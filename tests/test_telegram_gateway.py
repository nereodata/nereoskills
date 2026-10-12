"""Pruebas unitarias para el Gateway de Telegram de nereoskills.

Cubre exhaustivamente los escenarios de tests/features/telegram_gateway.feature:
- CA-M-1: Seguridad y lista blanca de usuarios.
- CA-M-2: Ingesta de tareas y bugs según Issue-as-Code v3.0.
- CA-M-3: Consulta de estado con Markdown formateado y exclusión de completadas.
- CA-M-4: Notificaciones salientes con entrega múltiple y resiliencia ante errores.
"""
import json
import logging
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from skills.telegram_gateway import gateway


class TelegramGatewaySecurityTests(unittest.TestCase):
    """Pruebas del filtro de seguridad y autorización (CA-M-1)."""

    def setUp(self):
        self.allowed = {"12345", "67890"}

    def test_authorized_user_validation(self):
        self.assertTrue(gateway.is_authorized("12345", self.allowed))
        self.assertTrue(gateway.is_authorized("67890", self.allowed))
        self.assertFalse(gateway.is_authorized("99999", self.allowed))

    def test_unauthorized_user_commands_are_ignored_silently_without_modifying_disk(self):
        unauthorized_id = "99999"
        authorized_id = "12345"
        commands = [
            "/estado",
            "/status",
            "/tarea Intento de escritura maliciosa",
            "/bug Falso reporte no autorizado",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tasks_dir = root / "docs/plan/tasks"
            bugs_dir = root / "docs/plan/bugs"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            bugs_dir.mkdir(parents=True, exist_ok=True)

            # Precarga de ficheros existentes para comprobar que no se alteran ni eliminan
            task_previa = tasks_dir / "T-WKF-0001-existente.md"
            bug_previo = bugs_dir / "B-WKF-0001-existente.md"
            task_previa_contenido = "---\nid: T-WKF-0001\ntitle: Previa\nstatus: completed\n---\n"
            bug_previo_contenido = "---\nid: B-WKF-0001\ntitle: Previo\nstatus: completed\n---\n"
            task_previa.write_text(task_previa_contenido, encoding="utf-8")
            bug_previo.write_text(bug_previo_contenido, encoding="utf-8")

            # 1. Comandos no autorizados: no responden, no crean ficheros y no modifican existentes
            for cmd in commands:
                with self.subTest(unauthorized_cmd=cmd):
                    response = gateway.handle_message(unauthorized_id, cmd, root, self.allowed)
                    self.assertIsNone(response)
                    self.assertEqual(len(list(tasks_dir.glob("*.md"))), 1)
                    self.assertEqual(len(list(bugs_dir.glob("*.md"))), 1)
                    self.assertEqual(task_previa.read_text(encoding="utf-8"), task_previa_contenido)
                    self.assertEqual(bug_previo.read_text(encoding="utf-8"), bug_previo_contenido)

            # 2. Control positivo: el usuario autorizado SÍ recibe respuesta (discrimina stub de implementación)
            control_response = gateway.handle_message(authorized_id, "/estado", root, self.allowed)
            self.assertIsNotNone(control_response, "El usuario autorizado debe recibir una respuesta")


class TelegramGatewayIngestionTests(unittest.TestCase):
    """Pruebas de creación de tareas y bugs con formato Issue-as-Code v3.0 (CA-M-2)."""

    def setUp(self):
        self.allowed = {"12345"}
        self.user_id = "12345"

    def test_create_task_with_active_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tasks_dir = root / "docs/plan/tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            (tasks_dir / "T-WKF-0002-existente.md").write_text("---\nid: T-WKF-0002\n---\n", encoding="utf-8")

            # Configurar versión activa explícita
            (root / "task_config.yaml").write_text("project:\n  version: \"v0.2.0\"\n", encoding="utf-8")

            response = gateway.handle_message(self.user_id, "/tarea Implementar vista resumen", root, self.allowed)
            expected_msg = "Tarea registrada: T-WKF-0003 - Implementar vista resumen"
            self.assertEqual(response, expected_msg)

            target_file = tasks_dir / "T-WKF-0003-implementar-vista-resumen.md"
            self.assertTrue(target_file.exists())
            content = target_file.read_text(encoding="utf-8")
            self.assertIn("id: T-WKF-0003", content)
            self.assertIn("status: planned", content)
            self.assertIn("version: \"v0.2.0\"", content)
            self.assertIn("title: \"Implementar vista resumen\"", content)

    def test_create_task_without_active_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tasks_dir = root / "docs/plan/tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            (tasks_dir / "T-WKF-0002-existente.md").write_text("---\nid: T-WKF-0002\n---\n", encoding="utf-8")

            # Aislar consulta de versión para independizar el test de la rama git actual
            with patch.object(gateway, "get_active_version", return_value=""):
                response = gateway.handle_message(self.user_id, "/tarea Refactorizar utilidades", root, self.allowed)
                expected_msg = "Tarea registrada: T-WKF-0003 - Refactorizar utilidades"
                self.assertEqual(response, expected_msg)

                target_file = tasks_dir / "T-WKF-0003-refactorizar-utilidades.md"
                self.assertTrue(target_file.exists())
                content = target_file.read_text(encoding="utf-8")
                self.assertIn("id: T-WKF-0003", content)
                self.assertIn("status: backlog", content)
                self.assertIn("version: \"\"", content)
                self.assertIn("title: \"Refactorizar utilidades\"", content)

    def test_create_bug_with_active_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bugs_dir = root / "docs/plan/bugs"
            bugs_dir.mkdir(parents=True, exist_ok=True)
            (bugs_dir / "B-WKF-0001-existente.md").write_text("---\nid: B-WKF-0001\n---\n", encoding="utf-8")

            (root / "task_config.yaml").write_text("project:\n  version: \"v0.2.0\"\n", encoding="utf-8")

            response = gateway.handle_message(self.user_id, "/bug Error 500 al listar métricas", root, self.allowed)
            expected_msg = "Bug registrado: B-WKF-0002 - Error 500 al listar métricas"
            self.assertEqual(response, expected_msg)

            target_file = bugs_dir / "B-WKF-0002-error-500-al-listar-metricas.md"
            self.assertTrue(target_file.exists())
            content = target_file.read_text(encoding="utf-8")
            self.assertIn("id: B-WKF-0002", content)
            self.assertIn("status: planned", content)
            self.assertIn("version: \"v0.2.0\"", content)
            self.assertIn("title: \"Error 500 al listar métricas\"", content)

    def test_create_bug_without_active_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bugs_dir = root / "docs/plan/bugs"
            bugs_dir.mkdir(parents=True, exist_ok=True)
            (bugs_dir / "B-WKF-0001-existente.md").write_text("---\nid: B-WKF-0001\n---\n", encoding="utf-8")

            # Aislar consulta de versión para independizar el test de la rama git actual
            with patch.object(gateway, "get_active_version", return_value=""):
                response = gateway.handle_message(self.user_id, "/bug Fallo tipográfico en menú", root, self.allowed)
                expected_msg = "Bug registrado: B-WKF-0002 - Fallo tipográfico en menú"
                self.assertEqual(response, expected_msg)

                target_file = bugs_dir / "B-WKF-0002-fallo-tipografico-en-menu.md"
                self.assertTrue(target_file.exists())
                content = target_file.read_text(encoding="utf-8")
                self.assertIn("id: B-WKF-0002", content)
                self.assertIn("status: backlog", content)
                self.assertIn("version: \"\"", content)
                self.assertIn("title: \"Fallo tipográfico en menú\"", content)

    def test_empty_arguments_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tasks_dir = root / "docs/plan/tasks"
            bugs_dir = root / "docs/plan/bugs"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            bugs_dir.mkdir(parents=True, exist_ok=True)

            resp_task = gateway.handle_message(self.user_id, "/tarea", root, self.allowed)
            self.assertEqual(resp_task, "Uso: /tarea <título descriptivo de la tarea>")
            self.assertEqual(len(list(tasks_dir.glob("*.md"))), 0)

            resp_bug = gateway.handle_message(self.user_id, "/bug", root, self.allowed)
            self.assertEqual(resp_bug, "Uso: /bug <descripción del error detectado>")
            self.assertEqual(len(list(bugs_dir.glob("*.md"))), 0)


class TelegramGatewayStatusTests(unittest.TestCase):
    """Pruebas de consulta de estado del backlog (CA-M-3)."""

    def setUp(self):
        self.allowed = {"12345"}
        self.user_id = "12345"

    def test_status_with_task_in_progress(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tasks_dir = root / "docs/plan/tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)

            (root / "task_config.yaml").write_text("project:\n  version: \"v0.2.0\"\n", encoding="utf-8")
            (tasks_dir / "T-WKF-0001.md").write_text(
                "---\nid: T-WKF-0001\ntitle: Estrategia de ramas\nstatus: completed\n---\n", encoding="utf-8")
            (tasks_dir / "T-WKF-0002.md").write_text(
                "---\nid: T-WKF-0002\ntitle: Gateway Telegram\nstatus: in_progress\n---\n", encoding="utf-8")
            (tasks_dir / "T-WKF-0003.md").write_text(
                "---\nid: T-WKF-0003\ntitle: Botones interactivos\nstatus: backlog\n---\n", encoding="utf-8")

            expected = (
                "*Versión activa:* `v0.2.0`\n"
                "*En curso:* `T-WKF-0002` - Gateway Telegram\n"
                "*Pendientes (1):*\n"
                "- `T-WKF-0003`: Botones interactivos"
            )

            for cmd in ["/estado", "/status"]:
                with self.subTest(command=cmd):
                    response = gateway.handle_message(self.user_id, cmd, root, self.allowed)
                    self.assertEqual(response, expected)

    def test_status_without_task_in_progress(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tasks_dir = root / "docs/plan/tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)

            (root / "task_config.yaml").write_text("project:\n  version: \"v0.2.0\"\n", encoding="utf-8")
            (tasks_dir / "T-WKF-0001.md").write_text(
                "---\nid: T-WKF-0001\ntitle: Estrategia de ramas\nstatus: completed\n---\n", encoding="utf-8")
            (tasks_dir / "T-WKF-0002.md").write_text(
                "---\nid: T-WKF-0002\ntitle: Gateway Telegram\nstatus: planned\n---\n", encoding="utf-8")

            expected = (
                "*Versión activa:* `v0.2.0`\n"
                "*En curso:* Ninguna\n"
                "*Pendientes (1):*\n"
                "- `T-WKF-0002`: Gateway Telegram"
            )

            response = gateway.handle_message(self.user_id, "/estado", root, self.allowed)
            self.assertEqual(response, expected)


class TelegramGatewayNotificationTests(unittest.TestCase):
    """Pruebas del canal de notificaciones salientes (CA-M-4)."""

    def test_notify_success_sends_to_all_chats(self):
        mock_http = MagicMock(return_value=True)
        chats = ["12345", "67890"]
        text = "Hito v0.2 completado con éxito"

        result = gateway.notify(text, chat_ids=chats, token="mock_token", http_client=mock_http)
        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 2)
        mock_http.assert_any_call("mock_token", "12345", "📢 Hito v0.2 completado con éxito")
        mock_http.assert_any_call("mock_token", "67890", "📢 Hito v0.2 completado con éxito")

    def test_notify_resilience_on_failure_logs_warning_and_returns_false(self):
        chats = ["12345", "67890"]
        text = "Alerta de sistema"

        # Caso A: excepción de conexión
        with self.subTest(error_type="exception"):
            mock_http = MagicMock(side_effect=RuntimeError("Connection refused"))
            with self.assertLogs(logger="skills.telegram_gateway.gateway", level="WARNING") as cm:
                result = gateway.notify(text, chat_ids=chats, token="mock_token", http_client=mock_http)
                self.assertFalse(result)
                self.assertTrue(any("Fallo al enviar notificación a Telegram: Alerta de sistema" in msg for msg in cm.output))

        # Caso B: respuesta de error del servicio (retorna False)
        with self.subTest(error_type="error_response"):
            mock_http = MagicMock(return_value=False)
            with self.assertLogs(logger="skills.telegram_gateway.gateway", level="WARNING") as cm:
                result = gateway.notify(text, chat_ids=chats, token="mock_token", http_client=mock_http)
                self.assertFalse(result)
                self.assertTrue(any("Fallo al enviar notificación a Telegram: Alerta de sistema" in msg for msg in cm.output))


class TelegramGatewayRobustnessAndPollingTests(unittest.TestCase):
    """Pruebas de robustez de formato Issue-as-Code, escaping YAML, y polling."""

    def test_yaml_frontmatter_validity_with_quotes_and_special_chars(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            title = 'Falla al pulsar "Guardar" y en C:\\temp\\test'
            task_id, task_path = gateway.create_task(root, title, version="v0.2.0")
            bug_id, bug_path = gateway.create_bug(root, title, version="v0.2.0")

            content_task = task_path.read_text(encoding="utf-8")
            content_bug = bug_path.read_text(encoding="utf-8")

            # Metadatos Issue-as-Code
            self.assertIn("created_at:", content_task)
            self.assertIn("updated_at:", content_task)
            self.assertIn("weight: 10", content_task)

            self.assertIn("created_at:", content_bug)
            self.assertIn("updated_at:", content_bug)
            self.assertIn("weight: 100", content_bug)

            # Verificar que el frontmatter es YAML 100% válido
            fm_task = gateway._parse_frontmatter(content_task)
            fm_bug = gateway._parse_frontmatter(content_bug)
            self.assertEqual(fm_task["title"], title)
            self.assertEqual(fm_bug["title"], title)

    def test_slug_generation_bounds_and_safety(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Solo emojis
            _, task_emoji = gateway.create_task(root, "🚀🔥🎉")
            self.assertEqual(task_emoji.name, "T-WKF-0001.md")

            # Título muy largo (> 100 caracteres)
            long_title = "a" * 120
            _, task_long = gateway.create_task(root, long_title)
            self.assertTrue(len(task_long.name) < 100)

    def test_bug_id_avoids_collision_with_existing_bug_in_tasks_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tasks_dir = root / "docs/plan/tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            # Simular B-WKF-0001 existente en docs/plan/tasks/
            (tasks_dir / "B-WKF-0001-error-antiguo.md").write_text("---\nid: B-WKF-0001\n---\n", encoding="utf-8")

            bug_id, _ = gateway.create_bug(root, "Nuevo error detectado")
            self.assertEqual(bug_id, "B-WKF-0002")

    @patch.object(gateway, "_default_http_post")
    @patch.object(gateway, "get_updates")
    def test_run_polling_processes_update_and_sends_reply(self, mock_updates, mock_send):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "task_config.yaml").write_text("project:\n  version: \"v0.2.0\"\n", encoding="utf-8")

            mock_updates.return_value = [
                {
                    "update_id": 1001,
                    "message": {
                        "from": {"id": 12345},
                        "chat": {"id": 98765},
                        "text": "/estado",
                    },
                }
            ]
            gateway.run_polling(root, token="mock_token", allowed_ids={"12345"}, timeout=1, max_iterations=1)

            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            self.assertEqual(args[0], "mock_token")
            self.assertEqual(args[1], "98765")
            self.assertIn("*Versión activa:* `v0.2.0`", args[2])

    @patch("urllib.request.urlopen")
    def test_default_http_post_retries_plain_text_on_http_400_markdown_error(self, mock_urlopen):
        err_400 = urllib.error.HTTPError("url", 400, "Bad Request", {}, None)
        success_cm = MagicMock()
        success_cm.__enter__.return_value = MagicMock(status=200)

        # Primer intento con Markdown falla con 400, reintento sin Markdown tiene éxito
        mock_urlopen.side_effect = [err_400, success_cm]
        result = gateway._default_http_post("token", "12345", "texto con _sin_cerrar", parse_mode="Markdown")

        self.assertTrue(result)
        self.assertEqual(mock_urlopen.call_count, 2)
        # Segundo intento no debe llevar parse_mode
        second_payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
        self.assertNotIn("parse_mode", second_payload)

    @patch.object(gateway, "handle_message", side_effect=RuntimeError("Fallo inesperado al procesar mensaje"))
    @patch.object(gateway, "get_updates")
    def test_run_polling_survives_message_processing_exception(self, mock_updates, mock_handle):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            mock_updates.return_value = [
                {
                    "update_id": 1002,
                    "message": {
                        "from": {"id": 12345},
                        "chat": {"id": 98765},
                        "text": "/tarea Mensaje defectuoso",
                    },
                }
            ]
            # No debe propagar la excepción y debe terminar las iteraciones limpiamente
            gateway.run_polling(root, token="mock_token", allowed_ids={"12345"}, timeout=1, max_iterations=1)
            mock_handle.assert_called_once()


if __name__ == "__main__":
    unittest.main()

