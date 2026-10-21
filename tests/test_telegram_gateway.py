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

    def test_other_messages_are_ignored(self):
        self.assertIsNone(self.responder('hola'))
        self.assertIn('/tarea', self.responder('/start'))

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


if __name__ == '__main__':
    unittest.main()
