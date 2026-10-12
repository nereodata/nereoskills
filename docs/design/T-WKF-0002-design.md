# Diseño Técnico: T-WKF-0002 - Integración de Gateway de Telegram

## 🏗️ Arquitectura
El gateway de Telegram para `nereoskills` actúa como un adaptador de comunicación desacoplado entre clientes externos (Telegram Bot API) y el sistema de gestión de tareas y orquestación local.

Se implementa como un módulo ligero en Python (`skills/telegram_gateway/gateway.py`) sin dependencias externas pesadas (usando la biblioteca estándar: `urllib.request`, `json`, `logging`, `os`, `pathlib`), que puede ser:
1. Importado directamente por el orquestador u otros scripts para emitir notificaciones salientes (`notify`).
2. Ejecutado como proceso daemon/polling para escuchar mensajes remotos (`handle_message`).
3. Invocado vía CLI para pruebas o integración manual.

## 🛠️ Cambios
- **[NEW]** `skills/telegram_gateway/gateway.py`: Implementación del gateway, manejador de comandos, utilidades de Issue-as-Code y cliente de notificación.
- **[NEW]** `skills/telegram_gateway/SKILL.md`: Documentación y definición formal de la skill.
- **[NEW]** `tests/test_telegram_gateway.py`: Suite de pruebas unitarias y de integración que verifica todos los escenarios de `tests/features/telegram_gateway.feature`.
- **[MODIFY]** `task_config.yaml`: No requiere cambios estructurales; se aprovechan las rutas `docs/plan/tasks/` y `docs/plan/bugs/`.

## 🎯 Mapa de impacto
- **Llamantes:** 
  - Orquestador (`skills/orquestar/orquestar.py`): Podrá importar opcionalmente `skills.telegram_gateway.gateway.notify` para enviar alertas de hitos o paradas sin acoplamiento duro.
- **Escenarios/tests afectados:** Ninguno. Es una funcionalidad nueva que no modifica interfaces existentes ni invalida pruebas previas (incluyendo `tests/test_orquestar.py`).
- **Decisiones contradichas:** Ninguna (`archivo:línea: ninguna`). Respeta estrictamente Issue-as-Code v3.0 (`skills/task-add/SKILL.md` y `skills/bug-add/SKILL.md`) en la asignación de `status: planned` con versión activa y `status: backlog` sin versión.
- **Sistema de referencia y fronteras:** 
  - Codificación UTF-8 en todas las lecturas y escrituras de archivos.
  - IDs de usuario y chat manejados como strings normalizados.
  - Formato Markdown para las respuestas enviadas al usuario.
- **Camino caliente:** No aplica (operaciones de I/O en red y ficheros locales activadas por mensajes discretos).

## 🧩 Patrones y Componentes
1. **Seguridad (Lista Blanca Estricta - CA-M-1):**
   - `is_authorized(user_id: str, allowed_ids: set[str]) -> bool`: Filtra de raíz cualquier ID que no coincida. Las peticiones no autorizadas se descartan silenciosamente sin responder ni tocar el disco.
2. **Ingesta de Backlog (Issue-as-Code v3.0 - CA-M-2):**
   - `get_active_version(root: Path) -> str`: Detecta la versión activa a partir de `task_config.yaml` o la rama activa `release/vX.Y`.
   - `get_next_id(directory: Path, prefix: str) -> str`: Autoincremento de ID escaneando archivos existentes (ej. `T-WKF-0003`, `B-WKF-0002`).
   - `create_task(root: Path, title: str, version: str) -> tuple[str, Path]`: Crea el `.md` con metadatos YAML conformes a la especificación.
   - `create_bug(root: Path, title: str, version: str) -> tuple[str, Path]`: Crea el `.md` de anomalía en `docs/plan/bugs/`.
3. **Consulta de Estado (CA-M-3):**
   - `get_status_summary(root: Path) -> str`: Analiza `docs/plan/tasks/`, identifica tareas `in_progress`, lista tareas pendientes (`backlog`, `planned`), excluye tareas cerradas (`completed`, `done`, `cancelled`), y genera la salida Markdown especificada.
4. **Notificaciones Salientes Resilientes (CA-M-4):**
   - `notify(text: str, chat_ids: list[str] | None = None, token: str | None = None, http_client=None) -> bool`:
     - Despacha `📢 {text}` a los destinatarios.
     - Captura `Exception` (timeouts, errores de red, respuestas HTTP no 200), registra un `WARNING` en el logger con `"Fallo al enviar notificación a Telegram: {text}"` y retorna `False` sin romper el flujo del llamante.
     - Retorna `True` si todas las entregas fueron exitosas.
5. **Servicio de Escucha y CLI:**
   - `run_polling(root: Path, token: str, allowed_ids: set[str], timeout: int = 20, max_iterations: int | None = None)`: Bucle de long-polling con `getUpdates` que despacha mensajes a `handle_message` y emite respuestas con `_default_http_post`.
   - `main()`: CLI con opciones `--poll`, `--status`, `--notify` y `--root`.

## 🧪 Testeabilidad
- Inyección de dependencias para el cliente HTTP: permite simular respuestas de la API de Telegram y fallos de red sin requerir credenciales reales ni conexión a Internet.
- Aislamiento de sistema de archivos: todas las funciones de backlog aceptan `root: Path` parametrizable para operar sobre `tempfile.TemporaryDirectory` en los tests unitarios.
