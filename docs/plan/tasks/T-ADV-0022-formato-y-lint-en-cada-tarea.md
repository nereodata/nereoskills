---
id: T-ADV-0022
title: "Formato y lint del proyecto sobre los ficheros tocados en cada tarea, no solo al cerrar la versión"
type: funcional
weight: 60
dificultad: media
version: "v1.0.0"
status: blocked
pendiente_de: especificador
depende_de: []
origen: "B-ADV-0006: la suite llega en rojo al cierre por formato (Prettier) acumulado tarea a tarea"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0022: Formato y lint del proyecto sobre los ficheros tocados en cada tarea, no solo al cerrar la versión

## 🎯 Objetivo de Negocio
Cada tarea verifica solo las pruebas de su triaje, así que los fallos de formato y lint (p. ej. Prettier, ESLint, ruff) se acumulan y solo aparecen al pasar la suite completa al cerrar la versión. B-ADV-0006 hace que el bucle se recupere de ese rojo; esta tarea evita que llegue a producirse, comprobando formato y lint en cada `task-dev` / `bug-fix` y en la revisión de Hades.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Detección de las etapas de formato y lint):** el proyecto puede declarar en `task_config.yaml` (p. ej. `validation.formato` y `validation.lint`) los comandos de formato y lint, aceptando un marcador de ficheros (`{ficheros}`) para limitarlos al delta. Sin declaración, se deducen de forma conservadora de los manifiestos habituales (`package.json` scripts `format:check`/`lint`, `pyproject.toml` con `ruff`, etc.) o se omiten sin error.
- [ ] **CA-M-2 (Uso en cada tarea):** `/task-dev` y `/bug-fix` ejecutan esas etapas sobre los ficheros que tocan antes de cerrar (aplicando el formateador si existe modo de escritura), y la tarea no pasa a `completed` con formato o lint en rojo en su delta.
- [ ] **CA-M-3 (Hades):** la revisión de código de Hades comprueba (vía `--verificar`, reutilizando evidencia del mismo árbol) que formato y lint pasan sobre el delta; un fallo es un hallazgo para el `desarrollador`.
- [ ] **CA-M-4 (Pruebas y documentación):** pruebas unitarias de la resolución de comandos y del marcador `{ficheros}`; documentación en las skills afectadas y en `skills/orquestar/SKILL.md`.

## 📋 Notas
- La suite completa al cerrar versión se mantiene como red de seguridad (B-ADV-0006).

## Bloqueo de especificaci?n (2026-10-26)

Hades `/review-spec`: RECHAZADO. H-01/H-02 altos y H-03 medio, todos para especificador con destino resolver. Ver [informe](../../review/spec_reviews/T-ADV-0022-spec-review.md) y [revisi?n de versi?n](../../review/versions/v1.0-revision.md). Se requiere concretar ambos flujos de cierre, contextos y resultados independientes, vigencia de evidencia y estructura de la caracter?stica. Avance conservado en `wip/T-ADV-0022` (`e47461f`); release mantiene el estado funcional previo. No hay implementaci?n ni pruebas funcionales ejecutadas. Triaje y borradores en WIP pendientes de ajustar tras especificar.
