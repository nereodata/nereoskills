"""Estado operativo compartido entre CLI y Telegram (T-ADV-0014)."""
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from tests import aislamiento_telegram

SPEC = importlib.util.spec_from_file_location('motor_estado', Path(__file__).with_name('orquestar.py'))
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


class EstadoAgentesTests(unittest.TestCase):
    """Contrato del informe de agentes, con reloj fijo y sin red."""

    def setUp(self):
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cfg = {
            'artemisa': {'harness': 'codex', 'model': 'base', 'effort': 'low',
                         'dificultad': {'dificil': {'model': 'hard'}},
                         'pasos': {'task-dev': {'effort': 'high'}},
                         'reserva': {'model': 'backup'},
                         'escalada': {'rechazos': 2, 'model': 'super'}},
            'atenea': {'harness': 'agy', 'model': 'planner'},
            'hades': {'harness': 'claude', 'model': 'review',
                      'dificultad': {'dificil': {'effort': 'high'}},
                      'reserva': [{'model': 'review-backup'}]}}
        (self.root / motor.CONFIG).write_text(json.dumps(self.cfg), encoding='utf-8')

    def outputs(self, step='task-dev', kind='PASO'):
        """Consulta el helper histórico tras separar el estado conciso."""
        with (patch.object(motor, 'estado', return_value=(kind, step, 'T-ADV-0014', 'release/v0.4')),
              patch.object(motor, 'dificultad_de', return_value='dificil'),
              patch.object(motor, 'backlog', return_value=[]),
              patch.object(motor, 'ahora', return_value='2026-10-23T12:00:00+00:00')):
            return (motor.informe_agentes(self.root, 'docs/requirements'),)

    def metrics(self, rows):
        (self.root / motor.METRICAS).write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')

    def test_effective_agents_and_inherited_reserves(self):
        for output in self.outputs():
            for expected in ('dificil', 'artemisa: codex/hard (high)',
                             'codex/backup (high)', 'hades: claude/review (high)',
                             'claude/review-backup (high)'):
                self.assertIn(expected, output)
        for output in self.outputs(step='work-plan'):
            informe_paso = output.split('Agentes para')[-1]
            self.assertIn('atenea: agy/planner', informe_paso)
            self.assertNotIn('artemisa:', informe_paso)

    def test_escalated_agent(self):
        self.metrics([{'tipo': 'agente', 'rol': 'hades', 'id': 'T-ADV-0014',
                       'veredicto': 'RECHAZADO'}] * 2)
        for output in self.outputs():
            self.assertIn('artemisa: codex/super (high)', output)
            self.assertIn('escalada', output)
            self.assertIn('codex/backup (high)', output)

    def test_window_and_quota_before_reserve_without_double_reasoning(self):
        self.cfg['artemisa']['model'] = 'm1'
        (self.root / motor.CONFIG).write_text(json.dumps(self.cfg), encoding='utf-8')
        self.metrics([
            {'fecha': '2026-10-23T07:00:00+00:00', 'arnes': 'codex',
             'modelos': {'m1': {'entrada': 100, 'cache_leida': 20, 'salida': 30, 'razonamiento': 10}}},
            {'fecha': '2026-10-23T06:59:59+00:00', 'arnes': 'codex',
             'modelos': {'m1': {'entrada': 900}}},
            {'fecha': '2026-10-23T12:00:01+00:00', 'arnes': 'codex',
             'modelos': {'m1': {'entrada': 900}}},
            {'fecha': '2026-10-23T13:50:00+02:00', 'arnes': 'codex',
             'modelo_cuota': 'm1', 'cuota_espera_s': 1800}])
        for output in self.outputs():
            self.assertIn('codex/m1: 100.0% consumido (agotado hasta', output)
            self.assertIn('agotado hasta', output)
            self.assertIn(datetime.fromisoformat('2026-10-23T12:20:00+00:00').astimezone().strftime('%H:%M'), output)
            self.assertIn('20 min', output)
            self.assertIn('codex/hard: 0.0% consumido (0 / 10000000 tokens en 5 h)', output)
            self.assertIn('codex/hard: 0.0% consumido', output)

    def test_expired_quota_and_global_wait(self):
        self.cfg['artemisa']['model'] = 'm1'
        (self.root / motor.CONFIG).write_text(json.dumps(self.cfg), encoding='utf-8')
        self.metrics([{'fecha': '2026-10-23T11:00:00+00:00', 'arnes': 'codex',
                       'modelos': {'m1': {}}, 'sin_cuota': True, 'espera_s': 60}])
        (self.root / motor.ESPERA).write_text('2026-10-23T12:15:00+00:00', encoding='utf-8')
        for output in self.outputs():
            self.assertIn('Espera global:', output)
            self.assertIn('15 min', output)
            cuota = next(line for line in output.splitlines() if line.startswith('codex/m1:'))
            self.assertIn('codex/m1: 0.0% consumido (0 / 10000000 tokens en 5 h)', cuota)
            self.assertNotIn('agotado', cuota)

    def test_no_step_or_metrics(self):
        for output in self.outputs(kind='FIN'):
            self.assertNotIn('Agentes para', output)
            self.assertIn('codex/base: 0.0% consumido', output)

    def test_read_only_and_legacy_quota(self):
        self.cfg['hades'] = {'harness': 'claude', 'model': 'old'}
        (self.root / motor.CONFIG).write_text(json.dumps(self.cfg), encoding='utf-8')
        self.metrics([{'fecha': '2026-10-23T11:50:00+00:00', 'arnes': 'claude',
                       'modelos': {'old': {'cache_escrita': 4}},
                       'sin_cuota': True, 'espera_s': 1800}])
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        for output in self.outputs():
            self.assertIn('claude/old: 100.0% consumido (agotado hasta', output)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_agent_records_each_quota_even_without_reported_usage(self):
        cfg = {'hades': {'harness': 'claude', 'model': 'first', 'reserva': {'model': 'second'}}}
        with (patch.object(motor, 'config', return_value=cfg),
              patch.dict(motor.os.environ, {'ORQUESTAR_ID': 'T-ADV-0014', 'ORQUESTAR_PASO': 'task-dev'}),
              patch.object(motor.shutil, 'which', side_effect=lambda x: x),
              patch.object(motor, 'lanzar', side_effect=[(1, {}, 'usage limit'), (1, {}, 'usage limit')]),
              patch.object(motor, 'excluir'), patch('builtins.print')):
            self.assertEqual(motor.agente(self.root, 'hades', 'review'), 1)
        rows = [json.loads(line) for line in (self.root / motor.METRICAS).read_text().splitlines()]
        self.assertEqual([r.get('modelo_cuota') for r in rows], ['first', 'second'])
        self.assertTrue(all(r.get('cuota_espera_s') == 300 for r in rows))
        self.assertNotIn('sin_cuota', rows[0])
        self.assertEqual(rows[1]['espera_s'], 300)

    def test_loop_records_each_quota_before_using_reserve(self):
        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None, estado=False,
                                       max_pasos=2, reintentos=2, espera_max=2, cmd=None)
        cfg = {'artemisa': {'harness': 'codex', 'model': 'first', 'reserva': {'model': 'second'}}}
        with (patch.object(motor, 'config', return_value=cfg),
              patch.object(motor, 'estado', side_effect=[('PASO', 'task-dev', 'T-ADV-0014', ''), ('FIN', 'done')]),
              patch.object(motor, 'ejecutar', side_effect=[(1, {}, 'usage limit'), (0, {}, 'ok')]),
              patch.object(motor, 'firma', side_effect=['a', 'b', 'b']),
              patch.object(motor, 'git', return_value=''), patch.object(motor, 'ingerir', return_value=[]),
              patch.object(motor, 'avisar'), patch.object(motor, 'excluir'), patch('builtins.print')):
            self.assertEqual(motor.bucle(args, self.root), 0)
        rows = [json.loads(line) for line in (self.root / motor.METRICAS).read_text().splitlines()]
        self.assertEqual(rows[0].get('modelo_cuota'), 'first')
        self.assertEqual(rows[0].get('cuota_espera_s'), 300)
        self.assertNotIn('modelo_cuota', rows[1])


if __name__ == '__main__':
    unittest.main()
