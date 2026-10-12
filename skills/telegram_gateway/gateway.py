"""Gateway de Telegram para nereoskills.

Proporciona integración desacoplada para la recepción de comandos remotos
(/tarea, /bug, /estado, /status) y emisión de notificaciones salientes del orquestador.
Soporta modo importación, escucha continua (long polling) e interfaz CLI.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def is_authorized(user_id: str, allowed_ids: set[str] | list[str]) -> bool:
    """Valida si un identificador de usuario pertenece a la lista blanca autorizada."""
    normalized_allowed = {str(item).strip() for item in allowed_ids if str(item).strip()}
    return str(user_id).strip() in normalized_allowed


def get_project_prefix(root: Path) -> str:
    """Obtiene el prefijo del proyecto desde task_config.yaml o devuelve 'WKF' por defecto."""
    config_file = root / "task_config.yaml"
    if config_file.exists():
        try:
            content = config_file.read_text(encoding="utf-8")
            match = re.search(r'prefix:\s*["\']?([^"\'\s\n]+)', content)
            if match:
                prefix = match.group(1).strip()
                if prefix:
                    return prefix
        except Exception:
            pass
    return "WKF"


def get_active_version(root: Path) -> str:
    """Devuelve la versión activa del proyecto según task_config.yaml o la rama git activa."""
    config_file = root / "task_config.yaml"
    if config_file.exists():
        try:
            content = config_file.read_text(encoding="utf-8")
            match = re.search(r'version:\s*["\']?([^"\'\s\n]+)', content)
            if match:
                version_raw = match.group(1).strip()
                if version_raw:
                    return version_raw if version_raw.startswith("v") else f"v{version_raw}"
        except Exception:
            pass

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip()
        match_rel = re.match(r"^release/v?(\d+\.\d+)", branch)
        if match_rel:
            return f"v{match_rel.group(1)}.0"
        match_hot = re.match(r"^hotfix/v?(\d+\.\d+\.\d+)", branch)
        if match_hot:
            return f"v{match_hot.group(1)}"
    except Exception:
        pass

    return ""


def get_next_id(directory_or_root: Path, prefix: str) -> str:
    """Calcula el siguiente ID autoincremental explorando directorios relevantes de backlog."""
    highest_index = 0
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)")

    search_paths = []
    if (directory_or_root / "docs/plan").exists():
        search_paths.append(directory_or_root / "docs/plan")
    elif directory_or_root.is_dir():
        search_paths.append(directory_or_root)
        if directory_or_root.parent.is_dir():
            search_paths.append(directory_or_root.parent)

    for base in search_paths:
        for file_path in base.glob("**/*.md"):
            match = pattern.match(file_path.name)
            if match:
                highest_index = max(highest_index, int(match.group(1)))

    return f"{prefix}-{highest_index + 1:04d}"


def _slugify(text: str) -> str:
    """Genera un slug limpio en minúsculas y sin caracteres diacríticos, acotado en longitud."""
    normalized = unicodedata.normalize("NFKD", text)
    without_diacritics = "".join(char for char in normalized if not unicodedata.combining(char))
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", without_diacritics).lower()
    slug = re.sub(r"[\s_]+", "-", cleaned).strip("-")
    return slug[:60].strip("-")


def create_task(root: Path, title: str, version: str = "") -> tuple[str, Path]:
    """Registra una nueva tarea siguiendo estrictamente el estándar Issue-as-Code v3.0."""
    tasks_dir = root / "docs/plan/tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"T-{get_project_prefix(root)}"
    task_id = get_next_id(root, prefix)

    clean_title = title.strip().splitlines()[0] if title.strip() else "Tarea sin título"
    slug = _slugify(clean_title)
    filename = f"{task_id}-{slug}.md" if slug else f"{task_id}.md"
    file_path = tasks_dir / filename

    status = "planned" if version else "backlog"
    version_val = f'"{version}"' if version else '""'
    escaped_title = json.dumps(clean_title, ensure_ascii=False)
    today = datetime.now().strftime("%Y-%m-%d")

    content = (
        f"---\n"
        f"id: {task_id}\n"
        f"title: {escaped_title}\n"
        f"type: funcional\n"
        f"weight: 10\n"
        f"version: {version_val}\n"
        f"status: {status}\n"
        f"depende_de: []\n"
        f"created_at: {today}\n"
        f"updated_at: {today}\n"
        f"---\n\n"
        f"# {task_id}: {clean_title}\n\n"
        f"## 🎯 Objetivo de Negocio\n"
        f"{clean_title}\n\n"
        f"## 📋 Criterios de Aceptación (Nivel Máster)\n"
        f"- [ ] **CA-M-1:** Especificación pendiente de desglose.\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return task_id, file_path


def create_bug(root: Path, title: str, version: str = "") -> tuple[str, Path]:
    """Registra un nuevo bug siguiendo estrictamente el estándar Issue-as-Code v3.0."""
    bugs_dir = root / "docs/plan/bugs"
    bugs_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"B-{get_project_prefix(root)}"
    bug_id = get_next_id(root, prefix)

    clean_title = title.strip().splitlines()[0] if title.strip() else "Bug sin título"
    slug = _slugify(clean_title)
    filename = f"{bug_id}-{slug}.md" if slug else f"{bug_id}.md"
    file_path = bugs_dir / filename

    status = "planned" if version else "backlog"
    version_val = f'"{version}"' if version else '""'
    escaped_title = json.dumps(clean_title, ensure_ascii=False)
    today = datetime.now().strftime("%Y-%m-%d")

    content = (
        f"---\n"
        f"id: {bug_id}\n"
        f"title: {escaped_title}\n"
        f"type: bug\n"
        f"weight: 100\n"
        f"version: {version_val}\n"
        f"status: {status}\n"
        f"created_at: {today}\n"
        f"updated_at: {today}\n"
        f"---\n\n"
        f"# {bug_id}: {clean_title}\n\n"
        f"## 🎯 Descripción del Fallo\n"
        f"{clean_title}\n\n"
        f"## 📋 Reproducir\n"
        f"1. Detallar pasos de reproducción.\n\n"
        f"## 📋 Evidencias\n"
        f"- N/A\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return bug_id, file_path


def _parse_frontmatter(content: str) -> dict[str, str]:
    """Extrae metadatos básicos del frontmatter YAML de un archivo markdown."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    try:
        import yaml
        loaded = yaml.safe_load(match.group(1))
        if isinstance(loaded, dict):
            return {k: (v if isinstance(v, list) else "" if v is None else str(v)) for k, v in loaded.items()}
    except Exception:
        pass

    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            raw_val = val.strip()
            if raw_val.startswith('"') and raw_val.endswith('"'):
                try:
                    data[key.strip()] = json.loads(raw_val)
                    continue
                except Exception:
                    pass
            data[key.strip()] = raw_val.strip("\"'")
    return data


