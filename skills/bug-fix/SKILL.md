---
name: bug-fix
description: Ciclo completo para la resolución de anomalías (bugs) (Triaje -> BDD -> Diseño -> Red/Fix -> QA -> Doc)
inputs:
  - modo: (Opcional) interactivo (por defecto) | orquestado
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
  - review-test
  - review-code
  - manage-docs
  - commit
---

# Skill: Resolución de Anomalías (/bug-fix)

Playbook para la resolución de bugs.

> **Modo orquestado** (invocada desde `/orquestar`): mismo ciclo, pero ningún HITL detiene el flujo. Lo que se habría validado se añade a `docs/review/versions/vX.Y-revision.md` (formato en `/orquestar`) para la revisión humana al cerrar la versión. Donde se pregunte al usuario, se toma la opción recomendada y se registra. Las revisiones de Hades se mantienen.
> Si la tarea ya está `in_progress` y el árbol tiene cambios sin commitear, son de un intento interrumpido de esta misma tarea (p. ej. por falta de cuota): retómalos desde la subfase en que quedaron en lugar de exigir árbol limpio o descartarlos.
> Si hay análisis de bloqueo de esta tarea en `docs/review/bloqueos/`, léelos antes de empezar y sigue la pista del último (desde la rama `wip/` que indique o desde cero). Cada intento empieza las revisiones de cero.
> Cada revisión de Hades se repite mientras haya progreso. **Atasco** (se aplica el bloqueo): un mismo 🔴/🟠 sigue `persiste` en dos reevaluaciones seguidas, o el número de 🔴/🟠 no baja en dos reevaluaciones seguidas, o se llega a 6 rondas. Si solo quedan 🟡/🔵, se cierra aplicando su destino.
> Durante las correcciones ejecuta solo las pruebas relevantes; la suite completa, una vez al cierre. En modo orquestado verifica con `orquestar.py --verificar` (suite) o `--verificar "<comando>"`: reutiliza el resultado en verde del mismo árbol exacto, y Hades y el bucle reutilizan esa misma evidencia.
> En modo orquestado el bug no es urgente: se corrige en la `release/vX.Y` activa.

## 0. Clasificación de Urgencia y Rama de Trabajo (inline)
Preguntar al usuario si el bug es urgente (hotfix) o no (release):
- **Si hotfix**:
  - Rama: `hotfix/vX.Y.(Z+1)` creada desde el último tag en `main` (ej. `vX.Y.Z`).
  - Commit inicial: `chore(hotfix): start hotfix vX.Y.Z`
- **Si release**:
  - Verificar rama activa: `release/vX.Y`.
- Actualizar el campo `version` del bug con la versión de la rama.

## 1. Inicialización (inline)
- Cargar metadatos del bug y sus hijos, si los tiene.
- Cambiar `status` a `in_progress` en el bug y sus hijos.
- Si es deuda registrada (`origen`), lee el reporte de origen para entender el hallazgo.

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
3. `Hades /review-spec` (aislado, hasta atasco) sobre los escenarios añadidos o modificados.
4. **HITL**: Validar reproducción.

### Subfase B: Diseño [EXEC/SKIP]
1. `/design`: Analizar bug + código → cambios (`[NEW]`, `[MODIFY]`, `[DELETE]`), SOLID/DRY/KISS/YAGNI, coherencia.
   - Output: `docs/design/[ID]-design.md`. Sin revisión de Hades: `/review-code` comprueba después que el código lo sigue.
   - Si se desvía de la arquitectura, añade la `DEC` al plan de plataforma en este mismo cambio.
2. **HITL (Opcional)**: Validar diseño.

### Subfase C: Desarrollo [EXEC/SKIP]
**Red Phase:**
1. Steps + unit tests que capturen fallo.
2. Verificar que fallan (solo tests relevantes) y guardar esa salida. En deuda sin fallo reproducible (p. ej. un refactor), no hay rojo: los tests existentes deben seguir en verde.
3. Lint y tipado limpios sobre las pruebas.
4. `Hades /review-test` (aislado, hasta atasco), con la salida del rojo.

**Fix Phase:**
1. Corrección mínima (docstrings sí, inline comments no).
2. Tests relevantes en cada corrección; suite completa una vez, al final.
3. Lint y tipado limpios sobre todo el delta.

### Subfase D: QA [EXEC/SKIP]
1. `Hades /review-code` (aislado, hasta atasco). Obligatoria si hay cambios de código de producción.
2. **HITL**: Validar funcionalidad e integración visual.

### Subfase E: Documentación [EXEC/SKIP]
- `/manage-docs`: Actualizar según `docs_config.yaml` (minimalista, inline).

### Subfase F: Cierre [EXEC]
1. **Deuda**: según el destino que marque Hades en cada 🟡/🔵: `resolver` se corrige; `registrar` → `/bug-add` como deuda registrada (sin versión, `origen` = este ID y su reporte); `descartar` no se hace nada.
2. Cierre: `status: completed` en el bug y sus hijos (inline).
3. `/commit`: Commit semántico `fix([ID])` (inline).
