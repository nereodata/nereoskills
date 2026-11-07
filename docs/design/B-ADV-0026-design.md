# Diseño Técnico: B-ADV-0026 - Intervención humana por Telegram sin detener tareas independientes

## 🏗️ Arquitectura
- **Componentes creados/modificados**:
  - `[NEW] skills/orquestar/intervencion.py`: Gestión persistente y atómica de preguntas humanas (`orquestar_preguntas.json`) y cola de respuestas entrantes (`orquestar_respuestas.jsonl`), aislamiento y recuperación de trabajo en ramas `wip/<ID>`, envío único de avisos accionables con diagnóstico de canal, validación de referencias/autorización/idempotencia, incorporación entre pasos y espera cooperativa cuando no quedan tareas elegibles.
  - `[MODIFY] skills/orquestar/orquestar.py`: Integración del módulo `intervencion`, cierre de `stdin` (`subprocess.DEVNULL`) en ejecuciones no interactivas de `lanzar()`, opciones CLI `--preguntar` y `--preguntas`, ingesta de respuestas entre pasos (`incorporar_respuestas`), restauración automática de `wip/<ID>` al reanudar la tarea, distinción entre bloqueos globales y de tarea en `estado()`/`parte()`/`resumen()` y espera de intervención sin trabajo elegible.
  - `[MODIFY] skills/telegram_gateway/gateway.py`: Comandos `/preguntas` (`/pendientes`) y `/responder` (`/reply`) para consultar preguntas abiertas y registrar respuestas vinculadas respetando el aislamiento por proyecto, la protección del árbol con bucle en marcha y la reanudación automática cuando el bucle quedó esperando por falta de tareas elegibles (salvo parada manual explícita).
  - `[MODIFY] skills/orquestar/SKILL.md`, `skills/telegram_gateway/SKILL.md`, `CHANGELOG.md`: Documentación del flujo de bloqueo local, consulta y respuesta por Telegram.

## 🛠️ Cambios
- **[NEW]** `skills/orquestar/intervencion.py`:
  - `PREGUNTAS_FILE = 'orquestar_preguntas.json'` y `RESPUESTAS_FILE = 'orquestar_respuestas.jsonl'` (escritura atómica con fichero temporal y `os.replace`, excluidos de Git en `PROPIOS`).
  - `solicitar_intervencion(root, motor, iid, pregunta, contexto='', paso='', aislar=True, base_commit=None)`:
    1. Genera o reutiliza el ID de pregunta `Q-<PREFIJO>-XXXX` para la tarea `iid` y pregunta dada (evitando duplicar si la misma pregunta ya está `pendiente`).
    2. Si `aislar=True`, conserva los cambios del árbol de trabajo ajenos al fichero del ítem y a la revisión de versión en la rama `wip/<iid>` (creándola o actualizándola desde el árbol actual y devolviendo la rama `release/vX.Y` a su estado limpio previo, coordinado con `resolver_arbol_sucio` de `B-ADV-0023`).
    3. Actualiza el frontmatter de `iid` (`status: blocked`, `pendiente_de: humano`) y añade la sección `## Intervención humana pendiente` en el fichero de la tarea y en `docs/review/versions/vX.Y-revision.md`, commiteando únicamente esos dos archivos en la rama activa.
    4. Envía una sola vez el aviso del evento `respuesta` con `iid`, `Q-<PREFIJO>-XXXX`, pregunta, contexto e instrucción `/responder <Q-ID> <respuesta>`, registrando `notificada: True/False` y `diagnostico_aviso` (`enviado`, `canal no disponible`, `evento desactivado` o `fallo de envío`) para no duplicar avisos en consultas o pasos posteriores.
  - `registrar_respuesta_telegram(root, motor, usuario, argumento, autorizados)`:
    1. Verifica que `usuario` pertenezca a `autorizados`.
    2. Analiza `<referencia> <respuesta>` (o detecta ambigüedad si hay varias preguntas pendientes y no se indica referencia inequívoca).
    3. Rechaza referencias con prefijo de otro proyecto (`no pertenece a este proyecto`), inexistentes (`no existe`), ya cerradas (`ya está cerrada`), ambiguas (listando los `Q-ID` pendientes) o vacías.
    4. Tolera entregas repetidas idénticas (idempotencia por `(pregunta_id, respuesta_normalizada)`): si ya está en cola o incorporada con el mismo texto, devuelve confirmación idempotente sin duplicar entradas ni reanudar dos veces.
    5. Si el bucle está vivo (`motor.pid_vivo(root)`): encola la respuesta en `orquestar_respuestas.jsonl` y actualiza `estado_respuesta: 'en_cola'` en `orquestar_preguntas.json` sin tocar archivos rastreados del repositorio, devolviendo `Respuesta recibida para <Q-ID> (<T-ID>); se incorporará al terminar el paso en curso`.
    6. Si el bucle no está vivo: ejecuta `incorporar_respuestas(root, motor)` inmediatamente; si la tarea pasa a `planned` y el bucle había quedado esperando por falta de tareas elegibles (`bucle_esperando` activo y sin `orquestar.parar`), lanza `motor.en_fondo(root, argumentos=[])` e informa de la reanudación efectiva. Si existe `orquestar.parar`, respeta la parada manual sin relanzar.
  - `incorporar_respuestas(root, motor)`:
    1. Consume de forma atómica `orquestar_respuestas.jsonl` entre pasos del bucle.
    2. Evalúa si la respuesta es suficiente (no vacía ni marcada como pendiente/incompleta con `PENDIENTE:` / `INSUFICIENTE:` o validación de campos requeridos).
    3. Si es insuficiente: mantiene `status: blocked` y `pendiente_de: humano`, conserva la pregunta en `pendiente` con nota de qué falta (`motivo_insuficiente`), anota el intento en la tarea/revisión y avisa al usuario sin reanudar.
    4. Si es suficiente: marca la pregunta como `incorporada` (impidiendo reanudaciones dobles tras reinicios o recargas), escribe la decisión humana en el fichero de la tarea y en `vX.Y-revision.md`, cambia el frontmatter a `status: planned` eliminando `pendiente_de`, commitea solo esos ficheros rastreados y avisa de que la tarea ha sido reanudada efectivamente.
  - `restaurar_wip_si_procede(root, motor, iid)`:
    - Cuando el bucle va a ejecutar el paso de `iid` tras haberse reanudado y la pregunta incorporada registra `wip_rama` (`wip/<iid>`), materializa en el árbol de trabajo los ficheros guardados en `wip/<iid>` y marca `wip_restaurado: True` para que el paso continúe exactamente desde su trabajo previo.
- **[MODIFY]** `skills/orquestar/orquestar.py`:
  - Añadir `PREGUNTAS_FILE`, `RESPUESTAS_FILE` y temporales a `PROPIOS`.
  - En `lanzar()`: pasar `stdin=subprocess.DEVNULL` cuando `entrada is None` en `subprocess.run`.
  - En `estado(root, docs)`: si no hay tareas elegibles en `release/vX.Y` y existen preguntas humanas pendientes en esa versión, no lanzar `revisar-version` prematuramente; devolver `('PARAR', 'Bloqueos en vX.Y: ...')` distinguiendo el bloqueo de tarea de los bloqueos globales.
  - En `bucle()`: incorporar respuestas entre pasos, detectar bloqueos humanos nuevos tras ejecutar un paso, restaurar `wip/<ID>` e inyectar las respuestas incorporadas en el prompt al retomar la tarea, y esperar intervención humana cuando no quedan tareas elegibles (`esperar_intervencion`).
- **[MODIFY]** `skills/telegram_gateway/gateway.py`:
  - Añadir `/preguntas` (`/pendientes`, `/questions`) y `/responder` (`/reply`, `/answer`) en `responder()` y `AYUDA`.

## 🎯 Mapa de impacto
- **Llamantes**:
  - `motor.lanzar(cmd, root, harness, entrada=None, env=None)`: todos los llamantes (`ejecutar`, `agente`, `gateway.invocar`) mantienen su firma; cuando `entrada is None`, `stdin` queda cerrado con `DEVNULL`.
  - `motor.estado(root, docs)`: mantiene la tupla `('PASO', ...)` / `('PARAR', ...)` / `('FIN', ...)`. Solo omite `revisar-version` cuando existen preguntas humanas activas registradas en `orquestar_preguntas.json` para esa versión; todos los tests existentes (sin `orquestar_preguntas.json`) conservan su comportamiento exacto.
  - `motor.parte(root)` y `motor.resumen(root)`: añaden información de preguntas humanas pendientes y distinguen bloqueo global frente a bloqueo de tarea cuando hay preguntas registradas, manteniendo intacto el formato existente cuando no las hay.
  - `gateway.responder(root, usuario, texto, autorizados)`: añade ramas para `/preguntas` y `/responder`, conservando intactos todos los comandos previos y la conversación libre.
- **Escenarios y tests afectados**:
  - Ningún escenario ni test existente cambia de contrato ni requiere modificarse.
  - Se añaden escenarios `@B-ADV-0026` en `skills/orquestar/features/orquestacion.feature` y `skills/telegram_gateway/features/telegram_gateway.feature`, y pruebas en `skills/orquestar/test_intervencion_humana.py`.
- **Decisiones contradichas**: ninguna (`archivo:línea`: ninguna contradicción con `docs/requirements/platform_plan.md` ni `skills/orquestar/SKILL.md`).
- **Sistema de referencia**: marcas temporales ISO 8601 con `motor.ahora()` (hora local del motor, coherente con `orquestar.py`).
- **Camino caliente**: lectura de `orquestar_preguntas.json` (pocos KB en disco local) solo al consultar estado o entre pasos del bucle; coste $O(1)$ despreciable frente a la invocación de arneses.

## 🧩 Patrones
- ** Escritura atómica**: `tempfile.NamedTemporaryFile` en el mismo directorio + `os.replace` para `orquestar_preguntas.json` y consumo por renombrado atómico para `orquestar_respuestas.jsonl` (igual que `ingerir()` con `orquestar_buzon.jsonl`).
- **Aislamiento de trabajo**: extracción de archivos del delta de la tarea hacia `wip/<ID>` mediante índice Git o checkout temporal, dejando `release/vX.Y` limpio antes de ejecutar la tarea independiente `B`.

