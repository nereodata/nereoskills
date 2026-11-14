# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

## [1.2.0] - En desarrollo

### Añadido

- **T-ADV-0041** — Flujo autónomo ligero activo por defecto (`PROJECT.md` o política base embebida) sin subfases ceremoniales ni revisiones a mitad de tarea: memoria de relevo portable (`--checkpoint`), presupuestos duros separados de cuota, enrutado y esperas locales por ítem (`DECISION_ITEM`), verificación determinista (`unittest` + `ruff`) y revisión independiente post-verde proporcional a superficies críticas.
- **T-ADV-0039** — Cada llamada entrega su resultado con su objetivo, entradas, perfil y llamada padre. La ratificación de una revisión resuelve su espera anterior y permite continuar tras un rechazo de otro alcance. La cuota del proveedor conserva su recuperación.

## [1.1.4] - 2026-11-12

### Corregido

- **B-ADV-0048** — Hades puede entregar un rechazo formal desde una reserva. Artemisa recibe la investigación técnica asignada al cierre y, si agota su cuota, retoma el mismo encargo al relanzar.

## [1.1.3] - 2026-11-11

### Corregido

- **B-ADV-0046** — El bucle conserva los pasos completados al encontrar una fila de métricas dañada. Los productores serializan sus escrituras y `--recuperar-metricas` guarda una copia íntegra antes de recuperar el registro.

- **B-ADV-0044** — El orquestador acota las revisiones técnicas pendientes aunque cada intento confirme otra nota de diagnóstico. Un retorno erróneo solo permite cerrar el desarrollo con una aprobación vigente sobre el producto.

## [1.1.2] - 2026-11-11

### Corregido

- **B-ADV-0039** — Las cuotas de reservas de Hades conservan su historial sin detener pasos completados por otro proveedor; una revisión aún pendiente informa su proveedor y modelo reales.

- **B-ADV-0036** — El cierre cuenta las recaídas por comprobación y causa. Tras tres en difícil, Hades revisa los arreglos y sus evidencias. Solo abre una pregunta humana cuando identifica la intervención necesaria.

- **B-ADV-0033** — El detector conserva el destino antes de recortar la evidencia, admite etiquetas Markdown y prioriza la última declaración de salida sobre la última de la tarea.

- **B-ADV-0040** — Hades continúa por sus reservas autorizadas ante suscripción de Claude deshabilitada, incluido el diagnóstico sin punto final y con sufijo explicativo, respeta perfiles estrictos y conserva la revisión pendiente sin preguntas nuevas. La recuperación del WIP espera al trabajo ajeno y preserva los bytes del parche en Windows.

- **B-ADV-0034** — Responder preguntas del orquestador desde CLI local sin Telegram, compartiendo validación, persistencia e incorporación con el gateway y respetando dependencias.

- **B-ADV-0032** — Los arneses se aíslan en una sesión POSIX para terminar también sus descendientes al vencer el timeout o la gracia tras JSON. Los timeouts no finitos recuperan el valor seguro por defecto. La supervisión continúa tras salir el padre o recibir EOF, y la desactivación explícita prevalece sobre el entorno. En Windows, un Job Object asignado antes de reanudar el arnés permite terminar los descendientes aunque el padre ya haya salido.
- **B-ADV-0037** — El preflight, Telegram y la API de publicación bloquean el cierre con revisiones formales pendientes o rechazadas e indican cómo reanudarlas. El selector distingue parches; las métricas mantienen su agrupación histórica.

## [1.1.1] - 2026-11-10

### Corregido

- **B-ADV-0035** — La limpieza del test de orquestación en fondo comprueba fallos de taskkill y espera de forma acotada la salida del proceso temporal.
- **B-ADV-0032** — Evitar bloqueos del orquestador cuando un arnés emite su resultado pero no cierra el proceso.
- **B-ADV-0033** — Enrutar los hallazgos de Hades destinados al especificador sin crear bloqueos humanos falsos.

## [1.1.0] - 2026-11-07

### Añadido

- **T-ADV-0032** — Coordinador compartido de chequeos de calidad y release (`chequeos.py`): catálogo honesto por disponibilidad y resultado, plan explicable con origen, identidad compuesta de evidencia, coordinación concurrente entre CLI, gateway, agentes y worktrees, precedencia del último resultado real con registro de intermitencias, caché por comprobación y reutilización de preflight en el worktree integrado respetando `release.restricciones`.

### Corregido

- **B-ADV-0030** — Adaptados tests de regresión de orquestación (`test_orquestar.py`) para abastecer las llamadas sucesivas a `firma()` en turnos con espera de cuota y verificar que los pasos completados con progreso no acumulan reintentos indebidos tras B-ADV-0027.

