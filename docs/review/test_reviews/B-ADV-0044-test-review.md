**Veredicto:** APROBADO

# B-ADV-0044 · Reevaluación C1 de las pruebas de D24–D26

**Media 9,75/10.** Las tres regresiones fallan en los dos consumidores del dictamen. Sus tres controles pasan en ambos. En las seis entradas, Hades emite el mismo rechazo exterior. Cada control cambia únicamente la presentación del texto que lo precede.

| Caso | Diferencia entre regresión y control | Resultado observado en la regresión con `motor.agente` | Resultado observado en la regresión con `pendientes_cierre` |
|---|---|---|---|
| D24 | La línea del fragmento empieza por `2. ejemplo`. El control antepone `paso `. | Claude registra la aprobación citada. | Devuelve `[]` y permite cerrar la ficha rechazada. |
| D25 | Las dos líneas que continúan la viñeta carecen de sangría. El control añade dos espacios delante de cada una. | Claude registra la aprobación citada. | Devuelve `[]` y permite cerrar la ficha rechazada. |
| D26 | El nombre `archivo.py` va entre acentos graves antes de la apertura de `<pre>`. El control quita solo esos dos acentos. | Claude queda sin dictamen y Codex registra la aprobación de la reserva. | Mantiene la ficha pendiente por «informe sin veredicto formal». |

En los tres controles se observa una sola llamada a Claude con el modelo principal y una sola métrica de Hades con su rechazo. El preflight encuentra «informe rechazado» en la entrada de la ficha completada `B-DEMO-0001`. Exigir el motivo concreto permite detectar D26 incluso cuando la barrera de cierre sigue activa.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Cada prueba entrega el mismo informe a los dos consumidores mediante subpruebas. Así se observa la decisión de cierre incluso después del fallo de atribución al proveedor. El triaje incluye el módulo que contiene las seis pruebas. |
| Aserciones | 9/10 | El arnés contrasta las métricas de Hades y las llamadas efectivas por proveedor y modelo. El preflight lee el informe y la ficha completada tras un commit real. Comprueba el ID y el motivo en la misma entrada mediante subcadenas. |
| Rojo correcto | 10/10 | Los seis fallos son de aserción y muestran las discrepancias de la tabla. Los controles alcanzan las mismas comprobaciones con la misma preparación. |
| Estabilidad | 10/10 | Cada prueba usa un repositorio Git temporal propio, configuración Git aislada y respuestas fijas de los proveedores simulados. Las aserciones son independientes del reloj y del orden entre pruebas. |

## Hallazgos y destino

**C1 queda sin hallazgos nuevos ni pendientes.** H1–H4 y N1–N10 constaban resueltos y el delta conserva las pruebas anteriores. La revisión D aportada dio por resueltos D21–D23. D24, D25 y D26 conservan su destino de producto `resolver` en C2, a cargo de Artemisa (`desarrollador`).

## Evidencia y límites

El archivo de pruebas del árbol de trabajo coincide con el del árbol verificado `3b74053034b7ed7c30f99e3a9d45945b14b77194`. La ejecución focalizada adjunta registró `FF.FF.FF.` en 6,102 s para seis métodos. Los seis fallos corresponden a dos subpruebas por regresión. En las tres subpruebas rojas de proveedor, la aserción sobre métricas falló antes de alcanzar la de llamadas efectivas. Los tres controles sí verificaron ambas.

El dictamen cubre las pruebas y su preparación. Se reutilizaron la ejecución focalizada y el resultado verde de Ruff selectivo (`E9,F63,F7,F82`). El proyecto carece de tipador declarado. Esta ronda no ejecutó la suite completa ni verificó una corrección de producción.
