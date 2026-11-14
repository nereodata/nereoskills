---
id: T-ADV-0038
title: "Reanudar una tarea pendiente de respuesta humana desde /desbloquear"
type: funcional
weight: 180
version: "v1.2.0"
status: planned
dificultad: dificil
depende_de: ["T-ADV-0041"]
created_at: 2026-11-11
updated_at: 2026-11-12
---

# T-ADV-0038 · Reanudar una tarea pendiente de respuesta humana desde /desbloquear

## 🎯 Objetivo de Negocio
Permitir al usuario entregar la decisión pendiente desde Telegram. Reutilizar la operación existente de `/responder` y su incorporación por el bucle.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1.** Ante una pregunta humana identificada, `/desbloquear <Q-ID> <respuesta>` aplica las mismas reglas de autorización, validación y persistencia que `/responder`. Repetir el mensaje no duplica la incorporación. La ayuda de Telegram muestra la sintaxis.
- [ ] **CA-M-2.** Tras incorporar la respuesta, el planificador recupera la tarea respetando dependencias y parada manual. Una espera de cuota o una intervención técnica sin pregunta explica su motivo y conserva su estado.
