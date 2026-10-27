import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs

from adevv import yaml_lite
from tests import aislamiento_telegram


SPEC = importlib.util.spec_from_file_location(
    'orquestar', Path(__file__).resolve().parents[1] / 'skills/orquestar/orquestar.py')
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


class OrquestarRegressionTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(motor, 'iniciar_gateway'))

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



class RevisionProductoTests(unittest.TestCase):
    """Versión v0.1 cerrada (tarea completada y revisada, revisión de arquitectura hecha) y v0.2 pendiente."""

    def setUp(self):
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
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
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
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
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
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
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
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
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
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

    def test_quota_wait_parses_compact_durations(self):
        casos = {'Individual quota reached. Resets in 56h48m9s.': 56 * 3600 + 48 * 60 + 9 + 120,
                 'quota exceeded, resets in 2d3h': 2 * 86400 + 3 * 3600 + 120,
                 'quota: retry in 48m9s': 48 * 60 + 9 + 120,
                 'quota: retry in 9s': 9 + 120,
                 'rate limit, try again in 2h 13m': 2 * 3600 + 13 * 60 + 120,
                 'rate limit, try again in 5 minutes': 300 + 120}
        for msg, esperado in casos.items():
            self.assertEqual(motor.espera_cuota(msg), esperado, msg)

    def test_antigravity_resource_exhausted_json_is_quota(self):
        msg = 'AGY_ERROR: {"status":"RESOURCE_EXHAUSTED","error_code":429}'
        self.assertEqual(motor.espera_cuota(msg), 1800)
        self.assertIsNotNone(motor.espera_cuota('RESOURCE_EXHAUSTED'))

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
        esperar.assert_called_once_with(self.root, 300, cuotas_esperadas=ANY)

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
        with (patch.object(motor, 'estado', return_value=('PASO', 'task-dev', 'T-ADV-0001', '')),
              patch.object(motor, 'ejecutar', return_value=(0, {}, '')) as ejecutar,
              patch.object(motor, 'firma', side_effect=['a', 'b']), patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'ingerir', return_value=[]), patch.object(motor, 'avisar'),
              patch.object(motor, 'excluir')):
            motor.bucle(args, self.root)
        self.assertEqual(ejecutar.call_args.kwargs['rol']['model'], 'claude-opus-5-5-medium')
        self.assertEqual(ejecutar.call_args.kwargs['env']['ORQUESTAR_ESCALADA'], '1')

    def test_lanzar_captures_session_id_for_each_harness(self):
        # 1. Claude
        claude_out = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='{"result":"ok","session_id":"sess-claude-123","num_turns":1}\n', stderr=''
        )
        with patch.object(subprocess, 'run', return_value=claude_out):
            code, m, _ = motor.lanzar(['claude', '--output-format', 'json'], self.root, 'claude')
            self.assertEqual(code, 0)
            self.assertEqual(m.get('sesion'), 'sess-claude-123')

        # 2. Antigravity (agy)
        agy_out = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='{"status":"SUCCESS","conversation_id":"conv-agy-789","response":"ok"}\n', stderr=''
        )
        with patch.object(subprocess, 'run', return_value=agy_out):
            code, m, _ = motor.lanzar(['agy', '--output-format', 'json'], self.root, 'agy')
            self.assertEqual(code, 0)
            self.assertEqual(m.get('sesion'), 'conv-agy-789')

        # 3. Codex (streaming JSON lines)
        codex_lines = [
            '{"type":"thread.started","thread_id":"th-codex-456"}\n',
            '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n'
        ]
        mock_popen = MagicMock()
        mock_popen.__enter__.return_value = mock_popen
        mock_popen.stdout = codex_lines
        mock_popen.returncode = 0
        with patch.object(subprocess, 'Popen', return_value=mock_popen):
            code, m, _ = motor.lanzar(['codex', 'exec', '--json'], self.root, 'codex')
            self.assertEqual(code, 0)
            self.assertEqual(m.get('sesion'), 'th-codex-456')

        # 4. Codex in agente does not have --ephemeral
        with patch.object(motor, 'lanzar', return_value=(0, {}, 'Veredicto: APROBADO')) as mock_lanzar, \
             patch.object(motor.shutil, 'which', side_effect=lambda x: x), \
             patch.object(motor, 'excluir'), \
             patch.object(motor, 'git', return_value=''), \
             patch.object(motor, 'config', return_value={'hades': {'harness': 'codex'}}), \
             patch.dict(motor.os.environ, {'ORQUESTAR_ID': 'T-ADV-0001'}, clear=True):
            motor.agente(self.root, 'hades', 'revisa')
            cmd_passed = mock_lanzar.call_args[0][0]
            self.assertNotIn('--ephemeral', cmd_passed)

    def test_hades_single_thread_resumes_session_and_strips_initial_header(self):
        lineas_lanzadas = []
        entradas_lanzadas = []

        def mock_lanzar(cmd, root, harness, entrada=None):
            lineas_lanzadas.append(cmd)
            entradas_lanzadas.append(entrada)
            return 0, {'sesion': 'sess-hades-prev'}, 'Veredicto: APROBADO'

        env = {'ORQUESTAR_PASO': 'task-dev', 'ORQUESTAR_ID': 'T-ADV-0001'}
        with patch.dict(motor.os.environ, env, clear=True), \
             patch.object(motor.shutil, 'which', side_effect=lambda x: x), \
             patch.object(motor, 'excluir'), \
             patch.object(motor, 'git', return_value=''), \
             patch.object(motor, 'lanzar', side_effect=mock_lanzar):

            # 1. First call creates session
            motor.agente(self.root, 'hades', 'revisa spec')
            self.assertNotIn('--resume', lineas_lanzadas[0])
            self.assertIn('actúa como ese agente', entradas_lanzadas[0])

            # 2. Second call resumes session and strips initial header
            motor.agente(self.root, 'hades', 'revisa test')
            self.assertIn('--resume', lineas_lanzadas[1])
            self.assertEqual(lineas_lanzadas[1][lineas_lanzadas[1].index('--resume') + 1], 'sess-hades-prev')
            self.assertNotIn('actúa como ese agente', entradas_lanzadas[1])
            self.assertIn('revisa test', entradas_lanzadas[1])

    def test_hades_resume_failure_falls_back_transparently_to_fresh_session(self):
        llamadas = []

        def mock_lanzar(cmd, root, harness, entrada=None):
            llamadas.append((cmd, entrada))
            if '--resume' in cmd:
                return 1, {}, 'Error: session sess-hades-prev not found'
            return 0, {'sesion': 'sess-hades-new'}, 'Veredicto: APROBADO'

        (self.root / motor.METRICAS).write_text(
            json.dumps({'tipo': 'agente', 'rol': 'hades', 'id': 'T-ADV-0001', 'arnes': 'claude',
                        'sesion': 'sess-hades-prev', 'codigo': 0}) + '\n',
            encoding='utf-8'
        )

        env = {'ORQUESTAR_PASO': 'task-dev', 'ORQUESTAR_ID': 'T-ADV-0001'}
        with patch.dict(motor.os.environ, env, clear=True), \
             patch.object(motor.shutil, 'which', side_effect=lambda x: x), \
             patch.object(motor, 'excluir'), \
             patch.object(motor, 'git', return_value=''), \
             patch.object(motor, 'lanzar', side_effect=mock_lanzar):
            code = motor.agente(self.root, 'hades', 'revisa code')
            self.assertEqual(code, 0)
            self.assertEqual(len(llamadas), 2)
            self.assertIn('--resume', llamadas[0][0])
            self.assertNotIn('--resume', llamadas[1][0])
            self.assertIn('actúa como ese agente', llamadas[1][1])

    def test_loop_resumes_developer_session_after_quota_wait(self):
        ejecuciones = []
        instante = [motor.fecha_estado('2026-10-27T12:00:00+00:00')]

        def esperar_cuota(root, segundos, **kwargs):
            """Simula la espera avanzando también el reloj de la política de cuota."""
            instante[0] += motor.timedelta(seconds=segundos)
            return True

        def mock_ejecutar(a, root, prompt, env=None, rol=None, sesion=None):
            ejecuciones.append(sesion)
            if len(ejecuciones) == 1:
                return 1, {'sesion': 'dev-sess-100'}, 'out of credits'
            return 0, {'sesion': 'dev-sess-100'}, 'ok'

        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None, estado=False, max_pasos=3,
                                        reintentos=2, espera_max=2, cmd=None)
        with patch.object(motor, 'estado', side_effect=[('PASO', 'task-dev', 'T-ADV-0001', ''),
                                                        ('PASO', 'task-dev', 'T-ADV-0001', ''),
                                                        ('FIN', 'Cerrado.')]), \
             patch.object(motor, 'ejecutar', side_effect=mock_ejecutar), \
             patch.object(motor, 'esperar', side_effect=esperar_cuota), \
             patch.object(motor, 'ahora', side_effect=lambda: instante[0].isoformat()), \
             patch.object(motor, 'firma', side_effect=['a', 'a', 'b']), \
             patch.object(motor, 'git', return_value=''), \
             patch.object(motor, 'ingerir', return_value=[]), \
             patch.object(motor, 'avisar'), \
             patch.object(motor, 'excluir'):
            self.assertEqual(motor.bucle(args, self.root), 0)

        self.assertEqual(len(ejecuciones), 2)
        self.assertIsNone(ejecuciones[0])
        self.assertEqual(ejecuciones[1], 'dev-sess-100')

    def test_session_isolation_across_ids_blocks_and_escalation(self):
        (self.root / motor.METRICAS).write_text(
            json.dumps({'tipo': 'agente', 'rol': 'hades', 'id': 'T-ADV-0001', 'arnes': 'claude',
                        'sesion': 'sess-1', 'codigo': 0}) + '\n',
            encoding='utf-8'
        )
        self.assertIsNone(motor.buscar_sesion_agente(self.root, 'hades', 'T-ADV-0002', 'claude'))

        with (self.root / motor.METRICAS).open('a', encoding='utf-8') as f:
            f.write(json.dumps({'tipo': 'paso', 'paso': 'especificar', 'id': 'T-ADV-0001', 'codigo': 0}) + '\n')
        self.assertIsNone(motor.buscar_sesion_agente(self.root, 'hades', 'T-ADV-0001', 'claude'))

        (self.root / motor.METRICAS).write_text(
            json.dumps({'tipo': 'agente', 'rol': 'hades', 'id': 'T-ADV-0001', 'arnes': 'claude',
                        'sesion': 'sess-pre-esc', 'codigo': 0}) + '\n' +
            json.dumps({'tipo': 'paso', 'paso': 'task-dev', 'id': 'T-ADV-0001', 'arnes': 'claude',
                        'escalado': True, 'codigo': 0}) + '\n',
            encoding='utf-8'
        )
        with patch.dict(motor.os.environ, {'ORQUESTAR_ESCALADA': '1'}):
            self.assertIsNone(motor.buscar_sesion_agente(self.root, 'hades', 'T-ADV-0001', 'claude'))


