# Revisión de especificación — B-ADV-0005

**Veredicto: APROBADO**
**Fecha:** 2026-10-26
**Modo:** orquestado, paso especificar.
**ID maestro:** B-ADV-0005.

## Alcance y criterio

Reevaluación exclusiva del delta de `skills/orquestar/features/orquestacion.feature` frente al contrato y las decisiones de `docs/plan/bugs/B-ADV-0005-arnes-no-encontrado-conmuta-a-reserva.md`, conforme al rol Hades y la skill `/review-spec` de la versión 0.6.0. Se revisan las correcciones de H-01 y H-02 y sus efectos sobre la especificación.

La propuesta anterior se contrasta con `wip/B-ADV-0005:skills/orquestar/features/orquestacion.feature`, atendiendo al significado de sus escenarios pese a los caracteres dañados. La recuperación conserva sus comportamientos y añade la cadena de tres configuraciones, la atribución concreta de métricas y la recuperación con instante fijo. No se han inspeccionado implementación, diseño ni pruebas, ni ejecutado suites. El WIP no se considera evidencia verde del árbol actual.

## Obligatorias

| Regla | Resultado | Motivo |
|---|---|---|
| No regresión | ✅ | Se conservan los comportamientos de los cuatro escenarios anteriores: reserva disponible en los tres flujos, agotamiento total de arneses, conservación de cuota en paso o agente y fallo por autenticación. La concreción de métricas y la expansión de cuota a dos ejemplos no reducen su alcance. |
| Coherencia | ✅ | La ampliación cumple el contrato y las decisiones del especificador: salta principal y reserva ausentes, llega a la segunda reserva, separa sesiones entre arneses, exige avisos por cada ausencia y no transforma ausencia en cuota ni sustituye la recuperación previa. |
| Trazabilidad | ✅ | No hay etiquetas `@CA-*`. La cadena en los tres consumidores corresponde a H-01; la atribución, el consumo cero y el instante fijo corresponden a H-02 y a DEC-ESP-02 del bug. |
| Delta real | ✅ | La cadena con reserva intermedia ausente discrimina un fallo que el salto directo no cubría. La ampliación de métricas y recuperación concreta resultados existentes sin introducir escenarios duplicados. |

## Puntuaciones

| Criterio | Puntuación | Justificación |
|---|---:|---|
| Claridad | 9/10 | Configuraciones ordenadas, flujos y efectos por ausencia explícitos; distingue ausencia de agotamiento de cuota. |
| Completitud | 9/10 | Cubre la continuidad a través de dos ausencias en los tres consumidores y mantiene los límites relevantes de la propuesta anterior. |
| Testeabilidad | 9/10 | Identifica flujo, posición, arnés y modelo de los intentos ausentes; fija todos los contadores indicados y el coste en cero, y exige conservar un instante de recuperación exacto. |
| Estructura | 10/10 | Escenarios en el feature de orquestación, organizados por comportamiento y con ejemplos por consumidor. |

**Media: 9,25/10.** Supera el umbral estricto de 8 y no existen hallazgos críticos ni altos pendientes.

## Reevaluación de hallazgos anteriores

### H-01 — 🟠 ALTA — Resuelto

- **Evidencia:** «Continuar tras una reserva intermedia ausente» establece principal `codex / principal-a` ausente, primera reserva `claude / reserva-b` ausente y segunda reserva `agy / reserva-c` disponible, en ese orden.
- **Resolución:** los ejemplos incluyen paso del bucle, agente Hades y conversación del gateway. En cada uno se exige que `agy / reserva-c` reciba la petición sin reutilizar sesiones de los otros arneses, sin fallo prematuro por ausencia ni espera de cuota. Exige warning, métrica separada y aviso del evento filtrable `arnes` por cada configuración ausente.
- **Para:** especificador.
- **Destino:** resolver en B-ADV-0005; satisfecho en la especificación revisada.

### H-02 — 🟡 MEDIA — Resuelto

- **Evidencia:** los escenarios de salto directo, cadena intermedia y cuota previa identifican los intentos ausentes por flujo, posición, arnés y modelo. Exigen cero tokens de entrada, caché leída, caché escrita, salida y razonamiento, y coste cero, sin agotamiento ni recuperación de cuota atribuibles a esos intentos.
- **Resolución:** el escenario de cuota previa fija la recuperación del principal en `2026-10-26T18:00:00Z` y exige conservar exactamente ese instante y su señal de cuota después de la última reserva ausente, tanto en paso como en agente. Los resultados permiten discriminar atribución equivocada, consumo indebido y sustitución del instante sin imponer nombres internos de campos.
- **Para:** especificador.
- **Destino:** resolver en el mismo feature; satisfecho en la especificación revisada.

## Hallazgos nuevos

Ninguno.

## Salida de la revisión

Especificación aprobada. H-01 y H-02 quedan resueltos en esta revisión. El veredicto se limita a la especificación; no acredita implementación ni pruebas. Solo se actualiza este informe, sin cambiar el estado del bug ni otros artefactos y sin realizar commits.
