---
id: T-ADV-0037
title: "Simplificar los dictámenes de Hades y medir el resultado de las revisiones"
type: funcional
weight: 90
dificultad: media
version: "v1.2.0"
status: planned
depende_de: []
origen: "Propuestas de optimización de v1.2.0 priorizadas el 2026-11-11 tras revisar Adevv y Afinn"
created_at: 2026-11-11
updated_at: 2026-11-11
---

# T-ADV-0037 · Simplificar los dictámenes de Hades y medir el resultado de las revisiones

## Objetivo

Distinguir el coste de invocar un arnés del resultado de una revisión independiente. Usar los informes canónicos y ampliar las métricas de T-ADV-0013 y T-ADV-0021 para evaluar qué revisiones consiguen cambios.

## Criterios de aceptación

- [ ] **CA-M-1.** Una aprobación limpia recoge alcance, evidencia, limitaciones y veredicto. Un rechazo explica qué comportamiento incorrecto podría pasar, cómo comprobarlo y quién puede resolverlo. Las rúbricas específicas se conservan cuando aportan una decisión.
- [ ] **CA-M-2.** El enrutado y el preflight de cierre interpretan tanto los informes históricos como el formato breve. Una revisión ausente, rechazada o pendiente sigue siendo distinguible de una aprobada.
- [ ] **CA-M-3.** La consulta y exportación de métricas separan intentos técnicos, revisiones con dictamen y hallazgos que dieron lugar a un cambio trazable. Una reserva o un error sin dictamen conserva su coste técnico sin sumar otra revisión terminada. Los datos históricos insuficientes se indican como desconocidos.
- [ ] **CA-M-4.** Comparar minutos por tarea aceptada y reaperturas posteriores en una muestra de cambios locales y casos de control de contenido, sincronización y uso real. Comprobar que la simplificación conserva la detección de los defectos de control.
