---
name: review-design
description: Revisión de la arquitectura (plan de plataforma y sus decisiones) frente a los requisitos; nunca mira código ni diseños de tarea
inputs:
  - design_file: Plan de plataforma, o su delta (decisiones de arquitectura nuevas o cambiadas)
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte de revisión generado
---

# Skill: Review Design (/review-design)

Audita solo la arquitectura: `platform_plan.md` y sus decisiones (`DEC-xx`), frente a los requisitos. Nunca mira el código ni los diseños de tarea (`docs/design/[ID]-design.md`): que el código sea correcto y siga el diseño y la arquitectura lo revisa `/review-code`. Haz la revisión más sencilla y rápida que dé una seguridad razonable de que no se escapa ningún problema 🔴 o 🟠; los 🟡/🔵 se señalan si se ven, sin buscarlos a fondo. Calidad, no perfección.

Sobre un delta (decisiones nuevas o cambiadas), juzga solo ese delta y su encaje con el resto del plan.

**Evalúa (1-10 cada uno):**
- **Cobertura**: cubre los requisitos funcionales y las necesidades que condicionan, con cifras con base o supuestos declarados.
- **Proporción**: sin sobreingeniería para el tamaño del producto; cada componente responde a una necesidad.
- **Estructura**: capas y responsabilidades claras, dependencias en un solo sentido, reglas de capa que se puedan comprobar.
- **Testeabilidad**: la estrategia de pruebas cubre los niveles necesarios y la lógica queda aislable de la E/S.
- **Coherencia**: las decisiones no se contradicen entre sí ni con los requisitos.

## Reporte
Ruta: la que indique quien invoca (p. ej. `platform_review.md` o la revisión de versión).
- **Veredicto**: APROBADO (media > 8, sin 🔴 ni 🟠) / RECHAZADO
- **Puntuaciones** y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA), solo si existen.
