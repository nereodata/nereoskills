**Veredicto:** APROBADO

# Revisión de pruebas: B-ADV-0026 · quinta ronda

- **Revisor:** Hades · **Fecha:** 2026-11-07 · **Skill:** `/review-test`, leída de la instalación indicada.
- **Alcance:** exclusivamente `skills/orquestar/test_intervencion_humana.py`, frente a los escenarios `@B-ADV-0026` de orquestación y Telegram y al triaje del bug.
- **Método:** revisión limitada a `test_bloqueo_incompleto_con_trabajo_ajeno_no_ejecuta_tarea`, añadida para la condición restante de RC-03, frente a CA-1/CA-2/CA-8. Se conserva el alcance aprobado de las rondas anteriores. No se ha consultado producción ni diseño. Se aplica la skill instalada `/review-test` ya leída en esta conversación.

## Puntuaciones

| Criterio | Nota | Justificación |
|---|---:|---|
| Cobertura | 9 | Conserva el alcance aprobado y añade el impedimento de recuperación por trabajo ajeno: retención de ejecución, conservación del archivo y de la pregunta, y diagnóstico global. |
| Aserciones | 9 | Las regresiones comprueban pregunta destinataria y respuesta anterior intacta, referencia Git de la rama ajena, estado en la release de origen y bloqueo recuperado. |
| Rojo correcto | 9 | Las tres nuevas pruebas alcanzan aserciones de negocio y fallan por los comportamientos que pretenden detectar, sin errores de preparación. |
| Estabilidad | 9 | Repositorios temporales con raíz explícita, ejecutores y transporte controlados, espera sustituida y recarga de módulo sin depender de una demora real. |
| **Media** | **9.00** | Superior a 8, sin hallazgos críticos ni altos abiertos. |

## Reevaluación de hallazgos anteriores

| Hallazgo | Estado | Evidencia en las pruebas revisadas |
|---|---|---|
| **RT-01 · ALTA · Espera activa sin elegibles** | **Resuelto** | `test_espera_activa_recibe_por_gateway_y_continua_sin_relanzar` (línea 662) ejecuta el bucle con espera habilitada. La espera controlada consulta preguntas y entrega la respuesta mediante el gateway. Exige la secuencia A/C y que `en_fondo` no se invoque. Complementa los casos de bucle detenido y parada manual. |
| **RT-02 · ALTA · Permisos de publicación no discriminados** | **Resuelto** | El test de autorización (línea 486) comprueba antes y después que el usuario 999 no recibe respuesta a `/cerrar` ni alcanza `cargar_cierre_version`; también verifica que el conjunto de autorizados se conserva. La comprobación del cierre normal permanece como complemento. La conclusión de autorización ya no depende del fallo de una versión incompleta. |
| **RT-03 · MEDIA · Resultados sin aserciones explícitas** | **Resuelto** | Al entrar B se exige HEAD sin `src/modulo_a.py`, además del árbol limpio y la conservación en wip. Antes de completar A reanudada se comprueban `planned`, ausencia de `pendiente_de`, pregunta incorporada y respuesta en la revisión de versión (línea 393). El caso de aviso consulta `/estado` y avanza el bucle con B controlada sin nuevos envíos (línea 255). Ambas consultas verifican tarea, pregunta e instrucción. La recarga verifica texto de pregunta, contexto y respuestas, además de incorporación única (línea 627). |
| **RT-04 · MEDIA · API de fixture en producción** | **Resuelto** | La pregunta cerrada se prepara respondiendo e incorporando mediante el flujo funcional (línea 486); desaparece `cerrar_pregunta_prueba`. Se usa la referencia realmente generada Q-ADV-0003 para comprobar el rechazo de una pregunta cerrada. La diferencia numérica respecto al ejemplo Q-ADV-0009 no altera el caso de negocio. |

