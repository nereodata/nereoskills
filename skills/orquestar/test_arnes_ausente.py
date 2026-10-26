"""Regresiones de reservas ante arneses ausentes sin procesos ni red."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def cargar(nombre, ruta):
    """Carga exclusivamente el motor del árbol de trabajo."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


BASE = Path(__file__).resolve().parents[1]
gateway = cargar('gateway_ausente', BASE / 'telegram_gateway/gateway.py')
motor = gateway.motor


class ArnesAusenteTests(unittest.TestCase):
    """Verifica efectos observables de pasos, agentes y gateway."""

    def setUp(self):
        """Aísla configuración, disco, sesiones y notificaciones."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cfg = {'harness': 'claude', 'model': 'principal',
                    'reserva': [{'harness': 'codex', 'model': 'reserva'}]}
        self.enterContext(patch.dict(motor.os.environ, {}, clear=True))
        self.enterContext(patch.object(motor, 'config', side_effect=lambda root: {
            'hades': self.cfg, 'artemisa': self.cfg, 'atenea': self.cfg}))
        self.enterContext(patch.object(motor, 'excluir'))
        self.enterContext(patch.object(motor, 'ahora', return_value='2026-10-26T17:00:00+00:00'))
        self.avisar_real = motor.avisar
        self.aviso = self.enterContext(patch.object(motor, 'avisar'))
        self.consola = self.enterContext(patch('builtins.print'))
        self.buscar = self.enterContext(patch.object(motor, 'buscar_ejecutable',
            side_effect=lambda exe: None if exe == 'claude' else exe))
        self.lanzar = self.enterContext(patch.object(motor, 'lanzar',
            return_value=(0, {'sesion': 'nueva'}, 'respuesta')))
        self.enterContext(patch.object(motor, 'construir_prompt_agente', return_value='peticion'))
        self.sesion_agente = self.enterContext(patch.object(motor, 'buscar_sesion_agente', side_effect=lambda *a: 'anterior' if a[-1] == 'claude' else None))
        self.enterContext(patch.object(gateway, 'construir_prompt', return_value='peticion'))
        self.enterContext(patch.object(gateway, 'obtener_sesion', side_effect=lambda *a: 'anterior' if a[-1] == 'claude' else None))
        self.guardar = self.enterContext(patch.object(gateway, 'guardar_sesion'))

    def bucle(self, progreso=True):
        """Ejecuta un único paso con los adaptadores reales y proceso simulado."""
        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None,
            estado=False, max_pasos=2, reintentos=2, espera_max=2, cmd=None, presupuesto=None)
        with (patch.object(motor, 'iniciar_gateway'),
              patch.object(motor, 'recargar_version', return_value=False),
              patch.object(motor, 'ingerir', return_value=[]),
              patch.object(motor, 'estado', side_effect=[('PASO', 'bug-fix', 'B-ADV-0005', ''), ('FIN', 'ok')]),
              patch.object(motor, 'firma', side_effect=['antes', 'despues' if progreso else 'antes']),
              patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'buscar_sesion_paso', return_value='anterior'),
              patch.object(motor, 'esperar', return_value=False) as esperar):
            codigo = motor.bucle(args, self.root)
        return codigo, esperar

    def comprobar_ausente(self, tipo):
        """Cada configuración omitida deja evidencia sin inventar consumo."""
        filas = motor.leer_metricas(self.root)
        ausente = [f for f in filas if f.get('arnes_ausente')]
        self.assertEqual(len(ausente), 1)
        self.assertEqual(ausente[0]['arnes'], 'claude')
        self.assertEqual(ausente[0]['tipo'], tipo)
        self.assertNotEqual(ausente[0]['codigo'], 0)
        self.assertEqual(ausente[0]['modelos'], {})
        self.assertEqual(ausente[0]['modelo'], 'principal')
        self.assertEqual(ausente[0]['posicion'], 0)
        for campo in ('entrada', 'cache_leida', 'cache_escrita', 'salida', 'razonamiento', 'coste_usd'):
            self.assertEqual(ausente[0][campo], 0)
        self.assertNotIn('cuota_espera_s', ausente[0])
        self.assertFalse(ausente[0].get('sin_cuota'))
        self.assertEqual(len([c for c in self.aviso.call_args_list
                              if c.args[1] == 'arnes' and '"claude"' in c.args[2]]), 1)
        self.assertTrue(any('claude' in str(c) and 'conmutando a reserva' in str(c)
                            for c in self.consola.call_args_list))

    def test_agente_salta_ausente_con_sesion_nueva(self):
        """Hades usa la reserva y no reanuda una sesión al cambiar de arnés."""
        self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
        self.lanzar.assert_called_once()
        self.assertEqual(self.lanzar.call_args.args[2], 'codex')
        self.assertNotIn('resume', self.lanzar.call_args.args[0])
        self.comprobar_ausente('agente')

    def test_paso_salta_ausente_sin_espera(self):
        """El paso continúa inmediatamente con la reserva de otro arnés."""
        codigo, esperar = self.bucle()
        self.assertEqual(codigo, 0)
        esperar.assert_not_called()
        self.lanzar.assert_called_once()
        self.assertEqual(self.lanzar.call_args.args[2], 'codex')
        self.assertNotIn('resume', self.lanzar.call_args.args[0])
        self.comprobar_ausente('paso')

    def test_gateway_salta_ausente_y_guarda_sesion_reserva(self):
        """La firma y persistencia pertenecen al arnés que sí respondió."""
        respuesta = gateway.conversar(self.root, '123', 'hola')
        self.assertIn('respuesta', respuesta)
        self.assertIn('codex/reserva', respuesta)
        self.guardar.assert_called_once_with(self.root, '123', 'codex', 'nueva')
        self.assertNotIn('resume', self.lanzar.call_args.args[0])
        self.comprobar_ausente('gateway')

    def test_todos_ausentes_fallo_claro_sin_cuota(self):
        """Ningún flujo aborta silenciosamente ni espera cuota inexistente."""
        self.buscar.side_effect = lambda exe: None
        for flujo in ('agente', 'paso', 'gateway'):
            with self.subTest(flujo=flujo):
                self.aviso.reset_mock()
                if flujo == 'agente':
                    self.assertNotEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
                elif flujo == 'paso':
                    codigo, esperar = self.bucle(progreso=False)
                    self.assertNotEqual(codigo, 0)
                    esperar.assert_not_called()
                else:
                    with self.assertRaisesRegex(RuntimeError, 'ning.n arn.s disponible'):
                        gateway.conversar(self.root, '123', 'hola')
                self.assertTrue(any(c.args[1] == 'error' and 'disponible' in c.args[2]
                                    for c in self.aviso.call_args_list))
        self.lanzar.assert_not_called()
        self.assertFalse(any(f.get('sin_cuota') for f in motor.leer_metricas(self.root)))

    def test_cadena_intermedia_ausente_en_tres_flujos(self):
        """Dos ausencias dejan dos evidencias y alcanzan la segunda reserva."""
        self.cfg.update(harness='codex', model='principal-a', reserva=[
            {'harness': 'claude', 'model': 'reserva-b'},
            {'harness': 'agy', 'model': 'reserva-c'}])
        self.buscar.side_effect = lambda exe: exe if exe == 'agy' else None
        for flujo in ('agente', 'paso', 'gateway'):
            with self.subTest(flujo=flujo):
                ruta = self.root / motor.METRICAS
                if ruta.exists():
                    ruta.unlink()
                self.aviso.reset_mock()
                self.consola.reset_mock()
                self.lanzar.reset_mock()
                if flujo == 'agente':
                    self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
                elif flujo == 'paso':
                    codigo, esperar = self.bucle()
                    self.assertEqual(codigo, 0)
                    esperar.assert_not_called()
                else:
                    self.assertIn('agy/reserva-c', gateway.conversar(self.root, '123', 'hola'))
                    self.guardar.assert_called_with(self.root, '123', 'agy', 'nueva')
                self.lanzar.assert_called_once()
                self.assertEqual(self.lanzar.call_args.args[2], 'agy')
                self.assertNotIn('--resume', self.lanzar.call_args.args[0])
                filas = [f for f in motor.leer_metricas(self.root) if f.get('arnes_ausente')]
                self.assertEqual([(f['tipo'], f['posicion'], f['arnes'], f['modelo']) for f in filas],
                    [(flujo, 0, 'codex', 'principal-a'), (flujo, 1, 'claude', 'reserva-b')])
                for fila in filas:
                    self.assertEqual(fila['modelos'], {})
                    for campo in ('entrada', 'cache_leida', 'cache_escrita', 'salida', 'razonamiento', 'coste_usd'):
                        self.assertEqual(fila[campo], 0)
                    self.assertFalse(fila.get('sin_cuota'))
                    self.assertNotIn('cuota_espera_s', fila)
                self.assertEqual(len([c for c in self.aviso.call_args_list if c.args[1] == 'arnes']), 2)
                for arnes in ('codex', 'claude'):
                    self.assertEqual(len([c for c in self.aviso.call_args_list
                                          if c.args[1] == 'arnes' and f'"{arnes}"' in c.args[2]]), 1)
                    self.assertTrue(any(arnes in str(c) and 'conmutando a reserva' in str(c)
                                        for c in self.consola.call_args_list))

    def test_cuota_se_conserva_si_ultima_reserva_ausente(self):
        """La recuperaci?n del principal sigue exactamente a las 18:00 UTC."""
        self.buscar.side_effect = lambda exe: None if exe == 'codex' else exe
        self.lanzar.return_value = (1, {}, 'out of credits')
        with patch.object(motor, 'espera_cuota', return_value=3600):
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
            codigo, esperar = self.bucle()
        self.assertNotEqual(codigo, 0)
        esperar.assert_called_once_with(self.root, 3600)
        filas = motor.leer_metricas(self.root)
        for tipo in ('agente', 'paso'):
            agotadas = [f for f in filas if f.get('tipo') == tipo and f.get('sin_cuota')]
            self.assertTrue(agotadas)
            self.assertTrue(all(f['arnes'] == 'claude' for f in agotadas))
            self.assertTrue(any(f.get('espera_s') == 3600 for f in agotadas))
        _, cuotas = motor.consumo_cuotas(self.root, motor.fecha_estado('2026-10-26T17:01:00Z'))
        self.assertEqual(cuotas[('claude', 'principal')].isoformat(), '2026-10-26T18:00:00+00:00')
        ausentes = [f for f in filas if f.get('arnes_ausente')]
        self.assertEqual([(f['tipo'], f['posicion'], f['arnes'], f['modelo']) for f in ausentes],
                         [('agente', 1, 'codex', 'reserva'), ('paso', 1, 'codex', 'reserva')])
        for fila in ausentes:
            self.assertEqual(fila['modelos'], {})
            for campo in ('entrada', 'cache_leida', 'cache_escrita', 'salida', 'razonamiento', 'coste_usd'):
                self.assertEqual(fila[campo], 0)
            self.assertFalse(fila.get('sin_cuota'))
            self.assertNotIn('cuota_espera_s', fila)
            self.assertNotIn('espera_s', fila)

    def test_errores_operacionales_no_prueban_reservas(self):
        """Autenticación fallida no se confunde con ejecutable ausente."""
        self.buscar.side_effect = lambda exe: exe
        self.lanzar.return_value = (1, {}, 'authentication failed')
        for flujo in ('agente', 'paso', 'gateway'):
            with self.subTest(flujo=flujo):
                self.lanzar.reset_mock()
                if flujo == 'agente':
                    self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
                elif flujo == 'paso':
                    codigo, esperar = self.bucle(progreso=False)
                    self.assertNotEqual(codigo, 0)
                    esperar.assert_not_called()
                else:
                    with self.assertRaisesRegex(RuntimeError, 'authentication failed'):
                        gateway.conversar(self.root, '123', 'hola')
                self.assertEqual(self.lanzar.call_count, 2)
                self.assertTrue(all(c.args[2] == 'claude' for c in self.lanzar.call_args_list))
        self.assertFalse(any(f.get('arnes_ausente') for f in motor.leer_metricas(self.root)))

    def test_evento_filtrable_y_activo_por_defecto(self):
        """El nuevo evento usa el mismo filtro que los avisos existentes."""
        self.assertIn('arnes', motor.EVENTOS)
        with (patch.object(motor, 'telegram', return_value=('token', ['123'], {'error'})),
              patch.object(motor, 'enviar') as enviar):
            self.assertFalse(self.avisar_real(self.root, 'arnes', 'ausente'))
            enviar.assert_not_called()
        with (patch.object(motor, 'telegram', return_value=('token', ['123'], {'arnes'})),
              patch.object(motor, 'enviar', return_value=True) as enviar):
            self.assertTrue(self.avisar_real(self.root, 'arnes', 'ausente'))
            enviar.assert_called_once()


if __name__ == '__main__':
    unittest.main()
