"""Aislamiento común de las pruebas: ninguna llega a Telegram, venga de donde venga el token.

Al importarlo se quitan las credenciales `TELEGRAM_*` del entorno del proceso (y de sus hijos) y se
sustituye `urllib.request.urlopen` por un envoltorio que aborta la ejecución si algo intenta llamar
a `api.telegram.org`. Las pruebas que necesiten credenciales las definen ellas con `patch.dict` y
simulan el envío con `patch`.
"""

import os
import urllib.request

CLAVES = ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_ALLOWED_USER_IDS', 'TELEGRAM_CHAT_ID')
ANFITRION = 'api.telegram.org'


class EnvioRealBloqueado(BaseException):
    """Una prueba intentó llamar a Telegram sin simular el envío.

    Hereda de `BaseException` para que ni `enviar()` ni ningún `except Exception` lo traguen.
    """


def proteger(urlopen_original):
    """Devuelve un `urlopen` que bloquea Telegram y delega el resto."""
    def urlopen(url, *args, **kwargs):
        destino = getattr(url, 'full_url', url)
        if ANFITRION in str(destino):
            raise EnvioRealBloqueado(f'La prueba intentó llamar a Telegram sin simularlo: {ANFITRION}')
        return urlopen_original(url, *args, **kwargs)
    urlopen.protegido = True
    return urlopen


for clave in CLAVES:
    os.environ.pop(clave, None)

if not getattr(urllib.request.urlopen, 'protegido', False):
    urllib.request.urlopen = proteger(urllib.request.urlopen)
