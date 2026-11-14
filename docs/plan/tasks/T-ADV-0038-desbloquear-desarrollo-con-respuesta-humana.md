---
id: T-ADV-0038
title: "Reanudar una tarea pendiente de respuesta humana desde /desbloquear"
type: funcional
weight: 180
version: "v1.2.0"
status: completed
dificultad: dificil
depende_de: ["T-ADV-0041"]
created_at: 2026-11-11
updated_at: 2026-11-14
---

# T-ADV-0038 · Reanudar una tarea pendiente de respuesta humana desde /desbloquear

## 🎯 Objetivo de Negocio
Permitir al usuario entregar la decisión pendiente desde Telegram. Reutilizar la operación existente de `/responder` y su incorporación por el bucle.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1.** Ante una pregunta humana identificada, `/desbloquear <Q-ID> <respuesta>` aplica las mismas reglas de autorización, validación y persistencia que `/responder`. Repetir el mensaje no duplica la incorporación. La ayuda de Telegram muestra la sintaxis.
- [x] **CA-M-2.** Tras incorporar la respuesta, el planificador recupera la tarea respetando dependencias y parada manual. Una espera de cuota o una intervención técnica sin pregunta explica su motivo y conserva su estado.

## 🛠️ Entrega y verificación
- **Gateway de Telegram (`skills/telegram_gateway/gateway.py`)**: Incorporación de `/desbloquear <Q-ID> <respuesta>` (y alias `/unblock`) en `AYUDA`, recordatorio conversacional y enrutado de `despachar()`, delegando íntegramente en `motor.responder_pregunta(...)` para reutilizar las mismas garantías de autorización, validación, persistencia, idempotencia y disparo del bucle en fondo que `/responder`.
- **Dominio compartido de intervenciones (`skills/orquestar/intervencion.py`)**: Diagnóstico sin mutación de estado ante esperas activas de cuota (global del bucle en `leer_espera`/`marcas_cuota` o local del ítem en `decision_item`) e intervenciones técnicas sin pregunta humana abierta (`pendiente_de` en `especificador`/`intervencion_tecnica`/`humano` sin `Q-ID`, `decision_item` en espera/asignación/aclaración, revisión de código bloqueada o `pausa_tecnica` en `contexto_ejecucion`), tanto al indicar un `<T-ID|B-ID>` como al omitir referencia sin preguntas abiertas, preservando íntegramente los mensajes de referencias inexistentes/ajenas, respuestas ambiguas y preguntas ya cerradas. Ajuste de detección de bloqueo/espera del motor, conservación de `orquestar.parar` y verificación de condiciones locales antes de lanzar el bucle en fondo.
- **Documentación y verificación**: Actualización de `skills/telegram_gateway/SKILL.md`, `README.md` y `CHANGELOG.md`; suite de pruebas focalizada en `tests/test_desbloquear_telegram.py` ejecutada mediante `adevv orquestar --verificar` sin tráfico real a Telegram.
