"""Recarga del gateway solo cuando termina el lote de mensajes."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from tests import aislamiento_telegram


SPEC = importlib.util.spec_from_file_location('gateway_recarga', Path(__file__).with_name('gateway.py'))
gateway = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gateway)


class GatewayRecargaTests(unittest.TestCase):
    """Comprueba el límite de polling y el offset que evita repetir mensajes."""

    def test_transfiere_tras_responder_lote_completo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eventos = []

            def recargar(*args):
                self.assertEqual(args[:3], (gateway.__file__, root, gateway.PID))
                self.assertEqual(args[4], 'gateway')
                eventos.append(('recarga', args[3]['desde']))
                return args[3]['desde'] == 43

            mensajes = [{'update_id': n, 'message': {'from': {'id': 1}, 'text': str(n), 'chat': {'id': 2}}} for n in (41, 42)]
            with patch.object(gateway.motor, 'recargar_version', side_effect=recargar, create=True), patch.object(gateway, 'actualizaciones', side_effect=lambda *a: eventos.append(('poll', a[1])) or mensajes), patch.object(gateway, 'responder', side_effect=lambda *a: eventos.append(('respuesta', a[2])) or 'ok'), patch.object(gateway.motor, 'enviar') as enviar:
                gateway.escuchar(root, 'token-falso', {'1'}, vueltas=2)
            self.assertEqual(eventos, [('recarga', None), ('poll', None), ('respuesta', '41'), ('respuesta', '42'), ('recarga', 43)])
            self.assertEqual(enviar.call_count, 2)

    def test_sin_cambio_continua_polling(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(gateway.motor, 'recargar_version', return_value=False, create=True), patch.object(gateway, 'actualizaciones', return_value=[]) as poll:
            gateway.escuchar(Path(tmp), 'token-falso', {'1'}, vueltas=2)
            self.assertEqual(poll.call_count, 2)

    def test_parada_no_recarga(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(gateway.motor, 'recargar_version', create=True) as recarga:
            root = Path(tmp)
            (root / gateway.PARADA).touch()
            gateway.escuchar(root, 'token-falso', {'1'})
            recarga.assert_not_called()

    def test_main_sucesor_restaura_offset_sin_reservar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            with patch.object(gateway.sys, 'argv', ['gateway', '--root', str(root)]), patch.object(gateway.sys, 'stdout'), patch.object(gateway.os, 'chdir'), patch.object(gateway.motor, 'credenciales', return_value=('token-falso', ['1'])), patch.object(gateway.motor, 'recibir_recarga', return_value={'desde': 43}), patch.object(gateway, 'reservar') as reservar, patch.object(gateway, 'escuchar') as escuchar, patch.object(gateway, 'limpiar'):
                self.assertEqual(gateway.main(), 0)
            reservar.assert_not_called()
            escuchar.assert_called_once_with(root, 'token-falso', {'1'}, desde=43)

    def test_offset_restaurado_se_usa_en_primer_poll(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(gateway.motor, 'recargar_version', return_value=False), patch.object(gateway, 'actualizaciones', return_value=[]) as poll:
            gateway.escuchar(Path(tmp), 'token-falso', {'1'}, vueltas=1, desde=43)
        poll.assert_called_once_with('token-falso', 43)

    def test_limpieza_antigua_conserva_pid_y_parada(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / gateway.PID).write_text(str(os.getpid() + 1))
            (root / gateway.PARADA).touch()
            gateway.limpiar(root)
            self.assertEqual((root / gateway.PID).read_text(), str(os.getpid() + 1))
            self.assertTrue((root / gateway.PARADA).exists())

    def test_transferencia_gateway_conserva_argumentos_y_raiz_absoluta(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destino = root / 'versions/0.6.0/skills/telegram_gateway/gateway.py'
            (root / gateway.PID).write_text(str(os.getpid()))
            with patch.object(gateway.motor, 'version_activa_distinta', return_value=(destino, '0.6.0')), patch.object(gateway.sys, 'argv', ['gateway', '--root', 'relativo', '--gestionado', '--root=anterior', '--root', 'duplicado']), patch.object(gateway.motor.subprocess, 'Popen', return_value=Mock(pid=9876)) as lanzar, patch('builtins.print') as imprimir:
                self.assertTrue(gateway.motor.recargar_version(gateway.__file__, root, gateway.PID, {'desde': 43}, 'gateway'))
            self.assertEqual(lanzar.call_args.args[0], [gateway.sys.executable, '-u', str(destino), '--gestionado', '--root', str(root)])
            self.assertEqual(lanzar.call_args.kwargs['cwd'], root)
            self.assertEqual((root / gateway.PID).read_text(), '9876')
            imprimir.assert_not_called()
            self.assertEqual((root / 'telegram.log').read_text(encoding='utf-8'), '[gateway] recargado a versión 0.6.0\n')
