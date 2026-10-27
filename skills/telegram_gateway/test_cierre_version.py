"""Contrato del cierre remoto con repositorios y remoto bare sin red."""

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tests import aislamiento_telegram


SPEC = importlib.util.spec_from_file_location('gateway_cierre', Path(__file__).with_name('gateway.py'))
gateway = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gateway)
motor = gateway.motor


class CierreTests(unittest.TestCase):
    """Cada prueba empieza con una release elegible y Git local real."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.root.mkdir()
        self.remote = Path(self.tmp.name) / 'remote.git'
        self.env = patch.dict(os.environ, {'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        self.git('remote', 'add', 'origin', str(self.remote))
        self.write('task_config.yaml', 'project:\n  version: v1.0.0\nrelease:\n  manifests:\n    - path: pyproject.toml\n      type: toml\n      key: project.version\n  preflight:\n    - python -c "raise SystemExit(0)"\n')
        self.write('pyproject.toml', '[project]\nversion = "1.0.0"\n')
        self.write('CHANGELOG.md', '## [v1.0.0]\nCambio\n')
        self.write('shared.txt', 'base\n')
        for name in ('requirements', 'req_analysis', 'platform_plan', 'platform_review', 'work_plan'):
            self.write(f'docs/requirements/{name}.md', 'APROBADO\n')
        self.task('completed')
        self.write('docs/review/code_reviews/T-DEMO-0001-code-review.md', 'APROBADO\n')
        self.write('docs/review/versions/v1.0-arquitectura.md', 'APROBADO\n')
        self.write('docs/review/versions/v1.0-revision.md', '## T-DEMO-0001\n- Bloqueos: ninguno\n- Validación funcional: Abrir la pantalla\n')
        self.commit()
        self.git('push', '-q', 'origin', 'main')
        self.git('checkout', '-qb', 'release/v1.0')
        self.write('release.txt', 'entrega\n')
        self.commit()
        self.oldcwd = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.oldcwd)
        self.launch = patch.object(motor, 'en_fondo')
        self.launcher = self.launch.start()
        self.addCleanup(self.launch.stop)
        conversation = patch.object(gateway, 'conversar', return_value='Comando de cierre ausente')
        conversation.start()
        self.addCleanup(conversation.stop)

    def git(self, *args):
        """Ejecuta Git únicamente en el repositorio temporal."""
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

    def write(self, name, value):
        """Escribe una fixture temporal."""
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding='utf-8')

    def task(self, status):
        """Prepara el ítem de la versión que se cierra."""
        self.write('docs/plan/tasks/task.md', f'---\nid: T-DEMO-0001\nversion: v1.0.0\nstatus: {status}\ndepende_de: []\n---\n')

    def commit(self):
        """Confirma el estado de la fixture."""
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def snapshot(self):
        """Observa referencias, índice y archivos antes y después de actuar."""
        files = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*')
                 if p.is_file() and '.git' not in p.relative_to(self.root).parts}
        return (self.git('show-ref'), self.git('branch', '--show-current'),
                self.git('ls-files', '--stage'), files, self.git('ls-remote', 'origin'))

    def respond(self, text='/cerrar v1.0 confirmo', user='111'):
        """Usa la entrada pública sin transporte Telegram."""
        return gateway.responder(self.root, user, text, {'111'})

    def test_summary_and_confirmation_do_not_write(self):
        before = self.snapshot()
        response = self.respond('/cerrar v1.0')
        for fragment in ('T-DEMO-0001', 'Bloqueos', 'Abrir la pantalla', '/cerrar v1.0 confirmo'):
            self.assertIn(fragment, response)
        self.assertEqual(before, self.snapshot())
        self.launcher.assert_not_called()
        with patch.object(motor, 'telegram', return_value=('ficticio', ['111'], {'version'})), patch.object(motor, 'enviar', return_value=True) as send:
            motor.avisar(self.root, 'version', 'Versión v1.0 terminada.')
        for fragment in ('T-DEMO-0001', 'Bloqueos', 'Abrir la pantalla', '/cerrar v1.0 confirmo'):
            self.assertIn(fragment, send.call_args.args[2])

    def assert_publication(self, status, following):
        """Comprueba cada ejemplo de cierre completo, incluida la etiqueta remota."""
        self.task(status)
        if following:
            self.write('docs/plan/tasks/next.md', '---\nid: T-DEMO-0002\nversion: v1.1.0\nstatus: planned\ndepende_de: []\n---\n')
        if self.git('status', '--porcelain'):
            self.commit()
        release = self.git('rev-parse', 'HEAD')
        response = self.respond()
        self.assertIn('v1.0.0', response)
        self.assertEqual(self.git('branch', '--show-current'), 'main')
        self.assertEqual(self.git('branch', '--list', 'release/v1.0'), '')
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual(self.git('cat-file', '-t', 'v1.0.0'), 'tag')
        main = self.git('rev-parse', 'main')
        self.assertEqual(main, self.git('rev-parse', 'v1.0.0^{}'))
        self.assertIn(release, self.git('rev-list', '--parents', '-1', 'main'))
        remote = dict(line.split()[::-1] for line in self.git('ls-remote', 'origin').splitlines())
        self.assertEqual(main, remote['refs/heads/main'])
        self.assertEqual(main, remote['refs/tags/v1.0.0^{}'])
        self.assertEqual(self.git('rev-parse', 'v1.0.0'), remote['refs/tags/v1.0.0'])
        if following:
            self.assertIn('segundo plano', response)
            self.launcher.assert_called_once_with(self.root, argumentos=[])
        else:
            self.assertIn('FIN', response)
            self.launcher.assert_not_called()

    def test_cancelled_and_continuation(self):
        self.assert_publication('cancelled', True)

    def test_completed_and_continuation(self):
        self.assert_publication('completed', True)

    def test_completed_and_finish(self):
        self.assert_publication('completed', False)

    def test_cancelled_and_finish(self):
        self.assert_publication('cancelled', False)

    def test_reject_each_precondition(self):
        cases = {
            'pid': 'PID', 'main': 'release/v1.0', 'version': 'revisión final',
            'planned': 'planned', 'in_progress': 'in_progress', 'blocked': 'bloqueo',
            'manual': 'revisión final', 'architecture': 'arquitectura',
            'product_pending': 'producto', 'product_apply': 'aplicar',
            'tracked': 'sucio', 'untracked': 'sucio', 'manifest': 'manifiesto',
            'changelog': 'changelog', 'preflight': 'preflight', 'local_tag': 'local', 'remote_tag': 'remota',
        }
        for case, fragment in cases.items():
            with self.subTest(case=case):
                self.git('checkout', 'release/v1.0')
                self.git('reset', '--hard', 'HEAD')
                base = self.git('rev-parse', 'HEAD')
                if case == 'pid': self.write(motor.PID, '999999')
                elif case == 'main': self.git('checkout', 'main')
                elif case in ('planned', 'in_progress', 'blocked'): self.task(case)
                elif case == 'manual': self.write(motor.PARADA, '')
                elif case == 'architecture': (self.root / 'docs/review/versions/v1.0-arquitectura.md').unlink()
                elif case.startswith('product_'): self.write('docs/review/versions/v1.0-producto.md', '**Decisión:** ' + ('PENDIENTE' if case.endswith('pending') else 'APLICAR'))
                elif case == 'tracked': self.write('shared.txt', 'dirty')
                elif case == 'untracked': self.write('new.txt', 'dirty')
                elif case == 'manifest': self.write('pyproject.toml', '[project]\nversion = "0.9.0"\n')
                elif case == 'changelog': self.write('CHANGELOG.md', '## [v0.9.0]\n')
                elif case == 'preflight': self.write('task_config.yaml', (self.root / 'task_config.yaml').read_text().replace('SystemExit(0)', 'SystemExit(1)'))
                elif case in ('local_tag', 'remote_tag'):
                    self.git('tag', 'v1.0.0')
                    if case == 'remote_tag':
                        self.git('push', '-q', 'origin', 'v1.0.0')
                        self.git('tag', '-d', 'v1.0.0')
                if case not in ('tracked', 'untracked', 'main', 'local_tag', 'remote_tag', 'version'):
                    self.commit()
                try:
                    before = self.snapshot()
                    response = self.respond('/cerrar v0.9 confirmo' if case == 'version' else '/cerrar v1.0 confirmo')
                    self.assertIn(fragment, response)
                    self.assertEqual(before, self.snapshot())
                    self.launcher.assert_not_called()
                finally:
                    self.git('checkout', 'release/v1.0')
                    self.git('reset', '--hard', base)
                    for name in (motor.PID, motor.PARADA, 'new.txt', 'docs/review/versions/v1.0-producto.md'):
                        (self.root / name).unlink(missing_ok=True)
                    if case == 'local_tag': self.git('tag', '-d', 'v1.0.0')
                    if case == 'remote_tag': self.git('push', '-q', '--delete', 'origin', 'v1.0.0')

    def test_unauthorized_is_silent(self):
        before = self.snapshot()
        self.assertIsNone(self.respond(user='222'))
        self.assertEqual(before, self.snapshot())
        self.launcher.assert_not_called()

    def test_push_failure_rolls_back(self):
        hook = self.remote / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\necho rechazo-test >&2\nexit 1\n', encoding='utf-8')
        hook.chmod(0o755)
        before = self.snapshot()
        self.assertIn('rechazo-test', self.respond())
        self.assertEqual(before, self.snapshot())
        self.launcher.assert_not_called()

    def test_atomic_unsupported_rolls_back(self):
        subprocess.run(['git', '--git-dir', str(self.remote), 'config', 'receive.advertiseAtomic', 'false'], check=True)
        before = self.snapshot()
        self.assertIn('atomic', self.respond())
        self.assertEqual(before, self.snapshot())
        self.launcher.assert_not_called()

    def test_merge_conflict_rolls_back(self):
        self.write('shared.txt', 'release\n')
        self.commit()
        self.git('checkout', 'main')
        self.write('shared.txt', 'main actualizado\n')
        self.commit()
        self.git('push', '-q', 'origin', 'main')
        self.git('checkout', 'release/v1.0')
        before = self.snapshot()
        self.assertIn('CONFLICT', self.respond())
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.root / '.git/MERGE_HEAD').exists())
        self.launcher.assert_not_called()

    def test_launch_failure_keeps_publication(self):
        self.write('docs/plan/tasks/next.md', '---\nid: T-DEMO-0002\nversion: v1.1.0\nstatus: planned\ndepende_de: []\n---\n')
        self.commit()
        self.launcher.side_effect = OSError('arranque-test')
        response = self.respond()
        for fragment in ('publicada', 'arranque-test', '/lanzar'):
            self.assertIn(fragment, response)
        self.assertEqual(self.git('branch', '--show-current'), 'main')
        self.assertIn(self.git('rev-parse', 'main'), self.git('ls-remote', 'origin', 'refs/heads/main'))
        self.assertEqual(self.git('cat-file', '-t', 'v1.0.0'), 'tag')
