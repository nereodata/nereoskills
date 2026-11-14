---
id: T-ADV-0037
title: "Simplificar los dictámenes de Hades y medir el resultado de las revisiones"
type: funcional
weight: 160
dificultad: media
version: "v1.2.0"
status: cancelled
depende_de: ["T-ADV-0039"]
origen: "Propuestas de optimización de v1.2.0 priorizadas el 2026-11-11 tras revisar Adevv y Afinn"
created_at: 2026-11-11
updated_at: 2026-11-12
superseded_by: T-ADV-0041
---

> Alcance vigente integrado en T-ADV-0041 y docs/plan/versions/v1.2.md.
> El contenido siguiente es histórico; no prescribe subfases ni revisiones del nuevo flujo.


# T-ADV-0037 · Simplificar los dictámenes de Hades y medir el resultado de las revisiones

## Objetivo

Distinguir el coste de invocar un arnés del resultado de una revisión independiente. Usar los informes canónicos y ampliar las métricas de T-ADV-0013 y T-ADV-0021 para evaluar qué revisiones consiguen cambios.

## Criterios de aceptación

- [ ] **CA-M-1.** Una aprobación limpia recoge alcance, evidencia, limitaciones y veredicto. Un rechazo explica qué comportamiento incorrecto podría pasar, cómo comprobarlo y quién puede resolverlo. Las rúbricas específicas se conservan cuando aportan una decisión.
- [ ] **CA-M-2.** El enrutado y el preflight de cierre interpretan tanto los informes históricos como el formato breve. Una revisión ausente, rechazada o pendiente sigue siendo distinguible de una aprobada.
- [ ] **CA-M-3.** La consulta y exportación de métricas separan intentos técnicos, revisiones con dictamen y hallazgos que dieron lugar a un cambio trazable. Una reserva o un error sin dictamen conserva su coste técnico sin sumar otra revisión terminada. Los datos históricos insuficientes se indican como desconocidos.
- [ ] **CA-M-4.** Comparar minutos por tarea aceptada y reaperturas posteriores en una muestra de cambios locales y casos de control de contenido, sincronización y uso real. Comprobar que la simplificación conserva la detección de los defectos de control.
- [ ] **CA-M-5.** Derivar los recuentos del resultado de T-ADV-0039. Conciliar respuesta e informe según la identidad y vigencia de la revisión. Un rechazo válido cuenta como revisión recibida y deja abierto el trabajo. Un desacuerdo de la misma revisión conserva las fuentes para aclaración. Evitar atribuir al intento un informe antiguo.
