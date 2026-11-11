---
id: B-ADV-0034
title: "El desbloqueo de tareas del orquestador solo es accesible por Telegram"
type: bug
weight: 20
dificultad: media
version: "v1.1.2"
status: blocked
created_at: 2026-11-10
updated_at: 2026-11-11
origen: "Incidencia comunicada por el usuario: el único canal de desbloqueo es Telegram (2026-11-10)"
pendiente_de: especificador
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
- [ ] **CA-2 — Nuevo endpoint de control:** la operación se publica como un
  endpoint local autenticado del orquestador, con contrato versionado que
  devuelve pregunta, estado de recepción e información de reanudación. Debe
  restringirse al propietario local o a credenciales explícitamente
  configuradas; no se expondrá por defecto en una interfaz de red pública.
- [ ] **CA-3 — CLI como cliente de referencia:** `adevv orquestar` proporciona
  una orden equivalente para consultar y responder, de modo que el desbloqueo
  siga disponible en instalaciones sin servidor HTTP ni Telegram.
- [ ] **CA-4 — Un único dominio:** el endpoint, la CLI y Telegram delegan en la
  misma operación de dominio. Conservan autorización, aislamiento por proyecto,
  resolución de ambigüedades, idempotencia, persistencia atómica y el protocolo
  existente de incorporación entre pasos.
- [ ] **CA-5 — Reanudación observable:** la respuesta distingue entre recibida,
  incorporada y tarea efectivamente reanudada. Respeta la parada manual, otra
  pregunta pendiente y las dependencias; un texto `PENDIENTE:` o
  `INSUFICIENTE:` conserva el bloqueo con diagnóstico.
- [ ] **CA-6 — Compatibilidad:** `/preguntas` y `/responder` continúan
  funcionando como adaptadores compatibles, sin cambios de formato que rompan
  los flujos existentes ni reenvíos duplicados.
- [ ] **CA-7 — Verificación:** pruebas controladas cubren el endpoint y la CLI
  sin Telegram, autorización local, preguntas ambiguas o cerradas, entregas
  repetidas, respuesta mientras otro paso está activo, reinicio y coexistencia
  con la orden Telegram.

## 💡 Alternativa de diseño

La alternativa más simple y probablemente suficiente es **no crear un servidor
HTTP**: añadir `adevv orquestar --preguntas` y `adevv orquestar --responder
<Q-ID> <respuesta>` como interfaz pública local sobre `responder_pregunta()`.
Después, si una integración externa lo justifica, un pequeño endpoint local
(por ejemplo, socket/pipe autenticado) puede reutilizar exactamente ese mismo
servicio. Esta opción evita abrir puertos, gestionar tokens HTTP y ampliar la
superficie de ataque, y resuelve ya el bloqueo fuera de Telegram.

La decisión de triaje debe determinar si existe un consumidor no local que
realmente requiera HTTP. Si lo hay, el endpoint debe mantenerse local por
defecto y la CLI debe ser su cliente de referencia; si no, la CLI cubre el
requisito funcional sin introducir un servidor.

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
  sus escenarios; primero Hades /review-spec sobre el conflicto de requisitos.
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
