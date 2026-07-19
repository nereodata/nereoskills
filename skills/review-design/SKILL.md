---
name: review-design
description: Auditoría del plan de diseño técnico para garantizar la calidad arquitectónica y testeabilidad.
inputs:
  - design_file: Ruta del documento de diseño técnico a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte de revisión de diseño generado
---

# Skill: Review Design (/review-design)

Audita la propuesta de diseño técnico antes de escribir código. Garantiza la calidad de la arquitectura, la adherencia a buenas prácticas y la viabilidad de pruebas.

## 📋 Pasos

### 1. Evalúa (1-10 por pilar)
- **Viabilidad**: Cubre BDD, sin complejidad innecesaria (KISS/YAGNI).
- **Modularidad**: SOLID, DRY, cohesión alta, acoplamiento bajo.
- **Testeabilidad**: Interfaces claras, mocks definidos, sin I/O real.
- **Delta-First**: Reutiliza código existente, consistencia.

### 2. Reporte [`docs/review/design_reviews/[ID]-design-review.md`]
- **Veredicto**: APROBADO (>8) / RECHAZADO (≤8)
- **Por Pilar**: Puntuación + nota.
- **Mejoras**: 🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA
