**Veredicto:** APROBADO · **9,25/10**

# B-ADV-0044 · Reevaluación independiente de pruebas

Paso `bug-fix` en `hotfix/v1.1.3`. Árbol revisado `17cea52d88b8d898df5bd6383189525f1e18a013`. Referencia histórica de la revisión de pruebas C1: `118e5e5ed1280b019580d1df22efcd4127a576ea`. El delta de pruebas corresponde a `skills/orquestar/test_progreso.py`, de `2774e2b` a `7a27d4c`.

## Reevaluación de H2, H3 y D3

| Hallazgo de producto | Qué discrimina la prueba | Resultado observado |
|---|---|---|
| H2 · Huella desplazada o eliminada | Tras aprobar A con su huella y confirmar el cambio de código a B, un commit modifica solo el informe. Una variante intercala una nota delante de la huella de A y la otra la borra. Ambas exigen que B siga pendiente en el selector y en el preflight. El control posterior exige huellas distintas y permite el cierre al aprobar expresamente B. | **Persiste** en ambas variantes. El selector devuelve `revisar-version` cuando corresponde `revisar-tarea` para el ID. |
| H3 · Veredicto citado y reserva | El principal devuelve código 0 y cita una aprobación histórica. Se prueban la continuación de un párrafo citado en Markdown, un bloque HTML y un cerco de tildes. Se exige que el principal quede sin veredicto y que la reserva registre el rechazo de su informe íntegro, entregado entre cercos, en la misma invocación. | **Persiste** con la continuación y con HTML. Las métricas contienen solo la fila de Claude y falta la de Codex. El control con tildes pasa y alcanza las comprobaciones del rechazo y de la invocación. |
| D3 · Restauración tras un rechazo del mismo producto | Se confirman en orden una aprobación y un rechazo de A con la misma huella. Se restaura en el WIP el texto exacto de la primera aprobación. El selector y el preflight deben mantener la revisión pendiente. Después se confirma un informe distinto que reevalúa el hallazgo sobre A y debe permitir el cierre. | **Persiste**. Al restaurar la copia, el selector adelanta `revisar-version`. El caso aísla la precedencia del rechazo manteniendo fijo el producto. |

Los cinco fallos reproducen decisiones de producto. Para H2, H3 y D3 corresponde al **desarrollador** resolverlas. En las cinco ramas rojas la ejecución termina en la primera aserción fallida. Los controles posteriores de cierre en H2 y D3 y las comprobaciones posteriores de métricas en las dos variantes rojas de H3 quedan pendientes de ejecución.

## Seguimiento de la revisión de pruebas anterior

| Hallazgos de pruebas de C1 | Estado en este delta |
|---|---|
| H1 (perfiles), H2 (cuota), H3 (notas), H4 (informe) | **Resueltos**. Se conservan las pruebas de perfiles, espera y consumo, repetición de notas y ausencia de informe para el ID ejecutado. |
| N1 (aprobación caducada), N2 (diagnóstico), N3 (índice Git), N4 (cierre por ambas entradas) | **Resueltos**. Se conservan sus aserciones y datos de prueba. |
| N5 (mandato rastreado), N6 (cambio atribuido a otro ID) | **Resueltos**. Siguen presentes la comparación de las huellas recibidas por el proveedor y la ejecución atribuida al segundo ID. |

## Cobertura de los seis escenarios

Los cuatro primeros conservan sus casos de C1: parada tras dos commits de impedimento en los tres pasos, agotamiento de `work-plan` tras un commit vacío y otro administrativo, recuperación del presupuesto de una ficha antigua por cada una de las cinco aportaciones y aislamiento de intentos entre IDs durante la recarga y el arranque manual. En el quinto, H2 y D3 refuerzan la condición de aprobación vigente que usa el cierre. Se conservan los casos del bucle con retorno 1. En el sexto, H3 distingue la cita técnica del dictamen propio de la reserva. Las pruebas del bucle siguen comprobando el consumo de ambos intentos y la espera por cuota.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 9/10 | Las dos ediciones de huella, las dos formas de cita y la restauración sobre el mismo producto reproducen las variantes pendientes. |
| Aserciones | 9/10 | Se observa el siguiente paso e ID, la lista de pendientes y la secuencia de proveedores con el veredicto de cada uno. Los controles positivos exigen admitir una reevaluación y el informe íntegro de la reserva. |
| Rojo correcto | 10/10 | Las cinco reproducciones fallan por el siguiente paso elegido o por la ausencia de la reserva. El sexto caso pasa con la misma preparación de H3. |
| Estabilidad | 9/10 | Cada caso usa un repositorio Git temporal aislado, textos fijos y proveedores simulados. Las expectativas dependen del orden explícito de los hechos. |

## Hallazgos nuevos de pruebas

Ninguno.

## Evidencia

La ejecución dirigida aportada para el árbol revisado registra **6 pruebas en 6,235 s, con 5 fallos de aserción, 1 caso en verde y 0 errores**. Se reutilizaron los resultados en verde de Ruff selectivo y `git diff --check`. El resultado de las 124 pruebas de C1 pertenece a su árbol histórico.
