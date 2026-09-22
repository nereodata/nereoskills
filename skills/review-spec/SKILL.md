---
name: review-spec
description: Evaluación de la calidad de la especificación antes de implementar
inputs:
  - spec_file: Ruta de la especificación a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte generado
---

# Skill: Specification Review (/review-spec)

Audita la especificación funcional (escenarios BDD y evals de IA) antes de codificar.

> - **Proporcionalidad:** Audita solo el delta funcional. Ajusta la profundidad al cambio.
> - **Ámbito:** Revisa archivos `.feature` y evals. **No ejecutes código ni pruebas**.

## 📋 Pasos de la Skill

### 1. Comprobaciones Obligatorias (Pasa / Falla)
Si alguna falla, es 🔴 CRÍTICO:
- **No regresión**: No se eliminan ni alteran escenarios preexistentes en los `.feature`.
- **Sin contradicciones**: Coherente con decisiones de diseño y contratos vigentes.
- **Trazabilidad**: Etiquetas (`@CA-*`) corresponden a criterios reales de la tarea/bug.
- **Delta real**: Describe un comportamiento nuevo o modificado (sin duplicados).

### 2. Pilares de Evaluación (1-10)
- **Claridad**: `Dado/Cuando/Entonces` concisos, inequívocos y orientados al usuario.
- **Completitud**: Camino feliz, casos límite y errores principales.
- **Testeabilidad**: Resultados observables con contenido y valores concretos.
- **Estructura**: Integrados en `.feature` funcionales (nunca por tarea ni por fase).

## 📋 Reporte [`docs/review/spec_reviews/[ID]-spec-review.md`]

- **Veredicto**: APROBADO (media > 8, sin 🔴 CRÍTICOS y sin 🟠 ALTAS) / RECHAZADO
- **Comprobaciones Obligatorias**: Lista con estado (✅ OK / ❌ Fallo + motivo).
- **Puntuaciones**: Nota (1-10) y apunte breve por pilar.
- **Hallazgos**: Solo si existen (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA).
