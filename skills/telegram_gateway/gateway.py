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
import base64
import ctypes
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.error
import urllib.request
from datetime import timedelta, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'orquestar', Path(__file__).resolve().parents[1] / 'orquestar' / 'orquestar.py')
motor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(motor)

_spec_metricas = importlib.util.spec_from_file_location(
    'metricas_gateway', Path(__file__).resolve().parents[1] / 'orquestar' / 'metricas.py')
metricas = importlib.util.module_from_spec(_spec_metricas)
_spec_metricas.loader.exec_module(metricas)
firmar = motor.firmar

ALTAS = {'/tarea': 'tarea', '/task': 'tarea', '/bug': 'bug'}
PID = 'telegram.pid'
LOG = 'telegram.log'
PARADA = 'telegram.parar'
AYUDA = ('Comandos:\n/estado — cómo va el bucle y el backlog\n'
         '/agentes (o /agents) — roles, modelos y porcentaje de cuota consumida\n'
         '/lanzar (o /run) — lanza el bucle en segundo plano\n'
         '/parar (o /stop) — para al terminar el paso en curso\n'
         '/cerrar vX.Y [confirmo] — revisa y cierra una versión\n'
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


class ModeloIndisponible(RuntimeError):
    """Señala cuota o fallo de arranque que permite probar una reserva."""


class GatewayNoDisponible(RuntimeError):
    """Conserva los motivos de indisponibilidad para responder al usuario."""


def invocar(root, prompt, cfg, sesion=None):
    """Invoca al modelo configurado mediante el motor de orquestación."""
    harness = cfg.get('harness', 'claude')
    base = motor.base_comando_agente(harness, prompt, sesion=sesion)
    if not base:
        raise RuntimeError(f'Arnés no soportado: {harness}')
    exe = getattr(motor, 'buscar_ejecutable', shutil.which)(base[0])
    if not exe:
        raise motor.ArnesAusente(f'No se encuentra el arnés "{base[0]}" en el PATH.')
    cmd = motor.con_modelo([exe] + base[1:], harness, cfg)
    try:
        codigo, m, salida = motor.lanzar(cmd, root, harness, entrada=prompt)
    except OSError as error:
        raise ModeloIndisponible(f'fallo de arranque: {error}') from error
    fecha = motor.ahora()
    instante = motor.fecha_estado(fecha)
    cuota = motor.espera_cuota(salida, ahora=instante.astimezone()) if codigo else None
    if cuota is not None:
        motor.registrar(root, {**m, 'tipo': 'gateway', 'fecha': fecha,
                               'arnes': harness, 'codigo': codigo,
                               'modelo_cuota': cfg.get('model') or 'predeterminado',
                               'cuota_espera_s': cuota})
        hasta = (instante + timedelta(seconds=cuota)).astimezone(timezone.utc)
        raise ModeloIndisponible(f'cuota hasta {hasta.isoformat()}')
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
    prompt = construir_prompt(root, texto)
    cuotas = motor.consumo_cuotas(root, motor.fecha_estado(motor.ahora()))[1]
    motivos = []
    for posicion, cfg_actual in enumerate([cfg] + motor.lista_reservas(cfg)):
        harness = cfg_actual.get('harness', 'claude')
        modelo = cfg_actual.get('model') or 'predeterminado'
        perfil = f'{harness}/{modelo}'
        hasta = cuotas.get((harness, modelo))
        if hasta:
            motivos.append(f'{perfil}: cuota hasta {hasta.astimezone(timezone.utc).isoformat()}')
            continue
        sesion = obtener_sesion(root, usuario, harness)
        try:
            codigo, s_id, resp = invocar(root, prompt, cfg_actual, sesion=sesion)
            if sesion and codigo != 0:
                codigo, s_id, resp = invocar(root, prompt, cfg_actual, sesion=None)
            if codigo != 0:
                raise RuntimeError(f'Fallo al invocar al modelo (código {codigo}): {resp}')
        except motor.ArnesAusente as error:
            motor.registrar_ausencia(root, 'gateway', posicion, cfg_actual)
            motivos.append(f'{perfil}: arnés ausente: {error}')
            continue
        except ModeloIndisponible as error:
            motivos.append(f'{perfil}: {error}')
            continue
        nueva_sesion, respuesta = s_id, resp
        cfg = cfg_actual
        break
    else:
        mensaje = ('Gateway: ningún arnés disponible en el principal ni en las reservas.\n'
                   + '\n'.join(motivos))
        motor.avisar(root, 'error', mensaje)
        raise GatewayNoDisponible(mensaje)

    if nueva_sesion:
        guardar_sesion(root, usuario, harness, nueva_sesion)
    modelo = cfg.get('model') or 'predeterminado'
    extra = f'{harness}/{modelo}' + (' · reserva' if posicion else '')
    return firmar(respuesta, extra=extra)


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
        resp = motor.parte(root)
    elif comando == '/cerrar':
        resp = motor.cargar_cierre_version().cerrar(root, argumento, motor)
    elif comando in ('/agentes', '/agents'):
        resp = motor.informe_agentes(root)
    elif comando in ('/parar', '/stop'):
        if not (root / motor.PID).exists():
            return firmar('El bucle ya está parado.')
        motor.excluir(root)
        (root / motor.PARADA).touch()
        return firmar('El bucle se detendrá al terminar el paso en curso.')
    elif comando in ('/lanzar', '/run'):
        if (root / motor.PID).exists():
            return firmar('El bucle ya está en marcha.')
        estado = motor.estado(root, 'docs/requirements')
        try:
            motor.en_fondo(root, argumentos=[])
        except SystemExit as error:
            return firmar(str(error))
        paso = ' '.join(str(x) for x in estado[1:3] if x)
        return firmar(f'Lanzamiento solicitado en segundo plano. Siguiente estado previsto: {estado[0]} {paso}')
    elif comando in ('/metricas', '/metrics'):
        resp = resumen_metricas(root, argumento or 'ultima')
    elif comando in ALTAS:
        if not argumento:
            return firmar(f'Uso: {comando} <título>')
        motor.apuntar(root, ALTAS[comando], argumento, str(usuario))
        if (root / motor.PID).exists():
            return firmar(f'Apuntado: «{argumento}». El bucle lo registra al terminar el paso en curso y te avisa.')
        hechos = motor.ingerir(root)
        return firmar('\n'.join(f'Registrada {iid}: {t} (backlog, sin versión).' for iid, t in hechos) \
            or 'Apuntado; se registrará en el próximo intento.')
    elif comando in ('/nuevo', '/reset'):
        borrar_sesion(root, usuario)
        return firmar('Hilo de conversación reiniciado.')
    elif comando in ('/start', '/ayuda', '/help'):
        resp = AYUDA
    else:
        try:
            return conversar(root, usuario, texto)
        except GatewayNoDisponible as error:
            return firmar(str(error))
    return firmar(resp)


def actualizaciones(token, desde=None, espera=25):
    """Mensajes nuevos por long polling ([] si falla la red)."""
    campos = {'timeout': espera, **({'offset': desde} if desde is not None else {})}
    url = f'https://api.telegram.org/bot{token}/getUpdates?{urllib.parse.urlencode(campos)}'
    try:
        with urllib.request.urlopen(url, timeout=espera + 10) as r:
            datos = json.loads(r.read().decode('utf-8'))
        return datos.get('result', []) if datos.get('ok') else []
    except urllib.error.HTTPError as ex:
        if ex.code == 409:
            print('[gateway] conflicto 409 en Telegram: otra instancia está escuchando con el mismo token', flush=True)
            time.sleep(5)
            raise
        print(f'[gateway] sin respuesta de Telegram ({type(ex).__name__})', flush=True)
        time.sleep(5)
        return []
    except Exception as ex:
        print(f'[gateway] sin respuesta de Telegram ({type(ex).__name__})', flush=True)
        time.sleep(5)
        return []


def pid_vivo(root):
    """Devuelve el PID registrado si sigue vivo; ignora marcas inválidas o muertas."""
    try:
        pid = int((root / PID).read_text(encoding='utf-8').strip())
        if pid <= 0:
            return None
        if os.name == 'nt':
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
            kernel.OpenProcess.restype = ctypes.c_void_p
            kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            handle = kernel.OpenProcess(0x1000, False, pid)
            if not handle:
                return pid if ctypes.get_last_error() == 5 else None
            try:
                codigo = ctypes.c_ulong()
                if not kernel.GetExitCodeProcess(handle, ctypes.byref(codigo)):
                    return pid
                return pid if codigo.value == 259 else None
            finally:
                kernel.CloseHandle(handle)
        os.kill(pid, 0)
        return pid
    except PermissionError:
        return pid
    except (OSError, ValueError, OverflowError):
        return None


def reservar(root):
    """Reserva el PID de forma exclusiva y retira restos de una ejecución anterior."""
    motor.excluir(root)
    try:
        archivo = (root / PID).open('x', encoding='utf-8')
    except FileExistsError:
        vivo = pid_vivo(root)
        if vivo:
            sys.exit(f'Ya hay un gateway en marcha (pid {vivo}).')
        (root / PID).unlink(missing_ok=True)
        archivo = (root / PID).open('x', encoding='utf-8')
    with archivo:
        archivo.write(str(os.getpid()))
    (root / PARADA).unlink(missing_ok=True)


def es_propietario_pid(root):
    """Comprueba si el proceso actual conserva la propiedad del PID."""
    try:
        return (root / PID).read_text(encoding='utf-8').strip() == str(os.getpid())
    except (FileNotFoundError, OSError, ValueError):
        return False


def limpiar(root):
    """Retira las marcas solo si el proceso actual conserva la propiedad del PID."""
    if es_propietario_pid(root):
        (root / PARADA).unlink(missing_ok=True)
        (root / PID).unlink(missing_ok=True)


def en_fondo(root):
    """Lanza gateway.py desacoplado, publica el PID y revierte reservas fallidas."""
    reservar(root)
    opciones = {'start_new_session': True}
    if os.name == 'nt':
        opciones = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW}
    try:
        with (root / LOG).open('a', encoding='utf-8') as log:
            proceso = subprocess.Popen(
                [sys.executable, '-u', str(Path(__file__).resolve()), '--root', str(root), '--gestionado'],
                cwd=root, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, **opciones)
        (root / PID).write_text(str(proceso.pid), encoding='utf-8')
    except BaseException:
        limpiar(root)
        raise
    print(f'[gateway] lanzado en segundo plano (pid {proceso.pid}); salida en {LOG}', flush=True)
    return 0


