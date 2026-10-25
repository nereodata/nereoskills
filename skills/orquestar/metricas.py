"""Consulta de solo lectura del consumo registrado por el orquestador."""
import csv
import json
import re
from collections import defaultdict


CAMPOS = ('id version tipo dificultad tiempo_estimado_min tiempo_real_min modelos_dev '
          'dev_tokens_originales dev_tokens_cache dev_tokens_salida dev_tokens_razonamiento '
          'modelos_hades hades_llamadas hades_rechazos hades_tokens_originales '
          'hades_tokens_cache hades_tokens_salida verificaciones_totales '
          'verificaciones_reutilizadas coste_estimado_usd').split()
ESTIMACIONES = {'sencilla': 7, 'media': 12, 'dificil': 25}
TARIFAS = (
    (('claude-opus',), (5, .5, 25)),
    (('claude-sonnet',), (3, .3, 15)),
    (('claude-haiku',), (1, .1, 5)),
    (('gemini-4-argon', 'gemini-pro'), (2, .2, 12)),
    (('gemini-3.8-flash', 'gemini-flash'), (.5, .05, 3)),
    (('gpt', 'codex'), (2.5, .25, 10)),
)
DEFECTO = (2.5, .25, 10)


def version(valor):
    """Normaliza versiones numéricas al bloque mayor.menor usado por vkey."""
    m = re.fullmatch(r'v?(\d+)\.(\d+)(?:\.\d+)?', str(valor or '').strip())
    return f'v{int(m[1])}.{int(m[2])}' if m else ''


def clave_version(valor):
    """Orden numérico compatible con vkey; sin-version queda al principio."""
    return tuple(map(int, valor[1:].split('.'))) if valor != 'sin-version' else (-1, -1)


def seleccionar(filtro, disponibles):
    """Resuelve todos los alias de filtro sin depender del orden del backlog."""
    filtro = filtro.strip().lower()
    ordenadas = sorted(disponibles - {'sin-version'}, key=clave_version)
    if filtro in ('todas', 'all'):
        return disponibles
    if filtro in ('ultima', 'last'):
        return set(ordenadas[-1:])
    if filtro.startswith(('ultimas:', 'last:')):
        cantidad = filtro.split(':', 1)[1]
        if not cantidad.isdigit() or int(cantidad) <= 0:
            raise ValueError('El filtro últimas:N / last:N requiere un N positivo.')
        return set(ordenadas[-int(cantidad):])
    versiones = [version(v) for v in filtro.split(',')]
    if not all(versiones):
        raise ValueError(f'Filtro de versión inválido: {filtro}')
    return set(versiones)


def coste(registro):
    """Usa coste reportado o una estimación ilustrativa USD por modelo."""
    if (registro.get('coste_usd') or 0) > 0:
        return registro['coste_usd']
    total = 0
    for modelo, uso in (registro.get('modelos') or {}).items():
        if (uso.get('coste_usd') or 0) > 0:
            total += uso['coste_usd']
            continue
        tarifas = next((t for familias, t in TARIFAS
                        if any(f in modelo.lower() for f in familias)), DEFECTO)
        total += sum((uso.get(campo) or 0) * tarifa
                     for campo, tarifa in zip(('entrada', 'cache_leida', 'salida'), tarifas)) / 1e6
    return total


def nueva_fila(iid, ver, item=None):
    """Construye el esquema compartido por CSV y terminal."""
    item = item or {}
    es_version = not iid.startswith(('T-', 'B-'))
    dificultad = item.get('dificultad', 'media')
    fila = dict.fromkeys(CAMPOS, 0)
    fila.update(id=iid, version=ver, tipo='version' if es_version else
                'bug' if item.get('paso') == 'bug-fix' or iid.startswith('B-') else 'funcional',
                dificultad=dificultad, tiempo_estimado_min=0 if es_version else
                ESTIMACIONES.get(dificultad, 12), modelos_dev=set(), modelos_hades=set())
    return fila


