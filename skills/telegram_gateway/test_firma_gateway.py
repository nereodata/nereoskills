import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from skills.telegram_gateway import gateway


class TestFirmaGateway(unittest.TestCase):
    """Pruebas unitarias para la firma de versión en respuestas y conversación del gateway."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def responder(self, texto, usuario='12345'):
        return gateway.responder(self.root, usuario, texto, {'12345'})

    def test_comandos_incluyen_firma_de_version(self):
        """Todos los comandos del gateway devuelven respuestas con la firma de versión al pie."""
        comandos = [
            '/estado',
            '/agentes',
            '/parar',
            '/lanzar',
            '/metricas',
            '/tarea Probar firma',
            '/bug Fallo de firma',
            '/nuevo',
            '/ayuda'
        ]
        with patch.object(gateway.motor, 'version_adevv', return_value='0.5.0', create=True), \
             patch.object(gateway.motor, 'parte', return_value='Parte del bucle'), \
             patch.object(gateway.motor, 'estado', return_value=('PASO', 'task-dev', 'T-ADV-0019', 'release/v0.5')), \
             patch.object(gateway.motor, 'informe_agentes', return_value='Agentes para task-dev T-ADV-0019\nhades: agy/gemini-4-argon-medium'), \
             patch.object(gateway.motor, 'en_fondo'), \
             patch.object(gateway.motor, 'apuntar'), \
             patch.object(gateway.motor, 'ingerir', return_value=[('T-ADV-0099', 'Tarea')]), \
             patch.object(gateway, 'resumen_metricas', return_value='Resumen de métricas'):

            for cmd in comandos:
                with self.subTest(cmd=cmd):
                    resp = self.responder(cmd)
                    self.assertIsNotNone(resp, f'El comando {cmd} no devolvió respuesta')
                    self.assertTrue(resp.endswith('— Adevv v0.5.0'),
                                    f'El comando {cmd} no termina con la firma: {resp!r}')

    def test_conversar_incluye_firma_con_harness_y_modelo(self):
        """La conversación libre añade la firma con arnés y modelo configurados."""
        cfg_simulada = {
            'atenea': {
                'harness': 'agy',
                'model': 'gemini-4-argon-medium'
            }
        }
        with patch.object(gateway.motor, 'version_adevv', return_value='0.5.0', create=True), \
             patch.object(gateway.motor, 'config', return_value=cfg_simulada), \
             patch.object(gateway, 'obtener_sesion', return_value=None), \
             patch.object(gateway, 'guardar_sesion'), \
             patch.object(gateway, 'invocar', return_value=(0, 'sesion-1', 'Respuesta conversacional del asistente')):

            resp = gateway.conversar(self.root, '12345', 'Hola, ¿qué tal?')
            self.assertTrue(resp.endswith('— Adevv v0.5.0 · agy/gemini-4-argon-medium'),
                            f'La conversación no termina con la firma esperada: {resp!r}')

    def test_escuchar_envia_mensajes_firmados_sin_duplicar(self):
        """escuchar() envía las respuestas a través de motor.enviar conservando la firma sin duplicar."""
        mensajes = [{
            'update_id': 100,
            'message': {
                'chat': {'id': 999},
                'from': {'id': '12345'},
                'text': '/ayuda'
            }
        }]
        enviados = []

        def mock_enviar(token, chat, texto, markdown=False):
            enviados.append(texto)
            return True

        with patch.object(gateway.motor, 'version_adevv', return_value='0.5.0', create=True), \
             patch.object(gateway, 'actualizaciones', return_value=mensajes), \
             patch.object(gateway.motor, 'enviar', side_effect=mock_enviar):
            gateway.escuchar(self.root, 'token-falso', {'12345'}, vueltas=1)

        self.assertEqual(len(enviados), 1)
        self.assertTrue(enviados[0].endswith('— Adevv v0.5.0'))
        self.assertNotIn('— Adevv v0.5.0\n\n— Adevv v0.5.0', enviados[0])

    def test_escuchar_error_incluye_firma(self):
        """En caso de excepción no controlada en responder(), el mensaje de error también se firma."""
        mensajes = [{
            'update_id': 101,
            'message': {
                'chat': {'id': 999},
                'from': {'id': '12345'},
                'text': '/estado'
            }
        }]
        enviados = []

        def mock_enviar(token, chat, texto, markdown=False):
            enviados.append(texto)
            return True

        with patch.object(gateway.motor, 'version_adevv', return_value='0.5.0', create=True), \
             patch.object(gateway, 'actualizaciones', return_value=mensajes), \
             patch.object(gateway, 'responder', side_effect=RuntimeError('Error simulado')), \
             patch.object(gateway.motor, 'enviar', side_effect=mock_enviar):
            gateway.escuchar(self.root, 'token-falso', {'12345'}, vueltas=1)

        self.assertEqual(len(enviados), 1)
        self.assertIn('No he podido procesarlo', enviados[0])
        self.assertTrue(enviados[0].endswith('— Adevv v0.5.0'))


if __name__ == '__main__':
    unittest.main()
