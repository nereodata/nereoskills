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

Audita solo las pruebas del delta, como si el código no existiera: si especifican bien el comportamiento, no si pasan (el código lo revisa `/review-code`). Incluye cómo se preparan los datos y estados de cada prueba. Quien invoca entrega lint y tipado limpios sobre las pruebas y la salida de la ejecución en rojo. Haz la revisión más sencilla y rápida que dé una seguridad razonable de que no se escapa ningún problema 🔴 o 🟠; los 🟡/🔵 se señalan si se ven, sin buscarlos a fondo. Calidad, no perfección.

**Evalúa (1-10 cada uno):**
- **Cobertura**: cubren los escenarios del `.feature` y sus casos relevantes; los steps casan con el texto.
- **Aserciones**: comprueban comportamiento real, no la mera ejecución; ninguna se cumple por construcción.
- **Rojo correcto**: fallarían sin la funcionalidad, por ella y no por sintaxis, imports o fixtures.
- **Estabilidad**: deterministas; no dependen del tiempo real, del orden de ejecución ni del entorno.

## Reporte [`docs/review/test_reviews/[ID]-test-review.md`]
- **Veredicto**: APROBADO (media > 8, sin 🔴 ni 🟠) / RECHAZADO
- **Puntuaciones** y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA), solo si existen.
