"""Identidad de versiones, huella de producto, evidencias y validación de revisiones."""

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from adevv import contexto_ejecucion
from adevv.registro_metricas import bloqueo, leer_registros
from adevv.yaml_lite import load_yaml

EVIDENCIAS = "orquestar_evidencias.jsonl"


def _es_ignorado_huella(rel: str) -> bool:
    partes = rel.split("/")
    if ".git" in partes or "__pycache__" in partes or any(p.startswith(".adevv-") for p in partes):
        return True
    if len(partes) == 1 and (rel.startswith(("orquestar.", "orquestar_", "telegram.")) or rel == ".env"):
        return True
    return False


def clave_version(valor):
    """Devuelve (mayor, menor, parche); la omisión del parche equivale a cero."""
    m = re.fullmatch(r"v?(\d+)\.(\d+)(?:\.(\d+))?", str(valor or "").strip())
    return (int(m[1]), int(m[2]), int(m[3] or 0)) if m else None


def nombre_version(clave):
    """Formatea una tupla (mayor, menor, parche) conservando parches positivos."""
    return f"v{clave[0]}.{clave[1]}" + (f".{clave[2]}" if clave[2] else "")


def carpetas_maestras(root, cfg=None):
    """Directorios configurados de tareas y bugs maestros."""
    root = Path(root)
    if cfg is None:
        p = root / "task_config.yaml"
        cfg = (load_yaml(p) or {}) if p.is_file() else {}
    master = (cfg.get("levels") or {}).get("master") or {}
    base = root / master.get("path", "docs/plan/")
    folders = master.get("folders") or {}
    return tuple(base / folders.get(t, master.get(t, t + "/")) for t in ("tasks", "bugs"))


def _rutas_excluidas(root, carpetas=None):
    root = Path(root)
    carpetas = carpetas if carpetas is not None else carpetas_maestras(root)
    excl = []
    for p in carpetas:
        try:
            excl.append(p.resolve().relative_to(root.resolve()).as_posix().rstrip("/") + "/")
        except ValueError:
            pass
    excl.append("docs/review/")
    return tuple(excl)


def _git_env():
    return {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "never",
    }


def huella_producto(root, arbol=None, carpetas=None):
    """SHA-256 determinista del código/archivos de producto excluyendo plan, revisiones y estado efímero."""
    root = Path(root).resolve()
    excluidos = _rutas_excluidas(root, carpetas)
    digest = hashlib.sha256()
    tiene_git = (root / ".git").exists()
    if arbol and tiene_git:
        try:
            entradas = subprocess.check_output(
                ["git", "ls-tree", "-rz", "--name-only", "--full-tree", arbol],
                cwd=root,
                env=_git_env(),
                stderr=subprocess.DEVNULL,
            )
            rutas = sorted({x.decode("utf-8", errors="replace") for x in entradas.split(b"\0") if x})
            for rel in rutas:
                if rel.startswith(excluidos) or _es_ignorado_huella(rel):
                    continue
                contenido = subprocess.check_output(
                    ["git", "show", f"{arbol}:{rel}"], cwd=root, env=_git_env(), stderr=subprocess.DEVNULL
                )
                digest.update(rel.encode("utf-8") + b"\0")
                digest.update(hashlib.sha256(contenido).digest() + b"\0")
            return digest.hexdigest()
        except (OSError, subprocess.CalledProcessError):
            pass

    candidatos = None
    if tiene_git:
        try:
            salida = subprocess.check_output(
                ["git", "ls-files", "-co", "--exclude-standard", "-z"],
                cwd=root,
                env=_git_env(),
                stderr=subprocess.DEVNULL,
            )
            if isinstance(salida, bytes):
                candidatos = [x.decode("utf-8", errors="replace") for x in salida.split(b"\0") if x]
        except (OSError, subprocess.CalledProcessError):
            candidatos = None
    if candidatos is None:
        candidatos = [
            p.relative_to(root).as_posix()
            for p in root.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(root).parts
        ]

    for rel in sorted(set(candidatos)):
        if rel.startswith(excluidos) or _es_ignorado_huella(rel):
            continue
        fp = root / rel
        if fp.is_file():
            digest.update(rel.encode("utf-8") + b"\0")
            digest.update(hashlib.sha256(fp.read_bytes()).digest() + b"\0")
    return digest.hexdigest()


