---
name: review-code
description: Revisión del código de producción del delta, de su corrección y de su conformidad con el diseño de la tarea y la arquitectura
inputs:
  - diff_or_files: Archivos modificados o diff a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte generado
---

# Skill: Code Review (/review-code)

Audita solo el código de producción del delta: todo lo que no es prueba, incluidos build, CI y configuración (las pruebas las revisa `/review-test`; la arquitectura, `/review-design`). Haz la revisión más sencilla y rápida que dé una seguridad razonable de que no se escapa ningún problema 🔴 o 🟠; los 🟡/🔵 se señalan si se ven, sin buscarlos a fondo. Calidad, no perfección.

**Análisis estático**: quien invoca entrega lint y tipado limpios sobre el delta; compruébalo con las herramientas que ya tenga el proyecto (linter, tipado, secretos, `git diff --check`; auditoría de dependencias solo si cambian los manifiestos). Fallo de tipado, compilación o secreto expuesto = 🔴; linter o vulnerabilidad = 🟠.

**Evalúa (1-10 cada uno):**
- **Corrección**: sin errores lógicos ni precondiciones implícitas; entradas, estados y valores extremos que la especificación no cubre se tratan bien.
- **Seguridad**: credenciales, inyecciones y validación de entradas.
- **Conformidad**: fiel al diseño de la tarea (`docs/design/[ID]-design.md`; divergencia no documentada = 🔴) y a la arquitectura del plan de plataforma (capas, stack, decisiones). Desviarse de la arquitectura sin una `DEC` en el plan de plataforma dentro del mismo delta = 🔴.
- **Calidad**: estilo del proyecto, nombres claros, sin duplicación ni código muerto.
- **Eficiencia**: complejidad y uso de recursos razonables.
- **Documentación**: docstrings en la API pública, sin comentarios superfluos; ningún documento de usuario queda falso tras el delta.

## Reporte [`docs/review/code_reviews/[ID]-code-review.md`]
- **Veredicto**: APROBADO (media > 8, sin 🔴 ni 🟠) / RECHAZADO
- **Análisis estático** (resumen o N/A), **Puntuaciones** y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA), solo si existen.
