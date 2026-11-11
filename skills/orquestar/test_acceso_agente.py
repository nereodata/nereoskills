"""B-ADV-0040: reservas por suscripción deshabilitada y recuperación aislada."""

import importlib.util
import io
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tests import aislamiento_telegram


SPEC = importlib.util.spec_from_file_location('motor_acceso', Path(__file__).with_name('orquestar.py'))
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)
LANZAR_REAL = motor.lanzar
POPEN_REAL = subprocess.Popen
ERROR = 'Your organization has disabled Claude subscription access for Claude Code.'
ERROR_REAL = ('Your organization has disabled Claude subscription access for Claude Code · '
              'Use an Anthropic API key instead, or ask your admin to enable access')


class AccesoAgenteTests(unittest.TestCase):
    """Ejecuta agentes reales salvo el proceso del proveedor, sin red."""

    def setUp(self):
        """Aísla estado, reloj y lanzadores de modelos."""
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.cfg = {'harness': 'claude', 'model': 'principal', 'reserva': [
            {'harness': 'agy', 'model': 'intermedia'}, {'harness': 'codex', 'model': 'ultima'}]}
        self.enterContext(patch.dict(motor.os.environ, {}, clear=True))
        self.enterContext(patch.object(motor, 'config', side_effect=lambda root: {'hades': self.cfg}))
        self.enterContext(patch.object(motor, 'ahora', return_value='2026-11-11T10:00:00Z'))
        self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe))
        self.enterContext(patch.object(motor, 'construir_prompt_agente', return_value='revisa'))
        self.enterContext(patch.object(motor, 'excluir'))
        self.enterContext(patch.object(motor, 'buscar_sesion_agente', return_value=None))
        self.aviso = self.enterContext(patch.object(motor, 'avisar'))
        self.consola = self.enterContext(patch('builtins.print'))
        self.lanzar = self.enterContext(patch.object(motor, 'lanzar'))

    def test_diagnostico_real_sin_punto_alcanza_reserva(self):
        """El error real 403 conserva diagnóstico y alcanza una reserva elegible."""
        self.lanzar.side_effect = [(1, {}, ERROR_REAL), (0, {}, 'Veredicto: APROBADO')]
        with patch.object(motor, 'buscar_sesion_agente', return_value='anterior'):
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
        self.assertEqual([c.args[2] for c in self.lanzar.call_args_list], ['claude', 'agy'])
        filas = motor.leer_metricas(self.root)
        self.assertTrue(filas[0]['acceso_denegado'])
        self.assertEqual(filas[0]['diagnostico'], ERROR_REAL)
        self.assertEqual(filas[0]['codigo'], 1)
        self.assertFalse(filas[0].get('veredicto') or filas[0].get('sin_cuota'))
        self.assertEqual((filas[-1]['arnes'], filas[-1]['veredicto']), ('agy', 'APROBADO'))
        self.assertFalse((self.root / motor.intervencion.PREGUNTAS).exists())

    def test_diagnostico_real_sin_punto_respeta_estricto(self):
        """No reintenta sesión ni usa reservas bajo el perfil estricto."""
        tareas = self.root / 'docs/plan/bugs'
        tareas.mkdir(parents=True)
        (tareas / 'B-ADV-0040.md').write_text(
            '---\nid: B-ADV-0040\nstatus: in_progress\n'
            'perfil: {hades: {harness: claude, model: principal}, estricto: true}\n---\n',
            encoding='utf-8')
        self.enterContext(patch.dict(motor.os.environ, {'ORQUESTAR_ID': 'B-ADV-0040'}))
        self.lanzar.return_value = (1, {}, ERROR_REAL)
        with patch.object(motor, 'buscar_sesion_agente', return_value='anterior'):
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
        self.lanzar.assert_called_once()
        fila = motor.leer_metricas(self.root)[-1]
        self.assertTrue(fila['acceso_denegado'])
        self.assertEqual(fila['diagnostico'], ERROR_REAL)
        self.assertFalse(fila.get('veredicto') or fila.get('sin_cuota'))
        self.assertTrue(any('revisión pendiente' in str(c) and 'estricto' in str(c)
                            for c in self.consola.call_args_list))
        self.assertFalse((self.root / motor.intervencion.PREGUNTAS).exists())

    def test_diagnostico_de_otro_proveedor_no_activa_reservas(self):
        """La frase no autoriza conmutación fuera de Claude."""
        self.cfg['harness'] = 'agy'
        self.lanzar.return_value = (1, {}, ERROR_REAL)
        self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
        self.lanzar.assert_called_once()
        fila = motor.leer_metricas(self.root)[-1]
        self.assertEqual(fila['diagnostico'], ERROR_REAL)
        self.assertFalse(fila.get('acceso_denegado') or fila.get('sin_cuota') or fila.get('veredicto'))

    def test_reserva_recibe_dictamen_real_y_no_inventa_cuota(self):
        """Conserva el rechazo auténtico y su destino tras el fallo técnico."""
        dictamen = 'Veredicto: RECHAZADO; hallazgo alto RT-REAL-01; para: especificador; destino: resolver'
        self.lanzar.side_effect = LANZAR_REAL
        with (patch.object(motor, 'tope_de_rechazos', return_value=''),
              patch.object(motor, '_ejecutar_captura_json', side_effect=[
                  (1, ERROR, '', False, False),
                  (0, json.dumps({'status': 'SUCCESS', 'response': dictamen}), '', False, False)])):
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
        self.assertEqual([c.args[2] for c in self.lanzar.call_args_list], ['claude', 'agy'])
        filas = motor.leer_metricas(self.root)
        self.assertTrue(filas[0]['acceso_denegado'])
        self.assertIn(ERROR, filas[0]['diagnostico'])
        self.assertEqual(filas[0]['modelo'], 'principal')
        self.assertNotIn('veredicto', filas[0])
        self.assertNotIn('cuota_espera_s', filas[0])
        self.assertFalse(filas[0].get('sin_cuota'))
        self.assertEqual((filas[-1]['arnes'], filas[-1]['veredicto']), ('agy', 'RECHAZADO'))
        tarea = self.root / 'docs/plan/bugs/B-ADV-0040.md'
        tarea.parent.mkdir(parents=True)
        tarea.write_text('---\nid: B-ADV-0040\nversion: v1.1.2\nstatus: in_progress\n---\n', encoding='utf-8')
        observado = next(c.args[0] for c in self.consola.call_args_list if 'RT-REAL-01' in str(c.args))
        self.assertEqual(observado, dictamen)
        destino = re.search(r'para: (\w+)', observado)[1]
        motor.enrutar_hallazgo(self.root, 'B-ADV-0040', destino, contexto=observado)
        self.assertEqual(motor.frontmatter(tarea)['status'], 'blocked')
        self.assertEqual(motor.frontmatter(tarea)['pendiente_de'], 'especificador')
        self.assertIn(dictamen, tarea.read_text(encoding='utf-8'))
        self.assertFalse((self.root / motor.intervencion.PREGUNTAS).exists())

    def test_primera_reserva_aprueba_y_registra_revisor(self):
        """El dictamen aprobado llega del primer proveedor autorizado."""
        self.lanzar.side_effect = [(1, {}, ERROR), (0, {}, 'Veredicto: APROBADO')]
        self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
        self.assertEqual([c.args[2] for c in self.lanzar.call_args_list], ['claude', 'agy'])
        self.assertEqual(motor.leer_metricas(self.root)[-1]['arnes'], 'agy')
        self.assertEqual(motor.leer_metricas(self.root)[-1]['veredicto'], 'APROBADO')
        self.assertFalse((self.root / motor.intervencion.PREGUNTAS).exists())

    def test_cuota_vigente_omite_agy_y_usa_codex(self):
        """La reserva agotada no recibe un lanzamiento ni una sesión ajena."""
        motor.registrar(self.root, {'tipo': 'agente', 'fecha': '2026-11-11T09:59:00Z',
                                  'arnes': 'agy', 'modelo_cuota': 'intermedia', 'cuota_espera_s': 3600})
        self.lanzar.side_effect = [(1, {}, ERROR), (0, {}, 'Veredicto: APROBADO')]
        self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
        self.assertEqual([c.args[2] for c in self.lanzar.call_args_list], ['claude', 'codex'])
        self.assertNotIn('resume', self.lanzar.call_args.args[0])
        self.assertEqual((motor.leer_metricas(self.root)[-1]['arnes'],
                          motor.leer_metricas(self.root)[-1]['veredicto']), ('codex', 'APROBADO'))

    def test_sesion_denegada_no_se_reintenta_y_estricto_no_cede(self):
        """Un perfil explícito estricto conserva el proveedor fijado."""
        tareas = self.root / 'docs/plan/bugs'
        tareas.mkdir(parents=True)
        (tareas / 'B-ADV-0040.md').write_text(
            '---\nid: B-ADV-0040\nstatus: in_progress\n'
            'perfil: {hades: {harness: claude, model: principal}, estricto: true}\n---\n',
            encoding='utf-8')
        self.enterContext(patch.dict(motor.os.environ, {'ORQUESTAR_ID': 'B-ADV-0040'}))
        self.lanzar.return_value = (1, {}, ERROR)
        with patch.object(motor, 'buscar_sesion_agente', return_value='anterior'):
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
        self.lanzar.assert_called_once()
        self.assertTrue(any('revisión pendiente' in str(c) and 'estricto' in str(c)
                            for c in self.consola.call_args_list))
        self.assertFalse(any(f.get('veredicto') for f in motor.leer_metricas(self.root)))
        self.assertTrue(motor.perfil_fijado_de(self.root, 'B-ADV-0040', 'hades')[1])

    def test_fallo_repetido_conserva_trabajo_preguntas_y_revision_pendiente(self):
        """Ningún diagnóstico con la palabra veredicto se convierte en revisión."""
        self.cfg['reserva'] = [{'model': 'otra'}]
        trabajo = self.root / 'trabajo.py'
        trabajo.write_text('trabajo sin completar', encoding='utf-8')
        preguntas = self.root / motor.intervencion.PREGUNTAS
        preguntas.write_text('[]', encoding='utf-8')
        self.lanzar.return_value = (1, {}, ERROR + ' Veredicto: APROBADO')
        for _ in range(2):
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
        self.assertEqual(self.lanzar.call_count, 4)
        self.assertEqual(preguntas.read_text(), '[]')
        self.assertEqual(trabajo.read_text(), 'trabajo sin completar')
        self.assertFalse(any(f.get('veredicto') for f in motor.leer_metricas(self.root)))
        self.assertTrue(any('revisión pendiente' in str(c) for c in self.consola.call_args_list))
        self.assertFalse((self.root / 'docs/review/code_reviews/B-ADV-0040-code-review.md').exists())

    def test_cuota_y_acceso_conservan_espera_real(self):
        """La reserva denegada no borra ni suplanta una cuota ya observada."""
        self.cfg['reserva'] = [{'harness': 'claude', 'model': 'otra'}]
        self.lanzar.side_effect = [(1, {}, 'usage limit resets in 60 minutes'), (1, {}, ERROR)]
        self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
        filas = motor.leer_metricas(self.root)
        self.assertTrue(filas[-1].get('sin_cuota'))
        self.assertEqual(filas[-1]['espera_s'], filas[0]['cuota_espera_s'])
        self.assertTrue(any(f.get('acceso_denegado') and f['modelo'] == 'otra' for f in filas))

    def test_bucle_no_lanza_paso_si_restauracion_espera_trabajo_ajeno(self):
        """La señal de espera impide ejecutar y notificar una reanudación ficticia."""
        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None,
            estado=False, max_pasos=1, reintentos=2, espera_max=0, cmd=None)
        with (patch.object(motor, 'iniciar_gateway'),
              patch.object(motor, 'recargar_version', return_value=False),
              patch.object(motor, 'ingerir', return_value=[]),
              patch.object(motor, 'incorporar_respuestas', return_value=[]),
              patch.object(motor, 'estado', return_value=('PASO', 'bug-fix', 'B-ADV-0040', '')),
              patch.object(motor, 'comprobar_promocion', return_value=(False, '')),
              patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'firma', side_effect=['antes', 'despues']),
              patch.object(motor.intervencion, 'restaurar', return_value=False),
              patch.object(motor.intervencion, 'notificar_reanudacion') as notificar,
              patch.object(motor, 'ejecutar', return_value=(0, {}, 'ok')) as ejecutar):
            self.assertEqual(motor.bucle(args, self.root), 2)
        ejecutar.assert_not_called()
        notificar.assert_not_called()

    def test_autenticacion_y_red_genericas_no_ceden(self):
        """El clasificador no amplía la recuperación a errores ajenos."""
        for error in ('authentication failed', 'network connection failed', 'access denied'):
            with self.subTest(error=error):
                self.lanzar.reset_mock()
                self.lanzar.return_value = (1, {}, error)
                self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
                self.lanzar.assert_called_once()
                self.assertIn(error, motor.leer_metricas(self.root)[-1].get('diagnostico', ''))
                fila = motor.leer_metricas(self.root)[-1]
                self.assertEqual(fila['codigo'], 1)
                self.assertFalse(fila.get('veredicto') or fila.get('sin_cuota') or fila.get('arnes_ausente'))
        self.assertFalse(any(f.get('acceso_denegado') for f in motor.leer_metricas(self.root)))


