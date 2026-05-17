---
name: bug-fix
description: Ciclo completo para la resolución de anomalías (bugs) detectadas.
---

# Skill: Resolución de Anomalías (/bug-fix)

Este flujo orquesta la resolución de bugs, soportando la jerarquía **Master/Componente v3.0**.

## Modos de Ejecución

1. **Modo Maestro (Master Fix)**:
    - Entrada: `B-[PRJ]-XXXX`
    - El AI analiza todos los componentes afectados por el bug maestro y aplica las correcciones secuencialmente.
2. **Modo Componente (Componente Fix)**:
    - Entrada: `B-[PRJ]-[COMP]-XXXX`
    - Foco exclusivo en la corrección técnica de un componente.

## Pasos de la Skill

### 0. Clasificación de Urgencia y Rama de Trabajo

- Preguntar al usuario: **"¿Este bug es urgente y necesita llegar a producción inmediatamente (hotfix), o puede resolverse dentro del bloque funcional actual (release)?"**
- **Si hotfix**:
  - Identificar la versión de producción afectada (último tag en `main`).
  - Calcular la versión patch: si el último tag es `vX.Y.Z`, la rama será `hotfix/vX.Y.(Z+1)`.
  - Crear la rama desde el tag: `git checkout -b hotfix/vX.Y.Z vX.Y.(Z-1)` (o el tag correspondiente).
  - Actualizar la versión en los manifiestos al patch correspondiente.
  - Commit inicial: `chore(hotfix): start hotfix vX.Y.Z`
- **Si no urgente**:
  - Verificar que la rama activa es `release/vX.Y`.
  - Si no lo es, advertir al usuario y sugerir cambiar a la rama release activa.
- En ambos casos, actualizar el campo `version` del bug con la versión de la rama de trabajo.

### 1. Reproducción y Esfuerzo

- Cargar metadatos del bug y la versión actual de `task_config.yaml` (`project.version`).
- **Actualización de Estado**: Cambiar el `status` a `in_progress`. (La versión ya fue asignada en el paso 0.)
- Establecer `actual_effort` y actualizar `remaining_effort`.
- **Fase de Pruebas**: Crear/actualizar pruebas que capturen el fallo.
  - **BDD**: Integrar el escenario en un `.feature` de sistema existente, evaluando el comportamiento funcional de lo que debe hacer la app (aplica a cualquier proyecto). No crear archivos `.feature` nominales al bug o ID de tarea, y reutiliar en la medida de lo posible los existentes.
  - **Evals (Solo proyectos y consultas IA)**: Valorar la necesidad de añadir/modificar *evals* para garantizar que los prompts se responden adecuadamente por los modelos seleccionados frente a este caso de uso.
  - Crear/actualizar Unit Tests que cubran el cambio técnico.
- **Human in the loop**: Solicitar confirmación del usuario antes de continuar. En este HITL deben validarse los escenarios BDD y, si aplica, los evals.

### 2. Desarrollo (Fix)

- Implementar la corrección siguiendo estándares (Docstrings obligatorios, no comentarios inline).
- Verificar que los tests pasan.

### 3. Fase de Verificación (QA)

- Ejecutar el proceso de revisión de corrección (`review-fix` logic) usando el skill `bug-fix-reviewer`.
- Validar que no hay regresiones.
- **Human in the loop**: Solicitar confirmación del usuario antes de continuar.

### 4. Cierre y Documentación

- Documentar la solución y actualizar métricas de esfuerzo en el archivo de backlog.
- **Estado final**: Marcar `status: completed` y asegurar que `version` coincide con la actual de `task_config.yaml`.
- Ejecutar la actualización de documentación del proyecto a través de `/manage-docs`.
- Si es **Master Fix**, verificar si otros componentes requieren correcciones para el mismo problema.

### 5. Persistencia

- Realizar los cambios y preparar para hacer commit con el prefijo `fix([ID])` (puedes apoyarte en la skill `commit`).
