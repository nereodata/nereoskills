import importlib.util
import shutil
import subprocess
import io
import os
import urllib.error
import urllib.request
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tests import aislamiento_telegram


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
        self.assertEqual(respuesta, motor.firmar('Registrada T-ADV-0003: Exportar informe (backlog, sin versión).'))
        fm = motor.frontmatter(self.root / 'docs/plan/tasks/T-ADV-0003-exportar-informe.md')
        self.assertEqual((fm['status'], fm['version']), ('backlog', ''))
        self.assertIn('T-ADV-0003', self.git('log', '-1', '--format=%s'))

    def test_bug_without_loop_is_registered_now(self):
        self.assertIn('B-ADV-0001', self.responder('/bug@AdevvBot El login falla'))
        self.assertTrue((self.root / 'docs/plan/bugs/B-ADV-0001-el-login-falla.md').exists())

    def test_with_loop_running_only_the_inbox_is_written(self):
        (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
        antes = self.backlog()
        with patch.object(motor, 'pid_vivo', return_value=True):
            self.assertIn('Apuntado', self.responder('/tarea Exportar informe'))
        self.assertEqual(self.backlog(), antes)
        self.assertIn('Exportar informe', (self.root / motor.BUZON).read_text(encoding='utf-8'))

    def test_empty_title_asks_for_usage(self):
        self.assertEqual(self.responder('/tarea'), motor.firmar('Uso: /tarea <título>'))
        self.assertFalse((self.root / motor.BUZON).exists())

    def test_status_summarizes_loop_version_and_backlog(self):
        (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
        motor.apuntar(self.root, 'bug', 'Pendiente', '12345')
        with patch.object(motor, 'pid_vivo', return_value=True), \
                patch.object(motor, 'git', return_value=''):
            texto = self.responder('/status')
        self.assertIn('bucle en marcha', texto)
        self.assertIn('v0.1.0:* 0/1 cerradas · en curso T-ADV-0002', texto)
        self.assertIn('Por registrar:* 1', texto)

    def test_unauthorized_other_messages_are_ignored(self):
        self.assertIsNone(self.responder('hola', usuario='99999'))

    def test_free_conversation_invokes_model_and_saves_session(self):
        with patch.object(gateway, 'invocar', return_value=(0, 'sess-101', 'Hola, soy el asistente.')) as inv:
            resp = self.responder('Hola, ¿qué hace este proyecto?')
        self.assertEqual(resp, motor.firmar('Hola, soy el asistente.', extra='claude/predeterminado'))
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
        self.assertEqual(resp, motor.firmar('Respuesta', extra='codex/model-atenea'))
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
        self.assertEqual(resp, motor.firmar('Respuesta', extra='codex/model-overridden'))
        inv.assert_called_once()
        cfg_usada = inv.call_args.args[2] if len(inv.call_args.args) > 2 else inv.call_args.kwargs.get('cfg')
        self.assertEqual(cfg_usada.get('harness'), 'codex')
        self.assertEqual(cfg_usada.get('model'), 'model-overridden')
        self.assertEqual(cfg_usada.get('effort'), 'high')

    def test_conversation_reuses_existing_session(self):
        gateway.guardar_sesion(self.root, '12345', 'claude', 'sess-existente')
        with patch.object(gateway, 'invocar', return_value=(0, 'sess-renovada', 'Respuesta continua.')) as inv:
            resp = self.responder('Siguiente duda')
        self.assertEqual(resp, motor.firmar('Respuesta continua.', extra='claude/predeterminado'))
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
        self.assertEqual(resp, motor.firmar('Respuesta en sesion nueva.', extra='claude/predeterminado'))
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
                         [(555, motor.firmar('No he podido procesarlo; mira el log del gateway.')),
                          (555, 'ayuda')])



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


    def test_actualizaciones_409_conflict_logs_and_raises(self):
        err = urllib.error.HTTPError('https://api.telegram.org', 409, 'Conflict', {}, io.BytesIO(b'{}'))
        with patch('urllib.request.urlopen', side_effect=err), \
             patch('time.sleep'), \
             patch('builtins.print') as mock_print:
            with self.assertRaises(urllib.error.HTTPError):
                gateway.actualizaciones('fake_token', espera=1)
            mock_print.assert_called_with(
                '[gateway] conflicto 409 en Telegram: otra instancia está escuchando con el mismo token',
                flush=True
            )

    def test_escuchar_stops_on_409_when_not_owner_of_pid(self):
        err = urllib.error.HTTPError('https://api.telegram.org', 409, 'Conflict', {}, io.BytesIO(b'{}'))
        (self.root / 'telegram.pid').write_text('999999', encoding='utf-8')
        with patch.object(gateway, 'actualizaciones', side_effect=err), \
             patch('builtins.print') as mock_print:
            gateway.escuchar(self.root, 'tok', AUTORIZADOS, vueltas=5)
            self.assertTrue(any('conflicto 409' in str(c) for c in mock_print.call_args_list))

    def test_escuchar_stops_after_three_consecutive_409_conflicts_for_owner(self):
        err = urllib.error.HTTPError('https://api.telegram.org', 409, 'Conflict', {}, io.BytesIO(b'{}'))
        (self.root / 'telegram.pid').write_text(str(os.getpid()), encoding='utf-8')
        calls = []

        def mock_actualizaciones(*args, **kwargs):
            calls.append(1)
            raise err

        with patch.object(gateway, 'actualizaciones', side_effect=mock_actualizaciones), \
             patch('builtins.print') as mock_print:
            gateway.escuchar(self.root, 'tok', AUTORIZADOS, vueltas=10)
            self.assertEqual(len(calls), 3)
            self.assertTrue(any('deteniendo escucha por conflicto 409' in str(c) for c in mock_print.call_args_list))

    def test_buscar_ejecutable_resolves_fallback_user_path_on_windows(self):
        with tempfile.TemporaryDirectory() as fake_home:
            user_bin = Path(fake_home) / '.local/bin'
            user_bin.mkdir(parents=True)
            fake_claude = user_bin / ('claude.cmd' if os.name == 'nt' else 'claude')
            fake_claude.write_text('echo fake claude', encoding='utf-8')
            if os.name != 'nt':
                fake_claude.chmod(0o755)

            real_which = shutil.which
            def mock_which(cmd, mode=os.F_OK | os.X_OK, path=None):
                if path is None:
                    return None
                return real_which(cmd, mode, path)

            with patch('shutil.which', side_effect=mock_which), \
                 patch('pathlib.Path.home', return_value=Path(fake_home)), \
                 patch.dict(os.environ, {'PATH': ''}, clear=True):
                if hasattr(motor, 'buscar_ejecutable'):
                    res = motor.buscar_ejecutable('claude')
                else:
                    res = None
                self.assertIsNotNone(res)
                self.assertEqual(Path(res).stem.lower(), 'claude')

    def test_buscar_ejecutable_expands_registry_variables_such_as_userprofile(self):
        with tempfile.TemporaryDirectory() as fake_custom:
            custom_bin = Path(fake_custom) / 'custom_bin'
            custom_bin.mkdir()
            fake_exe = custom_bin / ('custom_arnes.cmd' if os.name == 'nt' else 'custom_arnes')
            fake_exe.write_text('echo fake', encoding='utf-8')
            if os.name != 'nt':
                fake_exe.chmod(0o755)

            with patch.dict(os.environ, {'MY_CUSTOM_DIR': fake_custom, 'PATH': ''}, clear=True):
                class FakeWinreg:
                    HKEY_CURRENT_USER = 1
                    REG_EXPAND_SZ = 2

                    @staticmethod
                    def OpenKey(*args):
                        class Key:
                            def __enter__(self):
                                return self

                            def __exit__(self, *a):
                                pass

                        return Key()

                    @staticmethod
                    def QueryValueEx(k, name):
                        return '%MY_CUSTOM_DIR%\\custom_bin', 2

                    @staticmethod
                    def ExpandEnvironmentStrings(s):
                        return os.path.expandvars(s)

                with patch.object(motor, 'winreg', FakeWinreg), \
                     patch('pathlib.Path.home', return_value=Path(fake_custom)):
                    res = motor.buscar_ejecutable('custom_arnes')
                    self.assertIsNotNone(res)
                    self.assertEqual(Path(res).resolve(), fake_exe.resolve())


if __name__ == '__main__':
    unittest.main()
