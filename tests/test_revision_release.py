"""Regresiones B-ADV-0037 de revisión formal y pertenencia de parches."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adevv import release_tools
from tests.test_orquestar import motor


class RevisionesReleaseTests(unittest.TestCase):
    """Preflight local, publicación y selector sin red ni arneses reales."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write('task_config.yaml', 'project:\n  version: v1.1.2\nlevels:\n  master:\n    path: docs/plan/\n    folders:\n      tasks: tasks/\n      bugs: bugs/\n')
        self.write('pyproject.toml', '[project]\nversion = "1.1.2"\n')
        self.write('CHANGELOG.md', '## [1.1.2]\nFix\n')
        for name in ('requirements', 'req_analysis', 'platform_plan', 'platform_review', 'work_plan'):
            self.write(f'docs/{name}.md', 'APROBADO\n')
        self.item('B-ADV-0100', 'v1.1.2', 'completed')

    def preparar_git(self):
        """Prepara referencias publicables y un remoto bare exclusivamente local."""
        self.remote = self.root / 'remote.git'
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        self.write('.gitignore', 'remote.git/\n')
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        self.git('remote', 'add', 'origin', str(self.remote))
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.git('push', '-q', 'origin', 'main')
        self.git('checkout', '-qb', 'hotfix/v1.1.2')

    def git(self, *args):
        """Ejecuta Git en la fixture sin configuración personal."""
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        return subprocess.run(['git', *args], cwd=self.root, env=env,
                              check=True, capture_output=True, text=True).stdout.strip()

    def snapshot(self, excluir=()):
        """Observa referencias locales/remotas, índice y artefactos de cierre."""
        files = {p.relative_to(self.root).as_posix(): p.read_bytes()
                 for p in self.root.rglob('*') if p.is_file()
                 and not {'.git', 'remote.git'}.intersection(p.relative_to(self.root).parts)
                 and p.relative_to(self.root).as_posix() not in excluir
                 and p.relative_to(self.root).as_posix() != '.adevv-metricas/registro.lock'
                 and not p.name.startswith('orquestar_')}
        return (self.git('show-ref'), self.git('branch', '--show-current'),
                self.git('ls-files', '--stage'), self.git('ls-remote', 'origin'), files)

    def write(self, path, text):
        """Escribe artefactos de la fixture aislada."""
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')

    def item(self, iid, version, status, extra=''):
        """Añade un bug con pertenencia explícita."""
        self.write(f'docs/plan/{"tasks" if iid.startswith("T-") else "bugs"}/{iid}.md',
                   f'---\nid: {iid}\nversion: {version}\nstatus: {status}\ndepende_de: []\n{extra}---\n')

    def report(self, text, iid='B-ADV-0100'):
        """Declara un informe canónico de Hades."""
        self.write(f'docs/review/code_reviews/{iid}-code-review.md', text)

    def preflight(self):
        """Invoca el mismo ejecutable de completitud que la CLI release."""
        script = Path(__file__).resolve().parents[1] / 'skills/release/scripts/check_release_completeness.py'
        return subprocess.run([sys.executable, str(script), '--dir', str(self.root), '--version', 'v1.1.2'],
                              capture_output=True, text=True, encoding='utf-8')

    def test_cierre_rechaza_ausente_rechazado_vacio_y_na_sin_motivo(self):
        self.preparar_git()
        for text in (None, '', '**Veredicto:** RECHAZADO\n', '**Veredicto:** N/A\n'):
            with self.subTest(report=text):
                if text is not None:
                    self.report(text)
                before = self.snapshot()
                result = self.preflight()
                self.assertEqual(before, self.snapshot())
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('B-ADV-0100', result.stdout)
                self.assertIn('revisar-tarea', result.stdout)
                if text == '**Veredicto:** N/A\n':
                    self.assertIn('N/A sin justificación', result.stdout)

    def test_recuperar_hades_desbloquea_y_na_exige_motivo(self):
        self.preparar_git()
        self.assertNotEqual(self.preflight().returncode, 0)
        for text in ('**Veredicto:** APROBADO\n', '- **Veredicto**: **APROBADO** (media 9/10)\n',
                     '## Veredicto: ✅ APROBADO\n', '**Veredicto: APROBADO. Media: 9/10.**\n',
                     '**Veredicto:** N/A\nMotivo: sin cambios de código; solo documentación.\n'):
            with self.subTest(report=text):
                self.report(text)
                before = self.snapshot()
                self.assertEqual(self.preflight().returncode, 0)
                self.assertEqual(before, self.snapshot())

    def test_prefijo_parecido_no_acredita_revision(self):
        self.report('**Veredicto:** APROBADO\n', 'B-ADV-01000')
        self.assertFalse(motor.revisada(self.root, 'B-ADV-0100'))
        self.assertNotEqual(self.preflight().returncode, 0)

    def test_publicar_sin_revision_no_llega_a_git_ni_etiqueta(self):
        with patch.object(release_tools, '_ejecutar') as run:
            with self.assertRaisesRegex(release_tools.ReleaseValidationError, 'B-ADV-0100'):
                release_tools.publicar_version(self.root, 'v1.1.2')
            run.assert_not_called()

    def test_parche_anterior_no_bloquea_preflight_actual(self):
        self.item('B-ADV-0099', 'v1.1.1', 'completed')
        self.report('**Veredicto:** RECHAZADO\n', 'B-ADV-0099')
        self.report('**Veredicto:** APROBADO\n')
        self.assertEqual(self.preflight().returncode, 0)

    def test_selector_no_recupera_revision_del_parche_anterior(self):
        self.item('B-ADV-0099', 'v1.1.1', 'completed')
        self.item('B-ADV-0100', 'v1.1.2', 'planned')
        with patch.object(motor, 'git', return_value='hotfix/v1.1.2'):
            self.assertEqual(motor.estado(self.root, 'docs'),
                             ('PASO', 'bug-fix', 'B-ADV-0100', 'hotfix/v1.1.2'))

    def test_selector_rechaza_informe_no_aprobado_y_reanuda(self):
        self.report('**Veredicto:** RECHAZADO\n')
        with patch.object(motor, 'git', return_value='hotfix/v1.1.2'):
            self.assertEqual(motor.estado(self.root, 'docs')[1:3], ('revisar-tarea', 'B-ADV-0100'))
            self.report('**Veredicto:** APROBADO\n')
            self.assertEqual(motor.estado(self.root, 'docs')[1], 'revisar-version')

    def test_identidad_completa_y_dependencias_entre_parches(self):
        self.assertEqual(motor.vkey('v1.1'), motor.vkey('v1.1.0'))
        self.assertNotEqual(motor.vkey('v1.1.1'), motor.vkey('v1.1.2'))
        items = [{'id': 'A', 'version': 'v1.1.1', 'depende_de': ['B']},
                 {'id': 'B', 'version': 'v1.1.2', 'depende_de': []}]
        self.assertTrue(motor.errores_dependencias(items))

    def test_cancelado_no_exige_revision_y_hijo_usa_maestro(self):
        self.item('B-ADV-0099', 'v1.1.2', 'cancelled')
        self.item('B-ADV-0101', 'v1.1.2', 'completed', 'parent_id: B-ADV-0100\n')
        self.report('**Veredicto:** APROBADO\n')
        self.assertEqual(self.preflight().returncode, 0)

    def test_matriz_preflight_tarea_bug_ausente_rechazado(self):
        for iid in ('T-ADV-0100', 'B-ADV-0100'):
            for informe in (None, '**Veredicto:** RECHAZADO\n'):
                with self.subTest(iid=iid, informe=informe):
                    for path in self.root.glob('docs/plan/*/*.md'):
                        path.unlink()
                    for path in self.root.glob('docs/review/code_reviews/*.md'):
                        path.unlink()
                    self.item(iid, 'v1.1.2', 'completed')
                    if informe:
                        self.report(informe, iid)
                    if not (self.root / '.git').exists():
                        self.preparar_git()
                    before = self.snapshot()
                    result = self.preflight()
                    self.assertEqual(before, self.snapshot())
                    self.assertNotEqual(result.returncode, 0)
                    for fragment in (iid, 'informe ausente' if informe is None else 'informe rechazado',
                                     'revisar-tarea', 'validar'):
                        self.assertIn(fragment, result.stdout)

    def test_diagnostico_enumera_todos_y_excluye_aprobado(self):
        self.item('T-ADV-0100', 'v1.1.2', 'completed')
        self.item('B-ADV-0101', 'v1.1.2', 'completed')
        self.report('Veredicto: RECHAZADO')
        self.report('Veredicto: APROBADO', 'B-ADV-0101')
        result = self.preflight()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('T-ADV-0100: informe ausente', result.stdout)
        self.assertIn('B-ADV-0100: informe rechazado', result.stdout)
        self.assertNotIn('B-ADV-0101', result.stdout)

    def test_parche_cero_equivale_a_version_sin_parche_en_preflight(self):
        self.item('T-ADV-0100', 'v1.1', 'completed')
        script = Path(__file__).resolve().parents[1] / 'skills/release/scripts/check_release_completeness.py'
        result = subprocess.run([sys.executable, str(script), '--dir', str(self.root), '--version', 'v1.1.0'],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('T-ADV-0100: informe ausente', result.stdout)

    def test_cuota_de_hades_estado_recuperacion_y_revalidacion(self):
        self.write('orchestration.json', '{"hades": {"harness": "codex", "model": "modelo-test"}}')
        self.write('docs/review/versions/v1.1.2-arquitectura.md', 'APROBADO')
        self.write('docs/review/versions/v1.1.2-revision.md', 'Pendiente')
        self.preparar_git()
        before = self.snapshot()
        pruebas = subprocess.run([sys.executable, '-c', 'raise SystemExit(0)'], cwd=self.root)
        self.assertEqual(pruebas.returncode, 0)
        env = {'ORQUESTAR_ID': 'B-ADV-0100', 'ORQUESTAR_PASO': 'revisar-tarea'}
        with patch.dict(os.environ, env), patch.object(motor, 'buscar_ejecutable', return_value=sys.executable), \
             patch.object(motor, 'lanzar', return_value=(1, {}, 'rate limit reached')), \
             patch.object(motor, 'avisar'):
            self.assertNotEqual(motor.agente(self.root, 'hades', 'revisión formal'), 0)
        self.assertEqual(before, self.snapshot())
        with patch.object(motor, 'git', return_value='hotfix/v1.1.2'):
            estado = motor.parte(self.root, 'docs')
        result = self.preflight()
        self.assertEqual(before, self.snapshot())
        self.assertNotEqual(result.returncode, 0)
        for text in (estado, result.stdout):
            for fragment in ('B-ADV-0100', 'Hades sin cuota', 'recuperar', 'revisar-tarea', 'validar'):
                self.assertIn(fragment, text)
        self.assertFalse(motor.revisada(self.root, 'B-ADV-0100'))
        motor.reset_cuotas(self.root)
        self.assertNotEqual(self.preflight().returncode, 0)

        def emitir(*args, **kwargs):
            """Simula exclusivamente el transporte de un Hades recuperado."""
            self.report('**Veredicto:** APROBADO\n')
            return 0, {}, 'Veredicto: APROBADO'

        excluir = ('docs/review/code_reviews/B-ADV-0100-code-review.md',)
        before = self.snapshot(excluir)
        with patch.dict(os.environ, env), patch.object(motor, 'buscar_ejecutable', return_value=sys.executable), \
             patch.object(motor, 'lanzar', side_effect=emitir):
            self.assertEqual(motor.agente(self.root, 'hades', 'reanudar revisión'), 0)
        self.assertEqual(before, self.snapshot(excluir))
        self.assertEqual(self.preflight().returncode, 0)
        with patch.object(motor, 'git', return_value='hotfix/v1.1.2'):
            self.assertEqual(motor.estado(self.root, 'docs')[0], 'PARAR')
        self.assertIn('Pendiente', (self.root / 'docs/review/versions/v1.1.2-revision.md').read_text())

    def test_ruta_intervencion_conserva_parche(self):
        from types import SimpleNamespace
        proxy = SimpleNamespace(vkey=motor.vkey, frontmatter=motor.frontmatter,
                                fichero_de=lambda root, iid: root / 'docs/plan/bugs/B-ADV-0100.md')
        self.assertEqual(motor.intervencion.revision(self.root, proxy, 'B-ADV-0100'),
                         self.root / 'docs/review/versions/v1.1.2-revision.md')
