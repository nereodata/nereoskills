---
name: review-spec
description: Revisión de la especificación del delta (escenarios BDD y evals), sin tener en cuenta el diseño ni el código
inputs:
  - spec_file: Ruta de la especificación a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte generado
---

# Skill: Specification Review (/review-spec)

Audita solo la especificación del delta (`.feature` y evals), como si el diseño y el código no existieran: si describe bien el comportamiento, no cómo se implementa. Haz la revisión más sencilla y rápida que dé una seguridad razonable de que no se escapa ningún problema 🔴 o 🟠; los 🟡/🔵 se señalan si se ven, sin buscarlos a fondo. Calidad, no perfección.

**Obligatorias (si falla alguna, 🔴 CRÍTICO):**
- **No regresión**: no elimina ni altera escenarios existentes.
- **Coherencia**: no contradice decisiones ni contratos ya documentados.
- **Trazabilidad**: cada `@CA-*` existe en la tarea o bug de origen.
- **Delta real**: describe comportamiento nuevo o modificado, sin duplicados.

**Evalúa (1-10 cada uno):**
- **Claridad**: inequívoca y orientada al usuario.
- **Completitud**: camino feliz, límites y errores relevantes.
- **Testeabilidad**: resultados observables con valores concretos.
- **Estructura**: en el `.feature` de su funcionalidad, nunca por tarea, fase o versión.

## Reporte [`docs/review/spec_reviews/[ID]-spec-review.md`]
- **Veredicto**: APROBADO (media > 8, sin 🔴 ni 🟠) / RECHAZADO
- **Obligatorias** (✅ / ❌ + motivo), **Puntuaciones** y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA), solo si existen.
