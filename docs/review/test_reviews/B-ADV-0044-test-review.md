**Veredicto:** RECHAZADO · **8,50/10**

# B-ADV-0044 · Reevaluación independiente de pruebas C1

D3 y D8 quedan cubiertos. D6 tiene un rojo de comportamiento, pero el último rechazo de su historial pertenece a A. En el incidente documentado, el último rechazo pertenecía a B y la aprobación histórica posterior de B debía liberar el cierre. Queda un hallazgo de pruebas.

## Hallazgo nuevo

### N9 · 🟠 Alta · Falta la aprobación histórica de B después de un rechazo de B

En `skills/orquestar/test_progreso.py:489`, el auxiliar confirma el rechazo con `huella_a` y después introduce B. Sus dos variantes cambian únicamente la presencia de `huella_b` en la aprobación final. El caso de la línea 458 sí rechaza B, pero su aprobación final lleva huella explícita. Queda sin comprobar la combinación del informe de código D6.

Una regla que permita la aprobación histórica cuando el último rechazo pertenece a otro producto, pero bloquee toda aprobación sin huella después de un rechazo del producto actual, podría satisfacer estos controles y seguir bloqueando la aprobación legítima de B.

**Para** Artemisa (`desarrollador`). **Destino** `resolver` en C1. Conservar los controles aprobados. En el nuevo caso histórico, confirmar la aprobación escueta de A con su huella, introducir B con una huella distinta, confirmar el rechazo de B y luego confirmar una aprobación de B con explicación propia y sin línea de huella. Exigir que el selector avance a `revisar-version` y que `pendientes_cierre` quede vacío. El control de restauración revocada del mismo producto debe seguir exigiendo revisión.

## Hallazgos de producto y controles

| Hallazgo | Evidencia de C1 | Estado, responsable y destino |
|---|---|---|
| D3 · 🔴 Crítico | La aprobación dentro del cerco exterior Markdown dejó el preflight libre. Tras el rechazo del mismo producto, restaurar el informe en el WIP quitando solo el cerco hizo que el selector adelantara `revisar-version`. La prueba exige `revisar-tarea` para ese ID y su presencia entre los pendientes. Como control positivo, una nueva evaluación con cuerpo propio debe liberar ambos consumidores. | **Persiste en producto.** Cobertura C1 aceptada. Artemisa (`desarrollador`), `resolver` en C2. |
| D6 · 🟠 Alta | Las huellas de A y B eran distintas y el selector mantuvo `revisar-tarea` tras la aprobación histórica de B. El rojo acredita el recorrido con rechazo de A. N9 identifica la combinación que falta para reproducir el recorrido documentado. | **Persiste en producto.** Artemisa (`desarrollador`), `resolver` en C2 tras completar N9 en C1. |
| D8 · 🟠 Alta | La prueba abre la pregunta después del primer intento de A y entrega la respuesta por el adaptador local durante la espera simulada. El bucle salió con código 2 y la pregunta quedó incorporada con el texto esperado. Hubo dos llamadas a A en total y se exigían tres, una antes y dos después. Como control de aislamiento, la prueba comprueba en el último estado ofrecido para recarga que B conserva su intento consumido. | **Persiste en producto.** Cobertura C1 aceptada. Artemisa (`desarrollador`), `resolver` en C2. |

H1–H4 y N1–N8 de pruebas siguen resueltos en su alcance aprobado. D7 conserva su resolución en la revisión de código precedente.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 7/10 | Falta la secuencia de D6 que combina rechazo de B y aprobación posterior de B sin huella. |
| Aserciones | 9/10 | Se observan el selector, el preflight, las llamadas al arnés, la respuesta incorporada y el presupuesto del otro ID en el estado de recarga. |
| Rojo correcto | 9/10 | Los tres fallos son de aserción. D3 y D8 reproducen el incidente exacto. En D6 el fallo corresponde a una variante del historial. |
| Estabilidad | 9/10 | Cada caso tiene un repositorio Git temporal propio. La respuesta se entrega desde la pausa simulada y el recuento de intentos es exacto. |

**Evidencia y límites.** El delta local de `skills/orquestar/test_progreso.py` coincide con el adjunto, de `7336614` a `05920d0`. Se reutilizaron los tres fallos de aserción en 6,053 s y el verde de Ruff selectivo del árbol `566d0a3ea27e1ea6f94cbce4fb0d276fe4364aa1`. Las aserciones posteriores al primer fallo de cada prueba y los controles hermanos se evaluaron por lectura. El proyecto carece de tipado configurado.
