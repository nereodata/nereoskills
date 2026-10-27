# Revisión de especificación B-ADV-0020

**Veredicto: APROBADO**

Fecha: 2026-10-27. Modo: orquestado. Revisor: Hades. Ronda: 3.

## Alcance y método

Reevaluación de H1–H3 de la ronda 2 y del delta corrector de `skills/orquestar/features/orquestacion.feature`, frente al contrato, triaje y decisiones de `docs/plan/bugs/B-ADV-0020-marca-de-agotado-a-ciegas-impide-usar-modelo-con-cuota.md`. Se aplicaron las instrucciones de Hades y la skill `review-spec` instaladas en la versión 0.6.1, ignorando el modelo del frontmatter.

Se comparó el feature con `wip/B-ADV-0020:skills/orquestar/features/orquestacion.feature` para aislar las correcciones: ampliación del reset y dos escenarios nuevos. La comparación con la base release `f7ac5bd` confirma que el bloque BDD recuperado no elimina ni modifica escenarios previos. No se reabrieron escenarios no afectados ni se revisaron diseño, implementación o pruebas.

Se reutiliza la evidencia verde de `orquestar_evidencias.jsonl`: `git diff --check`, código 0, fecha `2026-10-27T09:46:54`, árbol `9b60570ae38189303e640f27024ad9799cea1e25`, identificado por el usuario como el árbol recibido. Corresponde a la verificación documental del triaje. No se relanzó ese chequeo ni se ejecutaron pruebas o suite completa. La evidencia corresponde al árbol de entrada, antes de actualizar este reporte; no acredita comportamiento funcional, pendiente del desarrollo.

## Obligatorias

| Criterio | Resultado | Evidencia |
| --- | --- | --- |
| No regresión | ✅ | Frente a `f7ac5bd`, el feature solo añade el bloque BDD del bug. Frente al WIP, las correcciones se limitan al reset y a los dos casos solicitados. |
| Coherencia | ✅ | La compatibilidad histórica conserva la recuperación distinta de 1800 segundos; la opción ausente usa 300 segundos; el reset mantiene las restricciones de pares ajenos, conforme al contrato y a DEC-ESP-20-02/03/04. |
| Trazabilidad | ✅ | Los escenarios correctores llevan `@B-ADV-0020` y corresponden a decisiones explícitas del bug. No introducen etiquetas `@CA-*` sin criterio de origen. |
| Delta real | ✅ | El histórico sin clasificación y la propiedad ausente cubren ramas distintas de las ya descritas; el reset precisa sus efectos sobre seleccionados y ajenos. |

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Claridad | 9/10 | Las aserciones identifican los pares seleccionados y los ajenos y precisan el tratamiento de ambos. |
| Completitud | 9/10 | Las correcciones cubren las tres carencias de la ronda anterior, incluidos compatibilidad histórica y configuración antigua. |
| Testeabilidad | 9/10 | Se fijan duración, antigüedad y tiempo restante, ausencia de la propiedad y resultados observables de selección y visualización. |
| Estructura | 9/10 | Las correcciones permanecen en el feature de orquestación. |

**Media: 9/10.** Sin hallazgos críticos ni altos pendientes.

## Reevaluación de hallazgos anteriores

### H1 — 🟠 ALTA — RESUELTO: compatibilidad de los demás registros históricos

- **Evidencia:** el escenario «Conservar la recuperación de una marca histórica distinta del antiguo valor por defecto» parte de un registro sin clasificación de 3600 segundos y antigüedad de 60 segundos, con reserva disponible. Al relanzar exige usar la reserva y no probar `codex/m1` durante los 3540 segundos restantes, conservando el registro sin reescribirlo.
- **Evaluación:** discrimina el tratamiento incorrecto de todos los registros históricos como sospechas y cumple la compatibilidad exigida por el triaje. La cobertura de 1800 segundos aceptada en la ronda anterior permanece intacta.
- **para:** especificador (asignación anterior satisfecha).
- **destino:** resolver — completado; sin acción pendiente.

### H2 — 🟡 MEDIA — RESUELTO: intervalo por defecto cuando se omite la opción

- **Evidencia:** el escenario «Usar el intervalo por defecto en una configuración sin la opción de sondeo» establece expresamente que `orchestration.json` no contiene `cuota_reintento_s`. Exige no reintentar antes de 300 segundos en el mismo proceso y probar al titular al alcanzarlos, antes de usar la reserva disponible.
- **Evaluación:** cubre la propiedad ausente de forma independiente de `null` y fija el intervalo por defecto con un límite temporal observable, conforme al contrato.
- **para:** especificador (asignación anterior satisfecha).
- **destino:** resolver — completado; sin acción pendiente.

### H3 — 🟡 MEDIA — RESUELTO: elegibilidad y restricciones tras el reset

- **Evidencia:** el esquema «Recuperar marcas por orden explícita» parte de marcas confirmadas vigentes con recuperación dentro de 3600 segundos. Nombra los pares seleccionados `<pares>` al exigir elegibilidad y desaparición del estado de agotado. Para los ajenos exige conservar marcas confirmadas, restricciones y visualización de agotado hasta su recuperación registrada.
- **Evaluación:** elimina el referente ambiguo «esos perfiles» y protege explícitamente a los pares ajenos al selector. Los ejemplos de modelo, arnés y reset global conservan su alcance; en el global no quedan pares ajenos entre los establecidos por el escenario.
- **para:** especificador (asignación anterior satisfecha).
- **destino:** resolver — completado; sin acción pendiente.

## Hallazgos nuevos

Ninguno. El delta corrector no introduce contradicciones ni carencias relevantes en el alcance revisado. La verificación documental del triaje es proporcionada a este paso, que solo recupera y corrige BDD; la verificación funcional sigue pendiente de la implementación.

## Salida para el bucle

**APROBADO. H1, H2 y H3 resueltos.** Sin hallazgos que enrutar. Puede continuar el siguiente paso de desarrollo previsto en el triaje; este veredicto aprueba únicamente la especificación reevaluada y no declara corregido el fallo funcional.
