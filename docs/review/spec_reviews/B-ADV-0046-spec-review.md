# B-ADV-0046 · Reevaluación de H-05

**Veredicto: APROBADO · Media: 9,75/10.**

**H-05: resuelto.** Tras la segunda recuperación, la línea añadida exige que la copia de evidencia creada en la primera siga disponible y sea idéntica byte a byte al registro original. El escenario detectaría tanto la pérdida de la copia como su sobrescritura con el registro saneado, incluso si los totales exportados siguieran siendo correctos. La condición se aplica a los dos ejemplos, incluido el que contiene el byte UTF-8 inválido `FF`.

**Criterios obligatorios:** ✅ No regresión, coherencia, trazabilidad y delta real. La adición conserva las comprobaciones previas y concreta la obligación de preservar evidencia en un momento que antes quedaba sin comprobar.

**Puntuaciones:** claridad 10/10, completitud 10/10, testeabilidad 10/10 y estructura 9/10.

**Hallazgos nuevos:** ninguno.

---

## Historial de dictámenes

# B-ADV-0046 · Revisión de especificación

**Veredicto: RECHAZADO**
**Media: 8,0/10.** Tres hallazgos de severidad alta requieren corrección en la fase A.

**Alcance.** Revisión única de los cuatro escenarios `@metricas` añadidos a `skills/orquestar/features/orquestacion.feature`. Se han contrastado con el diff, el feature completo, la ficha del bug y la rúbrica `review-spec` aportados. El arnés impidió abrir `hades.md` y la copia instalada de la skill con el error `registered Core launch requires an installed app`. El dictamen aplica la rúbrica reproducida en la solicitud. No se han ejecutado pruebas ni evaluado implementación.

## Obligatorias

| Criterio | Resultado | Motivo |
|---|---|---|
| No regresión | ✅ | El diff añade cuatro escenarios al final del feature. Todos los escenarios previos conservan su texto. |
| Coherencia | ✅ | La consulta de estado conserva los eventos legibles y comunica la corrupción. La exportación estricta rechaza los totales parciales. La recuperación requiere una solicitud explícita y conserva evidencia binaria. Estos comportamientos son compatibles con los contratos aportados. |
| Trazabilidad | ✅ | El delta no introduce etiquetas `@CA-*` y el bug expresa sus requisitos mediante una lista numerada. Los escenarios corresponden, respectivamente, a los requisitos 1/2/5/6, 2/3/5, 3/4/6 y 5/6. |
| Delta real | ✅ | El escenario de continuidad añade corrupción durante la recogida de métricas de un paso completado. B-ADV-0011 y B-ADV-0044 ya cubrían otros motivos de reintento tras el cierre. La cola parcial, la recuperación binaria y la integridad de los 400 eventos también aportan comportamiento nuevo. |

## Puntuaciones

| Dimensión | Puntuación | Fundamento |
|---|---:|---|
| Claridad | 8/10 | Los ejemplos distinguen el fragmento JSON del byte `0xFF`. El último escenario reúne la recogida del resultado y el relanzamiento en un mismo `Cuando`, lo que impide atribuir el diagnóstico a una ejecución concreta. |
| Completitud | 6/10 | Quedan abiertos el comportamiento del bucle en la ejecución afectada, la continuidad del cursor al retirar una línea y la conservación de escrituras coincidentes con la recuperación. |
| Testeabilidad | 9/10 | La línea 2, la copia idéntica byte a byte, los 7 tokens y los 400 identificadores con su contenido ofrecen resultados comprobables. Falta un coste conocido que pueda contrastarse después de recuperar. |
| Estructura | 9/10 | El delta está en `orquestacion.feature`, tal como pide el triaje A, y los cuatro escenarios se localizan mediante `@metricas`. |

## Hallazgos

| ID | Severidad | Hallazgo y corrección exigida | Responsable | Destino |
|---|---|---|---|---|
| H-01 | 🟠 ALTA | **La caída original podría pasar inadvertida.** En «El bucle conserva un paso ya completado», todas las observaciones se hacen después del relanzamiento. La primera ejecución podría caer al recoger las métricas y la segunda satisfacer el resultado descrito. Separar ambos momentos. Antes de recuperar, exigir que el bucle termine la recogida o se detenga de forma controlada, comunique el archivo y la línea concreta y conserve el cierre del paso. Tras recuperar y relanzar, exigir que el selector avance y que el paso tenga una sola ejecución en total. | especificador | resolver |
| H-02 | 🟠 ALTA | **El cursor solo se comprueba cuando la cola crece.** Ningún escenario mantiene una observación de eventos nuevos a través de una recuperación que acorta el archivo. Un cursor basado en líneas físicas podría saltarse la primera verificación posterior, aunque el total exportado fuese correcto. Fijar una verificación `V1` ya observada después del fragmento, recuperar, añadir `V2` y exigir que el observador entregue exactamente `V2` una vez. | especificador | resolver |
| H-03 | 🟠 ALTA | **Una recuperación podría perder una escritura confirmada.** El escenario de los 400 eventos acaba antes de solicitar la recuperación. El de recuperación actúa sobre un registro en reposo. Ambos admitirían que se confirmara una escritura mientras se recupera el archivo y que luego desapareciera del registro activo. Hacer coincidir una recuperación explícita con el registro de un evento identificable. Al terminar ambas operaciones, exigir que el activo contenga cada evento válido confirmado una sola vez y que la evidencia conserve los bytes originales del fragmento. | especificador | resolver |
| H-04 | 🟡 MEDIA | **La conservación del coste carece de un valor observable.** El requisito 5 menciona costes, pero el ejemplo recuperado solo cuantifica tokens. Dar al consumo de 7 tokens un coste conocido distinto de cero y exigir ese importe exacto tras recuperar y repetir la recuperación. | especificador | resolver |

