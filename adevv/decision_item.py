"""Decisiones por ítem, aislamiento de WIP y esperas técnicas no bloqueantes."""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from adevv import llamadas
from adevv.store import write_json_atomic


PREFIJOS_BUCLE = ("orquestar", "telegram.", ".adevv-")


def _tiene_git(root):
    return (Path(root) / ".git").exists()


def _git(root, *args, env=None, entrada=None, check=True):
    datos = entrada.encode("utf-8") if isinstance(entrada, str) else entrada
    try:
        res = subprocess.run(["git", *args], cwd=root, env=env, input=datos, capture_output=True)
    except OSError as exc:
        if check:
            raise RuntimeError(str(exc))
        return subprocess.CompletedProcess(["git", *args], 1, b"", str(exc).encode("utf-8"))
    if check and res.returncode:
        raise RuntimeError(res.stderr.decode("utf-8", "replace").strip())
    return res


def _carpeta(root):
    if not _tiene_git(root):
        return None
    res = _git(root, "rev-parse", "--absolute-git-dir", check=False)
    if res.returncode:
        return None
    gitdir = Path(res.stdout.decode("utf-8", "replace").strip())
    if not gitdir.is_absolute():
        gitdir = (Path(root) / gitdir).resolve()
    return gitdir / "adevv-decisiones"


def _ruta(root, rama, iid):
    carpeta = _carpeta(root)
    if not carpeta or not rama or not iid:
        return None
    clave = hashlib.sha256(f"{rama}\0{iid}".encode("utf-8")).hexdigest()
    return carpeta / f"{clave}.json"