def parar(root):
    """Solicita parada cooperativa sin credenciales ni señales destructivas al PID."""
    motor.excluir(root)
    if pid_vivo(root):
        (root / PARADA).touch()
        print('[gateway] parará al terminar la operación actual', flush=True)
    else:
        (root / PID).unlink(missing_ok=True)
        (root / PARADA).unlink(missing_ok=True)
        print('[gateway] ya está parado', flush=True)
    return 0


def escuchar(root, token, autorizados, vueltas=None, desde=None):
    """Bucle de long polling: responde a cada mensaje autorizado; un mensaje que falla no para el resto."""
    n = 0
    conflictos_409 = 0
    while (vueltas is None or n < vueltas) and not (root / PARADA).exists():
        if motor.recargar_version(__file__, root, PID, {'desde': desde}, 'gateway'):
            return
        n += 1
        try:
            items = actualizaciones(token, desde)
            conflictos_409 = 0
        except urllib.error.HTTPError as ex:
            if ex.code == 409:
                conflictos_409 += 1
                if not es_propietario_pid(root) or conflictos_409 >= 3:
                    print('[gateway] deteniendo escucha por conflicto 409 en Telegram', flush=True)
                    return
                continue
            raise
        for u in items:
            if (root / PARADA).exists():
                return
            desde = u['update_id'] + 1
            m = u.get('message') or {}
            try:
                respuesta = responder(root, m.get('from', {}).get('id', ''), m.get('text') or '', autorizados)
            except Exception as ex:
                print(f'[gateway] error con el mensaje {u["update_id"]}: {ex!r}', flush=True)
                respuesta = firmar('No he podido procesarlo; mira el log del gateway.')
            if respuesta and m.get('chat', {}).get('id'):
                motor.enviar(token, m['chat']['id'], respuesta, markdown=True)


def carpeta_inicio():
    """Resuelve Inicio del usuario con la API de carpetas especiales de Windows."""
    shell = ctypes.WinDLL('shell32')
    resolver = shell.SHGetFolderPathW
    resolver.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
                        ctypes.c_ulong, ctypes.c_wchar_p]
    resolver.restype = ctypes.c_long
    ruta = ctypes.create_unicode_buffer(32768)
    if resolver(None, 7, None, 0, ruta) != 0:
        raise OSError('No se pudo resolver la carpeta Inicio del usuario')
    return Path(ruta.value)


def programa_inicio(root, log):
    """Genera una entrada sin credenciales que invoca una vez la orden estable."""
    raiz = "'" + str(root).replace("'", "''") + "'"
    destino = "'" + str(log).replace("'", "''") + "'"
    carpeta_log = "'" + str(log.parent).replace("'", "''") + "'"
    programa = (
        "$ErrorActionPreference = 'Stop'; "
        f"$raiz = {raiz}; $log = {destino}; "
        f"[IO.Directory]::CreateDirectory({carpeta_log}) | Out-Null; "
        "try { "
        "if (-not (Test-Path -LiteralPath $raiz -PathType Container)) { "
        "throw ('proyecto inexistente: ' + $raiz) }; "
        "Set-Location -LiteralPath $raiz; "
        "& adevv telegram --fondo 2>&1 | Out-File -LiteralPath $log -Encoding utf8 -Append; "
        "exit $LASTEXITCODE "
        "} catch { $_.Exception.Message | Out-File -LiteralPath $log -Encoding utf8 -Append; exit 1 }")
    codificado = base64.b64encode(programa.encode('utf-16le')).decode('ascii')
    comando = ('powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden '
               f'-EncodedCommand {codificado}')
    return ('Set shell = CreateObject("WScript.Shell")\r\n'
            f'WScript.Quit shell.Run("{comando}", 0, True)\r\n')


