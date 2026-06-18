---
name: review-code
description: Realiza una revisión de código completa
---

# Skill: Code Review (/review-code)

Este flujo (ahora skill) orquesta la revisión del código para asegurar que cumple con los estándares de calidad del proyecto.

## Pasos de la Skill

### 1. Identificar Ámbito

Determinar qué archivos o bloques de código han sido modificados o deben ser revisados.

### 2. Análisis Crítico (Code Reviewer)

Analiza y puntúa (1-10) rigurosamente las siguientes áreas:

* **Seguridad (CRÍTICO)**: Manejo de credenciales, protección contra inyecciones sql/xss, validación de inputs.
* **Arquitectura**: Cumplimiento del diseño del sistema, patrones aplicados, acoplamiento y alta cohesión (los elementos de un módulo deben estar íntimamente relacionados con una única funcionalidad del negocio).
* **Buenas Prácticas / Estándares**: Sigue las guías de estilo del proyecto (PEP8, naming conventions, etc.).
* **Eficiencia**: Complejidad algorítmica y gestión de memoria/recursos.
* **Testeabilidad (CRÍTICO)**: Capacidad intrínseca del código para ser probado (Inversión de Control, modularidad, mocking). NO mide la cobertura ni la existencia de tests, sino la facilidad o dificultad técnica para escribirlos.
* **Mantenibilidad**: Código Limpio, DRY, SOLID, división de responsabilidades. Imports correctos.Penaliza la aparición de God Classes o God Methods. Cuando se cambia un módulo, clase o método se debe revisar no solo el diff sino el módulo/clase/método completo y adyacentes que puedan tener relación. Heurística de control: Como regla general, un método no debería superar las 20-30 líneas de código real, y una clase no debería gestionar más de un dominio conceptual. La violación de esta regla es un problema de severidad alta.

* **Documentación**: Presencia de docstrings obligatorios en clases y métodos. No debe haber apenas comentarios inline.
* **Cumplimiento de Requisitos**: Trazabilidad e implementación correcta de lo solicitado.

### 3. Generar Reporte Estandarizado

Es OBLIGATORIO generar un archivo `.md` (usualmente en `docs/review/code_reviews/`) con la siguiente estructura:

#### Estructura del Reporte

1. **Resumen Ejecutivo**: Puntuación global y veredicto.
2. **Análisis Detallado por Área**: Por cada una de las 8 áreas anteriores:
   * **Puntuación**: [1-10]
   * **Explicación**: Razonamiento detallado de la nota.
   * **Puntos Fuertes**: Listado de aciertos técnicos.
   * **Puntos de Mejora**: Listado de debilidades detectadas.
3. **Plan de Acción (Backlog de Revisión)**: Un listado de todas las mejoras detectadas, clasificadas y ordenadas por criticidad:
   * **🔴 CRÍTICO**: Bloquea el paso a producción.
   * **🟠 ALTA**: Debería corregirse antes del merge.
   * **🟡 MEDIA**: Deuda técnica a planificar.
   * **🔵 BAJA**: Sugerencia de estilo o mejora menor.
4. **Veredicto Final**
Calcular una puntuación global sobre 10. Informar al usuario si el código es "Apto para producción" (>8) o si requiere correcciones obligatorias pre-commit basándose en los puntos críticos y la nota global.
