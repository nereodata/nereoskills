import io
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from skills.orquestar import orquestar
from tests import aislamiento_telegram


class TestFirmaTelegram(unittest.TestCase):
    """Pruebas unitarias para la resolución de versión y firma de mensajes en el orquestador."""

    def test_version_adevv_desde_almacen_versiones(self):
        """Deduce la versión a partir de la ruta del script en ~/.adevv/versions/<ver>/..."""
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            script = home / 'versions' / '0.6.2' / 'skills' / 'orquestar' / 'orquestar.py'
            script.parent.mkdir(parents=True, exist_ok=True)
            script.touch()
            with patch.dict('os.environ', {'ADEVV_HOME': str(home)}):
                ver = orquestar.version_adevv(script)
                self.assertEqual(ver, '0.6.2')

    def test_version_adevv_desde_paquete_prevalece_sobre_pyproject(self):
        """La versión de adevv.__version__ prevalece sobre pyproject.toml fuera del almacén."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            script = d / 'skills' / 'orquestar' / 'orquestar.py'
            script.parent.mkdir(parents=True, exist_ok=True)
            script.touch()
            (d / 'pyproject.toml').write_text('[project]\nversion = "0.8.0"\n', encoding='utf-8')

            mock_adevv = types.ModuleType('adevv')
            mock_adevv.__version__ = '0.7.0'

            with patch.dict('sys.modules', {'adevv': mock_adevv}):
                ver = orquestar.version_adevv(script)
                self.assertEqual(ver, '0.7.0')

    def test_version_adevv_desde_pyproject_sin_paquete(self):
        """Obtiene la versión desde pyproject.toml si el paquete adevv no está disponible."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            script = d / 'skills' / 'orquestar' / 'orquestar.py'
            script.parent.mkdir(parents=True, exist_ok=True)
            script.touch()
            (d / 'pyproject.toml').write_text('[project]\nversion = "0.8.0"\n', encoding='utf-8')

            with patch.dict('sys.modules', {'adevv': None}):
                ver = orquestar.version_adevv(script)
                self.assertEqual(ver, '0.8.0')

    def test_version_adevv_defecto_sin_fuentes(self):
        """Aplica la versión por defecto cuando no hay almacén, paquete ni pyproject."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            script = d / 'script.py'
            script.touch()

            with patch.dict('sys.modules', {'adevv': None}):
                ver = orquestar.version_adevv(script)
                self.assertEqual(ver, 'desconocida')

    def test_firmar_formato_basico(self):
        """Añade la firma estándar con em-dash y versión al pie de un mensaje."""
        texto = 'Aviso de prueba del bucle'
        with patch.object(orquestar, 'version_adevv', return_value='0.5.0', create=True):
            firmado = orquestar.firmar(texto)
            self.assertEqual(firmado, f'{texto}\n\n— Adevv v0.5.0')

    def test_firmar_con_extra_arnes_y_modelo(self):
        """Añade arnés y modelo separados por punto medio cuando se proporciona el parámetro extra."""
        texto = 'Respuesta del modelo'
        with patch.object(orquestar, 'version_adevv', return_value='0.5.0', create=True):
            firmado = orquestar.firmar(texto, extra='agy/gemini-4-argon-medium')
            self.assertEqual(firmado, f'{texto}\n\n— Adevv v0.5.0 · agy/gemini-4-argon-medium')

    def test_tiene_firma_distingue_mencion_en_cuerpo_de_firma_final(self):
        """Distingue menciones intermedias de una firma final y no bloquea el firmado al pie."""
        cuerpo = 'Texto con mención — Adevv v0.4.0 en el cuerpo.\nSegunda línea de texto'
        self.assertFalse(orquestar.tiene_firma(cuerpo))

        with patch.object(orquestar, 'version_adevv', return_value='0.5.0', create=True):
            self.assertEqual(orquestar.firmar(cuerpo), f'{cuerpo}\n\n— Adevv v0.5.0')

        # Firmas finales reales
        final_std = 'Texto informativo\n\n— Adevv v0.5.0'
        self.assertTrue(orquestar.tiene_firma(final_std))
        self.assertEqual(orquestar.firmar(final_std), final_std)

        final_extra = 'Texto conversacional\n\n— Adevv v0.5.0 · agy/gemini-4-argon-medium'
        self.assertTrue(orquestar.tiene_firma(final_extra))
        self.assertEqual(orquestar.firmar(final_extra), final_extra)

        final_trail = 'Texto\n\n— Adevv v0.5.0  \n'
        self.assertTrue(orquestar.tiene_firma(final_trail))
        self.assertEqual(orquestar.firmar(final_trail), final_trail)

        # Sin firma
        self.assertFalse(orquestar.tiene_firma('Mensaje que menciona Adevv v0.5.0 sin firma'))
        self.assertFalse(orquestar.tiene_firma(''))
        self.assertFalse(orquestar.tiene_firma(None))

    def test_avisar_incluye_firma_de_version(self):
        """avisar() añade la firma de versión al pie de los avisos enviados."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = ('token-falso', ['12345'], ['version', 'error'])
            with patch.object(orquestar, 'version_adevv', return_value='0.5.0', create=True), \
                 patch.object(orquestar, 'telegram', return_value=cfg), \
                 patch.object(orquestar, 'enviar', return_value=True) as mock_enviar:
                ok = orquestar.avisar(root, 'version', 'Versión finalizada.')
                self.assertTrue(ok)
                mock_enviar.assert_called_once()
                args, _ = mock_enviar.call_args
                token, usuario, texto_enviado = args
                self.assertEqual(token, 'token-falso')
                self.assertEqual(usuario, '12345')
                self.assertIn(f'[{root.name}] Versión finalizada.', texto_enviado)
                self.assertTrue(texto_enviado.endswith('— Adevv v0.5.0'))

    def test_enviar_firma_idempotente_hacia_telegram_api(self):
        """enviar() garantiza que el mensaje viaja firmado y no se duplica si ya lo estaba."""
        llamadas = []

        class MockResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        def mock_urlopen(req, data=None, timeout=15):
            import urllib.parse
            campos = dict(urllib.parse.parse_qsl(data.decode('utf-8')))
            llamadas.append(campos.get('text'))
            return MockResponse()

        with patch.object(orquestar, 'version_adevv', return_value='0.5.0', create=True), \
             patch('urllib.request.urlopen', side_effect=mock_urlopen):
            orquestar.enviar('token-test', '123', 'Texto sin firma')
            self.assertEqual(llamadas[0], 'Texto sin firma\n\n— Adevv v0.5.0')

            # Enviando texto ya firmado
            orquestar.enviar('token-test', '123', 'Texto ya firmado\n\n— Adevv v0.5.0')
            self.assertEqual(llamadas[1], 'Texto ya firmado\n\n— Adevv v0.5.0')


if __name__ == '__main__':
    unittest.main()