def get_status_summary(root: Path) -> str:
    """Genera el resumen estructurado del estado del backlog en formato Markdown."""
    version_label = get_active_version(root) or "Ninguna"
    tasks_dir = root / "docs/plan/tasks"

    in_progress_label: str | None = None
    pending_items: list[tuple[str, str]] = []

    if tasks_dir.exists():
        for file_path in sorted(tasks_dir.glob("*.md")):
            frontmatter = _parse_frontmatter(file_path.read_text(encoding="utf-8"))
            task_id = frontmatter.get("id") or file_path.stem.split("-")[0]
            title = frontmatter.get("title") or file_path.stem
            status = frontmatter.get("status", "backlog")

            if status == "in_progress" and in_progress_label is None:
                in_progress_label = f"`{task_id}` - {title}"
            elif status in ("backlog", "planned"):
                pending_items.append((task_id, title))

    en_curso = in_progress_label if in_progress_label else "Ninguna"
    output_lines = [
        f"*Versión activa:* `{version_label}`",
        f"*En curso:* {en_curso}",
        f"*Pendientes ({len(pending_items)}):*",
    ]
    for tid, title in pending_items:
        output_lines.append(f"- `{tid}`: {title}")

    return "\n".join(output_lines)


def handle_message(user_id: str, text: str, root: Path, allowed_ids: set[str] | list[str]) -> str | None:
    """Procesa un comando entrante de Telegram respetando la lista blanca de seguridad."""
    if not is_authorized(user_id, allowed_ids):
        return None

    stripped_text = text.strip()
    if not stripped_text:
        return None

    parts = stripped_text.split(maxsplit=1)
    command = parts[0].lower()
    argument = parts[1].strip() if len(parts) > 1 else ""

    if command in ("/tarea", "/task"):
        if not argument:
            return "Uso: /tarea <título descriptivo de la tarea>"
        active_version = get_active_version(root)
        task_id, _ = create_task(root, argument, active_version)
        return f"Tarea registrada: {task_id} - {argument}"

    if command == "/bug":
        if not argument:
            return "Uso: /bug <descripción del error detectado>"
        active_version = get_active_version(root)
        bug_id, _ = create_bug(root, argument, active_version)
        return f"Bug registrado: {bug_id} - {argument}"

    if command in ("/estado", "/status"):
        return get_status_summary(root)

    return None


