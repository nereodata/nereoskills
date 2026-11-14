---
id: B-ADV-0049
title: "La conversación de Telegram no puede consultar ficheros sobre el avance de las tareas"
type: bug
weight: 100
dificultad: dificil
version: "v1.2.0"
status: completed
depende_de: []
created_at: 2026-11-12
updated_at: 2026-11-14
---

# B-ADV-0049 · La conversación de Telegram no puede consultar ficheros sobre el avance de las tareas

## Descripción del fallo

Desde hace algunas versiones, la conversación libre del gateway de Telegram no consigue informar del avance de las tareas. El comando `/estado` sí responde, pero al preguntar en lenguaje natural el asistente contesta que no puede ejecutar comandos y no consulta los datos del proyecto.

**Comportamiento esperado:** la conversación debe poder leer ficheros del proyecto para responder con información actual sobre tareas, revisiones, bloqueos y avance del bucle. Su capacidad debe limitarse a la lectura de ficheros: no debe modificar, crear ni borrar archivos, ejecutar acciones sobre el proyecto ni controlar procesos.

**Causa raíz:** combinación de cuatro defectos en `skills/telegram_gateway/gateway.py`:
1. `invocar()` reutilizaba `motor.base_comando_agente()`, concediendo permisos amplios de agente (`--dangerously-skip-permissions` en `claude`/`agy`, `--sandbox workspace-write` en `codex`) en vez de un contrato estricto de solo lectura de ficheros.
2. `invocar()` no limpiaba `CODEX_WINDOWS_REGISTERED_CORE` del entorno heredado en Windows (corregido en `orquestar.agente()` en `B-ADV-0045`, pero omitido en el gateway), por lo que las herramientas de `codex` fallaban con `registered Core launch requires an installed app` y el asistente contestaba que no podía ejecutar comandos sin leer el repositorio.
3. Las skills globales de Adevv instruían ejecutar `adevv orquestar --estado` por consola y `construir_prompt()` no desactivaba skills ni indicaba leer directamente `docs/plan/`, `docs/review/`, `task_config.yaml`, `orquestar.log` u `orquestar_preguntas.json` ni releerlos desde disco al reanudar sesión.
4. `invocar()` enviaba el prompt duplicado por `stdin` y `-p` en `agy`, y no clasificaba `acceso_suscripcion_denegado` de Claude ni salidas vacías/arneses no soportados como `ModeloIndisponible` para conmutar a reservas o comunicar indisponibilidad real.

## Reproducir

1. Con el gateway de Telegram conectado a un proyecto con tareas y evidencias de avance, consultar `/estado` y comprobar que responde.
2. Enviar un mensaje de conversación libre, por ejemplo: «¿Cómo va la tarea actual y qué queda pendiente?».
3. Observar que la respuesta declara que no puede ejecutar comandos en lugar de leer los ficheros pertinentes y explicar el avance.

## Criterios de aceptación

- [x] La conversación libre consulta los ficheros pertinentes del proyecto y responde sobre el avance real, identificando los ficheros que sustentan su respuesta.
- [x] Una consulta posterior refleja cambios en esos ficheros sin limitarse a repetir el contexto anterior del chat.
- [x] La lectura funciona con los arneses y reservas autorizados para la conversación; una indisponibilidad real se comunica sin inventar datos.
- [x] Los permisos efectivos permiten únicamente consultar ficheros del proyecto. Las peticiones de escribir, borrar, ejecutar acciones o controlar procesos se rechazan sin efectos, aunque lleguen en lenguaje natural o dentro del contenido leído.
- [x] `/estado` conserva su funcionamiento. La corrección se limita a los permisos de la conversación libre y no redefine los comandos explícitos del gateway.
- [x] Se verifica el recorrido de conversación con lectura permitida y acciones denegadas, sin enviar mensajes reales de Telegram desde las pruebas.

## Evidencias

- Incidencia comunicada por el usuario el 2026-11-12: `/estado` responde, pero la conversación dice que no puede ejecutar comandos al consultar el avance.
- Requisito explícito del usuario: «no debería poder hacer acciones, pero leer ficheros, sí. Solo leer ficheros».
- Punto de entrada para investigar: `skills/telegram_gateway/gateway.py`, conversación libre y selección del arnés correspondiente.
- Pendiente de reproducir técnicamente; no se adjunta una transcripción de Telegram.

## Resolución

- **Aislamiento de solo lectura por arnés (`skills/telegram_gateway/lector_proyecto.py`)**:
  - `claude`: invocación con `-p --restricted --permission-mode dontAsk --permission-prompts none --tools Read,Glob,Grep --allowedTools Read,Glob,Grep --disallowedTools Bash,Write,Edit,NotebookEdit,WebFetch,WebSearch --disable-slash-commands --strict-mcp-config --system-prompt-snapshot off` y política `--settings` que bloquea escrituras, comandos, red y `.env*`/`.git/**`.
  - `codex`: invocación con `--sandbox read-only` (o `-c sandbox_mode="read-only"` al reanudar con `resume`), `--ignore-user-config`, `--ignore-rules`, desactivación de `hooks`, `shell_tool`, `unified_exec`, `apps`, `plugins`, `multi_agent` y `skip_host_skill_discovery`, neutralización de cualquier otro `mcp_servers` local y servidor MCP stdio propio (`lector_proyecto.py`) que expone únicamente `listar_ficheros`, `leer_fichero` (incluyendo cola por `desde_linea` negativa y tolerancia a opcionales `null`) y `buscar_texto` confinados a la raíz del proyecto sin enlaces simbólicos/junctions ni acceso a `.env*`/`.git`.
  - `agy`: invocación con `--sandbox --disable-slash-commands --settings` permitiendo solo `read_file` dentro del proyecto y denegando `write_file(*)`, `command(*)`, `unsandboxed(*)`, `read_url(*)`, `execute_url(*)`, `mcp(*)` y lectura de `.env*`/`.git/**`, apoyada en un índice fresco y priorizado de ficheros legibles construido desde disco e inyectado en el prompt de cada turno (dado que `read_file` exige ruta de fichero regular y `agy` carece de listado nativo), sin duplicar el prompt por `stdin`.
- **Resiliencia e instrucciones del gateway (`skills/telegram_gateway/gateway.py`)**:
  - Limpieza de `CODEX_WINDOWS_REGISTERED_CORE` en el entorno hijo de `codex` en Windows.
  - Conmutación inmediata a reservas ante `acceso_suscripcion_denegado`, arnés no soportado o respuesta vacía del modelo, comunicando `GatewayNoDisponible` real sin inventar avance cuando caen todos los candidatos.
  - Prompt conversacional actualizado para exigir consulta directa en disco por turno, citación de rutas fuente y rechazo de acciones o inyecciones embebidas en ficheros leídos, preservando intactos `/estado`, el resto de comandos explícitos y `motor.base_comando_agente` de los roles internos.
- **Verificación**: Nuevas pruebas en `tests/test_conversacion_telegram_lectura.py` junto a la batería del gateway y limpieza de instrucciones/empaquetado ejecutadas con `adevv orquestar --verificar` sin tráfico real a Telegram.
