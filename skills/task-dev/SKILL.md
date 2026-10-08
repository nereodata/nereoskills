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
> Si hay análisis de bloqueo de esta tarea en `docs/review/bloqueos/`, léelos antes de empezar y sigue la pista del último (desde la rama `wip/` que indique o desde cero). Cada intento empieza las revisiones de cero.
> Cada revisión de Hades se repite mientras haya progreso. **Atasco** (se aplica el bloqueo): un mismo 🔴/🟠 sigue `persiste` en dos reevaluaciones seguidas, o el número de 🔴/🟠 no baja en dos reevaluaciones seguidas, o se llega a 6 rondas. Si solo quedan 🟡/🔵, se cierra aplicando su destino.
> Durante las correcciones ejecuta solo las pruebas relevantes; al cierre, la verificación que marque el triaje (la suite completa solo si el cambio la exige: el bucle la pasa una vez al terminar la versión). En modo orquestado verifica con `orquestar.py --verificar` (suite) o `--verificar "<comando>"`: reutiliza el resultado en verde del mismo árbol exacto, y Hades y el bucle reutilizan esa misma evidencia.

## 1. Inicialización (inline)
- **Validar Rama**: Debe ser `release/vX.Y` o `hotfix/vX.Y.Z`. Abortar si es `main`.
- **Cargar Metadatos**: Cargar la tarea y sus hijas, si las tiene.
- **Coherencia**: Validar que la versión en la tarea coincide con la de la rama activa.
- **Estado**: Cambiar `status` a `in_progress` en la tarea y sus hijas.

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

Marca también en el checklist la **verificación al cierre**, con su motivo en una línea. Elige la mínima que dé confianza razonable de no romper nada:
- `ninguna`: el cambio no afecta a nada que se ejecute (documentación, comentarios, textos de ayuda que ninguna prueba compara).
- `relevantes`: las pruebas de la tarea (las del rojo) y las del módulo que toca. Es la opción por defecto de un cambio localizado.
- `regresión`: además, las pruebas de lo que depende de lo modificado: quienes llaman a la función o al contrato cambiado y los flujos que lo atraviesan. Para cambios en interfaces, contratos o comportamiento compartido.
- `suite`: cambios transversales, como dependencias, configuración de build, CI o pruebas, esquemas o modelos de datos compartidos, utilidades base o refactors amplios.

Si durante el desarrollo el cambio crece más allá de lo previsto, sube el nivel y anótalo.

## 3. Fase de Implementación (secuencial)

### Subfase A: Definición [EXEC/SKIP]
1. `/generate-bdd`: Escenarios BDD en español → `.feature` existentes (no nominales). Si la tarea parte de escenarios ya aprobados en una fase previa (citados en sus criterios), trasládalos al `.feature` sin cambiarlos.
2. Evals: si involucra IA, NL2SQL o pipelines probabilísticos, 3-5 Golden Tests en Gherkin, en su suite aislada.
3. `Hades /review-spec` (aislado, hasta atasco) solo sobre lo que la tarea añade o modifica respecto a los escenarios de origen; si no añade ni modifica nada, se omite. Sin escenarios de origen, se revisa todo.
4. **HITL**: Validar especificación consolidada.

### Subfase B: Diseño [EXEC/SKIP]
1. `/design`: Analizar código existente → cambios (`[NEW]`, `[MODIFY]`, `[DELETE]`), SOLID/DRY/KISS/YAGNI, coherencia.
   - Output: `docs/design/[ID]-design.md`. Sin revisión de Hades: `/review-code` comprueba después que el código lo sigue.
   - Si se desvía de la arquitectura, añade la `DEC` al plan de plataforma en este mismo cambio.
2. **HITL (Opcional)**: Validar diseño.

### Subfase C: Desarrollo [EXEC/SKIP]
**Red Phase:**
1. Step defs + unit tests → `tests/unit/`.
2. Verificar que fallan (solo tests relevantes) y guardar esa salida.
3. Lint y tipado limpios sobre las pruebas.
4. `Hades /review-test` (aislado, hasta atasco), con la salida del rojo.

**Green Phase:**
1. Implementación mínima (docstrings sí, inline comments no).
2. Tests relevantes en cada corrección; al final, la verificación marcada en el triaje.
3. Lint y tipado limpios sobre todo el delta.

### Subfase D: QA [EXEC/SKIP]
1. `Hades /review-code` (aislado, hasta atasco). Obligatoria si hay cambios de código de producción.
2. **HITL**: Validar funcionalidad e integración visual.

### Subfase E: Documentación [EXEC/SKIP]
- `/manage-docs`: Actualizar según `docs_config.yaml` (minimalista, inline).

### Subfase F: Cierre [EXEC]
1. **Deuda**: según el destino que marque Hades en cada 🟡/🔵: `resolver` se corrige; `registrar` → `/bug-add` como deuda registrada (sin versión, `origen` = este ID y su reporte); `descartar` no se hace nada.
2. Cierre: `status: completed` en la tarea y sus hijas (inline).
3. `/commit`: Commit semántico (inline).
