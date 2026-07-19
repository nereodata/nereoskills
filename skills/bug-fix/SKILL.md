---
name: bug-fix
description: Ciclo completo para la resolución de anomalías (bugs) (Triaje -> BDD -> Diseño -> Red/Fix -> QA -> Doc)
inputs:
  - bug_id: ID del bug (B-PRJ-XXXX o B-PRJ-COMP-XXXX)
outputs:
  - status: completed
  - version: versión de la rama de trabajo asociada al hotfix o release
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

# Skill: Resolución de Anomalías (/bug-fix)

Playbook para la resolución de bugs.

## 0. Clasificación de Urgencia y Rama de Trabajo (inline)
Preguntar al usuario si el bug es urgente (hotfix) o no (release):
- **Si hotfix**:
  - Rama: `hotfix/vX.Y.(Z+1)` creada desde el último tag en `main` (ej. `vX.Y.Z`).
  - Commit inicial: `chore(hotfix): start hotfix vX.Y.Z`
- **Si release**:
  - Verificar rama activa: `release/vX.Y`.
- Actualizar el campo `version` del bug con la versión de la rama.

## 1. Inicialización (inline)
- Cargar metadatos del bug padre e hijos (componentes).
- Cambiar `status` a `in_progress` en el padre e hijos.
- Establecer esfuerzos (`actual_effort`, `remaining_effort`).

## 2. Triaje de Alcance (inline)
**Filosofía Delta-First**: Inspecciona el código actual y determina la causa raíz antes de corregir. Analiza el bug y determina qué subfases **realmente aportan valor** (no todas aplican).

Crea un checklist explícito en `task.md` marcando qué subfases ejecutar:
- **Subfase A: Definición** (BDD/evals de reproducción) → `[EXEC]` o `[SKIP]`?
- **Subfase B: Diseño** (Diseño técnico del arreglo) → `[EXEC]` o `[SKIP]`?
- **Subfase C: Desarrollo** (Fase Red/Fix) → `[EXEC]` o `[SKIP]`?
- **Subfase D: QA** (Revisión de código y validación funcional) → `[EXEC]` o `[SKIP]`?
- **Subfase E: Documentación** (Cambio en manuales/docs) → `[EXEC]` o `[SKIP]`?
- **Subfase F: Cierre** (Commit y cierre de bug) → `[EXEC]` (siempre)

**Criterio**: Ejecuta una subfase solo si produce cambios reales y aporta valor. Omite subfases que no aplican al tipo de bug.

## 3. Fase de Implementación (secuencial)

### Subfase A: Definición [EXEC/SKIP]
1. `/generate-bdd`: Escenarios BDD en español → `.feature` existentes (no nominales). Solo si bug destapa requisito faltante/alterado.
2. Evals: Golden Tests en Gherkin (aislados).
3. `Hades /review-spec` (aislado, ×3 iteraciones máx).
4. **HITL**: Validar reproducción.

### Subfase B: Diseño [EXEC/SKIP]
1. `/design`: Analizar bug + código → cambios (`[NEW]`, `[MODIFY]`, `[DELETE]`), SOLID/DRY/KISS/YAGNI, coherencia.
   - Output: `docs/design/[ID]-design.md`.
2. `Hades /review-design` (aislado, ×3 iteraciones máx).
3. **HITL (Opcional)**: Validar diseño.

### Subfase C: Desarrollo [EXEC/SKIP]
**Red Phase:**
1. Steps + unit tests que capturen fallo.
2. Verificar que fallan (solo tests relevantes).
3. `Hades /review-test` (aislado, ×3 iteraciones máx).

**Fix Phase:**
1. Corrección mínima (docstrings sí, inline comments no).
2. Tests relevantes + suite completa al final.

### Subfase D: QA [EXEC/SKIP]
1. `Hades /review-code` (aislado, ×3 iteraciones máx).
2. **HITL**: Validar funcionalidad e integración visual.

### Subfase E: Documentación [EXEC/SKIP]
- `/manage-docs`: Actualizar según `docs_config.yaml` (minimalista, inline).

### Subfase F: Cierre [EXEC]
1. `/commit`: Commit semántico `fix([ID])` (inline).
2. Cierre: Esfuerzos reales, `status: completed` padre + hijas (inline).
