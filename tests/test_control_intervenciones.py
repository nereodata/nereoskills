"""B-ADV-0034: control CLI local y dominio durable compartido con Telegram."""

import importlib.util
import io
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests import aislamiento_telegram
from tests.test_telegram_gateway import gateway


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/orquestar/orquestar.py'
motor = gateway.motor
IID = 'T-ADV-0101'
QID = 'Q-ADV-0001'
EN_FONDO_REAL = motor.en_fondo
PID_VIVO_REAL = motor.pid_vivo


class ControlIntervencionesTests(unittest.TestCase):
    """Git y persistencia reales; transporte y lanzamiento aislados."""

    def setUp(self):
        self.entorno = {k: v for k, v in os.environ.items() if not k.startswith('TELEGRAM_')}
        self.entorno['PYTHONUTF8'] = '1'
        self.tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.tmp)
        for args in (('init', '-q'), ('config', 'user.email', 'test@test'),
                     ('config', 'user.name', 'Test'), ('checkout', '-qb', 'hotfix/v1.1.2')):
            self.git(*args)
        (self.root / 'task_config.yaml').write_text('project:\n  prefix: ADV\n', encoding='utf-8')
        self.tarea = self.root / f'docs/plan/tasks/{IID}.md'
        self.tarea.parent.mkdir(parents=True)
        self.tarea.write_text('---\nid: T-ADV-0101\nversion: v1.1.2\nstatus: planned\n'
                              'depende_de: []\n---\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.enterContext(patch.object(motor, 'git', side_effect=self.git))
        self.aviso = self.enterContext(patch.object(motor, 'avisar', return_value=False))
        self.enterContext(patch.object(motor, 'telegram', return_value=None))
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
        self.pid = self.enterContext(patch.object(motor, 'pid_vivo', return_value=None))
        self.estado = self.enterContext(patch.object(motor, 'estado', return_value=(
            'PARAR', 'Bloqueo de tarea; faltan decisiones')))
        self.lanzar = self.enterContext(patch.object(motor, 'en_fondo', return_value=0))
        motor.solicitar_intervencion(self.root, IID, 'Indicar proveedor', aislar=False)
        self.registro = self.root / motor.intervencion.PREGUNTAS

    def git(self, *args):
        """Ejecuta Git real en la fixture y decodifica su salida UTF-8."""
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              capture_output=True, text=True, encoding='utf-8').stdout.strip()

    def preguntas(self):
        return json.loads(self.registro.read_text(encoding='utf-8'))

    def cli(self, referencia=QID, texto='Usar OAuth interno'):
        salida = io.StringIO()
        with (patch.object(Path, 'cwd', return_value=self.root),
              patch.object(sys, 'argv', ['orquestar', '--responder', referencia, texto]),
              patch.object(sys, 'stdout', salida), patch.object(sys, 'stderr', io.StringIO())):
            salida.reconfigure = lambda **kwargs: None
            sys.stderr.reconfigure = lambda **kwargs: None
            try:
                codigo = motor.main()
            except SystemExit as error:
                codigo = error.code
        return codigo, salida.getvalue()

    def telegram(self, texto, usuario='111'):
        return gateway.responder(self.root, usuario, '/responder ' + texto, {'111'})

    def test_cli_real_sin_telegram_consulta_recibe_dato_y_deduplica(self):
        """El parser real permite Q-ID e ID de tarea sin ejecutar el texto."""
        (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
        texto = '$(touch ejecutado); Usar OAuth interno'
        for referencia in (QID, IID):
            with self.subTest(referencia=referencia):
                antes = self.git('rev-parse', 'HEAD')
                consulta = subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPT), '--preguntas'], cwd=self.root,
                                          capture_output=True, text=True, encoding='utf-8', env=self.entorno)
                self.assertEqual(consulta.returncode, 0, consulta.stderr)
                self.assertIn(QID, consulta.stdout)
                resultado = subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPT), '--responder', referencia, texto],
                                           cwd=self.root, capture_output=True, text=True, encoding='utf-8', env=self.entorno)
                self.assertEqual(resultado.returncode, 0, resultado.stderr)
                self.assertIn('recibida' if referencia == QID else 'duplicada', resultado.stdout)
                self.assertEqual(self.git('rev-parse', 'HEAD'), antes)
                self.assertEqual(self.git('diff', 'HEAD'), '')
        q = self.preguntas()[0]
        self.assertEqual(q['recibidas'], [texto])
        self.assertEqual(len(q['cola']), 1)
        self.assertTrue(q['cola'][0]['usuario'].startswith('local:'))
        self.assertFalse((self.root / 'ejecutado').exists())
        self.pid.return_value = os.getpid()
        self.assertIn('duplicada', self.telegram(QID + ' ' + texto))
        self.assertEqual(len(self.preguntas()[0]['cola']), 1)
        self.lanzar.assert_not_called()

    def test_rechazos_no_mutan_preguntas_ni_tareas(self):
        """Referencia estricta CLI, cierres y ambigüedad conservan los datos."""
        motor.solicitar_intervencion(self.root, IID, 'Indicar puerto', aislar=False)
        datos = self.preguntas()
        cerrada = dict(datos[0], id='Q-ADV-0003', estado='incorporada')
        datos.append(cerrada)
        motor.intervencion.guardar(self.registro, datos)
        for ref, texto, diagnostico in ((QID, '  ', 'Falta la respuesta'),
                                       ('Q-ADV-9999', 'dato', 'no existe'),
                                       ('Q-OTRO-0001', 'dato', 'no pertenece'),
                                       (IID, 'dato', 'ambigua'),
                                       ('Q-ADV-0003', 'dato', 'cerrada'),
                                       ('cualquier', 'dato', 'no existe')):
            with self.subTest(ref=ref, texto=texto):
                antes = self.registro.read_bytes(), self.tarea.read_bytes(), self.git('rev-parse', 'HEAD')
                codigo, salida = self.cli(ref, texto)
                self.assertIn(diagnostico, salida)
                self.assertEqual(antes, (self.registro.read_bytes(), self.tarea.read_bytes(), self.git('rev-parse', 'HEAD')))
        self.lanzar.assert_not_called()

    def test_telegram_no_autorizado_no_consulta_ni_responde(self):
        antes = self.registro.read_bytes()
        for texto in ('/preguntas', '/responder ' + QID + ' dato'):
            self.assertIsNone(gateway.responder(self.root, '999', texto, {'111'}))
        self.assertEqual(self.registro.read_bytes(), antes)

    def test_incorporacion_cli_y_cerrada_no_relanzan_dos_veces(self):
        codigo, salida = self.cli()
        self.assertEqual(codigo, 0)
        self.assertIn('reanudada', salida)
        self.assertEqual(self.preguntas()[0]['estado'], 'incorporada')
        self.assertEqual(motor.frontmatter(self.tarea)['status'], 'planned')
        self.assertNotIn('pendiente_de', motor.frontmatter(self.tarea))
        self.lanzar.assert_called_once_with(self.root, argumentos=[])
        self.assertIn('cerrada', self.telegram(QID + ' Usar OAuth interno'))
        self.assertEqual(motor.incorporar_respuestas(self.root), [])
        self.lanzar.assert_called_once()

    def test_reinicio_tras_recepcion_incorpora_una_vez(self):
        self.pid.return_value = 42
        self.assertIn('recibida', self.cli()[1])
        self.assertEqual(motor.frontmatter(self.tarea)['status'], 'blocked')
        self.pid.return_value = None
        spec = importlib.util.spec_from_file_location('motor_reiniciado', SCRIPT)
        nuevo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nuevo)
        with patch.object(nuevo, 'avisar', return_value=False):
            self.assertEqual(len(nuevo.incorporar_respuestas(self.root)), 1)
            contexto = self.tarea.read_text(encoding='utf-8')
            self.assertEqual(contexto.count('Usar OAuth interno'), 1)
            cabeza = self.git('rev-parse', 'HEAD')
            self.assertEqual(nuevo.incorporar_respuestas(self.root), [])
            self.assertEqual(self.git('rev-parse', 'HEAD'), cabeza)
            self.assertEqual(self.tarea.read_text(encoding='utf-8'), contexto)
        self.assertEqual(self.preguntas()[0]['estado'], 'incorporada')

    def test_parada_manual_impide_relanzar(self):
        (self.root / motor.PARADA).touch()
        self.assertIn('parada manual', self.cli()[1])
        self.assertFalse(any('reanudada' in str(c) for c in self.aviso.call_args_list))
        self.assertTrue(any('incorporada' in str(c) for c in self.aviso.call_args_list))
        self.assertIn('Usar OAuth interno', self.registro.read_text(encoding='utf-8'))
        self.lanzar.assert_not_called()

    def test_insuficiente_conserva_bloqueo_y_motivo(self):
        for texto, motivo in (('PENDIENTE: falta URL', 'falta URL'),
                              ('INSUFICIENTE: falta puerto', 'falta puerto')):
            with self.subTest(texto=texto):
                self.assertIn(motivo, self.cli(texto=texto)[1])
                self.assertEqual(self.preguntas()[0]['estado'], 'pendiente')
                self.assertEqual(motor.frontmatter(self.tarea)['status'], 'blocked')
                self.assertEqual(self.preguntas()[0]['motivo_insuficiente'], motivo)
        self.lanzar.assert_not_called()

    def test_otra_pregunta_conserva_bloqueo(self):
        motor.solicitar_intervencion(self.root, IID, 'Indicar puerto', aislar=False)
        self.assertIn('otra pregunta', self.cli()[1])
        self.assertEqual(motor.frontmatter(self.tarea)['status'], 'blocked')
        self.assertEqual([q['estado'] for q in self.preguntas()], ['incorporada', 'pendiente'])
        self.lanzar.assert_not_called()

    def test_dependencia_pendiente_no_anuncia_elegibilidad(self):
        self.tarea.write_text(self.tarea.read_text(encoding='utf-8').replace(
            'depende_de: []', 'depende_de: [T-ADV-0100]'), encoding='utf-8')
        dependencia = self.tarea.with_name('T-ADV-0100.md')
        dependencia.write_text('---\nid: T-ADV-0100\nversion: v1.1.2\nstatus: blocked\n'
                               'depende_de: []\n---\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'dependencia')
        salida = self.cli()[1]
        self.assertIn('dependencias', salida)
        self.assertFalse(any('reanudada' in str(c) for c in self.aviso.call_args_list))
        self.assertTrue(any('incorporada' in str(c) for c in self.aviso.call_args_list))
        self.assertNotIn('elegible', salida)
        self.assertNotIn('reanudada', salida)
        self.assertEqual(self.preguntas()[0]['estado'], 'incorporada')
        self.lanzar.assert_not_called()

    def test_reserva_pid_visible_antes_de_segunda_respuesta(self):
        """El hijo simulado no publica su PID: debe reservarlo el lanzador."""
        otra = self.tarea.with_name('T-ADV-0102.md')
        otra.write_text('---\nid: T-ADV-0102\nversion: v1.1.2\nstatus: planned\n'
                        'depende_de: []\n---\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'otra tarea')
        segunda = motor.solicitar_intervencion(self.root, 'T-ADV-0102', 'Indicar URL', aislar=False)
        self.pid.side_effect = PID_VIVO_REAL
        self.lanzar.side_effect = EN_FONDO_REAL
        original = subprocess.Popen
        lanzamientos = []
        def iniciar(args, **kwargs):
            if len(args) >= 3 and args[0] == sys.executable and args[1] == '-u':
                lanzamientos.append(args)
                return SimpleNamespace(pid=os.getpid())
            return original(args, **kwargs)
        with patch.object(subprocess, 'Popen', side_effect=iniciar):
            self.assertIn('reanudada', self.cli()[1])
            self.assertEqual((self.root / motor.PID).read_text(encoding='utf-8'), str(os.getpid()))
            self.assertIn('recibida', self.telegram(segunda['id'] + ' https://servicio.invalid'))
        self.assertEqual(len(lanzamientos), 1)
        self.lanzar.assert_called_once()
        self.assertEqual(motor.frontmatter(otra)['status'], 'blocked')
        self.assertEqual(len(self.preguntas()[1]['cola']), 1)

    def test_fallo_de_lanzamiento_no_deja_reserva(self):
        original = subprocess.Popen
        def iniciar(args, **kwargs):
            if len(args) >= 3 and args[0] == sys.executable and args[1] == '-u':
                raise OSError('fallo de arranque controlado')
            return original(args, **kwargs)
        with patch.object(subprocess, 'Popen', side_effect=iniciar):
            with self.assertRaisesRegex(OSError, 'fallo de arranque'):
                EN_FONDO_REAL(self.root, argumentos=[])
        self.assertFalse((self.root / motor.PID).exists())

    def test_hijo_acepta_titularidad_pid_publicada_por_padre(self):
        """El proceso hijo debe aceptar su propio PID reservado, sin ejecutar tareas."""
        (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
        self.pid.side_effect = PID_VIVO_REAL
        en_bucle = [False]
        unlink_original = Path.unlink
        escribir_original = Path.write_text
        def unlink(ruta, *args, **kwargs):
            if ruta == self.root / motor.PID and not en_bucle[0]:
                self.fail('La reserva desaparece antes de entrar al bucle')
            return unlink_original(ruta, *args, **kwargs)
        def escribir(ruta, *args, **kwargs):
            if ruta == self.root / motor.PID and not en_bucle[0]:
                self.fail('La reserva aceptada vuelve a publicarse antes del bucle')
            return escribir_original(ruta, *args, **kwargs)
        def ejecutar_bucle(*args):
            en_bucle[0] = True
            self.assertEqual((self.root / motor.PID).read_text(encoding='utf-8'), str(os.getpid()))
            return 0
        salida = io.StringIO()
        with (patch.object(Path, 'cwd', return_value=self.root),
              patch.object(sys, 'argv', ['orquestar', '--max-pasos', '0']),
              patch.object(sys, 'stdout', salida), patch.object(sys, 'stderr', io.StringIO()),
              patch.object(motor, 'validar_lanzamiento_bucle'),
              patch.object(motor, 'recibir_recarga', return_value=None),
              patch.object(Path, 'unlink', unlink), patch.object(Path, 'write_text', escribir),
              patch.object(motor, 'bucle', side_effect=ejecutar_bucle) as bucle):
            salida.reconfigure = lambda **kwargs: None
            sys.stderr.reconfigure = lambda **kwargs: None
            codigo = motor.main()
        self.assertEqual(codigo, 0)
        bucle.assert_called_once()
        self.assertFalse((self.root / motor.PID).exists())

    def test_concurrencia_de_canales_y_aislamiento_de_raices(self):
        """Procesos independientes compiten por el mismo bloqueo SO."""
        with tempfile.TemporaryDirectory() as directorio:
            segunda = Path(directorio)
            subprocess.run(['git', 'clone', '-q', str(self.root), str(segunda)], check=True)
            motor.intervencion.guardar(segunda / motor.intervencion.PREGUNTAS,
                                      [dict(self.preguntas()[0], proyecto=str(segunda.resolve()))])
            intacto = (segunda / motor.intervencion.PREGUNTAS).read_bytes()
            (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
            codigo = r"""
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, sys.argv[1])
from tests.test_telegram_gateway import gateway
motor = gateway.motor
canal = sys.argv[2]
original_leer = motor.intervencion.leer
original_bloqueo = motor.intervencion.bloqueo
primera = True
primer_intento = True
@contextmanager
def bloqueo(*args, **kwargs):
    global primer_intento
    if primer_intento:
        primer_intento = False
        print('ATTEMPT', flush=True)
    with original_bloqueo(*args, **kwargs):
        yield
def leer(root):
    global primera
    resultado = original_leer(root)
    if primera:
        primera = False
        print('READ', flush=True)
        if canal == 'cli':
            sys.stdin.readline()
    return resultado
motor.intervencion.bloqueo = bloqueo
motor.intervencion.leer = leer
if canal == 'cli':
    sys.argv = ['orquestar', '--responder', 'Q-ADV-0001', 'Usar OAuth interno']
    motor.main()
else:
    print(gateway.responder(Path.cwd(), '111', '/responder Q-ADV-0001 Usar OAuth interno', {'111'}))
"""
            procesos = []
            salidas = []
            eventos = queue.Queue()
            def lector(proceso, canal):
                for linea in proceso.stdout:
                    eventos.put((canal, linea.strip()))
            def iniciar(canal):
                proceso = subprocess.Popen(
                    [sys.executable, '-X', 'utf8', '-c', codigo, str(SCRIPT.parents[2]), canal],
                    cwd=self.root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, encoding='utf-8', env=self.entorno)
                procesos.append(proceso)
                hilo = threading.Thread(target=lector, args=(proceso, canal), daemon=True)
                hilo.start()
                return proceso, hilo
            try:
                primero, hilo1 = iniciar('cli')
                self.assertEqual(eventos.get(timeout=15), ('cli', 'ATTEMPT'))
                self.assertEqual(eventos.get(timeout=15), ('cli', 'READ'))
                segundo, hilo2 = iniciar('telegram')
                self.assertEqual(eventos.get(timeout=15), ('telegram', 'ATTEMPT'))
                with self.assertRaises(queue.Empty):
                    eventos.get(timeout=1)
                primero.stdin.write('continuar\n')
                primero.stdin.flush()
                for proceso in procesos:
                    proceso.wait(timeout=15)
                hilo1.join(timeout=5)
                hilo2.join(timeout=5)
                while not eventos.empty():
                    salidas.append(eventos.get_nowait()[1])
                for proceso in procesos:
                    self.assertEqual(proceso.returncode, 0, proceso.stderr.read())
            finally:
                for proceso in procesos:
                    if proceso.poll() is None:
                        proceso.kill()
                    proceso.wait(timeout=15)
                    for flujo in (proceso.stdin, proceso.stdout, proceso.stderr):
                        flujo.close()
            self.assertEqual(sum('duplicada' in s for s in salidas), 1)
            self.assertEqual(len(self.preguntas()[0]['cola']), 1)
            self.assertEqual((segunda / motor.intervencion.PREGUNTAS).read_bytes(), intacto)


if __name__ == '__main__':
    unittest.main()
