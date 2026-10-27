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

**Análisis estático**: quien invoca entrega lint, tipado y chequeos de seguridad aplicables al delta (secretos, `git diff --check`; auditoría de dependencias si cambian manifiestos) en limpio; si ya constan en verde en la verificación del árbol (`--verificar`), no los relances: ejecuta con `--verificar` solo lo que falte. Fallo de tipado, compilación o secreto expuesto = 🔴; linter o vulnerabilidad = 🟠.

**Formato y lint por tarea**: toma `base_calidad` del triaje y ejecuta `adevv orquestar --calidad --base <base_calidad>` sin escritura. El motor comprueba ambas etapas mediante `--verificar`, reutilizando únicamente el verde del mismo árbol y comando (base y objetivos incluidos). Un cambio posterior, incluido el formateo, exige evidencia del árbol resultante. No uses `--aplicar`, no modifiques ficheros ni pases la suite completa. Fallo de formato/lint, configuración inválida o base inexistente: hallazgo para `desarrollador`, destino `resolver`, sin aprobación hasta corregirlo. Registra las omisiones justificadas; no equivalen a una herramienta ejecutada en verde. Contrato de configuración y deducción en `/orquestar`.

**Evalúa (1-10 cada uno):**
- **Corrección**: sin errores lógicos ni precondiciones implícitas; entradas, estados y valores extremos que la especificación no cubre se tratan bien.
- **Seguridad**: credenciales, inyecciones y validación de entradas.
- **Conformidad**: fiel al triaje de la tarea, a su diseño (`docs/design/[ID]-design.md`, cuando la Subfase B no se haya omitido en el triaje; divergencia no documentada = 🔴) y a la arquitectura del plan de plataforma (capas, stack, decisiones). Desviarse de la arquitectura sin una `DEC` en el plan de plataforma dentro del mismo delta = 🔴.
- **Calidad**: estilo del proyecto, nombres claros, sin duplicación ni código muerto.
- **Eficiencia**: complejidad y uso de recursos razonables.
- **Documentación**: docstrings en la API pública, sin comentarios superfluos; ningún documento de usuario queda falso tras el delta.

## Reporte [`docs/review/code_reviews/[ID]-code-review.md`]
- **Veredicto**: APROBADO (media > 8, sin 🔴 ni 🟠) / RECHAZADO
- **Análisis estático** (resumen o N/A), **Puntuaciones** y **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA), solo si existen.
