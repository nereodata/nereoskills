"""Regresiones de selección por cuota vigente y llamadas efectivas de Hades."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tests import aislamiento_telegram


def cargar(nombre):
    """Carga los motores del árbol de trabajo sin usar la versión instalada."""
    spec = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name(nombre + '.py'))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


motor = cargar('orquestar')
metricas = cargar('metricas')


class CuotaVigenteTests(unittest.TestCase):
    """Ejercita agentes y pasos con JSONL real, reloj fijo y sin lanzar arneses."""

    def setUp(self):
        """Aísla persistencia, variables del bucle y procesos externos."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cfg = {'harness': 'claude', 'model': 'titular',
                    'reserva': [{'model': 'intermedia'}, {'harness': 'agy', 'model': 'ultima'}]}
        self.enterContext(patch.dict(motor.os.environ, {}, clear=True))
        self.enterContext(patch.object(motor, 'ahora', return_value='2026-10-25T12:00:00+00:00'))
        self.enterContext(patch.object(motor, 'config', side_effect=lambda root: {
            'hades': self.cfg, 'artemisa': self.cfg}))
        self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe))
        self.enterContext(patch.object(motor, 'construir_prompt_agente', return_value='revisa'))
        self.enterContext(patch.object(motor, 'excluir'))
        self.enterContext(patch('builtins.print'))

    def agotamiento(self, modelo='titular', arnes='claude', fecha='2026-10-25T11:59:00+00:00', segundos=3600):
        """Añade una ventana explícita de agotamiento al registro temporal."""
        motor.registrar(self.root, dict(tipo='agente', rol='hades', fecha=fecha, arnes=arnes,
                                        modelo_cuota=modelo, cuota_espera_s=segundos))

    def invocar(self):
        """Devuelve los modelos realmente lanzados por una revisión exitosa."""
        with patch.object(motor, 'lanzar', return_value=(0, {}, 'APROBADO')) as lanzar:
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
        return [c.args[0][c.args[0].index('--model') + 1] if '--model' in c.args[0]
                else 'predeterminado' for c in lanzar.call_args_list]

    def test_siguiente_revision_omite_titular_tras_agotamiento_registrado(self):
        """La primera revisión registra la cuota y la siguiente usa la reserva directamente."""
        with patch.object(motor, 'lanzar', side_effect=[
                (1, {}, 'out of credits'), (0, {}, 'APROBADO')]) as lanzar:
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
        self.assertEqual(lanzar.call_count, 2)
        with patch.object(motor, 'consumo_cuotas', wraps=motor.consumo_cuotas) as consumo:
            self.assertEqual(self.invocar(), ['intermedia'])
        consumo.assert_called_once()

    def test_expiracion_y_fecha_futura_permiten_titular(self):
        """Una cuota al límite exacto, caducada o futura no excluye el titular."""
        for fecha in ('2026-10-25T11:00:00+00:00', '2026-10-25T10:59:59+00:00',
                      '2026-10-25T12:01:00+00:00'):
            with self.subTest(fecha=fecha):
                self.agotamiento(fecha=fecha)
                self.assertEqual(self.invocar(), ['titular'])

    def test_omite_titular_y_reserva_intermedia_agotados(self):
        """La primera configuración disponible conserva su orden relativo."""
        self.agotamiento()
        self.agotamiento('intermedia')
        self.assertEqual(self.invocar(), ['ultima'])

    def test_todas_agotadas_conservan_ultima_configuracion(self):
        """La lista nunca queda vacía y el fallo final conserva la señal de espera."""
        self.agotamiento()
        self.agotamiento('intermedia')
        self.agotamiento('ultima', 'agy')
        with patch.object(motor, 'lanzar', return_value=(1, {}, 'out of credits')) as lanzar:
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
        lanzar.assert_called_once()
        self.assertEqual(lanzar.call_args.args[2], 'agy')
        filas = motor.leer_metricas(self.root)
        self.assertTrue(filas[-1]['sin_cuota'])
        self.assertGreater(filas[-1]['espera_s'], 0)

    def test_sin_reservas_conserva_titular_sin_consultar_cuotas(self):
        """Una única configuración sigue el manejo de cuota existente."""
        self.cfg.pop('reserva')
        self.agotamiento()
        with patch.object(motor, 'consumo_cuotas', wraps=motor.consumo_cuotas) as consumo:
            self.assertEqual(self.invocar(), ['titular'])
        consumo.assert_not_called()

    def test_clave_incluye_arnes_y_modelo_predeterminado(self):
        """No se confunden modelos homónimos de arneses distintos ni el modelo implícito."""
        self.agotamiento(arnes='codex')
        self.assertEqual(self.invocar(), ['titular'])
        self.cfg.pop('model')
        self.agotamiento(modelo='predeterminado')
        self.assertEqual(self.invocar(), ['intermedia'])

    def test_bucle_omite_cuota_y_respeta_harness_forzado_y_cmd(self):
        """El paso usa cuotas; las opciones explícitas de arnés y comando conservan su selección."""
        for harness, cmd, arnes, esperado in (
                (None, None, 'claude', 'intermedia'),
                ('codex', None, 'codex', 'titular'),
                ('codex', None, 'claude', 'titular'),
                (None, 'personalizado {prompt}', 'claude', 'titular')):
            with self.subTest(harness=harness, cmd=cmd, arnes=arnes):
                ruta = self.root / motor.METRICAS
                if ruta.exists():
                    ruta.unlink()
                self.agotamiento(arnes=arnes)
                args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=harness,
                    estado=False, max_pasos=1, reintentos=2, espera_max=2, cmd=cmd)
                with (patch.object(motor, 'iniciar_gateway'),
                      patch.object(motor, 'recargar_version', return_value=False),
                      patch.object(motor, 'ingerir', return_value=[]),
                      patch.object(motor, 'estado', return_value=('PASO', 'task-dev', 'T-ADV-0021', '')),
                      patch.object(motor, 'ejecutar', return_value=(0, {}, 'ok')) as ejecutar,
                      patch.object(motor, 'firma', side_effect=['antes', 'despues']),
                      patch.object(motor, 'git', return_value=''),
                      patch.object(motor, 'avisar'),
                      patch.object(motor, 'esperar') as esperar):
                    motor.bucle(args, self.root)
                ejecutar.assert_called_once()
                self.assertEqual(ejecutar.call_args.kwargs['rol']['model'], esperado)
                esperar.assert_not_called()