La adaptación de los fixtures dirige las llamadas Git al repositorio temporal correspondiente, incluido el subproyecto de cada caso de canal. Los sustitutos conservan operaciones Git reales; no fabrican los resultados de aislamiento ni los estados del backlog.

## Evidencia de ejecución

Se reutiliza `orquestar_evidencias.jsonl`; no se han repetido pruebas ni ejecutado lint o tipado. El proyecto no tiene configuración de estas dos últimas herramientas, según el contexto recibido.

- **Rojo inicial:** 2026-11-07T12:16:44, árbol `4c05d7f1738fc122c80453ec3daf19bf856240b3`, comando `python -m unittest skills.orquestar.test_intervencion_humana`: 8 tests, 1 fallo por prompt sin `--preguntar` y 9 errores por API `solicitar_intervencion` ausente, incluidos subtests. No falla la preparación Git.
- **Verde previo:** 2026-11-07T12:21:44, árbol `fe5ff26fd51281a473dcf9b73b39b19e01114d6f`: mismo comando, 9 tests, OK.
- **Nueva ejecución acreditada disponible al revisar:** 2026-11-07T12:22:31, árbol `da7efc5c8fb9a78759990aff62f4f2c465f2cac9`: mismo comando, 9 tests, OK en 30,502 s.

El verde acredita ejecución; el veredicto se apoya en la cobertura y discriminación de las pruebas leídas. Esta revisión no emite un juicio sobre producción ni sustituye `/review-code` o la verificación de cierre indicada en el triaje.



## Delta de esta ronda

| Regresión | Evaluación de la prueba |
|---|---|
| `test_referencia_tarea_selecciona_pregunta_pendiente_actual` | Prepara una pregunta cerrada mediante respuesta e incorporación funcionales; crea otra pregunta de la misma tarea, responde por ID de tarea y exige Q-ADV-0002 con `auth.local` en cola, conservando `Interno` en Q-ADV-0001. Discrimina la selección incorrecta de la pregunta anterior. |
| `test_respuesta_se_incorpora_en_rama_de_la_tarea` | Encola con PID activo y crea otra release con Git real. La referencia de `release/v1.2` debe conservarse, mientras la tarea de `release/v1.1` queda `planned` y la pregunta incorporada. No fabrica esos estados mediante mocks. Cubre la contaminación de commits entre ramas y exige incorporación en origen. |
| `test_reinicio_completa_bloqueo_tras_publicar_registro` | Sustituye únicamente la escritura del bloqueo por un OSError controlado. Después retira el fallo y exige que el procesamiento recupere `blocked`/`humano` con una única pregunta pendiente. Antes de recuperar lee directamente el JSON y verifica una única pregunta Q-ADV-0001/Proveedor y la tarea todavía planned. Carga un módulo nuevo, recupera con él y comprueba blocked/humano y una única pregunta pendiente. |

**Nueva evidencia roja reutilizada:** `orquestar_evidencias.jsonl`, 2026-11-07T12:30:29, árbol `dd48ab2baf44390b7413373a12af1241e094b2b6`. Comando focalizado con los tres métodos anteriores: 3 tests en 4,741 s, **3 fallos y ningún error**. Fallan respectivamente porque se devuelve pregunta cerrada en lugar de Q-ADV-0002, cambia el commit de la release ajena y la tarea continúa `planned` sin `pendiente_de`. No se repite ese comando ni la suite completa. El verde de 9 pruebas corresponde al alcance anterior, no acredita estas tres regresiones nuevas en verde.

## Reevaluación final de RT-05

**RT-05 · MEDIA · Resuelto.** La prueba lee `orquestar_preguntas.json` directamente tras retirar el fallo simulado y comprueba la identidad y el texto de la única pregunta persistida. Antes de recuperar verifica que la tarea todavía está `planned`. Después carga `orquestar_corte` mediante `_cargar_modulo`, invoca `incorporar_respuestas` en esa instancia nueva y consulta con ella el estado final `blocked` / `pendiente_de: humano`. El fallo en `anotar` ya no está activo durante la recuperación. La simulación no depende de memoria de la instancia que recibió el corte.