## 🧪 Testeabilidad
- Arneses simulados mediante funciones inyectadas en `ejecutar` / `subprocess.run` y transporte Telegram controlado interceptando `enviar` / `urllib.request.urlopen`, sin tráfico de red real ni procesos colgados.


## Ajustes de implementacion (2026-11-07)

Las revisiones RC-01/02/03 concretan tres guardas: las referencias por tarea se resuelven entre sus preguntas pendientes y deben ser únicas; cada registro conserva su rama Git y la incorporación solo cambia a ella con árbol limpio; los cambios ajenos mantienen la respuesta en cola con diagnóstico. La incorporación usa `cambiar_de_rama` después de validar limpieza y nunca pide a Clio confirmar trabajo ajeno para poder responder.

Las fases `bloqueo_aplicado` y `aviso_intentado` permiten reconciliar solicitudes publicadas antes del bloqueo durante el arranque o reintento. Cada escritura de tarea/revisión conserva en JSON el contenido anterior y el previsto antes de escribir Git; una recuperación solo continúa sobre esos contenidos, conservando cambios ajenos. El aviso se marca antes del envío: un corte incierto queda visible como envío interrumpido sin reenvío automático. Una tarea con varias preguntas sigue bloqueada hasta incorporar todas.

Si la recuperación encuentra cambios ajenos y aún no puede persistir el bloqueo, `estado` devuelve un bloqueo global de persistencia en vez de considerar elegible la tarea todavía `planned`. El bucle conserva el árbol y termina sin lanzar otro paso; al limpiar el impedimento y relanzar, la reconciliación completa el bloqueo y permite seguir con las independientes. La reconciliación también procesa los diagnósticos `envío iniciado` tras un corte, aunque las otras fases ya estuviesen completas.

El contrato anterior se concreta con un unico registro `orquestar_preguntas.json`: cada pregunta contiene la cola de respuestas, su orden global, autor y fecha, respuestas recibidas para deduplicacion y estado de incorporacion. Se elimina la cola JSONL separada propuesta inicialmente: registro y cola se publican juntos con fsync y os.replace, evitando la perdida por escritura parcial entre ambos archivos. El nombre JSONL se reserva en PROPIOS por compatibilidad, pero no se crea.

El bloqueo del sistema operativo en el directorio Git serializa escrituras del gateway y del motor, se libera al morir el proceso y admite worktrees. Las consultas leen versiones completas publicadas atomicamente. No se ejecutan escrituras Git desde el gateway con PID activo. Sin PID, antes de incorporar se comprueba si el estado era espera por bloqueo local; solo ese caso relanza automaticamente.

El aislamiento usa checkout de `wip/<ID>`, commit del delta y retorno de release a ORQUESTAR_BASE (HEAD anterior al paso). Solo tarea e informe de version se escriben y confirman en release. El WIP conserva el arbol completo; al retomar se aplica con Git de tres vias el delta binario desde aquella base, excluyendo metadatos del backlog y revision de version que ya contienen la decision humana. Un conflicto detiene la restauracion y conserva los archivos para resolucion, sin sobrescribir cambios independientes.

`--preguntar ID PREGUNTA --contexto TEXTO` usa ese flujo y termina; el prompt del paso contiene el mandato. Ademas `detectar_bloqueo` captura bloqueos humanos persistidos por el agente sin usar la CLI al retornar ejecutar. El contexto procede de la ultima seccion de la tarea. Se conservan las paradas globales existentes.

La suficiencia preliminar sigue el protocolo explicito PENDIENTE:/INSUFICIENTE:, que conserva el bloqueo y explica que falta. Una decision concreta devuelve la tarea al agente para verificar su aplicabilidad; si no resuelve el recurso debe registrar una pregunta nueva y terminar. No se interpreta texto humano como permisos o comandos. No hay cambio de arquitectura ni dependencias.

La espera activa comprueba la cola y parada manual cada segundo, conserva el gateway y no dispara suite o revision de version mientras queden intervenciones locales pendientes. Con espera_max=0 devuelve control; el gateway relanza tras respuesta si corresponde. `parte`, `resumen`, `--preguntas` y Telegram exponen los IDs y el diagnostico, sin reenviar avisos.

API concreta: `listar_preguntas(root, solo_pendientes=False)`, `solicitar_intervencion(root, iid, pregunta, **opciones)`, `incorporar_respuestas(root)` y `responder_pregunta(root, usuario, argumento, autorizados)` delegan en intervencion con las funciones vigentes del motor, conservando la inyeccion por mocks en pruebas. No existe API de produccion para preparar fixtures.

Comprobacion del camino frecuente: las pruebas ejecutan consultas y varias vueltas con transporte contado; ninguna consulta envia HTTP, y la ejecucion no invoca arneses adicionales para gestionar estado o suficiencia preliminar. Solo se leen registros locales; no se instala ni consulta un servicio nuevo.
