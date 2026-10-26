---
name: telegram-gateway
description: Gateway de Telegram de Adevv. Atiende a los usuarios autorizados mientras el bucle trabaja: /estado resume el bucle y el backlog; /tarea y /bug registran entradas sin versión; /nuevo reinicia el hilo. Cualquier otro mensaje mantiene conversación interactiva en texto libre con el asistente del proyecto conservando el hilo de sesión. Los avisos de eventos del bucle (fin de versión, cuota, paradas) los envía orquestar.py con la misma configuración.
---

# Skill: Telegram Gateway (/telegram-gateway)

Canal de entrada por Telegram para un proyecto que corre con `/orquestar`. Los avisos de salida (fin de versión, falta de cuota, paradas que necesitan respuesta, errores) no son del gateway: los envía el bucle (ver «Avisos por Telegram» en `/orquestar`).

## 🔐 Configuración (fichero `.env` en la raíz o variables de entorno)
- Fichero `.env` en la raíz (recomendado para aislar el bot de cada proyecto; excluido de git por defecto).
- `TELEGRAM_BOT_TOKEN`: token del bot (de `@BotFather`). Nunca commitear en git.
- El `.env` del proyecto tiene precedencia independiente para cada variable; si falta o está vacía, se usa la variable del entorno de ejecución. Un token definido en el entorno sirve como respaldo para los avisos salientes del bucle. Por seguridad, el gateway solo escucha cuando el token efectivo está definido en el `.env` del proyecto; con token ambiental, `adevv telegram`, `adevv telegram --fondo` y el arranque gestionado se rechazan antes de reservar el PID o crear procesos. La entrada muestra: `token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto`. Los IDs pueden proceder del `.env` o del entorno independientemente del token.
- `TELEGRAM_ALLOWED_USER_IDS`: IDs numéricos de Telegram autorizados, separados por comas. Solo ellos reciben respuesta, y son también los destinatarios de los avisos del bucle. Los mensajes de cualquier otro usuario se ignoran sin tocar nada.
- Modelo conversacional: configurable en `orchestration.json` bajo la clave `"telegram"` (`harness`, `model`, `effort`). Si no se define, hereda por defecto la configuración de `"atenea"`.

## 📋 Comandos y Conversación Libre
- `/estado` o `/status`: resumen conciso del bucle, fase, versión y backlog; los agentes y porcentajes se consultan con `/agentes`.
- `/agentes` o `/agents`: roles declarados, variantes por dificultad, reservas y perfiles del paso actual, incluso en FIN/PARAR. Cada modelo muestra el porcentaje consumido: agotamiento vigente al 100%, cuota primaria nativa reciente de Codex o estimación de tokens locales en 5 h frente a `cuota_tokens_5h` o referencias por familia. Incluye reinicio si aplica; ver `/orquestar`, «Estado y agentes», para fuentes y límites. Equivale a `adevv orquestar --agentes` / `--agents` y no arranca ni modifica el bucle.
- `/lanzar` o `/run`: solicita el arranque en segundo plano en el proyecto del gateway y anuncia el siguiente paso previsto. Si existe `orquestar.pid`, informa de que ya está en marcha. El hijo usa la configuración habitual del proyecto y escribe en `orquestar.log`; la confirmación indica que el proceso fue lanzado, cuyo inicio puede detenerse por las validaciones normales del motor. Consulta `/estado` para seguirlo.
- `/parar` o `/stop`: si existe `orquestar.pid`, solicita la parada al acabar el paso en curso mediante `orquestar.parar`. Si no existe, informa de que ya está parado. No interrumpe el paso actual.
- `/cerrar vX.Y`: muestra la revisión (tareas, bloqueos y validaciones) y pide `/cerrar vX.Y confirmo`. La orden literal confirmada autoriza el cierre no interactivo: exige release exacta, revisión final, todos sus ítems completed/cancelled, sin PID ni parada manual ni decisiones de producto pendientes, árbol limpio, manifiestos alineados, changelog y preflight correcto. Publica main y etiqueta anotada con un push atómico, sin sobrescribir etiquetas. Si falla antes de publicar conserva el repositorio original y explica el motivo. Tras éxito elimina release y solicita el bucle en segundo plano si quedan versiones pendientes; en caso contrario informa FIN. Si falla el arranque conserva la versión publicada y propone `/lanzar`. CI y smoke tests posteriores quedan para la revisión humana.