class DificultadTests(unittest.TestCase):
    """Clasificación de dificultad (sencilla, media, dificil) y selección de modelo/esfuerzo."""

    def setUp(self):
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_backlog_reads_dificultad_normalizada_and_defaults_to_media(self):
        tareas = self.root / 'docs/plan/tasks'
        tareas.mkdir(parents=True)
        (tareas / 'T1.md').write_text('---\nid: T1\nweight: 10\n---\n', encoding='utf-8')
        (tareas / 'T2.md').write_text('---\nid: T2\ndificultad: sencilla\n---\n', encoding='utf-8')
        (tareas / 'T3.md').write_text('---\nid: T3\ndificultad: Difícil \n---\n', encoding='utf-8')
        (tareas / 'T4.md').write_text('---\nid: T4\ndificultad: desconocida\n---\n', encoding='utf-8')

        items = {it['id']: it['dificultad'] for it in motor.backlog(self.root)}
        self.assertEqual(items['T1'], 'media')
        self.assertEqual(items['T2'], 'sencilla')
        self.assertEqual(items['T3'], 'dificil')
        self.assertEqual(items['T4'], 'media')

    def test_ajustes_applies_dificultad_overrides(self):
        cfg = {
            'harness': 'agy',
            'model': 'flash-medium',
            'effort': 'medium',
            'dificultad': {
                'sencilla': {'model': 'flash-low', 'effort': 'low'},
                'dificil': {'model': 'pro-high', 'effort': 'high'},
            }
        }
        self.assertEqual(motor.ajustes(cfg, 'task-dev', 'sencilla'),
                         {'harness': 'agy', 'model': 'flash-low', 'effort': 'low'})
        self.assertEqual(motor.ajustes(cfg, 'task-dev', 'media'),
                         {'harness': 'agy', 'model': 'flash-medium', 'effort': 'medium'})
        self.assertEqual(motor.ajustes(cfg, 'task-dev', 'dificil'),
                         {'harness': 'agy', 'model': 'pro-high', 'effort': 'high'})

    def test_ajustes_paso_overrides_dificultad(self):
        cfg = {
            'harness': 'agy',
            'model': 'base-model',
            'effort': 'medium',
            'dificultad': {
                'sencilla': {'model': 'cheap-model', 'effort': 'low'},
            },
            'pasos': {
                'task-dev': {'effort': 'high'}
            }
        }
        res = motor.ajustes(cfg, 'task-dev', 'sencilla')
        self.assertEqual(res['model'], 'cheap-model')
        self.assertEqual(res['effort'], 'high')

    def test_escalada_takes_precedence_over_dificultad(self):
        cfg_artemisa = {
            'harness': 'agy',
            'model': 'default-model',
            'dificultad': {
                'sencilla': {'model': 'cheap-model', 'effort': 'low'},
            },
            'escalada': {
                'rechazos': 2,
                'model': 'opus-superior'
            }
        }
        cfg_res = motor.ajustes(cfg_artemisa, 'task-dev', 'sencilla')
        self.assertEqual(cfg_res['model'], 'cheap-model')

        with patch.object(motor, 'rechazos', return_value=2):
            cfg_esc, escalado = motor.escalada(self.root, 'artemisa', cfg_res, 'T-ADV-0001')
            self.assertTrue(escalado)
            self.assertEqual(cfg_esc['model'], 'opus-superior')

    def test_agente_applies_dificultad_from_active_orquestar_id(self):
        cfg = {
            'hades': {
                'harness': 'agy',
                'model': 'gemini-medium',
                'dificultad': {
                    'sencilla': {'model': 'gemini-low', 'effort': 'low'},
                    'dificil': {'model': 'gemini-pro', 'effort': 'high'},
                }
            }
        }
        tareas = self.root / 'docs/plan/tasks'
        tareas.mkdir(parents=True)
        (tareas / 'T-ADV-0001.md').write_text('---\nid: T-ADV-0001\ndificultad: sencilla\n---\n', encoding='utf-8')

        lanzados = []
        def fake_lanzar(cmd, root, harness, entrada=None):
            lanzados.append(cmd)
            return 0, {}, '## Informe\n- **Veredicto**: APROBADO (media 9)'

        env = {'ORQUESTAR_PASO': 'task-dev', 'ORQUESTAR_ID': 'T-ADV-0001'}
        with (patch.object(motor, 'config', return_value=cfg),
              patch.dict(motor.os.environ, env, clear=True),
              patch.object(motor, 'lanzar', side_effect=fake_lanzar),
              patch.object(motor.shutil, 'which', side_effect=lambda x: x),
              patch.object(motor, 'excluir'),
              patch('builtins.print')):
            motor.agente(self.root, 'hades', 'revisa')

        self.assertIn('--model', lanzados[0])
        idx = lanzados[0].index('--model')
        self.assertEqual(lanzados[0][idx + 1], 'gemini-low')

    def test_promover_dificultad_updates_frontmatter_and_metrics(self):
        tareas = self.root / 'docs/plan/tasks'
        tareas.mkdir(parents=True)
        (tareas / 'T-ADV-0001.md').write_text('---\nid: T-ADV-0001\ndificultad: sencilla\n---\n# Tarea\n', encoding='utf-8')

        with patch('builtins.print'):
            nueva = motor.promover_dificultad(self.root, 'T-ADV-0001', motivo='test')
        self.assertEqual(nueva, 'media')
        self.assertEqual(motor.dificultad_de(self.root, 'T-ADV-0001'), 'media')
        texto = (tareas / 'T-ADV-0001.md').read_text(encoding='utf-8')
        self.assertIn('dificultad: media', texto)

        f_met = self.root / motor.METRICAS
        self.assertTrue(f_met.exists())
        lineas = [json.loads(l) for l in f_met.read_text(encoding='utf-8').splitlines() if l.strip()]
        self.assertEqual(lineas[-1]['tipo'], 'promocion')
        self.assertEqual(lineas[-1]['id'], 'T-ADV-0001')
        self.assertEqual(lineas[-1]['de'], 'sencilla')
        self.assertEqual(lineas[-1]['dificultad'], 'media')

        with patch('builtins.print'):
            nueva2 = motor.promover_dificultad(self.root, 'T-ADV-0001')
        self.assertEqual(nueva2, 'dificil')
        self.assertEqual(motor.dificultad_de(self.root, 'T-ADV-0001'), 'dificil')

        with patch('builtins.print'):
            nueva3 = motor.promover_dificultad(self.root, 'T-ADV-0001')
        self.assertIsNone(nueva3)
        self.assertEqual(motor.dificultad_de(self.root, 'T-ADV-0001'), 'dificil')

    def test_reintentos_acumulados_and_rechazos_reset_on_promocion(self):
        tareas = self.root / 'docs/plan/tasks'
        tareas.mkdir(parents=True)
        (tareas / 'T1.md').write_text('---\nid: T1\ndificultad: sencilla\n---\n', encoding='utf-8')

        motor.registrar(self.root, {'tipo': 'paso', 'paso': 'task-dev', 'id': 'T1'})
        motor.registrar(self.root, {'tipo': 'paso', 'paso': 'task-dev', 'id': 'T1'})
        motor.registrar(self.root, {'tipo': 'agente', 'rol': 'hades', 'id': 'T1', 'veredicto': 'RECHAZADO'})
        motor.registrar(self.root, {'tipo': 'agente', 'rol': 'hades', 'id': 'T1', 'veredicto': 'RECHAZADO'})

        self.assertEqual(motor.rechazos(self.root, 'T1'), 2)
        self.assertEqual(motor.reintentos_acumulados(self.root, 'T1'), (2, 2))

        with patch('builtins.print'):
            motor.promover_dificultad(self.root, 'T1')

        self.assertEqual(motor.rechazos(self.root, 'T1'), 0)
        self.assertEqual(motor.reintentos_acumulados(self.root, 'T1'), (0, 0))

    def test_tope_de_rechazos_with_dificultad_levels(self):
        cfg = {
            'artemisa': {
                'harness': 'agy',
                'model': 'base-model',
                'dificultad': {
                    'sencilla': {'model': 'model-s'},
                    'media': {'model': 'model-m'},
                    'dificil': {'model': 'model-d'},
                },
                'escalada': {
                    'rechazos': 2,
                    'model': 'model-esc'
                }
            }
        }
        tareas = self.root / 'docs/plan/tasks'
        tareas.mkdir(parents=True)
        (tareas / 'T-S.md').write_text('---\nid: T-S\ndificultad: sencilla\n---\n', encoding='utf-8')
        (tareas / 'T-D.md').write_text('---\nid: T-D\ndificultad: dificil\n---\n', encoding='utf-8')

        with (patch.object(motor, 'config', return_value=cfg),
              patch.object(motor, 'rechazos', return_value=2)):
            # T-S can promote
            msg_s = motor.tope_de_rechazos(self.root, 'T-S')
            self.assertIn('subirá la dificultad de la tarea y la relanzará con el perfil del nuevo nivel', msg_s)

            # T-D cannot promote; should escalate
            msg_d = motor.tope_de_rechazos(self.root, 'T-D')
            self.assertIn('el bucle relanzará la tarea con un modelo superior', msg_d)

            # T-D already escalated; should apply rule 5
            with patch.dict(motor.os.environ, {'ORQUESTAR_ESCALADA': '1'}):
                msg_d_esc = motor.tope_de_rechazos(self.root, 'T-D')
                self.assertIn('aplica la regla 5 del modo orquestado', msg_d_esc)

    def test_comprobar_promocion_detects_rechazos_and_step_executions(self):
        tareas = self.root / 'docs/plan/tasks'
        tareas.mkdir(parents=True)
        (tareas / 'T1.md').write_text('---\nid: T1\ndificultad: sencilla\n---\n', encoding='utf-8')
        (tareas / 'T2.md').write_text('---\nid: T2\ndificultad: dificil\n---\n', encoding='utf-8')

        # 3 ejecuciones de paso (> 2)
        for _ in range(3):
            motor.registrar(self.root, {'tipo': 'paso', 'paso': 'task-dev', 'id': 'T1'})
        debe, motivo = motor.comprobar_promocion(self.root, 'T1')
        self.assertTrue(debe)
        self.assertIn('ejecuciones', motivo)

        # Si ya es difícil, no promueve
        for _ in range(3):
            motor.registrar(self.root, {'tipo': 'paso', 'paso': 'task-dev', 'id': 'T2'})
        debe_d, _ = motor.comprobar_promocion(self.root, 'T2')
        self.assertFalse(debe_d)

    def test_bucle_promotes_difficulty_on_sin_progreso_and_retries(self):
        self.root.joinpath('task_config.yaml').write_text('validation:\n  command: true\n', encoding='utf-8')
        tareas = self.root / 'docs/plan/tasks'
        tareas.mkdir(parents=True)
        (tareas / 'T1.md').write_text('---\nid: T1\nstatus: planned\ndificultad: sencilla\nversion: "v0.1.0"\n---\n', encoding='utf-8')
        (self.root / 'docs/requirements').mkdir(parents=True)
        (self.root / 'docs/requirements/requirements.md').write_text('Idea\n', encoding='utf-8')

        llamadas = []
        def fake_ejecutar(a, root, prompt, env=None, rol=None, sesion=None):
            llamadas.append(rol.get('model'))
            return 0, {}, 'output'

        cfg = {
            'artemisa': {
                'harness': 'agy',
                'model': 'model-base',
                'dificultad': {
                    'sencilla': {'model': 'model-sencillo'},
                    'media': {'model': 'model-medio'},
                    'dificil': {'model': 'model-dificil'}
                }
            }
        }
        class Args:
            docs = Path('docs/requirements')
            idea = ''
            test = None
            max_pasos = 5
            reintentos = 1
            cmd = None
            harness = 'agy'
            espera_max = 1
            estado = False

        with (patch.object(motor, 'config', return_value=cfg),
              patch.object(motor, 'ejecutar', side_effect=fake_ejecutar),
              patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'enviar', return_value=True) as enviar,
              patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'token-de-prueba', 'TELEGRAM_ALLOWED_USER_IDS': '1'}),
              patch('urllib.request.urlopen') as urlopen,
              patch.object(motor, 'firma', side_effect=[1, 1, 1, 2, 2]),
              patch.object(motor, 'estado', side_effect=[
                  ('PASO', 'task-dev', 'T1', 'release/v0.1'),
                  ('PASO', 'task-dev', 'T1', 'release/v0.1'),
                  ('FIN', 'v0.1'),
              ]),
              patch('builtins.print')):
            codigo = motor.bucle(Args(), self.root)
            self.assertEqual(motor.dificultad_de(self.root, 'T1'), 'media')
            self.assertEqual(llamadas[0], 'model-sencillo')
            self.assertEqual(llamadas[1], 'model-medio')
            enviar.assert_called()
            urlopen.assert_not_called()


