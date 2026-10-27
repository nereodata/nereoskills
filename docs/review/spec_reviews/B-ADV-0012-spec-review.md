# Revisión de especificación — B-ADV-0012

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Paso: especificar. Reevaluación de H-01/H-02.

## Alcance

Exclusivamente el delta respecto a HEAD de `tests/features/uso_sin_rutas.feature` (líneas 153-176), contrastado con `docs/plan/bugs/B-ADV-0012-tarea-atascada-en-dificil-para-todo-el-bucle.md`. Se aplican el agente Hades y la skill `review-spec` de la instalación 0.6.1, ignorando el modelo del frontmatter. No se revisan implementación ni diseño.

El delta añade un esquema con ejemplos para `task-dev` y `bug-fix`, y un escenario de promoción. Los escenarios anteriores se comprueban únicamente para asegurar su conservación; no se reevalúan. La decisión humana del contrato autoriza el bloqueo local y la continuidad con otras tareas elegibles.

## Comprobaciones obligatorias

| Comprobación | Resultado | Evidencia |
| --- | --- | --- |
| No regresión | ✅ | El diff respecto a HEAD solo añade los dos escenarios de B-ADV-0012. Todos los escenarios previos de B-ADV-0006 permanecen intactos, incluida la fila de parada al tercer fallo en dificil. |
| Coherencia | ✅ | El esquema exige blocked, pendiente_de humano, motivo, aviso por Telegram, espera de dependientes, avance de la independiente e informe al agotar elegibles. La promoción disponible precede al bloqueo. El contrato conserva expresamente la regla propia del cierre de suite. |
| Trazabilidad | ✅ | Ambos escenarios llevan `@B-ADV-0012` y corresponden al contrato de origen. No se añaden etiquetas `@CA-*` sin criterio documentado. |
| Delta real | ✅ | Los añadidos especifican bloqueo local y precedencia de la promoción; no se recupera el escenario duplicado de cierre de suite de WIP be865c1. |

## Puntuaciones

| Criterio | Nota | Justificación |
| --- | --- | --- |
| Claridad | 9/10 | Ambos escenarios declaran explícitamente `--reintentos=2`, distinguiendo configuración del ejemplo y umbral fijo. El bloqueo de la tarea y la continuidad del bucle quedan diferenciados. |
| Completitud | 9/10 | Cubre ambos pasos afectados, agotamiento sin promoción, dependientes, trabajo independiente, motivo persistido, aviso, fin de elegibles y promoción disponible. La excepción de suite mantiene su cobertura previa. |
| Testeabilidad | 9/10 | Precondiciones concretas, estados y efectos observables: dos intentos configurados, dificultad, cola de 2000 caracteres, revisión humana, aviso y selección de tareas. |
| Estructura | 9/10 | Amplía el archivo funcional existente, sin crear una especificación por bug o versión. |

**Media: 9/10.** Todas las comprobaciones obligatorias satisfechas; sin hallazgos críticos ni altos.

## Seguimiento de hallazgos anteriores

| Hallazgo | Estado | Evidencia de resolución |
| --- | --- | --- |
| H-01 — 🔴 CRÍTICO — Escenario añadido sin delta de comportamiento; para: especificador | **Resuelto** | No figura entre los añadidos «El cierre de suite conserva su regla de tres arreglos fallidos». Se conservan íntegros los escenarios de B-ADV-0006; no se duplica su regla. La decisión DEC-12-E1 del contrato mantiene la excepción en su cobertura existente. |
| H-02 — 🟡 MEDIA — Umbral de dos intentos sin configuración declarada; destino: resolver; responsable: especificador | **Resuelto** | Las líneas 157 y 172 declaran «el límite de intentos sin progreso está configurado con "--reintentos=2"». La resolución H-02 del contrato confirma que dos es la configuración del ejemplo. |

**Hallazgos nuevos: ninguno.** La corrección no altera los escenarios anteriores ni introduce otra duplicación.

## Evidencia y límites

La aprobación procede de la lectura del contrato y del diff de especificación respecto a HEAD. No acredita que el comportamiento esté implementado ni que los escenarios nuevos estén automatizados.

Se intentó únicamente `adevv orquestar --verificar "python -m unittest tests.test_orquestar.SuiteRecoveryTests tests.test_orquestar.DificultadTests"`. Terminó con código 1 antes de ejecutar o reutilizar las pruebas: al calcular la huella del árbol, `git add -A .` devolvió 128. No se acredita un verde del árbol actual ni se atribuye a este intento un registro nuevo de pruebas. El registro verde anterior de ese comando en `orquestar_evidencias.jsonl` corresponde a la huella `4cc5d5fdacaf3bb9a8f0874342cef2e033eb0a77`; no se ha podido comprobar su coincidencia con el árbol revisado. Es una limitación de verificación, no un defecto demostrado de la especificación.

No se ejecuta la suite completa, no se escriben pruebas y no se ejecuta `BloqueoSinProgresoTests`. Esa clase y su evidencia roja permanecen en WIP be865c1, pendientes de recuperación y revisión por el desarrollador: no se atribuyen al árbol actual. No se cambian estados ni se hace commit.
