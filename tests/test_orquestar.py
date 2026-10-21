import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    'orquestar', Path(__file__).resolve().parents[1] / 'skills/orquestar/orquestar.py')
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


class OrquestarRegressionTests(unittest.TestCase):
    def test_failed_capture_neither_reads_nor_writes_validation_evidence(self):
        for failed_command in ('add', 'write-tree'):
            with self.subTest(command=failed_command), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                evidence = root / motor.EVIDENCIAS
                previous = '{"arbol":"' + 'a' * 40 + '","comando":"suite","codigo":0}\n'
                evidence.write_text(previous, encoding='utf-8')

                def run(command, **kwargs):
                    if command[1] == failed_command:
                        self.assertTrue(kwargs['check'])
                        raise subprocess.CalledProcessError(128, command)
                    return subprocess.CompletedProcess(command, 0, stdout='a' * 40)

                with patch.object(motor, 'excluir'), patch.object(motor.subprocess, 'run', side_effect=run) as calls:
                    with self.assertRaises(subprocess.CalledProcessError):
                        motor.verificar(root, 'suite')
                self.assertEqual(evidence.read_text(encoding='utf-8'), previous)
                self.assertEqual(calls.call_count, 1 if failed_command == 'add' else 2)

    def test_invalid_tree_hash_is_rejected(self):
        with patch.object(motor.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout='')):
            with self.assertRaises(RuntimeError):
                motor.arbol(Path('.'))

    def test_content_changes_affect_signature_with_identical_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True, capture_output=True)
            source = root / 'source.py'
            source.write_text('first\n', encoding='utf-8')
            subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
            index_before = (root / '.git/index').read_bytes()
            with (patch.object(motor, 'estado', return_value=('PASO', 'task-dev')),
                 patch.object(motor, 'git', return_value='unchanged'),
                  patch.object(motor, 'backlog', return_value=[])):
                before = motor.firma(root, 'docs')
                self.assertEqual(before, motor.firma(root, 'docs'))
                source.write_text('second\n', encoding='utf-8')
                self.assertNotEqual(before, motor.firma(root, 'docs'))
                report = root / 'report.md'
                report.write_text('first finding\n', encoding='utf-8')
                before = motor.firma(root, 'docs')
                report.write_text('revised finding\n', encoding='utf-8')
                self.assertNotEqual(before, motor.firma(root, 'docs'))
            self.assertEqual((root / '.git/index').read_bytes(), index_before)

    def test_future_version_dependency_is_rejected(self):
        def items(first, second):
            return [{'id': 'T1', 'version': first, 'depende_de': ['T2']},
                    {'id': 'T2', 'version': second, 'depende_de': []}]

        self.assertEqual(len(motor.errores_dependencias(items('v0.9', 'v0.10'))), 1)
        for first, second in [('v0.10', 'v0.9'), ('v0.1', 'v0.1'), ('', 'v0.1')]:
            self.assertEqual(motor.errores_dependencias(items(first, second)), [])
        self.assertTrue(motor.errores_dependencias([
            {'id': 'T1', 'version': 'v0.1', 'depende_de': ['missing']}]))
        self.assertTrue(motor.errores_dependencias([
            {'id': 'T1', 'depende_de': ['T2']}, {'id': 'T2', 'depende_de': ['T1']}]))

    def test_suite_runs_at_version_close_not_after_each_task(self):
        self.assertTrue(motor.cierre_de_version(('PASO', 'revisar-version', 'v0.1', 'release/v0.1')))
        self.assertTrue(motor.cierre_de_version(('PARAR', 'Versión v0.1 terminada. Revisa')))
        self.assertTrue(motor.cierre_de_version(('PARAR', 'Bloqueos en v0.1: bloqueadas T1')))
        self.assertFalse(motor.cierre_de_version(('PASO', 'task-dev', 'T1', 'release/v0.1')))
        self.assertFalse(motor.cierre_de_version(('PARAR', 'Falta task_config.yaml en la raíz del proyecto.')))

    def test_red_suite_at_version_close_stops_before_review(self):
        args = motor.argparse.Namespace(idea=None, docs='docs', test='suite', harness='claude', estado=False,
                                        max_pasos=3, reintentos=2, espera_max=0, cmd=None)
        with tempfile.TemporaryDirectory() as directory:
            with (patch.object(motor, 'estado', return_value=('PASO', 'revisar-version', 'v0.1', None)),
                  patch.object(motor, 'config', return_value={}),
                  patch.object(motor, 'verificar', return_value=1) as verificar,
                  patch.object(motor, 'ejecutar') as ejecutar):
                self.assertEqual(motor.bucle(args, Path(directory)), 2)
        verificar.assert_called_once()
        ejecutar.assert_not_called()


