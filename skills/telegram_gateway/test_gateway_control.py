"""Control remoto autorizado con proyectos temporales y sin procesos reales."""
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tests import aislamiento_telegram


SPEC = importlib.util.spec_from_file_location('gateway_control', Path(__file__).with_name('gateway.py'))
gateway = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gateway)
motor = gateway.motor


class ControlTests(unittest.TestCase):
    """Efectos y respuestas de comandos sin Telegram, red ni modelos."""

    def setUp(self):
        """Aísla archivos y todas las fronteras con procesos externos."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.excluir = self.enterContext(patch.object(motor, 'excluir'))
        self.conversar = self.enterContext(patch.object(gateway, 'conversar', return_value='CONVERSACION'))
        self.proceso = self.enterContext(patch.object(motor.subprocess, 'Popen'))
        self.proceso.return_value.pid = 321
        self.estado = self.enterContext(patch.object(motor, 'estado', return_value=(
            'PASO', 'task-dev', 'T-ADV-0015', 'release/v0.4')))

    def responder(self, texto, usuario='12345'):
        """Procesa un mensaje con un único usuario autorizado."""
        with redirect_stdout(io.StringIO()):
            return gateway.responder(self.root, usuario, texto, {'12345'})

    def pid(self):
        """Simula la marca de ejecución sin un proceso vivo."""
        (self.root / motor.PID).write_text('777', encoding='utf-8')

    def datos(self):
        """Genera backlog y consumo conocido de dos versiones."""
        carpeta = self.root / 'docs/plan/tasks'
        carpeta.mkdir(parents=True)
        for iid, ver in [('T-ADV-0010', 'v0.3.0'), ('T-ADV-0015', 'v0.4.0')]:
            (carpeta / f'{iid}.md').write_text(
                f'---\nid: {iid}\ntitle: Control\nstatus: planned\nversion: {ver}\n'
                'depende_de: []\n---\n', encoding='utf-8')
        registros = [dict(tipo='paso', id='T-ADV-0010', duracion_s=60),
                     dict(tipo='paso', id='T-ADV-0015', duracion_s=120, coste_usd=1.5,
                          modelos={'modelo': dict(entrada=100, cache_leida=20, salida=30,
                                                  razonamiento=10)}),
                     dict(tipo='agente', rol='hades', id='T-ADV-0015', duracion_s=60,
                          coste_usd=0.5, modelos={'otro': dict(entrada=40, cache_leida=5, salida=6)})]
        (self.root / motor.METRICAS).write_text(
            '\n'.join(json.dumps(r) for r in registros), encoding='utf-8')

    def test_parar_y_alias_solicitan_parada_despues_de_excluir(self):
        """La parada conserva PID y solo crea la señal tras excluirla."""
        self.pid()
        for comando in ('/parar', '/stop@AdevvBot'):
            with self.subTest(comando=comando):
                senal = self.root / motor.PARADA
                senal.unlink(missing_ok=True)
                self.excluir.side_effect = lambda root: self.assertFalse(senal.exists())
                respuesta = self.responder(comando)
                self.assertTrue(senal.exists())
                self.assertEqual((self.root / motor.PID).read_text(), '777')
                self.assertIn('paso en curso', respuesta)
        self.assertEqual(self.excluir.call_count, 2)
        self.proceso.assert_not_called()
        self.conversar.assert_not_called()

    def test_parar_sin_bucle_no_escribe(self):
        """Parar dos veces es informativo y no crea señales sin PID."""
        for comando in ('/parar', '/stop'):
            self.assertIn('ya está parado', self.responder(comando))
        self.assertEqual(list(self.root.iterdir()), [])
        self.excluir.assert_not_called()

    def test_lanzar_y_alias_anuncian_paso_y_no_heredan_argumentos_gateway(self):
        """Comprueba el arranque compartido hasta la frontera Popen."""
        for comando in ('/lanzar', '/run@AdevvBot'):
            with self.subTest(comando=comando), patch.object(
                    sys, 'argv', ['gateway.py', '--root', str(self.root), '--estado']):
                respuesta = self.responder(comando)
                self.assertIn('Lanzamiento solicitado', respuesta)
                self.assertIn('task-dev T-ADV-0015', respuesta)
                llamada = self.proceso.call_args
                self.assertEqual(llamada.args[0], [sys.executable, '-u', str(Path(motor.__file__).resolve())])
                self.assertEqual(llamada.kwargs['cwd'], self.root)
                self.assertEqual(llamada.kwargs['stdin'], motor.subprocess.DEVNULL)
                if motor.os.name == 'nt':
                    self.assertTrue(llamada.kwargs['creationflags'] & motor.subprocess.CREATE_NO_WINDOW)
        self.assertEqual(self.proceso.call_count, 2)
        self.conversar.assert_not_called()

    def test_lanzar_con_pid_no_crea_otro_proceso(self):
        """Un PID existente evita cualquier arranque o consulta adicional."""
        self.pid()
        for comando in ('/lanzar', '/run'):
            self.assertIn('ya está en marcha', self.responder(comando))
        self.proceso.assert_not_called()
        self.estado.assert_not_called()
        self.excluir.assert_not_called()

    def test_en_fondo_cli_conserva_argumentos(self):
        """El llamante CLI sigue heredando sus opciones sin --fondo."""
        with patch.object(sys, 'argv', ['orquestar.py', '--fondo', '--docs', 'requisitos', '--max-pasos', '2']), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(motor.en_fondo(self.root), 0)
        self.assertEqual(self.proceso.call_args.args[0][3:], ['--docs', 'requisitos', '--max-pasos', '2'])

    def test_fallo_al_lanzar_no_confirma_exito(self):
        """El fallo llega al manejador de errores existente del polling."""
        self.proceso.side_effect = OSError('sin recursos')
        with self.assertRaisesRegex(OSError, 'sin recursos'):
            self.responder('/lanzar')

    def test_metricas_por_defecto_ultima_con_calculo_real_y_sin_escrituras(self):
        """El coste y tiempo no duplican el consumo de Hades."""
        self.datos()
        self.pid()
        antes = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        respuesta = self.responder('/metricas')
        self.assertNotIn('T-ADV-0010', respuesta)
        self.assertIn('T-ADV-0015', respuesta)
        self.assertIn('v0.4', respuesta)
        self.assertIn('2.00 min', respuesta)
        self.assertIn('Dev E/C/S=100/20/30', respuesta)
        self.assertIn('Hades E/C/S=40/5/6', respuesta)
        self.assertIn('USD≈2.000000', respuesta)
        self.assertEqual(antes, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.excluir.assert_not_called()
        self.proceso.assert_not_called()
        self.conversar.assert_not_called()

    def test_metricas_alias_y_filtros(self):
        """Acepta los filtros del módulo compartido y sufijos de bot."""
        self.datos()
        for comando in ('/metrics v0.3,v0.4', '/metricas@AdevvBot last:2', '/metrics todas'):
            with self.subTest(comando=comando):
                respuesta = self.responder(comando)
                self.assertIn('T-ADV-0010', respuesta)
                self.assertIn('T-ADV-0015', respuesta)
        self.assertNotIn('T-ADV-0015', self.responder('/metricas v0.3'))

    def test_metricas_sin_datos_y_errores(self):
        """Sin resultados parciales ante errores de filtro, lectura o JSONL."""
        self.assertIn('Sin métricas', self.responder('/metricas'))
        self.datos()
        self.assertIn('inválido', self.responder('/metrics invalido'))
        with (self.root / motor.METRICAS).open('a', encoding='utf-8') as out:
            out.write('\n{no es json}')
        respuesta = self.responder('/metricas')
        self.assertIn('línea 4', respuesta)
        self.assertNotIn('T-ADV-0015', respuesta)
        with patch.object(Path, 'open', side_effect=OSError('lectura denegada')):
            self.assertIn('lectura denegada', self.responder('/metricas'))

    def test_no_autorizados_no_invocan_motores_ni_leen_archivos(self):
        """La autorización precede incluso a las consultas de disco."""
        with patch.object(Path, 'exists', side_effect=AssertionError('lectura no autorizada')):
            for comando in ('/lanzar', '/run', '/parar', '/stop', '/metricas', '/metrics todas'):
                self.assertIsNone(self.responder(comando, '999'))
        self.proceso.assert_not_called()
        self.estado.assert_not_called()
        self.conversar.assert_not_called()

    def test_ayuda_documenta_comandos_alias_y_defecto(self):
        """Los comandos y su filtro son descubribles desde /ayuda."""
        respuesta = self.responder('/ayuda')
        for termino in ('/lanzar', '/run', '/parar', '/stop', '/metricas', '/metrics', 'ultima'):
            self.assertIn(termino, respuesta)


if __name__ == '__main__':
    unittest.main()
