#!/usr/bin/env python3
"""Lector de solo consulta y servidor MCP stdio para la conversación libre de Telegram.

Acota las herramientas efectivas de la conversación del gateway exclusivamente a
listar, leer y buscar texto en ficheros dentro de la raíz del proyecto, bloqueando
secretos locales (.env*, .git), enlaces simbólicos/junctions, rutas fuera del
proyecto y cualquier acción de escritura, borrado, ejecución o control de procesos.
"""

import argparse
from collections import deque
import fnmatch
import json
import os
import re
import stat
import sys
from pathlib import Path

ARNESES_CONVERSACION = ("claude", "codex", "agy")
DIRECTORIOS_OMITIDOS = frozenset(
    {
        ".git",
        "__pycache__",
        ".ruff_cache",
        ".pytest_cache",
        ".mypy_cache",
        "node_modules",
        ".venv",
        "venv",
    }
)
MAX_LINEAS_DEFECTO = 200
MAX_LINEAS_TOPE = 400
MAX_CARACTERES_SALIDA = 32768
MAX_BYTES_BUSQUEDA = 4 * 1024 * 1024
HERRAMIENTAS_LECTURA = ("listar_ficheros", "leer_fichero", "buscar_texto")


class PermisoLecturaError(PermissionError):
    """Indica que una ruta o acción excede el permiso de solo lectura del proyecto."""


def _es_enlace_o_reparse(ruta: Path) -> bool:
    """Detecta symlinks o junctions en POSIX y Windows sin seguir el destino."""
    try:
        st = os.lstat(ruta)
        if stat.S_ISLNK(st.st_mode):
            return True
        if hasattr(st, "st_file_attributes") and bool(st.st_file_attributes & 0x0400):
            return True
    except OSError:
        return False
    return ruta.is_symlink()


def _nombre_restringido(nombre: str) -> bool:
    bajo = nombre.lower()
    return bajo == ".git" or bajo == ".env" or bajo.startswith(".env.")


def resolver_ruta_lectura(root: Path, ruta: str = ".", *, directorio: bool = False) -> tuple[Path, str]:
    """Valida que `ruta` esté estrictamente dentro de `root` y sea apta para lectura."""
    if not isinstance(ruta, str) or not ruta.strip():
        ruta = "."
    limpia = ruta.strip()
    if "\x00" in limpia:
        raise PermisoLecturaError("Ruta inválida para lectura.")

    base_cruda = Path(root)
    if _es_enlace_o_reparse(base_cruda):
        raise PermisoLecturaError("La raíz del proyecto no puede ser un enlace simbólico.")
    base = base_cruda.resolve()

    candidata_cruda = Path(limpia)
    if not candidata_cruda.is_absolute():
        partes_norm = Path(os.path.normpath(limpia)).parts
        if any(p == ".." for p in partes_norm):
            raise PermisoLecturaError(f"Acceso denegado fuera del proyecto: {ruta}")
        candidata_cruda = base / limpia

    try:
        rel_partes = candidata_cruda.relative_to(base).parts
    except ValueError:
        try:
            resuelta_tmp = candidata_cruda.resolve()
            rel_partes = resuelta_tmp.relative_to(base).parts
            candidata_cruda = base.joinpath(*rel_partes)
        except (OSError, ValueError) as error:
            raise PermisoLecturaError(f"Acceso denegado fuera del proyecto: {ruta}") from error

    actual = base
    for parte in rel_partes:
        if parte in ("", "."):
            continue
        if parte == ".." or _nombre_restringido(parte):
            raise PermisoLecturaError(f"Acceso de lectura denegado sobre ruta protegida: {ruta}")
        actual = actual / parte
        if _es_enlace_o_reparse(actual):
            raise PermisoLecturaError(f"Acceso denegado a enlace simbólico o junction: {ruta}")

    try:
        resuelta = actual.resolve()
        rel_final = resuelta.relative_to(base)
    except (OSError, ValueError) as error:
        raise PermisoLecturaError(f"Acceso denegado fuera del proyecto: {ruta}") from error

    for parte in rel_final.parts:
        if _nombre_restringido(parte):
            raise PermisoLecturaError(f"Acceso de lectura denegado sobre ruta protegida: {ruta}")

    if not resuelta.exists():
        raise FileNotFoundError(f"No existe en el proyecto: {ruta}")
    if directorio and not resuelta.is_dir():
        raise ValueError(f"No es un directorio: {ruta}")
    if not directorio and not resuelta.is_file():
        raise ValueError(f"No es un fichero regular: {ruta}")

    rel_posix = "." if not rel_final.parts else rel_final.as_posix()
    return resuelta, rel_posix


