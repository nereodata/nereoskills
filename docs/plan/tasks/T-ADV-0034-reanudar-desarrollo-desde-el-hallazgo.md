---
id: T-ADV-0034
title: "Reanudar task-dev y bug-fix desde el hallazgo pendiente"
type: funcional
weight: 40
dificultad: dificil
version: "v1.2.0"
status: planned
depende_de: []
origen: "Propuestas de optimización de v1.2.0 priorizadas el 2026-11-11 tras revisar Adevv y Afinn"
created_at: 2026-11-11
updated_at: 2026-11-11
---

# T-ADV-0034 · Reanudar task-dev y bug-fix desde el hallazgo pendiente

## Objetivo

Al volver de una revisión, bloqueo o reinicio, retomar la subfase afectada con el WIP de la tarea y las aprobaciones que sigan vigentes. Ampliar el triaje de T-ADV-0006 y la continuidad de sesión de T-ADV-0008 para que la recuperación funcione también en una sesión nueva.

## Criterios de aceptación

- [ ] **CA-M-1.** Si Hades pide reforzar una aserción con la especificación aprobada, la retoma identifica el hallazgo, la prueba y la subfase. Tras corregirla se revisa la prueba afectada y se continúa con las revisiones pendientes.
- [ ] **CA-M-2.** Si la corrección cambia un criterio de aceptación, se reabren su especificación y las aprobaciones que dependían de ella. Las aprobaciones independientes conservan alcance y evidencia identificables.
- [ ] **CA-M-3.** Un reinicio, cambio de arnés o segunda retoma recupera el último estado acreditado sin duplicar revisiones ni perder WIP o commits intercalados. En tareas antiguas con evidencia incompleta se identifica qué alcance requiere verificación.
- [ ] **CA-M-4.** Demostrar ambos recorridos por las entradas orquestadas de task-dev y bug-fix. El cierre sigue exigiendo el dictamen final aplicable al cambio entregado.