class ReservaCuotaTests(unittest.TestCase):
    """Modelos de reserva ante agotamiento de cuota en pasos y subagentes."""

    def setUp(self):
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_lista_reservas_normalizes_object_and_list_with_field_inheritance(self):
        # 1. Sin reserva
        cfg_vacio = {'harness': 'claude', 'model': 'opus'}
        self.assertEqual(motor.lista_reservas(cfg_vacio), [])

        # 2. Objeto único con herencia de harness y effort
        cfg_obj = {
            'harness': 'claude',
            'model': 'claude-opus-5-5',
            'effort': 'high',
            'reserva': {'model': 'claude-sonnet-4-6'}
        }
        res_obj = motor.lista_reservas(cfg_obj)
        self.assertEqual(len(res_obj), 1)
        self.assertEqual(res_obj[0], {
            'harness': 'claude',
            'model': 'claude-sonnet-4-6',
            'effort': 'high'
        })

        # 3. Lista ordenada con sobreescritura y herencia parcial
        cfg_lista = {
            'harness': 'claude',
            'model': 'opus',
            'effort': 'medium',
            'reserva': [
                {'model': 'sonnet'},
                {'harness': 'agy', 'model': 'gemini-3.8-flash-medium'}
            ]
        }
        res_lista = motor.lista_reservas(cfg_lista)
        self.assertEqual(len(res_lista), 2)
        self.assertEqual(res_lista[0], {'harness': 'claude', 'model': 'sonnet', 'effort': 'medium'})
        self.assertEqual(res_lista[1], {'harness': 'agy', 'model': 'gemini-3.8-flash-medium', 'effort': 'medium'})

    def test_agente_switches_to_reserva_on_quota_and_succeeds(self):
        cfg = {
            'hades': {
                'harness': 'claude',
                'model': 'claude-opus-5-5',
                'reserva': {'harness': 'agy', 'model': 'gemini-3.8-flash-medium'}
            }
        }
        llamadas = []

        def fake_lanzar(cmd, root, harness, entrada=None):
            llamadas.append((cmd, harness))
            if harness == 'claude':
                return 1, {'sesion': 'sess-cl'}, 'Error: 429 out of credits'
            return 0, {'sesion': 'sess-agy'}, '## Informe\n- **Veredicto**: APROBADO (media 9)'

        env = {'ORQUESTAR_PASO': 'task-dev', 'ORQUESTAR_ID': 'T-ADV-0001'}
        with (patch.object(motor, 'config', return_value=cfg),
              patch.dict(motor.os.environ, env, clear=True),
              patch.object(motor, 'lanzar', side_effect=fake_lanzar),
              patch.object(motor.shutil, 'which', side_effect=lambda x: x),
              patch.object(motor, 'excluir'),
              patch('builtins.print')):
            codigo = motor.agente(self.root, 'hades', 'revisa')

        self.assertEqual(codigo, 0)
        self.assertEqual(len(llamadas), 2)
        self.assertEqual(llamadas[0][1], 'claude')
        self.assertEqual(llamadas[1][1], 'agy')

        metricas = [json.loads(l) for l in (self.root / motor.METRICAS).read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(metricas), 2)
        # Primer intento: agotó cuota pero no debe tener sin_cuota: True porque conmutó a reserva
        self.assertEqual(metricas[0]['arnes'], 'claude')
        self.assertEqual(metricas[0]['codigo'], 1)
        self.assertNotIn('sin_cuota', metricas[0])
        # Segundo intento: éxito de la reserva
        self.assertEqual(metricas[1]['arnes'], 'agy')
        self.assertEqual(metricas[1]['codigo'], 0)
        self.assertEqual(metricas[1]['veredicto'], 'APROBADO')

    def test_agente_exhausts_all_reservas_records_min_quota_and_fails(self):
        cfg = {
            'hades': {
                'harness': 'claude',
                'model': 'opus',
                'reserva': [
                    {'model': 'sonnet'},
                    {'harness': 'agy', 'model': 'flash'}
                ]
            }
        }
        llamadas = []

        def fake_lanzar(cmd, root, harness, entrada=None):
            llamadas.append(cmd)
            if len(llamadas) == 1:
                return 1, {}, 'usage limit reached | try again in 1 hour'
            if len(llamadas) == 2:
                return 1, {}, '429 too many requests'
            return 1, {}, 'out of credits | try again in 2 hours'

        env = {'ORQUESTAR_PASO': 'task-dev', 'ORQUESTAR_ID': 'T-ADV-0001'}
        with (patch.object(motor, 'config', return_value=cfg),
              patch.dict(motor.os.environ, env, clear=True),
              patch.object(motor, 'lanzar', side_effect=fake_lanzar),
              patch.object(motor.shutil, 'which', side_effect=lambda x: x),
              patch.object(motor, 'excluir'),
              patch('builtins.print')):
            codigo = motor.agente(self.root, 'hades', 'revisa')

        self.assertEqual(codigo, 1)
        self.assertEqual(len(llamadas), 3)

        metricas = [json.loads(l) for l in (self.root / motor.METRICAS).read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(metricas), 3)
        self.assertNotIn('sin_cuota', metricas[0])
        self.assertNotIn('sin_cuota', metricas[1])
        self.assertTrue(metricas[2]['sin_cuota'])
        # Menor cuota de las tres: sondeo supuesto de 300 segundos.
        self.assertEqual(metricas[2]['espera_s'], 300)

    def test_loop_retries_immediately_with_reserva_on_quota_without_waiting(self):
        cfg = {
            'artemisa': {
                'harness': 'claude',
                'model': 'opus',
                'reserva': {'harness': 'agy', 'model': 'gemini-3.8-flash-medium'}
            }
        }
        ejecuciones = []

        def fake_ejecutar(a, root, prompt, env=None, rol=None, sesion=None):
            ejecuciones.append((rol, sesion))
            if len(ejecuciones) == 1:
                return 1, {'sesion': 'sess-dev-1'}, 'out of credits'
            return 0, {'sesion': 'sess-dev-2'}, 'ok'

        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None, estado=False,
                                        max_pasos=2, reintentos=2, espera_max=2, cmd=None)
        with (patch.object(motor, 'config', return_value=cfg),
              patch.object(motor, 'estado', side_effect=[('PASO', 'task-dev', 'T-ADV-0001', ''),
                                                         ('FIN', 'Cerrado.')]),
              patch.object(motor, 'ejecutar', side_effect=fake_ejecutar),
              patch.object(motor, 'esperar') as mock_esperar,
              patch.object(motor, 'firma', side_effect=['a', 'b', 'b']),
              patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'ingerir', return_value=[]),
              patch.object(motor, 'avisar'),
              patch.object(motor, 'excluir'),
              patch('builtins.print')):
            codigo = motor.bucle(args, self.root)

        self.assertEqual(codigo, 0)
        self.assertEqual(len(ejecuciones), 2)
        # Primer intento con claude
        self.assertEqual(ejecuciones[0][0]['harness'], 'claude')
        # Segundo intento con agy (reserva)
        self.assertEqual(ejecuciones[1][0]['harness'], 'agy')
        # Al cambiar de arnés, la sesión debe ser None (sesión nueva)
        self.assertIsNone(ejecuciones[1][1])
        # No debió entrar en esperar()
        mock_esperar.assert_not_called()
        metricas = [json.loads(l) for l in (self.root / motor.METRICAS).read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(metricas), 2)
        self.assertTrue(metricas[0].get('sin_cuota'))
        pasos, _ = motor.reintentos_acumulados(self.root, 'T-ADV-0001')
        self.assertEqual(pasos, 1)

    def test_loop_exhausts_all_reservas_enters_wait(self):
        cfg = {
            'artemisa': {
                'harness': 'claude',
                'model': 'opus',
                'reserva': {'harness': 'claude', 'model': 'sonnet'}
            }
        }
        ejecuciones = []

        def fake_ejecutar(a, root, prompt, env=None, rol=None, sesion=None):
            ejecuciones.append((rol, sesion))
            return 1, {'sesion': 'sess-cl'}, 'out of credits'

        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None, estado=False,
                                        max_pasos=2, reintentos=2, espera_max=2, cmd=None)
        with (patch.object(motor, 'config', return_value=cfg),
              patch.object(motor, 'estado', side_effect=[('PASO', 'task-dev', 'T-ADV-0001', ''),
                                                         ('FIN', 'Cerrado.')]),
              patch.object(motor, 'ejecutar', side_effect=fake_ejecutar),
              patch.object(motor, 'esperar', return_value=True) as mock_esperar,
              patch.object(motor, 'firma', return_value='a'),
              patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'ingerir', return_value=[]),
              patch.object(motor, 'avisar'),
              patch.object(motor, 'excluir'),
              patch('builtins.print')):
            codigo = motor.bucle(args, self.root)

        self.assertEqual(len(ejecuciones), 2)
        mock_esperar.assert_called_once()


