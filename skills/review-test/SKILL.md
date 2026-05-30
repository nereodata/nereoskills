---
name: review-test
description: Evaluación de la calidad de la suite de pruebas
---

# Skill: Test Review (/review-test)

Este flujo (ahora skill) audita la suite de pruebas completa y valora su calidad y completitud, alertando si hay deficiencias.

## Pasos de la Skill

### 1. Inventario de Pruebas
Listar todos los archivos `.feature` de la carpeta de features y compararlos con los archivos `test_*.py` de tests (BDD y unitarios) existentes en el código.

### 2. Verificación de Implementación
Confirmar que NO existen features huérfanas (archivos feature sin tests que los implementen) y que todos los escenarios tienen sus Step Definitions implementados.

**Detección de verde falso**: revisar el *cuerpo* de cada step definition, no solo su existencia. El riesgo es un paso que **debería verificar algo pero pasa en silencio** sin comprobarlo.

- **Pasos de narrativa / contexto** (típicamente `Dado`/`Given` que solo preparan o ambientan, sin un resultado verificable): pueden quedar como `pass` o incluso vacíos. Es normal y legítimo; no requieren acción.
- **Pasos cuya verificación se omite deliberadamente** por ser compleja o frágil de implementar: NO deben quedar como `pass` mudo (aparentarían validar). Deben marcarse **explícitamente como `skipped` con su explicación** (ej. `pytest.skip("motivo")`), conservando el escenario BDD como requisito documentado y dejando constancia visible de que no se está verificando.
- **Red flag a penalizar**: un paso que por su redacción implica una comprobación (p. ej. un `Entonces`/`Then` que asevera un resultado) implementado como no-op que pasa, sin asserts y sin estar `skipped`.

### 3. Auditoría de Calidad (Test Reviewer)
Analizar y puntuar sobre 10 siguiendo estos tres pilares:
* **Bloque BDD (Contrato de Negocio)**:
  - Penalizar severamente (-5 puntos) si hay *features* huérfanas o escenarios sin steps.
  - Penalizar severamente los **pasos que deberían verificar y pasan en silencio** (p. ej. un `Entonces` sin asserts ni efectos y sin estar `skipped`): son verdes falsos. Exigir que se conviertan en comprobación real, o en `skipped` con explicación si su verificación se pospone por complejidad/fragilidad. Los pasos de narrativa/contexto sin valor verificable pueden quedar como `pass` y no se penalizan.
  - Asegurar uso correcto del runner (ej. `pytest-bdd`) y evitar llamadas a runners obsoletos.
  - Trazabilidad con tags de requisitos (`@RF-XXX`).
* **Bloque Unitario (Aislamiento técnico)**:
  - **Pureza**: Garantizar que NO hay accesos directos a BD, red o I/O real (usar mocks y fixtures de pytest).
  - Exigir cobertura *Edge* (casos excepcionales, nulos, asertos negativos).
* **Bloque de Integración (Flujo Real)**:
  - Validar testing del ciclo completo (ej. API -> Base de Datos) y persistencia real de los datos.

### 4. Generar Reporte Estandarizado
Es OBLIGATORIO generar un reporte `.md` en `docs/review/test_reviews/` con la siguiente estructura:

#### Estructura del Reporte:
1. **Resumen Ejecutivo**: Puntuación global (0-10) y veredicto.
2. **Análisis Detallado por Área**: Por cada bloque (BDD, Unitario e Integración):
   - **Puntuación**: [1-10]
   - **Explicación**: Razonamiento detallado de la nota. (En BDD mencionar Features Huérfanas).
   - **Puntos Fuertes**: Listado de aciertos en la implementación de pruebas.
   - **Puntos de Mejora**: Listado de debilidades detectadas.
3. **Plan de Acción (Backlog de Revisión)**: Un listado de todas las mejoras detectadas, clasificadas y ordenadas por criticidad:
   - **🔴 CRÍTICO**: Bloqueante (ej. features huérfanas, pasos no-op con verde falso, fallos graves de aislamiento).
   - **🟠 ALTA**: Urgente (ej. falta de tests edge cases críticos).
   - **🟡 MEDIA**: Deuda técnica (ej. refactorización de fixtures).
   - **🔵 BAJA**: Mejora menor (ej. nombres de tests más claros).

4. **Resultado final**
Calcular una puntuación global sobre 10. Informar al usuario si el código es "Apto para producción" (>8) o si requiere correcciones obligatorias pre-commit basándose en los puntos críticos y la nota global.


