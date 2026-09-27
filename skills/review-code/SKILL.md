---
name: review-code
description: Realiza una revisión de código completa
inputs:
  - diff_or_files: Archivos modificados o diff a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
  - review_file: Ruta del reporte generado
---

# Skill: Code Review (/review-code)

Audita el código de producción modificado: calidad, seguridad y fidelidad al diseño aprobado. La arquitectura y la testeabilidad las evalúa `/review-design`; las pruebas, `/review-test`.

> - **Proporcionalidad:** Audita solo el delta. Ajusta la profundidad al tamaño del cambio.
> - **Alcance:** Solo código de producción (los tests van a `/review-test`). **No ejecutes pruebas**.

## 📋 Pasos de la Skill

### 1. Análisis Estático (Determinista)
Ejecuta las herramientas disponibles en el proyecto sobre los archivos modificados:
- **Linter y Estilo:** `ruff check`, `eslint`, `flake8`.
- **Tipado:** `mypy`, `pyright`, `tsc --noEmit`.
- **Secretos:** `ripsecrets`, `gitleaks` o inspección del diff (API keys, tokens, certificados).
- **Higiene Git:** `git diff --check` (conflictos residuales o whitespace corrupto).
- **Dependencias:** `npm audit` o `pip-audit` (solo si se tocan manifiestos).

> *Fallo de tipado, compilación o secreto expuesto = 🔴 CRÍTICO; fallo de linter o vulnerabilidad = 🟠 ALTA.*

### 2. Áreas de Evaluación (1-10)
1. **Seguridad**: Credenciales, inyecciones, sanitización y validación de entradas.
2. **Conformidad con Diseño**: Fidelidad al diseño aprobado (divergencias no documentadas = 🔴 CRÍTICO).
3. **Buenas Prácticas**: Estilo del proyecto, nombres limpios y resultado de linters.
4. **Eficiencia**: Complejidad algorítmica y gestión razonable de recursos.
5. **Legibilidad**: Funciones cortas, sin duplicación dentro del cambio y sin código muerto.
6. **Documentación**: Docstrings en clases/métodos públicos; sin comentarios inline superfluos.

## 📋 Reporte [`docs/review/code_reviews/[ID]-code-review.md`]

- **Veredicto**: APROBADO (media > 8, sin 🔴 CRÍTICOS y sin 🟠 ALTAS) / RECHAZADO
- **Análisis Estático**: Salida resumida de las herramientas ejecutadas o "N/A".
- **Puntuaciones**: Nota (1-10) y apunte breve de 1 línea por área.
- **Hallazgos**: Solo si existen (🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA).