def _es_binario(ruta: Path) -> bool:
    try:
        with ruta.open("rb") as f:
            muestra = f.read(4096)
        return b"\x00" in muestra
    except OSError:
        return True


def _iterar_ficheros_legibles(base: Path, inicio: Path):
    """Recorre recursivamente ficheros regulares legibles dentro de `inicio`."""
    for dirpath, dirnames, filenames in os.walk(inicio, followlinks=False):
        actual = Path(dirpath)
        dirnames[:] = sorted(
            d
            for d in dirnames
            if d not in DIRECTORIOS_OMITIDOS and not _nombre_restringido(d) and not _es_enlace_o_reparse(actual / d)
        )
        for nombre in sorted(filenames):
            if _nombre_restringido(nombre):
                continue
            fichero = actual / nombre
            if _es_enlace_o_reparse(fichero) or not fichero.is_file():
                continue
            try:
                rel = fichero.resolve().relative_to(base).as_posix()
            except (OSError, ValueError):
                continue
            yield fichero, rel


def listar_ficheros(root: Path, directorio: str = ".", patron: str = "*", limite: int = 200) -> str:
    """Lista ficheros legibles dentro del directorio indicado del proyecto."""
    base = Path(root).resolve()
    inicio, rel_dir = resolver_ruta_lectura(base, directorio, directorio=True)
    patron_limpio = (patron or "*").strip() or "*"
    tope = max(1, min(int(limite or 200), 500))
    encontrados = []
    truncado = False

    for _, rel in _iterar_ficheros_legibles(base, inicio):
        nombre = rel.rsplit("/", 1)[-1]
        if fnmatch.fnmatch(nombre, patron_limpio) or fnmatch.fnmatch(rel, patron_limpio):
            if len(encontrados) >= tope:
                truncado = True
                break
            encontrados.append(rel)

    if not encontrados:
        return f"Directorio {rel_dir}: sin ficheros coincidentes con {patron_limpio!r}."
    cabecera = f"Directorio {rel_dir} ({len(encontrados)} ficheros" + (", lista truncada):" if truncado else "):")
    return cabecera + "\n" + "\n".join(encontrados)


def leer_fichero(
    root: Path,
    ruta: str,
    desde_linea: int = 1,
    max_lineas: int = MAX_LINEAS_DEFECTO,
) -> str:
    """Lee líneas UTF-8 numeradas de un fichero del proyecto (`desde_linea < 0` lee la cola)."""
    if not isinstance(ruta, str) or not ruta.strip():
        raise ValueError("Debes indicar la ruta del fichero a leer.")
    fichero, rel = resolver_ruta_lectura(Path(root), ruta, directorio=False)
    if _es_binario(fichero):
        raise PermisoLecturaError(f"El fichero es binario y no puede leerse como texto: {rel}")

    inicio = int(desde_linea if desde_linea is not None else 1)
    cantidad = max(1, min(int(max_lineas or MAX_LINEAS_DEFECTO), MAX_LINEAS_TOPE))

    if inicio < 0:
        cola = deque(maxlen=min(abs(inicio), MAX_LINEAS_TOPE))
        total = 0
        with fichero.open("r", encoding="utf-8", errors="replace") as f:
            for num, texto_linea in enumerate(f, 1):
                total = num
                cola.append((num, texto_linea.rstrip("\r\n")))
        seleccion = list(cola)[:cantidad]
    else:
        inicio = max(1, inicio)
        fin_buscado = inicio + cantidad - 1
        seleccion = []
        total = 0
        with fichero.open("r", encoding="utf-8", errors="replace") as f:
            for num, texto_linea in enumerate(f, 1):
                total = num
                if inicio <= num <= fin_buscado:
                    seleccion.append((num, texto_linea.rstrip("\r\n")))

    if total == 0:
        return f"Fichero: {rel} (vacío)"
    if not seleccion:
        return f"Fichero: {rel} (fuera de rango; total {total} líneas)"

    primera, ultima = seleccion[0][0], seleccion[-1][0]
    cuerpo = "\n".join(f"{num}: {contenido}" for num, contenido in seleccion)
    if len(cuerpo) > MAX_CARACTERES_SALIDA:
        cuerpo = cuerpo[:MAX_CARACTERES_SALIDA] + "\n... [contenido recortado por longitud]"
    return f"Fichero: {rel} (líneas {primera}-{ultima} de {total})\n{cuerpo}"


def buscar_texto(root: Path, consulta: str, directorio: str = ".", limite: int = 50) -> str:
    """Busca texto o expresión regular en los ficheros legibles del proyecto."""
    if not isinstance(consulta, str) or not consulta.strip():
        raise ValueError("Debes indicar el texto o patrón a buscar.")
    base = Path(root).resolve()
    inicio, _ = resolver_ruta_lectura(base, directorio, directorio=True)
    tope = max(1, min(int(limite or 50), 200))
    try:
        patron = re.compile(consulta, re.IGNORECASE)
    except re.error:
        patron = re.compile(re.escape(consulta), re.IGNORECASE)

    coincidencias = []
    truncado = False
    for fichero, rel in _iterar_ficheros_legibles(base, inicio):
        try:
            if fichero.stat().st_size > MAX_BYTES_BUSQUEDA or _es_binario(fichero):
                continue
            with fichero.open("r", encoding="utf-8", errors="replace") as f:
                for num, linea in enumerate(f, 1):
                    if patron.search(linea):
                        fragmento = linea.strip()[:240]
                        coincidencias.append(f"{rel}:{num}: {fragmento}")
                        if len(coincidencias) >= tope:
                            truncado = True
                            break
        except OSError:
            continue
        if truncado:
            break

    if not coincidencias:
        return f"Sin coincidencias para {consulta!r}."
    cabecera = f"Coincidencias ({len(coincidencias)}" + (", truncadas):" if truncado else "):")
    return cabecera + "\n" + "\n".join(coincidencias)


def ejecutar_herramienta(root: Path, nombre: str, argumentos: dict | None = None) -> str:
    """Ejecuta únicamente herramientas de lectura; rechaza cualquier otra acción."""
    args = argumentos if isinstance(argumentos, dict) else {}
    if nombre == "listar_ficheros":
        return listar_ficheros(
            root,
            directorio=str(args.get("directorio", ".")),
            patron=str(args.get("patron", "*")),
            limite=int(args.get("limite", 200)),
        )
    if nombre == "leer_fichero":
        return leer_fichero(
            root,
            ruta=str(args.get("ruta", "")),
            desde_linea=int(args.get("desde_linea", 1)),
            max_lineas=int(args.get("max_lineas", MAX_LINEAS_DEFECTO)),
        )
    if nombre == "buscar_texto":
        return buscar_texto(
            root,
            consulta=str(args.get("consulta", "")),
            directorio=str(args.get("directorio", ".")),
            limite=int(args.get("limite", 50)),
        )
    raise PermisoLecturaError(
        f"Acción denegada ({nombre}): la conversación de Telegram solo tiene permiso para consultar ficheros del proyecto."
    )


def evaluar_permiso_conversacion(root: Path, accion: str, objetivo: str = "") -> tuple[bool, str]:
    """Evalúa si una operación está permitida bajo la política efectiva de conversación."""
    accion_norm = (accion or "").strip().lower()
    lecturas = {"read", "read_file", "glob", "grep", "listar_ficheros", "leer_fichero", "buscar_texto"}
    if accion_norm not in lecturas:
        return False, f"Acción denegada ({accion}): solo se permite consultar ficheros del proyecto."
    if not objetivo or accion_norm in ("glob", "grep", "listar_ficheros", "buscar_texto"):
        ruta_obj = objetivo or "."
        try:
            base = Path(root).resolve()
            candidata = Path(ruta_obj)
            if not candidata.is_absolute():
                partes = Path(os.path.normpath(ruta_obj)).parts
                if any(p == ".." or _nombre_restringido(p) for p in partes):
                    return False, f"Acceso de lectura denegado sobre ruta protegida o externa: {objetivo}"
                candidata = base / ruta_obj
            if _es_enlace_o_reparse(candidata):
                return False, f"Acceso denegado a enlace simbólico: {objetivo}"
            rel = candidata.resolve().relative_to(base)
            if any(_nombre_restringido(p) for p in rel.parts):
                return False, f"Acceso de lectura denegado sobre ruta protegida: {objetivo}"
            return True, "lectura permitida"
        except (OSError, ValueError):
            return False, f"Acceso denegado fuera del proyecto: {objetivo}"
    try:
        resolver_ruta_lectura(Path(root), objetivo, directorio=False)
        return True, "lectura permitida"
    except PermisoLecturaError as error:
        return False, str(error)
    except (FileNotFoundError, ValueError):
        # El permiso de lectura sobre la ruta interna existe aunque el fichero aún no exista.
        return True, "lectura permitida"


