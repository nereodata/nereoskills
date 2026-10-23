# Diseño Técnico: T-ADV-0012 · Conversación libre con continuidad de hilo en el gateway de Telegram

## 1. Resumen y Contexto
El objetivo de **T-ADV-0012** es permitir que los usuarios autorizados de Telegram puedan no solo ejecutar comandos fijos (`/estado`, `/tarea`, `/bug`), sino también interactuar de forma conversacional y en texto libre con el modelo del proyecto, manteniendo la continuidad del hilo de conversación entre mensajes y pudiendo reiniciarlo mediante `/nuevo` o `/reset`. Además, el prompt contextualiza la interacción para evitar interferencias o modificaciones concurrentes sobre el repositorio mientras el bucle de `/orquestar` esté trabajando.

## 2. Decisiones de Arquitectura y Diseño

- **DEC-D01 (Configuración del modelo para Telegram):**
  - Se consulta `orchestration.json` a través de `motor.config(root)`.
  - Si existe la sección `"telegram"`, se utiliza su configuración (`harness`, `model`, `effort`).
  - En su defecto, se recurre a la configuración de `"atenea"` como asistente por defecto del proyecto (`harness` claude por defecto si no se especifica).

- **DEC-D02 (Persistencia de sesiones por usuario y arnés):**
  - Las sesiones activas se almacenan localmente en `root / motor.TELEGRAM_SESIONES` (`orquestar_telegram.json`).
  - Se añade `TELEGRAM_SESIONES` a la tupla `motor.PROPIOS` en `skills/orquestar/orquestar.py`, garantizando su exclusión automática de git vía `motor.excluir(root)`.
  - El formato del archivo es un JSON con clave por ID de usuario: `{"<usuario>": {"<harness>": "<session_id>"}}` (o mapeo directo por usuario/arnés), permitiendo mantener sesiones independientes por arnés y limpiarlas fácilmente por usuario.

- **DEC-D03 (Reanudación y fallback resiliente):**
  - Al recibir un mensaje que no es un comando fijo, `responder()` invoca la conversación.
  - Se recupera la sesión previa guardada para `(usuario, harness)`.
  - Si existe sesión previa, se invoca con `--resume` (o `--conversation` / `thread_id` según el arnés).
  - Si la reanudación falla (código de retorno distinto de 0 o excepción en el proceso del modelo), se captura el error y se reintenta automáticamente iniciando una sesión nueva (`sesion=None`).
  - Al completar la ejecución con éxito, se actualiza el ID de sesión del usuario en `orquestar_telegram.json` y se retorna el texto limpio de respuesta del modelo.

- **DEC-D04 (Comandos `/nuevo` / `/reset` y ayuda):**
  - Los comandos `/nuevo` y `/reset` eliminan la sesión registrada para el usuario emisor y retornan un mensaje confirmando que el hilo ha sido reiniciado (`"Hilo de conversación reiniciado."`).
  - El texto de `/ayuda`, `/help` y `/start` se amplía documentando `/nuevo` (o `/reset`) y explicando que cualquier mensaje sin comando conversa con el asistente del proyecto.

- **DEC-D05 (Contexto seguro con bucle en marcha):**
  - La función de construcción de prompt `construir_prompt(root, texto)` comprueba si existe `root / motor.PID` (`orquestar.pid`).
  - Si el bucle está en marcha, añade una advertencia explícita indicando que no debe modificar ni commitear ficheros rastreados del repositorio, limitándose a responder consultas, analizar el proyecto o indicar el uso de `/tarea` o `/bug` (`motor.apuntar`) si el usuario desea registrar trabajo.

## 3. Plan de Pruebas Unitarias (`tests/test_telegram_gateway.py`)
1. `test_free_conversation_invokes_model_and_saves_session`: Envío de texto libre por usuario autorizado invoca al modelo, devuelve su respuesta y persiste la sesión.
2. `test_conversation_reuses_existing_session`: Mensajes sucesivos del mismo usuario reanudan el `session_id` persistido.
3. `test_conversation_fallback_to_new_session_on_resume_failure`: Si la reanudación falla, se ejecuta una sesión nueva y se persiste el nuevo ID.
4. `test_nuevo_and_reset_clears_session_and_confirms`: `/nuevo` y `/reset` eliminan la sesión guardada y responden confirmación.
5. `test_prompt_includes_safety_notice_when_loop_is_running`: Con `orquestar.pid` presente, el prompt incluye las restricciones de seguridad.
6. `test_help_documents_nuevo_and_free_conversation`: `/ayuda` documenta `/nuevo` y la conversación libre.
