"""Identidad operativa de versiones y acreditación de revisiones de cierre."""

import hashlib
import os
import re
import subprocess
from collections import deque
from html.parser import HTMLParser
from itertools import chain
from pathlib import Path

from adevv.registro_metricas import leer_registros
from adevv.yaml_lite import load_yaml


def clave_version(valor):
    """Devuelve mayor, menor y parche; la omisión del parche equivale a cero."""
    m = re.fullmatch(r'v?(\d+)\.(\d+)(?:\.(\d+))?', str(valor or '').strip())
    return (int(m[1]), int(m[2]), int(m[3] or 0)) if m else None


def nombre_version(clave):
    """Conserva parches positivos y la ruta histórica del parche cero."""
    return f'v{clave[0]}.{clave[1]}' + (f'.{clave[2]}' if clave[2] else '')


def carpetas_maestras(root, cfg):
    """Directorios configurados de tareas y bugs maestros."""
    master = (cfg.get('levels') or {}).get('master') or {}
    base = root / master.get('path', 'docs/plan/')
    folders = master.get('folders') or {}
    return tuple(base / folders.get(tipo, master.get(tipo, tipo + '/')) for tipo in ('tasks', 'bugs'))


def huella_producto(root, arbol, carpetas, mandato_temporal=None):
    """Identifica rutas, modos y objetos Git del producto sin los documentos de seguimiento."""
    excluidos = tuple(p.relative_to(root).as_posix().encode() + b'/' for p in carpetas) + (b'docs/review/',)
    entradas = subprocess.check_output(['git', 'ls-tree', '-rz', '--full-tree', arbol], cwd=root)
    producto = hashlib.sha256()
    temporal = os.fsencode(mandato_temporal) if mandato_temporal is not None else None
    for entrada in entradas.split(b'\0'):
        ruta = entrada.partition(b'\t')[2]
        if entrada and ruta != temporal and not ruta.startswith(excluidos):
            producto.update(entrada + b'\0')
    return producto.hexdigest()


class CitasHTML(HTMLParser):
    """Separa el texto propio de las citas y los ejemplos de código HTML."""

    etiquetas = ('blockquote', 'pre', 'code')
    inicio_bloque_html = re.compile(
        r' {0,3}</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|'
        r'details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|'
        r'header|hgroup|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|'
        r'p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?=[\s/>]|$)', re.I)
    etiqueta = (r"""(?:</[a-z][\w-]*\s*>|<[a-z][\w-]*(?:\s+[^\s"'<>/=\x00]+(?:\s*=\s*"""
                r"""(?:'[^']*'|"[^"]*"|[^\s"'=<>`]+))?)*\s*/?>)""")
    etiqueta_aislada = re.compile(r' {0,3}' + etiqueta + r'[ \t]*', re.I)
    inicio_incompleto = re.compile(r'(?!' + etiqueta + r')<(?=/?[a-z])', re.I)

    def __init__(self):
        super().__init__()
        self.abiertas = []
        self.en_bloque_html = False
        self.visible = []
        self.bloque = False

    def handle_starttag(self, tag, attrs):
        if tag in self.etiquetas:
            if not self.abiertas:
                self.bloque = self.bloque or tag != 'code'
                self.visible.append(' ')
            self.abiertas.append(tag)
        elif not self.abiertas:
            self.visible.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.abiertas and tag == self.abiertas[-1]:
            self.abiertas.pop()
        elif not self.abiertas:
            self.visible.append(f'</{tag}>')

    def handle_data(self, data):
        if not self.abiertas:
            self.visible.append(data)

    def sin_citas(self, linea):
        """Retiene el texto propio a ambos lados de una cita, incluso entre líneas."""
        continuacion = self.abiertas or self.rawdata
        self.bloque = any(tag != 'code' for tag in self.abiertas)
        if not linea.strip():
            self.en_bloque_html = False
        elif not continuacion and (self.inicio_bloque_html.match(linea) or self.etiqueta_aislada.fullmatch(linea)):
            self.en_bloque_html = True
        codigo_sangrado = linea.expandtabs(4).startswith('    ') and not self.en_bloque_html
        if not continuacion and ('<' not in linea or codigo_sangrado
                                 or re.match(r' {0,3}(?:>|`{3,}|~{3,})', linea)):
            return linea
        protegida = linea.replace(r'\<', r'\&lt;')
        self.visible.clear()
        self.feed(protegida + '\n')
        visible = ''.join(self.visible).rstrip('\n')
        return visible if visible.strip() else None


