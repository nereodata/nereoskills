"""Gestión ligera y atómica de preguntas humanas (orquestar_preguntas.json)."""

from datetime import datetime
import json
from pathlib import Path
import re

from adevv.registro_metricas import bloqueo
from adevv.revisiones import clave_version, nombre_version
from adevv.store import write_json_atomic

ARCHIVO = "orquestar_preguntas.json"


def _cargar(root: Path) -> list[dict]:
    p = Path(root) / ARCHIVO
    if not p.is_file():
        return []
    try:
        datos = json.loads(p.read_text(encoding="utf-8"))
        return datos if isinstance(datos, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _guardar(root: Path, filas: list[dict]) -> None:
    write_json_atomic(Path(root) / ARCHIVO, filas)


def revision(root: Path, motor, iid: str) -> Path:
    """Ruta del documento de revisión de versión correspondiente al ítem."""
    ficha = motor.fichero_de(root, iid)
    fm = motor.frontmatter(ficha) if ficha else {}
    vk = clave_version(fm.get("version"))
    ver = nombre_version(vk) if vk else "sin-version"
    return Path(root) / "docs" / "review" / "versions" / f"{ver}-revision.md"


def _actualizar_estado_ficha(ficha: Path, nuevo_status: str, pendiente_de: str | None = None, nota: str = "") -> None:
    if not ficha or not ficha.is_file():
        return
    texto = ficha.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---)(.*)$", texto, re.S)
    if not m:
        return
    lineas = [l for l in m.group(2).splitlines() if not re.match(r"^(status|pendiente_de)\s*:", l)]
    lineas.append(f"status: {nuevo_status}")
    if pendiente_de:
        lineas.append(f"pendiente_de: {pendiente_de}")
    cuerpo = m.group(4)
    if nota:
        cuerpo = cuerpo.rstrip() + f"\n\n{nota.strip()}\n"
    ficha.write_text(m.group(1) + "\n".join(lineas) + m.group(3) + cuerpo, encoding="utf-8")


def solicitar(root: Path, motor, iid: str, pregunta: str, rama: str = "") -> str:
    """Registra una pregunta humana pendiente y bloquea la ficha del ítem."""
    root = Path(root)
    with bloqueo(root):
        filas = _cargar(root)
        for existente in filas:
            if existente.get("item_id") == iid and existente.get("estado") == "pendiente":
                return existente["id"]
        num = max((int(re.sub(r"\D", "", f.get("id", "0")) or 0) for f in filas), default=0) + 1
        qid = f"Q-{num:04d}"
        filas.append(
            {
                "id": qid,
                "item_id": iid,
                "pregunta": pregunta.strip(),
                "rama": rama,
                "estado": "pendiente",
                "creada_en": datetime.now().isoformat(timespec="seconds"),
            }
        )
        _guardar(root, filas)
        ficha = motor.fichero_de(root, iid)
        _actualizar_estado_ficha(ficha, "blocked", "humano", f"### Pregunta pendiente ({qid})\n{pregunta.strip()}")
    return qid


def consulta(root: Path) -> str:
    """Devuelve las preguntas humanas pendientes para CLI y Telegram."""
    pendientes = [f for f in _cargar(Path(root)) if f.get("estado") == "pendiente"]
    if not pendientes:
        return "No hay preguntas humanas pendientes."
    return "\n".join(f"- *{f['id']}* ({f['item_id']}): {f['pregunta']}" for f in pendientes)


def responder(root: Path, motor, referencia: str, respuesta: str, usuario: str = "") -> tuple[bool, str]:
    """Registra la respuesta a Q-XXXX (o ID de tarea con única pregunta) y desbloquea la ficha."""
    root = Path(root)
    ref = (referencia or "").strip()
    texto_resp = (respuesta or "").strip()
    if not ref or not texto_resp:
        return False, "Uso: /responder <Q-ID> <respuesta>"

    with bloqueo(root):
        filas = _cargar(root)
        candidatas = [
            f for f in filas if f.get("estado") == "pendiente" and (f.get("id") == ref or f.get("item_id") == ref)
        ]
        if len(candidatas) > 1:
            ids = ", ".join(f["id"] for f in candidatas)
            return False, f"Hay varias preguntas pendientes para {ref} ({ids}); indica el Q-ID exacto."
        if not candidatas:
            ya = next((f for f in filas if f.get("id") == ref and f.get("estado") == "respondida"), None)
            if ya:
                return True, f"{ref} ({ya.get('item_id')}) ya estaba respondida."
            ficha = motor.fichero_de(root, ref)
            if ficha:
                _, cuotas = motor.consumo_cuotas(root)
                if cuotas:
                    return False, f"{ref} no tiene pregunta humana pendiente; existe espera de cuota activa."
                fm = motor.frontmatter(ficha)
                return (
                    False,
                    f"{ref} no tiene pregunta humana pendiente (estado actual: {fm.get('status', 'desconocido')}).",
                )
            return False, f"No existe pregunta pendiente con referencia {ref}."

        objetivo = candidatas[0]
        objetivo["estado"] = "respondida"
        objetivo["respuesta"] = texto_resp
        objetivo["respondida_por"] = str(usuario)
        objetivo["respondida_en"] = datetime.now().isoformat(timespec="seconds")
        _guardar(root, filas)

        iid = objetivo["item_id"]
        ficha = motor.fichero_de(root, iid)
        _actualizar_estado_ficha(
            ficha,
            "planned",
            None,
            f"### Respuesta humana ({objetivo['id']})\n{texto_resp}",
        )
    return True, f"Respuesta registrada en {objetivo['id']}; {iid} vuelve a planned."
