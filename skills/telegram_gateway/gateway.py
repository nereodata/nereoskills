#!/usr/bin/env python3
"""Gateway de Telegram de Adevv: atiende a los usuarios autorizados mientras el bucle trabaja.

Comandos: /estado (/status) resume el bucle y el backlog; /tarea (/task) y /bug registran una entrada
sin versión. /lanzar (/run) y /parar (/stop) controlan el bucle; /metricas (/metrics) consulta consumo.
/nuevo (/reset) reinicia el hilo de conversación. Cualquier otro mensaje sin comando mantiene
una conversación interactiva con el asistente del proyecto conservando el hilo entre mensajes.
Nunca escribe en el backlog con el bucle en marcha: deja la petición en el buzón y el bucle
la registra entre pasos, con su propio commit. La configuración, el envío y el estado son los de
orquestar.py: TELEGRAM_BOT_TOKEN y TELEGRAM_ALLOWED_USER_IDS.
"""
import argparse
import importlib.util
import json
import os
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'orquestar', Path(__file__).resolve().parents[1] / 'orquestar' / 'orquestar.py')
motor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(motor)

_spec_metricas = importlib.util.spec_from_file_location(
    'metricas_gateway', Path(__file__).resolve().parents[1] / 'orquestar' / 'metricas.py')
metricas = importlib.util.module_from_spec(_spec_metricas)
_spec_metricas.loader.exec_module(metricas)

ALTAS = {'/tarea': 'tarea', '/task': 'tarea', '/bug': 'bug'}
AYUDA = ('Comandos:\n/estado — cómo va el bucle y el backlog\n'
         '/lanzar (o /run) — lanza el bucle en segundo plano\n'
         '/parar (o /stop) — para al terminar el paso en curso\n'
         '/metricas [filtro] (o /metrics) — consumo por tarea; por defecto ultima\n'
         '/tarea <título> — nueva tarea en el backlog, sin versión\n'
         '/bug <título> — nuevo bug, sin versión\n'
         '/nuevo (o /reset) — reinicia tu hilo de conversación\n'
         'Cualquier otro mensaje sin comando conversa con el asistente del proyecto.')


def cargar_sesiones(root):
    """Carga el diccionario de sesiones guardadas por usuario."""
    f = root / getattr(motor, 'TELEGRAM_SESIONES', 'orquestar_telegram.json')
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding='utf-8'))
    except Exception:
        return {}


def guardar_sesion(root, usuario, harness, sesion_id):
    """Guarda la sesión activa de un usuario para un arnés específico."""
    motor.excluir(root)
    sesiones = cargar_sesiones(root)
    usuario_str = str(usuario).strip()
    if usuario_str not in sesiones or not isinstance(sesiones[usuario_str], dict):
        sesiones[usuario_str] = {}
    sesiones[usuario_str][harness] = sesion_id
    f = root / getattr(motor, 'TELEGRAM_SESIONES', 'orquestar_telegram.json')
    f.write_text(json.dumps(sesiones, indent=2, ensure_ascii=False), encoding='utf-8')


def obtener_sesion(root, usuario, harness):
    """Obtiene el identificador de sesión para un usuario y arnés."""
    sesiones = cargar_sesiones(root)
    usuario_str = str(usuario).strip()
    if isinstance(sesiones.get(usuario_str), dict):
        return sesiones[usuario_str].get(harness)
    return sesiones.get(f'{usuario_str}:{harness}')


def borrar_sesion(root, usuario):
    """Elimina las sesiones registradas del usuario especificado."""
    sesiones = cargar_sesiones(root)
    usuario_str = str(usuario).strip()
    cambiado = False
    if usuario_str in sesiones:
        del sesiones[usuario_str]
        cambiado = True
    prefix = f'{usuario_str}:'
    for k in list(sesiones.keys()):
        if k.startswith(prefix):
            del sesiones[k]
            cambiado = True
    if cambiado:
        f = root / getattr(motor, 'TELEGRAM_SESIONES', 'orquestar_telegram.json')
        f.write_text(json.dumps(sesiones, indent=2, ensure_ascii=False), encoding='utf-8')


