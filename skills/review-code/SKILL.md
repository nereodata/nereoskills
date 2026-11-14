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

Audita post-verde y en una sola pasada tanto el código de producción del delta (incluidos build, CI y configuración) como las pruebas directas que lo respaldan (`PROJECT.md` §3). Haz la revisión más sencilla y rápida que dé una seguridad razonable de que no se escapa ningún problema 🔴 o 🟠; los 🟡/🔵 se señalan si se ven, sin buscarlos a fondo. Calidad suficiente y agilidad, no perfección ceremonial.

**Análisis estático**: quien invoca entrega lint, tipado y chequeos de seguridad aplicables al delta (secretos, `git diff --check`; auditoría de dependencias si cambian manifiestos) en limpio; si ya constan en verde en la verificación del árbol (`--verificar`), no los relances: ejecuta con `--verificar` solo lo que falte. Fallo de tipado, compilación o secreto expuesto = 🔴; linter o vulnerabilidad = 🟠.

**Formato y lint por tarea**: toma `base_calidad` de la ficha o mandato y ejecuta `adevv orquestar --calidad --base <base_calidad>` sin escritura. El motor comprueba ambas etapas mediante `--verificar`, reutilizando únicamente el verde del mismo árbol y comando (base y objetivos incluidos). Un cambio posterior, incluido el formateo, exige evidencia del árbol resultante. No uses `--aplicar`, no modifiques ficheros ni pases la suite completa. Fallo de formato/lint, configuración inválida o base inexistente: hallazgo para `desarrollador`, destino `resolver`, sin aprobación hasta corregirlo. Registra las omisiones justificadas; no equivalen a una herramienta ejecutada en verde. Contrato de configuración y deducción en `/orquestar`.

**Evalúa (1-10 cada uno):**
- **Corrección y pruebas**: sin errores lógicos ni regresiones; pruebas ejecutables directas en verde que cubren el comportamiento esencial sin falsos verdes ni efectos laterales externos.
- **Seguridad**: credenciales, inyecciones, permisos y validación de entradas.
- **Conformidad**: fiel al objetivo de la ficha, a `PROJECT.md` y a las decisiones de plataforma aplicables (`docs/design/[ID]-design.md` es opcional y solo aplica si el agente decidió crearlo).
- **Calidad**: estilo del proyecto, nombres claros, modularidad razonable, sin duplicación grave ni código muerto.
- **Eficiencia**: complejidad y uso de recursos razonables.
- **Documentación**: docstrings esenciales en API pública y coherencia con documentos de usuario afectados.

## Reporte [`docs/review/code_reviews/[ID]-code-review.md`]
- **Veredicto**: `**Veredicto:** APROBADO` (media > 8, sin 🔴 ni 🟠) o `**Veredicto:** RECHAZADO`, seguido inmediatamente de `Producto revisado: <huella>`.
- **Análisis estático** (resumen o N/A), **Puntuaciones** y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA), solo si existen.
