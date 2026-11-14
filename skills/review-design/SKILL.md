---
name: review-design
description: Revisión independiente de decisiones de arquitectura frente a los requisitos y proporción del producto
---

# /review-design

Revisa `platform_plan.md` (o su delta de decisiones `DEC-xx`) frente a los requisitos y a `PROJECT.md` (si existe), sin entrar al código de implementación.

1. **Qué comprobar**: Que la arquitectura cubra las necesidades reales sin sobreingeniería para el tamaño del producto, mantenga límites de responsabilidad claros, permita verificar la lógica de forma aislada y no contradiga requisitos ni decisiones previas.
2. **Informe** (en la ruta indicada por quien invoca, p. ej. `platform_review.md`):
   - Primera línea: `**Veredicto:** APROBADO` (sin 🔴 ni 🟠) o `**Veredicto:** RECHAZADO`.
   - Síntesis breve y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA) solo si existen, indicando qué simplificar, aclarar o decidir.