def settings_agy_solo_lectura(root: Path) -> str:
    """Construye la política de sesión de Antigravity limitada a lectura del proyecto."""
    raiz_posix = Path(root).resolve().as_posix()
    politica = {
        "permissions": {
            "allow": [
                "read_file(.)",
                f"read_file({raiz_posix})",
            ],
            "deny": [
                "write_file(*)",
                "command(*)",
                "unsandboxed(*)",
                "read_url(*)",
                "execute_url(*)",
                "mcp(*)",
                "read_file(.env)",
                "read_file(.env.*)",
                "read_file(**/.env)",
                "read_file(**/.env.*)",
                "read_file(.git/**)",
            ],
        }
    }
    return json.dumps(politica, ensure_ascii=False, separators=(",", ":"))


def settings_claude_solo_lectura() -> str:
    """Construye la política de sesión de Claude Code limitada a Read, Glob y Grep."""
    politica = {
        "permissions": {
            "allow": ["Read", "Glob", "Grep"],
            "deny": [
                "Bash",
                "Write",
                "Edit",
                "NotebookEdit",
                "WebFetch",
                "WebSearch",
                "Read(.env)",
                "Read(.env.*)",
                "Read(**/.env)",
                "Read(**/.env.*)",
                "Read(.git/**)",
            ],
        }
    }
    return json.dumps(politica, ensure_ascii=False, separators=(",", ":"))


def config_mcp_codex(root: Path, ejecutable_python: str | None = None) -> str:
    """Genera el bloque TOML inline `mcp_servers` de Codex con solo el lector del proyecto."""
    py = json.dumps(ejecutable_python or sys.executable, ensure_ascii=False)
    script = json.dumps(str(Path(__file__).resolve()), ensure_ascii=False)
    raiz = json.dumps(str(Path(root).resolve()), ensure_ascii=False)
    return f'mcp_servers={{proyecto={{command={py},args=[{script},"--root",{raiz}]}}}}'


def comando_conversacion(harness: str, prompt: str, root: Path, sesion: str | None = None) -> list[str] | None:
    """Construye el comando base de conversación de Telegram con permisos estrictos de solo lectura."""
    if harness == "claude":
        prefijo = ["claude", "--resume", sesion] if sesion else ["claude"]
        return prefijo + [
            "-p",
            "--restricted",
            "--permission-mode",
            "dontAsk",
            "--permission-prompts",
            "none",
            "--tools",
            "Read,Glob,Grep",
            "--allowedTools",
            "Read,Glob,Grep",
            "--disallowedTools",
            "Bash,Write,Edit,NotebookEdit,WebFetch,WebSearch",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--system-prompt-snapshot",
            "off",
            "--settings",
            settings_claude_solo_lectura(),
            "--output-format",
            "json",
        ]
    if harness == "codex":
        prefijo = ["codex", "exec", "resume", sesion] if sesion else ["codex", "exec"]
        sandbox = ["-c", 'sandbox_mode="read-only"'] if sesion else ["--sandbox", "read-only"]
        return (
            prefijo
            + [
                "--json",
                "-c",
                'approval_policy="never"',
            ]
            + sandbox
            + [
                "--ignore-rules",
                "-c",
                "features.shell_tool=false",
                "-c",
                "features.unified_exec=false",
                "-c",
                "features.apps=false",
                "-c",
                "features.plugins=false",
                "-c",
                "features.multi_agent=false",
                "-c",
                config_mcp_codex(root),
                "-",
            ]
        )
    if harness == "agy":
        prefijo = ["agy", "--conversation", sesion] if sesion else ["agy"]
        return prefijo + [
            "--sandbox",
            "--disable-slash-commands",
            "--settings",
            settings_agy_solo_lectura(root),
            "--output-format",
            "json",
            "-p",
            prompt,
        ]
    return None


