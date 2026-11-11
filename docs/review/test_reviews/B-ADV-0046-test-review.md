# B-ADV-0046 · Revisión de pruebas de C1

Veredicto: APROBADO

**Revisor:** Hades · `/review-test` v1.1.2
**Árbol evaluado:** `dd1701d2ae`
**Destino:** `docs/review/test_reviews/B-ADV-0046-test-review.md`
**Responsable de persistir el informe:** Artemisa

| Criterio | Anterior | Actual | Fundamento |
|---|---:|---:|---|
| Cobertura | 7/10 | 9/10 | Los seis escenarios tienen comprobaciones de comportamiento. El delta conecta las cuatro entradas con el escritor sometido a concurrencia y comprueba el estado del activo antes de añadir V2. |
| Aserciones | 8/10 | 9/10 | Se contrastan los 400 objetos completos con su multiplicidad, las filas válidas en orden, los totales exportados y los bytes de la evidencia después de la segunda recuperación. |
| Rojo correcto | 9/10 | 8/10 | El triaje reproduce la pérdida de sesión, la falta de diagnóstico y los errores de lectura y recogida de A. El caso de solapamiento se detiene antes de solicitar E3 por la ausencia de un atributo interno. |
| Estabilidad | 7/10 | 9/10 | La barrera y los eventos coordinan procesos independientes. El aviso del escritor precede a cualquier bloqueo y se comprueba la terminación del hijo. |
| **Media** | **7,75/10** | **8,75/10** | **Sin hallazgos críticos ni altos.** |

## Dictamen sobre H1–H4

| Hallazgo anterior | Dictamen | Evidencia del delta |
|---|---|---|
| **H1 🟠 · Cuatro productores representados por un único escritor** | **Resuelto** | `test_reanuda_con_metricas_corruptas` observa que el bucle entrega al escritor exactamente un paso `bug-fix` para A. La nueva prueba invoca `agente`, `verificar` y `gateway.invocar`, deja actuar al escritor real y lee las tres filas del activo. La barrera conserva su cometido de someter ese escritor a cuatro procesos y cotejar los 400 objetos Unicode. |
| **H2 🟠 · Dependencia de una primitiva de bloqueo y de `os.replace`** | **Resuelto en su severidad alta** | La recuperación abre la ventana tras guardar la evidencia. El hijo anuncia la solicitud al entrar en el registro de E3, antes de poder bloquearse. El padre exige que el hijo termine con código cero, coteja la copia íntegra y comprueba `[CONSUMO, V1, V2]`. Queda una limitación en la evidencia roja, detallada abajo. |
| **H3 🟡 · El cursor podía pasar con el fragmento todavía presente** | **Resuelto** | Antes de registrar V2, `filas_activas()` decodifica y analiza cada línea física del activo. Si `?\n` sigue presente, la prueba falla en ese punto. Tras comprobar exactamente `[CONSUMO, V1]`, reutiliza el cursor anterior y exige `[V2]` y después `[]`. |
| **H4 🟡 · Serialización del activo y nombre de la copia impuestos** | **Resuelto** | Para ambos fragmentos se comparan los objetos activos después de cada recuperación. La primera copia se localiza por sus bytes, sin exigir extensión ni anuncio en stdout. Después de la segunda recuperación se vuelve a leer **esa misma ruta** y se coteja con el original. |

## Contraste con los seis escenarios

| Escenario | Qué demuestra la prueba |
|---|---|
| 1. Sesión y cola parcial | Sitúa el corte dentro de V1, exige recuperar la sesión S y lee solo la fila completa sin diagnóstico. Al completar la escritura, el mismo observador recibe V1 una vez. |
| 2. Recuperación explícita | Tanto con JSON inválido como con `FF`, exige diagnóstico de línea 2, exportación estricta rechazada con stdout vacío y original íntegro. Tras cada recuperación exige las dos filas en orden y una exportación de 7 tokens, 0,25 USD y una verificación. |
| 3. Cuatro productores concurrentes | Además de la delegación de H1, comprueba la fila original, el diagnóstico de línea 2, la conservación del fragmento y la multiplicidad exacta de los 400 eventos. |
| 4. A completado antes de observar la corrupción | Comprueba el commit de cierre, la ficha completada, el consumo y la aprobación de A. Tras recuperar, el selector elige B y la secuencia acumulada de invocaciones es exactamente A, B. |
| 5. Observador tras la recuperación | Verifica directamente que quedan las dos filas válidas antes de añadir V2. La siguiente consulta usa el cursor obtenido antes de recuperar. |
| 6. Escritura durante la recuperación | Coordina la solicitud de E3 desde otro proceso y exige su confirmación, los tres eventos en orden y la evidencia original con `FF 0A` entre E1 y E2. |

## Hallazgos residuales

- **🟡 MEDIA · El rojo del solapamiento se produce al preparar la sincronización.** En el triaje anterior faltaba `recuperar`. En el actual, el acceso a `motor.metricas.registro_metricas` lanza `AttributeError` antes de arrancar el hijo. La traza actual no alcanza las aserciones sobre E3. **Destino:** comprobación focalizada al disponer de la recuperación. **Responsable:** desarrollador de B-ADV-0046.
- **🔵 BAJA · La prueba concurrente fija el separador posterior al fragmento.** `startswith(linea(CONSUMO) + fragmento + b'\n')` rechazaría un separador `CRLF` aunque los bytes del fragmento siguieran disponibles y el diagnóstico indicara la línea 2. **Destino:** ajuste menor en `test_cuatro_productores_con_cola_interrumpida`. **Responsable:** desarrollador de B-ADV-0046.

## Evidencia utilizada

El triaje aportado contiene **18 pruebas, 2 fallos y 5 errores**. Se acepta el verde comunicado para `test_agente_verificacion_y_gateway_delegan_en_registrar` y `git diff --check` sobre `dd1701d2ae`. Lint y tipado carecen de configuración. El arnés impidió abrir los archivos instalados de Hades y de la skill. El dictamen se basa en la skill v1.1.2, el informe anterior, los escenarios, las pruebas, el diff y las trazas suministrados. No se repitieron ejecuciones.

---

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
