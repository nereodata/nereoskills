---
name: task-dev
description: Ciclo de desarrollo completo para una tarea del backlog (BDD -> TDD -> Dev -> QA -> Doc)
---

# Skill: Desarrollo de Tarea (/task-dev)

Este flujo (ahora skill) orquesta el ciclo completo de desarrollo de una tarea, soportando la jerarquía **Master/Componente v3.0**.

## Modos de Ejecución

1.  **Modo Maestro (Master Mode)**:
    - Entrada: `T-[PRJ]-XXXX`
    - Comportamiento: El AI analiza el plan, identifica todas las tareas de componente vinculadas y las ejecuta secuencialmente.
2.  **Modo Componente (Component Mode)**:
    - Entrada: `T-[PRJ]-[COMP]-XXXX`
    - Comportamiento: El AI se enfoca exclusivamente en el alcance del componente técnico.

## Workflow Completo

### 1. Inicialización y Contexto
- **Validar rama de trabajo**:
  - La rama activa debe seguir el patrón `release/vX.Y` o `hotfix/vX.Y.Z`.
  - Si la rama es `main`, **abortar** con mensaje: "No se puede desarrollar directamente en main. Usa `/start-version` para crear un bloque funcional o crea una rama hotfix."
- Cargar metadatos de la tarea (ID, Weight, Version, Effort).
- Cargar la versión actual del proyecto desde `task_config.yaml` (`project.version`).
- **Coherencia de versión**: Verificar que el campo `version` de la tarea (si ya tiene uno asignado) coincide con la versión de la rama activa. Si no coincide, advertir al usuario.
- Si es **Component Mode**, identificar `parent_id` para actualizar métricas globales.
- Si es **Master Mode**, cargar lista de tareas hijas pendientes.

### 2. Gestión de Esfuerzo (Inicio)
- Confirmar `estimated_effort`.
- Establecer `remaining_effort` inicial igual al estimado si es nueva.
- **Actualización de Versión y Estado**: 
    - Cambiar `status` a `in_progress` (en curso).
    - **Obligatorio**: Actualizar el campo `version` de la tarea con la versión actual de `task_config.yaml`.

### 3. Ciclo de Desarrollo Técnico (Por cada Componente)
Para cada componente afectado (secuencialmente en Master Mode, o el único en Component Mode):

#### 3.1 Fase BDD/TDD (Red Phase - Automatizada)
- Definir escenarios en `<componente>/tests/bdd/features/` integrándolos en un `.feature` de sistema existente.
- Crear tests unitarios en `<componente>/tests/unit/` que cubran el cambio.
- **Validación Automatizada**: Ejecutar el bucle de autocorrección en fase roja:
  ```bash
  python .agents/scripts/auto_dev_loop.py --phase red --test-cmd "<comando-de-test>" --cwd "<ruta-componente>"
  ```
  - Si el script reporta éxito, los tests fallan correctamente y se puede proceder a la fase de codificación.
  - Si el script falla, leer el informe generado en `.agents/scratch/qa_feedback.md`, corregir los escenarios y re-ejecutar.
  - **Human-in-the-loop**: Solicitar confirmación al usuario únicamente si los tests pasan directamente sin codificación, lo que indica un diseño de test incorrecto.

#### 3.2 Fase de Desarrollo y Calidad (Green & QA Phase - Bucle de Autocorrección Cerrado)
- Implementar la lógica necesaria siguiendo estándares (Docstrings obligatorios, modularidad, DRY).
- **Bucle de Autocorrección Cerrado (Self-Correction Loop)**: Ejecutar el orquestador de validación de calidad local en segundo plano:
  ```bash
  python .agents/scripts/auto_dev_loop.py --phase green --test-cmd "<comando-de-test>" --cwd "<ruta-componente>" --lint-cmd "<comando-linter>" --typecheck-cmd "<comando-typecheck>"
  ```
  - **En caso de fallo (Exit 1)**: Leer los errores estructurados de tests, linting o tipo en `.agents/scratch/qa_feedback.md`. El subagente Coder debe corregir el código basándose en el feedback de forma autónoma (hasta un máximo de 3 intentos).
  - **En caso de éxito (Exit 0)**: Se garantiza que los tests pasan y que no hay regresiones de linter o tipos.
  - **Human-in-the-loop**: Si después de 3 intentos de autocorrección el script sigue fallando, abortar, escribir la causa en `.agents/scratch/blocked_reason.md` y notificar al programador humano solicitando asistencia.

#### 3.4 Sincronización de Diseño (Sync Phase)
- Revisar si el código altera el diseño técnico macro.
- Generar o actualizar los documentos definidos en `docs_config.yaml` usando la skill `/manage-docs`, asegurando un enfoque minimalista y útil.

### 4. Actualización de Métricas y Esfuerzo
**Al completar una sesión o el total de un componente:**
- Calcular `actual_effort` invertido en la sesión.
- Actualizar `remaining_effort` en el archivo de la tarea (estimación de lo que falta).
- Si el componente está terminado, marcar `status: completed` y asegurar que `version` coincide con la actual de `task_config.yaml`.

### 5. Finalización y Commit
- Generar un commit message estandarizado (usando lógica de `/commit`).
- Si es **Master Mode**, verificar si todos los componentes hijos están completados. Si es así, cerrar la Tarea Maestra (`completed`).