def agregar(registros, items, filtro='todas'):
    """Cruza el backlog con los registros sin modificar ninguna fuente."""
    por_id = {i['id']: i for i in items}
    filas = {}
    for item in items:
        ver = version(item.get('version')) or 'sin-version'
        filas[(ver, item['id'])] = nueva_fila(item['id'], ver, item)
    for registro in registros:
        iid = str(registro.get('id') or '')
        item = por_id.get(iid, {})
        rama = str(registro.get('rama') or '')
        rama_version = rama.split('/', 1)[1] if rama.startswith(('release/', 'hotfix/')) else ''
        ver = (version(item.get('version')) or version(registro.get('version')) or
               version(rama_version) or version(iid) or 'sin-version')
        if not iid or version(iid):
            iid = f"{registro.get('paso') or registro.get('tipo') or 'paso'}:{ver}"
        fila = filas.setdefault((ver, iid), nueva_fila(iid, ver, item))
        tipo = registro.get('tipo', 'paso')
        if tipo == 'paso':
            fila['tiempo_real_min'] += (registro.get('duracion_s') or 0) / 60
        if tipo == 'verificacion':
            fila['verificaciones_totales'] += 1
            fila['verificaciones_reutilizadas'] += bool(registro.get('reutilizada'))
        grupo = 'dev' if tipo == 'paso' else 'hades' if (
            tipo == 'agente' and registro.get('rol') == 'hades') else None
        if grupo == 'hades':
            fila['hades_llamadas'] += (not registro.get('cuota_espera_s')
                                       and not registro.get('sin_cuota')
                                       and registro.get('modelos') != {})
            fila['hades_rechazos'] += registro.get('veredicto') == 'RECHAZADO'
        if grupo:
            for modelo, uso in (registro.get('modelos') or {}).items():
                fila[f'modelos_{grupo}'].add(modelo)
                for origen, destino in (('entrada', 'originales'), ('cache_leida', 'cache'),
                                        ('salida', 'salida'), ('razonamiento', 'razonamiento')):
                    campo = f'{grupo}_tokens_{destino}'
                    if campo in fila:
                        fila[campo] += uso.get(origen) or 0
        fila['coste_estimado_usd'] += coste(registro)
    elegidas = seleccionar(filtro, {ver for ver, _ in filas})
    resultado = []
    for (ver, iid), fila in sorted(filas.items(), key=lambda par: (clave_version(par[0][0]), par[0][1])):
        if ver in elegidas:
            for campo in ('modelos_dev', 'modelos_hades'):
                fila[campo] = ';'.join(sorted(fila[campo]))
            resultado.append(fila)
    return resultado


def escribir_csv(filas, out):
    """Exporta cabecera estable y todos los campos usando el quoting estándar."""
    escritor = csv.DictWriter(out, fieldnames=CAMPOS)
    escritor.writeheader()
    escritor.writerows(filas)


def escribir_tabla(filas, out):
    """Presenta filas, desglose de tokens y totales por versión en terminal."""
    if not filas:
        print('Sin métricas para el filtro seleccionado.', file=out)
        return
    print('ID | Versión | Tipo | Dificultad | Est.min | Real.min | Hades llamadas/rechazos | '
          'Verificaciones/reutilizadas | USD estimado', file=out)
    totales = defaultdict(lambda: dict.fromkeys(
        [c for c in CAMPOS if c not in ('id', 'version', 'tipo', 'dificultad',
                                       'modelos_dev', 'modelos_hades')], 0))
    for fila in filas:
        print(f"{fila['id']} | {fila['version']} | {fila['tipo']} | {fila['dificultad']} | "
              f"{fila['tiempo_estimado_min']:.2f} | {fila['tiempo_real_min']:.2f} | "
              f"{fila['hades_llamadas']}/{fila['hades_rechazos']} | "
              f"{fila['verificaciones_totales']}/{fila['verificaciones_reutilizadas']} | "
              f"{fila['coste_estimado_usd']:.6f}", file=out)
        print(f"  Dev [{fila['modelos_dev']}]: entrada={fila['dev_tokens_originales']} "
              f"cache={fila['dev_tokens_cache']} salida={fila['dev_tokens_salida']} "
              f"razonamiento={fila['dev_tokens_razonamiento']}; "
              f"Hades [{fila['modelos_hades']}]: entrada={fila['hades_tokens_originales']} "
              f"cache={fila['hades_tokens_cache']} salida={fila['hades_tokens_salida']}", file=out)
        for campo in totales[fila['version']]:
            totales[fila['version']][campo] += fila[campo]
    for ver, total in totales.items():
        print(f"TOTAL {ver}: est.min={total['tiempo_estimado_min']:.2f} "
              f"real.min={total['tiempo_real_min']:.2f} "
              f"Hades={total['hades_llamadas']}/{total['hades_rechazos']} "
              f"verificaciones={total['verificaciones_totales']}/"
              f"{total['verificaciones_reutilizadas']} USD={total['coste_estimado_usd']:.6f}", file=out)
        print('  Tokens: ' + ' '.join(f'{k}={v}' for k, v in total.items() if '_tokens_' in k), file=out)


def consultar(root, items, filtro):
    """Lee y agrega el JSONL sin modificar el estado ni producir salida parcial."""
    registros = []
    ruta = root / 'orquestar_metricas.jsonl'
    if ruta.exists():
        with ruta.open(encoding='utf-8') as entrada:
            for numero, linea in enumerate(entrada, 1):
                if not linea.strip():
                    continue
                try:
                    registro = json.loads(linea)
                except json.JSONDecodeError as error:
                    raise ValueError(f'{ruta.name}: JSON inválido en línea {numero}') from error
                if not isinstance(registro, dict):
                    raise ValueError(f'{ruta.name}: se esperaba un objeto en línea {numero}')
                registros.append(registro)
    return agregar(registros, items, filtro)


def mostrar(root, items, filtro, csv_destino, out):
    """Lee el JSONL y genera salida sin tocar el estado del bucle."""
    filas = consultar(root, items, filtro)
    if csv_destino is None:
        escribir_tabla(filas, out)
    elif csv_destino == '-':
        escribir_csv(filas, out)
    else:
        with open(csv_destino, 'w', encoding='utf-8', newline='') as archivo:
            escribir_csv(filas, archivo)
    return 0