# B-ADV-0046 · Reevaluación de la especificación

**Veredicto: APROBADO**
**Media: 9,5/10.** H-01 a H-04 están resueltos. Queda un hallazgo nuevo de severidad media sobre la conservación de la evidencia tras una segunda recuperación.

**Alcance.** Revisión del delta desde `58b5774` en `skills/orquestar/features/orquestacion.feature`, contrastado con la ficha, el informe anterior y el feature íntegro. El arnés impidió abrir los archivos instalados de Hades y `/review-spec` con el error `registered Core launch requires an installed app`. Se utilizaron las copias actuales facilitadas en la solicitud. La revisión fue de solo lectura, sin ejecutar pruebas.

## Criterios obligatorios

| Criterio | Resultado | Motivo |
|---|---|---|
| No regresión | ✅ | El delta modifica dos escenarios sometidos a corrección y añade dos. Conserva las garantías anteriores de diagnóstico, exportación estricta, copia binaria, orden de las filas válidas y continuidad del paso. Los escenarios ya aprobados conservan su texto. |
| Coherencia | ✅ | La consulta de estado diagnostica la corrupción sin modificar el registro. La recuperación sigue siendo explícita. El escenario concurrente permite serializar las operaciones y exige conservar el evento cuya escritura se confirma. |
| Trazabilidad | ✅ | El delta no introduce etiquetas `@CA-*`. El diagnóstico durante la recogida y la reanudación corresponden a los requisitos 1, 3, 5 y 6. El cursor y la contabilidad corresponden al 5. La recuperación concurrente concreta los requisitos 3, 4, 5 y 6. |
| Delta real | ✅ | El observador debe reconocer un evento nuevo que ocupa una línea física ya observada. El escritor solicita registrar su evento durante una recuperación en curso. Ambos casos añaden condiciones distintas de la cola que crece y de los cuatro productores que escriben simultáneamente. |

## Puntuaciones

| Dimensión | Puntuación | Fundamento |
|---|---:|---|
| Claridad | 10/10 | La recogida de A y el relanzamiento tienen resultados separados. En el caso concurrente se distinguen la solicitud de escritura de E3 y su confirmación. |
| Completitud | 9/10 | Se cubren la recogida afectada, el acortamiento del registro, la escritura concurrente y la repetición de la recuperación. Falta comprobar la permanencia de la primera copia de evidencia tras esa repetición. |
| Testeabilidad | 10/10 | La línea 2, una ejecución total de A, las dos respuestas sucesivas del observador, los bytes `FF 0A` y el coste exacto de `0,25 USD` permiten detectar incumplimientos concretos. |
| Estructura | 9/10 | Los escenarios permanecen juntos en `orquestacion.feature`, bajo `@metricas`, en la ubicación funcional indicada por el triaje. |

## Estado de los hallazgos previos

| ID | Severidad previa | Estado | Evidencia en la especificación actual |
|---|---|---|---|
| H-01 | 🟠 Alta | `resuelto` | Antes de recuperar, el bucle debe informar de `orquestar_metricas.jsonl`, línea 2, sin excepción sin capturar. En esa misma ejecución conserva el commit, la ficha completada, el consumo y la aprobación de A. Tras recuperar y relanzar, el selector elige B y el total de ejecuciones de A entre ambos arranques es exactamente uno. |
| H-02 | 🟠 Alta | `resuelto` | El mismo observador ya recibió V1 en la línea 3. La recuperación deja dos filas válidas y V2 pasa a ocupar la línea 3. La consulta siguiente debe entregar solo V2 una vez y otra consulta sin escrituras debe quedar vacía. El ejemplo detecta tanto el salto de V2 como la repetición de V1. |
| H-03 | 🟠 Alta | `resuelto` | Otro proceso solicita registrar E3 mientras la recuperación está en curso. Tras completarse ambas operaciones y confirmarse E3, el activo debe contener exactamente E1, E2 y E3, una vez cada uno y con su contenido original. La evidencia debe conservar `FF 0A` entre E1 y E2. |
| H-04 | 🟡 Media | `resuelto` | El consumo de origen tiene 7 tokens y un coste de `0,25 USD`. La exportación debe mostrar esos valores y una sola verificación V tanto después de la primera recuperación como después de la segunda. |

## Hallazgo nuevo

| ID | Severidad | Hallazgo y corrección | Responsable | Destino |
|---|---|---|---|---|
| H-05 | 🟡 Media | La copia se compara byte a byte con el original después de la primera recuperación. La segunda solo comprueba las dos filas activas y los totales. Si esa solicitud sobrescribiera la copia con el registro ya saneado, todas las comprobaciones descritas seguirían cumpliéndose y se perdería el fragmento. Añadir al último `Entonces` que la evidencia de la primera recuperación sigue disponible e idéntica byte a byte al original. | especificador | `resolver` |
