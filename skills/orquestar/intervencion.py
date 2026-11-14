"""Intervenciones humanas duraderas, aisladas del paso activo del orquestador."""

import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from adevv.revisiones import nombre_version

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    import fcntl
except ImportError:
    fcntl = None

PREGUNTAS = "orquestar_preguntas.json"
RESPUESTAS = "orquestar_respuestas.jsonl"


@contextmanager
def bloqueo(root, nombre="adevv-intervencion.lock"):
    """Serializa gateway y motor mediante un bloqueo liberado por el sistema operativo."""
    ruta = Path(git(root, "rev-parse", "--absolute-git-dir")) / nombre
    with ruta.open("a+b") as fichero:
        if os.name == "nt":
            fichero.seek(0)
            fichero.write(b"0")
            fichero.flush()
            fichero.seek(0)
            msvcrt.locking(fichero.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(fichero, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                fichero.seek(0)
                msvcrt.locking(fichero.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(fichero, fcntl.LOCK_UN)


def guardar(ruta, datos):
    """Publica JSON completo con reemplazo atómico y sincronización a disco."""
    fd, temporal = tempfile.mkstemp(prefix="adevv-intervencion-", dir=ruta.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as salida:
            json.dump(datos, salida, ensure_ascii=False, indent=2)
            salida.flush()
            os.fsync(salida.fileno())
        os.replace(temporal, ruta)
    finally:
        Path(temporal).unlink(missing_ok=True)


def leer(root):
    """Lee el registro sin ocultar corrupción de los datos persistidos."""
    ruta = root / PREGUNTAS
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else []


def listar(root, solo_pendientes=False):
    """Devuelve preguntas del proyecto, opcionalmente solo las abiertas."""
    return [q for q in leer(root) if not solo_pendientes or q["estado"] == "pendiente"]


def git(root, *args, entrada=None, binario=False):
    """Ejecuta Git preservando los bytes de parches y propaga cualquier fallo."""
    if binario or entrada is not None:
        datos = entrada.encode("utf-8") if isinstance(entrada, str) else entrada
        salida = subprocess.run(["git", *args], cwd=root, input=datos, capture_output=True, check=True).stdout
        return salida if binario else salida.decode("utf-8").strip()
    return subprocess.run(
        ["git", *args], cwd=root, input=entrada, text=True, encoding="utf-8", capture_output=True, check=True
    ).stdout.strip()


def revision(root, motor, iid):
    """Resuelve el informe de la versión de una tarea."""
    v = motor.vkey(motor.frontmatter(motor.fichero_de(root, iid)).get("version"))
    if not v:
        raise ValueError("La intervención requiere una tarea con versión")
    return root / f"docs/review/versions/{nombre_version(v)}-revision.md"


def asegurar_destino(root, motor, q):
    """Selecciona la rama registrada solo con árbol limpio y conserva la cola si no es seguro."""
    rama = q.get("rama")
    if not rama or not rama.startswith(("release/", "hotfix/")):
        q["impedimento_incorporacion"] = "Falta una rama de destino válida; requiere recuperación local."
        return False
    actual = git(root, "branch", "--show-current")
    preparadas = q.get("escritura", {})
    if git(root, "status", "--porcelain"):
        propias = set(preparadas)
        modificadas = set(git(root, "diff", "--name-only", "HEAD").splitlines())
        modificadas.update(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
        if actual != rama or not modificadas.issubset(propias):
            q["impedimento_incorporacion"] = "Hay trabajo local; respuesta conservada en cola sin modificar Git."
            return False
        for rel in modificadas:
            if not (root / rel).exists() or (root / rel).read_text(encoding="utf-8") != preparadas[rel]["despues"]:
                q["impedimento_incorporacion"] = "Los archivos de destino tienen cambios ajenos; respuesta en cola."
                return False
    if actual != rama:
        if not motor.cambiar_de_rama(root, rama):
            q["impedimento_incorporacion"] = f"No se puede abrir {rama}; respuesta conservada en cola."
            return False
    q.pop("impedimento_incorporacion", None)
    return True


def anotar(root, motor, q, texto, cambios, preguntas):
    """Escribe contexto y estado únicamente en tarea e informe de versión."""
    tarea = motor.fichero_de(root, q["tarea_id"])
    informe = revision(root, motor, q["tarea_id"])
    cabecera, cuerpo = motor.reescribir_frontmatter(tarea.read_text(encoding="utf-8"), cambios)
    if cambios.get("status") == "planned":
        cabecera = "\n".join(l for l in cabecera.splitlines() if not l.startswith("pendiente_de:"))
    nota = f"\n\n## Intervención humana {q['id']}\n{texto}\n"
    if texto not in cuerpo:
        cuerpo += nota
    informe.parent.mkdir(parents=True, exist_ok=True)
    previo = informe.read_text(encoding="utf-8") if informe.exists() else ""
    contenidos = {
        tarea: cabecera + "\n---\n" + cuerpo,
        informe: previo if texto in previo else previo + f"\n\n## {q['tarea_id']} · {q['id']}\n{texto}\n",
    }
    if not q.get("escritura"):
        q["escritura"] = {
            str(p.relative_to(root)): {
                "antes": p.read_text(encoding="utf-8") if p.exists() else None,
                "despues": contenido,
            }
            for p, contenido in contenidos.items()
        }
        guardar(root / PREGUNTAS, preguntas)
    for rel, preparada in q["escritura"].items():
        ruta = root / rel
        actual = ruta.read_text(encoding="utf-8") if ruta.exists() else None
        if actual not in (preparada["antes"], preparada["despues"]):
            raise ValueError(f"Cambio ajeno en {rel}; se conserva la intervención para recuperación")
        ruta.write_text(preparada["despues"], encoding="utf-8")
    rutas = [str(p.relative_to(root)) for p in (tarea, informe)]
    git(root, "add", "--", *rutas)
    if git(root, "diff", "--cached", "--name-only", "--", *rutas):
        git(root, "commit", "-qm", f"docs({q['tarea_id']}): intervención {q['id']}", "--", *rutas)
    q.pop("escritura", None)


def completar_solicitud(root, motor, q, preguntas):
    """Reanuda las fases persistidas de bloqueo y aviso sin repetir efectos completados."""
    if not q.get("bloqueo_aplicado"):
        if not asegurar_destino(root, motor, q):
            guardar(root / PREGUNTAS, preguntas)
            return False
        anotar(
            root,
            motor,
            q,
            f"{q['pregunta']}\n{q['contexto']}\nResponder: /responder {q['id']} <respuesta>",
            {"status": "blocked", "pendiente_de": "humano"},
            preguntas,
        )
        q["bloqueo_aplicado"] = True
        guardar(root / PREGUNTAS, preguntas)
    if not q.get("aviso_intentado"):
        cfg = motor.telegram(root)
        diagnostico = (
            "canal no disponible"
            if not cfg
            else "evento desactivado"
            if "respuesta" not in cfg[2]
            else "envío iniciado"
        )
        q.update(diagnostico_aviso=diagnostico, aviso_intentado=True)
        guardar(root / PREGUNTAS, preguntas)
        if diagnostico == "envío iniciado":
            q["notificada"] = bool(
                motor.avisar(
                    root,
                    "respuesta",
                    f"{q['tarea_id']} · {q['id']}\n{q['pregunta']}\n{q['contexto']}\n/responder {q['id']} <respuesta>",
                )
            )
            q["diagnostico_aviso"] = "enviado" if q["notificada"] else "fallo de envío"
        guardar(root / PREGUNTAS, preguntas)
    elif q.get("diagnostico_aviso") == "envío iniciado":
        q["diagnostico_aviso"] = "envío interrumpido; consultar pregunta, sin reenvío automático"
        guardar(root / PREGUNTAS, preguntas)
    return True


def solicitar(root, motor, iid, pregunta, contexto="", paso="", aislar=True, base_commit=None, clave=""):
    """Conserva el trabajo, bloquea solo la tarea y emite un aviso accionable único."""
    if not pregunta.strip() or not motor.fichero_de(root, iid):
        raise ValueError("Se requieren tarea existente y pregunta concreta")
    motor.excluir(root)
    with bloqueo(root):
        preguntas = leer(root)
        if clave:
            incorporada = next(
                (
                    q
                    for q in reversed(preguntas)
                    if q["tarea_id"] == iid and q.get("clave") == clave and q["estado"] == "incorporada"
                ),
                None,
            )
            if incorporada:
                return incorporada.copy()
        existente = next(
            (
                q
                for q in preguntas
                if q["tarea_id"] == iid
                and q["estado"] == "pendiente"
                and ((clave and q.get("clave") == clave) or q["pregunta"] == pregunta)
            ),
            None,
        )
        if existente:
            completar_solicitud(root, motor, existente, preguntas)
            return existente
        qid = f"Q-{motor.prefijo(root)}-{len(preguntas) + 1:04d}"
        base = base_commit or git(root, "rev-parse", "HEAD")
        q = dict(
            id=qid,
            tarea_id=iid,
            clave=clave,
            pregunta=pregunta,
            contexto=contexto,
            paso=paso,
            estado="pendiente",
            proyecto=str(root.resolve()),
            fecha=motor.ahora(),
            base_commit=base,
            wip_rama="",
            wip_restaurado=False,
            notificada=False,
            rama=git(root, "branch", "--show-current"),
            bloqueo_aplicado=False,
            aviso_intentado=False,
        )
        if aislar and (git(root, "status", "--porcelain") or git(root, "rev-parse", "HEAD") != base):
            rama = git(root, "branch", "--show-current")
            if not rama.startswith(("release/", "hotfix/")):
                raise ValueError("El aislamiento requiere una rama release o hotfix")
            wip = f"wip/{iid}"
            git(root, "checkout", "-B", wip)
            git(root, "add", "-A")
            if git(root, "diff", "--cached", "--name-only"):
                git(root, "commit", "-qm", f"wip({iid}): conservar intervención humana")
            git(root, "branch", "-f", rama, base)
            git(root, "checkout", "-q", rama)
            q["wip_rama"] = wip
        preguntas.append(q)
        guardar(root / PREGUNTAS, preguntas)
        completar_solicitud(root, motor, q, preguntas)
        return q.copy()


def consulta(root, solo_pendientes=False):
    """Presenta referencias y diagnóstico sin efectos secundarios."""
    bloques = [
        f"Bloqueo de tarea {q['tarea_id']} · {q['id']}: {q['pregunta']}\n"
        f"{q['contexto']}\n{q.get('diagnostico_aviso', 'pendiente')}\n"
        f"{q.get('impedimento_incorporacion', '')}\n"
        f"/responder {q['id']} <respuesta>"
        for q in listar(root, True)
    ]
    if not solo_pendientes:
        bloques.extend(
            f"Decisión incorporada {q['tarea_id']} · {q['id']}: {q['pregunta']}\nRespuesta: {q.get('respuesta', '')}"
            for q in listar(root)
            if q.get("estado") == "incorporada"
        )
    return "\n".join(bloques) or "Sin preguntas pendientes."


def responder(root, motor, usuario, argumento, autorizados):
    """Recibe una respuesta autorizada sin modificar el árbol durante un paso."""
    if str(usuario) not in autorizados:
        return None
    return recibir(root, motor, usuario, argumento)


def recibir(root, motor, usuario, argumento, referencia_obligatoria=False):
    """Serializa recepción, incorporación y eventual arranque entre adaptadores."""
    with bloqueo(root, "adevv-respuesta.lock"):
        return recibir_serializado(root, motor, usuario, argumento, referencia_obligatoria)


def recibir_serializado(root, motor, usuario, argumento, referencia_obligatoria):
    """Aplica el contrato compartido bajo el bloqueo de recepción del proyecto."""
    with bloqueo(root):
        preguntas = leer(root)
        referencia, _, texto = argumento.strip().partition(" ")
        if referencia_obligatoria and not referencia.startswith(("Q-", "T-", "B-")):
            return "La referencia no existe."
        q = next((x for x in preguntas if referencia == x["id"]), None)
        if referencia.startswith(("T-", "B-")):
            candidatas = [x for x in preguntas if x["tarea_id"] == referencia and x["estado"] == "pendiente"]
            if len(candidatas) > 1:
                return "Respuesta ambigua: " + ", ".join(x["id"] for x in candidatas)
            q = candidatas[0] if candidatas else None
        if referencia.startswith("Q-") and not referencia.startswith(f"Q-{motor.prefijo(root)}-"):
            return "La referencia no pertenece a este proyecto."
        if not q:
            abiertas = [x for x in preguntas if x["estado"] == "pendiente"]
            if referencia.startswith(("Q-", "T-", "B-")):
                return "La referencia no existe."
            if len(abiertas) != 1:
                return "Respuesta ambigua: " + ", ".join(x["id"] for x in abiertas)
            q, texto = abiertas[0], argumento.strip()
        if q.get("proyecto") != str(root.resolve()):
            return "La referencia no pertenece a este proyecto."
        if q["estado"] != "pendiente":
            return "La pregunta ya está cerrada."
        texto = texto.strip()
        if not texto.strip():
            return "Falta la respuesta."
        if texto in q.get("recibidas", []):
            return f"Respuesta duplicada para {q['id']}; ya recibida."
        q.setdefault("recibidas", []).append(texto)
        q["respuesta_en_cola"] = texto
        q.setdefault("cola", []).append(
            {
                "texto": texto,
                "usuario": str(usuario),
                "fecha": motor.ahora(),
                "orden": 1 + max((r.get("orden", 0) for p in preguntas for r in p.get("cola", [])), default=0),
            }
        )
        guardar(root / PREGUNTAS, preguntas)
        qid, iid = q["id"], q["tarea_id"]
    if motor.pid_vivo(root):
        return f"Respuesta recibida para {qid} ({iid}); se incorporará al terminar el paso en curso"
    estado = motor.estado(root, "docs/requirements")
    esperando = estado[0] == "PARAR" and "Bloqueo de tarea;" in estado[1]
    incorporadas = motor.incorporar_respuestas(root)
    if (root / motor.PARADA).exists():
        return f"Respuesta recibida para {qid}; se respeta la parada manual."
    aplicada = any(q["id"] == qid for q in incorporadas)
    actual = next(q for q in listar(root) if q["id"] == qid)
    if not aplicada and actual.get("motivo_insuficiente") and not actual.get("cola"):
        return f"Respuesta recibida para {qid}; sigue bloqueada: {actual['motivo_insuficiente']}"
    tarea = motor.fichero_de(root, iid) if aplicada else None
    reanudable = tarea and motor.frontmatter(tarea).get("status") == "planned"
    if aplicada and not reanudable:
        return f"Respuesta incorporada para {qid}; la tarea sigue bloqueada por otra pregunta."
    if aplicada:
        items = {i["id"]: i for i in motor.backlog(root)}
        pendientes = motor.pendientes_de(items[iid], items)
        if pendientes:
            return f"Respuesta incorporada para {qid}; tarea {iid} en espera de dependencias: {', '.join(pendientes)}."
    if aplicada and esperando:
        motor.en_fondo(root, argumentos=[])
        return f"Respuesta incorporada; tarea {iid} reanudada."
    if aplicada:
        return f"Respuesta incorporada; tarea {iid} elegible para el próximo paso."
    return f"Respuesta recibida para {qid}; la tarea sigue bloqueada."


def incorporar(root, motor):
    """Incorpora respuestas duraderas en orden de recepción entre pasos."""
    if not (root / PREGUNTAS).exists():
        return []
    hechas = []
    with bloqueo(root):
        preguntas = leer(root)
        for q in preguntas:
            if q["estado"] == "pendiente" and (
                not q.get("bloqueo_aplicado")
                or not q.get("aviso_intentado")
                or q.get("diagnostico_aviso") == "envío iniciado"
            ):
                completar_solicitud(root, motor, q, preguntas)
        pendientes = [
            (r.get("orden", 0), q, r) for q in preguntas if q["estado"] == "pendiente" for r in q.get("cola", [])
        ]
        for _, q, r in sorted(pendientes, key=lambda x: x[0]):
            if q["estado"] != "pendiente":
                continue
            if not asegurar_destino(root, motor, q):
                guardar(root / PREGUNTAS, preguntas)
                continue
            texto = r["texto"]
            insuficiente = texto.upper().startswith(("PENDIENTE:", "INSUFICIENTE:"))
            if insuficiente:
                q["motivo_insuficiente"] = texto.partition(":")[2].strip()
                detalle = f"{q['id']}: sigue bloqueada; falta: {q['motivo_insuficiente']}"
                cambios = {"status": "blocked", "pendiente_de": "humano"}
            else:
                detalle = f"{q['id']}: Decisión humana de {r['usuario']}: {texto}"
                otras = any(
                    p["id"] != q["id"] and p["tarea_id"] == q["tarea_id"] and p["estado"] == "pendiente"
                    for p in preguntas
                )
                cambios = {"status": "blocked", "pendiente_de": "humano"} if otras else {"status": "planned"}
            anotar(root, motor, q, detalle, cambios, preguntas)
            q["cola"].remove(r)
            if not insuficiente:
                q.update(estado="incorporada", respuesta=texto)
                hechas.append(q.copy())
            q.pop("respuesta_en_cola", None)
            guardar(root / PREGUNTAS, preguntas)
            mensaje = (
                detalle
                if insuficiente
                else f"Respuesta incorporada para tarea {q['tarea_id']}: {texto}"
                if cambios["status"] == "planned"
                else f"{q['id']} incorporada; tarea bloqueada por otra pregunta."
            )
            motor.avisar(root, "respuesta", mensaje)
    return hechas


def notificar_reanudacion(root, motor, iid):
    """Avisa una sola vez después de que el bucle haya ejecutado la tarea retomada."""
    if not (root / PREGUNTAS).exists():
        return
    with bloqueo(root):
        preguntas = leer(root)
        for q in preguntas:
            if q["tarea_id"] == iid and q["estado"] == "incorporada" and not q.get("reanudacion_avisada"):
                q["reanudacion_avisada"] = True
                guardar(root / PREGUNTAS, preguntas)
                motor.avisar(root, "respuesta", f"Tarea {iid} reanudada: {q['respuesta']}")


def restaurar(root, motor, iid):
    """Restaura WIP sobre destino limpio; devuelve False si debe esperar trabajo ajeno."""
    if not (root / PREGUNTAS).exists():
        return
    with bloqueo(root):
        preguntas = leer(root)
        for q in preguntas:
            if q["tarea_id"] != iid or q["estado"] != "incorporada" or not q["wip_rama"] or q["wip_restaurado"]:
                continue
            sucio = bool(git(root, "status", "--porcelain"))
            if sucio:
                q["impedimento_incorporacion"] = "WIP pendiente: hay trabajo local en índice o árbol; no se restaura."
            if sucio or not asegurar_destino(root, motor, q):
                guardar(root / PREGUNTAS, preguntas)
                return False
            parche = git(
                root,
                "diff",
                "--binary",
                q["base_commit"],
                q["wip_rama"],
                "--",
                ".",
                ":!docs/plan",
                ":!docs/review/versions",
                binario=True,
            )
            if parche:
                git(root, "apply", "--3way", "-", entrada=parche)
            q["wip_restaurado"] = True
            guardar(root / PREGUNTAS, preguntas)


DESTINOS_HALLAZGO = {"artemisa", "especificador", "humano"}


def destino_hallazgo(texto):
    """Extrae el último destino explícito, admitiendo etiquetas Markdown."""
    coincidencias = re.findall(
        r"(?<!\w)[*`_]*destino[*`_ ]*(?::|=|\|)\s*[*`_ ]*(artemisa|especificador|humano)\b",
        texto or "",
        re.IGNORECASE,
    )
    return coincidencias[-1].lower() if coincidencias else ""


def anotar_hallazgo(root, motor, iid, destino, contexto):
    """Conserva la decisión de Hades en la tarea y en la revisión de su versión."""
    tarea = motor.fichero_de(root, iid)
    informe = revision(root, motor, iid)
    cambios = (
        {"status": "planned"}
        if destino == "artemisa"
        else {
            "status": "blocked",
            "pendiente_de": "especificador",
        }
    )
    cabecera, cuerpo = motor.reescribir_frontmatter(tarea.read_text(encoding="utf-8"), cambios)
    if destino == "artemisa":
        cabecera = "\n".join(linea for linea in cabecera.splitlines() if not linea.startswith("pendiente_de:"))
    texto = (
        f"## Hallazgo de Hades enrutado\n"
        f"- Destino: `{destino}`\n"
        f"- Decisión: {'reanudar desarrollo' if destino == 'artemisa' else 'ejecutar especificar'}\n"
        f"- Evidencia: {contexto.strip() or 'destino declarado por Hades'}\n"
    )
    if texto not in cuerpo:
        cuerpo = cuerpo.rstrip("\n") + "\n\n" + texto
    informe.parent.mkdir(parents=True, exist_ok=True)
    previo = informe.read_text(encoding="utf-8") if informe.exists() else ""
    bloque = f"\n## {iid} · Hallazgo de Hades\n{texto}"
    contenidos = {
        tarea: cabecera + "\n---\n" + cuerpo.rstrip("\n") + "\n",
        informe: previo if texto in previo else previo.rstrip("\n") + bloque,
    }
    for ruta, contenido in contenidos.items():
        ruta.write_text(contenido, encoding="utf-8")


def enrutar_hallazgo(root, motor, iid, destino, contexto="", base_commit=None):
    """Aplica el destino de Hades; solo `humano` abre una pregunta persistente."""
    destino = (destino or "").strip().lower()
    if destino not in DESTINOS_HALLAZGO:
        raise ValueError(f"Destino de hallazgo inválido: {destino or '(vacío)'}")
    if destino == "humano":
        return solicitar(
            root,
            motor,
            iid,
            f"Resuelve el impedimento de {iid}: {contexto}",
            contexto=contexto,
            base_commit=base_commit,
        )
    anotar_hallazgo(root, motor, iid, destino, contexto)
    return None


def detectar_bloqueo(root, motor, iid, base_commit, salida=""):
    """Convierte solo bloqueos realmente humanos en preguntas y conserva los destinos de Hades."""
    tarea = motor.fichero_de(root, iid) if iid else None
    if not tarea:
        return
    fm = motor.frontmatter(tarea)
    if fm.get("status") != "blocked" or fm.get("pendiente_de") != "humano":
        return
    if any(q["tarea_id"] == iid for q in listar(root, True)):
        return
    seccion = tarea.read_text(encoding="utf-8").rsplit("\n## ", 1)[-1]
    destino = destino_hallazgo(salida) or destino_hallazgo(seccion)
    contexto = (seccion + "\n" + (salida or ""))[-4000:]
    enrutar_hallazgo(root, motor, iid, destino or "humano", contexto=contexto, base_commit=base_commit)
