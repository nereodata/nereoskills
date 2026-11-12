# Revisión de especificación · B-ADV-0031

**Veredicto: APROBADO**

Fecha: 2026-11-12. Revisor: Hades. Skill: `/review-spec`. Paso: especificar. Objetivo: spec. Tipo: reevaluación.

## Alcance y evidencia

Reevaluación de H-01 a H-03 del dictamen anterior (invocación d2d356c2ce0543ab9b75122dce2f0eff) y de los cambios adjuntos en la ficha B-ADV-0031 y en `tests/features/publicacion.feature`. Se mantienen el contrato y los inputs funcionales recibidos: criterios del bug, triaje, CA-M-4 de T-ADV-0032, feature completa, informe anterior y delta. Los escenarios previamente aprobados se usan como contexto y no se vuelven a revisar.

Se ha leído la feature del árbol de trabajo y el informe anterior; la feature coincide con el material recibido. La comprobación de no regresión se limita al delta adjunto entre rondas. No se certifican cambios ajenos a ese alcance.

Se acepta la evidencia aportada de `git diff --check` en verde sobre el árbol identificado como `96caa38a7c`; no se repite. Ese chequeo documental no valida el comportamiento funcional, que se juzga leyendo la especificación. No se han revisado código, diseño ni pruebas de implementación, ni se han ejecutado tests, lint u otros chequeos. El bug permanece en fase de especificación; este dictamen no acredita su implementación ni su cierre.

Limitación de acceso: la lectura del agente y la skill en la copia instalada indicada fue denegada. Se aplican sus contenidos íntegros adjuntos a la petición, ignorando el modelo del frontmatter como se solicita. La lectura del repositorio y la escritura de este informe sí están disponibles. No se modifica la copia instalada.

## Obligatorias

| Criterio | Resultado | Motivo |
| --- | --- | --- |
| No regresión | ✅ | El delta conserva los escenarios ajenos al bug y sus expectativas. Las modificaciones de B-ADV-0031 concretan diagnósticos y secuencia de invocaciones; los dos esquemas añadidos completan los hallazgos anteriores sin retirar obligaciones. |
| Coherencia | ✅ | La espera se vincula a una comprobación equivalente en curso entre worktrees, conforme a CA-M-4. Se conserva el historial aplicable y la acreditación exclusiva de verdes aplicables; la cuota y las revisiones LLM quedan fuera del contrato del bug. |
| Trazabilidad | ✅ | Los cambios funcionales llevan `@B-ADV-0031` y corresponden a sus criterios de historial, decisión e identidad. El delta no incorpora etiquetas `@CA-*` nuevas. |
| Delta real | ✅ | Las adiciones distinguen espera con éxito o fallo y edición anterior a la consulta; las modificaciones hacen observables los motivos de decisión y el límite de cada invocación. No duplican los escenarios previos de publicación ni los de cambios durante la ejecución. |

## Puntuaciones

| Dimensión | Puntuación | Justificación |
| --- | ---: | --- |
| Claridad | 9/10 | La decisión de esperar tiene supuesto, mensaje y terminación definidos; los motivos de reutilización y ejecución son explícitos y las invocaciones tras un fallo están separadas. |
| Completitud | 9/10 | El delta cubre las omisiones señaladas: espera por equivalencia con resultados cero y uno, diagnóstico de identidad y edición previa con entorno estable para verificar y preflight. |
| Testeabilidad | 9/10 | Se observan mensajes, acreditación de Hades, conservación histórica y número de ejecuciones. Los casos de entorno parten por separado del historial original, evitando que un consumidor enmascare el comportamiento del siguiente. |
| Estructura | 10/10 | Los cambios permanecen en la feature funcional existente y los nuevos esquemas describen comportamiento sin imponer mecanismos de implementación. |

**Media: 9,25/10.** Supera 8 y no hay hallazgos críticos ni altos abiertos.

## Reevaluación de hallazgos anteriores

| Hallazgo | Estado | Evidencia y conclusión |
| --- | --- | --- |
| H-01 · 🟠 ALTA · Espera y diagnóstico de decisiones | **resuelto** | La DEC de especificación vincula la espera a CA-M-4. El nuevo esquema inicia verificar en el worktree secundario y hace que el preflight equivalente espere en el principal, explique la espera, comparta éxito o fallo y deje una sola ejecución real en el historial. Hades no acredita antes del resultado y solo acredita el éxito aplicable. Los escenarios modificados exigen explicar la reutilización por coincidencia de comando, entradas y entorno, y la ejecución por entorno ausente o distinto; el nuevo esquema de edición exige diagnosticar el cambio de entradas. |
| H-02 · 🟡 MEDIA · Cambio de entradas anterior a la reutilización | **resuelto** | El nuevo esquema parte de un éxito sobre `src/precios.py`, modifica ese archivo con comando y entorno estables y consulta Hades antes de verificar o preflight. Exige no acreditar el contenido actual, ejecutar una vez por cambio de entradas y conservar el éxito asociado al contenido anterior. |
| H-03 · 🔵 BAJA · Límite del reintento automático | **resuelto** | El preflight fallido termina con diagnóstico tras una sola ejecución. Una nueva solicitud explícita de verificación constituye otra invocación, explica el fallo anterior y ejecuta una sola vez. Queda delimitada la ausencia de reintento automático dentro del preflight. |

## Hallazgos nuevos

Ninguno. El delta no introduce contradicciones ni omisiones de gravedad crítica o alta respecto al contrato recibido. No se exige ampliar esta corrección a todas las ramas de coordinación de CA-M-4: la reevaluación se limita a la espera equivalente y a los cambios de identidad y diagnóstico afectados por los hallazgos anteriores.

## Dictamen formal

**APROBADO** para la especificación de B-ADV-0031 en el paso especificar. H-01, H-02 y H-03 quedan resueltos. No quedan correcciones de especificación pendientes derivadas de esta reevaluación.
