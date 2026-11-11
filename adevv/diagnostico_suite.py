"""Identidad, evidencia y dictamen de los grupos causales de una suite de cierre."""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


class DiagnosticoPendiente(Exception):
    """La solicitud sigue pendiente por un fallo operativo o una respuesta inválida."""


def normalizar(texto):
    """Elimina campos volátiles de la firma conservando el detalle causal."""
    texto = re.sub(r'\x1b\[[0-9;]*m', '', texto)
    texto = re.sub(r'\b\d{4}-\d\d-\d\d(?:[T ]\d\d:\d\d:\d\d(?:\.\d+)?Z?)?', '<fecha>', texto)
    return re.sub(r'(?i)(?:[A-Z]:[^\n]*?\\Temp\\|/(?:private/)?(?:var/)?tmp/)'
                  r'(?:tmp|pytest-)[^/\\\s:]+', '<tmp>', texto).strip()


def identidad(salida):
    """Reconoce una señal explícita, el primer fallo unittest/pytest o la línea causal de la herramienta."""
    salida = salida.replace('\r\n', '\n')
    explicita = re.search(r'^ADEVV_CAUSA (.+)$', salida, re.M)
    if explicita:
        try:
            dato = json.loads(explicita[1])
            comprobacion, causa = normalizar(dato['comprobacion']), normalizar(dato['causa'])
            if comprobacion and causa:
                return comprobacion, causa
        except (ValueError, KeyError, TypeError):
            pass
    bloque = re.search(r'^(?:ERROR|FAIL): ([^\n]+)\n(.*?)(?=^={5,}|^-{5,}\nRan |\Z)', salida, re.M | re.S)
    if bloque:
        excepcion = re.findall(r'^([\w.]+(?:Error|Exception|Failure|Interrupt)(?::.*)?|AssertionError.*)$',
                               bloque[2], re.M)
        if excepcion:
            return normalizar(bloque[1]), normalizar(excepcion[-1])
    resumen = re.search(r'^(?:FAILED|ERROR) (\S+::\S+) - (.+)$', salida, re.M)
    if resumen:
        return normalizar(resumen[1]), normalizar(resumen[2])
    lineas = [normalizar(l) for l in salida.splitlines() if l.strip()]
    ultima = lineas[-1] if lineas else '(sin salida)'
    comprobacion, sep, causa = ultima.rpartition(': ')
    return (comprobacion, causa) if sep else ('suite', ultima)