class LlamadasEfectivasTests(unittest.TestCase):
    """Cuenta llamadas reales sin alterar rechazos ni consumo registrado."""

    def test_rebotes_no_cuentan_y_rechazos_tokens_coste_se_conservan(self):
        """Cada marcador excluye solo llamadas; modelos ausentes o nulos son compatibles."""
        for marca in ({'cuota_espera_s': 60}, {'sin_cuota': True}, {'modelos': {}}):
            with self.subTest(marca=marca):
                base = dict(tipo='agente', rol='hades', id='T-ADV-0021',
                            modelos={'modelo': {'entrada': 7}}, coste_usd=1)
                registros = [{**base, **marca, 'veredicto': 'RECHAZADO'},
                             {**base, 'veredicto': 'APROBADO'},
                             dict(tipo='agente', rol='hades', id='T-ADV-0021', veredicto='RECHAZADO'),
                             dict(tipo='agente', rol='hades', id='T-ADV-0021', modelos=None),
                             {**base, 'cuota_espera_s': 0, 'sin_cuota': False}]
                fila = metricas.agregar(registros, [dict(id='T-ADV-0021', version='v0.6')])[0]
                self.assertEqual(fila['hades_llamadas'], 4)
                self.assertEqual(fila['hades_rechazos'], 2)
                self.assertEqual(fila['hades_tokens_originales'], 14 if marca == {'modelos': {}} else 21)
                self.assertEqual(fila['coste_estimado_usd'], 3)


if __name__ == '__main__':
    unittest.main()
