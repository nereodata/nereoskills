"""Comandos de agentes autorizados y separados del estado."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from skills.telegram_gateway import gateway
from tests import aislamiento_telegram


class AgentesTests(unittest.TestCase):
    """Telegram utiliza el informe común sin conversación ni arranque."""

    def test_aliases_help_authorization_and_signature(self):
        """Ambos alias exponen porcentajes y conservan firma y autorización."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(gateway.motor, 'informe_agentes', create=True,
                              return_value='artemisa: codex/gpt\ncodex/gpt: 42.5% consumido') as report, \
                    patch.object(gateway, 'conversar') as chat:
                for command in ('/agentes', '/agents@AdevvBot'):
                    response = gateway.responder(root, '1', command, {'1'})
                    self.assertIn('42.5% consumido', response)
                    self.assertIn('— Adevv v', response)
                self.assertEqual(report.call_count, 2)
                report.reset_mock()
                self.assertIsNone(gateway.responder(root, '2', '/agentes', {'1'}))
                report.assert_not_called()
                chat.assert_not_called()
            response = gateway.responder(root, '1', '/ayuda', {'1'})
            self.assertIn('/agentes', response)
            self.assertIn('/agents', response)
