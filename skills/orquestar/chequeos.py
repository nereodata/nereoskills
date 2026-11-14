"""Planificación, ejecución coordinada y reutilización de chequeos de calidad y release."""

from contextlib import contextmanager
from datetime import datetime
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time

from adevv import registro_metricas

try:
    import yaml
except ImportError:
    try:
        from adevv import yaml_lite as yaml
    except ImportError:
        yaml = None

try:
    from . import calidad
except ImportError:
    import importlib.util as _ilu

    _calidad_spec = _ilu.spec_from_file_location("adevv_calidad_interno", Path(__file__).with_name("calidad.py"))
    calidad = _ilu.module_from_spec(_calidad_spec)
    _calidad_spec.loader.exec_module(calidad)


ETAPAS_CATALOGO = (
    "formato",
    "lint",
    "tipado",
    "seguridad",
    "secretos",
    "dependencias",
    "pruebas",
    "builds",
)
DISPONIBILIDADES = ("configurado", "ausente", "omitido")
RESULTADOS = ("sin_acreditar", "pendiente", "ejecutando", "aprobado", "fallido", "interrumpido")
CANALES = ("cli", "gateway", "agente", "release")
ACCIONES_RELEASE = ("validar", "cerrar_local", "etiquetar", "publicar")
EVIDENCIAS = "orquestar_evidencias.jsonl"
METRICAS = registro_metricas.ARCHIVO
ESTADO_EN_CURSO = "estado_en_curso.json"
IGNORADOS_PROPIOS = {
    "/" + registro_metricas.AUXILIAR + "/",
    EVIDENCIAS,
    METRICAS,
    "orquestar.log",
    "orquestar.pid",
    "orquestar.parar",
    "orquestar.espera",
    "orquestar_buzon.jsonl",
    "orquestar_buzon.jsonl.tmp",
    ".env",
    "orquestar_telegram.json",
    "orquestar_prompt.txt",
    "telegram.pid",
    "telegram.log",
    "telegram.parar",
    "orquestar_preguntas.json",
    "orquestar_respuestas.jsonl",
    "adevv-intervencion-*",
}
ARCHIVOS_CONFIGURACION = (
    "pyproject.toml",
    "package.json",
    "ruff.toml",
    ".ruff.toml",
    "tsconfig.json",
    "setup.cfg",
)
ARCHIVOS_DEPENDENCIAS = (
    "requirements.lock",
    "requirements.txt",
    "uv.lock",
    "poetry.lock",
    "Pipfile.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
)

if not hasattr(sys, "_adevv_chequeos_lock"):
    sys._adevv_chequeos_lock = threading.Lock()
if not hasattr(sys, "_adevv_chequeos_memoria"):
    sys._adevv_chequeos_memoria = {}
_LOCK_GLOBAL = sys._adevv_chequeos_lock
_EJECUCIONES_MEMORIA = sys._adevv_chequeos_memoria


def _ahora():
    """Devuelve la fecha y hora local en formato ISO-8601 al segundo."""
    return datetime.now().isoformat(timespec="seconds")