def declaracion(texto):
    """Extrae (veredicto, huella) de las líneas propias del informe (ignorando cercos de código y citas)."""
    en_cerco = False
    veredicto = ""
    huella = None
    for cruda in (texto or "").splitlines()[:40]:
        linea = cruda.strip()
        if linea.startswith(("```", "~~~")):
            en_cerco = not en_cerco
            continue
        if en_cerco or linea.startswith(">"):
            continue
        if not veredicto:
            m = re.search(
                r"(?:^|[#*\-\s])veredicto\**\s*:\s*[^A-Za-z0-9N/]*(APROBADO|RECHAZADO|N/A)\b",
                linea,
                re.I,
            ) or re.match(r"^\**\s*(APROBADO|RECHAZADO|N/A)\s*\**$", linea, re.I)
            if m:
                veredicto = m.group(1).upper()
                continue
        if huella is None:
            mh = re.match(r"Producto revisado:\s*([0-9a-fA-F]{12,64})\b", linea)
            if mh:
                huella = mh.group(1).lower()
    return veredicto, huella


def motivo_informe(path):
    """Valida el veredicto formal de un informe de revisión."""
    try:
        texto = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return "informe ausente"
    except (OSError, UnicodeError):
        return "informe ilegible"
    veredicto, _ = declaracion(texto)
    if veredicto == "APROBADO":
        return ""
    if veredicto == "RECHAZADO":
        return "informe rechazado"
    if veredicto == "N/A":
        if re.search(
            r"Motivo:\s*.*(?:sin cambios de c[oó]digo|sin c[oó]digo|no hay cambios de c[oó]digo|fuera de superficies cr[ií]ticas|sin superficies cr[ií]ticas)",
            texto,
            re.I,
        ):
            return ""
        return "N/A sin justificación de ausencia de código"
    return "informe sin veredicto formal"


