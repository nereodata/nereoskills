**Veredicto:** RECHAZADO

Transcripción íntegra del dictamen independiente de Hades, invocación d2d356c2ce0543ab9b75122dce2f0eff. El revisor evaluó los adjuntos exactos; no pudo leer ni escribir el árbol. No se atribuyen verificaciones ejecutadas por Hades.

---

No he podido escribir `docs/review/spec_reviews/B-ADV-0031-spec-review.md`: la herramienta de escritura ha fallado. Devuelvo su contenido íntegro para transcripción.

# Revisión de especificación · B-ADV-0031

**Veredicto: RECHAZADO**

Fecha: 2026-11-11. Revisor: Hades. Skill: `/review-spec`. Modo: orquestado.

## Alcance y evidencia

Revisión independiente de los cuatro escenarios etiquetados `@B-ADV-0031` al final de `tests/features/publicacion.feature`, incluido el esquema con sus dos ejemplos. Se utilizan exclusivamente el bug y su triaje, la feature completa y las instrucciones completas de Hades y de la skill adjuntas a la petición. Los escenarios anteriores son contexto existente y no se vuelven a evaluar. No hay etiquetas `@CA-*` nuevas en el delta.

No se han revisado diseño, código ni pruebas, ni se han ejecutado verificaciones. No se recibió un informe anterior: esta es una primera revisión, no una reevaluación.

La herramienta de procesos no pudo iniciarse al intentar leer la copia instalada del agente y de la skill. Se aplican sus contenidos completos adjuntos; esto no impide juzgar la especificación. No se dispone de un diff independiente contra la base: la comprobación de no regresión se limita al delta expresamente delimitado por la petición. No se certifica el estado de otros archivos del árbol.

## Obligatorias

| Criterio | Resultado | Motivo |
| --- | --- | --- |
| No regresión | ✅ | El delta recibido añade los cuatro escenarios finales; no contiene eliminación ni modificación de los escenarios existentes. Comprobación limitada al material adjunto y al alcance declarado. |
| Coherencia | ✅ | Los comportamientos añadidos son compatibles con los criterios del bug: historial común aplicable, invalidación por un fallo posterior e identidad acreditable. Las omisiones de cobertura se detallan como hallazgos, sin atribuir contradicciones al contexto existente. |
| Trazabilidad | ✅ | Los cuatro escenarios llevan `@B-ADV-0031` y corresponden al bug recibido. No introducen `@CA-*` cuya existencia deba contrastarse. |
| Delta real | ✅ | Especifican comportamientos de reutilización y acreditación de evidencias que no aparecen en los escenarios previos adjuntos. No son duplicados de los casos de publicación o revisión formal existentes. |

## Puntuaciones

| Dimensión | Puntuación | Justificación |
| --- | ---: | --- |
| Claridad | 8/10 | Se entienden los consumidores y los resultados principales. Falta concretar la decisión de esperar y distinguir la ausencia de reintento automático de una verificación posterior solicitada. |
| Completitud | 7/10 | Cubre los cuatro riesgos declarados en los títulos, pero deja sin especificar una rama explícita del criterio de aceptación y el cambio de entradas anterior a una consulta. |
| Testeabilidad | 8/10 | La ejecución, reutilización, persistencia y contenido del mandato son observables. La explicación exigida por el criterio de aceptación solo se comprueba expresamente para el fallo anterior. |
| Estructura | 10/10 | Los escenarios se incorporan a la feature funcional existente y se identifican por el bug; no crean una feature por tarea o versión. |

**Media: 8,25/10.** La media supera 8, pero hay un hallazgo de gravedad alta; por tanto, no procede aprobar.

## Hallazgos

### H-01 · 🟠 ALTA · Falta especificar la decisión de esperar y el diagnóstico de las decisiones

- **Referencia:** segundo criterio de aceptación de v1.2.0 y los cuatro escenarios del delta.
- **Evidencia:** el criterio exige que se explique por qué procede «ejecutar, esperar o reutilizar». Los escenarios describen ejecución y reutilización, pero ninguno establece cuándo corresponde esperar, qué observa el consumidor en ese estado ni qué permite salir de él. Solo el caso de fallo anterior exige expresamente una explicación de la decisión de ejecutar.
- **Impacto:** una solución que siempre ejecutase o reutilizase, sin contemplar espera y sin explicar la reutilización, podría satisfacer estos escenarios dejando incumplido el criterio de aceptación. No puede inferirse del material recibido si esperar se refiere a una comprobación en curso, a otro estado o si esa rama se incluyó por error.
- **para:** `especificador`.
- **destino:** `resolver`.
- **Corrección requerida:** concretar el supuesto observable que requiere esperar y su resultado, y cubrirlo en la especificación. Añadir resultados observables para el motivo de reutilización y de ejecución por identidad no acreditada. Si esperar no forma parte del contrato de este bug, ajustar expresamente el criterio de aceptación y su justificación; no elegir silenciosamente una interpretación en el diseño.
- **Material necesario:** aclaración del significado de «esperar» en el criterio de origen. No se requiere diseño ni código para resolverlo.

### H-02 · 🟡 MEDIA · No se comprueba un cambio de entradas previo a la reutilización

- **Referencia:** tercer criterio de aceptación y escenarios «Evidencia sin identidad acreditable exige ejecución» y «Un comando modifica sus entradas durante la ejecución».
- **Evidencia:** el esquema mantiene el mismo comando y árbol, y varía el entorno. El último escenario cambia entradas durante la ejecución. Ninguno parte de un éxito seguido de un cambio relevante de entradas antes de que los consumidores consulten la evidencia.
- **Impacto:** queda sin una comprobación directa la obligación de respetar las entradas actuales. Los casos adjuntos no discriminan por sí solos una solución que controle el entorno y los cambios en vuelo, pero reutilice una evidencia anterior tras una edición previa.
- **para:** `especificador`.
- **destino:** `resolver`.
- **Corrección propuesta:** añadir un caso breve con éxito previo, cambio concreto de un archivo relevante antes de consultar y entorno sin cambios; exigir que Hades no lo acredite y que verificar y preflight ejecuten por cambio de entradas, conservando la trazabilidad del éxito anterior. Puede integrarse como variante de un escenario existente.

### H-03 · 🔵 BAJA · El límite del reintento automático queda implícito

- **Referencia:** «Un fallo posterior invalida un éxito compartido», últimas dos líneas.
- **Evidencia:** se exige que la siguiente verificación ejecute el comando y también que «no reintenta automáticamente el fallo», sin delimitar expresamente la invocación a la que se aplica esta última condición.
- **Impacto:** la lectura razonable distingue una nueva verificación solicitada de un reintento dentro del preflight fallido, pero esa distinción queda implícita al convertir el escenario en una prueba.
- **para:** `especificador`.
- **destino:** `resolver`.
- **Corrección propuesta:** indicar que el preflight fallido termina sin una segunda ejecución automática y que una nueva invocación de verificar ejecuta una vez el comando, explicando el fallo anterior.

## Condición de reevaluación

Resolver H-01 y remitir el cambio de especificación junto con este informe. H-02 y H-03 tienen destino `resolver` por ser ajustes pequeños del mismo contrato. No se solicita modificar código ni aportar pruebas de implementación para esta revisión.