def _proceso_vivo(pid):
    """Comprueba si existe un proceso activo con el PID indicado."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() == 5
        try:
            codigo = ctypes.c_ulong()
            return not kernel.GetExitCodeProcess(handle, ctypes.byref(codigo)) or codigo.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def directorio_git_comun(root):
    """Resuelve sin subprocesos el directorio Git común compartido entre el árbol principal y sus worktrees."""
    base = Path(root).resolve()
    dot_git = base / ".git"
    if dot_git.is_dir():
        commondir_file = dot_git / "commondir"
        if commondir_file.is_file():
            rel = commondir_file.read_text(encoding="utf-8", errors="replace").strip()
            return (dot_git / rel).resolve()
        return dot_git.resolve()
    if dot_git.is_file():
        try:
            contenido = dot_git.read_text(encoding="utf-8", errors="replace").strip()
            if contenido.lower().startswith("gitdir:"):
                raw_gitdir = contenido.split(":", 1)[1].strip()
                gitdir_path = Path(raw_gitdir)
                if not gitdir_path.is_absolute():
                    gitdir_path = (base / gitdir_path).resolve()
                commondir_file = gitdir_path / "commondir"
                if commondir_file.is_file():
                    rel = commondir_file.read_text(encoding="utf-8", errors="replace").strip()
                    return (gitdir_path / rel).resolve()
                return gitdir_path.parent.parent.resolve()
        except OSError:
            pass
    return dot_git.resolve()


def _excluir_propios(root):
    """Asegura que los artefactos de orquestación estén excluidos en info/exclude del repositorio."""
    try:
        comun = directorio_git_comun(root)
        if not comun.is_dir():
            return
        exclude = comun / "info" / "exclude"
        actual = exclude.read_text(encoding="utf-8", errors="replace") if exclude.is_file() else ""
        lineas = set(actual.splitlines())
        faltan = [nombre for nombre in sorted(IGNORADOS_PROPIOS) if nombre not in lineas]
        if faltan:
            exclude.parent.mkdir(parents=True, exist_ok=True)
            with exclude.open("a", encoding="utf-8") as f:
                f.write("\n" + "\n".join(faltan) + "\n")
    except OSError:
        pass


def directorio_coordinacion(root, crear=True):
    """Devuelve el directorio de coordinación compartido en el directorio Git común."""
    comun = directorio_git_comun(root)
    coord = comun / "adevv-chequeos"
    if crear and comun.exists():
        coord.mkdir(parents=True, exist_ok=True)
    return coord


@contextmanager
def indice_de_trabajo(root):
    """Captura el contenido rastreable del árbol sin modificar el índice del usuario."""
    base = Path(root).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmp) / "index")}
        entradas = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=base)
        if entradas:
            subprocess.run(
                ["git", "update-index", "-z", "--index-info"],
                cwd=base,
                env=env,
                input=entradas,
                capture_output=True,
                check=True,
            )
        subprocess.run(["git", "add", "-A", "."], cwd=base, env=env, capture_output=True, check=True)
        yield env


def arbol_trabajo(root):
    """Calcula el hash del árbol de trabajo completo incluyendo cambios sin commitear y no ignorados."""
    base = Path(root).resolve()
    _excluir_propios(base)
    with indice_de_trabajo(base) as env:
        valor = subprocess.run(
            ["git", "write-tree"],
            cwd=base,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", valor):
            raise RuntimeError("No se pudo calcular una huella Git válida del árbol")
        return valor


def _listar_ficheros_repositorio(root):
    """Obtiene la lista ordenada de ficheros del árbol de trabajo excluyendo .git y artefactos propios."""
    base = Path(root).resolve()
    resultado = []
    for dirpath, dirnames, filenames in os.walk(base):
        if Path(dirpath) == base and registro_metricas.AUXILIAR in dirnames:
            dirnames.remove(registro_metricas.AUXILIAR)
        dirnames[:] = [
            d for d in sorted(dirnames) if d not in (".git", "__pycache__") and not d.startswith("adevv-intervencion-")
        ]
        rel_dir = Path(dirpath).resolve().relative_to(base)
        for fname in sorted(filenames):
            if fname == ".git":
                continue
            if rel_dir == Path(".") and (fname in IGNORADOS_PROPIOS or fname.startswith("adevv-intervencion-")):
                continue
            rel_path = (rel_dir / fname).as_posix() if rel_dir != Path(".") else fname
            resultado.append(rel_path)
    return sorted(resultado)


def cargar_configuracion(root):
    """Lee y valida estrictamente las secciones validation y release de task_config.yaml."""
    fichero = Path(root) / "task_config.yaml"
    if not fichero.exists():
        return {}
    texto = fichero.read_text(encoding="utf-8")
    if yaml and hasattr(yaml, "safe_load"):
        cfg = yaml.safe_load(texto)
    elif yaml and hasattr(yaml, "load_yaml"):
        cfg = yaml.load_yaml(fichero)
    else:
        cfg = {}
    if cfg is None:
        return {}
    if not isinstance(cfg, dict):
        raise ValueError("task_config.yaml debe ser un mapa")
    _validar_configuracion(cfg)
    return cfg


def _validar_configuracion(cfg):
    """Rechaza configuraciones inválidas en validation y release identificando la clave infractora."""
    validation = cfg.get("validation")
    if validation is not None:
        if not isinstance(validation, dict):
            raise ValueError("Configuración inválida en validation: debe ser un mapa")
        for clave, valor in validation.items():
            if clave in ("command", "formato_escritura"):
                if not isinstance(valor, str) or not valor.strip():
                    raise ValueError(f"Configuración inválida en validation.{clave}: debe ser una cadena no vacía")
                continue
            if clave in ETAPAS_CATALOGO:
                if isinstance(valor, str):
                    if not valor.strip():
                        raise ValueError(f"Configuración inválida en validation.{clave}: comando vacío")
                elif isinstance(valor, dict):
                    for subclave in ("comando", "command"):
                        if subclave in valor:
                            subval = valor[subclave]
                            if not isinstance(subval, str) or not subval.strip():
                                raise ValueError(
                                    f"Configuración inválida en validation.{clave}.{subclave}: debe ser cadena no vacía"
                                )
                    if "obligatorio" in valor and not isinstance(valor["obligatorio"], bool):
                        raise ValueError(f"Configuración inválida en validation.{clave}.obligatorio: debe ser booleano")
                    if "entradas" in valor:
                        entradas = valor["entradas"]
                        if not isinstance(entradas, list) or not all(
                            isinstance(x, str) and x.strip() for x in entradas
                        ):
                            raise ValueError(
                                f"Configuración inválida en validation.{clave}.entradas: debe ser lista de rutas"
                            )
                else:
                    raise ValueError(
                        f"Configuración inválida en validation.{clave}: se esperaba cadena o mapa de configuración"
                    )
    release = cfg.get("release")
    if release is not None:
        if not isinstance(release, dict):
            raise ValueError("Configuración inválida en release: debe ser un mapa")
        if "puertas" in release:
            puertas = release["puertas"]
            if not isinstance(puertas, list) or not all(isinstance(p, str) and p in ETAPAS_CATALOGO for p in puertas):
                raise ValueError(
                    "Configuración inválida en release.puertas: debe ser una lista de etapas válidas del catálogo"
                )
        if "preflight" in release:
            preflight = release["preflight"]
            if not isinstance(preflight, list) or not all(isinstance(c, str) and c.strip() for c in preflight):
                raise ValueError("Configuración inválida en release.preflight: debe ser una lista de comandos")
        if "restricciones" in release:
            restricciones = release["restricciones"]
            if not isinstance(restricciones, dict):
                raise ValueError("Configuración inválida en release.restricciones: debe ser un mapa")
            for r_clave, r_val in restricciones.items():
                if r_clave in ACCIONES_RELEASE:
                    if isinstance(r_val, bool):
                        continue
                    if isinstance(r_val, list) and all(isinstance(c, str) and c in CANALES for c in r_val):
                        continue
                    raise ValueError(f"Configuración inválida en release.restricciones.{r_clave}: valor no reconocido")
                elif r_clave in CANALES:
                    if isinstance(r_val, bool):
                        continue
                    if isinstance(r_val, dict) and all(
                        k in ACCIONES_RELEASE and isinstance(v, bool) for k, v in r_val.items()
                    ):
                        continue
                    raise ValueError(
                        f"Configuración inválida en release.restricciones.{r_clave}: mapa de acciones inválido"
                    )
                else:
                    raise ValueError(f"Configuración inválida en release.restricciones.{r_clave}: clave desconocida")


def verificar_restriccion_release(root, canal, accion, cfg=None):
    """Comprueba si un canal está autorizado para ejecutar una acción de release según task_config.yaml."""
    if cfg is None:
        cfg = cargar_configuracion(root)
    else:
        _validar_configuracion(cfg)
    restricciones = ((cfg.get("release") or {}).get("restricciones")) or {}
    if canal in restricciones:
        regla_canal = restricciones[canal]
        if isinstance(regla_canal, bool) and not regla_canal:
            raise ValueError(f"Restricción de release: el canal {canal} no tiene permitido ejecutar {accion}.")
        if isinstance(regla_canal, dict) and regla_canal.get(accion) is False:
            raise ValueError(f"Restricción de release: el canal {canal} no tiene permitido {accion}.")
    if accion in restricciones:
        regla_accion = restricciones[accion]
        if isinstance(regla_accion, bool) and not regla_accion:
            raise ValueError(
                f"Restricción de release: la acción {accion} está deshabilitada por restricción del proyecto."
            )
        if isinstance(regla_accion, list) and canal not in regla_accion:
            raise ValueError(f"Restricción de release: la acción {accion} no está permitida desde el canal {canal}.")
    return True


def _comando_texto(comando):
    """Normaliza un comando en lista o cadena a su representación textual estable."""
    if comando is None:
        return None
    if isinstance(comando, str):
        return comando
    return " ".join(str(x) for x in comando)


def resolver_catalogo(root, cfg=None, ficheros=None):
    """Resuelve todas las etapas del catálogo indicando disponibilidad, comando efectivo, origen y entradas."""
    base = Path(root).resolve()
    if cfg is None:
        cfg = cargar_configuracion(base)
    validation = cfg.get("validation") or {}
    ficheros_repo = [
        f for f in (_listar_ficheros_repositorio(base) if ficheros is None else ficheros) if (base / f).is_file()
    ]
    scripts, ruff, _ = calidad._manifiestos(base)
    catalogo = {}

    for etapa in ETAPAS_CATALOGO:
        spec = validation.get(etapa)
        obligatorio = False
        entradas = None
        cmd_declarado = None
        if isinstance(spec, str):
            cmd_declarado = spec.strip()
            obligatorio = True
        elif isinstance(spec, dict):
            cmd_declarado = (spec.get("comando") or spec.get("command") or "").strip() or None
            obligatorio = bool(spec.get("obligatorio", bool(cmd_declarado)))
            entradas = list(spec["entradas"]) if "entradas" in spec else None

        if etapa == "pruebas" and not cmd_declarado and isinstance(validation.get("command"), str):
            cmd_declarado = validation["command"].strip()
            origen_pruebas = "task_config.yaml (validation.command)"
            obligatorio = True
        else:
            origen_pruebas = f"task_config.yaml (validation.{etapa})"

        if cmd_declarado:
            comando_efectivo = calidad._expandir(cmd_declarado, ficheros_repo, etapa)
            if isinstance(comando_efectivo, list) and not ficheros_repo and "{ficheros}" in cmd_declarado:
                catalogo[etapa] = {
                    "etapa": etapa,
                    "disponibilidad": "omitido",
                    "comando": None,
                    "comando_texto": None,
                    "origen": origen_pruebas,
                    "obligatorio": obligatorio,
                    "entradas": entradas,
                    "herramienta": None,
                    "motivo": "sin objetivos compatibles",
                }
                continue
            catalogo[etapa] = {
                "etapa": etapa,
                "disponibilidad": "configurado",
                "comando": comando_efectivo,
                "comando_texto": _comando_texto(comando_efectivo),
                "origen": origen_pruebas,
                "obligatorio": obligatorio,
                "entradas": entradas,
                "herramienta": None,
                "motivo": "configurado explícitamente",
            }
            continue

        if etapa in ("formato", "lint"):
            cmd_ded, _, herramienta, _ = calidad._deducir(etapa, scripts, ruff)
            if cmd_ded is not None:
                if herramienta in ("prettier", "eslint"):
                    clave_script = "format:check" if etapa == "formato" else "lint"
                    origen_ded = f"deducido de package.json (scripts.{clave_script})"
                else:
                    origen_ded = "deducido de pyproject.toml (tool.ruff)"
                objetivos = [
                    ("./" + f if f.startswith("-") else f)
                    for f in ficheros_repo
                    if Path(f).suffix.lower() in calidad.EXTENSIONES[herramienta]
                ]
                if objetivos:
                    cmd_lista = cmd_ded + objetivos
                    catalogo[etapa] = {
                        "etapa": etapa,
                        "disponibilidad": "configurado",
                        "comando": cmd_lista,
                        "comando_texto": _comando_texto(cmd_lista),
                        "origen": origen_ded,
                        "obligatorio": obligatorio,
                        "entradas": entradas,
                        "herramienta": herramienta,
                        "motivo": origen_ded,
                    }
                    continue
                catalogo[etapa] = {
                    "etapa": etapa,
                    "disponibilidad": "omitido",
                    "comando": None,
                    "comando_texto": None,
                    "origen": origen_ded,
                    "obligatorio": obligatorio,
                    "entradas": entradas,
                    "herramienta": herramienta,
                    "motivo": "sin objetivos compatibles",
                }
                continue

        motivo_ausente = "análisis obligatorio ausente" if obligatorio else "análisis opcional no configurado"
        catalogo[etapa] = {
            "etapa": etapa,
            "disponibilidad": "ausente",
            "comando": None,
            "comando_texto": None,
            "origen": None,
            "obligatorio": obligatorio,
            "entradas": entradas,
            "herramienta": None,
            "motivo": motivo_ausente,
        }
    return catalogo


def _hash_archivos(base, nombres):
    """Calcula un hash SHA-256 determinista del conjunto de archivos existentes de la lista."""
    digest = hashlib.sha256()
    for nombre in sorted(nombres):
        ruta = base / nombre
        if ruta.is_file():
            digest.update(nombre.encode("utf-8"))
            digest.update(b"\0")
            contenido = ruta.read_bytes().replace(b"\r\n", b"\n")
            digest.update(hashlib.sha256(contenido).digest())
            digest.update(b"\0")
    return digest.hexdigest()


def _calcular_entorno(root, entorno_override=None):
    """Calcula la huella del entorno relevante (herramienta, configuración, dependencias y plataforma)."""
    base = Path(root).resolve()
    entorno = {
        "herramienta": f"python-{sys.version.split()[0]}",
        "configuracion": _hash_archivos(base, ARCHIVOS_CONFIGURACION),
        "dependencias": _hash_archivos(base, ARCHIVOS_DEPENDENCIAS),
        "plataforma": f"{sys.platform}-py{sys.version_info.major}.{sys.version_info.minor}",
    }
    if entorno_override:
        for k, v in entorno_override.items():
            if v is not None:
                entorno[k] = str(v)
    return entorno


def _coincide_entrada(ruta_rel, patron):
    """Indica si una ruta relativa pertenece al prefijo o archivo declarado en entradas."""
    ruta_norm = ruta_rel.replace("\\", "/").strip("/")
    pat_norm = patron.replace("\\", "/").strip("/")
    if not pat_norm:
        return True
    return ruta_norm == pat_norm or ruta_norm.startswith(pat_norm + "/")


def _info_para_comando(root, etapa=None, comando=None, cfg=None, catalogo=None):
    """Resuelve la etapa y metadatos de configuración aplicables a una etapa o comando."""
    base = Path(root).resolve()
    if catalogo is None:
        if cfg is None:
            try:
                cfg = cargar_configuracion(base)
            except Exception:
                cfg = {}
        try:
            catalogo = resolver_catalogo(base, cfg=cfg)
        except Exception:
            catalogo = {}

    cmd_txt = _comando_texto(comando) if comando is not None else None
    if etapa and etapa in catalogo and (cmd_txt is None or catalogo[etapa].get("comando_texto") == cmd_txt):
        info = dict(catalogo[etapa])
        if comando is not None:
            info["disponibilidad"] = "configurado"
            info["comando"] = comando
            info["comando_texto"] = cmd_txt
        return etapa, info

    if cmd_txt is not None:
        for et_cat, item in catalogo.items():
            if item.get("disponibilidad") == "configurado" and item.get("comando_texto") == cmd_txt:
                info = dict(item)
                info["comando"] = comando
                info["comando_texto"] = cmd_txt
                return et_cat, info

    etapa_ef = etapa or "pruebas"
    base_cat = catalogo.get(etapa_ef) if etapa in catalogo else None
    info = {
        "etapa": etapa_ef,
        "disponibilidad": "configurado" if comando is not None else (base_cat or {}).get("disponibilidad", "ausente"),
        "comando": comando if comando is not None else (base_cat or {}).get("comando"),
        "comando_texto": cmd_txt if cmd_txt is not None else (base_cat or {}).get("comando_texto"),
        "origen": (base_cat or {}).get("origen") or "invocación directa",
        "obligatorio": bool((base_cat or {}).get("obligatorio", True)),
        "entradas": (base_cat or {}).get("entradas"),
        "herramienta": (base_cat or {}).get("herramienta"),
        "motivo": (base_cat or {}).get("motivo", ""),
    }
    return etapa_ef, info


def calcular_identidad(root, etapa, info_etapa, entorno_override=None, clave_arbol=None):
    """Calcula la identidad compuesta de una comprobación verificando que sus entradas sean acreditables."""
    base = Path(root).resolve()
    entradas = info_etapa.get("entradas")
    comando_texto = info_etapa.get("comando_texto") or _comando_texto(info_etapa.get("comando")) or ""
    entorno = _calcular_entorno(base, entorno_override=entorno_override)

    if entradas:
        for entrada in entradas:
            ruta_entrada = base / entrada.rstrip("/")
            if not ruta_entrada.exists():
                return {
                    "acreditable": False,
                    "motivo_no_acreditable": f"entrada relevante no acreditable ({entrada})",
                    "identidad": None,
                    "hash_contenido": None,
                    "entorno": entorno,
                    "comando": comando_texto,
                    "entradas": list(entradas),
                }
        todos = _listar_ficheros_repositorio(base)
        seleccionados = [f for f in todos if any(_coincide_entrada(f, e) for e in entradas)]
    else:
        seleccionados = _listar_ficheros_repositorio(base)

    digest = hashlib.sha256()
    for rel in sorted(seleccionados):
        digest.update(rel.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        p = base / rel
        if p.is_file():
            contenido = p.read_bytes().replace(b"\r\n", b"\n")
            digest.update(hashlib.sha256(contenido).digest())
        else:
            digest.update(b"DELETED")
        digest.update(b"\0")
    hash_contenido = digest.hexdigest()
    if not seleccionados and clave_arbol:
        hash_contenido = clave_arbol

    payload = {
        "comando": comando_texto,
        "entradas": list(entradas) if entradas else [],
        "hash_contenido": hash_contenido,
        "entorno": entorno,
    }
    identidad = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "acreditable": True,
        "motivo_no_acreditable": "",
        "identidad": identidad,
        "hash_contenido": hash_contenido,
        "entorno": entorno,
        "comando": comando_texto,
        "entradas": list(entradas) if entradas else [],
    }


def _worktrees_repositorio(root):
    """Enumera los directorios de trabajo asociados al mismo repositorio Git."""
    base = Path(root).resolve()
    worktrees = [base]
    comun = directorio_git_comun(base)
    if comun.is_dir():
        if comun.name == ".git":
            principal = comun.parent.resolve()
            if principal not in worktrees:
                worktrees.append(principal)
        wt_dir = comun / "worktrees"
        if wt_dir.is_dir():
            for gitdir_file in sorted(wt_dir.glob("*/gitdir")):
                try:
                    raw = gitdir_file.read_text(encoding="utf-8", errors="replace").strip()
                    if raw:
                        wt_path = Path(raw).resolve().parent
                        if wt_path.is_dir() and wt_path not in worktrees:
                            worktrees.append(wt_path)
                except OSError:
                    continue
    return worktrees


def _rutas_lectura_evidencias(root):
    """Enumera los archivos de evidencias aplicables al árbol o worktree actual."""
    base = Path(root).resolve()
    rutas = [wt / EVIDENCIAS for wt in _worktrees_repositorio(base)]
    comun = directorio_git_comun(base)
    if comun.is_dir():
        rutas.append(directorio_coordinacion(base, crear=False) / EVIDENCIAS)
    unicas = []
    vistas = set()
    for r in rutas:
        clave = str(r.resolve())
        if clave not in vistas:
            vistas.add(clave)
            unicas.append(r)
    return unicas


def tiene_evidencias(root):
    """Indica si existe algún archivo de evidencias aplicable al árbol o su coordinación común."""
    return any(r.is_file() for r in _rutas_lectura_evidencias(root))


def _sincronizar_lectura(root):
    """Sincroniza y devuelve las líneas JSONL aplicables entre worktrees y el almacén común."""
    base = Path(root).resolve()
    comun = directorio_git_comun(base)
    if not comun.is_dir():
        local = base / EVIDENCIAS
        if not local.is_file():
            return []
        return [l.strip() for l in local.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]

    coord = directorio_coordinacion(base, crear=True)
    ruta_sync = coord / "sincronizacion_evidencias.json"
    ruta_comun = coord / EVIDENCIAS
    try:
        estado_sync = json.loads(ruta_sync.read_text(encoding="utf-8")) if ruta_sync.is_file() else {}
    except (OSError, ValueError):
        estado_sync = {}
    if not isinstance(estado_sync, dict):
        estado_sync = {}
    archivos = estado_sync.get("archivos")
    if not isinstance(archivos, dict):
        archivos = {}
    entradas_comun = estado_sync.get("comun")
    if not isinstance(entradas_comun, list):
        entradas_comun = []

    worktrees = [str(wt) for wt in _worktrees_repositorio(base)]
    for conocido in list(archivos.keys()):
        if conocido not in worktrees:
            worktrees.append(conocido)

    modificado = False
    for wt_str in worktrees:
        wt_path = Path(wt_str)
        f_wt = wt_path / EVIDENCIAS
        prev_lines = archivos.get(wt_str)
        if f_wt.is_file():
            try:
                curr_lines = [
                    l.strip() for l in f_wt.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()
                ]
            except OSError:
                curr_lines = []
        else:
            curr_lines = None

        if curr_lines is None:
            if prev_lines is not None and wt_path.exists():
                entradas_comun = [e for e in entradas_comun if e.get("origen") != wt_str]
                archivos.pop(wt_str, None)
                modificado = True
            continue

        if curr_lines != prev_lines:
            modificado = True
            if prev_lines is not None and (
                len(curr_lines) < len(prev_lines) or curr_lines[: len(prev_lines)] != prev_lines
            ):
                if wt_str == str(base):
                    entradas_comun = [{"origen": wt_str, "linea": l} for l in curr_lines]
                    for otro_wt in list(archivos.keys()):
                        if otro_wt != wt_str:
                            f_otro = Path(otro_wt) / EVIDENCIAS
                            if not f_otro.is_file():
                                archivos.pop(otro_wt, None)
                else:
                    entradas_comun = [e for e in entradas_comun if e.get("origen") != wt_str]
                    entradas_comun.extend({"origen": wt_str, "linea": l} for l in curr_lines)
            else:
                nuevas = curr_lines if prev_lines is None else curr_lines[len(prev_lines) :]
                lineas_existentes = {e.get("linea") for e in entradas_comun}
                for l in nuevas:
                    if prev_lines is None and l in lineas_existentes:
                        continue
                    entradas_comun.append({"origen": wt_str, "linea": l})
            archivos[wt_str] = list(curr_lines)

    if ruta_comun.is_file():
        try:
            lineas_disco_comun = [
                l.strip() for l in ruta_comun.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()
            ]
        except OSError:
            lineas_disco_comun = []
        conocidas = {e.get("linea") for e in entradas_comun}
        for l in lineas_disco_comun:
            if l not in conocidas:
                entradas_comun.append({"origen": str(coord), "linea": l})
                conocidas.add(l)
                modificado = True

    lineas_resultado = [e["linea"] for e in entradas_comun if isinstance(e, dict) and e.get("linea")]
    if modificado:
        try:
            ruta_sync.write_text(
                json.dumps({"archivos": archivos, "comun": entradas_comun}, ensure_ascii=False),
                encoding="utf-8",
            )
            if lineas_resultado:
                ruta_comun.write_text("\n".join(lineas_resultado) + "\n", encoding="utf-8")
            elif ruta_comun.is_file():
                ruta_comun.write_text("", encoding="utf-8")
        except OSError:
            pass
    return lineas_resultado


def leer_evidencias(root):
    """Lee en orden cronológico los registros de evidencias del repositorio y su coordinación común."""
    with _LOCK_GLOBAL:
        lineas_crudas = _sincronizar_lectura(root)
    registros = []
    for linea in lineas_crudas:
        if not linea.strip():
            continue
        try:
            dato = json.loads(linea)
            if isinstance(dato, dict):
                registros.append(dato)
        except ValueError:
            continue
    return registros


def _escribir_evidencia(root, fila, repo_evidencia=None):
    """Persiste un registro de ejecución real en el archivo de evidencias del árbol y en el almacén común."""
    base = Path(root).resolve()
    _excluir_propios(base)
    linea = json.dumps(fila, ensure_ascii=False)
    texto = linea + "\n"
    with _LOCK_GLOBAL:
        comun = directorio_git_comun(base)
        if not comun.is_dir():
            with (base / EVIDENCIAS).open("a", encoding="utf-8") as f:
                f.write(texto)
            return

        _sincronizar_lectura(base)
        coord = directorio_coordinacion(base, crear=True)
        ruta_sync = coord / "sincronizacion_evidencias.json"
        ruta_comun = coord / EVIDENCIAS
        try:
            estado_sync = json.loads(ruta_sync.read_text(encoding="utf-8")) if ruta_sync.is_file() else {}
        except (OSError, ValueError):
            estado_sync = {}
        archivos = estado_sync.get("archivos") if isinstance(estado_sync.get("archivos"), dict) else {}
        entradas_comun = estado_sync.get("comun") if isinstance(estado_sync.get("comun"), list) else []

        destinos_locales = [base]
        if repo_evidencia is not None:
            base_repo = Path(repo_evidencia).resolve()
            if base_repo not in destinos_locales:
                destinos_locales.append(base_repo)

        for dest in destinos_locales:
            if not dest.exists():
                continue
            f_dest = dest / EVIDENCIAS
            with f_dest.open("a", encoding="utf-8") as f:
                f.write(texto)
            try:
                archivos[str(dest)] = [
                    l.strip() for l in f_dest.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()
                ]
            except OSError:
                pass

        origen_registro = str(Path(repo_evidencia).resolve()) if repo_evidencia is not None else str(base)
        entradas_comun.append({"origen": origen_registro, "linea": linea})
        try:
            with ruta_comun.open("a", encoding="utf-8") as fc:
                fc.write(texto)
            ruta_sync.write_text(
                json.dumps({"archivos": archivos, "comun": entradas_comun}, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass


def _leer_estado_en_curso_disco(root):
    """Lee el archivo de estado de ejecución en curso desde el directorio Git común."""
    comun = directorio_git_comun(root)
    if not comun.is_dir():
        return {}
    ruta = directorio_coordinacion(root, crear=False) / ESTADO_EN_CURSO
    if not ruta.is_file():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar_estado_en_curso_disco(root, datos):
    """Actualiza de forma atómica el estado en curso compartido en el directorio Git común."""
    comun = directorio_git_comun(root)
    if not comun.is_dir():
        return
    coord = directorio_coordinacion(root, crear=True)
    destino = coord / ESTADO_EN_CURSO
    with tempfile.NamedTemporaryFile("w", dir=coord, delete=False, encoding="utf-8") as tmp:
        json.dump(datos, tmp, ensure_ascii=False)
        ruta_tmp = Path(tmp.name)
    try:
        os.replace(ruta_tmp, destino)
    except OSError:
        ruta_tmp.unlink(missing_ok=True)


def registrar_ejecucion_interrumpida_prueba(root, etapa, comando, pid, salida_parcial=""):
    """Registra un estado en curso con el PID dado para verificar la recuperación ante cortes abruptos."""
    with _LOCK_GLOBAL:
        actual = _leer_estado_en_curso_disco(root)
        actual[etapa] = {
            "etapa": etapa,
            "comando": comando,
            "pid": int(pid),
            "fase": "ejecutando",
            "salida_parcial": salida_parcial,
            "identidad": "identidad-interrumpida",
            "fecha": _ahora(),
        }
        _guardar_estado_en_curso_disco(root, actual)


def _inspeccionar_en_curso(root):
    """Inspecciona ejecuciones activas y convierte procesos muertos en estado interrumpido."""
    with _LOCK_GLOBAL:
        datos = _leer_estado_en_curso_disco(root)
        modificado = False
        for etapa, info in list(datos.items()):
            if info.get("fase") == "ejecutando":
                pid = info.get("pid")
                if not _proceso_vivo(pid):
                    info["fase"] = "interrumpido"
                    modificado = True
        if modificado:
            _guardar_estado_en_curso_disco(root, datos)
        return datos


def _resumir_historial_etapa(registros, etapa, comando_texto):
    """Pliega los registros de una etapa o comando determinando su último resultado real e intermitencias."""
    if comando_texto:
        aplicables = [
            r
            for r in registros
            if r.get("comando") == comando_texto or (not r.get("comando") and etapa and r.get("etapa") == etapa)
        ]
    else:
        aplicables = [r for r in registros if etapa and r.get("etapa") == etapa]
    if not aplicables:
        return None
    ultimo = aplicables[-1]
    id_ultimo = ultimo.get("identidad") or ultimo.get("arbol")
    misma_id = [r for r in aplicables if (r.get("identidad") or r.get("arbol")) == id_ultimo]
    transiciones = [
        "aprobado"
        if (r.get("codigo") == 0 and not r.get("cambio_en_vuelo") and r.get("acreditado", True) is not False)
        else "fallido"
        for r in misma_id
    ]
    intermitente = len(set(transiciones)) > 1
    resultado = transiciones[-1]
    diagnostico = (
        f"Advertencia de intermitencia: la comprobación alternó resultados ({', '.join(transiciones)}) sobre la misma identidad."
        if intermitente
        else ""
    )
    return {
        "ultimo": ultimo,
        "resultado": resultado,
        "intermitente": intermitente,
        "transiciones": transiciones,
        "diagnostico": diagnostico,
    }


def _es_evidencia_reutilizable(base, ultimo, info, info_id, clave_arbol=None, en_git=None, cambios=None):
    """Determina si el último registro es verde y aplicable para el comando, entradas y entorno actuales."""
    if ultimo is None or not info_id.get("acreditable"):
        return False
    if ultimo.get("codigo") != 0 or ultimo.get("cambio_en_vuelo") or ultimo.get("acreditado") is False:
        return False
    if cambios and any(
        not info_id.get("entradas") or any(_coincide_entrada(c, e) for e in info_id["entradas"]) for c in cambios
    ):
        return False

    es_git = (Path(base) / ".git").exists() if en_git is None else bool(en_git)
    tiene_clave_entorno = "entorno" in ultimo
    entorno_prev = ultimo.get("entorno")
    if es_git or tiene_clave_entorno:
        if not isinstance(entorno_prev, dict) or not entorno_prev:
            return False
        if entorno_prev != info_id.get("entorno"):
            return False

    if ultimo.get("identidad") and info_id.get("identidad") and ultimo.get("identidad") == info_id.get("identidad"):
        if ultimo.get("hash_contenido") and ultimo.get("hash_contenido") not in (
            info_id.get("hash_contenido"),
            clave_arbol,
        ):
            return False
        return True

    if ultimo.get("hash_contenido"):
        if ultimo.get("hash_contenido") != info_id.get("hash_contenido"):
            return False
        if not info.get("entradas") and clave_arbol and ultimo.get("arbol") and ultimo.get("arbol") != clave_arbol:
            return False
        return True

    if clave_arbol and ultimo.get("arbol") == clave_arbol:
        return True
    return False


def _explicar_diferencia_identidad(ultimo, info_id, cambios=None, clave_arbol=None, en_git=True):
    """Explica con precisión por qué una evidencia previa no es reutilizable frente a la identidad actual."""
    if not info_id["acreditable"]:
        return info_id["motivo_no_acreditable"]
    if cambios:
        entradas = info_id.get("entradas") or []
        afectados = [c for c in cambios if not entradas or any(_coincide_entrada(c, e) for e in entradas)]
        if afectados:
            return f"cambio en contenido relevante ({', '.join(afectados)}): cambio de entradas (entradas modificadas)"
    if ultimo is None:
        return "sin evidencia previa acreditada"
    if ultimo.get("cambio_en_vuelo"):
        return "ejecución previa invalidada por cambio en vuelo (entradas modificadas durante la ejecución)"
    if ultimo.get("codigo") != 0 or ultimo.get("acreditado") is False:
        return "último resultado real fallido: el último resultado falló"

    entorno_prev = ultimo.get("entorno")
    entorno_act = info_id.get("entorno") or {}
    entorno_ausente = entorno_prev in (None, {}, "", "ausente")

    if not entorno_ausente:
        if not isinstance(entorno_prev, dict):
            return "cambio en entorno: el entorno del éxito histórico es distinto del entorno actual"
        if entorno_prev.get("herramienta") != entorno_act.get("herramienta"):
            return "cambio en entorno (herramienta): el entorno del éxito histórico es distinto del entorno actual"
        if entorno_prev.get("configuracion") != entorno_act.get("configuracion"):
            return "cambio en entorno (configuración): el entorno del éxito histórico es distinto del entorno actual"
        if entorno_prev.get("dependencias") != entorno_act.get("dependencias"):
            return "cambio en entorno (dependencias): el entorno del éxito histórico es distinto del entorno actual"
        if entorno_prev.get("plataforma") != entorno_act.get("plataforma"):
            return "cambio en entorno (plataforma): el entorno del éxito histórico es distinto del entorno actual"
        if entorno_prev != entorno_act:
            return "cambio en entorno: el entorno del éxito histórico es distinto del entorno actual"

    if ultimo.get("hash_contenido") and ultimo.get("hash_contenido") != info_id.get("hash_contenido"):
        return "cambio en contenido relevante: cambio de entradas (entradas modificadas)"
    if clave_arbol and ultimo.get("arbol") and ultimo.get("arbol") != clave_arbol:
        return "cambio en contenido relevante: cambio de entradas (entradas modificadas)"

    if entorno_ausente and (en_git or "entorno" in ultimo):
        return "evidencia histórica sin identidad compuesta acreditada: el entorno del éxito histórico está ausente (entorno desconocido)"
    if ultimo.get("contrato") != "v2" and "identidad" not in ultimo:
        return "evidencia histórica sin identidad compuesta acreditada: el entorno del éxito histórico está ausente (entorno desconocido)"
    return "cambio en contenido relevante: cambio de entradas (entradas modificadas)"


def _buscar_activo_en_curso(en_curso, etapa, comando_texto):
    """Busca una ejecución activa para la etapa o comando dado."""
    if etapa in en_curso and en_curso[etapa].get("fase") == "ejecutando":
        return en_curso[etapa]
    for item in en_curso.values():
        if item.get("fase") == "ejecutando" and comando_texto and item.get("comando") == comando_texto:
            return item
    return en_curso.get(etapa)


def planificar(root, etapas=None, puerta=None, entorno_override=None, cambios=None):
    """Construye el plan explicable de comprobaciones antes de ejecutar."""
    base = Path(root).resolve()
    cfg = cargar_configuracion(base)
    catalogo = resolver_catalogo(base, cfg=cfg)
    registros = leer_evidencias(base)
    en_curso = _inspeccionar_en_curso(base)
    en_git = (base / ".git").exists()
    try:
        clave_arbol = arbol_trabajo(base) if en_git else None
    except Exception:
        clave_arbol = None

    puertas_cfg = (cfg.get("release") or {}).get("puertas")
    if etapas is not None:
        seleccion = list(etapas)
    elif puerta == "release" and puertas_cfg:
        seleccion = list(ETAPAS_CATALOGO)
    else:
        seleccion = list(ETAPAS_CATALOGO)

    plan_etapas = {}
    lineas_texto = []

    for etapa in seleccion:
        info = catalogo.get(etapa) or {
            "etapa": etapa,
            "disponibilidad": "ausente",
            "comando": None,
            "comando_texto": None,
            "origen": None,
            "obligatorio": False,
            "entradas": None,
            "herramienta": None,
            "motivo": "análisis opcional no configurado",
        }
        disp = info["disponibilidad"]
        if disp != "configurado":
            plan_etapas[etapa] = {
                "etapa": etapa,
                "disponibilidad": disp,
                "resultado": "sin_acreditar",
                "comando": info["comando"],
                "origen": info["origen"],
                "obligatorio": info["obligatorio"],
                "accion": "omitir",
                "motivo": info["motivo"],
                "identidad": None,
            }
            lineas_texto.append(f"- {etapa}: [{disp}/sin_acreditar] acción=omitir ({info['motivo']})")
            continue

        info_id = calcular_identidad(base, etapa, info, entorno_override=entorno_override, clave_arbol=clave_arbol)
        resumen_hist = _resumir_historial_etapa(registros, etapa, info["comando_texto"])
        ultimo = resumen_hist["ultimo"] if resumen_hist else None

        activo = _buscar_activo_en_curso(en_curso, etapa, info["comando_texto"])
        motivo_espera = None
        siguiente_accion = None
        if activo and activo.get("fase") == "ejecutando":
            if activo.get("identidad") == info_id["identidad"] and info_id["acreditable"]:
                accion = "esperar"
                resultado_est = "ejecutando"
                motivo = "espera el resultado de la comprobación equivalente en curso; se compartirá su resultado"
                motivo_espera = "compartiendo ejecución en curso con la misma identidad (espera el resultado de la comprobación equivalente en curso)"
                siguiente_accion = "esperar resultado de la ejecución compartida"
            else:
                accion = "ejecutar"
                resultado_est = "pendiente"
                motivo = "ejecución en curso con identidad distinta"
                motivo_espera = "en espera de que finalice la ejecución en curso con identidad distinta"
                siguiente_accion = "ejecutar con identidad propia tras finalizar la ejecución activa"
        elif _es_evidencia_reutilizable(
            base,
            ultimo,
            info,
            info_id,
            clave_arbol=clave_arbol,
            en_git=en_git,
            cambios=cambios,
        ):
            accion = "reutilizar"
            resultado_est = "aprobado"
            motivo = (
                f"evidencia aprobada vigente para la misma identidad ({info_id['identidad'][:10]}): "
                "el último resultado real fue verde para el mismo comando, entradas y entorno"
            )
            siguiente_accion = "reutilizar evidencia acreditada"
        else:
            accion = "ejecutar"
            misma_id_fallida = (
                ultimo is not None
                and (
                    ultimo.get("identidad") == info_id["identidad"]
                    or (ultimo.get("comando") == info["comando_texto"] and ultimo.get("codigo") != 0)
                )
                and ultimo.get("codigo") != 0
            )
            resultado_est = "fallido" if misma_id_fallida else "pendiente"
            motivo = _explicar_diferencia_identidad(
                ultimo,
                info_id,
                cambios=cambios,
                clave_arbol=clave_arbol,
                en_git=en_git,
            )
            siguiente_accion = "ejecutar comprobación"

        plan_etapas[etapa] = {
            "etapa": etapa,
            "disponibilidad": disp,
            "resultado": resultado_est,
            "comando": info["comando"],
            "comando_texto": info["comando_texto"],
            "origen": info["origen"],
            "obligatorio": info["obligatorio"],
            "entradas": info["entradas"],
            "accion": accion,
            "motivo": motivo,
            "motivo_espera": motivo_espera,
            "siguiente_accion": siguiente_accion,
            "identidad": info_id["identidad"],
            "info_identidad": info_id,
        }
        lineas_texto.append(
            f"- {etapa}: [{disp}/{resultado_est}] comando={info['comando_texto']} "
            f"origen={info['origen']} acción={accion} ({motivo})"
        )

    return {
        "etapas": plan_etapas,
        "texto": "\n".join(lineas_texto),
    }


def _invocar_ejecutor(ejecutor, root, comando, etapa, stream_callback):
    """Invoca un ejecutor personalizado o subprocess.run capturando salida parcial y código de retorno."""
    if ejecutor is not None:
        sig = inspect.signature(ejecutor)
        kwargs = {}
        acepta_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        if "etapa" in sig.parameters or acepta_var_kw:
            kwargs["etapa"] = etapa
        if "stream_callback" in sig.parameters or acepta_var_kw:
            kwargs["stream_callback"] = stream_callback
        if "root" in sig.parameters or acepta_var_kw:
            kwargs["root"] = root
        res = ejecutor(comando, **kwargs)
        if isinstance(res, tuple) and len(res) == 2:
            return int(res[0]), str(res[1] or "")
        return int(res), ""

    cmd_ejec = comando if isinstance(comando, str) else _comando_texto(comando)
    with tempfile.TemporaryFile() as captura:
        proc = subprocess.run(
            cmd_ejec,
            shell=True,
            cwd=root,
            stdout=captura,
            stderr=subprocess.STDOUT,
        )
        captura.seek(0, os.SEEK_END)
        captura.seek(max(0, captura.tell() - 32768))
        salida = captura.read().decode("utf-8", errors="replace")
    if stream_callback and salida:
        stream_callback(salida)
    return proc.returncode, salida


def ejecutar_comprobacion(
    root,
    etapa=None,
    comando=None,
    ejecutor=None,
    entorno_override=None,
    canal="cli",
    forzar_ejecucion=False,
    clave_arbol=None,
    arbol_fn=None,
    repo_evidencia=None,
    imprimir_salida=False,
):
    """Ejecuta o reutiliza una comprobación coordinando concurrencia entre entradas y worktrees."""
    base = Path(root).resolve()
    if etapa in ETAPAS_CATALOGO or comando is None:
        cfg = cargar_configuracion(base)
        catalogo = resolver_catalogo(base, cfg=cfg)
    else:
        try:
            cfg = cargar_configuracion(base)
            catalogo = resolver_catalogo(base, cfg=cfg)
        except Exception:
            cfg = {}
            catalogo = {}

    etapa_ef, info = _info_para_comando(base, etapa=etapa, comando=comando, cfg=cfg, catalogo=catalogo)
    etapa_registro = etapa or etapa_ef

    if info["disponibilidad"] != "configurado" or not info["comando"]:
        return {
            "etapa": etapa_registro,
            "codigo": 1 if info.get("obligatorio") else 0,
            "estado": "sin_acreditar",
            "disponibilidad": info["disponibilidad"],
            "reutilizada": False,
            "acreditado": False,
            "motivo": info.get("motivo", "no configurado"),
        }

    en_git = (base / ".git").exists()
    if clave_arbol is not None:
        arbol_inicial = clave_arbol
    elif arbol_fn is not None:
        try:
            arbol_inicial = arbol_fn(base)
        except Exception:
            arbol_inicial = None
    elif en_git and ejecutor is None:
        try:
            arbol_inicial = arbol_trabajo(base)
        except Exception:
            arbol_inicial = None
    else:
        arbol_inicial = None

    info_id_inicial = calcular_identidad(
        base,
        etapa_ef,
        info,
        entorno_override=entorno_override,
        clave_arbol=arbol_inicial,
    )
    identidad_inicial = info_id_inicial["identidad"]
    coord_dir_str = str(directorio_coordinacion(base, crear=False).resolve() if en_git else base.resolve())
    coord_key = (coord_dir_str, info["comando_texto"])

    esperar_existente = None
    with _LOCK_GLOBAL:
        en_memoria = _EJECUCIONES_MEMORIA.get(coord_key)
        if en_memoria is None:
            for (c_dir, _), cand in _EJECUCIONES_MEMORIA.items():
                if c_dir == coord_dir_str and not cand["evento"].is_set():
                    if cand.get("identidad") == identidad_inicial and cand.get("comando") == info["comando_texto"]:
                        en_memoria = cand
                        break
        if en_memoria is not None and not en_memoria["evento"].is_set():
            if not forzar_ejecucion and identidad_inicial and en_memoria["identidad"] == identidad_inicial:
                esperar_existente = en_memoria
                en_memoria["esperando"] = True
                if "evento_esperando" in en_memoria:
                    en_memoria["evento_esperando"].set()
                est_disco = _leer_estado_en_curso_disco(base)
                clave_est = en_memoria.get("etapa_disco") or etapa_registro
                if clave_est in est_disco:
                    est_disco[clave_est]["motivo_espera"] = (
                        "espera el resultado de la comprobación equivalente en curso"
                    )
                    _guardar_estado_en_curso_disco(base, est_disco)

    if esperar_existente is not None:
        prefijo_log = "preflight" if canal == "release" else "orquestar"
        msg_espera = (
            f"[{prefijo_log}] espera el resultado de la comprobación equivalente en curso: {info['comando_texto']}"
        )
        print(msg_espera, flush=True)
        esperar_existente["evento"].wait(timeout=30)
        res_compartido = dict(esperar_existente.get("resultado") or {})
        es_exito = (res_compartido.get("codigo") == 0) and bool(res_compartido.get("acreditado", True))
        palabra = "éxito" if es_exito else "fallo"
        detalle_fin = (res_compartido.get("salida") or res_compartido.get("diagnostico") or "").strip()
        msg_fin = f"[{prefijo_log}] {palabra} al compartir la comprobación equivalente ({info['comando_texto']})" + (
            f": {detalle_fin}" if detalle_fin else ""
        )
        print(msg_fin, flush=True)
        res_compartido["reutilizada"] = True
        res_compartido["compartida_en_vuelo"] = True
        res_compartido["espero_en_curso"] = True
        res_compartido["motivo_espera"] = msg_espera
        res_compartido["resultado_compartido"] = palabra
        res_compartido["diagnostico"] = msg_fin
        res_compartido["motivo"] = msg_fin
        return res_compartido

    registros = leer_evidencias(base)
    resumen_hist = _resumir_historial_etapa(registros, etapa_ef, info["comando_texto"])
    ultimo = resumen_hist["ultimo"] if resumen_hist else None

    if not forzar_ejecucion and _es_evidencia_reutilizable(
        base,
        ultimo,
        info,
        info_id_inicial,
        clave_arbol=arbol_inicial,
        en_git=en_git,
    ):
        arbol_ref = arbol_inicial or ultimo.get("arbol") or info_id_inicial["identidad"] or ""
        motivo_reuso = (
            f"evidencia aprobada vigente para la misma identidad ({(info_id_inicial['identidad'] or arbol_ref)[:10]}): "
            "el último resultado real fue verde para el mismo comando, entradas y entorno"
        )
        if canal == "release":
            print(
                f"[preflight] verificación reutilizada: {info['comando_texto']} ({motivo_reuso}).",
                flush=True,
            )
        else:
            print(
                f"[orquestar] verificación reutilizada: {info['comando_texto']} ya pasó sobre este mismo árbol "
                f"({arbol_ref[:10]}); el último resultado real fue verde para el mismo comando, entradas y entorno.",
                flush=True,
            )
        return {
            "etapa": etapa_registro,
            "comando": info["comando_texto"],
            "codigo": 0,
            "estado": "aprobado",
            "disponibilidad": "configurado",
            "reutilizada": True,
            "acreditado": True,
            "cambio_en_vuelo": False,
            "identidad": identidad_inicial,
            "identidad_inicial": identidad_inicial,
            "identidad_final": identidad_inicial,
            "arbol": arbol_ref,
            "salida": ultimo.get("salida", ""),
            "motivo": motivo_reuso,
            "diagnostico": motivo_reuso,
            "canal": canal,
            "fecha": _ahora(),
        }

    motivo_ejecucion = _explicar_diferencia_identidad(
        ultimo,
        info_id_inicial,
        clave_arbol=arbol_inicial,
        en_git=en_git,
    )

    with _LOCK_GLOBAL:
        en_memoria = _EJECUCIONES_MEMORIA.get(coord_key)
        if en_memoria is not None and not en_memoria["evento"].is_set():
            if not forzar_ejecucion and identidad_inicial and en_memoria["identidad"] == identidad_inicial:
                esperar_existente = en_memoria
                en_memoria["esperando"] = True
                if "evento_esperando" in en_memoria:
                    en_memoria["evento_esperando"].set()
        if esperar_existente is None:
            actual_evento = threading.Event()
            registro_mem = {
                "identidad": identidad_inicial,
                "comando": info["comando_texto"],
                "etapa_disco": etapa_registro,
                "evento": actual_evento,
                "evento_esperando": threading.Event(),
                "esperando": False,
                "salida_parcial": "",
                "resultado": None,
            }
            _EJECUCIONES_MEMORIA[coord_key] = registro_mem
            estado_disco = _leer_estado_en_curso_disco(base)
            estado_disco[etapa_registro] = {
                "etapa": etapa_registro,
                "comando": info["comando_texto"],
                "pid": os.getpid(),
                "fase": "ejecutando",
                "salida_parcial": "",
                "identidad": identidad_inicial,
                "canal": canal,
                "fecha": _ahora(),
            }
            _guardar_estado_en_curso_disco(base, estado_disco)

    if esperar_existente is not None:
        prefijo_log = "preflight" if canal == "release" else "orquestar"
        msg_espera = (
            f"[{prefijo_log}] espera el resultado de la comprobación equivalente en curso: {info['comando_texto']}"
        )
        print(msg_espera, flush=True)
        esperar_existente["evento"].wait(timeout=30)
        res_compartido = dict(esperar_existente.get("resultado") or {})
        es_exito = (res_compartido.get("codigo") == 0) and bool(res_compartido.get("acreditado", True))
        palabra = "éxito" if es_exito else "fallo"
        detalle_fin = (res_compartido.get("salida") or res_compartido.get("diagnostico") or "").strip()
        msg_fin = f"[{prefijo_log}] {palabra} al compartir la comprobación equivalente ({info['comando_texto']})" + (
            f": {detalle_fin}" if detalle_fin else ""
        )
        print(msg_fin, flush=True)
        res_compartido["reutilizada"] = True
        res_compartido["compartida_en_vuelo"] = True
        res_compartido["espero_en_curso"] = True
        res_compartido["motivo_espera"] = msg_espera
        res_compartido["resultado_compartido"] = palabra
        res_compartido["diagnostico"] = msg_fin
        res_compartido["motivo"] = msg_fin
        return res_compartido

    if ultimo is not None:
        prefijo_log = "preflight" if canal == "release" else "orquestar"
        print(
            f"[{prefijo_log}] ejecutando {info['comando_texto']}: {motivo_ejecucion}",
            flush=True,
        )

    def _actualizar_stream(fragmento):
        with _LOCK_GLOBAL:
            registro_mem["salida_parcial"] += str(fragmento)
            est = _leer_estado_en_curso_disco(base)
            if etapa_registro in est:
                est[etapa_registro]["salida_parcial"] = registro_mem["salida_parcial"]
                _guardar_estado_en_curso_disco(base, est)

    inicio = time.monotonic()
    try:
        codigo, salida = _invocar_ejecutor(ejecutor, base, info["comando"], etapa_registro, _actualizar_stream)
    finally:
        with _LOCK_GLOBAL:
            est = _leer_estado_en_curso_disco(base)
            est.pop(etapa_registro, None)
            _guardar_estado_en_curso_disco(base, est)

    if imprimir_salida and salida:
        print(salida, end="" if salida.endswith("\n") else "\n", flush=True)

    duracion_s = round(time.monotonic() - inicio)
    info_id_final = calcular_identidad(
        base,
        etapa_ef,
        info,
        entorno_override=entorno_override,
        clave_arbol=arbol_inicial,
    )
    identidad_final = info_id_final["identidad"]
    cambio_en_vuelo = (
        not info_id_inicial["acreditable"] or not info_id_final["acreditable"] or identidad_inicial != identidad_final
    )
    acreditado = (codigo == 0) and not cambio_en_vuelo
    estado_final = "aprobado" if acreditado else ("sin_acreditar" if cambio_en_vuelo and codigo == 0 else "fallido")

    if not cambio_en_vuelo and arbol_inicial:
        arbol_actual = arbol_inicial
    elif arbol_fn is not None:
        try:
            arbol_actual = arbol_fn(base)
        except Exception:
            arbol_actual = info_id_final.get("hash_contenido") or arbol_inicial or ""
    elif ejecutor is None and en_git:
        try:
            arbol_actual = arbol_trabajo(base)
        except Exception:
            arbol_actual = info_id_final.get("hash_contenido") or arbol_inicial or ""
    else:
        arbol_actual = arbol_inicial or info_id_final.get("hash_contenido") or ""

    diagnostico_final = (
        motivo_ejecucion
        if codigo == 0 and not cambio_en_vuelo
        else (
            "cambio en vuelo detectado durante la ejecución"
            if cambio_en_vuelo
            else (salida.strip() or motivo_ejecucion or f"fallo con código {codigo}")
        )
    )
    fecha_actual = _ahora()
    fila_evidencia = {
        "contrato": "v2",
        "fecha": fecha_actual,
        "etapa": etapa_registro,
        "comando": info["comando_texto"],
        "arbol": arbol_actual,
        "arbol_inicial": arbol_inicial or arbol_actual,
        "identidad": identidad_inicial,
        "identidad_inicial": identidad_inicial,
        "identidad_final": identidad_final,
        "hash_contenido": info_id_inicial.get("hash_contenido"),
        "entorno": info_id_inicial.get("entorno"),
        "codigo": codigo,
        "codigo_proceso": codigo,
        "acreditado": acreditado,
        "cambio_en_vuelo": cambio_en_vuelo,
        "motivo": motivo_ejecucion,
        "motivo_no_reutilizacion": motivo_ejecucion if ultimo is not None else "",
        "diagnostico": diagnostico_final,
        "canal": canal,
        "salida": salida[-32768:] if salida else "",
        "duracion_s": duracion_s,
    }
    _escribir_evidencia(base, fila_evidencia, repo_evidencia=repo_evidencia)

    resultado_obj = {
        "etapa": etapa_registro,
        "fecha": fecha_actual,
        "comando": info["comando_texto"],
        "arbol": arbol_actual,
        "codigo": codigo,
        "estado": estado_final,
        "disponibilidad": "configurado",
        "reutilizada": False,
        "acreditado": acreditado,
        "cambio_en_vuelo": cambio_en_vuelo,
        "identidad": identidad_inicial if not cambio_en_vuelo else None,
        "identidad_inicial": identidad_inicial,
        "identidad_final": identidad_final,
        "motivo": motivo_ejecucion,
        "motivo_no_reutilizacion": motivo_ejecucion if ultimo is not None else "",
        "diagnostico": diagnostico_final,
        "salida": salida,
        "duracion_s": duracion_s,
        "canal": canal,
    }

    with _LOCK_GLOBAL:
        registro_mem["resultado"] = resultado_obj
        registro_mem["evento"].set()
        _EJECUCIONES_MEMORIA.pop(coord_key, None)

    return resultado_obj


def verificar_comando(
    root,
    comando,
    clave_arbol=None,
    arbol_fn=None,
    entorno_override=None,
    ejecutor=None,
    forzar_ejecucion=False,
):
    """Punto de entrada unificado para `adevv orquestar --verificar`."""
    return ejecutar_comprobacion(
        root,
        etapa=None,
        comando=comando,
        ejecutor=ejecutor,
        entorno_override=entorno_override,
        canal="cli",
        forzar_ejecucion=forzar_ejecucion,
        clave_arbol=clave_arbol,
        arbol_fn=arbol_fn,
        imprimir_salida=(ejecutor is None),
    )


def evaluar_puerta(
    root,
    puerta="release",
    ejecutar=False,
    ejecutor=None,
    entorno_override=None,
    canal="cli",
    forzar_ejecucion=False,
):
    """Evalúa una puerta de calidad o release separando disponibilidad y resultado."""
    base = Path(root).resolve()
    cfg = cargar_configuracion(base)
    plan = planificar(base, puerta=puerta, entorno_override=entorno_override)
    etapas_plan = plan["etapas"]

    puertas_requeridas = (cfg.get("release") or {}).get("puertas")
    if not puertas_requeridas:
        puertas_requeridas = [
            etapa
            for etapa, datos in etapas_plan.items()
            if datos.get("obligatorio") or datos.get("disponibilidad") == "configurado"
        ]

    resultados_etapas = {}
    fallos = []

    for etapa in ETAPAS_CATALOGO:
        datos = etapas_plan[etapa]
        es_requerida = etapa in puertas_requeridas or datos.get("obligatorio", False)
        if datos["disponibilidad"] != "configurado":
            resultados_etapas[etapa] = dict(datos)
            if es_requerida and datos["disponibilidad"] == "ausente":
                fallos.append(f"{etapa} ({datos['motivo']})")
            continue

        if ejecutar:
            res = ejecutar_comprobacion(
                base,
                etapa,
                ejecutor=ejecutor,
                entorno_override=entorno_override,
                canal=canal,
                forzar_ejecucion=forzar_ejecucion,
            )
            resultados_etapas[etapa] = {
                **datos,
                "resultado": res["estado"],
                "codigo": res["codigo"],
                "salida": res.get("salida", ""),
                "reutilizada": res.get("reutilizada", False),
                "motivo": res.get("motivo", datos.get("motivo", "")),
                "diagnostico": res.get("diagnostico", ""),
            }
            if res["estado"] != "aprobado" and es_requerida:
                fallos.append(f"{etapa} (fallido)")
        else:
            resultados_etapas[etapa] = dict(datos)
            if es_requerida and datos["resultado"] != "aprobado":
                fallos.append(f"{etapa} ({datos['resultado']})")

    estado_global = "fallido" if fallos else "aprobado"
    return {
        "puerta": puerta,
        "estado": estado_global,
        "motivo": "; ".join(fallos) if fallos else "todas las puertas requeridas acreditadas",
        "plan": plan,
        "etapas": resultados_etapas,
    }


def consultar_estado(root):
    """Consulta sin efectos laterales la fase activa, salida parcial, progreso y evidencias."""
    base = Path(root).resolve()
    en_curso = _inspeccionar_en_curso(base)
    registros = leer_evidencias(base)

    evidencias_mapa = {}
    claves_etapa = {r.get("etapa") for r in registros if r.get("etapa")}
    claves_cmd = {r.get("comando") for r in registros if r.get("comando")}

    for etapa in claves_etapa:
        resumen = _resumir_historial_etapa(registros, etapa, None)
        if resumen:
            evidencias_mapa[etapa] = {
                "resultado": resumen["resultado"],
                "intermitente": resumen["intermitente"],
                "transiciones": resumen["transiciones"],
                "diagnostico": resumen["diagnostico"],
                "ultimo": resumen["ultimo"],
            }
    for cmd in claves_cmd:
        resumen = _resumir_historial_etapa(registros, None, cmd)
        if resumen:
            evidencias_mapa[cmd] = {
                "resultado": resumen["resultado"],
                "intermitente": resumen["intermitente"],
                "transiciones": resumen["transiciones"],
                "diagnostico": resumen["diagnostico"],
                "ultimo": resumen["ultimo"],
            }

    ejecutando = [info for info in en_curso.values() if info.get("fase") == "ejecutando"]
    interrumpidos = [info for info in en_curso.values() if info.get("fase") == "interrumpido"]

    for info_int in interrumpidos:
        et = info_int.get("etapa")
        if et:
            evidencias_mapa[et] = {
                "resultado": "interrumpido",
                "intermitente": False,
                "transiciones": ["interrumpido"],
                "diagnostico": "Proceso en curso terminado abruptamente sin acreditar resultado.",
                "salida_parcial": info_int.get("salida_parcial", ""),
            }

    if ejecutando:
        actual = ejecutando[0]
        return {
            "fase": "ejecutando",
            "comando_activo": actual.get("comando"),
            "etapa_activa": actual.get("etapa"),
            "salida_parcial": actual.get("salida_parcial", ""),
            "progreso": None,
            "motivo_espera": actual.get("motivo_espera"),
            "siguiente_accion": "esperar finalización de la comprobación en curso",
            "evidencias": evidencias_mapa,
        }

    if interrumpidos:
        actual = interrumpidos[0]
        return {
            "fase": "interrumpido",
            "comando_activo": actual.get("comando"),
            "etapa_activa": actual.get("etapa"),
            "salida_parcial": actual.get("salida_parcial", ""),
            "progreso": None,
            "motivo_espera": "proceso previo interrumpido abruptamente",
            "siguiente_accion": "reejecutar comprobación interrumpida para acreditar el árbol actual",
            "evidencias": evidencias_mapa,
        }

    return {
        "fase": "inactivo",
        "comando_activo": None,
        "etapa_activa": None,
        "salida_parcial": "",
        "progreso": None,
        "motivo_espera": None,
        "siguiente_accion": "ninguna",
        "evidencias": evidencias_mapa,
    }


def diagnosticar_fallo(root, etapa, resultado_etapa, intentos_agotados=False, motivo_humano=None):
    """Diagnostica un fallo de comprobación proponiendo reparación acotada o intervención humana."""
    salida = (resultado_etapa or {}).get("salida") or (resultado_etapa or {}).get("motivo") or ""
    if intentos_agotados or motivo_humano:
        return {
            "etapa": etapa,
            "estado": "fallido",
            "causa": salida.strip(),
            "siguiente_accion": "intervencion_humana",
            "motivo_intervencion_humana": motivo_humano or salida.strip() or "Se requiere intervención humana.",
        }
    return {
        "etapa": etapa,
        "estado": "fallido",
        "causa": salida.strip(),
        "siguiente_accion": "reparar",
        "motivo_intervencion_humana": None,
    }


def planificar_reparacion(root, cambios=None, puerta="release", entorno_override=None):
    """Planifica la revalidación tras reparar un fallo conservando en caché las etapas no afectadas."""
    return planificar(root, puerta=puerta, entorno_override=entorno_override, cambios=cambios)


def comandos_verificados_arbol(root, clave_arbol=None, entorno_override=None):
    """Devuelve la lista de comandos cuyo último resultado real aplicable al árbol y entorno actuales está aprobado."""
    base = Path(root).resolve()
    registros = leer_evidencias(base)
    if not registros:
        return []
    en_git = (base / ".git").exists()
    if clave_arbol is not None:
        clave = clave_arbol
    elif en_git:
        try:
            clave = arbol_trabajo(base)
        except Exception:
            clave = None
    else:
        clave = None

    try:
        cfg = cargar_configuracion(base)
        catalogo = resolver_catalogo(base, cfg=cfg)
    except Exception:
        cfg = {}
        catalogo = {}

    ultimo_por_cmd = {}
    orden_cmds = []
    for fila in registros:
        cmd = fila.get("comando")
        if not cmd:
            continue
        if cmd not in orden_cmds:
            orden_cmds.append(cmd)
        ultimo_por_cmd[cmd] = fila

    acreditados = []
    for cmd in orden_cmds:
        ultimo = ultimo_por_cmd[cmd]
        etapa, info = _info_para_comando(base, comando=cmd, cfg=cfg, catalogo=catalogo)
        info_id = calcular_identidad(base, etapa, info, entorno_override=entorno_override, clave_arbol=clave)
        if _es_evidencia_reutilizable(base, ultimo, info, info_id, clave_arbol=clave, en_git=en_git):
            acreditados.append(cmd)
    return acreditados


def ultimo_resultado_arbol_comando(root, clave_arbol, comando):
    """Obtiene el último registro de ejecución real para un árbol y comando dados."""
    registros = leer_evidencias(root)
    aplicables = [
        r for r in registros if r.get("comando") == comando and (clave_arbol is None or r.get("arbol") == clave_arbol)
    ]
    return aplicables[-1] if aplicables else None


def ejecutar_preflight_worktree(
    repo_root,
    worktree_root=None,
    command=None,
    ejecutar_fn=None,
    timeout=600,
    entorno_override=None,
    forzar_ejecucion=False,
    ejecutor=None,
):
    """Evalúa un comando o la lista de preflight en el worktree reutilizando o compartiendo evidencia aplicable."""
    base_repo = Path(repo_root).resolve()
    fn_efectiva = ejecutar_fn if ejecutar_fn is not None else ejecutor

    if worktree_root is None and command is None:
        cfg = cargar_configuracion(base_repo)
        comandos_pf = list(((cfg.get("release") or {}).get("preflight")) or [])
        if not comandos_pf:
            cmd_val = (cfg.get("validation") or {}).get("command")
            if cmd_val:
                comandos_pf = [cmd_val]
        resultados = []
        for cmd_item in comandos_pf:
            adaptador = None
            if fn_efectiva is not None:

                def _hacer_adaptador(fn_local):
                    def _adapt(c, **kw):
                        sig = inspect.signature(fn_local)
                        pos = [
                            p
                            for p in sig.parameters.values()
                            if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                        ]
                        if len(pos) >= 2 and "etapa" not in sig.parameters:
                            return fn_local(base_repo, _comando_texto(c))
                        return fn_local(_comando_texto(c), **kw)

                    return _adapt

                adaptador = _hacer_adaptador(fn_efectiva)
            res_item = ejecutar_comprobacion(
                base_repo,
                "preflight",
                comando=cmd_item,
                ejecutor=adaptador,
                entorno_override=entorno_override,
                canal="release",
                forzar_ejecucion=forzar_ejecucion,
                repo_evidencia=base_repo,
            )
            resultados.append(res_item)
            if res_item["codigo"] != 0 or not res_item.get("acreditado", True):
                return {
                    "estado": "fallido",
                    "motivo": res_item.get("diagnostico")
                    or res_item.get("salida")
                    or res_item.get("motivo")
                    or "fallo en preflight",
                    "comandos": resultados,
                }
        return {
            "estado": "aprobado",
            "motivo": resultados[-1].get("diagnostico", "") if resultados else "sin comandos de preflight",
            "comandos": resultados,
        }

    base_wt = Path(worktree_root).resolve()
    with _LOCK_GLOBAL:
        _sincronizar_lectura(base_repo)
        if base_wt != base_repo:
            _sincronizar_lectura(base_wt)

    exc_capturada = [None]

    def _adaptador_ejecutor(cmd, **kwargs):
        if fn_efectiva is None:
            return _invocar_ejecutor(None, base_wt, cmd, "preflight", kwargs.get("stream_callback"))
        try:
            sig = inspect.signature(fn_efectiva)
            params = list(sig.parameters.values())
            acepta_var_pos = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
            acepta_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params)
            pos_params = [
                p
                for p in params
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            call_kw = {}
            if "shell" in sig.parameters or acepta_var_kw:
                call_kw["shell"] = True
            if "timeout" in sig.parameters or acepta_var_kw:
                call_kw["timeout"] = timeout
            if acepta_var_pos or len(pos_params) >= 2:
                res = fn_efectiva(base_wt, _comando_texto(cmd), **call_kw)
            else:
                res = fn_efectiva(_comando_texto(cmd), **call_kw)
        except (RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            exc_capturada[0] = exc
            cod = getattr(exc, "returncode", 1)
            return (int(cod) if isinstance(cod, int) and cod != 0 else 1), str(exc)

        if isinstance(res, tuple) and len(res) == 2:
            cod, sal = int(res[0]), str(res[1] or "")
            if cod != 0:
                exc_capturada[0] = RuntimeError(sal or f"Fallo de preflight (código {cod})")
            return cod, sal
        if isinstance(res, int) and not isinstance(res, bool):
            if res != 0:
                exc_capturada[0] = RuntimeError(f"Fallo de preflight (código {res})")
            return res, ""
        return 0, str(res or "")

    res = ejecutar_comprobacion(
        base_wt,
        "preflight",
        comando=command,
        ejecutor=_adaptador_ejecutor,
        entorno_override=entorno_override,
        canal="release",
        forzar_ejecucion=forzar_ejecucion,
        repo_evidencia=base_repo,
    )
    if res["codigo"] != 0 or not res.get("acreditado", True):
        if exc_capturada[0] is not None:
            raise exc_capturada[0]
        detalle = (res.get("salida") or res.get("diagnostico") or res.get("motivo") or "fallo en comprobación").strip()
        raise RuntimeError(f"Fallo de preflight ({_comando_texto(command)}): {detalle}")
    return bool(res.get("reutilizada", False))


def adoptar_flujo_comun(root, ruta_externa_afinn=None):
    """Clasifica evidencias históricas, migra lanzadores redundantes de cierre y registra el estado de Afinn externo."""
    base = Path(root).resolve()
    cfg = cargar_configuracion(base)
    registros = leer_evidencias(base)
    try:
        clave_actual = arbol_trabajo(base)
    except Exception:
        clave_actual = None

    transicion = {}
    vigentes = []
    for fila in registros:
        cmd = fila.get("comando")
        if not cmd:
            continue
        tiene_contrato_v2 = (fila.get("contrato") == "v2") or bool(fila.get("identidad"))
        if not tiene_contrato_v2:
            transicion[cmd] = {
                "clasificacion": "historial_sin_acreditar",
                "motivo": "registro histórico sin identidad compuesta completa",
            }
        elif fila.get("arbol") == clave_actual and fila.get("codigo") == 0 and not fila.get("cambio_en_vuelo"):
            transicion[cmd] = {
                "clasificacion": "vigente_reutilizable",
                "motivo": "evidencia con identidad compuesta vigente sobre el árbol actual",
            }
            if fila not in vigentes:
                vigentes.append(fila)
        else:
            transicion[cmd] = {
                "clasificacion": "invalida_o_antigua",
                "motivo": "evidencia de otro árbol o con resultado no aprobado",
            }

    lanzadores_migrados = []
    scripts_dir = base / "scripts"
    if scripts_dir.is_dir():
        for script_path in sorted(scripts_dir.glob("*.py")):
            texto = script_path.read_text(encoding="utf-8", errors="replace")
            if "subprocess.run" in texto and "ejecutar_cierre_comun" not in texto:
                nuevo_script = (
                    '"""Lanzador de cierre migrado al flujo común de chequeos compartidos."""\n'
                    "from pathlib import Path\n"
                    "from skills.orquestar import chequeos\n\n"
                    'if __name__ == "__main__":\n'
                    '    raise SystemExit(chequeos.ejecutar_cierre_comun(Path.cwd())["codigo"])\n'
                )
                script_path.write_text(nuevo_script, encoding="utf-8")
                lanzadores_migrados.append(str(script_path.relative_to(base)).replace("\\", "/"))

    if lanzadores_migrados and vigentes:
        try:
            nueva_clave = arbol_trabajo(base)
            for fila_vigente in vigentes:
                copia = dict(fila_vigente)
                et_v, inf_v = _info_para_comando(base, comando=copia.get("comando"), cfg=cfg)
                nueva_id = calcular_identidad(base, et_v, inf_v, clave_arbol=nueva_clave)
                copia["arbol"] = nueva_clave
                copia["identidad"] = nueva_id["identidad"]
                copia["identidad_inicial"] = nueva_id["identidad"]
                copia["identidad_final"] = nueva_id["identidad"]
                copia["hash_contenido"] = nueva_id["hash_contenido"]
                copia["entorno"] = nueva_id["entorno"]
                _escribir_evidencia(base, copia)
        except Exception:
            pass

    restricciones = dict(((cfg.get("release") or {}).get("restricciones")) or {})

    estado_externo = {
        "estado": "bloqueado",
        "migracion_in_situ_realizada": False,
        "ruta": str(ruta_externa_afinn) if ruta_externa_afinn else None,
        "motivo": (
            "El repositorio externo Afinn se encuentra fuera del workspace autorizado o no es accesible "
            "en este entorno; la adopción se verifica sobre una copia aislada."
        ),
    }

    return {
        "transicion_evidencia": transicion,
        "lanzadores_migrados": lanzadores_migrados,
        "restricciones_conservadas": restricciones,
        "migracion_afinn_externo": estado_externo,
    }


def ejecutar_cierre_comun(root, entorno_override=None, forzar_ejecucion=False):
    """Ejecuta el flujo común de cierre reutilizando la evidencia acreditada sobre el mismo árbol."""
    base = Path(root).resolve()
    cfg = cargar_configuracion(base)
    cmd_suite = (cfg.get("validation") or {}).get("command")
    preflight = ((cfg.get("release") or {}).get("preflight")) or []
    comandos = []
    if cmd_suite:
        comandos.append(cmd_suite)
    for c in preflight:
        if c not in comandos:
            comandos.append(c)

    todas_reutilizadas = True
    ultimo_res = None
    for cmd in comandos:
        res = ejecutar_comprobacion(
            base,
            "pruebas",
            comando=cmd,
            entorno_override=entorno_override,
            canal="release",
            forzar_ejecucion=forzar_ejecucion,
        )
        ultimo_res = res
        if not res.get("reutilizada"):
            todas_reutilizadas = False
        if res["codigo"] != 0 or not res.get("acreditado", True):
            return {
                "codigo": res["codigo"] or 1,
                "reutilizada": False,
                "motivo": res.get("motivo", ""),
                "diagnostico": res.get("diagnostico", ""),
                "resultado": res,
            }
    return {
        "codigo": 0,
        "reutilizada": todas_reutilizadas,
        "motivo": (ultimo_res or {}).get("motivo", ""),
        "diagnostico": (ultimo_res or {}).get("diagnostico", ""),
    }