class RevisionProductoTests(unittest.TestCase):
    """Versión v0.1 cerrada (tarea completada y revisada, revisión de arquitectura hecha) y v0.2 pendiente."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for f, texto in [('task_config.yaml', ''), ('docs/requirements.md', 'idea'),
                         ('docs/req_analysis.md', '**Estado:** ASUNCIONES_REALIZADAS'),
                         ('docs/platform_plan.md', ''), ('docs/platform_review.md', '**Veredicto:** APROBADO'),
                         ('docs/work_plan.md', ''), ('docs/review/code_reviews/T1-code-review.md', ''),
                         ('docs/review/versions/v0.1-arquitectura.md', '')]:
            (self.root / f).parent.mkdir(parents=True, exist_ok=True)
            (self.root / f).write_text(texto, encoding='utf-8')
        self.items = [{'paso': 'task-dev', 'id': 'T1', 'status': 'completed', 'version': 'v0.1.0',
                       'depende_de': [], 'weight': 0},
                      {'paso': 'task-dev', 'id': 'T2', 'status': 'planned', 'version': 'v0.2.0',
                       'depende_de': [], 'weight': 0}]

    def tearDown(self):
        self.tmp.cleanup()

    def estado(self, producto=None, rama='release/v0.1', decision=None):
        if decision:
            (self.root / motor.PRODUCTO.format(v='v0.1')).write_text(f'**Decisión:** {decision}\n', encoding='utf-8')
        cfg = {} if producto is None else {'producto': producto}
        with (patch.object(motor, 'backlog', return_value=self.items),
              patch.object(motor, 'config', return_value=cfg),
              patch.object(motor, 'git', side_effect=lambda *a, **k: rama if 'branch' in a else '')):
            return motor.estado(self.root, 'docs')

    def test_disabled_keeps_current_version_stop(self):
        for producto in (None, False, ['v0.2']):
            with self.subTest(producto=producto):
                e = self.estado(producto)
                self.assertEqual(e[0], 'PARAR')
                self.assertTrue(e[1].startswith('Versión v0.1 terminada'))
                self.assertNotIn('producto', e[1])

    def test_enabled_without_report_runs_review(self):
        for producto in (True, ['v0.1'], ['0.1']):
            with self.subTest(producto=producto):
                self.assertEqual(self.estado(producto), ('PASO', 'revisar-producto', 'v0.1', 'release/v0.1'))

    def test_decisions_drive_the_version_stop(self):
        e = self.estado(True, decision='PENDIENTE')
        self.assertEqual(e[0], 'PARAR')
        self.assertTrue(motor.cierre_de_version(e))
        self.assertIn('APLICAR', e[1])
        self.assertEqual(self.estado(True, decision='APLICAR'), ('PASO', 'aplicar-producto', 'v0.1', 'release/v0.1'))
        self.assertTrue(self.estado(True, decision='APLICADA')[1].startswith('Versión v0.1 terminada'))

    def test_pending_decisions_block_next_version_after_release(self):
        e = self.estado(True, rama='', decision='PENDIENTE')
        self.assertEqual(e[0], 'PARAR')
        self.assertIn('v0.1-producto.md', e[1])
        self.assertEqual(self.estado(True, rama='', decision='APLICAR'), ('PASO', 'aplicar-producto', 'v0.1', None))
        self.assertEqual(self.estado(True, rama='', decision='APLICADA'), ('PASO', 'start-version', 'v0.2', None))


class EnrutadoBloqueoTests(unittest.TestCase):
    """Tarea bloqueada en v0.1 según a quién la envió Hades, junto a otra elegible."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for f, texto in [('task_config.yaml', ''), ('docs/requirements.md', 'idea'),
                         ('docs/req_analysis.md', ''), ('docs/platform_plan.md', ''),
                         ('docs/platform_review.md', '**Veredicto:** APROBADO'), ('docs/work_plan.md', '')]:
            (self.root / f).parent.mkdir(parents=True, exist_ok=True)
            (self.root / f).write_text(texto, encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def estado(self, pendiente_de, otra='planned'):
        items = [{'paso': 'task-dev', 'id': 'T1', 'status': 'blocked', 'pendiente_de': pendiente_de,
                  'version': 'v0.1.0', 'depende_de': [], 'weight': 0},
                 {'paso': 'task-dev', 'id': 'T2', 'status': otra, 'pendiente_de': '',
                  'version': 'v0.1.0', 'depende_de': [], 'weight': 0}]
        with (patch.object(motor, 'backlog', return_value=items), patch.object(motor, 'config', return_value={}),
              patch.object(motor, 'revisada', return_value=True),
              patch.object(motor, 'git', side_effect=lambda *a, **k: 'release/v0.1' if 'branch' in a else '')):
            return motor.estado(self.root, 'docs')

    def test_specifier_gets_the_task(self):
        self.assertEqual(self.estado('especificador'), ('PASO', 'especificar', 'T1', 'release/v0.1'))

    def test_backlog_reads_who_the_task_waits_for(self):
        tarea = self.root / 'docs/plan/tasks/T1.md'
        tarea.parent.mkdir(parents=True)
        tarea.write_text('---\nid: T1\nstatus: blocked\npendiente_de: Especificador \n---\n', encoding='utf-8')
        self.assertEqual(motor.backlog(self.root)[0]['pendiente_de'], 'especificador')

    def test_specifier_starts_with_the_block_that_holds_more_tasks(self):
        items = [{'paso': 'task-dev', 'id': i, 'status': 'blocked', 'pendiente_de': 'especificador',
                  'version': 'v0.1.0', 'depende_de': [], 'weight': 0} for i in ('T1', 'T3')]
        items.append({'paso': 'task-dev', 'id': 'T4', 'status': 'planned', 'pendiente_de': '',
                      'version': 'v0.1.0', 'depende_de': ['T3'], 'weight': 0})
        with (patch.object(motor, 'backlog', return_value=items), patch.object(motor, 'config', return_value={}),
              patch.object(motor, 'git', side_effect=lambda *a, **k: 'release/v0.1' if 'branch' in a else '')):
            self.assertEqual(motor.estado(self.root, 'docs'), ('PASO', 'especificar', 'T3', 'release/v0.1'))

    def test_human_block_lets_the_rest_continue(self):
        for pendiente_de in ('humano', ''):
            with self.subTest(pendiente_de=pendiente_de):
                self.assertEqual(self.estado(pendiente_de), ('PASO', 'task-dev', 'T2', 'release/v0.1'))

    def test_human_block_stops_only_at_version_end(self):
        (self.root / 'docs/review/versions').mkdir(parents=True)
        (self.root / 'docs/review/versions/v0.1-arquitectura.md').write_text('', encoding='utf-8')
        e = self.estado('humano', otra='completed')
        self.assertEqual(e[0], 'PARAR')
        self.assertIn('bloqueadas T1', e[1])


if __name__ == '__main__':
    unittest.main()
