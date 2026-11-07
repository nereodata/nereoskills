"""Reservas del bucle con comandos, sesiones y métricas reales y arneses simulados."""
import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('motor_reservas_arnes', Path(__file__).with_name('orquestar.py'))
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


class ReservasArnesTests(unittest.TestCase):
    """Observa la frontera de lanzamiento sin simular ejecutar ni comando."""

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.args = argparse.Namespace(idea=None, docs='docs', test=None, harness='codex',
            estado=False, max_pasos=2, reintentos=2, espera_max=2, cmd=None,
            presupuesto=None, reintentos_arnes=0)
        self.principal = {'harness': 'codex', 'model': 'gpt-6.1-sol', 'effort': 'max'}
        self.reservas = [
            {'harness': 'agy', 'model': 'gemini-4-argon', 'effort': 'high'},
            {'harness': 'claude', 'model': 'claude-opus-5-5', 'effort': 'high'}]
        self.enterContext(patch.dict(motor.os.environ, {}, clear=True))
        for nombre in ('iniciar_gateway', 'excluir', 'avisar'):
            self.enterContext(patch.object(motor, nombre))
        self.enterContext(patch.object(motor, 'ingerir', return_value=[]))
        self.enterContext(patch.object(motor, 'recargar_version', return_value=False))
        self.enterContext(patch.object(motor, 'comprobar_promocion', return_value=(False, '')))
        self.enterContext(patch.object(motor, 'dificultad_de', return_value='dificil'))
        self.enterContext(patch.object(motor, 'construir_prompt_paso', return_value='trabajo'))
        self.enterContext(patch.object(motor, 'git', return_value=''))
        self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe))
        self.esperar = self.enterContext(patch.object(motor, 'esperar', return_value=False))
        self.enterContext(patch('builtins.print'))

    def correr(self, rol='artemisa'):
        """Cada perfil salvo el último agota cuota; el último completa el paso."""
        cfg = {**self.principal, 'reserva': self.reservas}
        (self.root / motor.CONFIG).write_text(json.dumps({rol: {'dificultad': {'dificil': cfg}}}), encoding='utf-8')
        motor.registrar(self.root, {'tipo': 'paso', 'paso': 'bug-fix', 'id': 'B-ADV-0029',
            'arnes': 'codex', 'modelo': 'gpt-6.1-sol', 'sin_cuota': True, 'sesion': 'codex-previa'})
        llamadas = []

        def lanzar(cmd, root, harness, entrada=None, env=None):
            llamadas.append((cmd, harness))
            indice = len(llamadas) - 1
            return (0 if indice == len(self.reservas) else 1,
                    {'sesion': f'sesion-{indice}'},
                    'ok' if indice == len(self.reservas) else 'quota exceeded; resets in 1h')

        with (patch.object(motor, 'estado', side_effect=[('PASO', 'bug-fix', 'B-ADV-0029', ''), ('FIN', 'ok')]),
              patch.object(motor, 'firma', side_effect=['antes', 'despues']),
              patch.object(motor, 'lanzar', side_effect=lanzar)):
            self.assertEqual(motor.bucle(self.args, self.root), 0)
        self.esperar.assert_not_called()
        filas = [f for f in motor.leer_metricas(self.root) if f.get('tipo') == 'paso'][1:]
        return llamadas, filas

    def test_reservas_cambian_comando_sesion_y_metricas_con_y_sin_cli(self):
        for rol in ('development', 'artemisa'):
            for forzado in ('codex', None):
                with self.subTest(rol=rol, forzado=forzado):
                    (self.root / motor.METRICAS).unlink(missing_ok=True)
                    self.args.harness = forzado
                    llamadas, filas = self.correr(rol)
                    self.assertEqual([h for _, h in llamadas], ['codex', 'agy', 'claude'])
                    self.assertEqual([cmd[0] for cmd, _ in llamadas], ['codex', 'agy', 'claude'])
                    self.assertIn('codex-previa', llamadas[0][0])
                    self.assertIn('resume', llamadas[0][0])
                    self.assertIn('gpt-6.1-sol', llamadas[0][0])
                    self.assertIn('model_reasoning_effort="max"', llamadas[0][0])
                    for indice, modelo in ((1, 'gemini-4-argon'), (2, 'claude-opus-5-5')):
                        cmd = llamadas[indice][0]
                        self.assertEqual(cmd[cmd.index('--model') + 1], modelo)
                        self.assertEqual(cmd[cmd.index('--effort') + 1], 'high')
                        self.assertNotIn('--resume', cmd)
                        self.assertNotIn('--conversation', cmd)
                        self.assertNotIn('codex-previa', cmd)
                        self.assertNotIn(f'sesion-{indice - 1}', cmd)
                    self.assertEqual([(f['arnes'], f['modelo'], f['sesion']) for f in filas], [
                        ('codex', 'gpt-6.1-sol', 'sesion-0'),
                        ('agy', 'gemini-4-argon', 'sesion-1'),
                        ('claude', 'claude-opus-5-5', 'sesion-2')])
                    self.assertTrue(all(f.get('sin_cuota') for f in filas[:2]))
                    self.assertFalse(filas[-1].get('sin_cuota', False))
                    self.assertEqual(self.args.harness, forzado)

    def test_reserva_del_mismo_arnes_hereda_esfuerzo_y_reanuda(self):
        self.reservas = [{'model': 'gpt-6-luna'}]
        llamadas, filas = self.correr()
        self.assertEqual([h for _, h in llamadas], ['codex', 'codex'])
        cmd = llamadas[1][0]
        self.assertIn('resume', cmd)
        self.assertIn('sesion-0', cmd)
        self.assertIn('gpt-6-luna', cmd)
        self.assertIn('model_reasoning_effort="max"', cmd)
        self.assertEqual((filas[1]['arnes'], filas[1]['modelo']), ('codex', 'gpt-6-luna'))

    def test_forzado_distinto_no_atribuye_modelo_del_principal_original(self):
        self.principal = {'harness': 'agy', 'model': 'gemini-4-argon', 'effort': 'high'}
        self.reservas = [self.reservas[-1]]
        llamadas, filas = self.correr()
        self.assertEqual([h for _, h in llamadas], ['codex', 'claude'])
        self.assertNotIn('gemini-4-argon', llamadas[0][0])
        self.assertNotIn('model_reasoning_effort="high"', llamadas[0][0])
        self.assertEqual((filas[0]['arnes'], filas[0]['modelo']), ('codex', 'predeterminado'))
        self.assertIn('claude-opus-5-5', llamadas[1][0])
        self.assertNotIn('sesion-0', llamadas[1][0])


if __name__ == '__main__':
    unittest.main()
