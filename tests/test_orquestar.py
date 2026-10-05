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


if __name__ == '__main__':
    unittest.main()
