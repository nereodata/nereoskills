# B-ADV-0046 · Revisión de pruebas de C1

**Veredicto: RECHAZADO**
**Revisor:** Hades · `/review-test` · perfil fijado de la versión 1.1.2
**Alcance:** seis escenarios `@metricas`, incluidas las dos variantes del escenario de recuperación explícita.

| Criterio | Puntuación | Fundamento |
|---|---:|---|
| Cobertura | 7/10 | Las pruebas ejercitan los seis casos. La de cuatro productores solo entra por un escritor y la del cursor omite comprobar el acortamiento que debe provocar la regresión. |
| Aserciones | 8/10 | Se comprueban la multiplicidad, el contenido Unicode, los totales y la evidencia original. Algunas aserciones imponen detalles de serialización y publicación ajenos a los escenarios. |
| Rojo correcto | 9/10 | El triaje reproduce fallos de sesión, diagnóstico, decodificación y recogida de A. Dos pruebas se detienen en operaciones de observación o recuperación todavía ausentes. |
| Estabilidad | 7/10 | Los registros son sintéticos y los procesos se coordinan sin pausas arbitrarias. La prueba de solapamiento depende de las primitivas concretas de publicación y bloqueo. |
| **Media** | **7,75/10** | **Dos hallazgos de severidad alta.** |

## Contraste con los seis escenarios

| Escenario | Valoración |
|---|---|
| 1. Sesión y cola parcial | Se escribe S seguida de media fila, se consulta la sesión y se completa la fila en una segunda escritura. El mismo cursor debe entregar V1 una vez y después devolver vacío. El rojo observado es `None != 'S'`. |
| 2. Recuperación explícita | Para JSON inválido y para el byte `FF` se exigen diagnóstico de línea 2, rechazo de la exportación sin totales parciales, copia íntegra y conservación de 7 tokens, 0,25 USD y una verificación tras ambas recuperaciones. El rojo distingue la ausencia de diagnóstico para JSON inválido del error de decodificación para `FF`. |
| 3. Cuatro productores concurrentes | La barrera reúne a cuatro procesos reales. La comparación de los 400 objetos completos detecta pérdidas, duplicados y alteraciones de contenido. Los cuatro procesos llaman directamente a `motor.registrar`. |
| 4. A completado antes de observar la corrupción | El repositorio Git temporal contiene el cierre y la revisión de A. La prueba comprueba consumo y aprobación, consulta el selector y exige la secuencia exacta de invocaciones A, B entre ambos arranques. El rojo reproduce `JSONDecodeError` al recoger A. |
| 5. Observador tras acortar el registro | La primera consulta recibe V1 y se reutiliza su cursor para exigir V2 una vez y luego vacío. Falta verificar que la recuperación quitó el fragmento antes de añadir V2. |
| 6. Escritura durante la recuperación | Un proceso independiente registra E3. Se cotejan los tres eventos en orden y todos los bytes de la copia. La coordinación puede agotar la espera aunque se conserve correctamente la escritura confirmada. |

## Hallazgos

1. **🟠 ALTA · Los cuatro productores se sustituyen por cuatro llamadas al mismo escritor.** En `test_cuatro_productores_con_cola_interrumpida`, el argumento `tipo` solo cambia los datos de `evento`. Si el gateway omite registrar un evento o usa una ruta de escritura que pierde el fragmento, los 400 objetos de la prueba aún pueden coincidir. **Para:** desarrollador. **Destino:** `resolver` en las pruebas de C1. Ejercitar el punto de registro que usa cada productor. Si los cuatro delegan en el mismo escritor, basta con comprobar esa delegación desde cada entrada y conservar la prueba concurrente para el escritor compartido.

2. **🟠 ALTA · La prueba de solapamiento exige un protocolo de bloqueo concreto.** En `test_escritura_coincide_con_publicacion_de_recuperacion`, la recuperación espera dentro de `os.replace`. El escritor señala `solicitado` al entrar en `msvcrt.locking` o `fcntl.flock`, o al terminar de escribir. Un escritor que espere correctamente mediante otra primitiva queda bloqueado mientras la recuperación espera su señal durante 30 segundos. Una publicación atómica que no pase por ese `os.replace` tampoco activa al hijo. **Para:** desarrollador. **Destino:** `resolver` en las pruebas de C1. Coordinar la ventana entre lectura y publicación con un punto de sincronización controlable y señalar la solicitud de E3 al entrar en la operación de registro, antes de que pueda bloquearse. Mantener la confirmación del hijo y el cotejo final del activo y de la evidencia.

3. **🟡 MEDIA · El escenario del cursor puede pasar sin haber acortado el archivo.** En `test_cursor_tras_recuperacion`, un retorno cero de la recuperación permite continuar. Si el fragmento `?\n` sigue presente, un cursor que falle únicamente al acortarse el registro podría entregar V2 y superar ambas aserciones. **Para:** desarrollador. **Destino:** `resolver`. Antes de registrar V2, leer directamente el activo y exigir dos filas físicas válidas, consumo y V1 en ese orden.

4. **🟡 MEDIA · La recuperación exige una representación concreta del activo y de la copia.** En `test_estado_exportacion_y_recuperacion_idempotente`, las filas activas deben conservar exactamente la serialización y los finales CRLF de la prueba. La búsqueda de evidencia también exige extensión `.jsonl` y un nombre publicado en stdout. El escenario exige orden y contenido en el activo, e identidad byte a byte y disponibilidad para la evidencia. Una copia íntegra con extensión `.bak` o un activo equivalente con finales LF quedarían rechazados. **Para:** desarrollador. **Destino:** `resolver`. Comparar las dos filas activas como objetos JSON en ambas recuperaciones y localizar la evidencia por su contenido en el directorio temporal, conservando su ruta para la segunda comprobación.

## Evidencia de la revisión

Se aceptó el `git diff --check` verde comunicado para `454b6c51a1`. El verificador ejecutó exclusivamente el triaje de C1 en rojo, con 17 pruebas, 2 fallos y 5 errores. Los dos `AttributeError` corresponden a `nuevas_metricas` y `recuperar` y dejan pendientes las aserciones posteriores de esos casos. No hay lint, formato ni tipado configurados. La revisión se realizó sobre los materiales adjuntos, sin repetir verificaciones ni evaluar código de producción.
