# Revisión de especificación — B-ADV-0006

**Veredicto: APROBADO** — Reevaluación de H1–H4.

## Alcance y evidencia

Revisión conjunta de los escenarios nuevos `@B-ADV-0006` de `tests/features/uso_sin_rutas.feature`, frente al bug `docs/plan/bugs/B-ADV-0006-suite-roja-al-cerrar-version-registra-bug-y-lo-arregla.md` y su triaje. Se revisan las correcciones de los tres escenarios originales y el nuevo esquema de identidad «Un cierre diferente obtiene su propio bug», añadido para resolver H3.

Se han leído el informe anterior, la especificación actual, la petición y el triaje, y sus diffs respecto a `HEAD`. Se ha comprobado expresamente el original mediante `git show HEAD:docs/plan/bugs/B-ADV-0006-suite-roja-al-cerrar-version-registra-bug-y-lo-arregla.md`.

Se aplican Hades y `/review-spec` de la instalación 0.6.0, ignorando el modelo del frontmatter. La petición sustituye el contrato anterior de parada inmediata con suite roja; la sustitución explícita del test anterior queda fuera de esta revisión. No se ha revisado diseño ni implementación ni se han ejecutado tests.

## Comprobaciones obligatorias

| Criterio | Resultado | Evidencia |
| --- | --- | --- |
| No regresión | ✅ | El diff del `.feature` solo añade escenarios del bug; no altera los existentes. |
| Coherencia | ✅ | El alta `planned` coincide con el punto 1 original y restaurado. Las recaídas, identidad y conservación de estados coinciden con las decisiones del triaje. |
| Trazabilidad | ✅ | Todos los escenarios revisados llevan `@B-ADV-0006` y corresponden a su petición o triaje. No introducen etiquetas `@CA-*` sin origen. |
| Delta real | ✅ | Describen recuperación, escalado y control del cierre. Los ejemplos de identidad complementan la reutilización sin duplicarla. |

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Claridad | 9/10 | Se distinguen alta, recaídas tras `completed`, promoción, parada y estados preservados. |
| Completitud | 9/10 | Se cubren contador inicial, límites por dificultad, salida variable, identidad por versión/comando, bloqueo y cancelación. |
| Testeabilidad | 9/10 | Los ejemplos fijan estado, dificultad, contador, continuidad o parada; también conservación o cambio del ID y actualización de salida. |
| Estructura | 9/10 | Los escenarios permanecen en el archivo funcional existente y usan esquemas para las variantes. |

**Media: 9/10.** Se cumplen las obligatorias y no quedan hallazgos críticos ni altos.

## Reevaluación de hallazgos anteriores

| Hallazgo | Estado | Evidencia y conclusión | Para | Destino |
| --- | --- | --- | --- | --- |
| H1 — Estado de alta contradictorio | **Resuelto** | El punto 1 actual coincide literalmente con el de `HEAD`: `status: planned`. El diff del bug solo cambia el estado de su propio frontmatter a `in_progress` y añade el triaje; no cambia ese requisito. La contradicción detectada en la ronda anterior procedía de una modificación mecánica ya restaurada. No queda una decisión del especificador pendiente. | especificador (asignación anterior; sin acción pendiente) | resolver — cerrado |
| H2 — Reapertura y contador antes del tercer fallo | **Resuelto** | El alta fija contador 0. El esquema parte de `completed` y enumera las recaídas 1, 2 y 3 en `media` y `dificil`: reapertura `planned`, continuidad antes del umbral, promoción con reinicio a 0 y parada al tercero en `dificil`, con ID y última salida en consola y Telegram. | especificador | resolver — cerrado |
| H3 — Identidad insuficientemente discriminada | **Resuelto** | La misma versión y comando conservan ID aunque cambie la salida. El nuevo esquema cambia por separado comando o versión y exige otro ID sin modificar el bug anterior. Revisados conjuntamente, ambos esquemas discriminan la identidad acordada. | especificador | resolver — cerrado |
| H4 — Cancelación omitida | **Resuelto** | El esquema de estados incluye `blocked` y `cancelled`; ambos permanecen sin reapertura y con información del impedimento. | especificador | resolver — cerrado |

## Hallazgos nuevos

Ninguno. Las correcciones y el esquema añadido no introducen contradicciones relevantes en el alcance revisado. No se requiere intervención humana.
