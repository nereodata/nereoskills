---
name: review-design
description: Auditoría del plan de diseño técnico
inputs:
  - design_file: Ruta del documento de diseño técnico a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte de revisión de diseño generado
---

# Skill: Review Design (/review-design)

Audita la propuesta de diseño técnico antes de escribir código.

> - **Proporcionalidad:** Audita el diseño frente a la tarea. Ajusta la profundidad al cambio.
> - **Ámbito:** Contrasta el diseño con los BDD y el código existente.

## 📋 Pasos de la Skill

### 1. Pilares de Evaluación (1-10)
- **Viabilidad y Cobertura**: Cubre la especificación BDD sin sobreingeniería (KISS/YAGNI).
- **Modularidad**: SOLID, DRY, alta cohesión y bajo acoplamiento.
- **Testeabilidad**: Interfaces claras, estrategia de mocks y desacoplado de I/O real.
- **Delta-First**: Reutilización de código existente y mínimo impacto.

## 📋 Reporte [`docs/review/design_reviews/[ID]-design-review.md`]

- **Veredicto**: APROBADO (media > 8, sin 🔴 CRÍTICOS y sin 🟠 ALTAS) / RECHAZADO
- **Puntuaciones**: Nota (1-10) y apunte breve por pilar.
- **Hallazgos**: Solo si existen (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA).
