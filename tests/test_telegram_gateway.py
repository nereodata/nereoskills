import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    'gateway', Path(__file__).resolve().parents[1] / 'skills/telegram_gateway/gateway.py')
gateway = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gateway)
motor = gateway.motor

AUTORIZADOS = {'12345', '67890'}


class GatewayTests(unittest.TestCase):
    """Proyecto con una tarea T-ADV-0002 en v0.1 en curso, en un repositorio git."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for args in (('init', '-q'), ('config', 'user.email', 't@t'), ('config', 'user.name', 't')):
            self.git(*args)
        (self.root / 'task_config.yaml').write_text('prefix: ADV\n', encoding='utf-8')
        tarea = self.root / 'docs/plan/tasks/T-ADV-0002-vista.md'
        tarea.parent.mkdir(parents=True)
        tarea.write_text('---\nid: T-ADV-0002\ntitle: "Vista"\nversion: v0.1.0\nstatus: in_progress\n'
                         'depende_de: []\n---\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-q', '-m', 'base')
        self.excluir = patch.object(motor, 'excluir')
        self.excluir.start()

    def tearDown(self):
        self.excluir.stop()
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout

    def responder(self, texto, usuario='12345'):
        return gateway.responder(self.root, usuario, texto, AUTORIZADOS)

    def backlog(self):
        return sorted(p.name for p in (self.root / 'docs/plan').rglob('*.md'))

    def test_unauthorized_users_get_nothing_and_change_nothing(self):
        antes = self.backlog()
        for texto in ('/estado', '/tarea Intento', '/bug Falso', '/ayuda'):
            with self.subTest(texto=texto):
                self.assertIsNone(self.responder(texto, usuario='99999'))
        self.assertEqual(self.backlog(), antes)
        self.assertFalse((self.root / motor.BUZON).exists())

    def test_task_without_loop_is_registered_now_without_version(self):
        respuesta = self.responder('/tarea Exportar informe')
        self.assertEqual(respuesta, 'Registrada T-ADV-0003: Exportar informe (backlog, sin versión).')
        fm = motor.frontmatter(self.root / 'docs/plan/tasks/T-ADV-0003-exportar-informe.md')
        self.assertEqual((fm['status'], fm['version']), ('backlog', ''))
        self.assertIn('T-ADV-0003', self.git('log', '-1', '--format=%s'))

    def test_bug_without_loop_is_registered_now(self):
        self.assertIn('B-ADV-0001', self.responder('/bug@AdevvBot El login falla'))
        self.assertTrue((self.root / 'docs/plan/bugs/B-ADV-0001-el-login-falla.md').exists())

    def test_with_loop_running_only_the_inbox_is_written(self):
        (self.root / motor.PID).write_text('1', encoding='utf-8')
        antes = self.backlog()
        self.assertIn('Apuntado', self.responder('/tarea Exportar informe'))
        self.assertEqual(self.backlog(), antes)
        self.assertIn('Exportar informe', (self.root / motor.BUZON).read_text(encoding='utf-8'))

    def test_empty_title_asks_for_usage(self):
        self.assertEqual(self.responder('/tarea'), 'Uso: /tarea <título>')
        self.assertFalse((self.root / motor.BUZON).exists())

    def test_status_summarizes_loop_version_and_backlog(self):
        (self.root / motor.PID).write_text('1', encoding='utf-8')
        motor.apuntar(self.root, 'bug', 'Pendiente', '12345')
        with patch.object(motor, 'git', return_value=''):
            texto = self.responder('/status')
        self.assertIn('bucle en marcha', texto)
        self.assertIn('v0.1.0:* 0/1 cerradas · en curso T-ADV-0002', texto)
        self.assertIn('Por registrar:* 1', texto)

    def test_unauthorized_other_messages_are_ignored(self):
        self.assertIsNone(self.responder('hola', usuario='99999'))

    def test_free_conversation_invokes_model_and_saves_session(self):
        with patch.object(gateway, 'invocar', return_value=(0, 'sess-101', 'Hola, soy el asistente.')) as inv:
            resp = self.responder('Hola, ¿qué hace este proyecto?')
        self.assertEqual(resp, 'Hola, soy el asistente.')
        self.assertEqual(inv.call_count, 1)
        self.assertIsNone(inv.call_args.kwargs['sesion'])
        sesiones_file = self.root / getattr(motor, 'TELEGRAM_SESIONES', 'orquestar_telegram.json')
        self.assertTrue(sesiones_file.exists())
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'claude'), 'sess-101')

    def test_conversation_coexistence_with_telegram_false_inherits_atenea(self):
        cfg = {
            'atenea': {'harness': 'codex', 'model': 'model-atenea'},
            'telegram': False,
        }
        with patch.object(motor, 'config', return_value=cfg), \
             patch.object(gateway, 'invocar', return_value=(0, 'sess-tg', 'Respuesta')) as inv:
            resp = self.responder('Hola')
        self.assertEqual(resp, 'Respuesta')
        inv.assert_called_once()
        cfg_usada = inv.call_args.args[2] if len(inv.call_args.args) > 2 else inv.call_args.kwargs.get('cfg')
        self.assertEqual(cfg_usada.get('harness'), 'codex')
        self.assertEqual(cfg_usada.get('model'), 'model-atenea')

    def test_conversation_coexistence_with_telegram_events_dict_inherits_atenea(self):
        cfg = {
            'atenea': {'harness': 'codex', 'model': 'model-atenea', 'effort': 'high'},
            'telegram': {'eventos': ['version'], 'model': 'model-overridden'},
        }
        with patch.object(motor, 'config', return_value=cfg), \
             patch.object(gateway, 'invocar', return_value=(0, 'sess-tg', 'Respuesta')) as inv:
            resp = self.responder('Hola')
        self.assertEqual(resp, 'Respuesta')
        inv.assert_called_once()
        cfg_usada = inv.call_args.args[2] if len(inv.call_args.args) > 2 else inv.call_args.kwargs.get('cfg')
        self.assertEqual(cfg_usada.get('harness'), 'codex')
        self.assertEqual(cfg_usada.get('model'), 'model-overridden')
        self.assertEqual(cfg_usada.get('effort'), 'high')

    def test_conversation_reuses_existing_session(self):
        gateway.guardar_sesion(self.root, '12345', 'claude', 'sess-existente')
        with patch.object(gateway, 'invocar', return_value=(0, 'sess-renovada', 'Respuesta continua.')) as inv:
            resp = self.responder('Siguiente duda')
        self.assertEqual(resp, 'Respuesta continua.')
        inv.assert_called_once()
        self.assertEqual(inv.call_args.kwargs['sesion'], 'sess-existente')
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'claude'), 'sess-renovada')

    def test_conversation_fallback_to_new_session_on_resume_failure(self):
        gateway.guardar_sesion(self.root, '12345', 'claude', 'sess-invalida')
        with patch.object(gateway, 'invocar', side_effect=[
            (1, None, 'error al reanudar'),
            (0, 'sess-nueva', 'Respuesta en sesion nueva.')
        ]) as inv:
            resp = self.responder('Pregunta tras fallo')
        self.assertEqual(resp, 'Respuesta en sesion nueva.')
        self.assertEqual(inv.call_count, 2)
        self.assertEqual(inv.call_args_list[0].kwargs['sesion'], 'sess-invalida')
        self.assertIsNone(inv.call_args_list[1].kwargs['sesion'])
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'claude'), 'sess-nueva')

    def test_nuevo_and_reset_clears_session_and_confirms(self):
        gateway.guardar_sesion(self.root, '12345', 'claude', 'sess-a-borrar')
        gateway.guardar_sesion(self.root, '67890', 'claude', 'sess-otra')
        resp_nuevo = self.responder('/nuevo')
        self.assertIn('reiniciado', resp_nuevo.lower())
        self.assertIsNone(gateway.obtener_sesion(self.root, '12345', 'claude'))
        self.assertEqual(gateway.obtener_sesion(self.root, '67890', 'claude'), 'sess-otra')

        gateway.guardar_sesion(self.root, '12345', 'claude', 'sess-2')
        resp_reset = self.responder('/reset')
        self.assertIn('reiniciado', resp_reset.lower())
        self.assertIsNone(gateway.obtener_sesion(self.root, '12345', 'claude'))

    def test_prompt_includes_safety_notice_when_loop_is_running(self):
        prompt_sin_bucle = gateway.construir_prompt(self.root, 'Hola')
        self.assertNotIn('no debes modificar ni commitear', prompt_sin_bucle.lower())

        (self.root / motor.PID).write_text('1234', encoding='utf-8')
        prompt_con_bucle = gateway.construir_prompt(self.root, 'Hola')
        self.assertIn('orquestar.pid', prompt_con_bucle)
        self.assertIn('no debes modificar ni commitear', prompt_con_bucle.lower())
        self.assertIn('apuntar', prompt_con_bucle.lower())

        with patch.object(gateway, 'invocar', return_value=(0, 'sess-pid', 'Respuesta segura')) as inv:
            self.responder('¿Qué puedes hacer?')
        inv.assert_called_once()
        prompt_enviado = inv.call_args.args[1] if len(inv.call_args.args) > 1 else inv.call_args.kwargs.get('prompt')
        self.assertIn('orquestar.pid', prompt_enviado)

    def test_help_documents_nuevo_and_free_conversation(self):
        ayuda = self.responder('/ayuda')
        self.assertIn('/nuevo', ayuda)
        self.assertIn('asistente', ayuda.lower())
        start = self.responder('/start')
        self.assertEqual(start, ayuda)

    def test_polling_answers_in_the_chat_and_survives_a_failing_message(self):
        updates = [{'update_id': 1, 'message': {'from': {'id': 12345}, 'chat': {'id': 555}, 'text': '/estado'}},
                   {'update_id': 2, 'message': {'from': {'id': 99999}, 'chat': {'id': 556}, 'text': '/estado'}},
                   {'update_id': 3, 'message': {'from': {'id': 12345}, 'chat': {'id': 555}, 'text': '/ayuda'}}]
        with (patch.object(gateway, 'actualizaciones', return_value=updates) as act,
              patch.object(gateway, 'responder', side_effect=[RuntimeError('x'), None, 'ayuda']),
              patch.object(motor, 'enviar') as enviar):
            gateway.escuchar(self.root, 'tok', AUTORIZADOS, vueltas=1)
        act.assert_called_once_with('tok', None)
        self.assertEqual([c.args[1:3] for c in enviar.call_args_list],
                         [(555, 'No he podido procesarlo; mira el log del gateway.'), (555, 'ayuda')])



    def test_credenciales_reads_from_env_file(self):
        env_file = self.root / '.env'
        env_file.write_text('TELEGRAM_BOT_TOKEN=token_archivo\nTELEGRAM_ALLOWED_USER_IDS="111, 222"\n', encoding='utf-8')
        tok, usr = motor.credenciales(self.root)
        self.assertEqual(tok, 'token_archivo')
        self.assertEqual(usr, ['111', '222'])

    def test_credenciales_falls_back_to_os_environ(self):
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'token_env', 'TELEGRAM_ALLOWED_USER_IDS': '333, 444'}):
            tok, usr = motor.credenciales(self.root)
            self.assertEqual(tok, 'token_env')
            self.assertEqual(usr, ['333', '444'])

    def test_credenciales_env_file_takes_precedence(self):
        env_file = self.root / '.env'
        env_file.write_text('TELEGRAM_BOT_TOKEN=token_local\n', encoding='utf-8')
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'token_global', 'TELEGRAM_ALLOWED_USER_IDS': '555'}):
            tok, usr = motor.credenciales(self.root)
            self.assertEqual(tok, 'token_local')
            self.assertEqual(usr, ['555'])


if __name__ == '__main__':
    unittest.main()