def construir_prompt(root, texto):
    """Construye el prompt con contexto de seguridad según el estado del bucle."""
    pid_file = root / getattr(motor, 'PID', 'orquestar.pid')
    bucle_en_marcha = pid_file.exists()
    aviso_bucle = (
        'AVISO: El bucle de /orquestar está en marcha (existe orquestar.pid). '
        'No debes modificar ni commitear ficheros rastreados del repositorio; '
        'limítate a consultar o analizar el código, o a indicar cómo apuntar tareas/bugs si el usuario lo pide.'
        if bucle_en_marcha else
        'El bucle de /orquestar no está en marcha actualmente.'
    )
    return (
        f'Estás respondiendo a través del gateway de Telegram de Adevv para el proyecto en {root}.\n'
        f'{aviso_bucle}\n\n'
        f'Mensaje del usuario:\n{texto}'
    )


def extraer_respuesta(salida, harness):
    """Extrae el contenido textual de la respuesta según el arnés."""
    if not salida:
        return ''
    for linea in reversed(salida.splitlines()):
        linea = linea.strip()
        if linea.startswith('{') and linea.endswith('}'):
            try:
                d = json.loads(linea)
                if harness == 'claude' and 'result' in d:
                    return d['result']
                if harness == 'agy' and 'response' in d:
                    return d['response']
                if 'response' in d:
                    return d['response']
                if 'result' in d:
                    return d['result']
            except Exception:
                pass
    if harness == 'codex':
        textos = []
        for linea in salida.splitlines():
            linea = linea.strip()
            if linea.startswith('{') and linea.endswith('}'):
                try:
                    ev = json.loads(linea)
                    if ev.get('type') == 'item.completed' and ev.get('item', {}).get('type') == 'agent_message':
                        textos.append(ev['item'].get('text', ''))
                except Exception:
                    pass
        if textos:
            return '\n'.join(textos)
    return salida.strip()


def invocar(root, prompt, cfg, sesion=None):
    """Invoca al modelo configurado mediante el motor de orquestación."""
    harness = cfg.get('harness', 'claude')
    base = motor.base_comando_agente(harness, prompt, sesion=sesion)
    if not base:
        raise RuntimeError(f'Arnés no soportado: {harness}')
    exe = shutil.which(base[0])
    if not exe:
        raise RuntimeError(f'No se encuentra el arnés "{base[0]}" en el PATH.')
    cmd = motor.con_modelo([exe] + base[1:], harness, cfg)
    codigo, m, salida = motor.lanzar(cmd, root, harness, entrada=prompt)
    sesion_id = m.get('sesion')
    if not sesion_id:
        for linea in reversed(salida.splitlines()):
            linea = linea.strip()
            if linea.startswith('{') and linea.endswith('}'):
                try:
                    d = json.loads(linea)
                    sesion_id = d.get('conversation_id') or d.get('session_id') or d.get('sessionId') or d.get('thread_id')
                    if sesion_id:
                        break
                except Exception:
                    pass
    texto_respuesta = extraer_respuesta(salida, harness)
    return codigo, sesion_id, texto_respuesta


def conversar(root, usuario, texto):
    """Mantiene la conversación con el modelo del proyecto conservando la sesión."""
    cfg_todo = motor.config(root) if hasattr(motor, 'config') else {}
    cfg_atenea = cfg_todo.get('atenea', {}) if isinstance(cfg_todo.get('atenea'), dict) else {}
    cfg_tg = cfg_todo.get('telegram', {}) if isinstance(cfg_todo.get('telegram'), dict) else {}
    cfg = {**cfg_atenea, **cfg_tg}
    harness = cfg.get('harness', 'claude')
    sesion = obtener_sesion(root, usuario, harness)
    prompt = construir_prompt(root, texto)

    if sesion:
        codigo, s_id, resp = invocar(root, prompt, cfg, sesion=sesion)
        if codigo != 0:
            codigo, s_id, resp = invocar(root, prompt, cfg, sesion=None)
            if codigo != 0:
                raise RuntimeError(f'Fallo al invocar al modelo (código {codigo}): {resp}')
        nueva_sesion, respuesta = s_id, resp
    else:
        codigo, s_id, resp = invocar(root, prompt, cfg, sesion=None)
        if codigo != 0:
            raise RuntimeError(f'Fallo al invocar al modelo (código {codigo}): {resp}')
        nueva_sesion, respuesta = s_id, resp

    if nueva_sesion:
        guardar_sesion(root, usuario, harness, nueva_sesion)
    return respuesta


