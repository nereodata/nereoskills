**Veredicto:** APROBADO

# B-ADV-0044 · Reevaluación independiente de pruebas

**Puntuación media: 9,25/10.** Rama `hotfix/v1.1.3`, perfil estricto. Árbol `5ff63caabd43347c22539f87f87c8c827a72db6e`, ronda anterior `b0dce90fafcf6d0d435126211f9dd7baf0ca5d40`, base de calidad `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`.

Los tres hallazgos de la ronda anterior quedan **resueltos**. Para cada uno hay un contraste que introduce el defecto concreto y muestra dónde lo detecta la prueba. Las tres pruebas pasan sobre el árbol dictaminado. Queda una observación menor sobre una aserción que se perdió al reforzar N1.

## Hallazgos de la ronda anterior

| Hallazgo | Estado | Evidencia |
|---|---|---|
| N1 🟠 · Una huella caducada podía acreditar el producto actual | **Resuelto** | `test_huella_anterior_no_libera_el_producto_actual` obtiene la huella de A, cambia `producto.py` para producir B y conserva la aprobación de A con una nota administrativa. Exige que `cierre_revisado` deniegue el cierre y que el único pendiente de release identifique el bug. Comprueba que las huellas difieren. Sobre el mismo B, con la misma nota, el mismo ID, la misma base y el mismo paso `bug-fix`, sustituir la huella por la de B permite cerrar y deja vacía la lista de pendientes. La variante `vigente = bool(actual[1])` falló al aceptar la huella de A. El caso del informe antiguo sin huella se conserva por separado. |
| N2 🟠 · La prueba no observaba la entrega del diagnóstico | **Resuelto** | La prueba simula la respuesta JSON del proveedor, invoca `motor.agente` y entrega la salida capturada a `diagnostico_suite.leer_dictamen`. Compara el resultado completo con los valores esperados de `causa`, `decision`, `destino`, `responsable` e `intervencion`. También exige retorno 0, una única llamada al perfil principal y ausencia de revisión pendiente. Al sustituir la emisión por una línea vacía, el lector real lanzó `DiagnosticoPendiente` en la comprobación de entrega. Esa excepción acredita la pérdida del contenido en el punto que debía detectarla. |
| N3 🟡 · Restaurar el índice a `HEAD` podía pasar inadvertido | **Resuelto** | `test_wip_rastreado_aunque_ignorado` parte de `return n` en `HEAD`, prepara `return n + n` en el índice y después deja `return 2*n` en el directorio de trabajo. Exige que cambien `firma` y `arbol` y que `git ls-files --stage` conserve la instantánea preparada. La variante que ejecuta `git read-tree HEAD` falló en esa última comparación. |

## Hallazgos anteriores de C1 y regresiones de D

| Hallazgo de C1 | Estado | Comprobación conservada |
|---|---|---|
| H1 🟠 · Perfiles autorizados | **Resuelto** | Se exige el modelo fijado en el caso estricto y la secuencia principal–reserva antes y después de la recarga y tras el arranque manual. |
| H2 🟠 · Espera por cuota | **Resuelto** | Se observa la llamada a `esperar` con la demora registrada para la reserva agotada y se comprueba el consumo de ambos intentos. |
| H3 🟡 · Reformulación del impedimento | **Resuelto** | Dos invocaciones confirman redacciones y fechas fijas distintas en la ficha y el resumen. Tras el segundo commit se exige la parada con el paso y el ID correctos. |
| H4 🟡 · Informe del ID correcto | **Resuelto** | La aserción de ausencia del informe usa el ID del caso, también para `task-dev`. |

En las regresiones solicitadas por D, H1 conserva la consulta al selector y al preflight de release sobre el disco que dejó el retorno erróneo. H2 queda cubierto por el contraste de huellas de N1. H3 y H4 conservan la distinción entre cita y dictamen y el uso de la reserva en la misma invocación. H5 conserva las cuatro filas de consumo y la exclusión de los reintentos técnicos del acumulado ordinario. H6 queda reforzado por N3. H7 conserva el contraste entre selección y recuperación para una ficha antigua sin `depende_de`. Esta valoración corresponde a la cobertura de pruebas. El dictamen de código de D sigue su propia revisión.

## Hallazgo nuevo

**N4 🔵 BAJA · Se pierde una comprobación positiva de `revisar-tarea`. Destino `resolver`, responsable `desarrollador`.** En la ronda anterior, el caso de reevaluación comprobaba que `cierre_revisado` aceptaba la aprobación vigente al entrar por `revisar-tarea`. El cambio a `bug-fix` permite comparar A y B por la misma vía, como exigía N1. El caso ya no detectaría un rechazo específico de `revisar-tarea` sobre ese mismo estado de disco. Basta conservar la nueva pareja de aserciones de `bug-fix` y añadir, tras confirmar la huella de B, la aserción positiva anterior para `revisar-tarea`. La observación afecta a esa entrada adicional y no reabre N1.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 9/10 | Se cubren los seis escenarios del triaje y los tres defectos de cobertura de la última ronda. N4 identifica la comprobación puntual que se ha perdido. |
| Aserciones | 10/10 | Los contrastes observan la decisión de cierre y release, los cinco valores recuperados por el consumidor y el contenido preparado en el índice. Cada defecto introducido infringe una comprobación concreta. |
| Rojo correcto | 9/10 | Las variantes de N1 y N3 producen fallos de aserción en el cierre y el índice. La de N2 alcanza el lector y falla porque el diagnóstico se perdió. Los rojos históricos aportan evidencia adicional para las regresiones de D. |
| Estabilidad | 9/10 | Los casos usan repositorios temporales, configuración Git aislada, datos fijos y proveedores y esperas simulados. Los resultados dependen de estados y salidas observables. |

## Evidencia y límites

Para `5ff63caabd43347c22539f87f87c8c827a72db6e` se reutilizaron las cuatro verificaciones aportadas en verde: `git diff --check`, el escaneo de patrones de secretos sobre el delta, Ruff con `E9,F63,F7,F82` y las tres pruebas de N1–N3, ejecutadas en 6,143 s. Los contrastes en rojo corresponden a sus respectivas variantes. Las 119 pruebas dirigidas pasaron en 194,650 s sobre `c79c4254e742a8b1996a8145f38445430989cb2d`. Durante esa ejecución cambió la ficha independiente B-ADV-0045, por lo que el resultado se atribuye únicamente a esa identidad. La suite completa corresponde al cierre de versión.

La lectura directa del agente, la skill y el fichero de pruebas falló al iniciar el proceso con `registered Core launch requires an installed app`. Las copias literales de Hades y `/review-test`, los informes previos, los escenarios, ambos deltas y las evidencias adjuntas fueron suficientes para dictaminar. No se repitieron comandos de verificación ni se modificaron ficheros.

**Destino del informe:** `docs/review/test_reviews/B-ADV-0044-test-review.md`, para transcripción literal.
