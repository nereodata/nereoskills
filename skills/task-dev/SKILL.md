---
name: task-dev
description: Ciclo de desarrollo completo de una tarea (BDD -> Diseño -> TDD -> Dev -> QA -> Doc)
inputs:
  - modo: (Opcional) interactivo (por defecto) | orquestado
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
  - review-test
  - review-code
  - manage-docs
  - commit
---

# Skill: Desarrollo de Tarea (/task-dev)

Playbook para el desarrollo de tareas.

> **Modo orquestado** (invocada desde `/orquestar`): mismo ciclo, pero ningún HITL detiene el flujo. Lo que se habría validado se añade a `docs/review/versions/vX.Y-revision.md` (formato en `/orquestar`) para la revisión humana al cerrar la versión. Donde se pregunte al usuario, se toma la opción recomendada y se registra. Las revisiones de Hades se mantienen.
> Si la tarea ya está `in_progress` y el árbol tiene cambios sin commitear, son de un intento interrumpido de esta misma tarea (p. ej. por falta de cuota): retómalos desde la subfase en que quedaron en lugar de exigir árbol limpio o descartarlos.
> Si la tarea vuelve tras un bloqueo, parte de la rama `wip/<ID>` si existe y lee en la revisión de versión cómo se resolvió (ajuste del especificador o respuesta del humano). Cada intento empieza las revisiones de cero.
> Cada revisión de Hades se invoca una sola vez sobre el alcance fijado en el triaje (nunca archivo por archivo ni ítem por ítem) y se repite mientras quede algo para el desarrollador. Lo que Hades asigne a otro: en modo orquestado, regla 5 de `/orquestar`; en interactivo, se plantea al usuario. Si solo quedan 🟡/🔵, se cierra aplicando su destino.
> **Impedimentos**: si no puedes resolver algo que la tarea necesita, no lo sortees ni lo finjas: en cuanto lo veas, llévalo tal como esté a la revisión de Hades en curso, describiendo el impedimento. Él decide de quién es.
> **Pruebas y chequeos**: lanza solo lo que pueda fallar por tu cambio, no la suite completa (el bucle la pasa una vez al cerrar la versión). Si algo falla, itera solo sobre lo que falla hasta verlo en verde y entonces ejecuta la verificación del triaje. En modo orquestado ejecuta los comandos de verificación y análisis estático con `adevv orquestar --verificar "<comando>"`: reutiliza el resultado en verde del mismo árbol exacto, y Hades reutiliza esa evidencia sin relanzarlos.

## 1. Inicialización (inline)
- **Validar Rama**: Debe ser `release/vX.Y` o `hotfix/vX.Y.Z`. Abortar si es `main`.
- **Cargar Metadatos**: Cargar la tarea y sus hijas, si las tiene.
- **Coherencia**: Validar que la versión en la tarea coincide con la de la rama activa.
- **Estado**: Cambiar `status` a `in_progress` en la tarea y sus hijas.

## 2. Triaje de Alcance (inline)
**Filosofía Delta-First**: Inspecciona qué existe ya antes de construir. Si la tarea combina distintas naturalezas de trabajo (lógica, datos/contenido, configuración, documentación), no apliques todas las subfases a todo: decide qué subfases aportan valor real y **a qué parte concreta de la tarea** aplica cada una.

Anota el triaje en el fichero de la tarea marcando `[EXEC]` (indicando sobre qué parte del trabajo aplica) o `[SKIP]` (con el motivo en una línea):
- **Subfase A: Definición** (Escenarios BDD/evals nuevos o modificados) → `[EXEC]` / `[SKIP]`
- **Subfase B: Diseño** (Decisiones técnicas o de estructura no obvias) → `[EXEC]` / `[SKIP]`
- **Subfase C1: Pruebas** (Tests nuevos o modificados cuando la verificación existente no cubre ya esa parte) → `[EXEC]` / `[SKIP]`
- **Subfase C2: Implementación** (Construcción del cambio) → `[EXEC]` / `[SKIP]`
- **Subfase D: QA** (Revisión de Hades sobre el entregable) → `[EXEC]` / `[SKIP]`
- **Subfase E: Documentación** (Manuales o guías afectadas) → `[EXEC]` / `[SKIP]`
- **Subfase F: Cierre** (Commit y cierre de tarea) → `[EXEC]` (siempre)
- **Verificación al cierre**: qué comando (pruebas, validador o linter del proyecto) garantiza que el cambio funciona y por qué, en una línea. Elige solo lo que ejercita el delta; la suite completa la pasa el bucle al cerrar la versión. Si el cambio crece, amplíala y anótalo.

**Regla del triaje**: El triaje gobierna el resto de la tarea. Cada subfase `[EXEC]` se ejecuta y se revisa **una sola vez sobre el alcance fijado para ella** (nunca archivo por archivo ni ítem por ítem), y Hades evalúa conforme a este triaje.

## 3. Fase de Implementación (secuencial, según el triaje)

### Subfase A: Definición [EXEC/SKIP]
1. `/generate-bdd` sobre el alcance fijado en el triaje → `.feature` existentes (no nominales). Si la tarea parte de escenarios ya aprobados en una fase previa (citados en sus criterios), trasládalos al `.feature` sin cambiarlos.
2. Evals: si involucra salidas no deterministas (p. ej. IA, NL2SQL o pipelines probabilísticos), Golden Tests en Gherkin en su suite aislada.
3. `Hades /review-spec` (aislado) solo sobre lo que la tarea añade o modifica respecto a los escenarios de origen; si no añade ni modifica nada, se omite. Sin escenarios de origen, se revisa todo.
4. **HITL**: Validar especificación consolidada.

### Subfase B: Diseño [EXEC/SKIP]
1. `/design` sobre la parte fijada en el triaje → `docs/design/[ID]-design.md`. Sin revisión de Hades: `/review-code` comprueba después que el código lo sigue.
   - Si se desvía de la arquitectura, añade la `DEC` al plan de plataforma en este mismo cambio.
2. **HITL (Opcional)**: Validar diseño.

### Subfase C1: Pruebas (Red Phase) [EXEC/SKIP]
1. Step defs y pruebas para el alcance fijado en el triaje.
2. Verificar que fallan (solo tests relevantes) y guardar esa salida.
3. Lint y tipado limpios sobre las pruebas.
4. `Hades /review-test` (aislado), con la salida del rojo.

### Subfase C2: Implementación (Green Phase) [EXEC/SKIP]
1. Construcción mínima del cambio (docstrings sí, inline comments no).
2. En cada corrección, solo lo que falla; al terminar, la verificación anotada en el triaje en verde.
3. Lint, tipado y chequeos de seguridad del proyecto (secretos, `git diff --check`, y auditoría de dependencias si cambian manifiestos) limpios sobre todo el delta, registrados con `--verificar`.

### Subfase D: QA [EXEC/SKIP]
1. `Hades /review-code` (aislado), una sola vez sobre el delta completo de la tarea.
2. **HITL**: Validar funcionalidad e integración visual.

### Subfase E: Documentación [EXEC/SKIP]
- `/manage-docs`: Actualizar según `docs_config.yaml` (minimalista, inline).

### Subfase F: Cierre [EXEC]
1. **Deuda**: según el destino que marque Hades en cada 🟡/🔵: `resolver` se corrige; `registrar` → `/bug-add` como deuda registrada (sin versión, `origen` = este ID y su reporte); `descartar` no se hace nada.
2. Cierre: `status: completed` en la tarea y sus hijas (inline).
3. `/commit`: Commit semántico (inline).
