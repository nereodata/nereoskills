---
name: review-test
description: Evaluación de la calidad de la suite de pruebas
inputs:
  - test_files: Ruta de los archivos de prueba
outputs:
  - verdict: APROBADO o RECHAZADO
---

# Skill: Test Review (/review-test)

Audita la suite de pruebas para asegurar cobertura y evitar verdes falsos.

## 📋 Pasos de la Skill

### 1. Verde Falso
- No-ops en `Entonces` (deben verificar o ser `skipped` con motivo).
- Pasos Dado/Cuando sin asserts pueden ser `pass`.

### 2. Evalúa (1-10 por bloque)
- **BDD**: Sin features huérfanas, sin no-ops, trazabilidad.
- **Unitario (Aislamiento)**: Sin red/BD/I/O real, edge cases.
- **Integración**: Flujo punta a punta (si aplica).

### 3. Reporte [`docs/review/test_reviews/[ID]-test-review.md`]
- **Veredicto**: APROBADO (>8) / RECHAZADO (≤8)
- **Por Bloque**: Puntuación + nota.
- **Mejoras**: 🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA
