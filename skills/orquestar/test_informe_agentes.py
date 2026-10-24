"""Informe de agentes y cuota con entradas locales y reloj controlado."""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('informe_motor', Path(__file__).with_name('orquestar.py'))
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


class InformeTests(unittest.TestCase):
    """Cuotas visibles y consultas sin escrituras ni modelos reales."""

    def setUp(self):
        """Aísla sesiones, métricas y configuración."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sessions = self.root / 'codex' / 'sessions'
        self.sessions.mkdir(parents=True)
        self.enterContext(patch.dict(os.environ, {'CODEX_HOME': str(self.sessions.parent)}))
        self.enterContext(patch.object(motor, 'ahora', return_value='2026-10-24T12:00:00+00:00'))
        self.enterContext(patch.object(motor, 'estado', return_value=('FIN', 'Terminado')))
        self.cfg = {
            'artemisa': {'harness': 'codex', 'model': 'gpt-base', 'cuota_tokens_5h': 1000,
                         'dificultad': {'dificil': {'model': 'gpt-hard', 'reserva': {'model': 'gpt-reserve'}}},
                         'pasos': {'task-dev': {'model': 'gpt-step'}},
                         'reserva': {'harness': 'agy', 'model': 'flash', 'cuota_tokens_5h': 20000000}},
            'hades': {'harness': 'claude', 'model': 'sonnet'},
            'atenea': {'harness': 'agy', 'model': 'argon'},
            'clio': {'harness': 'agy', 'model': 'flash'},
            'cronos': {'harness': 'agy', 'model': 'pro'}}
        self.save_config()

    def save_config(self):
        """Guarda configuración de la fixture."""
        (self.root / motor.CONFIG).write_text(json.dumps(self.cfg), encoding='utf-8')

    def metrics(self, rows):
        """Escribe métricas conocidas."""
        (self.root / motor.METRICAS).write_text('\n'.join(map(json.dumps, rows)), encoding='utf-8')

    def native(self, name, timestamp, percent, reset):
        """Escribe un evento Codex de cuota primaria."""
        row = {'timestamp': timestamp, 'type': 'event_msg', 'payload': {
            'type': 'token_count', 'rate_limits': {'primary': {'used_percent': percent, 'resets_at': reset}}}}
        (self.sessions / name).write_text(json.dumps(row) + '\n{incompleto', encoding='utf-8')

    def test_roles_profiles_and_unique_percentages_even_when_stopped(self):
        """FIN y PARAR no ocultan ningún rol, variante o reserva."""
        for state in (('FIN', 'Terminado'), ('PARAR', 'Falta configuración')):
            with patch.object(motor, 'estado', return_value=state):
                output = motor.informe_agentes(self.root)
            for role in self.cfg:
                self.assertIn(role + ':', output)
            for model in ('gpt-base', 'gpt-hard', 'gpt-reserve', 'gpt-step', 'flash', 'argon', 'sonnet', 'pro'):
                self.assertIn(model, output)
            self.assertEqual(output.count('agy/flash: 0.0% consumido'), 1)
            self.assertIn('dificil', output)

    def test_window_limits_and_no_double_reasoning(self):
        """La frontera de 5 h incluye tokens y excluye antiguos y futuros."""
        self.metrics([
            {'fecha': '2026-10-24T07:00:00Z', 'arnes': 'codex', 'modelos': {
                'gpt-base': {'entrada': 100, 'cache_leida': 20, 'cache_escrita': 10, 'salida': 70, 'razonamiento': 70}}},
            {'fecha': '2026-10-24T06:59:59Z', 'arnes': 'codex', 'modelos': {'gpt-base': {'entrada': 900}}},
            {'fecha': '2026-10-24T12:00:01Z', 'arnes': 'codex', 'modelos': {'gpt-base': {'entrada': 900}}}])
        output = motor.informe_agentes(self.root)
        self.assertIn('codex/gpt-base: 20.0% consumido (200 / 1000 tokens en 5 h)', output)
        self.assertIn('0 / 20000000 tokens en 5 h', output)
        self.assertIn('0 / 5000000 tokens en 5 h', output)

    def test_native_latest_valid_and_exhaustion_precedence(self):
        """Nativo reciente vence estimación; agotamiento vigente vence nativo."""
        reset = datetime.fromisoformat('2026-10-24T13:00:00+00:00').timestamp()
        self.native('old.jsonl', '2026-10-24T11:00:00Z', 10, reset)
        self.native('new.jsonl', '2026-10-24T11:59:00Z', 42.5, reset)
        self.native('future.jsonl', '2026-10-24T12:01:00Z', 99, reset)
        self.assertIn('codex/gpt-base: 42.5% consumido · resetea', motor.informe_agentes(self.root))
        self.metrics([{'fecha': '2026-10-24T06:00:00Z', 'arnes': 'codex',
                       'modelo_cuota': 'gpt-base', 'cuota_espera_s': 25200}])
        self.assertIn('codex/gpt-base: 100.0% consumido (agotado hasta', motor.informe_agentes(self.root))
        self.assertIn('faltan 60 min', motor.informe_agentes(self.root))

    def test_expired_invalid_native_and_invalid_limits_fall_back(self):
        """Eventos caducados o inválidos no contaminan el cálculo local."""
        self.native('expired.jsonl', '2026-10-24T11:59:00Z', 75, 1)
        self.native('nan.jsonl', '2026-10-24T11:59:00Z', float('nan'), 9999999999)
        self.cfg['artemisa']['cuota_tokens_5h'] = -1
        self.save_config()
        self.assertIn('codex/gpt-base: 0.0% consumido (0 / 10000000 tokens en 5 h)', motor.informe_agentes(self.root))

    def test_effective_step_and_read_only_status(self):
        """El informe identifica perfil efectivo; estado omite agentes y cuotas."""
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch.object(motor, 'estado', return_value=('PASO', 'task-dev', 'T-ADV-0020', 'release/v0.5')), \
                patch.object(motor, 'dificultad_de', return_value='dificil'):
            self.assertIn('artemisa: codex/gpt-step', motor.informe_agentes(self.root))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                motor.resumen(self.root)
            for text in (motor.parte(self.root), output.getvalue()):
                self.assertNotIn('codex/', text)
                self.assertNotIn('Agentes para', text)
                self.assertNotIn('tokens (5 h)', text)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_cli_aliases_are_queries_without_initializing_project(self):
        """Ambos flags funcionan sin requisitos ni bucle y no escriben señales."""
        for flag in ('--agentes', '--agents'):
            result = subprocess.run([sys.executable, str(Path(motor.__file__)), flag], cwd=self.root,
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('gpt-base', result.stdout)
            self.assertIn('% consumido', result.stdout)
        self.assertFalse((self.root / motor.PID).exists())


if __name__ == '__main__':
    unittest.main()
