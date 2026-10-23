"""Lifecycle del gateway aislado de Telegram, modelos y procesos reales."""
import argparse
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from adevv.processes import _clasificar_linea_comandos


SPEC = importlib.util.spec_from_file_location('gateway_fondo', Path(__file__).with_name('gateway.py'))
gateway = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gateway)
motor = gateway.motor
EXCLUIR = motor.excluir


class FondoTests(unittest.TestCase):
    """Archivos temporales, PID controlados y fronteras externas simuladas."""

    def setUp(self):
        """Evita heredar credenciales o lanzar procesos del equipo."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.enterContext(patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': '',
                                                 'TELEGRAM_ALLOWED_USER_IDS': ''}))
        self.enterContext(patch.object(motor, 'excluir'))
        self.stdout = self.enterContext(redirect_stdout(io.StringIO()))

    def marca(self, valor):
        """Escribe una marca PID sin depender de constantes nuevas."""
        (self.root / 'telegram.pid').write_text(str(valor), encoding='utf-8')

    def cli(self, *args):
        """Invoca la CLI restaurando directorio y streams del runner."""
        cwd = Path.cwd()
        self.addCleanup(os.chdir, cwd)
        with patch.object(sys, 'argv', ['gateway.py', '--root', str(self.root), *args]), \
                patch.object(gateway.sys, 'stdout'):
            return gateway.main()

    def test_fondo_publica_pid_log_y_comando_clasificable(self):
        """La frontera Popen recibe un gateway sin credenciales en argumentos."""
        with patch.object(motor.subprocess, 'Popen') as popen:
            popen.return_value.pid = 321
            self.assertEqual(gateway.en_fondo(self.root), 0)
        cmd = popen.call_args.args[0]
        self.assertEqual(cmd[:3], [sys.executable, '-u', str(Path(gateway.__file__).resolve())])
        self.assertEqual(cmd[3:], ['--root', str(self.root), '--gestionado'])
        self.assertEqual(_clasificar_linea_comandos(subprocess.list2cmdline(cmd)), 'gateway')
        self.assertEqual((self.root / 'telegram.pid').read_text(), '321')
        self.assertTrue((self.root / 'telegram.log').exists())
        kw = popen.call_args.kwargs
        self.assertEqual(kw['cwd'], self.root)
        self.assertEqual(kw['stdin'], subprocess.DEVNULL)
        self.assertEqual(kw['stderr'], subprocess.STDOUT)
        if os.name == 'nt':
            self.assertTrue(kw['creationflags'] & subprocess.CREATE_NO_WINDOW)
        else:
            self.assertTrue(kw['start_new_session'])

    def test_pid_vivo_no_duplica(self):
        """Un proceso reservado vivo impide otro hijo."""
        self.marca(os.getpid())
        with patch.object(motor.subprocess, 'Popen') as popen:
            with self.assertRaisesRegex(SystemExit, 'marcha'):
                gateway.en_fondo(self.root)
        popen.assert_not_called()
        self.assertEqual((self.root / 'telegram.pid').read_text(), str(os.getpid()))

    def test_marcas_invalidas_y_muertas_se_recuperan(self):
        """Los restos no bloquean el siguiente arranque ni dejan una parada antigua."""
        for contenido in ('basura', '', '0', '-1', '999999999'):
            with self.subTest(contenido=contenido), patch.object(motor.subprocess, 'Popen') as popen:
                self.marca(contenido)
                (self.root / 'telegram.parar').touch()
                popen.return_value.pid = 321
                gateway.en_fondo(self.root)
                self.assertEqual((self.root / 'telegram.pid').read_text(), '321')
                self.assertFalse((self.root / 'telegram.parar').exists())

    def test_fallo_popen_limpia_reserva(self):
        """Un fallo de lanzamiento no anuncia éxito ni bloquea reintentos."""
        with patch.object(motor.subprocess, 'Popen', side_effect=OSError('fallo')):
            with self.assertRaises(OSError):
                gateway.en_fondo(self.root)
        self.assertFalse((self.root / 'telegram.pid').exists())

    def test_parar_cli_sin_credenciales_conserva_bucle_y_pid_vivo(self):
        """La parada CLI se limita a la señal del gateway."""
        self.marca(os.getpid())
        (self.root / motor.PID).write_text('123')
        self.assertEqual(self.cli('--parar'), 0)
        self.assertTrue((self.root / 'telegram.parar').exists())
        self.assertEqual((self.root / 'telegram.pid').read_text(), str(os.getpid()))
        self.assertEqual((self.root / motor.PID).read_text(), '123')

    def test_parar_obsoleto_limpia_y_es_idempotente(self):
        """Sin gateway no queda solicitud que afecte al próximo arranque."""
        self.marca('invalido')
        (self.root / 'telegram.parar').touch()
        self.assertEqual(self.cli('--parar'), 0)
        self.assertEqual(self.cli('--parar'), 0)
        self.assertFalse((self.root / 'telegram.pid').exists())
        self.assertFalse((self.root / 'telegram.parar').exists())

    def test_polling_no_empieza_si_hay_parada(self):
        """La señal previa evita red y respuesta."""
        (self.root / 'telegram.parar').touch()
        with patch.object(gateway, 'actualizaciones') as polling:
            gateway.escuchar(self.root, 'tok', {'42'}, vueltas=1)
        polling.assert_not_called()

    def test_parada_entre_mensajes_no_procesa_el_siguiente(self):
        """Termina la operación en curso y no empieza otra tras la señal."""
        mensajes = [dict(update_id=n, message=dict(text='hola', chat=dict(id=42))) for n in (1, 2)]
        def responder(*args):
            """La operación actual recibe una solicitud de parada concurrente."""
            (self.root / 'telegram.parar').touch()
            return 'respuesta'
        with patch.object(gateway, 'actualizaciones', return_value=mensajes), \
                patch.object(gateway, 'responder', side_effect=responder) as respuesta, \
                patch.object(motor, 'enviar') as enviar:
            gateway.escuchar(self.root, 'tok', {'42'}, vueltas=1)
        self.assertEqual(respuesta.call_count, 1)
        enviar.assert_called_once()

    def test_cli_propietario_limpia_al_salir_incluso_con_error(self):
        """El PID es el de la escucha y las marcas desaparecen al salir."""
        def escuchar(*args):
            """Comprueba propiedad y provoca un error de operación."""
            self.assertEqual((self.root / 'telegram.pid').read_text(), str(os.getpid()))
            (self.root / 'telegram.parar').touch()
            raise RuntimeError('escucha fallida')
        with patch.object(motor, 'credenciales', return_value=('tok', ['42'])), \
                patch.object(gateway, 'escuchar', side_effect=escuchar):
            with self.assertRaisesRegex(RuntimeError, 'escucha fallida'):
                self.cli()
        self.assertFalse((self.root / 'telegram.pid').exists())
        self.assertFalse((self.root / 'telegram.parar').exists())

    def test_cli_sin_credenciales_no_lanza(self):
        """La configuración incompleta falla antes de reservar PID o crear hijo."""
        with patch.object(motor.subprocess, 'Popen') as popen:
            with self.assertRaisesRegex(SystemExit, 'Faltan'):
                self.cli('--fondo')
        popen.assert_not_called()
        self.assertFalse((self.root / 'telegram.pid').exists())

    def test_gestionado_espera_publicacion_y_limpia(self):
        """Un hijo rápido no escucha antes de la publicación del PID por el padre."""
        self.marca(777)
        def publicar(*args):
            """Simula la escritura del padre después de Popen."""
            self.marca(os.getpid())
        with patch.object(motor, 'credenciales', return_value=('tok', ['42'])), \
                patch.object(gateway.time, 'sleep', side_effect=publicar) as dormir, \
                patch.object(gateway, 'escuchar') as escuchar:
            self.assertEqual(self.cli('--gestionado'), 0)
        dormir.assert_called_once()
        escuchar.assert_called_once()
        self.assertFalse((self.root / 'telegram.pid').exists())

    def test_autoarranque_frontera_y_fallo_tolerado(self):
        """Solo consulta configuración habilitada y acota el lanzador."""
        with patch.object(motor, 'telegram', return_value=('tok', ['42'], set())), \
                patch.object(motor.subprocess, 'run') as run:
            run.return_value.returncode = 0
            motor.iniciar_gateway(self.root)
            self.assertEqual(run.call_args.args[0], [sys.executable, str(Path(gateway.__file__).resolve()),
                                                   '--root', str(self.root), '--fondo'])
            self.assertEqual(run.call_args.kwargs['timeout'], 10)
            run.side_effect = OSError('sin recursos')
            motor.iniciar_gateway(self.root)
        self.assertIn('gateway', self.stdout.getvalue())

    def test_autoarranque_desactivado_no_invoca_procesos(self):
        """Sin credenciales y con telegram:false la frontera no se cruza."""
        with patch.object(motor.subprocess, 'run') as run:
            motor.iniciar_gateway(self.root)
            with patch.object(motor, 'credenciales', return_value=('tok', ['42'])), \
                    patch.object(motor, 'config', return_value={'telegram': False}):
                motor.iniciar_gateway(self.root)
        run.assert_not_called()

    def test_puntos_de_entrada_y_estado(self):
        """Ambos arranques reales llaman al helper; --estado es solo lectura."""
        args = argparse.Namespace(idea=None, docs='docs', test=None, max_pasos=0, estado=False)
        with patch.object(motor, 'iniciar_gateway') as inicio, \
                patch.object(motor.subprocess, 'Popen') as popen:
            popen.return_value.pid = 321
            motor.en_fondo(self.root, argumentos=[])
            inicio.assert_called_once_with(self.root)
            inicio.reset_mock()
            motor.bucle(args, self.root)
            inicio.assert_called_once_with(self.root)
            inicio.reset_mock()
            args.estado = True
            motor.bucle(args, self.root)
            inicio.assert_not_called()

    def test_archivos_excluidos_realmente_de_git(self):
        """PROPIOS excluye las tres marcas en un repositorio temporal real."""
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True, capture_output=True)
        for nombre in ('telegram.pid', 'telegram.log', 'telegram.parar'):
            self.assertIn(nombre, motor.PROPIOS)
        cwd = Path.cwd()
        try:
            os.chdir(self.root)
            EXCLUIR(self.root)
        finally:
            os.chdir(cwd)
        for nombre in ('telegram.pid', 'telegram.log', 'telegram.parar'):
            (self.root / nombre).touch()
        estado = subprocess.run(['git', 'status', '--porcelain'], cwd=self.root,
                                check=True, capture_output=True, text=True)
        self.assertEqual(estado.stdout, '')


if __name__ == '__main__':
    unittest.main()
