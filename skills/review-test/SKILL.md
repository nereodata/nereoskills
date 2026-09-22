---
name: review-test
description: Evaluación de calidad y cobertura de pruebas
inputs:
  - test_files: Archivos de prueba modificados o creados
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte generado
---

# Skill: Test Review (/review-test)

Audita los tests del delta para validar cobertura y calidad mediante inspección de código.

> - **Proporcionalidad:** Audita solo el delta. Ajusta la profundidad al tamaño del cambio.
> - **Inspección estática:** Revisa el código del test; **no mutes código ni hagas experimentos**.

## 📋 Pasos de la Skill

### 1. Cobertura (Determinista)
Si el runner lo permite (ej: `pytest --cov`, `npm test -- --coverage`), ejecútalo una vez sobre los tests afectados y anota el porcentaje.

### 2. Evaluación (1-10 por bloque)
- **Cobertura Funcional (BDD)**: Steps implementados con lógica real (sin no-ops ni `pass` vacíos).
- **Aserciones y Aislamiento**: Aserciones sobre valores reales (sin `assert True`); unitarios sin I/O real.
- **Integración**: Flujo punta a punta (si aplica).

## 📋 Reporte [`docs/review/test_reviews/[ID]-test-review.md`]

- **Veredicto**: APROBADO (media > 8, sin 🔴 CRÍTICOS y sin 🟠 ALTAS) / RECHAZADO
- **Cobertura**: Porcentaje numérico o "N/A".
- **Puntuaciones**: Nota (1-10) y apunte breve por bloque.
- **Hallazgos**: Solo si existen (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA).