La corrección añade observaciones del estado previo y cambia la instancia que recupera; no fabrica el resultado ni debilita las aserciones anteriores. RT-01 a RT-04 permanecen resueltos. No se amplía la revisión al código de producción ni se reabre el alcance previamente aprobado.

**Verde final disponible al revisar:** `orquestar_evidencias.jsonl`, 2026-11-07T12:33:05, árbol `4702684229a8101bd638cdf8fd953ad521a1942d`, comando `python -m unittest skills.orquestar.test_intervencion_humana`: **12 tests, OK**, en 43,209 s. Se reutiliza esta evidencia junto con los rojos históricos; no se ha ejecutado ninguna prueba en esta ronda.

## Delta de la quinta ronda

**Prueba:** `test_bloqueo_incompleto_con_trabajo_ajeno_no_ejecuta_tarea`, al final de `skills/orquestar/test_intervencion_humana.py`.

La preparación crea una tarea y commit en el repositorio temporal real. El OSError controlado se limita a la anotación inicial; el mock se retira antes de ejecutar el bucle. Después se crea un archivo ajeno con contenido concreto. La regresión no sustituye la planificación ni la recuperación, solo el ejecutor y el transporte de avisos.

El ejecutor devuelve una tupla válida `(0, {}, '')`, de modo que una ejecución indebida llega a la aserción `assert_not_called` en lugar de fallar al desempaquetar el mock. El límite de una vuelta evita reintentos prolongados y no sustituye la comprobación de ausencia de ejecución. Se exige además retorno 2, conservación literal de `trabajo_ajeno.txt`, pregunta pendiente y diagnóstico «Bloqueo global» en `parte()`.

Las aserciones cubren el bloqueo efectivo antes de ejecutar A (CA-1), la preservación del trabajo ajeno (CA-2) y la retención segura de la intervención durante la recuperación (CA-8). No son resultados fabricados por los sustitutos. Las comprobaciones posteriores a `assert_not_called` se alcanzarán al corregir la ejecución indebida; el rojo actual no se presenta como evidencia de que ya hayan pasado.

### Evidencia focalizada reutilizada

Comando: `python -m unittest skills.orquestar.test_intervencion_humana.IntervencionHumanaTests.test_bloqueo_incompleto_con_trabajo_ajeno_no_ejecuta_tarea`, conservado en `orquestar_evidencias.jsonl` mediante `--verificar`.

- **Diagnóstico inicial descartado como rojo de negocio:** 2026-11-07T12:38:30, árbol `a9c7184c36a0f202658121e6e1b875a65fe172df`: 1 test, 1 error, por retorno incompleto del mock, según el contexto recibido.
- **Rojo correcto tras corregir el ejecutor:** 2026-11-07T12:38:45, árbol `422b4e754782b737487370d272a7f75fa83a682c`: 1 test en 1,783 s, 1 fallo, ningún error. Falla `assert_not_called`: `ejecutar` fue invocado una vez. La preparación alcanza el comportamiento que se quiere impedir.

No se ha repetido el comando focalizado ni ejecutado la suite completa. Las evidencias verdes de 12 tests pertenecen al alcance anterior y no acreditan esta nueva regresión en verde. Se mantiene la ausencia de configuración de lint/tipado indicada para el proyecto.

## Hallazgos nuevos

Sin hallazgos nuevos. RT-01 a RT-05 permanecen resueltos y se conserva el alcance aprobado.

## Veredicto final

**APROBADO, 9.00/10.** La nueva regresión discrimina la condición restante de RC-03 con rojo de comportamiento válido. Este veredicto corresponde a las pruebas; no declara corregida producción. Solo se actualiza este informe, sin cambios de código ni commit.
