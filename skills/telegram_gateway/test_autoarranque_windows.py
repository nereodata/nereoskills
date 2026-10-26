"""Autoarranque con Inicio temporal, lanzador ficticio y sin conexión a Telegram."""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('gateway_auto', Path(__file__).with_name('gateway.py'))
gateway = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gateway)


class Salida(io.StringIO):
    """Captura compatible con la consola configurable del gateway."""

    def reconfigure(self, **kwargs):
        """Conserva la captura en memoria."""


class AutoarranqueTests(unittest.TestCase):
    """Comprueba las órdenes públicas y la ejecución del registro publicado."""

    def setUp(self):
        """Aísla credenciales, Inicio, lanzador y todos los archivos generados."""
        tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.base = Path(tmp).resolve()
        self.root = self.base / "Proyecto Uno á ' &"
        self.otro = self.base / 'Proyecto Dos'
        self.inicio = self.base / 'Inicio simulado'
        for carpeta in (self.root, self.otro, self.inicio):
            carpeta.mkdir()
        self.enterContext(patch.dict(os.environ, {
            'LOCALAPPDATA': str(self.base / 'Local'), 'APPDATA': str(self.base / 'Roaming')}))
        os.environ.pop('TELEGRAM_BOT_TOKEN', None)
        os.environ.pop('TELEGRAM_ALLOWED_USER_IDS', None)
        self.cwd = Path.cwd()
        self.addCleanup(os.chdir, self.cwd)
        self.salida = Salida()

    def cli(self, accion, root=None, windows=True):
        """Ejecuta main con la misma opción que recibe el despachador público."""
        with patch.object(sys, 'argv', ['adevv', '--root', str(root or self.root),
                                       '--autoarranque', accion]), \
                patch.object(gateway.sys, 'platform', 'win32' if windows else 'linux'), \
                patch.object(gateway, 'carpeta_inicio', return_value=self.inicio, create=True), \
                redirect_stdout(self.salida):
            return gateway.main()

    def entradas(self):
        """Devuelve entradas ejecutables, excluyendo diagnósticos."""
        return sorted(self.inicio.glob('*.vbs'))

    def test_registro_idempotente_y_proyectos_independientes(self):
        """Tres altas producen dos entradas sin versiones ni secretos."""
        for root in (self.root, self.root, self.otro):
            self.assertEqual(self.cli('on', root), 0)
            self.assertIn(str(root), self.salida.getvalue())
            self.assertIn('autoarranque registrado', self.salida.getvalue())
            self.salida.seek(0)
            self.salida.truncate()
        self.assertEqual(len(self.entradas()), 2)
        for entrada in self.entradas():
            contenido = entrada.read_text(encoding='utf-16')
            self.assertIn(', 0, True)', contenido)
            self.assertNotIn('.adevv', contenido)

    def test_consulta_baja_y_baja_repetida_conservan_ajena(self):
        """Estado es de lectura y off retira únicamente el proyecto seleccionado."""
        self.assertEqual(self.cli('on'), 0)
        propia = self.entradas()[0]
        self.assertEqual(self.cli('on', self.otro), 0)
        ajena = next(p for p in self.entradas() if p != propia)
        original = ajena.read_bytes()
        snapshot = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.entradas()}
        self.salida.seek(0)
        self.salida.truncate()
        self.assertEqual(self.cli('estado'), 0)
        self.assertIn('autoarranque registrado', self.salida.getvalue())
        self.assertIn(str(self.root), self.salida.getvalue())
        self.assertEqual(snapshot, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.entradas()})
        for accion in ('off', 'estado', 'off'):
            self.salida.seek(0)
            self.salida.truncate()
            self.assertEqual(self.cli(accion), 0)
            self.assertIn('autoarranque no registrado', self.salida.getvalue())
            self.assertIn(str(self.root), self.salida.getvalue())
            self.assertFalse(propia.exists())
            self.assertEqual(ajena.read_bytes(), original)

    def test_fuera_windows_sin_efectos(self):
        """La activación no compatible informa y preserva el directorio ajeno."""
        ajena = self.inicio / 'ajena.txt'
        ajena.write_text('conservar', encoding='utf-8')
        with patch.object(gateway.subprocess, 'Popen') as proceso:
            self.assertNotEqual(self.cli('on', windows=False), 0)
        proceso.assert_not_called()
        self.assertIn('no está soportado', self.salida.getvalue())
        self.assertEqual(list(self.inicio.iterdir()), [ajena])
        self.assertEqual(ajena.read_text(encoding='utf-8'), 'conservar')

    def ejecutar_inicio(self, local=None, ids=None, ambiental='', ids_ambientales='', eliminar=False):
        """Ejecuta VBS/PowerShell nativos contra un adevv ficticio que observa main."""
        self.assertEqual(self.cli('on'), 0)
        if local is not None or ids is not None:
            (self.root / '.env').write_text(
                ''.join(f'{clave}={valor}\n' for clave, valor in (
                    ('TELEGRAM_BOT_TOKEN', local), ('TELEGRAM_ALLOWED_USER_IDS', ids))
                        if valor is not None),
                encoding='utf-8')
        if eliminar:
            self.root.rmdir()
        binario = self.base / 'bin'
        binario.mkdir()
        fixture = Path(__file__).resolve()
        (binario / 'adevv.cmd').write_text(
            '@echo off\nchcp 850 >nul\n"%ADEVV_TEST_PYTHON%" "%ADEVV_TEST_FIXTURE%" '
            '--lanzador %*\nexit /b %errorlevel%\n', encoding='ascii')
        observacion = self.base / 'observacion.jsonl'
        env = dict(os.environ, PATH=str(binario) + os.pathsep + os.environ['PATH'],
                   PYTHONPATH=str(Path(__file__).resolve().parents[2]),
                   ADEVV_TEST_PYTHON=sys.executable, ADEVV_TEST_FIXTURE=str(fixture),
                   ADEVV_OBSERVACION=str(observacion))
        for clave, valor in (('TELEGRAM_BOT_TOKEN', ambiental),
                             ('TELEGRAM_ALLOWED_USER_IDS', ids_ambientales)):
            if valor:
                env[clave] = valor
            else:
                env.pop(clave, None)
        proceso = subprocess.run(['cscript.exe', '//Nologo', str(self.entradas()[0])],
                                 env=env, cwd=self.base, capture_output=True, timeout=45)
        registros = [json.loads(linea) for linea in observacion.read_text(encoding='utf-8').splitlines()] \
            if observacion.exists() else []
        self.assertEqual(len(registros), 0 if eliminar else 1, registros)
        datos = registros[0] if registros else None
        logs = list((self.base / 'Local').rglob('*.log'))
        diagnostico = '\n'.join(p.read_text(encoding='utf-8-sig') for p in logs)
        return proceso, datos, diagnostico

    @unittest.skipUnless(sys.platform == 'win32', 'requiere intérpretes de Inicio de Windows')
    def test_inicio_efectivo_con_ids_locales(self):
        """Inicio ejecuta la orden estable desde una raíz literal y crea un hijo oculto."""
        proceso, datos, _ = self.ejecutar_inicio('token-local-ficticio', '111')
        self.assertEqual(proceso.returncode, 0, proceso.stderr)
        self.assertEqual(datos['argv'], ['telegram', '--fondo'])
        self.assertEqual(datos['cwd'], str(self.root))
        self.assertEqual(datos['procesos'], 1)
        self.assertTrue(datos['flags'] & subprocess.CREATE_NO_WINDOW)
        self.assertEqual(datos['escucha'], 0)

    @unittest.skipUnless(sys.platform == 'win32', 'requiere intérpretes de Inicio de Windows')
    def test_inicio_efectivo_con_ids_ambientales(self):
        """Los IDs ambientales permiten el arranque con token local."""
        proceso, datos, _ = self.ejecutar_inicio('token-local-ficticio', ids_ambientales='222')
        self.assertEqual(proceso.returncode, 0, proceso.stderr)
        self.assertEqual(datos['argv'], ['telegram', '--fondo'])
        self.assertEqual(datos['cwd'], str(self.root))
        self.assertEqual(datos['procesos'], 1)
        self.assertTrue(datos['flags'] & subprocess.CREATE_NO_WINDOW)

    @unittest.skipUnless(sys.platform == 'win32', 'requiere intérpretes de Inicio de Windows')
    def test_proyecto_eliminado(self):
        """Un proyecto eliminado deja diagnóstico fuera de él sin invocar adevv."""
        proceso, datos, log = self.ejecutar_inicio(eliminar=True)
        self.assertNotEqual(proceso.returncode, 0)
        self.assertIsNone(datos)
        self.assertIn('proyecto inexistente', log)
        self.assertFalse((self.root / gateway.PID).exists())

    def comprobar_rechazo(self, motivo, **kwargs):
        """Comprueba terminación sin procesos, escucha ni PID y con causa observable."""
        proceso, datos, log = self.ejecutar_inicio(**kwargs)
        self.assertNotEqual(proceso.returncode, 0)
        self.assertEqual(datos['argv'], ['telegram', '--fondo'])
        self.assertEqual(datos['procesos'], 0)
        self.assertEqual(datos['escucha'], 0)
        self.assertFalse(datos['pid'])
        self.assertIn(motivo, log)

    @unittest.skipUnless(sys.platform == 'win32', 'requiere intérpretes de Inicio de Windows')
    def test_token_ausente(self):
        """La falta de token termina con el diagnóstico de credenciales incompletas."""
        self.comprobar_rechazo('Faltan TELEGRAM_BOT_TOKEN', ids='111')

    @unittest.skipUnless(sys.platform == 'win32', 'requiere intérpretes de Inicio de Windows')
    def test_token_solo_ambiental(self):
        """El token ambiental conserva el diagnóstico de solo avisos."""
        self.comprobar_rechazo('solo avisos', ambiental='token-entorno-ficticio', ids_ambientales='222')

    @unittest.skipUnless(sys.platform == 'win32', 'requiere intérpretes de Inicio de Windows')
    def test_ids_ausentes(self):
        """La falta de IDs termina antes de reservar o lanzar el gateway."""
        self.comprobar_rechazo('Faltan TELEGRAM_BOT_TOKEN', local='token-local-ficticio')


def lanzador_ficticio():
    """Observa la CLI real sin crear procesos de gateway ni usar Telegram."""
    argv = sys.argv[2:]
    sys.argv = ['adevv', *argv[1:]]
    with patch.object(gateway.motor, 'excluir'), \
            patch.object(gateway.subprocess, 'Popen') as proceso, \
            patch.object(gateway, 'escuchar') as escucha, \
            patch.object(gateway, 'pid_vivo', return_value=None):
        proceso.return_value.pid = 123456
        try:
            codigo = gateway.main()
        except SystemExit as error:
            print(str(error), flush=True)
            codigo = 1
        datos = {'argv': argv, 'cwd': str(Path.cwd()), 'procesos': proceso.call_count,
                 'escucha': escucha.call_count, 'pid': (Path.cwd() / gateway.PID).exists(),
                 'flags': proceso.call_args.kwargs.get('creationflags', 0) if proceso.called else 0}
        with Path(os.environ['ADEVV_OBSERVACION']).open('a', encoding='utf-8') as registro:
            registro.write(json.dumps(datos) + '\n')
    return codigo


if __name__ == '__main__':
    if '--lanzador' in sys.argv:
        sys.exit(lanzador_ficticio())
    unittest.main()