CERCO = r' {0,3}(`{3,}|~{3,})'


def contenido_de_lista(linea, sangrias, literal):
    """Separa los marcadores Markdown y la sangría de sus elementos anidados."""
    contenido = linea.expandtabs(4)
    if not contenido.strip():
        return '', '', False
    espacios = len(contenido) - len(contenido.lstrip(' '))
    cambio = False
    while sangrias and espacios < sangrias[-1]:
        sangrias.pop()
        cambio = True
    inicio = sangrias[-1] if sangrias else 0
    if literal and not cambio:
        return contenido[inicio:], '', False
    fin = inicio
    while marca := re.match(r' {0,3}(?:[-+*]|\d{1,9}[.)]) (?: {0,3}(?=\S))?', contenido[fin:]):
        fin += marca.end()
        sangrias.append(fin)
        cambio = True
    return contenido[fin:], contenido[inicio:fin], cambio


def cierra_cerco(linea, marca):
    """CommonMark permite cerrar con el mismo signo y longitud igual o mayor."""
    return re.fullmatch(r' {0,3}' + marca + marca[0] + r'*[ \t]*', linea)


def contenido_del_informe(texto):
    """Retira un cerco Markdown que envuelve el informe entero y conserva los ejemplos internos."""
    lineas = texto.strip('\r\n').splitlines()
    if len(lineas) >= 3 and (inicio := re.fullmatch(CERCO + r'(?:markdown|md)?\s*', lineas[0], re.I)):
        if cierra_cerco(lineas[-1], inicio[1]) and not any(cierra_cerco(l, inicio[1]) for l in lineas[1:-1]):
            return lineas[1:-1]
    return lineas


def interrumpe_cita(linea):
    """Reconoce bloques que pueden empezar sin línea en blanco tras un párrafo citado."""
    return (CitasHTML.inicio_bloque_html.match(linea)
            or re.match(r' {0,3}<(?:pre|script|style|textarea)(?=[\s>]|$)', linea, re.I)
            or re.match(r' {0,3}<(?:!--|\?|![A-Z]|!\[CDATA\[)', linea)
            or re.fullmatch(r' {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*', linea))


TOKEN_HTML = re.compile(CitasHTML.etiqueta + r'|<!--.*?(?:-->|\Z)', re.I | re.S)
FRAGMENTO = re.compile(TOKEN_HTML.pattern + r'|\\[^\w\s]|(?<!`)(?P<marca>`+)(?!`)(?P<codigo>.*?)'
                       r'(?<!`)(?P=marca)(?!`)', re.I | re.S)


ENCABEZADO = re.compile(r' {0,3}#{1,6}(?:\s|$)')


def ocultar_fragmentos(texto):
    """Oculta código Markdown y deja intacto el contenido literal de un pre efectivo."""
    partes = []
    inicio = 0
    html = CitasHTML()
    while inicio < len(texto):
        literal = 'pre' in html.abiertas
        token = (TOKEN_HTML if literal else FRAGMENTO).search(texto, inicio)
        if token is None:
            break
        partes.append(texto[inicio:token.start()])
        valor = token[0]
        if not literal and token['codigo'] is not None:
            valor = '…'
        elif literal or re.match(r'<pre(?=[\s/>])', valor, re.I):
            html.feed(valor)
        partes.append(valor)
        inicio = token.end()
    partes.append(texto[inicio:])
    return ''.join(partes)


def parrafo_sin_codigo(linea, pendientes, sangrias):
    """Procesa los fragmentos en línea una vez por párrafo o encabezado Markdown."""
    parrafo = [linea]
    if not ENCABEZADO.match(linea):
        while pendientes:
            original = pendientes[0].expandtabs(4)
            espacios = len(original) - len(original.lstrip(' '))
            sangria = next((n for n in reversed(sangrias) if n <= espacios), 0)
            otra = original[sangria:]
            if (not otra.strip() or interrumpe_cita(otra) or re.match(CERCO, otra) or ENCABEZADO.match(otra)
                    or re.match(r' {0,3}(?:>|(?:[-+*]|0{0,8}1[.)])\s+\S|=+\s*$)', otra)
                    or (sangrias and sangria < sangrias[-1]
                        and re.match(r' {0,3}(?:[-+*]|\d{1,9}[.)])(?:\s|$)', otra))):
                break
            parrafo.append(pendientes.popleft())
    return deque(ocultar_fragmentos('\n'.join(parrafo)).split('\n'))


