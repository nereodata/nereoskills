import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs


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


CREDENCIALES = {'TELEGRAM_BOT_TOKEN': 'tok', 'TELEGRAM_ALLOWED_USER_IDS': '42, 43'}


class AvisosTelegramTests(unittest.TestCase):
    """Avisos del bucle: fin de versión, cuota, respuesta del humano y fallos; solo los eventos activos."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness='claude', estado=False,
                                             max_pasos=3, reintentos=2, espera_max=2, cmd=None)

    def tearDown(self):
        self.tmp.cleanup()

    def avisos(self, estado, cfg=None, ejecucion=(0, {}, ''), env=None):
        """Ejecuta el bucle y devuelve (código, [(url, chat, texto)] enviados a Telegram)."""
        enviados = []

        def urlopen(url, datos, timeout):
            campos = parse_qs(datos.decode())
            enviados.append((url, campos['chat_id'][0], campos['text'][0]))
            return MagicMock(**{'__enter__.return_value.status': 200})

        with (patch.dict(motor.os.environ, CREDENCIALES if env is None else env, clear=True),
              patch.object(motor, 'estado', side_effect=lambda *a: estado),
              patch.object(motor, 'config', return_value=cfg or {}),
              patch.object(motor, 'ejecutar', return_value=ejecucion),
              patch.object(motor, 'esperar', return_value=True),
              patch.object(motor, 'registrar'), patch.object(motor, 'firma', return_value='igual'),
              patch.object(motor, 'git', return_value=''),
              patch('urllib.request.urlopen', side_effect=urlopen)):
            codigo = motor.bucle(self.args, self.root)
        return codigo, enviados

    def test_version_end_and_product_end_notify_every_authorized_user(self):
        codigo, enviados = self.avisos(('PARAR', 'Versión v0.1 terminada. Revisa'))
        self.assertEqual(codigo, 2)
        self.assertEqual([chat for _, chat, _ in enviados], ['42', '43'])
        self.assertIn('bottok/sendMessage', enviados[0][0])
        self.assertIn('Versión v0.1 terminada', enviados[0][2])
        self.assertIn(self.root.name, enviados[0][2])
        codigo, enviados = self.avisos(('FIN', 'Todas las tareas con versión están cerradas.'))
        self.assertEqual(codigo, 0)
        self.assertIn('Producto terminado', enviados[0][2])

    def test_human_answer_needed_notifies(self):
        _, enviados = self.avisos(('PARAR', 'Requisitos con preguntas sin valor por defecto seguro.'))
        self.assertIn('preguntas', enviados[0][2])

    def test_quota_wait_and_quota_stop_notify(self):
        sin_cuota = (1, {}, 'You hit your usage limit. try again in 1h 30m')
        _, enviados = self.avisos(('PASO', 'task-dev', 'T1', None), ejecucion=sin_cuota)
        self.assertIn('Sin cuota', enviados[0][2])
        self.assertIn('código 1', enviados[-1][2])

    def test_only_enabled_events_are_sent(self):
        cfg = {'telegram': {'eventos': ['cuota']}}
        self.assertEqual(self.avisos(('PARAR', 'Versión v0.1 terminada.'), cfg=cfg)[1], [])

    def test_disabled_or_without_credentials_sends_nothing(self):
        self.assertEqual(self.avisos(('PARAR', 'Versión v0.1 terminada.'), cfg={'telegram': False})[1], [])
        self.assertEqual(self.avisos(('PARAR', 'Versión v0.1 terminada.'), env={'TELEGRAM_BOT_TOKEN': 'tok'})[1], [])
        self.assertEqual(self.avisos(('PARAR', 'Versión v0.1 terminada.'), env={})[1], [])

    def test_send_failure_does_not_break_the_loop(self):
        with (patch.dict(motor.os.environ, CREDENCIALES),
              patch.object(motor, 'config', return_value={}),
              patch('urllib.request.urlopen', side_effect=OSError('sin red'))):
            self.assertFalse(motor.avisar(self.root, 'version', 'hola'))

    def test_markdown_rejected_is_retried_as_plain_text(self):
        modos = []

        def urlopen(url, datos, timeout):
            modos.append(parse_qs(datos.decode()).get('parse_mode'))
            if len(modos) == 1:
                raise HTTPError('https://api.telegram.org', 400, 'Bad Request', {}, None)
            return MagicMock(**{'__enter__.return_value.status': 200})

        with patch('urllib.request.urlopen', side_effect=urlopen):
            self.assertTrue(motor.enviar('tok', '42', '*x', markdown=True))
        self.assertEqual(modos, [['Markdown'], None])


class BuzonTests(unittest.TestCase):
    """Altas desde Telegram: sin versión, con el ID siguiente y un commit que solo lleva esos ficheros."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 't@t')
        self.git('config', 'user.name', 't')
        (self.root / 'task_config.yaml').write_text('project:\n  prefix: ADV\n', encoding='utf-8')
        (self.root / 'docs/plan/tasks').mkdir(parents=True)
        (self.root / 'docs/plan/tasks/T-ADV-0007-previa.md').write_text('---\nid: T-ADV-0007\n---\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-q', '-m', 'base')

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout

    def test_inbox_is_registered_without_version_and_committed_alone(self):
        (self.root / 'ajeno.txt').write_text('cambio del usuario', encoding='utf-8')
        with patch.object(motor, 'excluir'):
            motor.apuntar(self.root, 'tarea', 'Exportar a CSV', '42')
            motor.apuntar(self.root, 'bug', 'El login falla con tildes', '42')
        self.assertEqual(motor.ingerir(self.root), [('T-ADV-0008', 'Exportar a CSV'),
                                                    ('B-ADV-0001', 'El login falla con tildes')])
        tarea = motor.frontmatter(self.root / 'docs/plan/tasks/T-ADV-0008-exportar-a-csv.md')
        self.assertEqual((tarea['status'], tarea['version']), ('backlog', ''))
        self.assertNotIn('depende_de', tarea)
        self.assertTrue((self.root / 'docs/plan/bugs/B-ADV-0001-el-login-falla-con-tildes.md').exists())
        commit = self.git('show', '--name-only', '--format=%s', 'HEAD')
        self.assertIn('T-ADV-0008, B-ADV-0001', commit)
        self.assertNotIn('ajeno.txt', commit)
        self.assertFalse((self.root / motor.BUZON).exists())
        self.assertEqual(motor.ingerir(self.root), [])

    def test_unversioned_task_does_not_trigger_dependencies_step(self):
        items = [{'paso': 'task-dev', 'id': 'T1', 'status': 'backlog', 'version': '', 'depende_de': None,
                  'pendiente_de': '', 'weight': 0}]
        for f in ('requirements.md', 'req_analysis.md', 'platform_plan.md', 'platform_review.md', 'work_plan.md'):
            (self.root / 'docs' / f).write_text('', encoding='utf-8')
        with (patch.object(motor, 'backlog', return_value=items), patch.object(motor, 'git', return_value='')):
            self.assertEqual(motor.estado(self.root, 'docs')[0], 'FIN')
            items[0]['version'] = 'v0.2.0'
            self.assertEqual(motor.estado(self.root, 'docs')[1], 'calcular-dependencias')


