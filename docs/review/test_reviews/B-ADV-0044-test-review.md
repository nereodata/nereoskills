**Veredicto:** APROBADO · **9,50/10**

# B-ADV-0044 · Reevaluación independiente de pruebas C1

Las cuatro pruebas reproducen los defectos de D3, H3, D5 y D6 por sus efectos observables en el selector de tareas o en la invocación de la reserva. Los hallazgos anteriores de C1, H1–H4 y N1–N8, siguen resueltos. **Hallazgos nuevos de pruebas: ninguno.**

| Caso | Qué distingue la prueba | Rojo observado |
|---|---|---|
| D3 | Tras aprobar y rechazar el mismo producto, restaura en el WIP la aprobación con las mismas palabras, una línea vacía y cuatro espacios delante del párrafo. Exige que el ID siga pendiente. Conserva el control positivo de una reevaluación con texto propio. | El selector adelantó `revisar-version` cuando correspondía `revisar-tarea` para `B-DEMO-0001`. |
| H3 | El principal devuelve código 0 con una aprobación citada en un `blockquote` que empieza después de texto y cuya etiqueta continúa en la línea siguiente. La prueba exige llamadas efectivas al principal y a la reserva, ausencia de veredicto del primero y rechazo de la segunda en la misma invocación. | Las métricas solo registraron a `claude`. La prueba esperaba la secuencia `claude`, `codex`. |
| D5 | Confirma en Git una reevaluación que cita el SHA del primer rechazo y comprueba que el cierre está libre. Inserta únicamente una nota entre la huella y la referencia. Exige que la aprobación conserve su vigencia y que, tras un segundo rechazo, restaurar ese informe en el WIP deje el ID pendiente. | El control previo a la nota pasó. Después de confirmarla, el selector volvió a `revisar-tarea`. |
| D6 | Para el mismo ID, confirma una aprobación escueta y un rechazo de A. Corrige después `producto.py`, comprueba que B tiene otra huella y confirma una aprobación de B con explicación propia. Exige `revisar-version` y una lista de pendientes vacía. | El selector mantuvo `revisar-tarea` después de aprobar B. |

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Las cuatro entradas reproducen las condiciones identificadas en D. D5 cubre también la precedencia de un rechazo posterior. |
| Aserciones | 9/10 | D3, D5 y D6 consultan el selector y el preflight de cierre. H3 contrasta las llamadas al proveedor con la atribución del dictamen en métricas. |
| Rojo correcto | 10/10 | Las cuatro pruebas llegaron a una aserción de comportamiento y fallaron en la decisión prevista para su defecto. |
| Estabilidad | 9/10 | Cada caso usa un repositorio Git temporal aislado. Las referencias se obtienen de sus commits y las respuestas de los proveedores están simuladas. |

**Evidencia.** El archivo local `skills/orquestar/test_progreso.py` coincide con el blob del delta `6fcc7ff5c322c2a182cfe44e6f147e38bf2b5682`. La ejecución dirigida aportada para el árbol `41e0939b3365d0f3cadf5a2117dda0ad64ba640a` registró cuatro fallos de aserción en 6,413 s. Cada caso se detuvo en el primer fallo descrito en la tabla. Las aserciones posteriores se evaluaron por lectura. Ruff selectivo pasó en ese árbol y el proyecto carece de tipado configurado.

**Responsable.** Artemisa (`desarrollador`) conserva D3, H3, D5 y D6 con destino `resolver` en C2. El dictamen aprueba las regresiones de C1. Los cuatro defectos de producto siguen abiertos.
