**Veredicto:** RECHAZADO
Producto revisado: 381878a43ad2164a6a74852edf841f04840ff7ca852c6ffe9d0d12aebf2dca14
Rechazo reevaluado: 2d780edd0cc1872cf489c32ec62732364196b6d0

# B-ADV-0044 · Reevaluación independiente de código D

**Calificación global de 7,00/10.** Las tres regresiones de la última C1 pasan en el árbol `cff52f5481280368df0943abe889928d6e0e88fe`. D7 queda resuelto. D3 y D6 persisten en dos recorridos de compatibilidad del informe canónico. D8 afecta a la renovación de intentos al incorporar una respuesta durante la espera del bucle.

## Estado de los hallazgos anteriores

| Hallazgo | Estado | Comprobación |
|---|---|---|
| D3 · Restauración de un informe revocado | **Persiste.** Resuelto el caso del lenguaje del ejemplo. | Se omite la etiqueta de lenguaje y se conservan las palabras del ejemplo. La regresión comprueba el bloqueo de la copia y el cierre con la referencia correcta. Al retirar el cerco exterior de un informe íntegro aún se libera el cierre. |
| D6 · Atribución entre productos | **Persiste.** Resuelto el caso con huella explícita en la nueva aprobación de B. | El recorrido cronológico conserva la huella de A cuando una nota la elimina al introducir B. Si la aprobación propia de B es histórica y carece de huella, la comparación vuelve a mezclar los productos. |
| D7 · Rechazo propio antes de una cita HTML | **Resuelto.** | El lector entrega el prefijo visible y omite el contenido del `blockquote`. La regresión acredita un único rechazo de `claude` y una sola llamada al principal. El control H3 sigue activando la reserva cuando la única aprobación está citada. |
| H1–H7, D1, D2, D4 y D5 | **Siguen resueltos en los recorridos acreditados.** | Se mantienen el objetivo por ID tras relanzar, la recuperación de la cabecera y de la referencia, la selección de reserva, el consumo, el WIP rastreado, las dependencias históricas, el avance por reevaluación, el mandato temporal y el rechazo tras el encabezado citado. |

## Hallazgos que persisten

### D3 · 🔴 Crítico · Quitar el cerco exterior permite cerrar con una aprobación revocada

En un Git temporal confirmé una aprobación con huella de A y el cuerpo «Revisado el doble.», envuelta íntegramente en un bloque `~~~markdown`. El selector permitió `revisar-version`. Confirmé un rechazo de A y comprobé que pasó a `revisar-tarea`. Restauré en el WIP la aprobación original quitando únicamente las dos líneas del cerco. **El selector volvió a `revisar-version` y `pendientes_cierre` devolvió `[]`.** El producto, el veredicto, la huella y las palabras de la revisión eran los mismos.

El lector de cabeceras admite expresamente ese envoltorio y lo retira en `adevv/revisiones.py:97`. El comparador histórico lee el texto crudo en `adevv/revisiones.py:188`. Dentro del cerco cuenta las palabras de la cabecera y la propia huella como cuerpo. Al retirar el cerco, excluye esos campos. La comprobación de subsecuencia en la línea 243 pierde la coincidencia y la huella de A permite cerrar.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Normalizar el envoltorio de informe completo de manera coherente en ambas lecturas, conservando el contenido de los ejemplos internos. En esta secuencia el selector debe mantener el ID en `revisar-tarea` y el preflight debe incluirlo hasta una reevaluación válida.

### D6 · 🟠 Alta · Una aprobación histórica propia de B queda bloqueada por la aprobación escueta de A

Para el mismo ID confirmé una aprobación de A con huella y cuerpo vacío. Cambié el código a B y confirmé un rechazo. Después confirmé una aprobación de B en formato histórico, sin línea de huella y con una explicación propia. Verifiqué que las huellas de A y B difieren. **El selector mantuvo `revisar-tarea` y el preflight diagnosticó «aprobación restaurada anterior al rechazo».**

