---
name: review-code
description: Realiza una revisión de código completa
---

# Skill: Code Review (/review-code)

Este flujo (ahora skill) orquesta la revisión del código para asegurar que cumple con los estándares de calidad del proyecto.

## Pasos de la Skill

### 1. Identificar Ámbito

Determinar qué archivos o bloques de código han sido modificados o deben ser revisados.

### 2. Conformidad con el Diseño (Obligatorio, previo a puntuar)

Antes de puntuar nada, enumera cada decisión del documento de diseño y si el código la implementa.
Recorre las **dos** direcciones — la segunda es la que se escapa siempre:

* Decisiones del diseño que el código **no** implementa.
* Decisiones que el código **toma** y el diseño **no menciona**: umbrales y constantes sin criterio
  detrás, ramas de comportamiento no especificadas, reglas de negocio inventadas para hacer encajar
  dos requisitos incompatibles. Una regla que no aparece en ningún artefacto es un conflicto de
  especificación disfrazado, y es el hallazgo más caro de encontrar más tarde.

Una divergencia no declarada es 🔴 CRÍTICO con independencia de la calidad del código.

### 3. Análisis Crítico (Code Reviewer)

Analiza y puntúa (1-10) rigurosamente las siguientes áreas:

* **Seguridad (CRÍTICO)**: Manejo de credenciales, protección contra inyecciones sql/xss, validación de inputs.
* **Arquitectura**: Cumplimiento del diseño del sistema, patrones aplicados, acoplamiento y alta cohesión (los elementos de un módulo deben estar íntimamente relacionados con una única funcionalidad del negocio).
* **Buenas Prácticas / Estándares**: Sigue las guías de estilo del proyecto (PEP8, naming conventions, etc.).
* **Eficiencia**: Complejidad algorítmica y gestión de memoria/recursos.
* **Testeabilidad (CRÍTICO)**: Capacidad intrínseca del código para ser probado (Inversión de Control, modularidad, mocking). NO mide la cobertura ni la existencia de tests, sino la facilidad o dificultad técnica para escribirlos.
* **Mantenibilidad**: Código Limpio, DRY, SOLID, división de responsabilidades. Imports correctos.Penaliza la aparición de God Classes o God Methods. Cuando se cambia un módulo, clase o método se debe revisar no solo el diff sino el módulo/clase/método completo y adyacentes que puedan tener relación. Heurística de control: Como regla general, un método no debería superar las 20-30 líneas de código real, y una clase no debería gestionar más de un dominio conceptual. La violación de esta regla es un problema de severidad alta.

* **Documentación**: Presencia de docstrings obligatorios en clases y métodos. No debe haber apenas comentarios inline.
* **Cumplimiento de Requisitos**: Trazabilidad e implementación correcta de lo solicitado.

Limitar `review-code` a la testeabilidad intrínseca del código. No revisar la existencia o cobertura
de tests, repetir comprobaciones de la fase roja ni ejecutar mutation testing. Delegar la calidad
y cobertura de la suite en `review-test` y reservar mutation testing para una solicitud expresa.

### 4. Generar Reporte Estandarizado

Es OBLIGATORIO generar un archivo `.md` (usualmente en `docs/review/code_reviews/`) con la siguiente estructura:

#### Estructura del Reporte

1. **Resumen Ejecutivo**: Puntuación global y veredicto.
2. **Conformidad con el Diseño**: Resultado de las dos direcciones (decisiones no implementadas y
   decisiones no documentadas).
3. **Análisis Detallado por Área**: Por cada una de las 8 áreas anteriores:
   * **Puntuación**: [1-10]
   * **Explicación**: Razonamiento detallado de la nota.
   * **Puntos Fuertes**: Listado de aciertos técnicos.
   * **Puntos de Mejora**: Listado de debilidades detectadas.
4. **Plan de Acción (Backlog de Revisión)**: Un listado de todas las mejoras detectadas, clasificadas y ordenadas por criticidad:
   * **🔴 CRÍTICO**: Bloquea el paso a producción.
   * **🟠 ALTA**: Debería corregirse antes del merge.
   * **🟡 MEDIA**: Deuda técnica a planificar.
   * **🔵 BAJA**: Sugerencia de estilo o mejora menor.
5. **Veredicto Final**
Calcular una puntuación global sobre 10. Informar al usuario si el código es "Apto para producción" (>8) o si requiere correcciones obligatorias pre-commit basándose en los puntos críticos y la nota global.
