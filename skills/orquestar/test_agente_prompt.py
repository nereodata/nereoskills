"""Pruebas unitarias para el canal limpio de prompts en --agente (T-ADV-0017)."""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from tests import aislamiento_telegram

SPEC = importlib.util.spec_from_file_location('orquestar_motor', Path(__file__).with_name('orquestar.py'))
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


class AgentePromptTests(unittest.TestCase):
    """Verifica prioridades, fallback, exclusión git y auto-limpieza en finally."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        git_dir = self.root / '.git'
        git_dir.mkdir(parents=True, exist_ok=True)

    def test_propios_incluye_orquestar_prompt_txt(self):
        """orquestar_prompt.txt debe formar parte de PROPIOS para exclusión de git."""
        self.assertIn('orquestar_prompt.txt', motor.PROPIOS)

    def test_excluir_agrega_orquestar_prompt_txt(self):
        """excluir() debe añadir orquestar_prompt.txt a .git/info/exclude."""
        motor.excluir(self.root)
        exclude_file = self.root / '.git' / 'info' / 'exclude'
        self.assertTrue(exclude_file.exists())
        contenido = exclude_file.read_text(encoding='utf-8')
        self.assertIn('orquestar_prompt.txt', contenido)

    def test_es_fichero_rastreado_git_detecta_seguimiento(self):
        """es_fichero_rastreado_git devuelve True si git ls-files tiene éxito y False si falla."""
        with patch('subprocess.run') as mock_run:
            mock_res_ok = MagicMock(returncode=0, stderr='')
            mock_res_untracked = MagicMock(returncode=1, stderr="error: pathspec 'temporal.txt' did not match any file(s) known to git")

            mock_run.return_value = mock_res_ok
            self.assertTrue(motor.es_fichero_rastreado_git(self.root, self.root / 'seguido.txt'))
            mock_run.assert_called_with(
                ['git', 'ls-files', '--error-unmatch', '--', 'seguido.txt'],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False
            )

            mock_run.return_value = mock_res_untracked
            self.assertFalse(motor.es_fichero_rastreado_git(self.root, self.root / 'temporal.txt'))

    def test_es_fichero_rastreado_git_archivo_con_guiones(self):
        """Nombres de fichero que comienzan por guiones no deben colisionar con opciones de git."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr='')
            self.assertTrue(motor.es_fichero_rastreado_git(self.root, self.root / '--mandato.txt'))
            mock_run.assert_called_with(
                ['git', 'ls-files', '--error-unmatch', '--', '--mandato.txt'],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False
            )

    def test_es_fichero_rastreado_git_fallo_operativo_retorna_true(self):
        """Ante errores operacionales de git, se asume seguimiento para preservar el fichero."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stderr='fatal: not a git repository')
            self.assertTrue(motor.es_fichero_rastreado_git(self.root, self.root / 'duda.txt'))

            mock_run.return_value = MagicMock(returncode=1, stderr='error: git index locked')
            self.assertTrue(motor.es_fichero_rastreado_git(self.root, self.root / 'duda.txt'))

    def test_main_agente_con_prompt_directo_ignora_stdin(self):
        """--prompt pasa el texto directamente al agente sin leer stdin."""
        args = ['orquestar.py', '--agente', 'hades', '--prompt', 'Mandato directo para Hades']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'agente', return_value=0) as mock_agente:
            retorno = motor.main()
            self.assertEqual(retorno, 0)
            mock_agente.assert_called_once_with(self.root, 'hades', 'Mandato directo para Hades')

    def test_main_agente_prioridad_prompt_sobre_prompt_file(self):
        """--prompt prevalece sobre --prompt-file si ambos están presentes."""
        prompt_file = self.root / 'otro_mandato.txt'
        prompt_file.write_text('Contenido de archivo', encoding='utf-8')

        args = ['orquestar.py', '--agente', 'hades', '--prompt', 'Directo', '--prompt-file', str(prompt_file)]
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'agente', return_value=0) as mock_agente:
            retorno = motor.main()
            self.assertEqual(retorno, 0)
            mock_agente.assert_called_once_with(self.root, 'hades', 'Directo')

    def test_main_agente_prioridad_prompt_file_sobre_stdin(self):
        """--prompt-file prevalece sobre stdin cuando ambos están disponibles."""
        prompt_file = self.root / 'archivo_mandato.txt'
        prompt_file.write_text('Contenido del archivo', encoding='utf-8')

        args = ['orquestar.py', '--agente', 'hades', '--prompt-file', str(prompt_file)]
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin si hay --prompt-file')), \
             patch.object(motor, 'es_fichero_rastreado_git', return_value=True), \
             patch.object(motor, 'agente', return_value=0) as mock_agente:
            retorno = motor.main()
            self.assertEqual(retorno, 0)
            mock_agente.assert_called_once_with(self.root, 'hades', 'Contenido del archivo')

    def test_main_agente_fallback_a_stdin_valido(self):
        """Si no hay --prompt ni --prompt-file, lee el mandato desde stdin."""
        args = ['orquestar.py', '--agente', 'hades']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', return_value='Mandato desde stdin\n'), \
             patch.object(motor, 'agente', return_value=0) as mock_agente:
            retorno = motor.main()
            self.assertEqual(retorno, 0)
            mock_agente.assert_called_once_with(self.root, 'hades', 'Mandato desde stdin\n')

    def test_main_agente_prompt_directo_vacio_falla_sin_invocar_agente(self):
        """--prompt con texto en blanco debe fallar con SystemExit sin invocar al agente ni leer stdin."""
        args = ['orquestar.py', '--agente', 'hades', '--prompt', '   \t\n  ']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'agente') as mock_agente, \
             self.assertRaises(SystemExit) as ctx:
            motor.main()
        self.assertIn('Falta el mandato', str(ctx.exception))
        mock_agente.assert_not_called()

    def test_main_agente_prompt_file_vacio_falla_sin_invocar_agente(self):
        """--prompt-file con contenido en blanco debe fallar con SystemExit sin invocar al agente ni leer stdin."""
        prompt_file = self.root / 'vacio.txt'
        prompt_file.write_text('    \n', encoding='utf-8')

        args = ['orquestar.py', '--agente', 'hades', '--prompt-file', str(prompt_file)]
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'agente') as mock_agente, \
             self.assertRaises(SystemExit) as ctx:
            motor.main()
        self.assertIn('Falta el mandato', str(ctx.exception))
        mock_agente.assert_not_called()

    def test_main_agente_prompt_file_no_rastreado_en_raiz_se_elimina_tras_ejecucion(self):
        """--prompt-file temporal en la raíz existe durante la ejecución y se borra en finally."""
        prompt_file = self.root / 'mandato_temporal.txt'
        prompt_file.write_text('Contenido de prueba', encoding='utf-8')

        def validar_existencia_durante_agente(root_arg, rol_arg, prompt_arg):
            self.assertTrue(prompt_file.exists())
            self.assertEqual(prompt_arg, 'Contenido de prueba')
            return 0

        args = ['orquestar.py', '--agente', 'hades', '--prompt-file', 'mandato_temporal.txt']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'es_fichero_rastreado_git', return_value=False), \
             patch.object(motor, 'agente', side_effect=validar_existencia_durante_agente) as mock_agente:
            retorno = motor.main()
            self.assertEqual(retorno, 0)
            mock_agente.assert_called_once()
            self.assertFalse(prompt_file.exists())

    def test_main_agente_prompt_file_se_elimina_tras_systemexit_por_cuota(self):
        """El borrado en finally del prompt temporal opera ante SystemExit simulando falta de cuota."""
        prompt_file = self.root / 'orquestar_prompt.txt'
        prompt_file.write_text('Mandato cuota', encoding='utf-8')

        def simular_salida_cuota(root_arg, rol_arg, prompt_arg):
            self.assertTrue(prompt_file.exists())
            sys.exit(2)

        args = ['orquestar.py', '--agente', 'hades', '--prompt-file', 'orquestar_prompt.txt']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'es_fichero_rastreado_git', return_value=False), \
             patch.object(motor, 'agente', side_effect=simular_salida_cuota):
            with self.assertRaises(SystemExit) as ctx:
                motor.main()
            self.assertEqual(ctx.exception.code, 2)
            self.assertFalse(prompt_file.exists())

    def test_main_agente_prompt_file_se_elimina_tras_excepcion_ordinaria(self):
        """El borrado en finally del prompt temporal opera ante excepciones no controladas."""
        prompt_file = self.root / 'orquestar_prompt.txt'
        prompt_file.write_text('Mandato antes de fallo', encoding='utf-8')

        def simular_fallo(root_arg, rol_arg, prompt_arg):
            self.assertTrue(prompt_file.exists())
            raise RuntimeError('Fallo simulado')

        args = ['orquestar.py', '--agente', 'hades', '--prompt-file', 'orquestar_prompt.txt']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'es_fichero_rastreado_git', return_value=False), \
             patch.object(motor, 'agente', side_effect=simular_fallo):
            with self.assertRaises(RuntimeError):
                motor.main()
            self.assertFalse(prompt_file.exists())

    def test_main_agente_prompt_file_rastreado_no_se_elimina(self):
        """Si el fichero de prompt está rastreado por git, no debe ser eliminado."""
        prompt_file = self.root / 'mandato_oficial.txt'
        prompt_file.write_text('Mandato versionado', encoding='utf-8')

        args = ['orquestar.py', '--agente', 'hades', '--prompt-file', 'mandato_oficial.txt']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'es_fichero_rastreado_git', return_value=True), \
             patch.object(motor, 'agente', return_value=0):
            retorno = motor.main()
            self.assertEqual(retorno, 0)
            self.assertTrue(prompt_file.exists())
            self.assertEqual(prompt_file.read_text(encoding='utf-8'), 'Mandato versionado')

    def test_main_agente_prompt_file_con_guiones_rastreado_no_se_elimina(self):
        """Ficheros cuyo nombre empieza por guiones rastreados en git no se borran."""
        prompt_file = self.root / '--mandato.txt'
        prompt_file.write_text('Mandato con guiones', encoding='utf-8')

        args = ['orquestar.py', '--agente', 'hades', '--prompt-file=--mandato.txt']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'es_fichero_rastreado_git', return_value=True), \
             patch.object(motor, 'agente', return_value=0):
            retorno = motor.main()
            self.assertEqual(retorno, 0)
            self.assertTrue(prompt_file.exists())
            self.assertEqual(prompt_file.read_text(encoding='utf-8'), 'Mandato con guiones')

    def test_main_agente_prompt_file_fallo_git_preserva_archivo(self):
        """Ante un fallo operativo de git, el fichero se conserva por precaución."""
        prompt_file = self.root / 'posible_temporal.txt'
        prompt_file.write_text('Contenido preservado ante fallo git', encoding='utf-8')

        args = ['orquestar.py', '--agente', 'hades', '--prompt-file', 'posible_temporal.txt']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'es_fichero_rastreado_git', return_value=True), \
             patch.object(motor, 'agente', return_value=0):
            retorno = motor.main()
            self.assertEqual(retorno, 0)
            self.assertTrue(prompt_file.exists())

    def test_main_agente_prompt_file_en_subdirectorio_no_se_elimina(self):
        """Ficheros en subdirectorios no son borrados automáticamente."""
        subdir = self.root / 'subcarpeta'
        subdir.mkdir(parents=True, exist_ok=True)
        prompt_file = subdir / 'mandato_sub.txt'
        prompt_file.write_text('Mandato en subcarpeta', encoding='utf-8')

        args = ['orquestar.py', '--agente', 'hades', '--prompt-file', str(prompt_file)]
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
             patch.object(motor, 'es_fichero_rastreado_git', return_value=False), \
             patch.object(motor, 'agente', return_value=0):
            retorno = motor.main()
            self.assertEqual(retorno, 0)
            self.assertTrue(prompt_file.exists())

    def test_main_agente_prompt_file_externo_no_se_elimina(self):
        """Ficheros fuera del árbol del proyecto no deben ser eliminados."""
        with tempfile.TemporaryDirectory() as external_dir:
            external_file = Path(external_dir) / 'externo_mandato.txt'
            external_file.write_text('Mandato en directorio externo', encoding='utf-8')

            args = ['orquestar.py', '--agente', 'hades', '--prompt-file', str(external_file)]
            with patch.object(sys, 'argv', args), \
                 patch('pathlib.Path.cwd', return_value=self.root), \
                 patch('sys.stdin.read', side_effect=AssertionError('No debe leer de stdin')), \
                 patch.object(motor, 'es_fichero_rastreado_git', return_value=False), \
                 patch.object(motor, 'agente', return_value=0) as mock_agente:
                retorno = motor.main()
                self.assertEqual(retorno, 0)
                mock_agente.assert_called_once_with(self.root, 'hades', 'Mandato en directorio externo')
                self.assertTrue(external_file.exists())
                self.assertEqual(external_file.read_text(encoding='utf-8'), 'Mandato en directorio externo')

    def test_main_agente_sin_mandato_falla_sin_invocar_agente(self):
        """Si no se proporciona mandato, sys.exit con aviso y sin llamar al agente."""
        args = ['orquestar.py', '--agente', 'hades']
        with patch.object(sys, 'argv', args), \
             patch('pathlib.Path.cwd', return_value=self.root), \
             patch('sys.stdin.read', return_value='   '), \
             patch.object(motor, 'agente') as mock_agente, \
             self.assertRaises(SystemExit) as ctx:
            motor.main()
        self.assertIn('Falta el mandato', str(ctx.exception))
        mock_agente.assert_not_called()


if __name__ == '__main__':
    unittest.main()
