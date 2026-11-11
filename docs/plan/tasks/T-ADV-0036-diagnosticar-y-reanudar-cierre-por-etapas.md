---
id: T-ADV-0036
title: "Diagnosticar fallos independientes y reanudar el cierre por etapas"
type: funcional
weight: 80
dificultad: dificil
version: "v1.2.0"
status: planned
depende_de: ["B-ADV-0031"]
origen: "Propuestas de optimización de v1.2.0 priorizadas el 2026-11-11 tras revisar Adevv y Afinn"
created_at: 2026-11-11
updated_at: 2026-11-11
---

# T-ADV-0036 · Diagnosticar fallos independientes y reanudar el cierre por etapas

## Objetivo

Reducir las vueltas completas de reparación en un cierre como B-AFN-0185. Aplicar el catálogo y la planificación de T-ADV-0032 con la fuente común de evidencias de B-ADV-0031. El delta es su uso en la secuencia real de fallo, diagnóstico, reparación y revalidación del cierre.

## Criterios de aceptación

- [ ] **CA-M-1.** Tras el primer fallo se identifica la etapa y se recogen los demás fallos de etapas independientes que puedan ejecutarse. Se explican las etapas pendientes por dependencia, coste o falta de entorno.
- [ ] **CA-M-2.** Tras una reparación se repiten las comprobaciones afectadas y se ejecutan las pendientes. Cada verde reutilizado sigue siendo válido para sus entradas y entorno. Cuando el proyecto solo declara un comando opaco, su resultado acredita ese comando completo.
- [ ] **CA-M-3.** El diagnóstico distingue una recaída de la misma causa de un fallo recién descubierto en otra etapa. La versión solo supera el cierre cuando todas sus comprobaciones obligatorias están acreditadas.
- [ ] **CA-M-4.** Reproducir en un proyecto de prueba la secuencia de Afinn con defectos de formato, contenido e integración, incluidos los siete fallos de integración del episodio. Comparar con el cierre anterior el número de repeticiones completas y el tiempo hasta identificar los fallos independientes.
