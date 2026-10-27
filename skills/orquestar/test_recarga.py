"""Contrato de recarga cooperativa sin red ni almacén real."""
import argparse
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from tests import aislamiento_telegram


SPEC = importlib.util.spec_from_file_location('motor_recarga', Path(__file__).with_name('orquestar.py'))
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


class RecargaTests(unittest.TestCase):
    """Detecta únicamente scripts del almacén y transfiere su propiedad."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.actual = self.root / 'versions/0.5.0/skills/orquestar/orquestar.py'
        self.nuevo = self.root / 'versions/0.6.0/skills/orquestar/orquestar.py'
        for script in (self.actual, self.nuevo):
            script.parent.mkdir(parents=True)
            script.touch()
        self.puntero('0.6.0')
        self.env = patch.dict(os.environ, {'ADEVV_HOME': str(self.root)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def puntero(self, version):
        (self.root / 'active.json').write_text(json.dumps({'version': version}), encoding='utf-8')

    def test_detecta_script_homologo_y_reversion(self):
        self.assertEqual(motor.version_activa_distinta(self.actual), (self.nuevo, '0.6.0'))
        self.puntero('0.5.0')
        self.assertEqual(motor.version_activa_distinta(self.nuevo), (self.actual, '0.5.0'))

    def test_no_recarga_sin_destino_valido(self):
        for valor in ('0.5.0', '../escape', '', None, {}, 'ausente'):
            with self.subTest(valor=valor):
                self.puntero(valor)
                self.assertIsNone(motor.version_activa_distinta(self.actual))
        for texto in ('{', '[]', '\ufffd'):
            (self.root / 'active.json').write_text(texto, encoding='utf-8')
            self.assertIsNone(motor.version_activa_distinta(self.actual))
        (self.root / 'active.json').unlink()
        self.assertIsNone(motor.version_activa_distinta(self.actual))

    def test_checkout_no_se_recarga(self):
        self.assertIsNone(motor.version_activa_distinta(Path(__file__).with_name('orquestar.py')))

    def test_transfiere_argumentos_raiz_estado_y_pid(self):
        (self.root / motor.PID).write_text(str(os.getpid()))
        hijo = Mock(pid=9876)
        estado = {'n': 3, 'sin_progreso': 1, 'esperado': 90}
        with patch.object(motor, '__file__', str(self.actual)), patch.object(motor.sys, 'argv', ['viejo', '--max-pasos', '8']), patch.object(motor.subprocess, 'Popen', return_value=hijo) as lanzar, patch('builtins.print') as imprimir:
            self.assertTrue(motor.recargar_version(self.actual, self.root, motor.PID, estado, 'orquestar'))
        imprimir.assert_called_once_with('[orquestar] recargado a versión 0.6.0', flush=True)
        args, opciones = lanzar.call_args
        self.assertEqual(args[0], [motor.sys.executable, '-u', str(self.nuevo), '--max-pasos', '8'])
        self.assertEqual(opciones['cwd'], self.root)
        self.assertEqual((self.root / motor.PID).read_text(), '9876')
        datos = json.loads(opciones['env']['ADEVV_RECARGA'])
        self.assertEqual(datos['estado'], estado)
        with patch.dict(os.environ, opciones['env']), patch.object(motor.os, 'getpid', return_value=9876):
            self.assertEqual(motor.recibir_recarga(self.root, motor.PID, self.nuevo), estado)
            self.assertNotIn('ADEVV_RECARGA', os.environ)

    def test_fallo_lanzamiento_conserva_pid(self):
        (self.root / motor.PID).write_text(str(os.getpid()))
        with patch.object(motor.subprocess, 'Popen', side_effect=OSError('fallo')):
            self.assertFalse(motor.recargar_version(self.actual, self.root, motor.PID, {}, 'orquestar'))
        self.assertEqual((self.root / motor.PID).read_text(), str(os.getpid()))

    def test_bucle_transfiere_antes_de_calcular_paso(self):
        a = argparse.Namespace(estado=False, idea=None, docs='docs', max_pasos=8,
                               recarga={'n': 3, 'sin_progreso': 1, 'esperado': 90})
        with patch.object(motor, 'iniciar_gateway'), patch.object(motor, 'suite', return_value=None), patch.object(motor, 'recargar_version', return_value=True, create=True) as recarga, patch.object(motor, 'estado') as estado:
            self.assertEqual(motor.bucle(a, self.root), 0)
        estado.assert_not_called()
        self.assertEqual(recarga.call_args.args[3], a.recarga)

    def test_parada_tiene_prioridad(self):
        (self.root / motor.PARADA).touch()
        a = argparse.Namespace(estado=False, idea=None, docs='docs', max_pasos=1)
        with patch.object(motor, 'iniciar_gateway'), patch.object(motor, 'suite', return_value=None), patch.object(motor, 'recargar_version', create=True) as recarga:
            self.assertEqual(motor.bucle(a, self.root), 2)
        recarga.assert_not_called()

    def test_fallo_publicacion_cancela_hijo_y_conserva_propietario(self):
        pid = self.root / motor.PID
        pid.write_text(str(os.getpid()))
        hijo = Mock(pid=9876)
        with patch.object(motor.subprocess, 'Popen', return_value=hijo), patch.object(motor.os, 'replace', side_effect=OSError('bloqueado')):
            self.assertFalse(motor.recargar_version(self.actual, self.root, motor.PID, {}, 'orquestar'))
        hijo.terminate.assert_called_once()
        hijo.wait.assert_called_once()
        self.assertEqual(pid.read_text(), str(os.getpid()))

    def test_main_antiguo_no_borra_marcas_del_sucesor(self):
        pid = self.root / motor.PID

        def transferir(a, root):
            pid.write_text('9876')
            (root / motor.PARADA).touch()
            return 0

        with patch.object(motor.sys, 'argv', ['orquestar']), patch.object(motor.sys, 'stdout'), patch.object(motor.sys, 'stderr'), patch.object(motor.Path, 'cwd', return_value=self.root), patch.object(motor, 'validar_lanzamiento_bucle'), patch.object(motor, 'excluir'), patch.object(motor, 'bucle', side_effect=transferir):
            self.assertEqual(motor.main(), 0)
        self.assertEqual(pid.read_text(), '9876')
        self.assertTrue((self.root / motor.PARADA).exists())

    def test_main_sucesor_reanuda_sin_validar_o_reservar(self):
        (self.root / motor.PID).write_text(str(os.getpid()))
        estado = {'n': 4, 'sin_progreso': 1, 'esperado': 20}
        with patch.object(motor.sys, 'argv', ['orquestar']), patch.object(motor.sys, 'stdout'), patch.object(motor.sys, 'stderr'), patch.object(motor.Path, 'cwd', return_value=self.root), patch.object(motor, 'recibir_recarga', return_value=estado), patch.object(motor, 'validar_lanzamiento_bucle') as validar, patch.object(motor, 'bucle', return_value=0) as bucle:
            self.assertEqual(motor.main(), 0)
        validar.assert_not_called()
        self.assertEqual(bucle.call_args.args[0].recarga, estado)

    def test_transferencia_real_de_proceso(self):
        fuente = str(Path(motor.__file__).resolve())
        carga = ('import importlib.util, json, os, sys\nfrom pathlib import Path\n'
                 f'spec = importlib.util.spec_from_file_location("motor", {fuente!r})\n'
                 'motor = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(motor)\n'
                 'root = Path.cwd()\n')
        self.actual.write_text(carga + '(root / motor.PID).write_text(str(os.getpid()))\n'
                               'original = motor.subprocess.Popen\nhijos = []\n'
                               'def lanzar(*args, **kwargs):\n    hijo = original(*args, **kwargs)\n    hijos.append(hijo)\n    return hijo\n'
                               'motor.subprocess.Popen = lanzar\n'
                               'assert motor.recargar_version(__file__, root, motor.PID, {"n": 4}, "orquestar")\n'
                               'try:\n    hijos[0].wait(timeout=10)\nfinally:\n    if hijos[0].poll() is None:\n        hijos[0].kill()\n        hijos[0].wait()\n', encoding='utf-8')
        self.nuevo.write_text(carga + 'estado = motor.recibir_recarga(root, motor.PID, __file__)\n'
                              '(root / "resultado.json").write_text(json.dumps({"estado": estado, "pid": os.getpid(), "args": sys.argv[1:]}))\n', encoding='utf-8')
        resultado = subprocess.run([motor.sys.executable, str(self.actual), '--docs', 'carpeta con espacios'], cwd=self.root, capture_output=True, timeout=15)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        datos = json.loads((self.root / 'resultado.json').read_text())
        self.assertEqual(datos['estado'], {'n': 4})
        self.assertEqual(datos['args'], ['--docs', 'carpeta con espacios'])
        self.assertEqual((self.root / motor.PID).read_text(), str(datos['pid']))
