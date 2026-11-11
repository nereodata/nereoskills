"""Pruebas unitarias para reanudación de sesión codex y cálculo neto de tokens cacheados (B-ADV-0004)."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from tests import aislamiento_telegram

SPEC = importlib.util.spec_from_file_location('orquestar_motor', Path(__file__).with_name('orquestar.py'))
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


def es_subsecuencia_contigua(sublista, lista):
    """Verifica si sublista aparece como elementos consecutivos en lista."""
    n = len(sublista)
    return any(lista[i:i + n] == sublista for i in range(len(lista) - n + 1))


class EntornoRolTests(unittest.TestCase):
    """Observa el comando y entorno entregados al crear el proceso de Hades."""

    marca = 'CODEX_WINDOWS_REGISTERED_CORE'

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.padre = {self.marca: '1', 'CODEX_WINDOWS_SANDBOX_PACKAGE_FAMILY': 'familia',
                      'CODEX_APP_TOOLS_PIPE_PATH': 'pipe-de-prueba', 'PROYECTO': 'ejemplo'}
        self.enterContext(patch.dict(os.environ, self.padre, clear=True))
        self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda nombre: nombre))
        self.enterContext(patch.object(motor, 'construir_prompt_agente', return_value='revisa'))
        self.enterContext(patch.object(motor, 'registrar'))
        self.procesos = []

    def lanzar_rol(self, plataforma='nt', sesion=None, codigos=(0,), arnes='codex'):
        def proceso(cmd, **kwargs):
            self.assertEqual(dict(os.environ), self.padre)
            entorno = kwargs.get('env')
            self.procesos.append((cmd, dict(os.environ if entorno is None else entorno)))
            hijo = MagicMock()
            hijo.returncode = codigos[len(self.procesos) - 1]
            hijo.stdout = iter(())
            return hijo

        def captura(cmd, **kwargs):
            hijo = proceso(cmd, **kwargs)
            hijo.stdout, hijo.stderr = '{"result": "revisado"}', ''
            return hijo

        (self.root / 'orchestration.json').write_text(json.dumps({'hades': {'harness': arnes}}),
                                                      encoding='utf-8')
        with (patch.object(motor, 'os', wraps=os) as sistema,
              patch.object(motor, 'buscar_sesion_agente', return_value=sesion),
              patch.object(motor.subprocess, 'Popen', side_effect=proceso),
              patch.object(motor.subprocess, 'run', side_effect=captura)):
            sistema.name, sistema.environ = plataforma, os.environ
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)
        self.assertEqual(dict(os.environ), self.padre)

    def comprobar_codex_windows(self, reanudaciones):
        self.assertEqual(len(self.procesos), len(reanudaciones))
        for (cmd, entorno), reanudada in zip(self.procesos, reanudaciones):
            self.assertEqual(entorno, {k: v for k, v in self.padre.items() if k != self.marca})
            self.assertEqual(cmd[:2], ['codex', 'exec'])
            self.assertEqual('resume' in cmd, reanudada)
            sandbox = ['-c', 'sandbox_mode="workspace-write"'] if reanudada else ['--sandbox', 'workspace-write']
            self.assertTrue(es_subsecuencia_contigua(sandbox, cmd))
            self.assertTrue(es_subsecuencia_contigua(['-c', 'approval_policy="never"'], cmd))
            self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', cmd)
            self.assertNotIn('--skip-git-repo-check', cmd)
            if reanudada:
                self.assertTrue(es_subsecuencia_contigua(['resume', 'sesion-previa'], cmd))

    def test_sesion_nueva(self):
        self.lanzar_rol()
        self.comprobar_codex_windows([False])

    def test_sesion_reanudada(self):
        self.lanzar_rol(sesion='sesion-previa')
        self.comprobar_codex_windows([True])

    def test_recuperacion_con_sesion_nueva(self):
        self.lanzar_rol(sesion='sesion-previa', codigos=(1, 0))
        self.comprobar_codex_windows([True, False])

    def test_windows_sin_marca(self):
        del self.padre[self.marca]
        del os.environ[self.marca]
        self.lanzar_rol()
        self.comprobar_codex_windows([False])

    def test_codex_fuera_de_windows(self):
        self.lanzar_rol(plataforma='posix')
        self.assertEqual([env for cmd, env in self.procesos], [self.padre])

    def test_otro_arnes_en_windows(self):
        self.lanzar_rol(arnes='claude')
        self.assertEqual([env for cmd, env in self.procesos], [self.padre])


class CodexResumeAndUsageTests(unittest.TestCase):
    """Verifica comando sin --sandbox en reanudación y resta de cached_input_tokens en entrada."""

    def test_base_comando_agente_codex_sin_sesion_mantiene_sandbox(self):
        """Sin sesión previa, codex exec usa '--sandbox', 'workspace-write' consecutivo."""
        cmd = motor.base_comando_agente('codex', 'prompt', sesion=None)
        self.assertTrue(es_subsecuencia_contigua(['--sandbox', 'workspace-write'], cmd),
                        f"Debe contener la subsecuencia ['--sandbox', 'workspace-write']: {cmd}")
        self.assertNotIn('resume', cmd)

    def test_base_comando_agente_codex_con_sesion_usa_sandbox_mode_config_sin_flag_sandbox(self):
        """Con sesión previa, codex exec resume usa -c sandbox_mode='workspace-write' y rechaza flag --sandbox."""
        cmd = motor.base_comando_agente('codex', 'prompt', sesion='th_12345')
        self.assertIn('resume', cmd)
        self.assertIn('th_12345', cmd)
        self.assertNotIn('--sandbox', cmd, "codex exec resume no admite el flag '--sandbox'")
        self.assertTrue(es_subsecuencia_contigua(['-c', 'sandbox_mode="workspace-write"'], cmd),
                        f"Debe contener la subsecuencia ['-c', 'sandbox_mode=\"workspace-write\"']: {cmd}")

    def test_lanzar_codex_resta_cached_input_tokens_de_entrada(self):
        """En codex, entrada reporta tokens netos (input_tokens - cached_input_tokens) para evitar doble cómputo."""
        eventos = [
            json.dumps({"type": "thread.started", "thread_id": "th_12345"}),
            json.dumps({"type": "turn.completed", "usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 800,
                "output_tokens": 50,
                "cache_write_input_tokens": 10,
                "reasoning_output_tokens": 5
            }})
        ]
        salida_lineas = [e + '\n' for e in eventos]

        mock_popen = MagicMock()
        mock_popen.__enter__.return_value = mock_popen
        mock_popen.stdout = iter(salida_lineas)
        mock_popen.returncode = 0

        with patch('subprocess.Popen', return_value=mock_popen):
            codigo, m, _ = motor.lanzar(['codex', 'exec', '--model', 'gpt-6.1-sol'], Path.cwd(), 'codex')

        self.assertEqual(codigo, 0)
        self.assertEqual(m['sesion'], 'th_12345')
        modelo_stats = m['modelos']['gpt-6.1-sol']
        self.assertEqual(modelo_stats['entrada'], 200, "Debe ser 1000 - 800 = 200")
        self.assertEqual(modelo_stats['cache_leida'], 800)
        self.assertEqual(modelo_stats['salida'], 50)

    def test_lanzar_codex_limite_max_cero_cuando_cache_supera_entrada(self):
        """Si cached_input_tokens supera a input_tokens, entrada debe ser 0 por max(0, ...)."""
        eventos = [
            json.dumps({"type": "turn.completed", "usage": {
                "input_tokens": 100,
                "cached_input_tokens": 300,
                "output_tokens": 10
            }})
        ]
        salida_lineas = [e + '\n' for e in eventos]

        mock_popen = MagicMock()
        mock_popen.__enter__.return_value = mock_popen
        mock_popen.stdout = iter(salida_lineas)
        mock_popen.returncode = 0

        with patch('subprocess.Popen', return_value=mock_popen):
            codigo, m, _ = motor.lanzar(['codex', 'exec', '--model', 'gpt-6.1-sol'], Path.cwd(), 'codex')

        self.assertEqual(codigo, 0)
        modelo_stats = m['modelos']['gpt-6.1-sol']
        self.assertEqual(modelo_stats['entrada'], 0, "No debe permitir valores negativos: max(0, 100 - 300) == 0")
        self.assertEqual(modelo_stats['cache_leida'], 300)

    def test_lanzar_codex_casos_limite_ausentes_y_nulos(self):
        """Verifica comportamiento con claves ausentes o con valor None en usage."""
        casos = [
            ({"input_tokens": 500, "cached_input_tokens": 0}, 500),
            ({"input_tokens": 500, "cached_input_tokens": None}, 500),
            ({"input_tokens": 500}, 500),
            ({"input_tokens": None, "cached_input_tokens": 50}, 0),
            ({"cached_input_tokens": 50}, 0),
        ]
        for uso_parcial, entrada_esperada in casos:
            with self.subTest(uso=uso_parcial):
                eventos = [json.dumps({"type": "turn.completed", "usage": uso_parcial})]
                salida_lineas = [e + '\n' for e in eventos]

                mock_popen = MagicMock()
                mock_popen.__enter__.return_value = mock_popen
                mock_popen.stdout = iter(salida_lineas)
                mock_popen.returncode = 0

                with patch('subprocess.Popen', return_value=mock_popen):
                    codigo, m, _ = motor.lanzar(['codex', 'exec', '--model', 'gpt-6.1-sol'], Path.cwd(), 'codex')

                self.assertEqual(codigo, 0)
                modelo_stats = m['modelos']['gpt-6.1-sol']
                self.assertEqual(modelo_stats['entrada'], entrada_esperada)


if __name__ == '__main__':
    unittest.main()
