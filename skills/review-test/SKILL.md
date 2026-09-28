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

Audita los tests del delta en fase roja, antes de escribir el código de producción. Solo las pruebas: el código lo revisa `/review-code`.

> - **Proporcionalidad:** Audita solo el delta. Ajusta la profundidad al tamaño del cambio.
> - **Esfuerzo mínimo suficiente:** Haz la revisión más sencilla y rápida que dé una seguridad suficiente; no buscamos el 100 %.

## 📋 Pasos de la Skill

### 1. Comprobaciones de la fase roja
Por defecto basta con leer los tests frente al `.feature`. Ejecuta solo lo que sea rápido y aporte:
- **Casan con la spec**: ningún step sin definir ni ambiguo respecto al `.feature` (🔴 CRÍTICO). Si el runner tiene ejecución en seco, es la forma más barata de comprobarlo.
- **Fallan por el motivo correcto**: por la funcionalidad que falta, no por errores de sintaxis, imports o fixtures (🔴 CRÍTICO). Si el código ya existe y los tests pasan, anota "N/A: revisión posterior al código".
- **Mutaciones o pruebas extra**: solo si el riesgo de un falso rojo es alto y no se ve leyendo.
- **Cobertura**: si el runner la da sin coste añadido (ej: `pytest --cov`), anota el porcentaje.

### 2. Evaluación (1-10 por bloque)
- **Cobertura Funcional (BDD)**: Steps implementados con lógica real (sin no-ops ni `pass` vacíos).
- **Aserciones y Aislamiento**: Aserciones sobre valores reales (sin `assert True`); unitarios sin I/O real.
- **Integración**: Flujo punta a punta (si aplica).

## 📋 Reporte [`docs/review/test_reviews/[ID]-test-review.md`]

- **Veredicto**: APROBADO (media > 8, sin 🔴 CRÍTICOS y sin 🟠 ALTAS) / RECHAZADO
- **Ejecución**: Resultado en rojo (tests, steps sin definir, motivo del fallo) y cobertura, o "N/A".
- **Puntuaciones**: Nota (1-10) y apunte breve por bloque.
- **Hallazgos**: Solo si existen (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA).
