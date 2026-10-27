"""Regresiones del aislamiento común de las pruebas frente a Telegram (B-ADV-0019)."""

import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tests import aislamiento_telegram


class AislamientoTelegramTests(unittest.TestCase):
    """El entorno de pruebas no conserva credenciales y no deja salir mensajes."""

    def test_entorno_sin_credenciales_de_telegram(self):
        """Tras importar el soporte no queda ninguna variable TELEGRAM_*."""
        for clave in aislamiento_telegram.CLAVES:
            self.assertNotIn(clave, os.environ)

    def test_credenciales_se_quitan_aunque_el_proceso_las_herede(self):
        """Un proceso que hereda el token lo pierde al cargar el soporte."""
        raiz = Path(__file__).resolve().parents[1]
        entorno = {**os.environ, 'TELEGRAM_BOT_TOKEN': 'heredado', 'TELEGRAM_ALLOWED_USER_IDS': '1', 'TELEGRAM_CHAT_ID': '1'}
        codigo = ("import os; from tests import aislamiento_telegram; "
                  "print(any(k in os.environ for k in aislamiento_telegram.CLAVES))")
        salida = subprocess.run([sys.executable, '-c', codigo], cwd=raiz, env=entorno,
                                capture_output=True, text=True, check=True, timeout=30)
        self.assertEqual(salida.stdout.strip(), 'False')

    def test_llamada_real_a_telegram_aborta_en_voz_alta(self):
        """`enviar()` no puede tragarse el bloqueo: aborta la ejecución."""
        import urllib.request
        with self.assertRaises(aislamiento_telegram.EnvioRealBloqueado):
            urllib.request.urlopen('https://api.telegram.org/botX/sendMessage', b'', timeout=1)

    def test_otras_urls_se_delegan(self):
        """El envoltorio solo bloquea Telegram."""
        original = MagicMock(return_value='respuesta')
        urlopen = aislamiento_telegram.proteger(original)
        self.assertEqual(urlopen('http://localhost/x', timeout=1), 'respuesta')
        original.assert_called_once_with('http://localhost/x', timeout=1)

    def test_pruebas_pueden_simular_el_envio(self):
        """Un `patch` de urlopen sigue funcionando con credenciales propias de la prueba."""
        with patch('urllib.request.urlopen', side_effect=OSError('sin red')) as urlopen:
            import urllib.request
            with self.assertRaises(OSError):
                urllib.request.urlopen('https://api.telegram.org/botX/sendMessage')
            urlopen.assert_called_once()


if __name__ == '__main__':
    unittest.main()
