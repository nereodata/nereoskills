---
id: B-ADV-0034
title: "El desbloqueo de tareas del orquestador solo es accesible por Telegram"
type: bug
weight: 20
dificultad: media
version: "v1.1.2"
status: planned
created_at: 2026-11-10
updated_at: 2026-11-10
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
