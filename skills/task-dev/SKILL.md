---
name: task-dev
description: Ciclo de desarrollo completo de una tarea (BDD -> Diseño -> TDD -> Dev -> QA -> Doc)
inputs:
  - task_id: ID de la tarea (T-PRJ-XXXX o T-PRJ-COMP-XXXX)
outputs:
  - status: completed
  - version: versión del bloque funcional asociada a la tarea
prerequisites:
  - git_status: limpio (sin cambios no commiteados)
  - branch: release/vX.Y o hotfix/vX.Y.Z activa
dependencies:
  - generate-bdd
  - review-spec
  - design
  - review-design
  - review-test
  - review-code
  - manage-docs
  - commit
---

# Skill: Desarrollo de Tarea (/task-dev)

Playbook para el desarrollo de tareas.

## 1. Inicialización (inline)
- **Validar Rama**: Debe ser `release/vX.Y` o `hotfix/vX.Y.Z`. Abortar si es `main`.
- **Cargar Metadatos**: Cargar tarea padre e hijas (componentes).
- **Coherencia**: Validar que la versión en la tarea coincide con la de la rama activa.
- **Estado**: Cambiar `status` a `in_progress` en padre e hijas. Establecer `estimated_effort` y `remaining_effort`.

## 2. Triaje de Alcance (inline)
**Filosofía Delta-First**: Inspecciona si la funcionalidad ya existe antes de codificar. Analiza el cambio y determina qué subfases **realmente aportan valor** (no todas aplican).

Crea un checklist explícito en `task.md` marcando qué subfases ejecutar:
- **Subfase A: Definición** (Cambio de comportamiento BDD) → `[EXEC]` o `[SKIP]`?
- **Subfase B: Diseño** (Cambio técnico estructurado) → `[EXEC]` o `[SKIP]`?
- **Subfase C: Desarrollo** (Cambio en código/tests) → `[EXEC]` o `[SKIP]`?
- **Subfase D: QA** (Revisión de código y validación funcional) → `[EXEC]` o `[SKIP]`?
- **Subfase E: Documentación** (Cambio en manuales/diseño técnico) → `[EXEC]` o `[SKIP]`?
- **Subfase F: Cierre** (Commit y cierre de tarea) → `[EXEC]` (siempre)

**Criterio**: Ejecuta una subfase solo si produce cambios reales y aporta valor. Omite subfases que no aplican al tipo de cambio.

## 3. Fase de Implementación (secuencial)

### Subfase A: Definición [EXEC/SKIP]
1. `/generate-bdd`: Escenarios BDD en español → `.feature` existentes (no nominales).
2. Evals: Golden Tests en Gherkin (aislados).
3. `Hades /review-spec` (aislado, ×3 iteraciones máx).
4. **HITL**: Validar especificación consolidada.

### Subfase B: Diseño [EXEC/SKIP]
1. `/design`: Analizar código existente → cambios (`[NEW]`, `[MODIFY]`, `[DELETE]`), SOLID/DRY/KISS/YAGNI, coherencia.
   - Output: `docs/design/[ID]-design.md`.
2. `Hades /review-design` (aislado, ×3 iteraciones máx).
3. **HITL (Opcional)**: Validar diseño.

### Subfase C: Desarrollo [EXEC/SKIP]
**Red Phase:**
1. Step defs + unit tests → `tests/unit/`.
2. Verificar que fallan (solo tests relevantes).
3. `Hades /review-test` (aislado, ×3 iteraciones máx).

**Green Phase:**
1. Implementación mínima (docstrings sí, inline comments no).
2. Tests relevantes + suite completa al final.

### Subfase D: QA [EXEC/SKIP]
1. `Hades /review-code` (aislado, ×3 iteraciones máx).
2. **HITL**: Validar funcionalidad e integración visual.

### Subfase E: Documentación [EXEC/SKIP]
- `/manage-docs`: Actualizar según `docs_config.yaml` (minimalista, inline).

### Subfase F: Cierre [EXEC]
1. `/commit`: Commit semántico (inline).
2. Cierre: Esfuerzos reales, `status: completed` padre + hijas (inline).
