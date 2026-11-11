"""Persistencia local del JSONL de métricas compartido por los productores de Adevv."""

import io
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

if os.name == 'nt':
    import msvcrt
else:
    import fcntl


ARCHIVO = 'orquestar_metricas.jsonl'
AUXILIAR = '.adevv-metricas'


def instantanea(ruta):
    """Cierra el registro antes de analizarlo o publicar su recuperación."""
    try:
        return ruta.read_bytes()
    except FileNotFoundError:
        return b''


def analizar(datos):
    """Emite los bytes originales, el objeto y el diagnóstico de cada línea física."""
    for numero, linea in enumerate(io.BytesIO(datos), 1):
        objeto, error = None, ''
        if linea.strip(b' \t\r\n'):
            try:
                objeto = json.loads(linea.decode('utf-8'))
                if not isinstance(objeto, dict):
                    raise ValueError('se esperaba un objeto')
            except (ValueError, RecursionError) as exc:
                objeto, error = None, f'{ARCHIVO}: línea {numero}: {exc}'
        yield linea, objeto, error


def leer_registros(root, tolerar_ultima=False):
    """Distingue consulta estricta, corrupción cerrada y cola aún en escritura."""
    filas = []
    for linea, objeto, error in analizar(instantanea(Path(root) / ARCHIVO)):
        if error:
            if not tolerar_ultima:
                raise ValueError(error)
            if linea.endswith(b'\n'):
                print(error, file=sys.stderr)
        elif objeto is not None:
            filas.append(objeto)
    return filas


@contextmanager
def bloqueo(root):
    """Comparte un bloqueo de ruta estable entre append y recuperación."""
    auxiliar = Path(root) / AUXILIAR
    auxiliar.mkdir(exist_ok=True)
    with (auxiliar / 'registro.lock').open('a+b') as candado:
        candado.seek(0)
        if os.name == 'nt':
            msvcrt.locking(candado.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(candado, fcntl.LOCK_EX)
        yield auxiliar


def registrar(root, fila):
    """Separa una cola interrumpida y añade una fila completa bajo el mismo bloqueo."""
    datos = json.dumps(fila, ensure_ascii=False).encode('utf-8') + b'\n'
    with bloqueo(root), (Path(root) / ARCHIVO).open('a+b') as activo:
        if activo.tell():
            activo.seek(-1, os.SEEK_END)
            if activo.read(1) != b'\n':
                activo.write(b'\n')
        activo.write(datos)


def guardar_evidencia(auxiliar, datos):
    """Conserva una instantánea exclusiva y sincronizada antes de modificar el activo."""
    with tempfile.NamedTemporaryFile(dir=auxiliar, prefix='original-', suffix='.jsonl', delete=False) as copia:
        copia.write(datos)
        copia.flush()
        os.fsync(copia.fileno())
        return Path(copia.name)


def publicar(temporal, ruta):
    """Permite que lectores de Windows cierren su instantánea antes del reemplazo."""
    limite = time.monotonic() + 2
    while True:
        try:
            os.replace(temporal, ruta)
            return
        except PermissionError as error:
            if getattr(error, 'winerror', None) not in (5, 32) or time.monotonic() >= limite:
                raise
            time.sleep(0.02)


def recuperar(root):
    """Retira solo líneas inválidas, conservando sus bytes originales en la evidencia."""
    ruta = Path(root) / ARCHIVO
    with bloqueo(root) as auxiliar:
        datos = instantanea(ruta)
        saneado = bytearray()
        errores = []
        for linea, _, error in analizar(datos):
            if error:
                errores.append(error)
            else:
                saneado.extend(linea)
        if not errores:
            return None
        copia = guardar_evidencia(auxiliar, datos)
        fd, temporal = tempfile.mkstemp(dir=auxiliar)
        try:
            with os.fdopen(fd, 'wb') as salida:
                salida.write(saneado)
                salida.flush()
                os.fsync(salida.fileno())
            publicar(temporal, ruta)
        finally:
            Path(temporal).unlink(missing_ok=True)
        for error in errores:
            print(error, file=sys.stderr)
        return copia
