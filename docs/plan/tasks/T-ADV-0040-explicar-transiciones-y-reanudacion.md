---
id: T-ADV-0040
title: "Explicar por qué paró el proceso y qué trabajo se retomará"
type: funcional
weight: 150
dificultad: media
version: "v1.2.0"
status: planned
depende_de: ["T-ADV-0035"]
created_at: 2026-11-12
updated_at: 2026-11-12
---

# T-ADV-0040 · Explicar por qué paró el proceso y qué trabajo se retomará

## Objetivo

Que una persona pueda seguir una transición de trabajo y sus llamadas desde CLI o Telegram y determinar cuándo sirve relanzar. Aprovechar los registros y consultas existentes.

## Criterios de aceptación

- [ ] **CA-M-1.** Una transición identifica ítem, estado anterior y siguiente, disparador, quién decidió, agente asignado o condición para reanudar, evidencia y llamada relacionada cuando proceda. La consulta distingue una asignación pendiente de una ejecución iniciada.
- [ ] **CA-M-2.** En el recorrido de Afinn, el rechazo de Hades, la entrega a Artemisa y una posible espera real de Artemisa se pueden seguir en orden. Si el proceso sale por límite de espera, el aviso indica la llamada y el perfil afectados y el estado persistido del encargo.
- [ ] **CA-M-3.** El aviso y las consultas de estado en CLI y Telegram leen la misma transición confirmada. Tras reiniciar explican tanto la última salida del proceso como el siguiente trabajo elegible o la condición que lo impide. Una consulta sobre datos antiguos distingue hechos registrados de causas desconocidas.