def resumen_metricas(root, filtro):
    """Presenta tiempo, tokens E/C/S y coste por tarea con el cálculo de la CLI."""
    try:
        filas = metricas.consultar(root, motor.backlog(root), filtro)
    except (ValueError, OSError) as error:
        return f'No se pudieron consultar las métricas: {error}'
    if not filas:
        return 'Sin métricas para el filtro seleccionado.'
    lineas = ['Métricas · tokens E/C/S: entrada/caché leída/salida · coste estimado USD']
    for fila in filas:
        lineas.append(
            f"{fila['id']} ({fila['version']}): {fila['tiempo_real_min']:.2f} min · "
            f"Dev E/C/S={fila['dev_tokens_originales']}/{fila['dev_tokens_cache']}/{fila['dev_tokens_salida']} · "
            f"Hades E/C/S={fila['hades_tokens_originales']}/{fila['hades_tokens_cache']}/{fila['hades_tokens_salida']} · "
            f"USD≈{fila['coste_estimado_usd']:.6f}")
    return '\n'.join(lineas)


def responder(root, usuario, texto, autorizados):
    """Respuesta a un mensaje, o None si el usuario no está autorizado."""
    if str(usuario).strip() not in autorizados:
        return None
    comando, _, argumento = texto.strip().partition(' ')
    comando, argumento = comando.split('@')[0].lower(), argumento.strip()
    if comando in ('/estado', '/status'):
        return motor.parte(root)
    if comando in ('/parar', '/stop'):
        if not (root / motor.PID).exists():
            return 'El bucle ya está parado.'
        motor.excluir(root)
        (root / motor.PARADA).touch()
        return 'El bucle se detendrá al terminar el paso en curso.'
    if comando in ('/lanzar', '/run'):
        if (root / motor.PID).exists():
            return 'El bucle ya está en marcha.'
        estado = motor.estado(root, 'docs/requirements')
        try:
            motor.en_fondo(root, argumentos=[])
        except SystemExit as error:
            return str(error)
        paso = ' '.join(str(x) for x in estado[1:3] if x)
        return f'Lanzamiento solicitado en segundo plano. Siguiente estado previsto: {estado[0]} {paso}'
    if comando in ('/metricas', '/metrics'):
        return resumen_metricas(root, argumento or 'ultima')
    if comando in ALTAS:
        if not argumento:
            return f'Uso: {comando} <título>'
        motor.apuntar(root, ALTAS[comando], argumento, str(usuario))
        if (root / motor.PID).exists():
            return f'Apuntado: «{argumento}». El bucle lo registra al terminar el paso en curso y te avisa.'
        hechos = motor.ingerir(root)
        return '\n'.join(f'Registrada {iid}: {t} (backlog, sin versión).' for iid, t in hechos) \
            or 'Apuntado; se registrará en el próximo intento.'
    if comando in ('/nuevo', '/reset'):
        borrar_sesion(root, usuario)
        return 'Hilo de conversación reiniciado.'
    if comando in ('/start', '/ayuda', '/help'):
        return AYUDA
    return conversar(root, usuario, texto)


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
    """Punto de entrada principal para la ejecución en línea de comandos."""
    ap = argparse.ArgumentParser(description='Gateway de Telegram de Adevv.')
    ap.add_argument('--root', type=Path, default=Path.cwd(), help='raíz del proyecto')
    ap.add_argument('--estado', action='store_true', help='imprime el resumen que devuelve /estado y sale')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    root = a.root.resolve()
    os.chdir(root)
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