La aprobación actual tiene un commit de emisión conocido. En `adevv/revisiones.py:238`, el filtro por producto solo se aplica si hay huella explícita en esa aprobación. Así llega a la línea 243 el cuerpo vacío de A, que coincide por construcción con cualquier explicación. El retorno anticipado impide aplicar la acreditación histórica por commit prevista en la línea 279.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Comparar los productos de ambas emisiones usando su commit cuando falte la huella declarada. La aprobación histórica de B debe liberar el selector y el preflight. La copia revocada del mismo producto debe seguir pendiente.

## Hallazgo nuevo

### D8 · 🟠 Alta · Una respuesta incorporada durante la espera deja consumido el intento anterior

Ejercité `bucle` con dos intentos y un fallo técnico sin dictamen. Entre pasos abrí una pregunta para ese ID. El selector alcanzó la espera de intervención. Entregué la respuesta por el adaptador local con el motor activo y dejé que la espera real la incorporase. La pregunta terminó en `incorporada`. **El siguiente fallo técnico paró el bucle con código 2. Hubo dos llamadas en total, una antes y una después de responder.** Con la renovación documentada corresponden tres, una antes y dos después.

En `skills/orquestar/orquestar.py:139`, `esperar_intervencion` consume las respuestas incorporadas y devuelve un booleano. El bucle continúa y, en la línea 3687, la cola ya está vacía. Por tanto, no borra el contador de ese ID. La siguiente revisión sin avance alcanza el límite en la línea 4048. La incorporación ordinaria en la cabecera del bucle, cubierta por el verde dirigido, sí entrega los IDs al reinicio.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Hacer llegar al mismo reinicio por ID las respuestas incorporadas durante la espera. Conservar el presupuesto consumido por otros IDs y comprobar el número de llamadas después de reanudar.

## Alcance y evidencia

Contrasté el delta de B-ADV-0044 desde la base de triaje `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` con el diseño, la guía, la firma por paso, la recuperación por error y cuota, la transferencia de contadores en recarga y los consumidores del dictamen. El triaje sitúa el origen del reinicio por HEAD en `31d7acd` y documenta cómo se añadieron el WIP y la recuperación por cambios confirmados. Los cambios concurrentes de otros IDs conservan su autoría. C1 mantiene su aprobación de **9,50/10**.

Antes de escribir el informe comprobé en Git la coincidencia del árbol de trabajo rastreado con el árbol de evidencia, recalculé la huella SHA-256 de sus entradas de producto y verifiqué que la última modificación confirmada del informe canónico era el rechazo de la cabecera. Las tres comprobaciones adicionales descritas arriba usaron repositorios Git temporales ya retirados, el código de este árbol y proveedores simulados. Se observaron los resultados del selector y el preflight para D3 y D6, y el estado de la pregunta, las llamadas y la salida de `bucle` para D8.

**Verificación reutilizada.** Las tres regresiones estaban en rojo por aserción en `e453d91f77`. En el árbol revisado pasaron 161 pruebas dirigidas en 259,395 s. Ruff selectivo, ambas comprobaciones de `git diff --check` y el escaneo de secretos terminaron con código 0. `--calidad` terminó con código 0 e informó de que había omitido formato y lint por ausencia de herramientas. Ruff se ejecutó por separado. El proyecto carece de tipado configurado y el delta conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | D3 permite un cierre indebido. D6 impide un cierre válido y D8 detiene una revisión un intento antes de lo debido. |
| Seguridad | 9/10 | Las consultas Git pasan argumentos separados y el escaneo de secretos está en verde. |
| Conformidad | 6/10 | Se conservan las capas y la biblioteca estándar. Persisten diferencias con el diseño en la identidad del informe histórico y la renovación de intentos por ID. |
| Calidad | 7/10 | Selector y preflight comparten la decisión de vigencia. La cabecera y el comparador interpretan de dos maneras el mismo envoltorio admitido. |
| Eficiencia | 8/10 | La reconstrucción consulta la historia de la ruta canónica y lee un blob por revisión confirmada. |
| Documentación | 7/10 | La guía recoge el límite y la persistencia. La garantía de renovación de intentos tras una respuesta falla en la vía de espera. |
