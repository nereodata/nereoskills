---
id: B-ADV-0034
title: "El desbloqueo de tareas del orquestador solo es accesible por Telegram"
type: bug
weight: 20
dificultad: media
version: "v1.1.2"
status: planned
created_at: 2026-11-10
updated_at: 2026-11-11
origen: "Incidencia comunicada por el usuario: el único canal de desbloqueo es Telegram (2026-11-10)"
---

# B-ADV-0034: El desbloqueo de tareas del orquestador solo es accesible por Telegram

## 🎯 Descripción del Fallo

**Causa raíz:** el modelo duradero de intervención humana y la operación
`responder_pregunta()` viven correctamente en el orquestador, pero la única
interfaz de usuario que las invoca es `/responder <Q-ID> <respuesta>` del
gateway de Telegram. Ni la CLI de `adevv orquestar` ni una interfaz de control
del propio orquestador permiten listar las preguntas pendientes, aportar una
respuesta y confirmar que la tarea ha vuelto a ser elegible.

**Comportamiento observado:** una tarea bloqueada solo puede desbloquearse
desde Telegram. Si Telegram no está configurado, está caído, no es el canal del
operador o se trabaja desde otra automatización, el bloqueo persiste aunque el
operador disponga de una respuesta válida.

**Comportamiento esperado:** el orquestador expone un punto de control propio
para consultar y resolver preguntas pendientes. Telegram se limita a ser un
adaptador de ese punto de control, por lo que ambos canales producen el mismo
estado persistido, aplican las mismas validaciones y no pueden reanudar dos
veces una tarea.

## 📋 Reproducir

1. Ejecutar un proyecto sin credenciales de Telegram y bloquear una tarea con
   `adevv orquestar --preguntar`.
2. Consultar el estado del orquestador y obtener la referencia `Q-...`.
3. Intentar registrar una respuesta y reanudar la tarea sin usar Telegram.
4. Comprobar que no existe una interfaz soportada para ello y que la tarea
   continúa en `blocked`.

## ✅ Criterios de aceptación

- [ ] **CA-1 — Operación independiente del canal:** el orquestador ofrece una
  operación documentada para listar preguntas pendientes y otra para registrar
  una respuesta vinculada a `Q-ID` (o a un ID de tarea inequívoco), sin requerir
  Telegram.
- [ ] **CA-2 — Control local sin servidor:** esta entrega publica la respuesta
  mediante CLI local. No requiere endpoint HTTP, socket, pipe, proceso de escucha,
  token de API ni contrato de red versionado. La autoridad local procede de los
  permisos del sistema operativo del usuario que ejecuta la orden sobre el
  proyecto; no se requieren identidad ni credenciales de Telegram. No se añade
  elevación de privilegios ni acceso remoto.
- [ ] **CA-3 — Contrato CLI:** `adevv orquestar --preguntas` conserva su consulta
  existente y `adevv orquestar --responder <Q-ID> "<respuesta>"` registra una
  respuesta no vacía. Admite un ID de tarea en lugar de Q-ID solo si identifica
  una única pregunta pendiente. Las referencias inexistentes, ajenas al proyecto,
  ambiguas y cerradas, y el texto vacío se rechazan con diagnóstico sin modificar
  preguntas ni tareas. La respuesta se trata como dato, sin ejecutarla.
- [ ] **CA-4 — Un único dominio:** CLI y Telegram delegan en la misma operación
  de dominio. Conservan aislamiento por raíz de proyecto, resolución de
  ambigüedades, idempotencia, persistencia atómica y el protocolo existente de
  incorporación entre pasos. La CLI identifica al operador local sin suplantar
  un usuario Telegram ni añadirlo a la lista de autorizados del gateway; Telegram
  mantiene su validación de remitentes autorizados.