- **B-ADV-0028** — `/estado` en Telegram desglosa por separado tareas y bugs de la versión abierta, agrupando variantes numéricas por `vkey`.

- **B-ADV-0024** — El gateway clasifica las marcas de cuota sin hora como supuestas de 300 s mediante `fallo_cuota`, permite su sondeo periódico con `configuraciones_con_cuota`, registra la recuperación tras éxito y avisa de falta de créditos una sola vez por episodio.

- **B-ADV-0027** — `reintentos_acumulados` no promueve indebidamente en tareas multiturno con progreso o aprobación de Hades y respeta las bajadas manuales de dificultad en Markdown reseteando contadores.

- **B-ADV-0026** — Preguntas humanas persistentes y accionables por Telegram, aislamiento del trabajo bloqueado y continuación de tareas independientes; respuestas incorporadas entre pasos y reanudación respetando parada manual.

- **B-ADV-0025** — `/cerrar` y `/release` comparten validaciones y publicación en `release_tools`, con preflight aislado y push atómico de main y la etiqueta solicitada.

- **B-ADV-0023** — Tras un bloqueo local, Clio resuelve los cambios pendientes o se conservan en stash con aviso antes de seguir con otra tarea, también en la misma rama; si no queda limpio, el bucle para.

- **B-ADV-0029** — Las reservas del bucle conservan su arnés al usar `--harness`; comandos, sesiones, cuotas y métricas usan el perfil efectivo, sin reutilizar la sesión de otro arnés.

## [1.0.0] - 2026-10-27

### Añadido

- **T-ADV-0023** — `/cerrar vX.Y [confirmo]` desde Telegram: resumen de la revisión, cierre no interactivo con push atómico y etiqueta anotada, y relanzamiento del bucle.
- **T-ADV-0025** — Limpieza de deuda menor de v0.3 a v0.6 en utilidades comunes del bucle y del gateway.
- **T-ADV-0031** — Perfil de arnés, modelo y esfuerzo fijado por tarea o bug (único o por rol), con reservas y aviso, modo `estricto`, validación del backlog y alta desde Telegram.
- **T-ADV-0024** — Registro por proyecto del gateway en Inicio de Windows mediante `adevv telegram --autoarranque on|off|estado`, ejecución oculta y diagnóstico de arranques inválidos.
- **T-ADV-0022** — Formato y lint por tarea sobre el delta Git estable, comandos explícitos o deducción conservadora y evidencia reutilizable por Hades.
- **T-ADV-0026** — Reservas conversacionales de Telegram por cuota o fallo de arranque, continuidad de sesiones propias, retorno al titular y diagnóstico por modelo con cuotas compartidas.
- **T-ADV-0030** — Token ambiental de Telegram como respaldo solo para avisos; el gateway requiere token definido en el `.env` del proyecto.

### Corregido

- **B-ADV-0022** — `/cerrar` y las altas por Telegram usan el bucle vivo y no un PID huérfano, las métricas ya no copian la salida de las verificaciones, un único helper reescribe el frontmatter y `/estado` indica el motivo real de la espera.
- **B-ADV-0021** — Volver atrás con bucles en marcha hacia un motor sin recarga ya no lo mata en silencio: se avisa.
- **B-ADV-0019** — Las pruebas ya no envían avisos reales a Telegram con el token del entorno.
- **B-ADV-0017** — El gateway conserva `telegram.log` y no acumula `--root` repetidos tras recargar de versión.
- **B-ADV-0016** — `espera_cuota()` reconoce «Resets in 56h48m9s» y no vuelve a probar el modelo agotado cada 30 minutos.
- **B-ADV-0014** — Las dependencias inválidas del backlog se devuelven a Cronos en vez de parar el bucle.
- **B-ADV-0010** — Suite verde al cerrar v1.0: patrón prohibido en `telegram_gateway.feature` y `/status` con PID simulado.
- **B-ADV-0015** — Los cambios sin commitear ya no paran el cambio de rama: Clio los resuelve y, si no puede, se guardan en un stash con aviso.
- **B-ADV-0020** — Comprobación de cuotas supuestas al relanzar y por intervalo, aviso de créditos por episodio y `--cuota-reset` sin borrar histórico, con recuperación de esperas y origen visible en estado/agentes.
- **B-ADV-0013** — Recuperación por perfil de los análisis sin progreso, aislamiento por paso y argumento, continuidad local y conservación de intentos en recarga.
- **B-ADV-0012** — Bloqueo local de tareas sin progreso tras agotar promociones, con diagnóstico persistido, aviso y continuidad de tareas independientes.
- **B-ADV-0009** — Instalación inmediata con bucles en marcha, conservación de versiones existentes y copias globales diferidas hasta que terminen los bucles, también con `--forzar`. La versión nueva se adopta mediante la recarga cooperativa existente.
- **B-ADV-0011** — Reintentos acotados por perfil ante fallos del arnés en pasos, reservas y diagnóstico final con cola de salida, conservando cuota y progreso commiteado.
- **B-ADV-0007** — Las pruebas de `test_cli_commands` ya no arrancan un gateway de Telegram real con el token del entorno.
- **B-ADV-0006** — Recuperación automática de la suite roja al cerrar la versión: bug reutilizable con salida del fallo, promoción de dificultad y parada tras tres arreglos fallidos en dificil.
- **B-ADV-0005** — Continuidad con reservas cuando falta el ejecutable en pasos, agentes y conversación de Telegram; evento filtrable `arnes`, métricas sin consumo y conservación de cuota previa.