def lineas_del_informe(texto):
    """Conserva las declaraciones del informe fuera de citas y ejemplos de código."""
    abierto = ''
    parrafo_citado = False
    citas_html = CitasHTML()
    sangrias = []
    pendientes = deque(contenido_del_informe(CitasHTML.inicio_incompleto.sub('&lt;', texto)))
    preparadas = deque()
    while preparadas or pendientes:
        preparada = bool(preparadas)
        original = (preparadas or pendientes).popleft()
        literal = abierto or citas_html.en_bloque_html or citas_html.abiertas or citas_html.rawdata
        linea, marcador, cambio_lista = contenido_de_lista(original, sangrias, literal)
        if cambio_lista:
            citas_html = CitasHTML()
            if marcador:
                parrafo_citado = False
            abierto = ''
        if parrafo_citado and interrumpe_cita(linea):
            parrafo_citado = False
        if not abierto:
            if (not preparada and '`' in linea
                    and not (citas_html.en_bloque_html or citas_html.rawdata or 'pre' in citas_html.abiertas)
                    and not (interrumpe_cita(linea) or citas_html.etiqueta_aislada.fullmatch(linea)
                             or re.match(r' {0,3}(?:>|`{3,}|~{3,})| {4}', linea))):
                preparadas = parrafo_sin_codigo(linea, pendientes, sangrias)
                linea = preparadas.popleft()
            visible = citas_html.sin_citas(linea)
            if visible is None:
                if citas_html.bloque or not linea.strip():
                    parrafo_citado = False
                yield None
                continue
            linea = visible
        marca = re.match(CERCO, linea)
        contenido = linea.strip()
        if abierto:
            if cierra_cerco(linea, abierto):
                abierto = ''
        elif marca:
            abierto = marca[1]
            parrafo_citado = False
        elif contenido.startswith('>'):
            citado = re.sub(r'^(?:> ?)+', '', contenido)
            bloque = re.match(r' {0,3}(?:#{1,6}(?:\s|$)|`{3,}|~{3,}|(?:=+|-+)\s*$)', citado)
            parrafo_citado = bool(citado.strip() and not bloque and not citado.startswith(('    ', '\t')))
        elif parrafo_citado and contenido and not re.match(r' {0,3}(?:#{1,6}|[-+*]|\d+[.)])\s', linea):
            yield None
            continue
        else:
            parrafo_citado = False
            yield None if linea.startswith('    ') else (marcador + contenido).strip().replace('**', '')
            continue
        yield None


def cabecera_informe(texto):
    """Lee el veredicto, el producto y la referencia opcional al rechazo reevaluado."""
    lineas = iter(lineas_del_informe(texto))
    for line in lineas:
        if not line:
            continue
        formal = re.match(r'^(?:[-#]+\s*)?Veredicto(?: final)?:\s*(?:✅\s*)?(APROBADO|RECHAZADO|N/A)(?=$|[\s.,;—(])', line, re.I)
        simple = re.fullmatch(r'(APROBADO|RECHAZADO|N/A)[.]?', line, re.I)
        if formal or simple:
            siguiente = next((l for l in lineas if l != ''), None)
            huella = re.fullmatch(r'Producto revisado:\s*(.*)', siguiente or '', re.I)
            if huella:
                siguiente = next((l for l in lineas if l != ''), None)
            rechazo = re.fullmatch(r'Rechazo reevaluado:\s*([a-f0-9]{40}|[a-f0-9]{64})', siguiente or '', re.I)
            return (formal or simple)[1].upper(), huella[1] if huella else None, rechazo[1].lower() if rechazo else None
    return '', None, None


def declaracion(texto):
    """Devuelve el veredicto propio y la huella de producto declarada."""
    return cabecera_informe(texto)[:2]


def config_maestras(root):
    """Obtiene las carpetas para consultas independientes de la CLI."""
    path = root / 'task_config.yaml'
    cfg = load_yaml(path) if path.exists() else {}
    return carpetas_maestras(root, cfg or {})


