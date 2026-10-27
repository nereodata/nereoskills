# Revisión de especificación — B-ADV-0012

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Modo orquestado, B-ADV-0012.

## Alcance y criterio

Reevaluación de cero de los dos escenarios `@B-ADV-0012` de `tests/features/uso_sin_rutas.feature` frente al contrato de `docs/plan/bugs/B-ADV-0012-tarea-atascada-en-dificil-para-todo-el-bucle.md`. Se aplican el agente Hades y `/review-spec` de la instalación 0.6.1, ignorando el modelo del frontmatter.

El juicio procede de los escenarios y del contrato actuales, sin tomar la aprobación narrada en el bug ni el informe anterior como evidencia de corrección. Los escenarios anteriores se consideran únicamente para comprobar conservación y ausencia de duplicación; no se reevalúa su contenido.

## Comprobaciones obligatorias

| Comprobación | Resultado | Evidencia |
| --- | --- | --- |
| No regresión | ✅ | El archivo de especificación no presenta diferencias respecto a HEAD. Conserva los escenarios de B-ADV-0006, incluida la parada tras tres recaídas en dificil. |
| Coherencia | ✅ | El esquema exige bloqueo local con pendiente_de humano, motivo con intentos, dificultad y cola de salida, aviso por Telegram, continuidad de la independiente, espera de la dependiente e informe al agotar elegibles. El segundo escenario conserva la promoción disponible antes del bloqueo. La excepción de suite permanece en su cobertura previa. |
| Trazabilidad | ✅ | Ambos escenarios llevan @B-ADV-0012 y corresponden al comportamiento del bug. No introducen etiquetas @CA-* sin criterio de origen. |
| Delta real | ✅ | Especifican el aislamiento de la tarea atascada y la precedencia de la promoción. No añaden otro escenario que repita la excepción de cierre de suite. |

## Puntuaciones

| Criterio | Nota | Justificación |
| --- | --- | --- |
| Claridad | 9/10 | Ambos escenarios explicitan --reintentos=2: dos es la configuración del ejemplo. El bloqueo de la tarea y la continuidad del bucle quedan diferenciados. |
| Completitud | 9/10 | Cubre task-dev y bug-fix, dificultad máxima sin promoción, motivo, notificación, dependencias, trabajo independiente, cierre de elegibles y promoción disponible. La excepción de suite conserva su cobertura existente. |
| Testeabilidad | 9/10 | Son observables los dos intentos configurados, estados, dificultad, últimos 2000 caracteres de salida, revisión humana, aviso y ejecución o espera de tareas. |
| Estructura | 9/10 | Amplía el archivo funcional existente, sin crear una especificación por bug ni duplicar escenarios previos. |

**Media: 9/10.** Sin hallazgos críticos ni altos.

## Seguimiento de hallazgos anteriores

| Hallazgo | Estado | Evidencia actual |
| --- | --- | --- |
| H-01 — 🔴 CRÍTICO — Duplicación de la parada de suite; para: especificador | **Resuelto** | Los dos escenarios de B-ADV-0012 no añaden una excepción de suite. La regla sigue en los escenarios de B-ADV-0006, conforme a DEC-12-E1 del contrato. |
| H-02 — 🟡 MEDIA — Dos intentos sin configuración declarada; destino: resolver; responsable: especificador | **Resuelto** | Ambos escenarios declaran explícitamente --reintentos=2; el contrato confirma que dos es el valor del ejemplo. |

**Hallazgos nuevos: ninguno.**

## Evidencia y límites

Revisión por lectura del contrato y de la especificación actual, con comprobación de diferencias del archivo respecto a HEAD. No se revisan código, diseño ni pruebas automatizadas, y no se ejecutan pruebas ni la suite completa. Esta aprobación acredita la especificación, no su implementación ni su automatización.

Solo se escribe este informe en el árbol de trabajo. No se modifica la copia instalada, no se cambian estados y no se realizan commits.