Cada comando de preflight dispone de 600 segundos por defecto. `task_config.yaml::release.preflight_timeout` permite fijar otro límite positivo y finito, en segundos. Git conserva un límite independiente de 120 segundos por operación. Un timeout rechaza el cierre y se comunica con su motivo.
- `/metricas [filtro]` o `/metrics [filtro]`: resumen por tarea de versión, minutos reales, tokens de desarrollo y Hades (`E/C/S`: entrada/caché leída/salida) y coste aproximado USD. Por defecto consulta `ultima`; acepta los mismos filtros de `adevv orquestar --metricas`: `todas`/`all`, `ultima`/`last`, `ultimas:N`/`last:N` y listas como `v0.3,v0.4`. Reutiliza su cálculo y tarifas ilustrativas (no precios vigentes); el tiempo real incluye las revisiones una sola vez y razonamiento no vuelve a sumarse a salida. Sin datos lo indica; filtros inválidos o JSONL corrupto devuelven explicación sin resultados parciales. Es una consulta local que no modifica el bucle, incluso si está activo.
- `/tarea <título>` (o `/task`) y `/bug <título>`: nueva tarea o bug maestro **sin versión** (`status: backlog`, como la deuda registrada). El bucle no lo trabaja hasta que le pones versión (o, si es un bug, hasta que `revisar-deuda` lo incluya). Las tareas van sin `depende_de`: se calculan cuando entran en una versión.
- `/nuevo` o `/reset`: elimina la sesión guardada del usuario emisor y reinicia el hilo de conversación.
- `/ayuda` (o `/help`, `/start`): lista de comandos disponibles.
- **Conversación libre**: cualquier mensaje enviado por un usuario autorizado que no comience por un comando fijo mantiene una conversación interactiva en texto libre con el asistente del proyecto. El hilo de la conversación se persiste automáticamente en `orquestar_telegram.json` (excluido de git) por usuario y arnés. Si la reanudación de una sesión previa falla, conmuta automáticamente a una sesión nueva sin interrumpir la experiencia.
- **Contexto seguro con el bucle en marcha**: si existe `orquestar.pid`, el asistente es instruido para no modificar ni commitear archivos rastreados del repositorio, limitándose a responder consultas, analizar el proyecto o sugerir registrar tareas o bugs mediante el buzón.
- **Firma de versión al pie**: todas las respuestas a comandos (`/estado`, `/agentes`, `/metricas`, `/tarea`, `/bug`, `/lanzar`, `/parar`, `/nuevo`, `/ayuda`) y respuestas de error añaden al pie la firma de versión de Adevv del proceso (`— Adevv vX.Y.Z`). En conversación libre, añade además el arnés y modelo que respondió (`— Adevv vX.Y.Z · <harness>/<model>`). Si el mensaje ya incluye la firma final, no se duplica al enviarse.

**Nunca escribe en el backlog con el bucle en marcha.** Deja la petición en el buzón (`orquestar_buzon.jsonl`, excluido de git) y el bucle la registra entre pasos, con un commit que solo lleva esos ficheros, y te avisa del ID. Sin bucle, la registra y la commitea en el momento, en la rama actual.

La conversación prueba primero el titular y después las reservas de `telegram.reserva` (objeto o lista ordenada), que heredan los campos no redefinidos (`harness`, `model`, `effort`). Sin reserva propia, conserva las heredadas de Atenea. Salta sin ejecutar cualquier modelo con cuota vigente registrada, incluso si es el único. Si detecta cuota durante la ejecución, falta el ejecutable o falla el arranque, pasa inmediatamente a la siguiente reserva; los errores ordinarios conservan el reintento sin sesión y su tratamiento de error, sin conmutar.

Cada intento reanuda exclusivamente la sesión del mismo usuario y arnés, también en reservas; sin sesión propia inicia una nueva. Guarda la sesión del respondedor sin reemplazar las de otros arneses. Cada mensaje reconsidera al titular, que vuelve a tener prioridad cuando vence su cuota. La firma identifica `harness/model` y añade `reserva` cuando corresponde. Si todos están indisponibles, devuelve un diagnóstico firmado por configuración, con cuota y recuperación (ISO UTC), ausencia o fallo de arranque, sin esperar.

Los agotamientos detectados se registran en las métricas compartidas, con su recuperación exacta, para `/agentes` y el bucle. Cada ejecutable ausente conserva warning, métrica de consumo cero y aviso filtrable `arnes`; las ausencias y fallos de arranque no generan cuota. Si no queda ninguna configuración disponible, se solicita también el aviso `error`.

## 🛠️ Uso
Desde la raíz del proyecto:
```bash
adevv telegram            # escucha (long polling) hasta Ctrl+C
adevv telegram --fondo    # escucha en segundo plano, sin ventana adicional
adevv telegram --parar    # pide parar el gateway al acabar la operación actual
adevv telegram --estado   # imprime lo que respondería /estado
```

`--fondo` reserva `telegram.pid`, evita duplicar un proceso vivo y recupera marcas obsoletas. La salida se añade a `telegram.log`. `--parar` funciona sin credenciales y crea `telegram.parar`; el gateway limpia PID y señal al salir, incluso si falla. Estos tres archivos quedan excluidos de git. La parada espera al polling actual (hasta unos 35 segundos) o a la conversación en curso. El comando Telegram `/parar` controla el bucle; la CLI `adevv telegram --parar` controla el gateway.

Desde v0.5, un gateway ejecutado desde `~/.adevv/versions/` (o `$ADEVV_HOME/versions/`) detecta los cambios de `active.json` antes del siguiente polling. Tras completar el lote en curso, transfiere `telegram.pid` al motor de la versión activa y escribe `[gateway] recargado a versión X.Y.Z`. Conserva argumentos, raíz, sesiones y offset de Telegram para no repetir mensajes ya atendidos. Las señales de parada tienen prioridad; un puntero inválido, motor ausente o fallo de lanzamiento mantiene el gateway actual. Los árboles de desarrollo no se recargan. La instalación conserva intactos los archivos en uso; gateways anteriores a v0.5 requieren reinicio manual.

Al ejecutar `adevv orquestar` en primer o segundo plano se solicita automáticamente `--fondo` si `telegram(root)` tiene credenciales y Telegram está habilitado. Un gateway vivo se conserva; un fallo de arranque deja un aviso sin abortar el bucle. `"telegram": false` en `orchestration.json` desactiva este autoarranque y los avisos. Las consultas de estado, métricas, verificaciones y revisiones no lo activan. El gateway permanece escuchando cuando acaba o se para el bucle; usa `adevv telegram --parar` para detenerlo.

Si el token procede del entorno porque el proyecto no define uno en su `.env`, los avisos salientes siguen usando ese respaldo, pero el autoarranque del gateway se omite. El bucle muestra una sola vez por ejecución: `token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto`. Para habilitar la conversación entrante, define el token del bot en el `.env` del proyecto.
