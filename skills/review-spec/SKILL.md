---
name: review-spec
description: Evaluación de la calidad de la especificación (escenarios BDD + evals) antes de implementar
inputs:
  - spec_file: Ruta de la especificación a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
---

# Skill: Specification Review (/review-spec)

Audita la especificación (escenarios BDD a nivel feature y evals de IA) antes de escribir código.

## 📋 Pasos de la Skill

### 1. Evalúa (1-10 por pilar)
- **Claridad**: Escenarios sin ambigüedades, `Dado/Cuando/Entonces` concretos.
- **Completitud**: Camino feliz, casos límite, errores.
- **Testeabilidad**: Resultados observables y objetivos.
- **Estructura**: Integrados en `.feature` existentes (no nominales).

### 2. Reporte [`docs/review/spec_reviews/[ID]-spec-review.md`]
- **Veredicto**: APROBADO (>8) / RECHAZADO (≤8)
- **Por Pilar**: Puntuación + nota breve.
- **Mejoras**: 🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA
