"""Regresiones de B-ADV-0015: un árbol sucio no para el cambio de rama."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills.orquestar import orquestar


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


class CambioDeRamaSucioTests(unittest.TestCase):
    """Con cambios pendientes, el bucle los resuelve o los guarda en un stash."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for c in (['init', '-q', '-b', 'main'], ['config', 'user.email', 'a@b.c'], ['config', 'user.name', 'T']):
            git(self.root, *c)
        (self.root / 'a.txt').write_text('a', encoding='utf-8')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-q', '-m', 'init')
        git(self.root, 'branch', 'release/v1.0')
        self.cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.cwd)

    def test_clio_commitea_y_se_cambia_de_rama(self):
        def clio(root, rol, prompt):
            git(root, 'add', '.')
            git(root, 'commit', '-q', '-m', 'wip')
        (self.root / 'b.txt').write_text('b', encoding='utf-8')
        with patch.object(orquestar, 'agente', clio):
            self.assertTrue(orquestar.cambiar_de_rama(self.root, 'release/v1.0'))
        self.assertEqual(git(self.root, 'branch', '--show-current'), 'release/v1.0')
        self.assertEqual(git(self.root, 'stash', 'list'), '')

    def test_sin_resolver_se_guarda_en_stash_y_avisa(self):
        (self.root / 'b.txt').write_text('b', encoding='utf-8')
        with patch.object(orquestar, 'agente', side_effect=SystemExit('sin arnés')), \
                patch.object(orquestar, 'avisar') as avisar:
            self.assertTrue(orquestar.cambiar_de_rama(self.root, 'release/v1.0'))
        self.assertEqual(git(self.root, 'branch', '--show-current'), 'release/v1.0')
        self.assertIn('orquestar: main', git(self.root, 'stash', 'list'))
        self.assertFalse((self.root / 'b.txt').exists())
        self.assertIn('stash', avisar.call_args[0][2])

    def test_arbol_limpio_no_lanza_a_clio(self):
        with patch.object(orquestar, 'agente') as ag:
            self.assertTrue(orquestar.cambiar_de_rama(self.root, 'release/v1.0'))
        ag.assert_not_called()


if __name__ == '__main__':
    unittest.main()
