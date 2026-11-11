**Veredicto:** APROBADO · **9,50/10**

# B-ADV-0044 · Reevaluación independiente de pruebas C1

Las tres regresiones reproducen los recorridos D3, D6 y D7 del último dictamen de Hades. Cada una llega a la decisión observable que motivó el hallazgo y falla allí. Los hallazgos anteriores de pruebas H1–H4 y N1–N8 siguen resueltos. **Sin hallazgos nuevos de pruebas.**

| Caso | Qué exige la prueba | Rojo observado |
|---|---|---|
| D3 · Restauración en el WIP | Tras aprobar y rechazar el mismo producto, restaura el informe quitando solo `python` de la apertura `~~~python`. El selector debe devolver `revisar-tarea` para el ID y el cierre debe incluirlo entre los pendientes. Como control positivo, confirma el mismo informe con el SHA del último rechazo y exige `revisar-version` y pendientes vacíos. | El selector adelantó `revisar-version` al restaurar el informe, antes de añadir la referencia. |
| D6 · Origen de la aprobación | El mismo commit introduce B y borra la huella de la aprobación escueta de A. La prueba comprueba que las huellas difieren, confirma un rechazo de B y después una aprobación con la huella de B y explicación propia. Exige que el selector avance a `revisar-version` y que el cierre quede libre. | Las huellas eran distintas. Tras aprobar B, el selector mantuvo `revisar-tarea`. |
| D7 · Rechazo propio seguido de una cita | El principal devuelve código 0 y declara el rechazo antes de una aprobación citada en la misma línea. La prueba exige que las métricas atribuyan el único dictamen a `claude` y que la lista de llamadas contenga únicamente al principal. D4 conserva su entrada y ambas aserciones al compartir el auxiliar. H3 conserva el control donde el único veredicto del principal está dentro de la cita y corresponde llamar a la reserva. | Las métricas registraron a `claude` sin dictamen y a `codex` con `APROBADO`. |

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Cada caso reproduce la secuencia concreta del hallazgo. D3 comprueba también qué permite levantar el rechazo. |
| Aserciones | 9/10 | D3 y D6 comprueban el selector y los pendientes de cierre. D7 contrasta el dictamen registrado con las llamadas efectivas al proveedor simulado. |
| Rojo correcto | 10/10 | Los tres fallos son de aserción y corresponden a la decisión errónea prevista en cada recorrido. |
| Estabilidad | 9/10 | Cada caso tiene su propio repositorio Git temporal. Las huellas y referencias proceden de ese historial y las respuestas de los proveedores son fijas. |

**Evidencia y límites.** El delta de `skills/orquestar/test_progreso.py` va del blob aprobado `6fcc7ff` al blob local `7336614f0dbc5a4eb2593de236a5b13300713190`. La ejecución dirigida aportada para el árbol `e453d91f77b9222c05607e4b4f7d3dc0e7441d5b` registró tres fallos de aserción en 3,950 s. Las aserciones posteriores a cada fallo se evaluaron por lectura. Se reutilizó el verde de Ruff selectivo del mismo árbol. Tipado sin configurar.

**Destino de los hallazgos de producto.** D3 (🔴 crítico), D6 y D7 (🟠 alta) siguen abiertos para Artemisa (`desarrollador`), con destino `resolver` en C2. El resto conserva el dictamen precedente.
