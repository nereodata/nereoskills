# Revisión de especificación · T-ADV-0039

**Veredicto: APROBADO**

Fecha: 2026-11-12. Rama: `release/v1.2`. Reevaluación del delta final ampliado.

Alcance: ficha T-ADV-0039 y únicamente los siete escenarios/esquemas `@T-ADV-0039` de `tests/features/uso_sin_rutas.feature`. El diff funcional añade 75 líneas y no altera escenarios previos. No se revisan diseño, código, pruebas de implementación ni otros dictámenes. Este dictamen de especificación de Adevv no sustituye los dictámenes históricos de especificación o código de Afinn.

## Obligatorias

| Comprobación | Resultado |
| --- | --- |
| No regresión | ✅ Delta aditivo; escenarios anteriores intactos. |
| Coherencia | ✅ Los comportamientos concuerdan con los cuatro criterios y el triaje de la ficha. |
| Trazabilidad | ✅ Todos los escenarios citan la tarea existente; no hay etiquetas CA inexistentes. Se detalla la correspondencia abajo. |
| Delta real | ✅ Se añaden correlación entre revisiones, contrato por entrada, retoma, aclaración y tratamiento del histórico parcial. |

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | ---: | --- |
| Claridad | 8 | Se separan los recorridos principales; quedan disyunciones menores y una condición de perfil estricto. |
| Completitud | 9 | Se cubren reserva, rechazo, cuota total, retoma, aclaración, fallo técnico, entrega sin dictamen e histórico parcial. |
| Testeabilidad | 8 | Se exigen identidad, perfil efectivo, salida, conservación de evidencia, eventos sin consumo duplicado y recuperación observable; pueden concretarse mejor algunas variantes. |
| Estructura | 9 | Los escenarios permanecen en el archivo funcional existente. |

**Media: 8,5/10. Sin hallazgos críticos ni altos.**

## Cobertura de los criterios

| Criterio | Evidencia de especificación |
| --- | --- |
| CA-M-1 | La matriz de reserva devuelve resultado y perfil efectivo e identifica trabajo, invocación, padre y rol. La cuota del principal permanece registrada. Afinn acredita recepción de la especificación y devolución del rechazo posterior a Artemisa. |
| CA-M-2 | Agotamiento total con una hora de indisponibilidad y cero horas de espera del proceso; retoma la misma acción y evidencia, registra perfil/hora de recuperación, conserva relación padre y respeta la restricción del perfil estricto. |
| CA-M-3 | Se distinguen reserva válida, contradicción, fallo de ejecución, entrega sin dictamen y cuota. La aclaración conserva las fuentes, tiene perfiles autorizados y espera identificada por llamada/revisión; al recuperarse permite un dictamen concordante. |
| CA-M-4 | Los esquemas ejercen las tres entradas y el esquema de fallos declara proveedores simulados. Se comprueban resultados, identidad, consumo, retoma e histórico parcial desconocido. La unicidad de implementación de la decisión espera/reserva se reserva a la revisión de código, por ser una propiedad estructural. |

## Hallazgos

### 🟡 MEDIA · Algunas variantes siguen expresadas mediante condiciones o disyunciones

El agotamiento incluye «si el perfil es estricto» sin una columna de ejemplos que obligue a ejecutar la variante estricta. El aislamiento usa «cuota o aclaración» y «pruebas o de otra tarea». Explicitar esas combinaciones facilitaría comprobar cada límite. El contrato exigido es comprensible y el conjunto ya cubre recuperación e identidad con suficiencia; no bloquea la aprobación.

## Cierre de los hallazgos anteriores

La separación de reserva válida y agotamiento elimina el recorrido principal condicional del primer borrador. La aclaración conserva ambas fuentes y su propia espera. El histórico parcial exige correlación desconocida sin cancelar otra revisión. La ratificación de especificación tiene un resultado intermedio antes del rechazo de código, con revisión y entradas coincidentes; no necesita imponer los identificadores literales del episodio para expresar esa correlación. La matriz final añade fallo técnico y entrega sin dictamen, y el registro exige las identidades y la recuperación observables que faltaban.
