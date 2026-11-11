---
id: T-ADV-0035
title: "Pedir intervención humana solo ante una decisión o recurso pendiente del usuario"
type: funcional
weight: 50
dificultad: dificil
version: "v1.2.0"
status: planned
depende_de: []
origen: "Propuestas de optimización de v1.2.0 priorizadas el 2026-11-11 tras revisar Adevv y Afinn"
created_at: 2026-11-11
updated_at: 2026-11-11
---

# T-ADV-0035 · Pedir intervención humana solo ante una decisión o recurso pendiente del usuario

## Objetivo

Aplicar el mismo criterio a preguntas originadas por un agente, un dictamen o el motor de recuperación. Integrar las correcciones de v1.1.2 (B-ADV-0033, B-ADV-0036, B-ADV-0039 y B-ADV-0040) en un comportamiento comprobable desde el paso hasta la cola de preguntas.

## Criterios de aceptación

- [ ] **CA-M-1.** Un hallazgo con responsable de desarrollo o especificación vuelve a ese rol. Un destino ambiguo se aclara dentro del flujo. Un fallo de proveedor usa las reservas autorizadas y, si se agotan temporalmente, deja una espera técnica recuperable.
- [ ] **CA-M-2.** Una pregunta humana explica la decisión o el recurso concreto que únicamente puede aportar el usuario. Ante el mismo impedimento se conserva una sola pregunta y su respuesta incluso después de una reanudación.
- [ ] **CA-M-3.** Repetir la misma indisponibilidad o reescribir su diagnóstico no acredita avance. Al recuperar el recurso se retoma el paso pendiente y las tareas independientes siguen siendo elegibles.
- [ ] **CA-M-4.** Cubrir con proveedores simulados un fallo técnico, un conflicto resoluble por el especificador y una decisión genuinamente humana. Verificar estado, cola y destino a través de los canales existentes.
