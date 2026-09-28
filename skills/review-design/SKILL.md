---
name: review-design
description: Revisión del documento de diseño técnico frente a la especificación y el código existente
inputs:
  - design_file: Ruta del documento de diseño técnico a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte de revisión de diseño generado
---

# Skill: Review Design (/review-design)

Audita solo el documento de diseño del delta, frente a la especificación y al código existente, antes de implementar (la implementación la revisa `/review-code`). Haz la revisión más sencilla y rápida que dé una seguridad razonable de que no se escapa ningún problema 🔴 o 🟠; los 🟡/🔵 se señalan si se ven, sin buscarlos a fondo. Calidad, no perfección.

**Evalúa (1-10 cada uno):**
- **Viabilidad y cobertura**: cubre la especificación sin sobreingeniería para el tamaño del producto.
- **Modularidad**: alta cohesión, bajo acoplamiento, una regla en un solo sitio.
- **Testeabilidad**: interfaces claras y lógica aislable de la E/S.
- **Delta-first**: reutiliza lo existente con el mínimo impacto. Si cambia un contrato, el mapa de impacto está completo (llamantes, tests afectados, decisiones contradichas).

## Reporte [`docs/review/design_reviews/[ID]-design-review.md`]
- **Veredicto**: APROBADO (media > 8, sin 🔴 ni 🟠) / RECHAZADO
- **Puntuaciones** y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA), solo si existen.
