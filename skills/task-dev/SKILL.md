---
name: task-dev
description: Proceso y criterios para el desarrollo completo de una tarea del backlog
---

# Skill: Desarrollo de Tarea

Conocimiento de proceso para el ciclo completo de desarrollo de una tarea, siguiendo la jerarquía **Master/Componente v3.0**.

## Modos de Ejecución

1.  **Modo Maestro (Master Mode)**:
    - Entrada: `T-[PRJ]-XXXX`
    - Analizar el plan, identificar las tareas de componente vinculadas y evaluar sus dependencias.
    - Componentes independientes (sin dependencias de código compartido) pueden ejecutarse en paralelo.
    - Componentes con dependencias: ejecutar secuencialmente en orden de dependencia.
2.  **Modo Componente (Component Mode)**:
    - Entrada: `T-[PRJ]-[COMP]-XXXX`
    - Foco exclusivo en el alcance del componente técnico.

## Fases del Desarrollo

### 1. Inicialización y Contexto
- **Validar rama de trabajo**:
  - La rama activa debe seguir el patrón `release/vX.Y` o `hotfix/vX.Y.Z`.
  - Si la rama es `main`, **abortar** con mensaje: "No se puede desarrollar directamente en main. Usa `/start-version` para crear un bloque funcional o crea una rama hotfix."
- Cargar metadatos de la tarea (ID, Weight, Version, Effort).
- Cargar la versión actual del proyecto desde `task_config.yaml` (`project.version`).
- **Coherencia de versión**: Verificar que el campo `version` de la tarea coincide con la versión de la rama activa. Si no coincide, advertir al usuario.
- Si es **Component Mode**, identificar `parent_id` para actualizar métricas globales.
- Si es **Master Mode**, cargar lista de tareas hijas pendientes y analizar dependencias entre componentes.

### 2. Gestión de Esfuerzo (Inicio)
- Confirmar `estimated_effort`.
- Establecer `remaining_effort` inicial igual al estimado si es nueva.
- **Actualización de Versión y Estado**:
    - Cambiar `status` a `in_progress`.
    - **Obligatorio**: Actualizar el campo `version` de la tarea con la versión actual de `task_config.yaml`.

### 3. Análisis y Especificación (Red Phase)
- Definir escenarios BDD en `<componente>/tests/bdd/features/`, integrándolos en un `.feature` de sistema existente.
- Crear tests unitarios en `<componente>/tests/unit/` que cubran el cambio.
- Validar calidad de tests (puntuación mínima 8/10). NO se inicia la implementación sin tests validados.
- Confirmar que los tests fallan inicialmente (Estado Rojo).
- **HITL — Validación de escenarios**: verificar que los tests capturan correctamente el requisito antes de construir la solución.

### 4. Implementación (Green Phase)
- Implementar la lógica necesaria siguiendo estándares (Docstrings obligatorios, limpieza).
- Refactorizar hasta que todos los tests creados en la fase roja pasen con éxito.
- **HITL — Validación funcional**: el usuario valida que el resultado funciona correctamente (integración visual, UX, efectos secundarios) — lo que los tests BDD/unitarios no cubren.

### 5. Revisión de Calidad (QA Phase)
- Ejecutar suite de pruebas completa para descartar regresiones.
- Revisión de código (8 áreas, puntuación mínima 8/10).
- Esta fase debe ejecutarse con evaluación objetiva, sin influencia de las decisiones tomadas durante la implementación.

### 6. Documentación y Cierre
- Generar o actualizar los documentos definidos en `docs_config.yaml`.
- Calcular `actual_effort` invertido en la sesión.
- Actualizar `remaining_effort` en el archivo de la tarea.
- Si el componente está terminado, marcar `status: completed` y asegurar que `version` coincide con la actual de `task_config.yaml`.
- Generar commit semántico estandarizado.
- Si es **Master Mode**, verificar si todos los componentes hijos están completados. Si es así, cerrar la Tarea Maestra (`completed`).