- [ ] **CA-5 — Reanudación observable:** la respuesta distingue entre recibida,
  incorporada y tarea efectivamente reanudada. Respeta la parada manual, otra
  pregunta pendiente y las dependencias; un texto `PENDIENTE:` o
  `INSUFICIENTE:` conserva el bloqueo con diagnóstico.
- [ ] **CA-6 — Compatibilidad:** `/preguntas` y `/responder` continúan
  funcionando como adaptadores compatibles, sin cambios de formato que rompan
  los flujos existentes ni reenvíos duplicados.
- [ ] **CA-7 — Verificación:** pruebas controladas cubren CLI sin Telegram,
  rechazos de CA-3, aislamiento entre dos raíces de proyecto, entregas repetidas
  por ambos canales y concurrencia entre CLI y Telegram, recepción mientras otro
  paso está activo, reinicio antes de incorporación, parada manual, respuestas
  insuficientes, otra pregunta pendiente y dependencias no satisfechas. Se conserva
  la regresión del rechazo de remitentes Telegram no autorizados. Los escenarios
  y tests ejecutables se elaboran en la subfase A/C1 del siguiente bug-fix.

## DEC-ESP-0034-01 · Alcance local del control (2026-11-11)

- **Decisión:** el control propio del orquestador en v1.1.2 es la CLI local,
  con consulta existente y nueva orden de respuesta. Se sustituye la obligación
  original de endpoint de CA-2 y se alinean CA-3/CA-4/CA-7. El endpoint queda fuera
  de esta entrega; no es un entregable opcional ni una condición de cierre.
- **Motivo:** el problema demostrado es responder sin Telegram desde la máquina
  del operador. No consta consumidor remoto; la CLI resuelve ese valor y respeta
  `docs/requirements/platform_plan.md:11` (sin servidores propios). No se modifica
  esa restricción ni se presupone que un socket o pipe quede exceptuado.
- **Alternativa descartada:** servidor HTTP o escucha local autenticada con contrato
  versionado; añade servicio, transporte y credenciales sin consumidor justificado.
  Requeriría una ampliación separada con revisión arquitectónica cuando exista ese
  consumidor. No se crea ahora tarea ni versión adicional para ello.
- **Contrato y autenticación:** el contrato público de esta entrega es la sintaxis
  CLI de CA-3 y los estados de CA-5. No se promete JSON ni protocolo versionado.
  El usuario local actúa con sus permisos de archivos existentes; la autorización
  del gateway sigue siendo independiente. No se abre ninguna interfaz de red.
- **Estados:** recepción durable no significa incorporación ni arranque. Con paso
  activo se confirma recepción en cola; la incorporación ocurre entre pasos y
  sobre la rama de destino. Una respuesta concreta permite `planned` únicamente
  tras resolver todas las preguntas; la elegibilidad respeta las dependencias.
  La parada manual impide relanzar. Solo se anuncia reanudación si se ha lanzado
  efectivamente el bucle; de lo contrario se informa incorporación o impedimento.
  `PENDIENTE:`/`INSUFICIENTE:` conservan bloqueo y motivo. No se exige nuevo
  estado persistido ni consulta adicional para observar estos resultados.
- **Idempotencia:** repetir el mismo texto para una pregunta pendiente no agrega
  otra recepción; responder una cerrada se rechaza. Tras reinicio se conserva la
  respuesta recibida y se incorpora una sola vez. CLI y Telegram comparten estas
  garantías sin producir reanudaciones duplicadas ni reenviar avisos de consulta.
- **Delta e historial:** `git log` identifica `80a482d` como introducción de la
  intervención durable y el triaje reconoce `--preguntas` existente. La corrección
  añade el acceso de respuesta CLI y solo los huecos del dominio demostrados por
  pruebas; no reimplementa la consulta ni la persistencia. No hay escenarios de
  este bug aprobados que deban modificarse o retirarse.
- **Validación de este paso:** exclusivamente documental, sin código ni tests;
  `adevv orquestar --verificar "git diff --check"`, conforme al triaje. El próximo
  bug-fix concretará su comando de pruebas dirigidas antes de implementar.

