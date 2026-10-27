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
from tests import aislamiento_telegram


SPEC = importlib.util.spec_from_file_location('gateway_fondo', Path(__file__).with_name('gateway.py'))
gateway = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gateway)
motor = gateway.motor
EXCLUIR = motor.excluir


class CapturaSalida(io.StringIO):
    """Stream capturable que admite la configuración de consola del gateway."""

    def reconfigure(self, **kwargs):
        """Ignora la configuración de encoding durante las pruebas."""


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

    def cli(self, *args, root=None, salida=None):
        """Invoca la CLI restaurando directorio y streams del runner."""
        proyecto = root or self.root
        cwd = Path.cwd()
        self.addCleanup(os.chdir, cwd)
        with patch.object(sys, 'argv', ['gateway.py', '--root', str(proyecto), *args]), \
                patch.object(gateway.sys, 'stdout', salida) if salida is not None else patch.object(gateway.sys, 'stdout'):
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

    def test_credenciales_indican_origen_independiente_de_los_ids(self):
        """Los dos campos usan su fuente local primero y origen solo describe el token."""
        casos = (
            ('token-local-ficticio', '111', None, None,
             'token-local-ficticio', ['111'], 'proyecto'),
            ('token-local-ficticio', '111', 'token-entorno-ficticio', '222',
             'token-local-ficticio', ['111'], 'proyecto'),
            ('token-local-ficticio', None, None, '222',
             'token-local-ficticio', ['222'], 'proyecto'),
            (None, '111', 'token-entorno-ficticio', None,
             'token-entorno-ficticio', ['111'], 'entorno'),
            (None, None, 'token-entorno-ficticio', '222',
             'token-entorno-ficticio', ['222'], 'entorno'),
            ('', '', 'token-entorno-ficticio', '222',
             'token-entorno-ficticio', ['222'], 'entorno'),
            ('', '111', 'token-entorno-ficticio', '222',
             'token-entorno-ficticio', ['111'], 'entorno'),
            ('token-local-ficticio', '', 'token-entorno-ficticio', '222',
             'token-local-ficticio', ['222'], 'proyecto'),
            (None, '111', None, None,
             '', ['111'], 'ninguno'),
            (None, None, None, None, '', [], 'ninguno'),
        )
        for token_local, ids_locales, token_ambiental, ids_ambientales, token, ids, origen in casos:
            with self.subTest(token_local=token_local, ids_locales=ids_locales,
                              token_ambiental=token_ambiental, ids_ambientales=ids_ambientales):
                locales = []
                if token_local is not None:
                    locales.append(f'TELEGRAM_BOT_TOKEN={token_local}')
                if ids_locales is not None:
                    locales.append(f'TELEGRAM_ALLOWED_USER_IDS={ids_locales}')
                (self.root / '.env').write_text('\n'.join(locales), encoding='utf-8')
                with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': '',
                                            'TELEGRAM_ALLOWED_USER_IDS': ''}) as ambiental:
                    if token_ambiental is None:
                        ambiental.pop('TELEGRAM_BOT_TOKEN')
                    else:
                        ambiental['TELEGRAM_BOT_TOKEN'] = token_ambiental
                    if ids_ambientales is None:
                        ambiental.pop('TELEGRAM_ALLOWED_USER_IDS')
                    else:
                        ambiental['TELEGRAM_ALLOWED_USER_IDS'] = ids_ambientales
                    credenciales = motor.credenciales(self.root)
                self.assertEqual((credenciales.token, credenciales.usuarios, credenciales.origen),
                                 (token, ids, origen))
                self.assertEqual(tuple(credenciales), (token, ids))

    def test_autoarranque_con_token_ambiental_solo_informa_una_vez(self):
        """Cada bucle informa una vez aunque solicite varias veces el autoarranque."""
        clave = str(self.root.resolve())
        motor._gateway_aviso_entorno.discard(clave)
        self.addCleanup(motor._gateway_aviso_entorno.discard, clave)
        motivo = 'token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto'
        with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'token-entorno-ficticio',
                                    'TELEGRAM_ALLOWED_USER_IDS': '222'}), \
                patch.object(motor.subprocess, 'run') as run, \
                patch.object(motor.subprocess, 'Popen') as popen, \
                patch.object(gateway, 'escuchar') as escuchar, \
                patch.object(gateway, 'reservar') as reservar, \
                patch.object(motor, 'avisar', return_value=False), \
                patch.object(motor, 'suite', return_value=''):
            args = argparse.Namespace(estado=False, idea=None, docs='docs', test=None, max_pasos=0)
            for _ in range(2):
                inicio = len(self.stdout.getvalue())
                motor.bucle(args, self.root)
                self.assertEqual(self.stdout.getvalue()[inicio:].count(motivo), 1)
                for _ in range(3):
                    motor.iniciar_gateway(self.root)
                self.assertEqual(self.stdout.getvalue()[inicio:].count(motivo), 1)
        run.assert_not_called()
        popen.assert_not_called()
        escuchar.assert_not_called()
        reservar.assert_not_called()

    def test_autoarranque_con_token_local_conserva_escucha(self):
        """Las tres combinaciones locales autorizadas solicitan el gateway una vez."""
        casos = (('111', None, None), ('111', 'token-entorno-ficticio', '222'),
                 (None, None, '222'))
        with patch.object(motor.subprocess, 'run') as run, \
                patch.object(gateway, 'escuchar') as escuchar, \
                patch.object(motor.subprocess, 'Popen') as popen:
            run.return_value.returncode = 0
            for indice, (ids_locales, token_ambiental, ids_ambientales) in enumerate(casos):
                proyecto = self.root / f'Proyecto{indice}'
                proyecto.mkdir()
                local = ['TELEGRAM_BOT_TOKEN=token-local-ficticio']
                if ids_locales is not None:
                    local.append(f'TELEGRAM_ALLOWED_USER_IDS={ids_locales}')
                (proyecto / '.env').write_text('\n'.join(local), encoding='utf-8')
                with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': '',
                                            'TELEGRAM_ALLOWED_USER_IDS': ''}) as entorno:
                    if token_ambiental is not None:
                        entorno['TELEGRAM_BOT_TOKEN'] = token_ambiental
                    if ids_ambientales is not None:
                        entorno['TELEGRAM_ALLOWED_USER_IDS'] = ids_ambientales
                    motor.iniciar_gateway(proyecto)
                llamada = run.call_args_list[-1]
                self.assertEqual(llamada.args[0][-2:], [str(proyecto), '--fondo'])
        self.assertEqual(run.call_count, len(casos))
        escuchar.assert_not_called()
        popen.assert_not_called()
        self.assertNotIn('token de Telegram del entorno: solo avisos', self.stdout.getvalue())

    def test_credenciales_incompletas_no_avisan_ni_arrancan(self):
        """Sin ambos valores efectivos no salen avisos ni se cruza ninguna entrada de escucha."""
        casos = (('token-local-ficticio', None, None, None),
                 (None, '111', None, None), ('', '111', None, None),
                 (None, None, None, None),
                 (None, None, 'token-entorno-ficticio', None))
        with patch.object(motor, 'enviar') as enviar, \
                patch.object(motor.subprocess, 'run') as run, \
                patch.object(motor.subprocess, 'Popen') as popen, \
                patch.object(gateway, 'reservar') as reservar, \
                patch.object(gateway, 'escuchar') as escuchar:
            for local, ids_locales, ambiental, ids_ambientales in casos:
                locales = []
                if local is not None:
                    locales.append(f'TELEGRAM_BOT_TOKEN={local}')
                if ids_locales is not None:
                    locales.append(f'TELEGRAM_ALLOWED_USER_IDS={ids_locales}')
                (self.root / '.env').write_text('\n'.join(locales), encoding='utf-8')
                with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': '',
                                            'TELEGRAM_ALLOWED_USER_IDS': ''}) as entorno:
                    if ambiental is not None:
                        entorno['TELEGRAM_BOT_TOKEN'] = ambiental
                    if ids_ambientales is not None:
                        entorno['TELEGRAM_ALLOWED_USER_IDS'] = ids_ambientales
                    self.assertFalse(motor.avisar(self.root, 'version', 'Versión terminada'))
                    motor.iniciar_gateway(self.root)
                    for args in ((), ('--fondo',), ('--gestionado',)):
                        with self.subTest(args=args, local=local, ids_locales=ids_locales), \
                                self.assertRaisesRegex(SystemExit, 'Faltan TELEGRAM_BOT_TOKEN'):
                            self.cli(*args)
        enviar.assert_not_called()
        run.assert_not_called()
        popen.assert_not_called()
        reservar.assert_not_called()
        escuchar.assert_not_called()
        self.assertFalse((self.root / 'telegram.pid').exists())

    def test_aviso_usa_el_respaldo_ambiental_y_prefija_el_proyecto(self):
        """Avisos locales y ambientales conservan el destinatario y la firma exactos."""
        proyecto = self.root / 'ProyectoDemo'
        proyecto.mkdir()
        casos = (
            ('token-local-ficticio', '111', None, None,
             'token-local-ficticio', '111'),
            ('token-local-ficticio', '111', 'token-entorno-ficticio', '222',
             'token-local-ficticio', '111'),
            ('token-local-ficticio', '', 'token-entorno-ficticio', '222',
             'token-local-ficticio', '222'),
            ('', '111', 'token-entorno-ficticio', '222', 'token-entorno-ficticio', '111'),
            ('', '', 'token-entorno-ficticio', '222', 'token-entorno-ficticio', '222'),
        )
        for local, ids_locales, ambiental, ids_ambientales, token_esperado, id_esperado in casos:
            with self.subTest(local=local, ids_locales=ids_locales):
                (proyecto / '.env').write_text(
                    f'TELEGRAM_BOT_TOKEN={local}\nTELEGRAM_ALLOWED_USER_IDS={ids_locales}\n',
                    encoding='utf-8')
                with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': '',
                                            'TELEGRAM_ALLOWED_USER_IDS': ''}) as entorno, \
                        patch.object(motor, 'version_adevv', return_value='1.0.0', create=True), \
                        patch.object(motor, 'enviar', return_value=True) as enviar, \
                        patch.object(motor.subprocess, 'run') as run, \
                        patch.object(motor.subprocess, 'Popen') as popen, \
                        patch.object(gateway, 'escuchar') as escuchar:
                    if ambiental is None:
                        entorno.pop('TELEGRAM_BOT_TOKEN')
                    else:
                        entorno['TELEGRAM_BOT_TOKEN'] = ambiental
                    if ids_ambientales is None:
                        entorno.pop('TELEGRAM_ALLOWED_USER_IDS')
                    else:
                        entorno['TELEGRAM_ALLOWED_USER_IDS'] = ids_ambientales
                    self.assertTrue(motor.avisar(proyecto, 'version', 'Versión terminada'))
                enviar.assert_called_once()
                self.assertEqual(enviar.call_args.args[:2], (token_esperado, id_esperado))
                run.assert_not_called()
                popen.assert_not_called()
                escuchar.assert_not_called()
                texto = enviar.call_args.args[2]
                self.assertTrue(texto.startswith('[ProyectoDemo] Versión terminada'))
                self.assertTrue(texto.endswith('— Adevv v1.0.0'))

    def test_entradas_de_escucha_rechazan_token_ambiental_antes_de_efectos(self):
        """Cada entrada rechaza el token ambiental antes de reserva, proceso o escucha."""
        motivo = 'token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto'
        casos = ((None, None, 'token-entorno-ficticio', '222'),
                 (None, '111', 'token-entorno-ficticio', '222'),
                 ('', '111', 'token-entorno-ficticio', '222'),
                 ('   ', '111', 'token-entorno-ficticio', '222'))
        with patch.object(motor.subprocess, 'Popen') as popen, \
                patch.object(gateway, 'reservar') as reservar, \
                patch.object(gateway, 'escuchar') as escuchar, \
                patch.object(motor, 'recibir_recarga', return_value={'desde': 123}):
            for local, ids_locales, ambiental, ids_ambientales in casos:
                locales = []
                if local is not None:
                    locales.append(f'TELEGRAM_BOT_TOKEN={local}')
                if ids_locales is not None:
                    locales.append(f'TELEGRAM_ALLOWED_USER_IDS={ids_locales}')
                (self.root / '.env').write_text('\n'.join(locales), encoding='utf-8')
                with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': ambiental,
                                            'TELEGRAM_ALLOWED_USER_IDS': ids_ambientales}):
                    for args in ((), ('--fondo',), ('--gestionado',)):
                        with self.subTest(args=args, local=local, ids_locales=ids_locales):
                            try:
                                self.cli(*args)
                            except SystemExit as error:
                                self.assertEqual(str(error), f'[gateway] {motivo}')
                            else:
                                self.fail('La escucha aceptó un token que solo autoriza avisos')
        popen.assert_not_called()
        reservar.assert_not_called()
        escuchar.assert_not_called()
        self.assertFalse((self.root / 'telegram.pid').exists())

    def test_entradas_de_escucha_locales_conservan_token_de_proyecto(self):
        """Los tres modos funcionan con credenciales locales, cruzadas y combinadas."""
        casos = (('111', None, None, '111'),
                 ('111', 'token-entorno-ficticio', '222', '111'),
                 (None, None, '222', '222'))
        with patch.object(motor, 'recibir_recarga', return_value={'desde': 123}), \
                patch.object(gateway, 'escuchar') as escuchar, \
                patch.object(motor.subprocess, 'Popen') as popen:
            popen.return_value.pid = 321
            for indice, (ids_locales, token_ambiental, ids_ambientales, usuario) in enumerate(casos):
                proyecto = self.root / f'Proyecto{indice}'
                proyecto.mkdir()
                local = ['TELEGRAM_BOT_TOKEN=token-local-ficticio']
                if ids_locales is not None:
                    local.append(f'TELEGRAM_ALLOWED_USER_IDS={ids_locales}')
                (proyecto / '.env').write_text('\n'.join(local), encoding='utf-8')
                with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': '',
                                            'TELEGRAM_ALLOWED_USER_IDS': ''}) as entorno:
                    if token_ambiental is not None:
                        entorno['TELEGRAM_BOT_TOKEN'] = token_ambiental
                    if ids_ambientales is not None:
                        entorno['TELEGRAM_ALLOWED_USER_IDS'] = ids_ambientales
                    for args in ((), ('--gestionado',), ('--fondo',)):
                        salida = CapturaSalida()
                        self.assertEqual(self.cli(*args, root=proyecto, salida=salida), 0)
                        self.assertNotIn('token de Telegram del entorno: solo avisos', salida.getvalue())
        self.assertEqual(escuchar.call_count, 2 * len(casos))
        for indice, (_, _, _, usuario) in enumerate(casos):
            for llamada in escuchar.call_args_list[indice * 2:(indice + 1) * 2]:
                self.assertEqual(llamada.args[0].resolve(), (self.root / f'Proyecto{indice}').resolve())
                self.assertEqual(llamada.args[1:3], ('token-local-ficticio', {usuario}))
                self.assertEqual(llamada.kwargs, {'desde': 123})
        self.assertEqual(popen.call_count, len(casos))

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
            inicio.assert_called_once_with(self.root, informar=False)
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