def maestro_por_id(iid, carpetas):
    """Localiza una ficha histórica cuyo nombre de archivo puede diferir del ID."""
    for carpeta in carpetas:
        for path in carpeta.glob('*.md'):
            cabecera = re.match(r'^---\s*\n(.*?)\n---', path.read_text(encoding='utf-8'), re.S)
            if cabecera and (load_yaml(cabecera[1]) or {}).get('id') == iid:
                return path
    return None


def commit_del_intento(root, iid):
    """Recupera el último HEAD atribuido al ID que pertenece a la historia actual."""
    for fila in reversed(leer_registros(root, tolerar_ultima=True)):
        commit = fila.get('commit_producto')
        if (fila.get('tipo') == 'paso' and fila.get('id') == iid and isinstance(commit, str)
                and re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', commit)
                and subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'],
                                   cwd=root, capture_output=True).returncode == 0):
            return commit
    return None


def palabras_informe(texto):
    """Identifica el cuerpo histórico aunque al restaurarlo se sangre, cite o intercale una nota."""
    cuerpo = []
    cerco = ''
    for linea in contenido_del_informe(texto):
        contenido = linea.strip().lstrip('> \t')
        marca = re.match(r'(`{3,}|~{3,})', contenido)
        if cerco:
            if marca and marca[0].startswith(cerco) and not contenido[marca.end():].strip():
                cerco = ''
            else:
                cuerpo.extend(re.findall(r'\w+', contenido.casefold()))
            continue
        if marca:
            cerco = marca[0]
            continue
        contenido = contenido.lstrip('#-* \t').replace('**', '')
        if re.match(r'(?:Producto revisado|Rechazo reevaluado|Veredicto(?: final)?):', contenido, re.I):
            continue
        if not re.fullmatch(r'APROBADO\.?|RECHAZADO\.?|N/A\.?', contenido, re.I):
            cuerpo.extend(re.findall(r'\w+', contenido.casefold()))
    return cuerpo


def informes_confirmados(root, ruta, historial):
    """Lee en orden de emisión las revisiones de la ruta, incluidas sus eliminaciones."""
    for sha in reversed(historial):
        commit = sha.decode('ascii')
        blob = subprocess.run(['git', 'show', f'{commit}:{ruta}'], cwd=root, capture_output=True)
        yield commit, '' if blob.returncode else blob.stdout.decode('utf-8')


def acreditacion_anterior(root, ruta, historial, texto, carpetas):
    """Atribuye cada edición al producto y la referencia de su emisión original."""
    buscado = cabecera_informe(texto)[0]
    previo = emision = huella = referencia = ultimo_rechazo = None
    informe_emitido = ''
    aprobaciones = []
    revocadas = 0
    for commit, informe in chain(informes_confirmados(root, ruta, historial), [(None, texto)]):
        veredicto, declarada, reevaluado = cabecera_informe(informe)
        if veredicto != previo or (declarada is not None and declarada != huella):
            emision, huella, referencia = commit, declarada, reevaluado
            informe_emitido = informe
        elif reevaluado:
            referencia = reevaluado
        previo = veredicto
        if commit and veredicto == 'RECHAZADO':
            ultimo_rechazo = commit
            revocadas = len(aprobaciones)
        elif commit and veredicto == buscado:
            aprobaciones.append((emision, huella, informe))
    if ultimo_rechazo and referencia:
        return emision, huella, referencia != ultimo_rechazo
    if not revocadas:
        return emision, huella, False
    producto_actual = huella
    if producto_actual is None and emision:
        producto_actual = huella_producto(root, emision, carpetas)
    palabras = palabras_informe(informe_emitido if huella is None else texto)
    for origen, declarada, historico in aprobaciones[:revocadas]:
        anteriores = palabras_informe(historico)
        comparar_productos = huella is not None or (not anteriores and bool(palabras))
        if comparar_productos and producto_actual is not None:
            producto = declarada if declarada is not None else huella_producto(root, origen, carpetas)
            if producto != producto_actual:
                continue
        actuales = iter(palabras)
        if all(p in actuales for p in anteriores):
            return emision, huella, True
    return emision, huella, False