if __name__ == '__main__':
    unittest.main()


class SuiteRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.tmp)
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
        self.enterContext(patch.object(motor, 'recargar_version', return_value=False))
        self.git('init', '-q')
        self.git('config', 'user.name', 'Suite Test')
        self.git('config', 'user.email', 'suite@example.test')
        self.git('checkout', '-q', '-b', 'release/v0.1')
        (self.root / 'task_config.yaml').write_text(
            'project:\n  prefix: DEM\nlevels:\n  master:\n    path: backlog/\n'
            '    folders:\n      tasks: tasks/\n      bugs: bugs/\n', encoding='utf-8')
        for name in ('requirements', 'req_analysis', 'platform_plan', 'platform_review', 'work_plan'):
            p = self.root / 'docs' / (name + '.md')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('**Veredicto:** APROBADO', encoding='utf-8')
        initial = self.root / 'backlog/tasks/T-DEM-0001.md'
        initial.parent.mkdir(parents=True, exist_ok=True)
        initial.write_text('---\nid: T-DEM-0001\nstatus: completed\nversion: v0.1.0\ndepende_de: []\n---\n', encoding='utf-8')
        report = self.root / 'docs/review/code_reviews/T-DEM-0001-code-review.md'
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text('APROBADO', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.enterContext(patch.object(motor, 'git', side_effect=lambda *a: self.git(*a)))
        motor.excluir(self.root)

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def evidence(self, text='format: src/app.js: error', command='suite'):
        with (self.root / motor.EVIDENCIAS).open('a', encoding='utf-8') as out:
            out.write(json.dumps({'arbol': 'a' * 40, 'comando': command, 'codigo': 1,
                                  'salida': text}) + '\n')

    def observe_failure(self, text='format: src/app.js: error', command='suite'):
        self.evidence(text, command)
        return motor.registrar_fallo_suite(self.root, 'v0.1', command)

    def complete(self, iid):
        p = motor.fichero_de(self.root, iid)
        p.write_text(p.read_text(encoding='utf-8').replace('status: planned', 'status: completed'), encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'fix attempt')

    def test_capture_and_green_reuse_keep_return_contract(self):
        command = f'"{sys.executable}" -c "import sys; print(123); print(456, file=sys.stderr); sys.exit(7)"'
        self.assertEqual(motor.verificar(self.root, command), 7)
        row = json.loads((self.root / motor.EVIDENCIAS).read_text(encoding='utf-8').splitlines()[-1])
        self.assertIn('123', row['salida'])
        self.assertIn('456', row['salida'])
        self.assertEqual(row['codigo'], 7)
        self.assertEqual(row['comando'], command)
        self.assertEqual(row['arbol'], motor.arbol(self.root))
        command = f'"{sys.executable}" -c "print(789)"'
        self.assertEqual(motor.verificar(self.root, command), 0)
        with patch.object(motor.subprocess, 'run', wraps=motor.subprocess.run) as calls:
            self.assertEqual(motor.verificar(self.root, command), 0)
        self.assertFalse(any(c.kwargs.get('shell') for c in calls.call_args_list))

    def test_capture_is_bounded_and_retains_last_error(self):
        command = f'"{sys.executable}" -c "print(\'x\' * 70000); print(\'last error\'); raise SystemExit(1)"'
        with patch('builtins.print'):
            self.assertEqual(motor.verificar(self.root, command), 1)
        row = json.loads((self.root / motor.EVIDENCIAS).read_text(encoding='utf-8').splitlines()[-1])
        self.assertLessEqual(len(row['salida']), 32768)
        self.assertIn('last error', row['salida'])

    def test_registration_uses_configured_path_prefix_and_normal_selection(self):
        iid, stop = self.observe_failure()
        self.assertEqual(iid, 'B-DEM-0001')
        self.assertFalse(stop)
        p = motor.fichero_de(self.root, iid)
        self.assertEqual(p.parent, self.root / 'backlog/bugs')
        fm = motor.frontmatter(p)
        self.assertEqual(fm['status'], 'planned')
        self.assertEqual(motor.vkey(fm['version']), (0, 1))
        self.assertEqual(motor.lista(fm['depende_de']), [])
        self.assertIn('format: src/app.js: error', p.read_text(encoding='utf-8'))
        self.assertIn('suite', p.read_text(encoding='utf-8'))
        self.assertEqual(motor.estado(self.root, 'docs'), ('PASO', 'bug-fix', iid, 'release/v0.1'))
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_recurrences_reuse_bug_preserve_work_and_promote_after_three(self):
        iid, _ = self.observe_failure()
        p = motor.fichero_de(self.root, iid)
        with p.open('a', encoding='utf-8') as out:
            out.write('\n## Triaje del arreglo\nTrabajo del desarrollador.\n')
        for count in range(1, 4):
            self.complete(iid)
            same, stop = self.observe_failure(f'new error {count}')
            self.assertEqual(same, iid)
            self.assertFalse(stop)
            fm = motor.frontmatter(p)
            self.assertEqual(fm['status'], 'planned')
            self.assertEqual(fm['suite_intentos'], str(count if count < 3 else 0))
            self.assertEqual(fm['dificultad'], 'media' if count < 3 else 'dificil')
            self.assertIn('Trabajo del desarrollador.', p.read_text(encoding='utf-8'))
            self.assertIn(f'new error {count}', p.read_text(encoding='utf-8'))
        self.assertEqual(len(list(p.parent.glob('*.md'))), 1)
        rows = motor.leer_metricas(self.root)
        self.assertEqual(len([r for r in rows if r.get('tipo') == 'promocion']), 1)

    def test_maximum_stops_after_three_failed_fixes_with_last_output(self):
        iid, _ = self.observe_failure()
        motor.actualizar_dificultad(self.root, iid, 'dificil')
        for count in range(1, 4):
            self.complete(iid)
            same, stop = self.observe_failure(f'last failure {count}')
            self.assertEqual(same, iid)
            self.assertEqual(bool(stop), count == 3)
            fm = motor.frontmatter(motor.fichero_de(self.root, iid))
            self.assertEqual(fm['suite_intentos'], str(count))
            self.assertEqual(fm['dificultad'], 'dificil')
            self.assertEqual(fm['status'], 'planned' if count < 3 else 'blocked')
        self.assertIn(iid, stop)
        self.assertIn('last failure 3', stop)
        fm = motor.frontmatter(motor.fichero_de(self.root, iid))
        self.assertEqual(fm['status'], 'blocked')
        self.assertEqual(fm['pendiente_de'], 'humano')

    def test_blocked_and_cancelled_are_not_reopened(self):
        iid, _ = self.observe_failure()
        p = motor.fichero_de(self.root, iid)
        for status in ('blocked', 'cancelled'):
            original = p.read_text(encoding='utf-8')
            original = original.replace('status: planned', f'status: {status}').replace('status: blocked', f'status: {status}')
            p.write_text(original, encoding='utf-8')
            same, stop = self.observe_failure()
            self.assertEqual(same, iid)
            self.assertIn(iid, stop)
            self.assertEqual(p.read_text(encoding='utf-8'), original)

    def test_pending_recheck_does_not_count_another_fix_or_duplicate(self):
        iid, _ = self.observe_failure()
        same, stop = self.observe_failure('another observation')
        self.assertEqual(same, iid)
        self.assertFalse(stop)
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, iid))['suite_intentos'], '0')
        previous = motor.fichero_de(self.root, iid).read_bytes()
        other, _ = self.observe_failure(command='another suite')
        self.assertNotEqual(other, iid)
        self.assertEqual(motor.fichero_de(self.root, iid).read_bytes(), previous)
        self.evidence()
        other_version, _ = motor.registrar_fallo_suite(self.root, 'v0.2', 'suite')
        self.assertNotIn(other_version, (iid, other))
        self.assertEqual(motor.fichero_de(self.root, iid).read_bytes(), previous)

    def test_loop_runs_bug_fix_then_green_suite_then_review(self):
        args = motor.argparse.Namespace(idea=None, docs='docs', test='suite', harness='claude', estado=False,
                                       max_pasos=3, reintentos=2, espera_max=0, cmd=None)
        steps = []
        events = []
        def verify_suite(root, command):
            result = 1 if not events else 0
            events.append('suite roja' if result else 'suite verde')
            return result
        def execute(a, root, prompt, **kwargs):
            steps.append(kwargs['env']['ORQUESTAR_PASO'])
            if steps[-1] == 'bug-fix':
                iid = kwargs['env']['ORQUESTAR_ID']
                self.complete(iid)
                report = root / f'docs/review/code_reviews/{iid}-code-review.md'
                report.write_text('APROBADO', encoding='utf-8')
                self.git('add', '.')
                self.git('commit', '-qm', 'review')
                events.append('bug-fix completado')
            else:
                events.append('revisar-version')
                (root / motor.PARADA).write_text('stop', encoding='utf-8')
            return 0, {}, ''
        self.evidence()
        with (patch.object(motor, 'verificar', side_effect=verify_suite) as verify,
              patch.object(motor, 'ejecutar', side_effect=execute),
              patch.object(motor, 'avisar')):
            self.assertEqual(motor.bucle(args, self.root), 2)
        self.assertEqual(events, ['suite roja', 'bug-fix completado', 'suite verde', 'revisar-version'])
        self.assertEqual(steps, ['bug-fix', 'revisar-version'])
        self.assertEqual(verify.call_count, 2)

    def test_loop_at_maximum_notifies_and_never_launches_review(self):
        iid, _ = self.observe_failure()
        motor.actualizar_dificultad(self.root, iid, 'dificil')
        for _ in range(2):
            self.complete(iid)
            self.observe_failure()
        self.complete(iid)
        report = self.root / f'docs/review/code_reviews/{iid}-code-review.md'
        report.write_text('APROBADO', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'review')
        self.evidence('final error src/app.js')
        args = motor.argparse.Namespace(idea=None, docs='docs', test='suite', harness='claude', estado=False,
                                       max_pasos=1, reintentos=2, espera_max=0, cmd=None)
        with (patch.object(motor, 'verificar', return_value=1),
              patch.object(motor, 'ejecutar') as execute,
              patch.object(motor, 'avisar') as notify,
              patch('builtins.print') as output):
            self.assertEqual(motor.bucle(args, self.root), 2)
        execute.assert_not_called()
        self.assertIn(iid, notify.call_args.args[2])
        self.assertIn('final error src/app.js', notify.call_args.args[2])
        self.assertTrue(any(iid in str(c) and 'final error' in str(c) for c in output.call_args_list))

    def test_escaped_command_reuses_id_without_pyyaml(self):
        command = r'"C:\Program Files\Python\python.exe" -c "print(1)"'
        with patch.object(motor, 'yaml', yaml_lite), patch.dict(sys.modules, {'yaml': None}):
            iid, _ = self.observe_failure(command=command)
            for count in (1, 2):
                self.complete(iid)
                same, stop = self.observe_failure(f'error {count}', command=command)
                self.assertEqual(same, iid)
                self.assertFalse(stop)
                fm = motor.frontmatter(motor.fichero_de(self.root, iid))
                self.assertEqual(fm['suite_intentos'], str(count))
            self.assertEqual(len(list(motor.backlog_dirs(self.root)[1].glob('*.md'))), 1)

    def test_long_stop_output_fits_final_telegram_transport(self):
        iid, _ = self.observe_failure()
        motor.actualizar_dificultad(self.root, iid, 'dificil')
        for _ in range(2):
            self.complete(iid)
            self.observe_failure()
        self.complete(iid)
        text = '\U0001f600' * 5000 + '\nlast error src/app.js'
        _, stop = self.observe_failure(text)
        with (patch.object(motor, 'telegram', return_value=('fake', ['123'], {'version'})),
              patch.object(motor, 'enviar', return_value=True) as send,
              patch('builtins.print')):
            self.assertEqual(motor.parar(self.root, 'version', stop), 2)
        message = send.call_args.args[2]
        self.assertLessEqual(len(message.encode('utf-16-le')) // 2, 4096)
        self.assertIn(iid, message)
        self.assertIn('last error src/app.js', message)
        self.assertIn('Adevv v', message)
        body = motor.fichero_de(self.root, iid).read_text(encoding='utf-8')
        captured = '\n'.join(line[4:] for line in body.splitlines() if line.startswith('    '))
        self.assertEqual(captured, text)

    def check_checkout_before_suite(self, closing):
        self.git('checkout', '-qb', 'another')
        self.evidence()
        events = []
        def verify(root, command):
            events.append(('suite', self.git('branch', '--show-current')))
            return 1
        def execute(*args, **kwargs):
            events.append((kwargs['env']['ORQUESTAR_PASO'], self.git('branch', '--show-current')))
            self.assertEqual(self.git('status', '--porcelain'), '')
            return 0, {}, ''
        args = motor.argparse.Namespace(idea=None, docs='docs', test='suite', harness='claude', estado=False,
                                       max_pasos=1, reintentos=2, espera_max=0, cmd=None)
        with (patch.object(motor, 'estado', side_effect=[closing, ('PASO', 'bug-fix', 'B-DEM-0001', 'release/v0.1')]),
              patch.object(motor, 'firma', side_effect=[0, 1]),
              patch.object(motor, 'verificar', side_effect=verify),
              patch.object(motor, 'ejecutar', side_effect=execute),
              patch.object(motor, 'avisar')):
            self.assertEqual(motor.bucle(args, self.root), 2)
        self.assertEqual(events, [('suite', 'release/v0.1'), ('bug-fix', 'release/v0.1')])
        self.assertIn('B-DEM-0001', self.git('log', '-1', '--format=%s', 'release/v0.1'))
        self.assertEqual(self.git('log', '-1', '--format=%s', 'another'), 'fixture')

    def test_checkout_precedes_suite_for_review_step(self):
        self.check_checkout_before_suite(('PASO', 'revisar-version', 'v0.1', 'release/v0.1'))

    def test_checkout_precedes_suite_for_final_stop(self):
        self.check_checkout_before_suite(('PARAR', 'Versión v0.1 terminada. Revisa'))

    def test_dirty_tree_prevents_checkout_suite_and_bug_registration(self):
        self.git('checkout', '-qb', 'another')
        (self.root / 'pending.txt').write_text('pending work', encoding='utf-8')
        args = motor.argparse.Namespace(idea=None, docs='docs', test='suite', harness='claude', estado=False,
                                       max_pasos=1, reintentos=2, espera_max=0, cmd=None)
        for closing in (('PASO', 'revisar-version', 'v0.1', 'release/v0.1'),
                        ('PARAR', 'Versión v0.1 terminada. Revisa')):
            with (self.subTest(closing=closing), patch.object(motor, 'estado', return_value=closing),
                  patch.object(motor, 'verificar') as verify, patch.object(motor, 'ejecutar') as execute,
                  patch.object(motor, 'registrar_fallo_suite') as register, patch.object(motor, 'avisar')):
                self.assertEqual(motor.bucle(args, self.root), 2)
            verify.assert_not_called()
            execute.assert_not_called()
            register.assert_not_called()
            self.assertEqual(self.git('branch', '--show-current'), 'another')


class BloqueoSinProgresoTests(unittest.TestCase):
    """Aísla una tarea atascada usando Git, selector y persistencia reales."""
    def setUp(self):
        self.tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.tmp)
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
        self.enterContext(patch.object(motor, 'recargar_version', return_value=False))
        self.git('init', '-q')
        self.git('config', 'user.name', 'Suite Test')
        self.git('config', 'user.email', 'suite@example.test')
        self.git('checkout', '-q', '-b', 'release/v0.1')
        (self.root / 'task_config.yaml').write_text(
            'project:\n  prefix: DEM\nlevels:\n  master:\n    path: backlog/\n'
            '    folders:\n      tasks: tasks/\n      bugs: bugs/\n', encoding='utf-8')
        for name in ('requirements', 'req_analysis', 'platform_plan', 'platform_review', 'work_plan'):
            p = self.root / 'docs' / (name + '.md')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('**Veredicto:** APROBADO', encoding='utf-8')
        initial = self.root / 'backlog/tasks/T-DEM-0001.md'
        initial.parent.mkdir(parents=True, exist_ok=True)
        initial.write_text('---\nid: T-DEM-0001\nstatus: completed\nversion: v0.1.0\ndepende_de: []\n---\n', encoding='utf-8')
        report = self.root / 'docs/review/code_reviews/T-DEM-0001-code-review.md'
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text('APROBADO', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.enterContext(patch.object(motor, 'git', side_effect=lambda *a: self.git(*a)))
        motor.excluir(self.root)

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()


    def test_bloquea_solo_atascada_y_completa_independiente(self):
        """Ambos pasos aíslan el bloqueo; media promociona antes de bloquear."""
        for paso, nivel in [('task-dev', 'dificil'), ('bug-fix', 'dificil'), ('task-dev', 'media')]:
            with self.subTest(paso=paso, dificultad=nivel):
                self.ejercitar_bloqueo(paso, nivel)

    def ejercitar_bloqueo(self, paso, nivel):
        """Observa las llamadas del arnés y el resultado persistido del bucle."""
        for carpeta in ('backlog/tasks', 'backlog/bugs'):
            for p in (self.root / carpeta).glob('*.md'):
                p.unlink()
        iid = 'T-DEM-0001' if paso == 'task-dev' else 'B-DEM-0001'
        carpeta = 'tasks' if paso == 'task-dev' else 'bugs'
        atascada = self.root / f'backlog/{carpeta}/{iid}.md'
        atascada.parent.mkdir(parents=True, exist_ok=True)
        atascada.write_text(f'---\nid: {iid}\nstatus: in_progress\ndificultad: {nivel}\n'
                            'version: v0.1.0\ndepende_de: []\n---\n\nTrabajo previo.\n', encoding='utf-8')
        for otro, dependencia in [('T-DEM-0002', '[]'), ('T-DEM-0003', f'[{iid}]')]:
            (self.root / f'backlog/tasks/{otro}.md').write_text(
                f'---\nid: {otro}\nstatus: planned\nversion: v0.1.0\ndepende_de: {dependencia}\n---\n', encoding='utf-8')
        revision = self.root / 'docs/review/versions/v0.1-revision.md'
        revision.parent.mkdir(parents=True, exist_ok=True)
        revision.write_text('Contenido previo.\n', encoding='utf-8')
        (revision.parent / 'v0.1-arquitectura.md').write_text('APROBADO', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'preparar tareas')
        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness='claude',
            estado=False, max_pasos=8, reintentos=2, espera_max=0, cmd=None)
        llamadas = []
        cola = 'Z' * 1989 + 'FIN RECHAZO'
        def ejecutar(a, root, prompt, **kwargs):
            actual = kwargs['env']['ORQUESTAR_ID']
            llamadas.append((actual, motor.dificultad_de(root, actual)))
            if actual != iid:
                self.assertEqual(actual, 'T-DEM-0002')
                self.assertEqual(self.git('status', '--porcelain'), '')
                p = motor.fichero_de(root, actual)
                p.write_text(p.read_text(encoding='utf-8').replace('status: planned', 'status: completed'), encoding='utf-8')
                (root / f'docs/review/code_reviews/{actual}-code-review.md').write_text('APROBADO', encoding='utf-8')
                self.git('add', '.')
                self.git('commit', '-qm', 'completar independiente')
            return 0, {}, 'DESCARTAR' * 500 + cola
        with (patch.object(motor, 'ejecutar', side_effect=ejecutar),
              patch.object(motor, 'construir_prompt_paso', return_value='prompt'),
              patch.object(motor, 'comprobar_promocion', return_value=(False, '')),
              patch.object(motor, 'avisar') as aviso, patch('builtins.print')):
            self.assertEqual(motor.bucle(args, self.root), 2)
        fm = motor.frontmatter(atascada)
        self.assertEqual(fm['status'], 'blocked')
        self.assertEqual(fm['pendiente_de'], 'humano')
        self.assertEqual(fm['dificultad'], 'dificil')
        texto = atascada.read_text(encoding='utf-8').split('---', 2)[2]
        for fragmento in ('Trabajo previo.', '2 intentos', 'dificil', cola):
            self.assertIn(fragmento, texto)
        self.assertNotIn('DESCARTAR', texto)
        informe = revision.read_text(encoding='utf-8')
        self.assertIn('Contenido previo.', informe)
        self.assertIn(iid, informe)
        self.assertIn(cola, informe)
        self.assertIn('2 intentos', informe)
        self.assertIn('dificil', informe)
        self.assertTrue(any(iid in c.args[2] and cola in c.args[2] for c in aviso.call_args_list))
        self.assertEqual(llamadas, [(iid, 'media')] * 2 + [(iid, 'dificil')] * 2 + [('T-DEM-0002', 'media')]
                         if nivel == 'media' else [(iid, 'dificil')] * 2 + [('T-DEM-0002', 'media')])
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, 'T-DEM-0002'))['status'], 'completed')
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, 'T-DEM-0003'))['status'], 'planned')
        estado = motor.estado(self.root, 'docs')
        self.assertEqual(estado[0], 'PARAR')
        self.assertTrue(estado[1].startswith(motor.FIN_VERSION[0]))
        self.assertIn(iid, estado[1])
        self.assertEqual(self.git('status', '--porcelain'), '')


