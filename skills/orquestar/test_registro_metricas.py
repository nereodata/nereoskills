"""Regresiones de persistencia con registros sintéticos y productores independientes."""
import csv
import io
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import chdir, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from skills.orquestar.test_fallos_arnes import motor
from skills.telegram_gateway import gateway


SCRIPT = Path(motor.__file__).resolve()
ID = 'T-DEMO-0001'
CONSUMO = {'tipo': 'paso', 'id': ID, 'modelos': {'dev': {'entrada': 7}}, 'coste_usd': 0.25}
V1 = {'tipo': 'verificacion', 'id': ID, 'comando': 'V1'}
V2 = {**V1, 'comando': 'V2'}


def linea(objeto):
    return json.dumps(objeto, ensure_ascii=False).encode('utf-8') + b'\r\n'


def evento(tipo, numero):
    return {'tipo': tipo, 'numero': numero, 'texto': f'{tipo}/{numero} á中🌱' * 60}


def producir(root, tipo, barrera):
    with chdir(root):
        barrera.wait(timeout=30)
        for numero in range(100):
            motor.registrar(root, evento(tipo, numero))


def escribir_durante_recuperacion(root, publicando, solicitado):
    if not publicando.wait(30):
        raise RuntimeError('La recuperación no llegó a publicar')
    registrar = motor.registrar
    def anunciar(raiz, fila):
        solicitado.set()
        return registrar(raiz, fila)

    with chdir(root), patch.object(motor, 'registrar', anunciar):
        motor.registrar(root, V2)


class RegistroMetricasTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.ruta = self.root / motor.METRICAS
        self.mp = multiprocessing.get_context('spawn')

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root,
                              env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, encoding='utf-8',
                              capture_output=True, timeout=30)

    def proceso(self, funcion, *args):
        proceso = self.mp.Process(target=funcion, args=(self.root, *args))
        proceso.start()
        def limpiar():
            if proceso.is_alive():
                proceso.terminate()
            proceso.join(10)
            proceso.close()
        self.addCleanup(limpiar)
        return proceso

    def test_cola_parcial_sesion_y_cursor(self):
        sesion = dict(tipo='agente', rol='hades', id=ID, arnes='codex', sesion='S')
        datos = linea(V1)
        corte = datos.index(b'V1')
        self.ruta.write_bytes(linea(sesion) + datos[:corte])
        with patch.dict(os.environ, ORQUESTAR_ESCALADA=''):
            self.assertEqual(motor.buscar_sesion_agente(self.root, 'hades', ID, 'codex'), 'S')
        with redirect_stderr(io.StringIO()) as err:
            filas, cursor = motor.nuevas_metricas(self.root, 0)
        self.assertEqual(err.getvalue(), '')
        self.assertEqual(filas, [sesion])
        with self.ruta.open('ab') as salida:
            salida.write(datos[corte:])
        filas, cursor = motor.nuevas_metricas(self.root, cursor)
        self.assertEqual(filas, [V1])
        self.assertEqual(motor.nuevas_metricas(self.root, cursor)[0], [])

    def comprobar_totales(self):
        resultado = self.cli('--metricas', '--csv')
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        fila, = csv.DictReader(io.StringIO(resultado.stdout))
        self.assertEqual((fila['id'], int(fila['dev_tokens_originales']),
                          float(fila['coste_estimado_usd']), int(fila['verificaciones_totales'])),
                         (ID, 7, 0.25, 1))

    def filas_activas(self):
        with self.ruta.open('rb') as entrada:
            return [json.loads(linea.decode('utf-8')) for linea in entrada]

    def test_estado_exportacion_y_recuperacion_idempotente(self):
        for fragmento in (b'_s": 0}\n', b'\xff\n'):
            with self.subTest(fragmento=fragmento):
                original = linea(CONSUMO) + fragmento + linea(V1)
                self.ruta.write_bytes(original)
                with redirect_stdout(io.StringIO()) as estado, redirect_stderr(io.StringIO()) as error:
                    motor.resumen(self.root)
                self.assertIn('1 pasos', estado.getvalue())
                self.assertIn('1 verificaciones', estado.getvalue())
                self.assertRegex(error.getvalue(), r'orquestar_metricas\.jsonl[^\n]*línea 2')
                resultado = self.cli('--metricas', '--csv')
                self.assertNotEqual(resultado.returncode, 0)
                self.assertEqual(resultado.stdout, '')
                self.assertRegex(resultado.stderr, r'orquestar_metricas\.jsonl[^\n]*línea 2')
                self.assertEqual(self.ruta.read_bytes(), original)
                resultado = self.cli('--recuperar-metricas')
                self.assertEqual(resultado.returncode, 0, resultado.stderr)
                copia = next(p for p in self.root.rglob('*')
                             if p != self.ruta and p.is_file() and p.read_bytes() == original)
                self.assertEqual(self.filas_activas(), [CONSUMO, V1])
                self.comprobar_totales()
                resultado = self.cli('--recuperar-metricas')
                self.assertEqual(resultado.returncode, 0, resultado.stderr)
                self.assertEqual(copia.read_bytes(), original)
                self.assertEqual(self.filas_activas(), [CONSUMO, V1])
                self.comprobar_totales()

    def test_cursor_tras_recuperacion(self):
        self.ruta.write_bytes(linea(CONSUMO) + b'?\n' + linea(V1))
        filas, cursor = motor.nuevas_metricas(self.root, 0)
        self.assertEqual(filas, [CONSUMO, V1])
        resultado = self.cli('--recuperar-metricas')
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(self.filas_activas(), [CONSUMO, V1])
        with chdir(self.root):
            motor.registrar(self.root, V2)
        filas, cursor = motor.nuevas_metricas(self.root, cursor)
        self.assertEqual(filas, [V2])
        self.assertEqual(motor.nuevas_metricas(self.root, cursor)[0], [])

    def test_cuatro_productores_con_cola_interrumpida(self):
        fragmento = b'{"roto":"\xf0\x9f'
        self.ruta.write_bytes(linea(CONSUMO) + fragmento)
        tipos = ('paso', 'agente', 'verificacion', 'gateway')
        barrera = self.mp.Barrier(len(tipos))
        procesos = [self.proceso(producir, tipo, barrera) for tipo in tipos]
        for proceso in procesos:
            proceso.join(60)
            self.assertEqual(proceso.exitcode, 0)
        with redirect_stderr(io.StringIO()) as error:
            filas = motor.leer_metricas(self.root)
        self.assertRegex(error.getvalue(), r'orquestar_metricas\.jsonl[^\n]*línea 2')
        with self.ruta.open('rb') as entrada:
            self.assertEqual(json.loads(entrada.readline()), CONSUMO)
            self.assertIn(entrada.readline(), (fragmento + b'\n', fragmento + b'\r\n'))
        self.assertEqual(filas[0], CONSUMO)
        self.assertCountEqual(filas[1:], [evento(t, n) for t in tipos for n in range(100)])

    def test_agente_verificacion_y_gateway_delegan_en_registrar(self):
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        with (chdir(self.root), patch.dict(os.environ, ORQUESTAR_ID='', ORQUESTAR_PASO=''),
              patch.object(motor, 'buscar_ejecutable', return_value='arnes'),
              patch.object(motor, 'lanzar', return_value=(0, {'sesion': 'S'}, 'ok')),
              patch.object(motor, 'registrar', wraps=motor.registrar) as registro):
            self.assertEqual(motor.agente(self.root, 'clio', 'consulta'), 0)
            self.assertEqual(motor.verificar(self.root, 'echo prueba'), 0)
            agente, verificacion = [c.args[1] for c in registro.call_args_list]
            self.assertEqual((agente['tipo'], agente['rol'], agente['sesion']), ('agente', 'clio', 'S'))
            self.assertEqual((verificacion['tipo'], verificacion['comando']), ('verificacion', 'echo prueba'))
        with (chdir(self.root), patch.object(gateway.motor, 'buscar_ejecutable', return_value='arnes'),
              patch.object(gateway.motor, 'lanzar', return_value=(1, {}, 'usage limit reached resets in 1680s')),
              patch.object(gateway.motor, 'registrar', wraps=gateway.motor.registrar) as registro):
            with self.assertRaises(gateway.ModeloIndisponible):
                gateway.invocar(self.root, 'hola', {'harness': 'codex', 'model': 'm'})
            fila = registro.call_args.args[1]
            self.assertEqual((fila['tipo'], fila['modelo_cuota']), ('gateway', 'm'))
        self.assertEqual(self.filas_activas(), [agente, verificacion, fila])

    def test_escritura_coincide_con_publicacion_de_recuperacion(self):
        original = linea(CONSUMO) + b'\xff\n' + linea(V1)
        self.ruta.write_bytes(original)
        publicando, solicitado = self.mp.Event(), self.mp.Event()
        registro_metricas = motor.registro_metricas
        guardar = registro_metricas.guardar_evidencia
        proceso = self.proceso(escribir_durante_recuperacion, publicando, solicitado)
        def con_instantanea(*args):
            copia = guardar(*args)
            publicando.set()
            self.assertTrue(solicitado.wait(30), 'El escritor no solicitó el registro de E3')
            return copia

        with patch.object(registro_metricas, 'guardar_evidencia', con_instantanea):
            copia = motor.metricas.recuperar(self.root)
        proceso.join(30)
        self.assertEqual(proceso.exitcode, 0)
        self.assertTrue(publicando.is_set())
        self.assertEqual(copia.read_bytes(), original)
        self.assertEqual(motor.metricas.leer_registros(self.root), [CONSUMO, V1, V2])
