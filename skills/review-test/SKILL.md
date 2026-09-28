---
name: review-test
description: Revisión de las pruebas del delta, sin tener en cuenta el código
inputs:
  - test_files: Archivos de prueba modificados o creados
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte generado
---

# Skill: Test Review (/review-test)

Audita solo las pruebas del delta, como si el código no existiera: si especifican bien el comportamiento, no si pasan (el código lo revisa `/review-code`). Haz la revisión más sencilla que dé una seguridad suficiente: no buscamos el 100 %.

**Evalúa (1-10 cada uno):**
- **Cobertura**: cubren los escenarios del `.feature` y sus casos relevantes; los steps casan con el texto.
- **Aserciones**: comprueban comportamiento real, no la mera ejecución.
- **Rojo correcto**: fallarían sin la funcionalidad, por ella y no por sintaxis, imports o fixtures.

## Reporte [`docs/review/test_reviews/[ID]-test-review.md`]
- **Veredicto**: APROBADO (media > 8, sin 🔴 ni 🟠) / RECHAZADO
- **Puntuaciones** y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA), solo si existen.
