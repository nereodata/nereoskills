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
> Si la tarea vuelve tras un bloqueo, parte de la rama `wip/<ID>` si existe y lee en la revisión de versión cómo se resolvió (ajuste del especificador o respuesta del humano). Cada intento empieza las revisiones de cero.
> Cada revisión de Hades se invoca una sola vez sobre el alcance fijado en el triaje (nunca archivo por archivo ni ítem por ítem) y se repite mientras quede algo para el desarrollador. Lo que Hades asigne a otro: en modo orquestado, regla 5 de `/orquestar`; en interactivo, se plantea al usuario. Si solo quedan 🟡/🔵, se cierra aplicando su destino.
> **Impedimentos**: si no puedes resolver algo que la tarea necesita, no lo sortees ni lo finjas: en cuanto lo veas, llévalo tal como esté a la revisión de Hades en curso, describiendo el impedimento. Él decide de quién es.
> **Pruebas y chequeos**: lanza solo lo que pueda fallar por tu cambio, no la suite completa (el bucle la pasa una vez al cerrar la versión). Si algo falla, itera solo sobre lo que falla hasta verlo en verde y entonces ejecuta la verificación del triaje. En modo orquestado ejecuta los comandos de verificación y análisis estático con `adevv orquestar --verificar "<comando>"`: reutiliza el resultado en verde del mismo árbol exacto, y Hades reutiliza esa evidencia sin relanzarlos.
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
- Cargar metadatos del bug y sus hijos, si los tiene. Si no declara `dificultad`, asume `media` por defecto.
- Cambiar `status` a `in_progress` en el bug y sus hijos.
- Antes de tocar ficheros, registra el SHA de `git rev-parse HEAD` como `base_calidad` en el triaje. Conserva esa base durante commits y reintentos del bug.
- Si es deuda registrada (`origen`), lee el reporte de origen para entender el hallazgo.

## 2. Triaje de Alcance (inline)
**Filosofía Delta-First**: Inspecciona el código actual y determina la causa raíz antes de corregir. Si el bug combina distintas naturalezas de trabajo (lógica, datos/contenido, configuración, documentación), no apliques todas las subfases a todo: decide qué subfases aportan valor real y **a qué parte concreta del arreglo** aplica cada una.

Anota el triaje en el fichero del bug marcando `[EXEC]` (indicando sobre qué parte del trabajo aplica) o `[SKIP]` (con el motivo en una línea):
- **Subfase A: Definición** (Escenarios BDD/evals nuevos o modificados si destapa requisito faltante/alterado) → `[EXEC]` / `[SKIP]`
- **Subfase B: Diseño** (Decisiones técnicas o de estructura no obvias) → `[EXEC]` / `[SKIP]`
- **Subfase C1: Pruebas** (Tests nuevos o modificados que capturen el fallo cuando la verificación existente no lo cubre ya) → `[EXEC]` / `[SKIP]`
- **Subfase C2: Corrección** (Implementación del arreglo) → `[EXEC]` / `[SKIP]`
- **Subfase D: QA** (Revisión de Hades sobre el entregable) → `[EXEC]` / `[SKIP]`
- **Subfase E: Documentación** (Manuales o guías afectadas) → `[EXEC]` / `[SKIP]`
- **Subfase F: Cierre** (Commit y cierre de bug) → `[EXEC]` (siempre)
- **Verificación al cierre**: qué comando (pruebas, validador o linter del proyecto) garantiza que el arreglo funciona y por qué, en una línea. Elige solo lo que ejercita el delta; la suite completa la pasa el bucle al cerrar la versión. Si el cambio crece, amplíala y anótalo.

**Regla del triaje**: El triaje gobierna el resto de la tarea. Cada subfase `[EXEC]` se ejecuta y se revisa **una sola vez sobre el alcance fijado para ella** (nunca archivo por archivo ni ítem por ítem), y Hades evalúa conforme a este triaje.

## 3. Fase de Implementación (secuencial, según el triaje)

### Subfase A: Definición [EXEC/SKIP]
1. `/generate-bdd` sobre el alcance fijado en el triaje → `.feature` existentes (no nominales). Solo si el bug destapa un requisito faltante o alterado.
2. Evals: si involucra salidas no deterministas (p. ej. IA, NL2SQL o pipelines probabilísticos), Golden Tests en Gherkin en su suite aislada.
3. `Hades /review-spec` (aislado) sobre los escenarios añadidos o modificados.
4. **HITL**: Validar reproducción.

### Subfase B: Diseño [EXEC/SKIP]
1. `/design` sobre la parte fijada en el triaje → `docs/design/[ID]-design.md`. Sin revisión de Hades: `/review-code` comprueba después que el código lo sigue.
   - Si se desvía de la arquitectura, añade la `DEC` al plan de plataforma en este mismo cambio.
2. **HITL (Opcional)**: Validar diseño.

### Subfase C1: Pruebas (Red Phase) [EXEC/SKIP]
1. Steps y pruebas que capturen el fallo para el alcance fijado en el triaje.
2. Verificar que fallan (solo tests relevantes) y guardar esa salida. En deuda sin fallo reproducible (p. ej. un refactor), los tests deben validar el contrato esperado.
3. Lint y tipado limpios sobre las pruebas.
4. `Hades /review-test` (aislado), con la salida de la ejecución.

### Subfase C2: Corrección (Fix Phase) [EXEC/SKIP]
1. Corrección mínima (docstrings sí, inline comments no).
2. En cada corrección, solo lo que falla; al terminar, la verificación anotada en el triaje en verde.
3. Lint, tipado y chequeos de seguridad del proyecto (secretos, `git diff --check`, y auditoría de dependencias si cambian manifiestos) limpios sobre todo el delta, registrados con `--verificar`.
4. Ejecuta `adevv orquestar --calidad --base <base_calidad> --aplicar`: escritura disponible y comprobaciones de formato y lint mediante el verificador de evidencia de `/orquestar`. Tras cambios de formato, repite las pruebas afectadas del triaje. Ningún rojo de calidad permite `completed`.

### Subfase D: QA [EXEC/SKIP]
1. `Hades /review-code` (aislado), una sola vez sobre el delta completo del bug.
2. **HITL**: Validar funcionalidad e integración visual.

### Subfase E: Documentación [EXEC/SKIP]
- `/manage-docs`: Actualizar según `docs_config.yaml` (minimalista, inline).

### Subfase F: Cierre [EXEC]
1. **Deuda**: según el destino que marque Hades en cada 🟡/🔵: `resolver` se corrige; `registrar` → `/bug-add` como deuda registrada (sin versión, `origen` = este ID y su reporte); `descartar` no se hace nada.
2. Tras todos los cambios de código, documentación y reportes, repite `adevv orquestar --calidad --base <base_calidad> --aplicar`; acredita el árbol final con el mismo comando sin escritura vía `--verificar`. Si el formato cambia contenido, repite las pruebas afectadas del triaje. Solo en verde: `status: completed` en el bug y sus hijos (inline), comprueba la calidad de ese último cambio y commitea; cualquier fallo devuelve el estado a `in_progress`.
3. `/commit`: Commit semántico `fix([ID])` (inline).