def _archivos_cambiados_item(root: Path, iid: str, ficha: Path | None) -> list[str]:
    if not (root / ".git").exists():
        return []
    try:
        commits = []
        if ficha and ficha.exists():
            c_ficha = subprocess.check_output(
                [
                    "git",
                    "log",
                    "-1",
                    "--format=%H",
                    "-G",
                    r"^status:\s*['\"]?completed",
                    "--",
                    ficha.relative_to(root).as_posix(),
                ],
                cwd=root,
                env=_git_env(),
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if c_ficha:
                commits.append(c_ficha)
        c_grep = subprocess.check_output(
            ["git", "log", "--format=%H", "-F", f"--grep={iid}"],
            cwd=root,
            env=_git_env(),
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
        commits.extend(c.strip() for c in c_grep if c.strip() and c.strip() not in commits)
        if not commits:
            return []
        salida = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", *commits],
            cwd=root,
            env=_git_env(),
            text=True,
            stderr=subprocess.DEVNULL,
        )
        excl = _rutas_excluidas(root)
        return sorted({r.strip() for r in salida.splitlines() if r.strip() and not r.strip().startswith(excl)})
    except (OSError, subprocess.CalledProcessError, ValueError):
        return []


def motivo_revision(root, iid, ficha=None, carpetas=None):
    """Devuelve '' si la revisión del ítem está aprobada o exenta por no tocar superficies críticas."""
    root = Path(root)
    informe = root / "docs" / "review" / "code_reviews" / f"{iid}-code-review.md"
    if not informe.is_file():
        cambiados = _archivos_cambiados_item(root, iid, Path(ficha) if ficha else None)
        if cambiados and not contexto_ejecucion.toca_superficie_critica(root, cambiados):
            return ""
        return "informe ausente"
    return motivo_informe(informe)


def diagnostico_revision(root, iid, ficha=None, carpetas=None):
    """Describe el bloqueo de revisión añadiendo causa de cuota si Hades quedó sin cuota."""
    motivo = motivo_revision(root, iid, ficha, carpetas)
    if not motivo:
        return ""
    ultimo = None
    for dato in leer_registros(root, tolerar_ultima=True):
        if dato.get("tipo") == "agente" and dato.get("rol") == "hades" and dato.get("id") == iid:
            ultimo = dato
    if ultimo and (ultimo.get("sin_cuota") or ultimo.get("cuota_espera_s")):
        motivo += "; Hades sin cuota: recuperar disponibilidad de Hades"
    return f"{iid}: {motivo}; obtener revisión con revisar-tarea y volver a validar el cierre."


def pendientes_cierre(root, version, cfg=None):
    """Enumera maestros abiertos o completados sin revisión válida de la versión indicada."""
    root = Path(root)
    if cfg is None:
        p = root / "task_config.yaml"
        cfg = (load_yaml(p) or {}) if p.is_file() else {}
    carpetas = carpetas_maestras(root, cfg)
    pendientes = []
    for carpeta in carpetas:
        if not carpeta.is_dir():
            continue
        for path in sorted(carpeta.glob("*.md")):
            texto = path.read_text(encoding="utf-8")
            m = re.match(r"^---\s*\n(.*?)\n---", texto, re.S)
            fm = (load_yaml(m[1]) or {}) if m else {}
            if not fm.get("id") or fm.get("parent_id") or clave_version(fm.get("version")) != clave_version(version):
                continue
            iid, status = str(fm["id"]), str(fm.get("status", "")).lower()
            if status == "completed":
                mensaje = diagnostico_revision(root, iid, path, carpetas)
                if mensaje:
                    pendientes.append(mensaje)
            elif status not in {"cancelled", "superseded", "rejected"}:
                pendientes.append(f"{iid}: trabajo pendiente ({status or 'sin estado'}).")
    return pendientes


def evidencia_vigente(root: Path, huella: str, comando: str) -> bool:
    """Comprueba si comando ya pasó en verde para la misma huella de producto."""
    archivo = Path(root) / EVIDENCIAS
    if not archivo.is_file():
        return False
    cmd_norm = " ".join(comando.strip().split())
    exito = False
    for linea in archivo.read_text(encoding="utf-8", errors="replace").splitlines():
        if not linea.strip():
            continue
        try:
            d = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if d.get("huella") == huella and " ".join(str(d.get("comando", "")).strip().split()) == cmd_norm:
            exito = d.get("codigo") == 0
    return exito


def registrar_evidencia(root: Path, huella: str, comando: str, codigo: int, duracion_s: int = 0) -> None:
    """Persiste el resultado de una verificación vinculada a su huella de producto."""
    root = Path(root)
    fila = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "huella": huella,
        "comando": " ".join(comando.strip().split()),
        "codigo": int(codigo),
        "duracion_s": int(duracion_s),
    }
    with bloqueo(root):
        with (root / EVIDENCIAS).open("a", encoding="utf-8") as f:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def verificar_restriccion_release(root: Path, actor: str, accion: str, cfg: dict | None = None) -> None:
    """Valida políticas opcionales task_config.yaml::release.restricciones."""
    if cfg is None:
        p = Path(root) / "task_config.yaml"
        cfg = (load_yaml(p) or {}) if p.is_file() else {}
    restricciones = ((cfg.get("release") or {}).get("restricciones") or {}).get(accion)
    if isinstance(restricciones, dict) and restricciones.get("permitido") is False:
        raise ValueError(f"Acción de release '{accion}' deshabilitada por configuración.")
    if isinstance(restricciones, list) and actor not in restricciones:
        raise ValueError(f"El actor '{actor}' no está autorizado para '{accion}'.")


def ejecutar_preflight_worktree(root: Path, worktree: Path, command: str, ejecutar_fn, timeout: float = 600) -> None:
    """Ejecuta un comando de preflight salvo que su huella de producto ya esté acreditada en verde."""
    huella = huella_producto(worktree)
    if evidencia_vigente(root, huella, command):
        return
    ejecutar_fn(worktree, command, shell=True, timeout=timeout)
    registrar_evidencia(root, huella, command, 0)