def _default_http_post(token: str, chat_id: str, message: str, parse_mode: str | None = None) -> bool:
    """Realiza la petición HTTP POST a la API de Telegram con reintento en texto plano si falla Markdown."""
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    def _send(mode: str | None) -> bool:
        payload_data: dict[str, str] = {"chat_id": str(chat_id), "text": message}
        if mode:
            payload_data["parse_mode"] = mode
        payload = json.dumps(payload_data).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200

    try:
        return _send(parse_mode)
    except urllib.error.HTTPError as err:
        if parse_mode and err.code == 400:
            logger.warning("Fallo al enviar con parse_mode=%s (código 400). Reintentando en texto plano...", parse_mode)
            try:
                return _send(None)
            except Exception as retry_err:
                logger.warning("Fallo al enviar mensaje a Telegram (reintento plano): %s", retry_err)
                return False
        logger.warning("Error HTTP al enviar mensaje a Telegram (%s): %s", err.code, err)
        return False
    except Exception as exc:
        logger.warning("Excepción al enviar mensaje a Telegram: %s", exc)
        return False


def notify(text: str, chat_ids: list[str] | None = None, token: str | None = None, http_client=None) -> bool:
    """Envía una notificación saliente a los chats configurados sin propagar excepciones."""
    effective_token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if chat_ids is None:
        raw_env_ids = os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "")
        chat_ids = [item.strip() for item in raw_env_ids.split(",") if item.strip()]

    client = http_client or _default_http_post
    formatted_message = f"📢 {text}"

    try:
        success = True
        for chat_id in chat_ids:
            response = client(effective_token, str(chat_id).strip(), formatted_message)
            if not response:
                success = False

        if not success:
            logger.warning("Fallo al enviar notificación a Telegram: %s", text)
            return False

        return True
    except Exception:
        logger.warning("Fallo al enviar notificación a Telegram: %s", text)
        return False


def get_updates(token: str, offset: int | None = None, timeout: int = 20) -> list[dict]:
    """Obtiene actualizaciones pendientes de Telegram mediante long polling."""
    if not token:
        return []
    url = f"https://api.telegram.org/bot{token}/getUpdates?timeout={timeout}"
    if offset is not None:
        url += f"&offset={offset}"
    try:
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, timeout=timeout + 5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("ok"):
                    return data.get("result", [])
    except Exception as exc:
        logger.warning("Error al consultar getUpdates en Telegram: %s", exc)
    return []


def run_polling(root: Path, token: str, allowed_ids: set[str], timeout: int = 20, max_iterations: int | None = None) -> None:
    """Bucle continuo de long-polling para recibir mensajes y responder a comandos autorizados con tolerancia a fallos."""
    offset: int | None = None
    iterations = 0

    logger.info("Iniciando servicio de polling del Gateway de Telegram...")
    while max_iterations is None or iterations < max_iterations:
        iterations += 1
        try:
            updates = get_updates(token, offset=offset, timeout=timeout)
        except Exception as poll_err:
            logger.warning("Error imprevisto en ciclo de polling: %s", poll_err)
            updates = []

        for update in updates:
            offset = update["update_id"] + 1
            try:
                message = update.get("message") or update.get("channel_post")
                if not message:
                    continue

                user_id = str(message.get("from", {}).get("id", ""))
                chat_id = str(message.get("chat", {}).get("id", ""))
                text = message.get("text", "")

                response = handle_message(user_id, text, root, allowed_ids)
                if response and chat_id:
                    sent = _default_http_post(token, chat_id, response, parse_mode="Markdown")
                    if not sent:
                        logger.warning("No se pudo entregar respuesta al chat %s para update %s", chat_id, update.get("update_id"))
            except Exception as msg_err:
                logger.error("Error al procesar actualización %s: %s", update.get("update_id"), msg_err, exc_info=True)

        if not updates and max_iterations is None:
            time.sleep(1)


def main() -> int:
    """Punto de entrada CLI del Gateway de Telegram."""
    parser = argparse.ArgumentParser(description="Gateway de Telegram para nereoskills")
    parser.add_argument("--poll", action="store_true", help="Inicia el bucle de long-polling")
    parser.add_argument("--status", action="store_true", help="Imprime el resumen actual del backlog")
    parser.add_argument("--notify", metavar="TEXTO", help="Envía una notificación saliente a los chats autorizados")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Directorio raíz del proyecto")

    args = parser.parse_args()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    allowed_ids = {item.strip() for item in os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if item.strip()}

    if args.status:
        print(get_status_summary(args.root))
        return 0

    if args.notify:
        ok = notify(args.notify, token=token)
        return 0 if ok else 1

    if args.poll:
        if not token:
            print("Error: Se requiere TELEGRAM_BOT_TOKEN para iniciar el modo polling.")
            return 1
        try:
            run_polling(args.root, token, allowed_ids)
        except KeyboardInterrupt:
            print("\nPolling detenido por el usuario.")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