ESQUEMA_HERRAMIENTAS_MCP = [
    {
        "name": "listar_ficheros",
        "description": "Lista los ficheros legibles del proyecto dentro de un directorio.",
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
        "inputSchema": {
            "type": "object",
            "properties": {
                "directorio": {"type": "string", "description": "Directorio relativo al proyecto (por defecto '.')."},
                "patron": {"type": "string", "description": "Filtro glob opcional (por defecto '*')."},
                "limite": {"type": "integer", "description": "Máximo de ficheros a listar (1-500)."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "leer_fichero",
        "description": "Lee líneas numeradas actuales desde disco de un fichero del proyecto.",
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
        "inputSchema": {
            "type": "object",
            "properties": {
                "ruta": {"type": "string", "description": "Ruta relativa del fichero dentro del proyecto."},
                "desde_linea": {
                    "type": "integer",
                    "description": "Línea inicial (1-based) o negativa para leer las últimas N líneas.",
                },
                "max_lineas": {"type": "integer", "description": "Máximo de líneas a devolver (1-400)."},
            },
            "required": ["ruta"],
            "additionalProperties": False,
        },
    },
    {
        "name": "buscar_texto",
        "description": "Busca texto o patrón en los ficheros legibles del proyecto.",
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
        "inputSchema": {
            "type": "object",
            "properties": {
                "consulta": {"type": "string", "description": "Texto o expresión regular a buscar."},
                "directorio": {"type": "string", "description": "Subdirectorio relativo donde acotar la búsqueda."},
                "limite": {"type": "integer", "description": "Máximo de coincidencias (1-200)."},
            },
            "required": ["consulta"],
            "additionalProperties": False,
        },
    },
]


def _procesar_mensaje_mcp(root: Path, mensaje: dict) -> dict | None:
    """Procesa una petición JSON-RPC 2.0 del protocolo MCP."""
    metodo = mensaje.get("method")
    tiene_id = "id" in mensaje
    msg_id = mensaje.get("id")
    params = mensaje.get("params") if isinstance(mensaje.get("params"), dict) else {}

    if not tiene_id:
        return None

    if metodo == "initialize":
        version_cliente = str(params.get("protocolVersion") or "2024-11-05")
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": version_cliente,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "adevv-lector-proyecto", "version": "1.0.0"},
            },
        }
    if metodo == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if metodo == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": ESQUEMA_HERRAMIENTAS_MCP}}
    if metodo == "resources/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": []}}
    if metodo == "prompts/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"prompts": []}}
    if metodo == "tools/call":
        nombre = str(params.get("name") or "")
        argumentos = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        try:
            salida = ejecutar_herramienta(root, nombre, argumentos)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": salida}], "isError": False},
            }
        except (PermisoLecturaError, FileNotFoundError, ValueError, OSError) as error:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": str(error)}], "isError": True},
            }
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Método no soportado en modo solo lectura: {metodo}"},
    }


def _leer_mensaje_stdio(stream) -> tuple[dict | None, bool]:
    """Lee un mensaje JSON-RPC por NDJSON o Content-Length; devuelve (mensaje, usa_headers)."""
    while True:
        linea = stream.readline()
        if not linea:
            return None, False
        texto = linea.decode("utf-8", errors="replace").strip()
        if not texto:
            continue
        if texto.lower().startswith("content-length:"):
            longitud = int(texto.split(":", 1)[1].strip())
            while True:
                cab = stream.readline()
                if not cab or not cab.strip():
                    break
            cuerpo = stream.read(longitud)
            if not cuerpo:
                return None, True
            return json.loads(cuerpo.decode("utf-8", errors="replace")), True
        return json.loads(texto), False


def _escribir_mensaje_stdio(stream, respuesta: dict, usar_headers: bool) -> None:
    datos = json.dumps(respuesta, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if usar_headers:
        stream.write(f"Content-Length: {len(datos)}\r\n\r\n".encode("ascii") + datos)
    else:
        stream.write(datos + b"\n")
    stream.flush()


def servir_mcp_stdio(root: Path, entrada=None, salida=None) -> int:
    """Atiende peticiones MCP JSON-RPC de solo lectura sobre stdio."""
    base = Path(root).resolve()
    lector = entrada if entrada is not None else sys.stdin.buffer
    escritor = salida if salida is not None else sys.stdout.buffer
    while True:
        try:
            mensaje, usar_headers = _leer_mensaje_stdio(lector)
        except (ValueError, OSError) as error:
            respuesta_err = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"JSON inválido: {error}"},
            }
            _escribir_mensaje_stdio(escritor, respuesta_err, False)
            continue
        if mensaje is None:
            return 0
        if not isinstance(mensaje, dict):
            continue
        respuesta = _procesar_mensaje_mcp(base, mensaje)
        if respuesta is not None:
            _escribir_mensaje_stdio(escritor, respuesta, usar_headers)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Servidor MCP stdio de solo lectura para proyectos Adevv.")
    ap.add_argument("--root", type=Path, required=True, help="Raíz del proyecto autorizada para lectura")
    args = ap.parse_args(argv)
    return servir_mcp_stdio(args.root.resolve())


if __name__ == "__main__":
    sys.exit(main())