class RecuperacionAccesoTests(unittest.TestCase):
    """Copias estructurales de Q-ADV-0001/0002 con Git y registro durables."""

    def git(self, *args):
        """Opera exclusivamente en el repositorio temporal."""
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True,
                              text=True, encoding='utf-8').stdout.strip()

    def test_dos_respuestas_con_wip_y_trabajo_ajeno_retoman_revision(self):
        """Incorpora una sola vez y revisa con la reserva sin nuevas preguntas."""
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        entorno = {k: v for k, v in motor.os.environ.items()
                   if not k.startswith(('ORQUESTAR_', 'TELEGRAM_'))}
        with (patch.dict(motor.os.environ, entorno, clear=True),
              patch.object(motor, 'avisar'), patch.object(motor, 'telegram', return_value=None),
              patch.object(motor, 'pid_vivo', return_value=123), patch('builtins.print')):
            for args in (('init', '-q'), ('config', 'user.email', 'test@test'),
                         ('config', 'user.name', 'Test'), ('config', 'core.autocrlf', 'false'), ('checkout', '-qb', 'hotfix/v1.1.2')):
                self.git(*args)
            (self.root / '.gitignore').write_text('orquestar_*\n', encoding='utf-8')
            (self.root / 'task_config.yaml').write_text('project:\n  prefix: ADV\n', encoding='utf-8')
            tareas = self.root / 'docs/plan/bugs'
            tareas.mkdir(parents=True)
            ids = ('B-ADV-0032', 'B-ADV-0033')
            for iid in ids:
                (tareas / f'{iid}.md').write_text(f'---\nid: {iid}\nversion: v1.1.2\n'
                    'status: in_progress\ndepende_de: []\n---\nHistorial previo.\n', encoding='utf-8')
                (self.root / f'{iid}.py').write_bytes(b'base\n')
            (self.root / 'ajeno.txt').write_bytes(b'base\n')
            self.git('add', '.')
            self.git('commit', '-qm', 'base')
            for n, iid in enumerate(ids, 1):
                (self.root / f'{iid}.py').write_bytes(b'WIP conservado\n')
                q = motor.solicitar_intervencion(self.root, iid, 'Restaurar acceso o usar reserva', contexto=ERROR)
                self.assertEqual(q['id'], f'Q-ADV-{n:04d}')
                respuesta = motor.intervencion.recibir(self.root, motor, 'local:test',
                    q['id'] + ' Usar los perfiles de reserva ya configurados')
                self.assertIn('recibida', respuesta)
            ajeno = self.root / 'ajeno.txt'
            ajeno.write_text('cambio ajeno\n', encoding='utf-8')
            self.assertEqual(motor.incorporar_respuestas(self.root), [])
            self.assertTrue(all(q['cola'] for q in motor.listar_preguntas(self.root)))
            self.git('add', 'ajeno.txt')
            self.git('commit', '-qm', 'guardar trabajo independiente')
            self.assertEqual(len(motor.incorporar_respuestas(self.root)), 2)
            ajeno.write_text('otro cambio ajeno\n', encoding='utf-8')
            self.git('add', 'ajeno.txt')
            self.git('commit', '-qm', 'guardar segundo cambio independiente')
            cfg = {'hades': {'harness': 'claude', 'model': 'principal',
                            'reserva': [{'harness': 'codex', 'model': 'reserva'}]}}
            for iid in ids:
                try:
                    motor.intervencion.restaurar(self.root, motor, iid)
                except subprocess.CalledProcessError as error:
                    self.fail(f'Restauración WIP real con Git: {error.stderr}')
                self.assertEqual((self.root / f'{iid}.py').read_text(), 'WIP conservado\n')
                with (patch.object(motor, 'config', return_value=cfg),
                      patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe),
                      patch.object(motor, 'buscar_sesion_agente', return_value=None),
                      patch.object(motor, 'construir_prompt_agente', return_value='revisa'),
                      patch.object(motor, 'lanzar', side_effect=[(1, {}, ERROR),
                          (0, {}, 'Veredicto: APROBADO')]) as lanzar,
                      patch.dict(motor.os.environ, {'ORQUESTAR_ID': iid, 'ORQUESTAR_PASO': 'bug-fix'})):
                    self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
                    self.assertEqual([c.args[2] for c in lanzar.call_args_list], ['claude', 'codex'])
                tarea = tareas / f'{iid}.md'
                self.assertEqual(motor.frontmatter(tarea)['status'], 'planned')
                self.assertIn('Historial previo.', tarea.read_text(encoding='utf-8'))
                self.assertIn('Usar los perfiles', tarea.read_text(encoding='utf-8'))
                self.git('add', '.')
                self.git('commit', '-qm', 'conservar trabajo retomado')
            self.assertEqual(ajeno.read_text(), 'otro cambio ajeno\n')
            preguntas = motor.listar_preguntas(self.root)
            self.assertEqual(len(preguntas), 2)
            for q in preguntas:
                self.assertEqual(q['estado'], 'incorporada')
                self.assertTrue(q['wip_restaurado'])
                self.assertEqual(len(q['recibidas']), 1)
                self.assertEqual(self.git('show', q['wip_rama'] + ':' + q['tarea_id'] + '.py'), 'WIP conservado')
            self.assertEqual(motor.incorporar_respuestas(self.root), [])


    def test_instantaneas_pendiente_e_incorporada_esperan_arbol_limpio(self):
        """Ejercita cada fila H2 con registro durable, Git real y revisión simulada."""
        for numero, iid, incorporada in ((1, 'B-ADV-0032', False), (2, 'B-ADV-0033', True)):
            with self.subTest(iid=iid):
                self.comprobar_instantanea(numero, iid, incorporada)

    def test_indice_ajeno_cancelado_en_worktree_tambien_bloquea(self):
        """Un índice ajeno no desaparece porque el archivo vuelva a los bytes de HEAD."""
        self.comprobar_instantanea(2, 'B-ADV-0033', True, indice_cancelado=True)

    def comprobar_instantanea(self, numero, iid, incorporada, indice_cancelado=False):
        """Genera datos sintéticos independientes sin tocar las preguntas del proyecto."""
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        entorno = {k: v for k, v in motor.os.environ.items()
                   if not k.startswith(('ORQUESTAR_', 'TELEGRAM_'))}
        with (patch.dict(motor.os.environ, entorno, clear=True),
              patch.object(motor, 'avisar') as aviso,
              patch.object(motor, 'telegram', return_value=None),
              patch.object(motor, 'pid_vivo', return_value=123), patch('builtins.print')):
            for args in (('init', '-q'), ('config', 'user.email', 'test@test'),
                         ('config', 'user.name', 'Test'), ('config', 'core.autocrlf', 'false'),
                         ('checkout', '-qb', 'hotfix/v1.1.2')):
                self.git(*args)
            (self.root / '.gitignore').write_text('orquestar_*\n', encoding='utf-8')
            (self.root / 'task_config.yaml').write_text('project:\n  prefix: ADV\n', encoding='utf-8')
            tarea = self.root / f'docs/plan/bugs/{iid}.md'
            tarea.parent.mkdir(parents=True)
            tarea.write_text(f'---\nid: {iid}\nversion: v1.1.2\nstatus: in_progress\n'
                             'depende_de: []\n---\nRT-PREVIO\n' + ERROR + '\n', encoding='utf-8')
            ajeno = self.root / 'ajeno.txt'
            ajeno.write_bytes(b'base\n')
            self.git('add', '.')
            self.git('commit', '-qm', 'base')
            wip = self.root / 'borrador.txt'
            esperado = f'WIP-{iid}\n'.encode('utf-8')
            wip.write_bytes(esperado)
            q = motor.solicitar_intervencion(self.root, iid, 'Acceso de Hades', contexto=ERROR, paso='bug-fix')
            registros = motor.listar_preguntas(self.root)
            registros[0]['id'] = f'Q-ADV-{numero:04d}'
            motor.intervencion.guardar(self.root / motor.intervencion.PREGUNTAS, registros)
            respuesta = 'Usar la reserva Codex ya configurada; pruebas con mocks'
            motor.intervencion.recibir(self.root, motor, 'local:test', registros[0]['id'] + ' ' + respuesta)
            if incorporada:
                self.assertEqual(len(motor.incorporar_respuestas(self.root)), 1)
            w0 = self.git('rev-parse', q['wip_rama'])
            self.assertEqual(self.git('show', w0 + ':borrador.txt'), esperado.decode().strip())
            self.assertFalse(motor.listar_preguntas(self.root)[0]['wip_restaurado'])
            ajeno.write_bytes(b'AJENO\n')
            if indice_cancelado:
                self.git('add', 'ajeno.txt')
                ajeno.write_bytes(b'base\n')
                self.assertFalse(self.git('diff', 'HEAD', '--name-only'))
            a0 = ajeno.read_bytes()
            def git_bytes(*args):
                return subprocess.check_output(['git', *args], cwd=self.root)
            indice = git_bytes('diff', '--cached', '--binary')
            head = self.git('rev-parse', 'HEAD')
            estado_a0 = git_bytes('status', '--porcelain', '--', 'ajeno.txt')
            diff_a0 = git_bytes('diff', '--binary', '--', 'ajeno.txt')
            stashes = git_bytes('stash', 'list')
            cfg = {'hades': {'harness': 'claude', 'model': 'principal',
                            'reserva': [{'harness': 'codex', 'model': 'reserva'}]}}
            aviso.reset_mock()
            proceso_codex = MagicMock()
            proceso_codex.__enter__.return_value = proceso_codex
            proceso_codex.stdin = io.StringIO()
            proceso_codex.stdout = io.StringIO(json.dumps({'type': 'item.completed', 'item': {
                'type': 'agent_message', 'text': 'Veredicto: APROBADO; sin hallazgos'}}) + '\n')
            proceso_codex.returncode = 0
            with (patch('builtins.print') as consola,
                  patch.object(motor, 'config', return_value=cfg),
                  patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe),
                  patch.object(motor, 'buscar_sesion_agente', return_value=None),
                  patch.object(motor, 'construir_prompt_agente', return_value='review-test'),
                  patch.object(motor, '_ejecutar_captura_json', return_value=(1, ERROR, '', False, False)),
                  patch.object(motor, 'lanzar', wraps=LANZAR_REAL) as lanzar,
                  patch.dict(motor.os.environ, {'ORQUESTAR_ID': iid, 'ORQUESTAR_PASO': 'bug-fix'})):
                self.assertEqual(motor.incorporar_respuestas(self.root), [])
                motor.intervencion.restaurar(self.root, motor, iid)
                lanzar.assert_not_called()
                self.assertFalse(wip.exists())
                self.assertEqual(ajeno.read_bytes(), a0)
                self.assertEqual(self.git('rev-parse', 'HEAD'), head)
                self.assertEqual(git_bytes('diff', '--cached', '--binary'), indice)
                self.assertEqual(git_bytes('status', '--porcelain', '--', 'ajeno.txt'), estado_a0)
                self.assertTrue(diff_a0)
                if indice_cancelado:
                    self.assertTrue(indice)
                self.assertEqual(git_bytes('diff', '--binary', '--', 'ajeno.txt'), diff_a0)
                self.assertEqual(git_bytes('stash', 'list'), stashes)
                self.assertFalse(any('reanudada' in str(c) for c in aviso.call_args_list))
                if indice_cancelado:
                    self.git('commit', '-qm', 'guardar indice del propietario')
                self.git('add', 'ajeno.txt')
                self.git('commit', '-qm', 'guardar cambio ajeno')
                self.assertEqual(len(motor.incorporar_respuestas(self.root)), 0 if incorporada else 1)
                self.assertEqual(motor.frontmatter(tarea)['status'], 'planned')
                self.assertNotIn('pendiente_de', motor.frontmatter(tarea))
                motor.intervencion.restaurar(self.root, motor, iid)
                self.assertEqual(wip.read_bytes(), esperado)
                self.assertTrue(motor.listar_preguntas(self.root)[0]['wip_restaurado'])
                self.assertEqual(ajeno.read_bytes(), a0)
                self.assertNotIn('ajeno.txt', self.git('diff', 'HEAD', '--name-only'))
                informe = self.root / f'docs/review/test_reviews/{iid}-test-review.md'
                informe.parent.mkdir(parents=True)
                informe.write_text('RT-PREVIO\nRevisión pendiente\n', encoding='utf-8')
                with patch.object(motor.subprocess, 'Popen', side_effect=lambda cmd, **kwargs:
                        proceso_codex if cmd[0] == 'codex' else POPEN_REAL(cmd, **kwargs)):
                    self.assertEqual(motor.agente(self.root, 'hades', 'review-test'), 0)
                observado = next(c.args[0] for c in consola.call_args_list
                                 if c.args and str(c.args[0]).startswith('Veredicto:'))
                self.assertEqual(observado, 'Veredicto: APROBADO; sin hallazgos')
                informe.write_text(informe.read_text(encoding='utf-8') + observado + '\n', encoding='utf-8')
                self.assertIn('RT-PREVIO', informe.read_text(encoding='utf-8'))
                self.assertTrue(informe.read_text(encoding='utf-8').rstrip().endswith(observado))
                self.assertEqual(re.search(r'Veredicto: (\w+)', observado)[1], 'APROBADO')
                self.assertEqual([c.args[2] for c in lanzar.call_args_list], ['claude', 'codex'])
                filas = motor.leer_metricas(self.root)
                self.assertTrue(filas[0]['acceso_denegado'])
                self.assertEqual((filas[-1]['arnes'], filas[-1]['veredicto']), ('codex', 'APROBADO'))
                self.assertFalse(any(f.get('sin_cuota') or f.get('cuota_espera_s') for f in filas))
                self.assertEqual(motor.frontmatter(tarea)['status'], 'planned')
                self.assertIn('RT-PREVIO', tarea.read_text(encoding='utf-8'))
                self.assertIn(ERROR, tarea.read_text(encoding='utf-8'))
                self.assertEqual(tarea.read_text(encoding='utf-8').count(respuesta), 1)
                self.assertEqual(motor.incorporar_respuestas(self.root), [])
                wip.write_bytes(b'continuacion del paso\n')
                motor.intervencion.restaurar(self.root, motor, iid)
                self.assertEqual(wip.read_bytes(), b'continuacion del paso\n')
                preguntas = motor.listar_preguntas(self.root)
                self.assertEqual(len(preguntas), 1)
                self.assertEqual(preguntas[0]['estado'], 'incorporada')
                self.assertEqual(len(preguntas[0]['recibidas']), 1)
                self.assertEqual(preguntas[0]['respuesta'], respuesta)
                self.assertEqual(self.git('rev-parse', q['wip_rama']), w0)


if __name__ == '__main__':
    unittest.main()
