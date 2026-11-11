**Veredicto:** APROBADO · **9,50/10**

# B-ADV-0044 · Reevaluación independiente de pruebas C1

**N8 resuelto.** La prueba distingue una aprobación revocada, un rechazo anterior (R1) y el último rechazo del mismo producto (R2). Solo la reevaluación que cita R2 permite pasar a la revisión de versión. No quedan hallazgos de pruebas pendientes.

Revisé el delta de `skills/orquestar/test_progreso.py` entre `e120182fc99dd933c1c8ea8a171d07a26c49934e` y `8841db1c8976d9e180dbae79e7a0c04bf2e02d08` en `hotfix/v1.1.3`. El archivo local coincide con el blob revisado `7bed01e`.

## Reevaluación de N8

La prueba confirma en Git la aprobación, R1 y R2 para el mismo ID y la misma huella. Los dos rechazos tienen textos distintos. Después confirma una nota en el resumen de versión, de modo que `HEAD` queda un commit por delante de R2. En los tres subcasos conserva el cuerpo de la aprobación en el informe de trabajo y cambia únicamente el SHA del campo `Rechazo reevaluado`.

| SHA citado | Paso observado en el árbol actual | Comprobación previa al cierre |
|---|---|---|
| Aprobación original | `revisar-tarea` para `B-DEMO-0001` | El ID figura entre los pendientes. |
| R1, rechazo anterior | `revisar-tarea` para `B-DEMO-0001` | El ID figura entre los pendientes. |
| R2, último rechazo | `revisar-version` | La lista de pendientes está vacía. |

El caso de R1 detecta una regla que acepte cualquier rechazo histórico. El de R2 detecta una regla que exija citar el `HEAD` administrativo. **N7 sigue resuelto**: el caso D4 verifica tanto la única llamada efectiva al proveedor principal como el rechazo registrado en métricas. Los hallazgos de pruebas H1–H4 y N1–N6 conservan su estado de resueltos de la ronda anterior.

## Evidencia y alcance

El verificador cargó en memoria `6a4dd52:adevv/revisiones.py` y ejecutó la prueba actual. Registró **dos fallos de subcaso en una prueba, en 5,045 s**. Tanto al citar la aprobación como al citar R1, el selector adelantó `revisar-version`. En ambos subcasos el fallo ocurrió antes de la aserción de pendientes. El control positivo de R2 pasó.

Con el árbol actual, **las ocho pruebas dirigidas pasaron en 18,925 s**, incluidas las comprobaciones del selector y del cierre para las tres referencias. Los cuatro rojos de C1 anteriores reprodujeron defectos de producto en D3 (dos restauraciones de una aprobación revocada), H3 (apertura HTML multilínea) y D4 (rechazo propio tras un encabezado citado). Sus reproducciones están en verde en esta ejecución. El dictamen de esta ronda corresponde a las pruebas C1.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | El control cubre las tres referencias y separa el último rechazo del último commit. |
| Aserciones | 9/10 | Cada referencia exige un paso concreto y comprueba por separado los pendientes de cierre. |
| Rojo correcto | 10/10 | Las dos referencias obsoletas fallan en la decisión del selector histórico y el control válido pasa con la misma preparación. |
| Estabilidad | 9/10 | El repositorio temporal fija el orden de los commits. La prueba obtiene los SHA de Git y prescinde de fechas y valores de hash predefinidos. |

**Hallazgos nuevos de pruebas:** ninguno. Se reutilizó la evidencia aportada de ejecución, Ruff, escaneo de secretos y comprobaciones de diferencias Git.