def gestionar_autoarranque(root, accion):
    """Registra, consulta o retira únicamente la entrada de Inicio de este proyecto."""
    if sys.platform != 'win32':
        print(f'[gateway] {root}: el autoarranque no está soportado en este sistema')
        return 1
    try:
        identidad = hashlib.sha256(os.path.normcase(str(root)).encode('utf-8')).hexdigest()
        entrada = carpeta_inicio() / f'Adevv-Telegram-{identidad}.vbs'
        if accion == 'on':
            base = Path(os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
                        or Path.home() / 'AppData' / 'Local')
            log = base / 'Adevv' / 'autoarranque' / f'{identidad}.log'
            entrada.parent.mkdir(parents=True, exist_ok=True)
            temporal = None
            try:
                with tempfile.NamedTemporaryFile(dir=entrada.parent, suffix='.tmp', delete=False) as archivo:
                    temporal = Path(archivo.name)
                    archivo.write(programa_inicio(root, log).encode('utf-16'))
                os.replace(temporal, entrada)
            finally:
                if temporal is not None:
                    temporal.unlink(missing_ok=True)
        elif accion == 'off':
            entrada.unlink(missing_ok=True)
        estado = 'registrado' if entrada.exists() else 'no registrado'
        print(f'[gateway] {root}: autoarranque {estado}')
        return 0
    except OSError as error:
        print(f'[gateway] {root}: no se pudo gestionar el autoarranque: {error}')
        return 1


def main():
    """Punto de entrada principal para la ejecución en línea de comandos."""
    ap = argparse.ArgumentParser(description='Gateway de Telegram de Adevv.')
    ap.add_argument('--root', type=Path, default=Path.cwd(), help='raíz del proyecto')
    modo = ap.add_mutually_exclusive_group()
    modo.add_argument('--estado', action='store_true', help='imprime el resumen que devuelve /estado y sale')
    modo.add_argument('--fondo', action='store_true', help=f'escucha en segundo plano, salida en {LOG}')
    modo.add_argument('--parar', action='store_true', help='pide parar el gateway al acabar la operación actual')
    modo.add_argument('--gestionado', action='store_true', help=argparse.SUPPRESS)
    modo.add_argument('--autoarranque', choices=('on', 'off', 'estado'),
                      help='registra, quita o consulta el arranque con la sesión de Windows')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    root = a.root.resolve()
    if a.autoarranque:
        return gestionar_autoarranque(root, a.autoarranque)
    os.chdir(root)
    if a.estado:
        print(motor.parte(root))
        return 0
    if a.parar:
        return parar(root)
    credenciales = motor.credenciales(root)
    token, autorizados = credenciales
    origen = getattr(credenciales, 'origen', 'proyecto')
    if not token or not autorizados:
        sys.exit('Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_ALLOWED_USER_IDS (en .env o en el entorno).')
    if origen == 'entorno':
        sys.exit(f'[gateway] {motor._GATEWAY_SOLO_AVISOS}')
    if a.fondo:
        if pid_vivo(root):
            print('[gateway] ya está en marcha', flush=True)
            return 0
        return en_fondo(root)
    recarga = motor.recibir_recarga(root, PID, __file__)
    if recarga is None and a.gestionado:
        for _ in range(100):
            if (root / PID).exists() and (root / PID).read_text(encoding='utf-8').strip() == str(os.getpid()):
                break
            time.sleep(0.05)
        else:
            sys.exit('No se publicó el PID del gateway; se cancela la escucha.')
    elif recarga is None:
        reservar(root)
    try:
        print(f'[gateway] escuchando para {root.name} ({len(autorizados)} usuarios autorizados)', flush=True)
        if recarga is None:
            escuchar(root, token, set(autorizados))
        else:
            escuchar(root, token, set(autorizados), desde=recarga['desde'])
    except KeyboardInterrupt:
        pass
    finally:
        limpiar(root)
    return 0


if __name__ == '__main__':
    sys.exit(main())
