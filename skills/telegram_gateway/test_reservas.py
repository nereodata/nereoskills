"""Reservas conversacionales sin red, modelos ni credenciales reales."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('gateway_reservas', Path(__file__).with_name('gateway.py'))
gateway = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gateway)
motor = gateway.motor


class ReservasTests(unittest.TestCase):
    """Verifica lanzamientos, respuestas, sesiones y evidencia común de cuota."""

    def setUp(self):
        """Aísla disco, reloj, avisos y procesos del proyecto real."""
        self.tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.tmp)
        self.cfg = {'atenea': {'harness': 'codex', 'model': 'm1', 'effort': 'high',
                              'reserva': [{'harness': 'agy', 'model': 'm2'},
                                          {'harness': 'claude', 'model': 'm3'}]}}
        self.enterContext(patch.object(motor, 'config', side_effect=lambda r: self.cfg))
        self.enterContext(patch.object(motor, 'ahora', return_value='2026-10-26T12:00:00+00:00'))
        self.enterContext(patch.object(motor, 'excluir'))
        self.enterContext(patch.object(motor, 'avisar'))
        self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda e: e))
        self.launch = self.enterContext(patch.object(motor, 'lanzar'))
        self.launch.return_value = (0, {'sesion': 'nueva'}, 'respuesta')

    def agotar(self, model='m1', harness='codex'):
        """Persiste un agotamiento vigente con el esquema del motor."""
        motor.registrar(self.root, {'tipo': 'gateway', 'fecha': motor.ahora(), 'arnes': harness,
                                   'modelo_cuota': model, 'cuota_espera_s': 1800})

    def test_cuota_cruda_arranque_reserva_y_metricas(self):
        """La cuota en stderr no se pierde al extraer un result vacío."""
        gateway.guardar_sesion(self.root, '123', 'codex', 'anterior')
        self.launch.side_effect = [(1, {'modelos': {'m1': {'entrada': 10}}},
                                    '{"result":""}\nusage limit reached'),
                                   OSError('no arranca'), (0, {'sesion': 's3'}, 'respuesta')]
        texto = gateway.conversar(self.root, '123', 'hola')
        self.assertIn('claude/m3', texto)
        self.assertIn('reserva', texto)
        self.assertEqual([c.args[2] for c in self.launch.call_args_list], ['codex', 'agy', 'claude'])
        for llamada, modelo in zip(self.launch.call_args_list, ('m1', 'm2', 'm3')):
            self.assertIn(modelo, llamada.args[0])
        self.assertIn('model_reasoning_effort="high"', self.launch.call_args_list[0].args[0])
        self.assertIn('high', self.launch.call_args_list[1].args[0])
        self.assertIn('high', self.launch.call_args_list[2].args[0])
        self.assertTrue(all('anterior' not in str(c.args[0]) for c in self.launch.call_args_list[1:]))
        self.assertEqual(gateway.obtener_sesion(self.root, '123', 'claude'), 's3')
        filas = motor.leer_metricas(self.root)
        cuota = next(f for f in filas if f.get('modelo_cuota') == 'm1')
        self.assertEqual(cuota['cuota_espera_s'], 1800)
        self.assertEqual(cuota['modelos']['m1']['entrada'], 10)
        recuperacion = motor.fecha_estado('2026-10-26T12:30:00Z')
        for instante, vigente in [('2026-10-26T12:15:00Z', True),
                                   ('2026-10-26T12:30:00Z', False)]:
            with patch.object(motor, 'ahora', return_value=instante):
                cuotas = motor.consumo_cuotas(self.root, motor.fecha_estado(instante))[1]
                self.assertEqual(cuotas.get(('codex', 'm1')), recuperacion if vigente else None)
                self.assertNotIn(('agy', 'm2'), cuotas)
                informe = gateway.responder(self.root, '123', '/agentes', {'123'})
                self.assertEqual('100.0%' in informe, vigente)
                if vigente:
                    self.assertIn(recuperacion.astimezone().strftime('%H:%M'), informe)
        self.assertEqual(len([f for f in filas if f.get('cuota_espera_s') is not None]), 1)

    def test_salta_cuota_y_vuelve_al_titular(self):
        """Cada mensaje reconsidera prioridad y mantiene sesiones por arnés."""
        gateway.guardar_sesion(self.root, '12345', 'codex', 'codex-s1')
        gateway.guardar_sesion(self.root, '12345', 'agy', 'agy-s1')
        self.agotar()
        self.launch.side_effect = [(0, {'sesion': 'agy-s2'}, 'respuesta'),
                                   (0, {'sesion': 'agy-s3'}, 'respuesta'),
                                   (0, {'sesion': 'codex-s2'}, 'respuesta')]
        self.assertIn('reserva', gateway.conversar(self.root, '12345', 'hola'))
        self.assertEqual(self.launch.call_count, 1)
        self.assertEqual(self.launch.call_args.args[2], 'agy')
        self.assertIn('agy-s1', self.launch.call_args.args[0])
        self.assertNotIn('codex-s1', self.launch.call_args.args[0])
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'agy'), 'agy-s2')
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'codex'), 'codex-s1')
        with patch.object(motor, 'ahora', return_value='2026-10-26T12:01:00+00:00'):
            gateway.conversar(self.root, '12345', 'otra')
        self.assertEqual(self.launch.call_count, 2)
        self.assertEqual(self.launch.call_args.args[2], 'agy')
        self.assertIn('agy-s2', self.launch.call_args.args[0])
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'agy'), 'agy-s3')
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'codex'), 'codex-s1')
        with patch.object(motor, 'ahora', return_value='2026-10-26T12:31:00+00:00'):
            respuesta = gateway.conversar(self.root, '12345', 'otra')
        self.assertEqual(self.launch.call_count, 3)
        self.assertEqual(self.launch.call_args.args[2], 'codex')
        self.assertIn('codex/m1', respuesta)
        self.assertNotIn('reserva', respuesta)
        self.assertIn('codex-s1', self.launch.call_args.args[0])
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'agy'), 'agy-s3')

    def test_aislamiento_otro_usuario(self):
        """Las reservas y el retorno no reciben sesiones de otro usuario."""
        gateway.guardar_sesion(self.root, '12345', 'codex', 'codex-s1')
        gateway.guardar_sesion(self.root, '12345', 'agy', 'agy-s3')
        self.agotar()
        self.launch.side_effect = [(0, {'sesion': 'agy-u2'}, 'respuesta'),
                                   (0, {'sesion': 'codex-u2'}, 'respuesta')]
        with patch.object(motor, 'ahora', return_value='2026-10-26T12:10:00+00:00'):
            gateway.conversar(self.root, '67890', 'hola')
        self.assertEqual(self.launch.call_count, 1)
        self.assertEqual(self.launch.call_args.args[2], 'agy')
        self.assertEqual(gateway.obtener_sesion(self.root, '67890', 'agy'), 'agy-u2')
        with patch.object(motor, 'ahora', return_value='2026-10-26T12:31:00+00:00'):
            gateway.conversar(self.root, '67890', 'otra')
        self.assertEqual(self.launch.call_count, 2)
        self.assertEqual(self.launch.call_args.args[2], 'codex')
        for llamada in self.launch.call_args_list:
            for sesion in ('codex-s1', 'agy-s3', 'agy-u2'):
                self.assertNotIn(sesion, llamada.args[0])
            self.assertNotIn('--resume', llamada.args[0])
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'agy'), 'agy-s3')
        self.assertEqual(gateway.obtener_sesion(self.root, '12345', 'codex'), 'codex-s1')

    def test_todos_indisponibles_diagnostico_al_usuario(self):
        """El usuario ve motivos por perfil, sin lanzar el agotado."""
        self.agotar()
        self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda e: None if e == 'agy' else e))
        self.launch.side_effect = PermissionError('denegado')
        texto = gateway.responder(self.root, '123', 'hola', {'123'})
        for fragmento in ('codex/m1', 'cuota', 'agy/m2', 'claude/m3', 'arranque'):
            self.assertIn(fragmento, texto)
        self.assertIn('12:30:00', texto)
        self.assertEqual(self.launch.call_count, 1)
        self.assertIn('Adevv v', texto)
        self.assertEqual(self.launch.call_args.args[2], 'claude')
        lineas = texto.splitlines()
        self.assertTrue(any('codex/m1' in l and 'cuota' in l for l in lineas))
        self.assertTrue(any('agy/m2' in l and ('ausente' in l or 'encuentra' in l) for l in lineas))
        self.assertTrue(any('claude/m3' in l and 'arranque' in l for l in lineas))

    def test_unico_agotado_no_se_lanza(self):
        """Sin reservas tampoco se ejecuta un perfil con cuota vigente."""
        self.cfg['atenea'].pop('reserva')
        self.agotar()
        texto = gateway.responder(self.root, '123', 'hola', {'123'})
        self.assertIn('codex/m1', texto)
        self.assertIn('cuota', texto)
        self.assertIn('12:30:00', texto)
        self.launch.assert_not_called()

    def test_herencia_objeto_lista_y_reserva_propia(self):
        """Reservas heredadas o propias mantienen orden y esfuerzo."""
        for reserva in ({'model': 'm4'}, [{'model': 'm4'}]):
            with self.subTest(reserva=reserva):
                self.cfg['telegram'] = {'reserva': reserva}
                self.launch.side_effect = [(1, {}, 'usage limit reached'), (0, {}, 'respuesta')]
                texto = gateway.conversar(self.root, '123', 'hola')
                self.assertIn('codex/m4', texto)
                cmd = self.launch.call_args.args[0]
                self.assertIn('m4', cmd)
                self.assertIn('model_reasoning_effort="high"', cmd)
                (self.root / motor.METRICAS).unlink(missing_ok=True)
                self.launch.reset_mock()

    def test_error_ordinario_no_conmuta(self):
        """El fallo ordinario conserva reintento sin sesión y error."""
        gateway.guardar_sesion(self.root, '123', 'codex', 'previa')
        self.launch.return_value = (1, {}, 'fallo ordinario')
        with self.assertRaisesRegex(RuntimeError, 'fallo ordinario'):
            gateway.conversar(self.root, '123', 'hola')
        self.assertEqual(self.launch.call_count, 2)
        self.assertEqual([c.args[2] for c in self.launch.call_args_list], ['codex', 'codex'])
        self.assertIn('previa', self.launch.call_args_list[0].args[0])
        self.assertNotIn('previa', self.launch.call_args_list[1].args[0])