class RolesTests(unittest.TestCase):
    """Atenea analiza y decide, Artemisa desarrolla; cada una con su arnés, modelo y esfuerzo."""

    CFG = {'atenea': {'harness': 'claude', 'model': 'claude-opus-5-5', 'effort': 'medium'},
           'artemisa': {'harness': 'agy', 'model': 'gemini-3.8-flash-medium'}}

    def args(self, harness=None, cmd=None):
        return motor.argparse.Namespace(harness=harness, cmd=cmd, presupuesto=None)

    def test_development_steps_go_to_artemisa_and_the_rest_to_atenea(self):
        with patch.object(motor, 'config', return_value=self.CFG):
            for paso in ('task-dev', 'bug-fix', 'revisar-tarea'):
                self.assertEqual(motor.rol_de(Path('.'), paso), ('artemisa', self.CFG['artemisa']))
            for paso in ('ciclo-requisitos', 'platform-plan', 'work-plan', 'especificar', 'revisar-version'):
                self.assertEqual(motor.rol_de(Path('.'), paso), ('atenea', self.CFG['atenea']))

    def test_without_roles_every_step_uses_development(self):
        dev = {'harness': 'codex', 'model': 'gpt'}
        with patch.object(motor, 'config', return_value={'development': dev}):
            self.assertEqual(motor.rol_de(Path('.'), 'platform-plan')[1], dev)
            self.assertEqual(motor.rol_de(Path('.'), 'task-dev')[1], dev)

    def test_each_role_launches_its_own_harness_and_model(self):
        with patch.object(motor.shutil, 'which', side_effect=lambda x: x):
            atenea = motor.comando(self.args(), 'p', rol=self.CFG['atenea'])
            artemisa = motor.comando(self.args(), 'p', rol=self.CFG['artemisa'])
            forzado = motor.comando(self.args(harness='codex'), 'p', rol=self.CFG['artemisa'])
        self.assertEqual(atenea[0], 'claude')
        self.assertEqual(atenea[-4:], ['--model', 'claude-opus-5-5', '--effort', 'medium'])
        self.assertEqual(artemisa[0], 'agy')
        self.assertEqual(artemisa[-2:], ['--model', 'gemini-3.8-flash-medium'])
        self.assertEqual(forzado[:2], ['codex', 'exec'])
        self.assertNotIn('-m', forzado)

    def test_agy_json_output_gives_usage_and_errors(self):
        salida = ('{"status":"SUCCESS","response":"hecho","num_turns":3,"usage":{"input_tokens":10,'
                  '"output_tokens":5,"thinking_tokens":2,"cache_read_tokens":1}}')
        cmd = ['agy', '-p', 'x', '--output-format', 'json', '--model', 'gemini-3.8-flash-medium']
        with patch.object(motor.subprocess, 'run', return_value=subprocess.CompletedProcess(cmd, 0, salida, '')):
            codigo, m, _ = motor.lanzar(cmd, Path('.'), 'agy')
        self.assertEqual((codigo, m['turnos']), (0, 3))
        self.assertEqual(m['modelos']['gemini-3.8-flash-medium'],
                         {'entrada': 10, 'salida': 5, 'cache_leida': 1, 'razonamiento': 2})
        fallo = salida.replace('SUCCESS', 'ERROR')
        with patch.object(motor.subprocess, 'run', return_value=subprocess.CompletedProcess(cmd, 0, fallo, '')):
            self.assertEqual(motor.lanzar(cmd, Path('.'), 'agy')[0], 1)

    def test_step_settings_override_the_role_effort(self):
        cfg = {'atenea': {'harness': 'claude', 'model': 'opus', 'effort': 'medium',
                          'pasos': {'platform-plan': {'effort': 'high'}}}}
        with patch.object(motor, 'config', return_value=cfg):
            self.assertEqual(motor.rol_de(Path('.'), 'platform-plan')[1],
                             {'harness': 'claude', 'model': 'opus', 'effort': 'high'})
            self.assertEqual(motor.rol_de(Path('.'), 'start-version')[1]['effort'], 'medium')