## 📋 Evidencias

- `README.md` documenta la consulta y la respuesta exclusivamente mediante
  `/preguntas` y `/responder` de Telegram.
- `skills/telegram_gateway/gateway.py` enruta `/responder` a
  `motor.responder_pregunta()`.
- `skills/orquestar/orquestar.py` ya centraliza la operación durable
  `responder_pregunta()`, pero no la publica como control de CLI o endpoint.
- `skills/orquestar/intervencion.py` contiene la validación y persistencia que
  deben permanecer como fuente única de verdad.

## Triaje · 2026-11-11

- `base_calidad`: `424a3493a5dd58174df251166afb1f89d38872ed`.
- Rama conservada: `hotfix/v1.1.2`, ya activa y coherente con la versión del bug;
  no se crea otra rama ni se publica la versión.
- Delta real: `--preguntas` ya está implementado en el parser y consulta el
  dominio; falta exponer la respuesta desde CLI. No se reimplementará la consulta.
- Impedimento de definición: CA-2 exige un endpoint local autenticado y contrato
  versionado, mientras la alternativa permite omitirlo si no hay consumidor
  externo. `docs/requirements/platform_plan.md:11` descarta servidores propios.
  No existe aquí decisión que determine transporte, autenticación o consumidor.
  No se elimina CA-2 ni se introduce una arquitectura nueva desde desarrollo.
- Subfase A: [EXEC] definir el alcance de control independiente del canal y
  sus escenarios; conflicto de requisitos resuelto por DEC-ESP-0034-01;
  Hades revisa esa resolución antes de continuar a escenarios.
- Subfase B: [EXEC] diseño de adaptadores y contrato compartido, una vez resuelto
  el impedimento de definición.
- Subfase C1: [EXEC] regresiones dirigidas de CLI y del control que se acuerde,
  con equivalencia Telegram, persistencia e idempotencia.
- Subfase C2: [EXEC] adaptador de respuesta y solo las carencias del dominio
  demostradas por esas regresiones.
- Subfase D: [EXEC] Hades sobre el entregable completo; ahora se eleva el
  impedimento a la revisión de especificación, sin fingir escenarios aprobados.
- Subfase E: [EXEC] README y skills operativas afectadas por el contrato final.
- Subfase F: [EXEC] cierre y commit; no marcar completed mientras falte definición.
- Verificación al cierre: pruebas unitarias dirigidas de control/CLI que se
  identifiquen tras resolver el alcance, más regresiones de intervención y
  Telegram afectadas; registrar el comando exacto antes de implementarlas.
  En este intento, limitado al triaje documental, únicamente
  `adevv orquestar --verificar "git diff --check"`; no hay cambio ejecutable que
  justifique pruebas funcionales ni suite completa.

## Hallazgo de Hades enrutado
- Destino: `especificador`
- Decisión: ejecutar especificar
- Evidencia: Hades review-spec: NO APROBADO; H-01 ALTA para especificador. CA-2/CA-4/CA-7 exigen endpoint autenticado versionado; alternativa permite CLI suficiente y platform_plan.md:11 descarta servidores propios. Decision: ejecutar especificar para reconciliar alcance obligatorio, compatibilidad de arquitectura, transporte, autenticacion y contrato antes de escenarios/diseno/codigo. No falta recurso externo ni se necesita pregunta humana. Informe docs/review/spec_reviews/B-ADV-0034-spec-review.md; revision sobre adjuntos por fallo de acceso local del arnes.

## Cierre del paso especificar · 2026-11-11

H-01 resuelto por DEC-ESP-0034-01 y aprobado por Hades (9/10, solo definición).
Se devuelve el bug a `planned` sin `pendiente_de`. Continúa bug-fix desde subfase A;
no hay código, tests ni escenarios aprobados en este paso. El hallazgo enrutado
anterior y el triaje se conservan como historial, sin bloqueo vigente.