class RecuperacionAnalisisTests(unittest.TestCase):
    """Recorre el bucle con perfiles ficticios y resultados observables, sin proveedores."""

    setUp = BloqueoSinProgresoTests.setUp
    git = BloqueoSinProgresoTests.git
    pasos = ('especificar', 'revisar-tarea', 'revisar-version', 'calcular-dependencias',
             'work-plan', 'revisar-deuda', 'aplicar-producto')
    perfiles = [('codex', 'base-demo', 'medium'), ('codex', 'superior-demo', 'high'),
                ('claude', 'escalado-demo', 'high'), ('agy', 'reserva-demo', 'medium')]

    def preparar(self):
        """Declara el contrato común en la configuración real de ambos roles."""
        cfg = {'harness': 'codex', 'model': 'base-demo', 'effort': 'medium',
               'dificultad': {'media': {'model': 'base-demo'},
                              'dificil': {'model': 'superior-demo', 'effort': 'high'}},
               'escalada': {'harness': 'claude', 'model': 'escalado-demo', 'effort': 'high'},
               'reserva': [{'model': 'superior-demo', 'effort': 'high'},
                           {'harness': 'agy', 'model': 'reserva-demo'}]}
        (self.root / motor.CONFIG).write_text(json.dumps({'atenea': cfg, 'artemisa': cfg}), encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'perfiles ficticios')
        return cfg

    def argumentos(self, recarga=None):
        return motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None,
            estado=False, max_pasos=80, reintentos=2, espera_max=0, cmd=None, recarga=recarga)

    def simular(self, pares, avanzar=None, recarga=None, capturar=None, continuar=False):
        """Intercala pares sin modificar artificialmente la firma por cambiar de selector."""
        iterador = iter(pares)
        llamadas = []
        progreso = [0]
        siguiente = [False]
        def seleccionar(*args):
            if continuar and progreso[0] and not siguiente[0]:
                siguiente[0] = True
                return ('PASO', 'start-version', 'v0.2', None)
            return next(iterador, ('FIN', 'fin simulado'))
        def ejecutar(a, root, prompt, **kw):
            cfg = kw['rol']
            perfil = tuple(cfg.get(k) for k in ('harness', 'model', 'effort'))
            par = (kw['env']['ORQUESTAR_PASO'], kw['env']['ORQUESTAR_ID'])
            llamadas.append((par, perfil, kw.get('sesion'), kw['env'].get('ORQUESTAR_ESCALADA')))
            if avanzar and avanzar(len(llamadas), par, perfil):
                progreso[0] += 1
            return 0, {'sesion': 'sesion-anterior'}, ''
        def transferir(*args):
            if capturar is not None:
                capturar.append(json.loads(json.dumps(args[3])))
            return False
        with (patch.object(motor, 'estado', side_effect=seleccionar),
              patch.object(motor, 'firma', side_effect=lambda *a: progreso[0]),
              patch.object(motor, 'ejecutar', side_effect=ejecutar),
              patch.object(motor, 'construir_prompt_paso', return_value='prompt'),
              patch.object(motor, 'buscar_sesion_paso', return_value='sesion-anterior'),
              patch.object(motor, 'recargar_version', side_effect=transferir),
              patch.object(motor, 'avisar'), patch('builtins.print')):
            resultado = motor.bucle(self.argumentos(recarga), self.root)
        return resultado, llamadas

    def test_exito_en_escalada_y_reserva_para_los_siete_pasos(self):
        self.preparar()
        for paso in self.pasos:
            for ganador in (2, 3):
                with self.subTest(paso=paso, ganador=ganador):
                    par = (paso, 'T-DEM-0001' if paso in self.pasos[:2] else
                           None if paso in ('work-plan', 'calcular-dependencias') else 'v0.1')
                    contador = 2 * ganador + 1
                    resultado, llamadas = self.simular(
                        [('PASO', *par, None)] * (contador + 1),
                        avanzar=lambda n, par, perfil: n == contador, continuar=True)
                    self.assertEqual(resultado, 0)
                    self.assertEqual([c[1] for c in llamadas],
                                     [p for p in self.perfiles[:ganador] for _ in range(2)] + [self.perfiles[ganador], self.perfiles[0], self.perfiles[0]])
                    for i in range(2, contador, 2):
                        self.assertIsNone(llamadas[i][2], 'cambiar de perfil exige sesión nueva')
                    self.assertEqual(llamadas[contador][0], ('start-version', 'v0.2'))
                    self.assertEqual(llamadas[contador + 1][0], (par[0], par[1] or ''))

    def test_agotamiento_global_diagnostica_sin_escribir_backlog(self):
        self.preparar()
        for paso in self.pasos[2:]:
            with self.subTest(paso=paso):
                antes = motor.fichero_de(self.root, 'T-DEM-0001').read_bytes()
                with patch.object(motor, 'parar', return_value=2) as parar:
                    argumento = None if paso in ('work-plan', 'calcular-dependencias') else 'v0.1'
                    resultado, llamadas = self.simular([('PASO', paso, argumento, None)] * 9)
                self.assertEqual(resultado, 2)
                self.assertEqual([c[1] for c in llamadas], [p for p in self.perfiles for _ in range(2)])
                diagnostico = parar.call_args.args[2]
                for fragmento in (paso, argumento or '(sin argumento)', '2 intentos', *('/'.join(p) for p in self.perfiles)):
                    self.assertIn(fragmento, diagnostico)
                self.comprobar_diagnostico(diagnostico)
                self.assertEqual(motor.fichero_de(self.root, 'T-DEM-0001').read_bytes(), antes)
                self.assertEqual(self.git('status', '--porcelain'), '')

    def test_rechazos_previos_no_adelantan_escalada_ni_sustituyen_reservas(self):
        """La recuperación de análisis conserva el orden aunque Hades haya rechazado el ID."""
        cfg = self.preparar()
        cfg['escalada']['reserva'] = [{'model': 'reserva-exclusiva-escalada'}]
        (self.root / motor.CONFIG).write_text(json.dumps({'artemisa': cfg}), encoding='utf-8')
        with patch.object(motor, 'rechazos', return_value=2):
            resultado, llamadas = self.simular(
                [('PASO', 'revisar-tarea', 'T-DEM-0001', None)] * 7,
                avanzar=lambda n, par, perfil: n == 7)
        self.assertEqual(resultado, 0)
        self.assertEqual([c[1] for c in llamadas],
                         [p for p in self.perfiles[:3] for _ in range(2)] + [self.perfiles[3]])
        self.assertTrue(all(c[3] is None for c in llamadas))

    def test_intercalado_y_progreso_reinician_solo_el_par_correcto(self):
        self.preparar()
        for otro in [('especificar', 'T-DEM-0002'), ('revisar-tarea', 'T-DEM-0001')]:
            with self.subTest(otro=otro):
                uno = ('especificar', 'T-DEM-0001')
                secuencia = [uno, uno, uno, otro, uno, uno, otro]
                _, llamadas = self.simular([('PASO', *par, None) for par in secuencia])
                self.assertEqual([c[1] for c in llamadas],
                    [self.perfiles[i] for i in (0, 0, 1, 0, 1, 2, 0)])
                secuencia = [uno, uno, uno, otro, otro, otro, uno, uno, uno, uno, otro]
                _, llamadas = self.simular([('PASO', *par, None) for par in secuencia],
                                          avanzar=lambda n, par, perfil: n == 7)
                self.assertEqual([c[1] for c in llamadas],
                    [self.perfiles[i] for i in (0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1)])

    def test_recarga_conserva_dos_pares_y_contadores_parciales(self):
        self.preparar()
        uno, otro = ('especificar', 'T-DEM-0001'), ('especificar', 'T-DEM-0002')
        estados = []
        self.simular([('PASO', *par, None) for par in [uno, uno, uno, otro]], capturar=estados)
        transferencia = estados[-1]
        transferencia['n'] = 1
        _, llamadas = self.simular([('PASO', *par, None) for par in [uno, uno, otro, otro]], recarga=transferencia)
        self.assertEqual([c[1] for c in llamadas], [self.perfiles[i] for i in (1, 2, 0, 1)])

    def test_perfiles_heredan_sobreescrituras_y_no_expanden_reservas(self):
        cfg = self.preparar()
        cfg['pasos'] = {'work-plan': {'effort': 'low'}}
        cfg['dificultad']['dificil']['reserva'] = [{'model': 'no-expandir-nivel'}]
        cfg['escalada']['reserva'] = [{'model': 'no-expandir-escalada'}]
        (self.root / motor.CONFIG).write_text(json.dumps({'atenea': cfg}), encoding='utf-8')
        cadena = motor.cadena_analisis(self.root, 'work-plan', 'media')
        self.assertEqual([tuple(c.get(k) for k in ('harness', 'model', 'effort')) for c in cadena],
            [('codex', 'base-demo', 'low'), ('codex', 'superior-demo', 'low'),
             ('claude', 'escalado-demo', 'high'), ('codex', 'superior-demo', 'high'),
             ('agy', 'reserva-demo', 'low')])
        for cfg_sin_niveles in ({'harness': 'codex', 'model': 'solo'},
                               {'harness': 'codex', 'model': 'solo', 'reserva': [{'model': 'reserva'}]}):
            (self.root / motor.CONFIG).write_text(json.dumps({'atenea': cfg_sin_niveles}), encoding='utf-8')
            cadena = motor.cadena_analisis(self.root, 'work-plan', 'media')
            self.assertEqual([c['model'] for c in cadena],
                             ['solo', 'reserva'] if 'reserva' in cfg_sin_niveles else ['solo'])

    def test_agotamiento_local_bloquea_y_continua_independiente(self):
        self.preparar()
        for paso in self.pasos[:2]:
            with self.subTest(paso=paso):
                atascada = motor.fichero_de(self.root, 'T-DEM-0001')
                estado = 'blocked\npendiente_de: especificador' if paso == 'especificar' else 'completed'
                atascada.write_text('---\nid: T-DEM-0001\nstatus: ' + estado + '\ndificultad: media\n'
                                    'version: v0.1.0\ndepende_de: []\n---\nTrabajo previo.\n', encoding='utf-8')
                (self.root / 'docs/review/code_reviews/T-DEM-0001-code-review.md').unlink(missing_ok=True)
                for iid, dep in [('T-DEM-0002', '[]'), ('T-DEM-0003', '[T-DEM-0001]')]:
                    (self.root / f'backlog/tasks/{iid}.md').write_text(
                        f'---\nid: {iid}\nstatus: planned\nversion: v0.1.0\ndepende_de: {dep}\n---\n', encoding='utf-8')
                revision = self.root / 'docs/review/versions/v0.1-revision.md'
                revision.parent.mkdir(parents=True, exist_ok=True)
                revision.write_text('Contenido previo.\n', encoding='utf-8')
                (revision.parent / 'v0.1-arquitectura.md').write_text('APROBADO', encoding='utf-8')
                self.git('add', '.')
                self.git('commit', '-qm', 'caso local')
                llamadas = []
                def ejecutar(a, root, prompt, **kw):
                    iid = kw['env']['ORQUESTAR_ID']
                    llamadas.append((iid, tuple(kw['rol'].get(k) for k in ('harness', 'model', 'effort'))))
                    if iid != 'T-DEM-0001':
                        self.assertEqual(iid, 'T-DEM-0002')
                        f = motor.fichero_de(root, iid)
                        f.write_text(f.read_text(encoding='utf-8').replace('status: planned', 'status: completed'), encoding='utf-8')
                        (root / f'docs/review/code_reviews/{iid}-code-review.md').write_text('APROBADO', encoding='utf-8')
                        self.git('add', '.')
                        self.git('commit', '-qm', 'completar independiente')
                    return 0, {}, 'cola local'
                with (patch.object(motor, 'ejecutar', side_effect=ejecutar),
                      patch.object(motor, 'construir_prompt_paso', return_value='prompt'),
                      patch.object(motor, 'comprobar_promocion', return_value=(False, '')),
                      patch.object(motor, 'avisar') as avisar, patch('builtins.print') as imprimir):
                    self.assertEqual(motor.bucle(self.argumentos(), self.root), 2)
                self.assertEqual(llamadas, [('T-DEM-0001', p) for p in self.perfiles for _ in range(2)] +
                                 [('T-DEM-0002', self.perfiles[0])])
                fm = motor.frontmatter(atascada)
                self.assertEqual((fm['status'], fm['pendiente_de'], fm['dificultad']), ('blocked', 'humano', 'media'))
                self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, 'T-DEM-0002'))['status'], 'completed')
                self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, 'T-DEM-0003'))['status'], 'planned')
                for texto in (atascada.read_text(encoding='utf-8'), revision.read_text(encoding='utf-8'),
                              '\n'.join(str(c) for c in avisar.call_args_list),
                              '\n'.join(str(c) for c in imprimir.call_args_list)):
                    for dato in (paso, 'T-DEM-0001', '2 intentos', *('/'.join(p) for p in self.perfiles)):
                        self.assertIn(dato, texto)
                    self.comprobar_diagnostico(texto)
                self.assertIn('Trabajo previo.', atascada.read_text(encoding='utf-8'))
                self.assertIn('Contenido previo.', revision.read_text(encoding='utf-8'))
                self.assertEqual(self.git('status', '--porcelain'), '')

    def comprobar_diagnostico(self, texto):
        """Cada perfil se informa en orden y asociado a su propio conteo."""
        posiciones = [texto.index('/'.join(p)) for p in self.perfiles]
        self.assertEqual(posiciones, sorted(posiciones))
        for inicio, fin in zip(posiciones, posiciones[1:] + [len(texto)]):
            self.assertIn('2 intentos', texto[inicio:fin])