ESCALADA = {'artemisa': {'harness': 'agy', 'model': 'gemini-3.8-flash-medium',
                         'escalada': {'rechazos': 2, 'model': 'claude-opus-5-5-medium'}},
            'hades': {'harness': 'claude', 'model': 'opus', 'effort': 'medium',
                      'pasos': {'revisar-version': {'effort': 'high'}}}}


class EscaladaTests(unittest.TestCase):
    """Hades deja su veredicto en las métricas; tras dos rechazos seguidos, Artemisa para y sube de modelo."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cfg = patch.object(motor, 'config', return_value=ESCALADA)
        self.cfg.start()

    def tearDown(self):
        self.cfg.stop()
        self.tmp.cleanup()

    def hades(self, veredicto, paso='revisar-tarea', iid='T-ADV-0001', escalada=False):
        """Lanza a Hades con una salida que trae el veredicto; devuelve (comando lanzado, lo impreso)."""
        lanzados = []

        def lanzar(cmd, root, harness, entrada=None):
            lanzados.append(cmd)
            return 0, {}, f'## Informe\n- **Veredicto**: {veredicto} (media 6)'

        env = {'ORQUESTAR_PASO': paso, 'ORQUESTAR_ID': iid, **({'ORQUESTAR_ESCALADA': '1'} if escalada else {})}
        with (patch.dict(motor.os.environ, env, clear=True), patch.object(motor, 'lanzar', side_effect=lanzar),
              patch.object(motor.shutil, 'which', side_effect=lambda x: x), patch.object(motor, 'excluir'),
              patch('builtins.print') as impreso):
            motor.agente(self.root, 'hades', 'revisa')
        return lanzados[0], ' '.join(str(c.args[0]) for c in impreso.call_args_list if c.args)

    def test_verdicts_are_recorded_and_an_approval_resets_the_count(self):
        self.hades('RECHAZADO')
        self.assertEqual(motor.rechazos(self.root, 'T-ADV-0001'), 1)
        self.hades('APROBADO')
        self.assertEqual(motor.rechazos(self.root, 'T-ADV-0001'), 0)
        self.hades('RECHAZADO', iid='T-ADV-0002')
        self.assertEqual(motor.rechazos(self.root, 'T-ADV-0001'), 0)

    def test_hades_uses_the_effort_of_the_step(self):
        cmd, _ = self.hades('APROBADO', paso='revisar-version')
        self.assertEqual(cmd[-4:], ['--model', 'opus', '--effort', 'high'])
        cmd, _ = self.hades('APROBADO', paso='revisar-tarea')
        self.assertEqual(cmd[-1], 'medium')

    def test_second_rejection_tells_artemisa_to_stop_and_the_next_launch_escalates(self):
        _, impreso = self.hades('RECHAZADO')
        self.assertNotIn('no sigas corrigiendo', impreso)
        cfg = motor.rol_de(self.root, 'task-dev')[1]
        self.assertEqual(motor.escalada(self.root, 'artemisa', cfg, 'T-ADV-0001'), (cfg, False))
        _, impreso = self.hades('RECHAZADO')
        self.assertIn('no sigas corrigiendo', impreso)
        self.assertIn('modelo superior', impreso)
        escalado, si = motor.escalada(self.root, 'artemisa', cfg, 'T-ADV-0001')
        self.assertTrue(si)
        self.assertEqual(escalado, {'harness': 'agy', 'model': 'claude-opus-5-5-medium'})
        self.assertEqual(motor.escalada(self.root, 'atenea', cfg, 'T-ADV-0001'), (cfg, False))

    def test_after_escalation_two_more_rejections_block_the_task(self):
        for _ in range(3):
            self.hades('RECHAZADO', escalada=True)
        _, impreso = self.hades('RECHAZADO', escalada=True)
        self.assertIn('regla 5', impreso)
        self.assertIn('pendiente_de: especificador', impreso)

    def test_without_escalation_three_rejections_block_the_task(self):
        sin_escalada = {'artemisa': {'harness': 'agy', 'model': 'gemini-3.8-flash-medium'},
                        'hades': {'harness': 'claude', 'model': 'opus'}}
        with patch.object(motor, 'config', return_value=sin_escalada):
            for _ in range(2):
                _, impreso = self.hades('RECHAZADO')
                self.assertNotIn('regla 5', impreso)
            _, impreso = self.hades('RECHAZADO')
            self.assertIn('regla 5', impreso)
            self.assertIn('pendiente_de: especificador', impreso)

    def test_subagent_out_of_credits_triggers_quota_wait_in_loop(self):
        msg = '{"type":"error","message":"Your workspace is out of credits. Add credits to continue."}'
        self.assertEqual(motor.espera_cuota(msg), 1800)

        def ejecutar_paso(a, root, prompt, env=None, rol=None):
            with (patch.dict(motor.os.environ, env or {}, clear=True),
                  patch.object(motor, 'lanzar', return_value=(1, {}, msg)),
                  patch.object(motor.shutil, 'which', side_effect=lambda x: x),
                  patch.object(motor, 'excluir')):
                motor.agente(root, 'hades', 'revisa')
            return 0, {}, 'No puedo seguir sin Hades.'

        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None, estado=False, max_pasos=2,
                                        reintentos=2, espera_max=2, cmd=None)
        with (patch.object(motor, 'estado', side_effect=[('PASO', 'task-dev', 'T-ADV-0001', ''),
                                                         ('FIN', 'Cerrado.')]),
              patch.object(motor, 'ejecutar', side_effect=ejecutar_paso),
              patch.object(motor, 'esperar', return_value=True) as esperar,
              patch.object(motor, 'firma', return_value='igual'),
              patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'ingerir', return_value=[]),
              patch.object(motor, 'avisar'),
              patch.object(motor, 'excluir')):
            self.assertEqual(motor.bucle(args, self.root), 0)
        esperar.assert_called_once_with(self.root, 1800)

    def test_agent_prompt_lists_verified_commands_for_current_tree(self):
        clave = 'b' * 40
        (self.root / motor.EVIDENCIAS).write_text(
            f'{{"arbol":"{clave}","comando":"npm run content:validate","codigo":0}}\n', encoding='utf-8')
        with patch.object(motor, 'arbol', return_value=clave):
            prompt = motor.construir_prompt_agente(self.root, 'hades', 'revisa')
        self.assertIn('Verificado en verde sobre este árbol (bbbbbbbbbb): `npm run content:validate`', prompt)

    def test_loop_launches_the_escalated_model_with_its_flag(self):
        for _ in range(2):
            self.hades('RECHAZADO')
        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None, estado=False, max_pasos=1,
                                        reintentos=2, espera_max=0, cmd=None)
        with (patch.object(motor, 'estado', return_value=('PASO', 'revisar-tarea', 'T-ADV-0001', '')),
              patch.object(motor, 'ejecutar', return_value=(0, {}, '')) as ejecutar,
              patch.object(motor, 'firma', side_effect=['a', 'b']), patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'ingerir', return_value=[]), patch.object(motor, 'avisar'),
              patch.object(motor, 'excluir')):
            motor.bucle(args, self.root)
        self.assertEqual(ejecutar.call_args.kwargs['rol']['model'], 'claude-opus-5-5-medium')
        self.assertEqual(ejecutar.call_args.kwargs['env']['ORQUESTAR_ESCALADA'], '1')


if __name__ == '__main__':
    unittest.main()
