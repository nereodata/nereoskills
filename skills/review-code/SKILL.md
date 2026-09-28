---
name: review-code
description: Revisión del código de producción del delta
inputs:
  - diff_or_files: Archivos modificados o diff a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte generado
---

# Skill: Code Review (/review-code)

Audita solo el código de producción del delta (la arquitectura la revisa `/review-design`; las pruebas, `/review-test`). Haz la revisión más sencilla y rápida que dé una seguridad razonable de que no se escapa ningún problema 🔴 o 🟠; los 🟡/🔵 se señalan si se ven, sin buscarlos a fondo. Calidad, no perfección.

**Análisis estático**: ejecuta sobre lo modificado las herramientas que ya tenga el proyecto (linter, tipado, secretos, `git diff --check`; auditoría de dependencias solo si cambian los manifiestos). Fallo de tipado, compilación o secreto expuesto = 🔴; linter o vulnerabilidad = 🟠.

**Evalúa (1-10 cada uno):**
- **Seguridad**: credenciales, inyecciones y validación de entradas.
- **Conformidad con el diseño**: fiel al diseño aprobado (divergencia no documentada = 🔴).
- **Calidad**: estilo del proyecto, nombres claros, sin duplicación ni código muerto.
- **Eficiencia**: complejidad y uso de recursos razonables.
- **Documentación**: docstrings en la API pública, sin comentarios superfluos.

## Reporte [`docs/review/code_reviews/[ID]-code-review.md`]
- **Veredicto**: APROBADO (media > 8, sin 🔴 ni 🟠) / RECHAZADO
- **Análisis estático** (resumen o N/A), **Puntuaciones** y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA), solo si existen.