def leer(root, rama, iid):
    ruta = _ruta(root, rama, iid)
    if not ruta or not ruta.exists():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def listar(root, rama=None):
    carpeta = _carpeta(root)
    if not carpeta or not carpeta.exists():
        return []
    out = []
    for f in sorted(carpeta.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if rama is None or d.get("rama") == rama:
                out.append(d)
        except (OSError, ValueError):
            continue
    return out


def guardar(root, rama, iid, datos):
    ruta = _ruta(root, rama, iid)
    if not ruta:
        return datos
    ruta.parent.mkdir(parents=True, exist_ok=True)
    registro = {"rama": rama, "iid": iid, **datos}
    write_json_atomic(ruta, registro)
    return registro


def borrar(root, rama, iid):
    ruta = _ruta(root, rama, iid)
    if ruta:
        ruta.unlink(missing_ok=True)


def extraer_decision(salida):
    """Extrae el último bloque estructurado DECISION_ITEM {...} emitido por el paso."""
    for linea in reversed((salida or "").splitlines()):
        m = re.search(r"\bDECISION_ITEM\s+(\{.*\})\s*$", linea.strip())
        if m:
            try:
                obj = json.loads(m.group(1))
                if isinstance(obj, dict):
                    return obj
            except ValueError:
                continue
    return None


def _es_archivo_bucle(rel):
    return Path(rel).name.startswith(PREFIJOS_BUCLE) or rel.startswith(".adevv-")


def _lineas_git(root, *args):
    out = _git(root, *args, check=False).stdout.decode("utf-8", "replace").splitlines()
    return [r for r in out if r and not _es_archivo_bucle(r)]


def aislar_wip(root, motor, iid, base_commit):
    """Guarda cambios sin confirmar del ítem en refs/heads/wip/<iid> y limpia el árbol."""
    if not _tiene_git(root) or not base_commit:
        return ""
    motor.excluir(root)
    cambiados = _lineas_git(root, "diff", "--name-only", base_commit)
    nuevos = _lineas_git(root, "ls-files", "--others", "--exclude-standard")
    head = _git(root, "rev-parse", "HEAD", check=False).stdout.decode("utf-8", "replace").strip()
    if not cambiados and not nuevos and head == base_commit:
        return ""
    fd, idx_tmp = tempfile.mkstemp(prefix="adevv-wip-idx-")
    os.close(fd)
    Path(idx_tmp).unlink(missing_ok=True)
    env = {**os.environ, "GIT_INDEX_FILE": idx_tmp}
    try:
        _git(root, "read-tree", head or base_commit, env=env)
        objetivos = sorted(set(cambiados + nuevos))
        if objetivos:
            _git(root, "add", "-A", "--", *objetivos, env=env)
        arbol = _git(root, "write-tree", env=env).stdout.decode("utf-8").strip()
        commit = (
            _git(root, "commit-tree", arbol, "-p", base_commit, "-m", f"wip({iid})", env=env)
            .stdout.decode("utf-8")
            .strip()
        )
        wip_rama = f"wip/{iid}"
        _git(root, "update-ref", f"refs/heads/{wip_rama}", commit)
    finally:
        Path(idx_tmp).unlink(missing_ok=True)
    _git(root, "reset", "--hard", base_commit)
    for rel in nuevos:
        p = Path(root) / rel
        p.unlink(missing_ok=True)
        padre = p.parent
        while padre != Path(root) and padre.exists() and not any(padre.iterdir()):
            padre.rmdir()
            padre = padre.parent
    return wip_rama


def restaurar_wip(root, rama, iid):
    """Restaura sobre un árbol limpio el WIP aislado de una espera técnica previa."""
    d = leer(root, rama, iid)
    if not d or not d.get("wip_rama") or d.get("wip_en_arbol"):
        return True
    if _git(root, "status", "--porcelain", check=False).stdout.strip():
        return False
    wip_rama = d["wip_rama"]
    base = d.get("base_commit") or ""
    if not base or _git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{wip_rama}", check=False).returncode:
        return True
    parche = _git(root, "diff", "--binary", base, wip_rama, check=False).stdout
    if parche:
        aplico = _git(root, "apply", "--3way", "-", entrada=parche, check=False)
        if aplico.returncode:
            aplico = _git(root, "apply", "-", entrada=parche, check=False)
            if aplico.returncode:
                return False
    d["wip_en_arbol"] = True
    guardar(root, rama, iid, d)
    return True


def bloqueada_condicion(root, motor, d):
    """Comprueba sin invocar modelos si persiste una causa objetivamente irresoluble ahora."""
    if not d or d.get("tipo") != "espera":
        return False
    causa = d.get("causa")
    if causa not in ("cuota", "ejecutable"):
        return False
    rol = d.get("rol") or "hades"
    iid = d.get("iid", "")
    dif = motor.dificultad_de(root, iid) if iid else None
    cfg = motor.aplicar_perfil(
        root, iid, rol, motor.ajustes(motor.config(root).get(rol, {}), d.get("paso", ""), dificultad=dif)
    )
    perfiles = [cfg] + motor.lista_reservas(cfg)
    if causa == "cuota":
        return not bool(motor.configuraciones_con_cuota(root, perfiles))
    for p in perfiles:
        base = motor.base_comando_agente(p.get("harness", "claude"), "x", sesion=None)
        if base and motor.buscar_ejecutable(base[0]):
            return False
    return True


def texto_decision(d):
    if not d:
        return ""
    if d.get("tipo") == "asignacion":
        return (
            f"{d['iid']}: asignada a {d['destino']} → {d['siguiente']} "
            f"({d.get('mandato', '')}; condición: {d.get('condicion', '')})"
        )
    if d.get("tipo") == "aclaracion":
        return f"{d['iid']}: aclaración pendiente ({d.get('impedimento', '')})"
    if d.get("tipo") == "espera":
        obj = f" ({d['objetivo']})" if d.get("objetivo") else ""
        return f"{d['iid']}: en {d['situacion']}{obj} — condición: {d.get('condicion', '')}"
    return ""


def resumen(root, rama=None):
    lineas = [texto_decision(d) for d in listar(root, rama)]
    return "\n".join(l for l in lineas if l)


def contexto_prompt(root, rama, iid):
    """Contexto inyectado al paso cuando retoma una aclaración, asignación o espera."""
    d = leer(root, rama, iid)
    if not d:
        return "", ""
    if d.get("tipo") == "aclaracion":
        return (
            f" Aclara la decisión pendiente sobre el impedimento «{d.get('impedimento', '')}»: "
            "indica destino, mandato y condición de salida mediante DECISION_ITEM."
        ), ""
    if d.get("tipo") == "asignacion":
        return (
            f" Asignación técnica para {d['destino']}: {d.get('mandato', '')}. "
            f"Condición de salida: {d.get('condicion', '')}."
        ), ""
    if d.get("tipo") == "espera":
        rev = f"Revisión pendiente: {d['objetivo']}. " if d.get("objetivo") else ""
        return (f" Reanudación tras {d['situacion']}. {rev}Condición para resolver: {d.get('condicion', '')}."), d.get(
            "entradas", ""
        )
    return "", ""


def _clasificar_llamada_pendiente(pendientes):
    for r in reversed(pendientes):
        if not r.objetivo:
            continue
        salida = r.salida or ""
        if r.estado == "espera_cuota" or r.espera_s is not None:
            return r, "cuota", "espera de cuota", "capacidad recuperada del rol requerido"
        if "ningún arnés disponible" in salida:
            return r, "ejecutable", "pausa motivada", "ejecutable autorizado disponible"
        if "Acceso por suscripción deshabilitado" in salida:
            return r, "suscripcion", "espera técnica", "recuperar acceso de un perfil autorizado"
    return None, "", "", ""


def _guardar_espera(root, motor, rama, iid, base_commit, previa, campos):
    objetivo = campos.get("objetivo", "")
    prev_ent = (previa or {}).get("entradas") or ""
    entradas = prev_ent if (previa or {}).get("objetivo") == objetivo and prev_ent else campos.pop("entradas", "")
    wip = aislar_wip(root, motor, iid, base_commit) or (previa or {}).get("wip_rama", "")
    base = {
        "tipo": "espera",
        "entradas": entradas,
        "wip_rama": wip,
        "base_commit": base_commit if wip else "",
        "wip_en_arbol": False,
    }
    return guardar(root, rama, iid, {**base, **campos})


def aplicar_post_paso(root, motor, intervencion, paso, iid, rama, base_commit, almacen_llamadas, salida):
    """Registra transiciones de DECISION_ITEM o esperas de revisión y aísla WIP cuando procede."""
    if not _tiene_git(root) or not rama or not iid:
        return None
    previa = leer(root, rama, iid)
    dec = extraer_decision(salida)
    if dec is not None:
        destino = str(dec.get("destino") or "").strip().lower()
        clave, impedimento = str(dec.get("clave") or "").strip(), str(dec.get("impedimento") or "").strip()
        aclarar = {"tipo": "aclaracion", "clave": clave, "impedimento": impedimento}
        if destino == "humano":
            pregunta = str(dec.get("pregunta") or "").strip()
            if not pregunta:
                return guardar(root, rama, iid, aclarar)
            borrar(root, rama, iid)
            intervencion.solicitar(
                root, motor, iid, pregunta, contexto=impedimento, paso=paso, base_commit=base_commit, clave=clave
            )
            return {"tipo": "humano", "iid": iid}
        if destino == "espera_tecnica":
            objetivo = str(dec.get("revision") or dec.get("objetivo") or "").strip()
            cond = str(dec.get("condicion") or "condición técnica recuperada").strip()
            datos = {
                "causa": "servicio",
                "situacion": "espera técnica",
                "paso": paso,
                "rol": "hades",
                "clave": clave,
                "objetivo": objetivo,
                "impedimento": impedimento,
                "condicion": cond,
            }
            return _guardar_espera(root, motor, rama, iid, base_commit, previa, datos)
        if destino in ("especificador", "artemisa"):
            mandato, cond = str(dec.get("mandato") or "").strip(), str(dec.get("condicion") or "").strip()
            if not mandato or not cond:
                return guardar(root, rama, iid, aclarar)
            sig = "especificar" if destino == "especificador" else ("bug-fix" if iid.startswith("B-") else "task-dev")
            datos = {
                "tipo": "asignacion",
                "destino": destino,
                "siguiente": sig,
                "clave": clave,
                "impedimento": impedimento,
                "mandato": mandato,
                "condicion": cond,
            }
            return guardar(root, rama, iid, datos)
        return guardar(root, rama, iid, aclarar)

    entregas = llamadas.leer(almacen_llamadas) if almacen_llamadas else []
    r, causa, situacion, cond = _clasificar_llamada_pendiente(llamadas.pendientes(entregas) if entregas else [])
    if r is not None:
        datos = {
            "causa": causa,
            "situacion": situacion,
            "paso": paso,
            "rol": r.rol,
            "clave": r.objetivo,
            "objetivo": r.objetivo,
            "entradas": r.entradas,
            "condicion": cond,
        }
        return _guardar_espera(root, motor, rama, iid, base_commit, previa, datos)

    if previa:
        if previa.get("tipo") == "asignacion" and paso != previa.get("siguiente"):
            return previa
        borrar(root, rama, iid)
    return None
