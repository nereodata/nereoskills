#!/usr/bin/env python3
"""Gateway de Telegram de Adevv: atiende a los usuarios autorizados mientras el bucle trabaja.

Comandos: /estado (/status) resume el bucle y el backlog; /tarea (/task) y /bug registran una entrada
sin versión. Nunca escribe en el backlog con el bucle en marcha: deja la petición en el buzón y el bucle
la registra entre pasos, con su propio commit. La configuración, el envío y el estado son los de
orquestar.py: TELEGRAM_BOT_TOKEN y TELEGRAM_ALLOWED_USER_IDS.
"""
import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'orquestar', Path(__file__).resolve().parents[1] / 'orquestar' / 'orquestar.py')
motor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(motor)

ALTAS = {'/tarea': 'tarea', '/task': 'tarea', '/bug': 'bug'}
AYUDA = ('Comandos:\n/estado — cómo va el bucle y el backlog\n'
         '/tarea <título> — nueva tarea en el backlog, sin versión\n/bug <título> — nuevo bug, sin versión')


def responder(root, usuario, texto, autorizados):
    """Respuesta a un mensaje, o None si el usuario no está autorizado o no es un comando."""
    if str(usuario).strip() not in autorizados:
        return None
    comando, _, argumento = texto.strip().partition(' ')
    comando, argumento = comando.split('@')[0].lower(), argumento.strip()
    if comando in ('/estado', '/status'):
        return motor.parte(root)
    if comando in ALTAS:
        if not argumento:
            return f'Uso: {comando} <título>'
        motor.apuntar(root, ALTAS[comando], argumento, str(usuario))
        if (root / motor.PID).exists():
            return f'Apuntado: «{argumento}». El bucle lo registra al terminar el paso en curso y te avisa.'
        hechos = motor.ingerir(root)  # sin bucle en marcha, se registra ya
        return '\n'.join(f'Registrada {iid}: {t} (backlog, sin versión).' for iid, t in hechos) \
            or 'Apuntado; se registrará en el próximo intento.'
    if comando in ('/start', '/ayuda', '/help'):
        return AYUDA
    return None


def actualizaciones(token, desde=None, espera=25):
    """Mensajes nuevos por long polling ([] si falla la red)."""
    campos = {'timeout': espera, **({'offset': desde} if desde is not None else {})}
    url = f'https://api.telegram.org/bot{token}/getUpdates?{urllib.parse.urlencode(campos)}'
    try:
        with urllib.request.urlopen(url, timeout=espera + 10) as r:
            datos = json.loads(r.read().decode('utf-8'))
        return datos.get('result', []) if datos.get('ok') else []
    except Exception as ex:
        print(f'[gateway] sin respuesta de Telegram ({type(ex).__name__})', flush=True)
        time.sleep(5)
        return []


def escuchar(root, token, autorizados, vueltas=None):
    """Bucle de long polling: responde a cada mensaje autorizado; un mensaje que falla no para el resto."""
    desde, n = None, 0
    while vueltas is None or n < vueltas:
        n += 1
        for u in actualizaciones(token, desde):
            desde = u['update_id'] + 1
            m = u.get('message') or {}
            try:
                respuesta = responder(root, m.get('from', {}).get('id', ''), m.get('text') or '', autorizados)
            except Exception as ex:
                print(f'[gateway] error con el mensaje {u["update_id"]}: {ex!r}', flush=True)
                respuesta = 'No he podido procesarlo; mira el log del gateway.'
            if respuesta and m.get('chat', {}).get('id'):
                motor.enviar(token, m['chat']['id'], respuesta, markdown=True)


def main():
    ap = argparse.ArgumentParser(description='Gateway de Telegram de Adevv.')
    ap.add_argument('--root', type=Path, default=Path.cwd(), help='raíz del proyecto')
    ap.add_argument('--estado', action='store_true', help='imprime el resumen que devuelve /estado y sale')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    root = a.root.resolve()
    os.chdir(root)  # el motor consulta git en el directorio actual
    if a.estado:
        print(motor.parte(root))
        return 0
    token, autorizados = motor.credenciales(root)
    if not token or not autorizados:
        sys.exit('Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_ALLOWED_USER_IDS (en .env o en el entorno).')
    print(f'[gateway] escuchando para {root.name} ({len(autorizados)} usuarios autorizados)', flush=True)
    try:
        escuchar(root, token, set(autorizados))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