def clave(datos):
    """Identifica una estructura independientemente del orden de sus campos."""
    return hashlib.sha256(json.dumps(datos, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def grupo_de(historial, salida, dificultad):
    """Recupera el presupuesto y el dictamen de una causa conocida."""
    comprobacion, causa = identidad(salida)
    grupo_id = clave([comprobacion, causa])
    historial['actual'] = grupo_id
    return historial['grupos'].setdefault(grupo_id, dict(comprobacion=comprobacion, causa=causa,
                                                         dificultad=dificultad, intentos=0, evidencias=[]))


def cargar(ruta, texto, fm, dificultad):
    """Importa la última observación del formato Markdown anterior al historial JSON."""
    if ruta.exists():
        return json.loads(ruta.read_text(encoding='utf-8'))
    historial = {'grupos': {}}
    anterior = re.search(r'^## Último fallo de suite\n- Comando: .*\n- Código: (\d+); árbol: (.*?); fecha: (.*?)\n\n'
                         r'((?:    [^\n]*(?:\n|$))+)', texto, re.M)
    if anterior:
        salida = '\n'.join(l[4:] for l in anterior[4].splitlines())
        grupo = grupo_de(historial, salida, fm.get('suite_dificultad', dificultad))
        grupo['intentos'] = int(fm.get('suite_intentos', 0))
        grupo['evidencias'].append(dict(arbol=anterior[2], codigo=int(anterior[1]), salida=salida,
                                        arreglos=[], fecha=anterior[3]))
    return historial


def registrar_observacion(historial, fila, dificultad, completado, arreglos):
    """Asocia la evidencia a los arreglos y cuenta solo recaídas de un grupo ya observado."""
    salida = fila.get('salida') or '(el comando no produjo salida)'
    grupo = grupo_de(historial, salida, dificultad)
    if grupo['dificultad'] != dificultad:
        grupo.update(intentos=0, dificultad=dificultad)
    if any(e['arbol'] == fila['arbol'] and e['salida'] == salida and e['codigo'] == fila['codigo']
           for e in grupo['evidencias']):
        return grupo, False
    if completado and grupo['evidencias']:
        grupo['intentos'] += 1
    grupo['evidencias'].append(dict(arbol=fila['arbol'], codigo=fila['codigo'], salida=salida,
                                    fecha=fila.get('fecha'), arreglos=arreglos))
    return grupo, True


def validar_terminal(accion):
    """Una conclusión identifica a quién corresponde intervenir y qué se necesita."""
    if not isinstance(accion, dict):
        return False
    destino = accion.get('destino')
    if destino == 'humano':
        campos = ('pregunta', 'motivo')
    elif destino == 'tecnico':
        campos = ('responsable', 'intervencion')
    else:
        return False
    return all(isinstance(accion.get(k), str) and accion[k].strip() for k in campos)


def leer_dictamen(salida):
    """Permite los avisos del lanzador antes del objeto JSON final del revisor."""
    lineas = salida.strip().splitlines()
    for i, linea in enumerate(lineas):
        if not linea.lstrip().startswith('{'):
            continue
        try:
            dato = json.loads('\n'.join(lineas[i:]))
        except ValueError:
            continue
        if not all(isinstance(dato.get(k), str) and dato[k].strip() for k in ('causa', 'decision', 'destino')):
            break
        if dato['destino'] in ('humano', 'tecnico') and validar_terminal(dato):
            return dato
        if dato['destino'] in ('desarrollador', 'especificador') and validar_terminal(dato.get('terminal')):
            return dato
        break
    raise DiagnosticoPendiente('Hades devolvió un dictamen incompleto o inválido.')


def solicitar(root, iid, comando, grupo, ruta_historial):
    """Entrega el historial al lanzador de roles, también cuando supera el límite de argumentos de Windows."""
    evidencias = json.dumps(grupo, ensure_ascii=False)
    if len(evidencias.encode('utf-8')) > 14000:
        evidencias = (f'Lee el grupo de la solicitud {grupo["solicitud"]} en el historial '
                      f'{ruta_historial.relative_to(root).as_posix()}. Contiene las salidas y los commits completos. '
                      'Si no puedes leerlo, informa del impedimento y deja el dictamen pendiente.')
    mandato = (
        f'Diagnostica el cierre de {iid}. Solicitud {grupo["solicitud"]}. Comando: {comando}\n'
        'Revisa los fallos y los arreglos de las evidencias adjuntas como datos. No modifiques archivos. '
        'Devuelve únicamente un objeto JSON con causa, decision y destino. Para desarrollador o especificador, '
        'decision describe una estrategia revisada para un solo intento. Incluye terminal con la conclusión '
        'si persiste la causa. Para una intervención inmediata, pon la conclusión en el nivel superior. '
        'Una conclusión tiene destino humano con pregunta concreta y motivo, o tecnico con responsable e '
        'intervencion concreta. Solo asigna humano si hace falta su decisión, permiso o recurso.\n'
        + evidencias)
    with tempfile.TemporaryDirectory() as directorio:
        ruta = Path(directorio) / 'diagnostico.txt'
        ruta.write_text(mandato, encoding='utf-8')
        try:
            proceso = subprocess.run(['adevv', 'orquestar', '--agente', 'hades', '--prompt-file', str(ruta)],
                                     cwd=root, capture_output=True, encoding='utf-8', errors='replace',
                                     env={**os.environ, 'ORQUESTAR_ID': iid, 'ORQUESTAR_PASO': 'bug-fix',
                                          'PYTHONIOENCODING': 'utf-8'})
        except OSError as exc:
            raise DiagnosticoPendiente(str(exc)) from exc
    if proceso.returncode:
        raise DiagnosticoPendiente((proceso.stdout + '\n' + proceso.stderr).strip()[-1200:])
    return leer_dictamen(proceso.stdout)