def motivo_revision(root, iid, ficha=None, carpetas=None, objetivo=None):
    """Contrasta la aprobación con el producto del cierre del ID, también tras relanzar."""
    root = Path(root)
    informe = root / 'docs/review/code_reviews' / f'{iid}-code-review.md'
    motivo = motivo_informe(informe)
    if motivo or not (root / '.git').exists():
        return motivo
    carpetas = carpetas or config_maestras(root)
    ficha = ficha or maestro_por_id(iid, carpetas)
    if not ficha:
        return 'falta la ficha del producto revisado'
    ruta = informe.relative_to(root).as_posix()
    actual = informe.read_text(encoding='utf-8')
    confirmar = objetivo is not None
    try:
        historial = subprocess.check_output(['git', 'log', '--format=%H', '--', ruta], cwd=root).splitlines()
        emision, huella, restaurado = acreditacion_anterior(root, ruta, historial, actual, carpetas)
        if restaurado:
            return 'aprobación restaurada anterior al rechazo'
        if objetivo is None:
            cierre = subprocess.check_output(['git', 'log', '-1', '--format=%H', '-G',
                """^status:[[:space:]]*['"]?completed['"]?([[:space:]]|$)""", '--', ficha.relative_to(root).as_posix()],
                cwd=root, text=True).strip()
            objetivo = cierre or 'HEAD'
            referencia_informe = emision or (historial[0].decode('ascii') if historial else None)
            for posterior in (referencia_informe, commit_del_intento(root, iid)):
                if posterior and subprocess.run(['git', 'merge-base', '--is-ancestor', objetivo, posterior],
                                               cwd=root).returncode == 0:
                    objetivo = posterior
        if huella is not None:
            vigente = huella == huella_producto(root, objetivo, carpetas)
        elif emision:
            vigente = (emision == objetivo or
                       huella_producto(root, emision, carpetas) == huella_producto(root, objetivo, carpetas))
        else:
            vigente = not confirmar and not historial
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        return 'no se pudo acreditar el producto revisado'
    return '' if vigente else 'informe anterior al cambio de producto'


def motivo_informe(path):
    """Interpreta el dictamen formal de un informe de revisión."""
    try:
        texto = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return 'informe ausente'
    except (OSError, UnicodeError):
        return 'informe ilegible'
    veredicto, _ = declaracion(texto)
    if veredicto.upper() == 'APROBADO':
        return ''
    if veredicto.upper() == 'RECHAZADO':
        return 'informe rechazado'
    if veredicto.upper() == 'N/A':
        if any(re.match(r'Motivo:\s*.*(?:sin cambios de c[oó]digo|sin c[oó]digo|no hay cambios de c[oó]digo)',
                        linea or '', re.I) for linea in lineas_del_informe(texto)):
            return ''
        return 'N/A sin justificación de ausencia de código'
    return 'informe sin veredicto formal'


def diagnostico_revision(root, iid, ficha=None, carpetas=None):
    """Añade la última causa de cuota y la vía de recuperación sin invocar modelos."""
    motivo = motivo_revision(root, iid, ficha, carpetas)
    if not motivo:
        return ''
    ultimo = None
    for dato in leer_registros(root, tolerar_ultima=True):
        if dato.get('tipo') == 'agente' and dato.get('rol') == 'hades' and dato.get('id') == iid:
            ultimo = dato
    if ultimo and (ultimo.get('sin_cuota') or ultimo.get('cuota_espera_s')):
        motivo += '; Hades sin cuota: recuperar disponibilidad de Hades'
    return f'{iid}: {motivo}; obtener revisión con revisar-tarea y volver a validar el cierre.'


def pendientes_cierre(root, version, cfg=None):
    """Enumera maestros abiertos o completados sin revisión válida de este parche."""
    root = Path(root)
    if cfg is None:
        path = root / 'task_config.yaml'
        cfg = (load_yaml(path) or {}) if path.exists() else {}
    carpetas = carpetas_maestras(root, cfg)
    pendientes = []
    for carpeta in carpetas:
        for path in sorted(carpeta.glob('*.md')):
            texto = path.read_text(encoding='utf-8')
            m = re.match(r'^---\s*\n(.*?)\n---', texto, re.S)
            fm = (load_yaml(m[1]) or {}) if m else {}
            if not fm.get('id') or fm.get('parent_id') or clave_version(fm.get('version')) != clave_version(version):
                continue
            iid, status = str(fm['id']), str(fm.get('status', '')).lower()
            if status == 'completed':
                mensaje = diagnostico_revision(root, iid, path, carpetas)
                if mensaje:
                    pendientes.append(mensaje)
            elif status not in {'cancelled', 'superseded', 'rejected'}:
                pendientes.append(f'{iid}: trabajo pendiente ({status or "sin estado"}).')
    return pendientes
