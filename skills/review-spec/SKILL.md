---
name: review-spec
description: Evaluación de la calidad de la especificación (escenarios BDD + evals) antes de implementar
---

# Skill: Specification Review (/review-spec)

Audita la calidad de la especificación producida en la fase de análisis — los escenarios BDD a nivel feature y los criterios de evaluación (evals) — antes de que se escriba ningún test o código. Valida que la especificación es clara, completa y testeable.

## Pasos de la Skill

### 1. Inventario de la Especificación
Listar los escenarios BDD definidos (archivos `.feature`) y los criterios de evaluación (evals) asociados a la tarea/bug. Verificar que cubren todos los componentes afectados.

### 2. Auditoría de Calidad (Spec Reviewer)
Analizar y puntuar sobre 10 siguiendo estos pilares:
* **Claridad**: Los escenarios usan lenguaje inequívoco. Cada `Dado/Cuando/Entonces` describe un estado o acción concreta, no vaga.
* **Completitud**: Los escenarios cubren el camino feliz, los casos límite y los casos de error relevantes. No hay criterios de aceptación del requisito sin un escenario que los valide.
* **Testeabilidad**: Cada escenario es verificable de forma objetiva. Los `Entonces` describen resultados observables y comprobables, no intenciones.
* **Atomicidad**: Cada escenario valida una sola cosa. No hay escenarios que mezclen múltiples comportamientos.
* **Trazabilidad**: Los escenarios referencian el requisito correspondiente (`Ref: RF-XXX`).
* **Coherencia de sistema**: Los escenarios se integran en `.feature` de sistema existentes. No hay archivos `.feature` nominales a IDs de tarea/bug.
* **Cobertura por evals**: Los criterios de evaluación complementan los BDD donde el comportamiento no es expresable como escenario Gherkin.

### 3. Generar Reporte Estandarizado
Es OBLIGATORIO generar un reporte `.md` en `docs/review/spec_reviews/` con la siguiente estructura:

#### Estructura del Reporte:
1. **Resumen Ejecutivo**: Puntuación global (0-10) y veredicto.
2. **Análisis Detallado por Área**: Por cada pilar:
   - **Puntuación**: [1-10]
   - **Explicación**: Razonamiento detallado de la nota.
   - **Puntos Fuertes**: Aciertos de la especificación.
   - **Puntos de Mejora**: Debilidades detectadas (ambigüedades, huecos, escenarios no testeables).
3. **Plan de Acción (Backlog de Revisión)**: Listado de mejoras clasificadas por criticidad:
   - **🔴 CRÍTICO**: Bloqueante (ej. criterio de aceptación sin escenario, escenario no testeable).
   - **🟠 ALTA**: Urgente (ej. caso límite relevante sin cubrir).
   - **🟡 MEDIA**: Mejora de claridad o atomicidad.
   - **🔵 BAJA**: Sugerencia de estilo o redacción.

4. **Resultado final**
Calcular una puntuación global sobre 10. Informar si la especificación está "Lista para implementar" (>8) o si requiere correcciones obligatorias antes de pasar a desarrollo.
