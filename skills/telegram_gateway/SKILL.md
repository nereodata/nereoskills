---
name: telegram-gateway
description: Gateway de Telegram de Adevv. Atiende a los usuarios autorizados mientras el bucle trabaja: /estado resume el bucle y el backlog; /tarea y /bug registran entradas sin versión; /nuevo reinicia el hilo. Cualquier otro mensaje mantiene conversación interactiva en texto libre con el asistente del proyecto conservando el hilo de sesión. Los avisos de eventos del bucle (fin de versión, cuota, paradas) los envía orquestar.py con la misma configuración.
---

# Skill: Telegram Gateway (/telegram-gateway)

Canal de entrada por Telegram para un proyecto que corre con `/orquestar`. Los avisos de salida (fin de versión, falta de cuota, paradas que necesitan respuesta, errores) no son del gateway: los envía el bucle (ver «Avisos por Telegram» en `/orquestar`).

## 🔐 Configuración (fichero `.env` en la raíz o variables de entorno)
- Fichero `.env` en la raíz (recomendado para aislar el bot de cada proyecto; excluido de git por defecto).
- `TELEGRAM_BOT_TOKEN`: token del bot (de `@BotFather`). Nunca commitear en git.
- `TELEGRAM_ALLOWED_USER_IDS`: IDs numéricos de Telegram autorizados, separados por comas. Solo ellos reciben respuesta, y son también los destinatarios de los avisos del bucle. Los mensajes de cualquier otro usuario se ignoran sin tocar nada.
- Modelo conversacional: configurable en `orchestration.json` bajo la clave `"telegram"` (`harness`, `model`, `effort`). Si no se define, hereda por defecto la configuración de `"atenea"`.

## 📋 Comandos y Conversación Libre
- `/estado` o `/status`: si el bucle está en marcha, parado o esperando cuota; la fase según el disco; la versión abierta (cerradas, en curso, bloqueadas); el backlog sin versión; las altas por registrar y el último paso. Añade el ejecutor Artemisa/Atenea y Hades efectivos para el paso/dificultad, con arnés, modelo, esfuerzo, reservas y escalada. Muestra tokens registrados en las últimas 5 h por arnés/modelo y cuotas agotadas conocidas con hora local de vencimiento y minutos restantes; separa la espera global. «Sin agotamiento registrado» no garantiza cuota disponible; registros antiguos sin plazo/modelo no permiten reconstruirla.
- `/lanzar` o `/run`: solicita el arranque en segundo plano en el proyecto del gateway y anuncia el siguiente paso previsto. Si existe `orquestar.pid`, informa de que ya está en marcha. El hijo usa la configuración habitual del proyecto y escribe en `orquestar.log`; la confirmación indica que el proceso fue lanzado, cuyo inicio puede detenerse por las validaciones normales del motor. Consulta `/estado` para seguirlo.
- `/parar` o `/stop`: si existe `orquestar.pid`, solicita la parada al acabar el paso en curso mediante `orquestar.parar`. Si no existe, informa de que ya está parado. No interrumpe el paso actual.
- `/metricas [filtro]` o `/metrics [filtro]`: resumen por tarea de versión, minutos reales, tokens de desarrollo y Hades (`E/C/S`: entrada/caché leída/salida) y coste aproximado USD. Por defecto consulta `ultima`; acepta los mismos filtros de `adevv orquestar --metricas`: `todas`/`all`, `ultima`/`last`, `ultimas:N`/`last:N` y listas como `v0.3,v0.4`. Reutiliza su cálculo y tarifas ilustrativas (no precios vigentes); el tiempo real incluye las revisiones una sola vez y razonamiento no vuelve a sumarse a salida. Sin datos lo indica; filtros inválidos o JSONL corrupto devuelven explicación sin resultados parciales. Es una consulta local que no modifica el bucle, incluso si está activo.
- `/tarea <título>` (o `/task`) y `/bug <título>`: nueva tarea o bug maestro **sin versión** (`status: backlog`, como la deuda registrada). El bucle no lo trabaja hasta que le pones versión (o, si es un bug, hasta que `revisar-deuda` lo incluya). Las tareas van sin `depende_de`: se calculan cuando entran en una versión.
- `/nuevo` o `/reset`: elimina la sesión guardada del usuario emisor y reinicia el hilo de conversación.
- `/ayuda` (o `/help`, `/start`): lista de comandos disponibles.
- **Conversación libre**: cualquier mensaje enviado por un usuario autorizado que no comience por un comando fijo mantiene una conversación interactiva en texto libre con el asistente del proyecto. El hilo de la conversación se persiste automáticamente en `orquestar_telegram.json` (excluido de git) por usuario y arnés. Si la reanudación de una sesión previa falla, conmuta automáticamente a una sesión nueva sin interrumpir la experiencia.
- **Contexto seguro con el bucle en marcha**: si existe `orquestar.pid`, el asistente es instruido para no modificar ni commitear archivos rastreados del repositorio, limitándose a responder consultas, analizar el proyecto o sugerir registrar tareas o bugs mediante el buzón.

**Nunca escribe en el backlog con el bucle en marcha.** Deja la petición en el buzón (`orquestar_buzon.jsonl`, excluido de git) y el bucle la registra entre pasos, con un commit que solo lleva esos ficheros, y te avisa del ID. Sin bucle, la registra y la commitea en el momento, en la rama actual.

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
