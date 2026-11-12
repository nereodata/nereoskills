"""Resultados y recuperación de llamadas al LLM, independientes del transporte y del backlog."""

import hashlib
import json
import time
from datetime import datetime
from dataclasses import asdict, dataclass, field
from pathlib import Path

from adevv.store import write_json_atomic


@dataclass(frozen=True)
class Resultado:
    invocacion: str
    trabajo: str
    paso: str
    rol: str
    estado: str
    codigo: int
    padre: str = ''
    objetivo: str = ''
    entradas: str = ''
    perfil: dict = field(default_factory=dict)
    veredicto: str = ''
    salida: str = ''
    espera_s: float | None = None
    fuentes: dict = field(default_factory=dict)
    orden: int = field(default_factory=time.time_ns)
    iniciada: int = 0

    @property
    def referencia(self):
        """Solo un objetivo y unas entradas acreditados permiten conciliar dos invocaciones."""
        if not self.objetivo or not self.entradas:
            return self.invocacion
        return hashlib.sha256(json.dumps(
            [self.trabajo, self.paso, self.rol, self.objetivo, self.entradas]).encode()).hexdigest()

    @property
    def restante(self):
        if self.espera_s is None:
            return None
        return max(0, self.espera_s - (time.time_ns() - self.orden) / 1_000_000_000)


def estado(codigo, *, cuota=None, entrega=True, contradiccion=False):
    if cuota is not None:
        return 'espera_cuota'
    if codigo:
        return 'fallo_tecnico'
    if contradiccion:
        return 'aclaracion_pendiente'
    return 'recibida' if entrega else 'entrega_pendiente'


def recuperacion(resultado, *, hay_reserva=False, esperado=0, limite=0):
    """Política común de reserva y espera para pasos, roles y diagnósticos."""
    if resultado.estado == 'recibida':
        return 'continuar'
    if hay_reserva:
        return 'reserva'
    if resultado.espera_s is not None and esperado + resultado.espera_s <= limite:
        return 'esperar'
    return 'conservar'


def publicar(directorio, resultado):
    """Una llamada publica su propio archivo atómico, también cuando hay llamadas simultáneas."""
    if not directorio:
        return
    carpeta = Path(directorio)
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = hashlib.sha256(resultado.invocacion.encode()).hexdigest() + '.json'
    write_json_atomic(carpeta / nombre, asdict(resultado))


def leer(directorio):
    if not directorio or not Path(directorio).exists():
        return []
    resultados = []
    for ruta in Path(directorio).glob('*.json'):
        resultados.append(Resultado(**json.loads(ruta.read_text(encoding='utf-8'))))
    return sorted(resultados, key=lambda r: r.orden)


def pendientes(resultados):
    """El último resultado del mismo trabajo y alcance sustituye la espera anterior de ese alcance."""
    ultimos = {}
    for resultado in sorted(resultados, key=lambda r: (r.iniciada or r.orden, r.orden)):
        ultimos[resultado.referencia] = resultado
    return [r for r in ultimos.values() if r.estado != 'recibida']


def desde_metricas(filas):
    """Adapta registros antiguos conservando el alcance desconocido y el registro original."""
    resultados = []
    for n, fila in enumerate(filas):
        if fila.get('tipo') != 'agente':
            continue
        cuota = fila.get('espera_s', 1800) if fila.get('sin_cuota') else None
        entrega = bool(fila.get('veredicto') or fila.get('tipo_dictamen')
                       or (fila.get('rol') != 'hades' and not fila.get('codigo')))
        try:
            orden = int(datetime.fromisoformat(fila['fecha']).timestamp() * 1_000_000_000) + n
        except (KeyError, ValueError, TypeError):
            orden = n
        resultados.append(Resultado(
            fila.get('invocacion') or f'historica-{n}', fila.get('id', ''), fila.get('paso', ''),
            fila.get('rol', ''), estado(fila.get('codigo', 0), cuota=cuota, entrega=entrega),
            fila.get('codigo', 0), objetivo=fila.get('objetivo_llamada', ''),
            entradas=fila.get('entradas_llamada', ''), espera_s=cuota,
            perfil={'harness':fila.get('arnes'), 'model':fila.get('modelo_cuota') or fila.get('modelo')},
            veredicto=fila.get('veredicto', ''), fuentes={'registro': fila}, orden=orden))
    return resultados