## [0.6.1] - 2026-10-26

### Corregido

#### General
- **B-ADV-0008** — La nota del prompt para el repositorio fuente de Adevv se lee como una restricción a skills/, agents/ y workflows/

## [0.6.0] - 2026-10-26

### Añadido

#### General
- **T-ADV-0021** — Salto de configuraciones con cuota agotada vigente en agente() y exclusión de rebotes sin cuota en hades_llamadas

### Corregido

#### General
- **B-ADV-0003** — Aislamiento de iniciar_gateway en tests de bucle, PATH de usuario en subprocesos y colisión 409 en gateway.py
- **B-ADV-0004** — Fallo de reanudación codex exec resume por flag --sandbox y doble conteo de tokens cacheados en codex

## [0.5.0] - 2026-10-24

### A?adido

#### General
- **T-ADV-0018** ? Auto-recarga autom?tica del bucle y del gateway de Telegram al cambiar la versi?n activa de Adevv
- **T-ADV-0019** ? Firma con la versi?n de Adevv al pie de todos los mensajes de Telegram
- **T-ADV-0020** ? Comando independiente /agentes (--agentes) con porcentaje de cuota consumida por modelo y limpieza de /estado

## [0.4.0] - 2026-10-23

### Añadido

#### General
- **T-ADV-0013** — Comando de métricas (`adevv metrics` / `adevv orquestar --metricas`) con tabla por versión, exportación CSV y coste estimado de API
- **T-ADV-0014** — Mostrar agentes configurados para la tarea actual y estado de cuota en `/estado`
- **T-ADV-0015** — Control remoto del bucle (`/lanzar`, `/parar`) y consulta de `/metricas` desde Telegram
- **T-ADV-0016** — Ejecución en segundo plano de `adevv telegram` (`--fondo`, `--parar`) y auto-arranque desde `orquestar`
- **T-ADV-0017** — Canal limpio de prompts en `--agente` (`--prompt` y limpieza automática de temporales)

### Corregido

#### General
- **B-ADV-0002** — Ajustes menores transversales v0.3: coexistencia de clave `telegram` en `orchestration.json` y marca `sin_cuota` en intento intermedio de paso

## [0.3.0] - 2026-10-23

### Añadido

#### General
- **T-ADV-0010** — Modelos de reserva ante agotamiento de cuota en pasos y subagentes
- **T-ADV-0011** — Subida automática de dificultad de la tarea tras más de 2 reintentos
- **T-ADV-0012** — Conversación libre con continuidad de hilo en el gateway de Telegram

## [0.2.0] - 2026-10-23

### Añadido

#### General
- **T-ADV-0008** — Continuidad de hilo en revisiones de Hades por tarea y reanudación tras espera de cuota
- **T-ADV-0009** — Clasificación de dificultad al crear tareas/bugs y selección de agente/modelo por dificultad

## [0.1.0] - 2026-10-23

### Añadido

#### General
- **T-ADV-0001** — Publicación de versiones sin contenido interno
- **T-ADV-0002** — Instalación y sincronización con los arneses
- **T-ADV-0003** — Adevv desde cualquier proyecto sin rutas
- **T-ADV-0004** — Actualización automática de versiones publicadas
- **T-ADV-0005** — Migración de proyectos con submódulo
- **T-ADV-0006** — Triaje por subfase y alcance sin doble validación en desarrollo y revisión
- **T-ADV-0007** — Detección y espera de cuota agotada en subagentes (--agente)

### Corregido

#### General
- **B-ADV-0001** — Corrección transversal v0.1: resolución de rutas en sync, aislamiento de suite, lista blanca en versions y evaluar_tabla pura
