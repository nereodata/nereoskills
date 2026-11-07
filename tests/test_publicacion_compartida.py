"""Contrato común de publicación con repositorios Git locales aislados."""

import subprocess
import unittest
from unittest.mock import patch

from adevv import release_tools
from skills.telegram_gateway import cierre_version
from tests import test_install_and_release as fixtures


class PublicacionCompartida(unittest.TestCase):
    """Comprueba atomicidad, rollback y consumidores de la política común."""

    setUp = fixtures.TestInstallAndRelease.setUp
    tearDown = fixtures.TestInstallAndRelease.tearDown

    def git(self, *args, remote=False):
        """Consulta el repositorio de prueba o su remoto bare."""
        root = self.origin_dir if remote else self.repo_dir
        return subprocess.run(['git', '-C', str(root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def preparar(self):
        """Crea una release con contenido diferente al main inicial."""
        self.git('checkout', '-b', 'release/v0.1')
        (self.repo_dir / 'CHANGELOG.md').write_text('## [0.1.0]\nCambios\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-m', 'release preparada')
        return self.git('rev-parse', 'main'), self.git('rev-parse', 'HEAD')

    def estado(self):
        """Captura referencias y árbol para comprobar rollback."""
        return (self.git('branch', '--show-current'), self.git('rev-parse', 'HEAD'),
                self.git('rev-parse', 'main'), self.git('tag'),
                self.git('status', '--porcelain'), self.git('rev-parse', 'main', remote=True),
                self.git('tag', remote=True))

    def test_push_atomico_y_tag_anotado(self):
        """Publica solo main y la etiqueta solicitada en una transacción."""
        self.preparar()
        self.git('tag', '-a', 'v9.9.9', '-m', 'ajena')
        release_tools.publicar_version(self.repo_dir, 'v0.1.0')
        self.assertEqual(self.git('tag', remote=True), 'v0.1.0')
        self.assertEqual(self.git('cat-file', '-t', 'v0.1.0', remote=True), 'tag')
        self.assertEqual(self.git('rev-parse', 'main', remote=True),
                         self.git('rev-parse', 'v0.1.0^{}', remote=True))

    def test_preflight_fallido_conserva_estado(self):
        """Un preflight fallido no modifica referencias ni árbol original."""
        self.preparar()
        config = self.repo_dir / 'task_config.yaml'
        config.write_text(config.read_text(encoding='utf-8') +
                          '  preflight:\n    - python -c "raise SystemExit(3)"\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-m', 'preflight fallido')
        antes = self.estado()
        with self.assertRaisesRegex(RuntimeError, 'preflight'):
            release_tools.publicar_version(self.repo_dir, 'v0.1.0')
        self.assertEqual(self.estado(), antes)

    def test_push_rechazado_conserva_estado(self):
        """Un remoto sin soporte atómico no recibe ninguna referencia."""
        self.preparar()
        self.git('config', 'receive.advertiseAtomic', 'false', remote=True)
        antes = self.estado()
        with self.assertRaises(RuntimeError):
            release_tools.publicar_version(self.repo_dir, 'v0.1.0')
        self.assertEqual(self.estado(), antes)

    def test_changelog_obligatorio(self):
        """Ambas entradas usan la misma validación de changelog."""
        with self.assertRaisesRegex(ValueError, 'changelog'):
            release_tools.validar_publicacion(self.repo_dir, 'v0.1.0')

    def test_manifiestos_desalineados(self):
        """Se validan los manifiestos además del paquete Python."""
        self.preparar()
        path = self.repo_dir / 'task_config.yaml'
        path.write_text(path.read_text(encoding='utf-8').replace('v0.1.0', 'v0.2.0'), encoding='utf-8')
        with self.assertRaises(ValueError):
            release_tools.validar_publicacion(self.repo_dir, 'v0.1.0')

    def test_telegram_delega_publicacion(self):
        """El adaptador no implementa otra transacción de publicación."""
        with patch.object(release_tools, 'publicar_version') as publicar, patch.object(cierre_version, 'git', return_value=''):
            cierre_version.publicar(self.repo_dir, 'release/v0.1', 'v0.1.0', {})
        publicar.assert_called_once_with(self.repo_dir, 'v0.1.0', rama='release/v0.1', cfg={})
