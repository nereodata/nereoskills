# Revisión de tests: B-ADV-0032 — H-05

**Veredicto: APROBADO**
**Revisor:** Hades
**Árbol declarado:** `c6acc8eeb5613df7a42008528f1c3734440dd230`
**Media: 8,75/10. Sin hallazgos ALTA ni CRÍTICA vigentes.**
**Destino:** `docs/review/test_reviews/B-ADV-0032-test-review.md`

## Alcance y límites

Una única revisión de `tests.test_orquestar.SubprocesoColgadoTests`, centrada en el delta H-05 y su interacción con las regresiones previamente aprobadas.

H-05 exige terminar descendientes Windows con pipes heredados después de salir el padre, en tres caminos: captura JSON por gracia, captura JSON por timeout y captura por líneas por timeout.

Se aplican las instrucciones adjuntas de Hades y `/review-test`. El acceso a los archivos falló por Core launch y también falló la escritura del informe. Se revisa el material exacto proporcionado; no se atribuye comprobación independiente del árbol.

No se revisa ni modifica producción. No se ejecutan pruebas ni se repiten las verificaciones aportadas.

## Evidencia aceptada

Sobre el árbol `c6acc8eeb5`:

- `python -m unittest tests.test_orquestar.SubprocesoColgadoTests`: **12 pruebas en 41,394 s, tres fallos de aserción y un skip POSIX explícito**. Los tres fallos corresponden a los modos Windows del nuevo test; ocurren en el watchdog después de constatar la creación del hijo. Las otras diez pruebas ejecutadas no presentan fallos.
- `python -m py_compile tests/test_orquestar.py`: verde.
- `git diff --check`: verde.
- Formato, lint y tipado sin herramientas configuradas; no se contabilizan como verificaciones superadas.

La ejecución anterior sobre `924d343a45` terminó con tres errores `TimeoutExpired`. El árbol actual convierte esos resultados en fallos de aserción explícitos. No se confunden las dos ejecuciones.

La ejecución POSIX real continúa pendiente en **B-ADV-0038**. El skip no acredita esa validación.

La evidencia actual es **RED para H-05**. La aprobación evalúa la calidad de las pruebas para continuar la corrección; no declara que la funcionalidad esté corregida.

## Puntuaciones

| Criterio | Puntuación | Evaluación |
|---|---:|---|
| Cobertura | 9/10 | Añade los tres caminos Windows exigidos, con descendiente real y pipes heredados; conserva las regresiones aprobadas. |
| Aserciones | 9/10 | Exige retorno acotado, código, métrica, salida y desaparición del PID; JSON por gracia comprueba además los tokens de entrada. |
| Rojo correcto | 9/10 | Los tres modos alcanzan el watchdog tras crear al hijo. No fallan por sintaxis, carga o preparación. Las aserciones posteriores todavía no se alcanzan en ese RED. |
| Estabilidad | 8/10 | Usa temporales, procesos locales, plazos y limpieza. Mantiene dependencia acotada del arranque y planificación de Windows y de sus utilidades de procesos. |
| **Media** | **8,75/10** | **Supera el umbral estricto de 8, sin hallazgos bloqueantes.** |

## Evaluación del delta H-05

### Preparación del escenario

`test_windows_descendiente_con_padre_salido_y_pipes_heredados` recorre `json_gracia`, `json_timeout` y `lineas_timeout`.

El programa padre crea un hijo que duerme 60 s sin redirigir sus streams, registra su PID, emite la salida y termina sin esperar al hijo. La preparación representa el escenario de un descendiente que conserva los pipes tras la salida del padre, sin proveedores externos.

Antes de cada subcaso se eliminan el PID y el resultado anteriores. Esto evita que datos residuales satisfagan las comprobaciones del siguiente modo.

### Oráculos de comportamiento

En `json_gracia`, el padre emite una respuesta JSON final válida. La gracia de 0,2 s queda por debajo del timeout de 3 s. La prueba exige:

- Código 0 y métrica `cierre_forzado`.
- Conservación del mensaje.
- Siete tokens de entrada asociados a `agy`.

En `json_timeout` y `lineas_timeout`, el padre emite una línea que no constituye una respuesta final. Ambos exigen código 124, métrica `timeout` y conservación de esa salida. Los comandos seleccionan respectivamente captura JSON con `agy` y captura por líneas con `codex`.

Las aserciones distinguen el cierre por gracia del cierre por timeout y protegen la conservación de resultados.

### Detección del bloqueo y del descendiente superviviente

El worker separado permite detectar que `lanzar()` no devuelve el control sin bloquear indefinidamente el proceso principal de pruebas.

El watchdog de 12 s comprueba primero que existe el PID registrado y luego falla expresamente. La evidencia actual alcanza ese punto en los tres modos. La creación del hijo descarta un fallo de preparación que impidiera iniciar el escenario.

Cuando el worker devuelve el control, la prueba exige salida normal y lee el resultado serializado. Una caída del worker o la ausencia del archivo no se aceptan como éxito.

Después consulta `tasklist`, con timeout y comprobación de código 0, y rechaza la presencia del PID exacto entrecomillado en la salida CSV. Esta comprobación sucede antes de la limpieza. Por tanto, la limpieza no puede hacer pasar la aserción de desaparición.

El test discrimina también una corrección parcial que desbloquee los lectores pero deje vivo al descendiente.

### Estabilidad y limpieza

Los plazos de 3 y 12 s permanecen claramente por debajo de los 60 s de espera del hijo. Su terminación natural no satisface la prueba durante una ejecución ordinaria.

El `finally` intenta terminar el árbol del worker si continúa vivo y el PID del hijo si llegó a registrarse. Las consultas y esperas de limpieza están acotadas.

Permanece la dependencia habitual de planificación de las pruebas con procesos reales. El margen de arranque es mayor que el señalado y corregido en RT-02; no se identifica una nueva carencia que justifique reabrir ese hallazgo.

El RED aportado demuestra el bloqueo observado. Todavía no acredita la ejecución satisfactoria de las aserciones posteriores sobre resultado, métricas y desaparición del descendiente. Esta limitación no invalida sus oráculos.

## Reevaluación de hallazgos anteriores

| Antecedente | Estado | Evaluación |
|---|---|---|
| RT-01 de la revisión inmediatamente anterior: falta de protección del aislamiento POSIX en captura por líneas | **Resuelto; se conserva** | El test portable exige `start_new_session=True` en ese camino. H-05 no altera esa protección. |
| RT-02 de aquella revisión: margen de arranque de 0,2 s | **Resuelto; se conserva** | La regresión de timeout antes del JSON mantiene 2 s y sus aserciones de resultado y salida parcial. |
| H-01: descendientes y pipes tras salir el padre | **Se conserva la aprobación de las pruebas existentes** | H-05 añade cobertura real Windows para los tres caminos indicados. No se declara corregida su implementación. |
| H-02: configuración de timeout no finita | **Se conserva la evaluación anterior** | Permanecen los casos `inf`, `-inf`, `nan`, ambas variables de entorno, cero y positivo válido. |
| H-03: timeout explícitamente desactivado | **Resuelto en el alcance probado; se conserva** | Se mantiene la distinción entre argumento omitido y `None`, y la propagación desde el perfil. |
| H-04: timeout durante la espera posterior al EOF | **Resuelto en el alcance probado; se conserva** | Se mantiene la espera bloqueada y las exigencias de terminación, código 124 y métrica `timeout`. |
| RT-01 histórico: interpretación insuficiente de errores de `ps` | **Resuelto; se conserva** | Continúan las comprobaciones de código, diagnóstico y estado antes de aceptar la desaparición. |
| Ejecución POSIX real | **Pendiente en B-ADV-0038** | No se duplica el seguimiento ni se acredita mediante mocks o skips. |

Los identificadores RT-01/RT-02 corresponden a cada informe histórico; no se equiparan hallazgos distintos por compartir identificador.

## Antecedentes conservados

1. **Revisión completa inicial: APROBADO, media 8,75/10.** Aprobó las pruebas de H-01/H-02. Señaló como MEDIA la interpretación de errores de `ps` y como BAJA la falta de ejecución POSIX real. Quedaron resueltas las observaciones sobre el padre ya finalizado en el mock, la comparación del grupo del invocador y la cobertura de las ramas de entorno.

2. **Reevaluación del RT-01 histórico de `ps`: APROBADO, media 8,50/10.** Consideró corregido el falso positivo por salida vacía ante errores de consulta. La evidencia comunicada fue de seis pruebas, cinco correctas y un skip POSIX. La validación POSIX quedó registrada en B-ADV-0038.

3. **Revisión de reanudación: RECHAZADO, media 8,25/10.** Identificó RT-01 ALTA por no proteger la creación de sesión POSIX en captura por líneas y RT-02 MEDIA por el timeout real de 0,2 s. Consideró cubiertos H-03 y H-04 en las pruebas.

4. **Reevaluación inmediatamente anterior: APROBADO, media 8,75/10.** Cerró ambos hallazgos mediante el test portable de aislamiento por líneas y la ampliación del timeout a 2 s. Conservó la limitación POSIX y distinguió la aprobación de las pruebas de la corrección de producción.

Esta revisión mantiene esas decisiones y evalúa únicamente el nuevo alcance H-05 dentro de la clase indicada.

## Hallazgos nuevos

No se identifican hallazgos nuevos.

## Dictamen

**APROBADO para el alcance de pruebas de B-ADV-0032, incluido H-05.**

Las pruebas nuevas discriminan el bloqueo de los tres caminos Windows y comprueban la terminación del descendiente cuando se devuelve el control. Puede continuar la corrección pendiente.

Este dictamen no aprueba producción, no declara GREEN de H-05 ni acredita ejecución POSIX real.

**Entrega:** no se pudo escribir el archivo de destino. El intento de lectura falló por Core launch y el intento de escritura también falló. Se entrega aquí el informe completo, con los antecedentes conservados.

---

## Informes anteriores

# Revisión de tests: B-ADV-0032

**Veredicto: APROBADO**
**Revisor:** Hades
**Media: 8,75/10. Sin hallazgos ALTA ni CRÍTICA vigentes.**

## Alcance y evidencia

Reevaluación de RT-01/RT-02 exclusivamente sobre `tests.test_orquestar.SubprocesoColgadoTests`, según las pruebas exactas adjuntas. Se revisan ambas correcciones y su interacción con las regresiones de la clase. No se revisa producción.

El acceso al disco falló por ambas vías disponibles. Las instrucciones de Hades, la skill `/review-test`, la ficha, las pruebas y los informes anteriores se han leído en los materiales proporcionados. No se ha comprobado directamente el árbol ni escrito este informe.

Se acepta como evidencia del coordinador:

- **RED mediante `--verificar`:** 11 pruebas en 8,138 s, cuatro fallos de aserción esperados: propagación de `None` desde `ejecutar()`, cancelación del timeout tras EOF, padre terminado con pipes abiertos y recuperación del entorno pese a `None` explícito.
- La prueba portable incorporada para RT-01 pasa.
- Un skip POSIX explícito. **No se acredita ejecución POSIX real**; permanece registrada en **B-ADV-0038**.
- Compilación y ambos chequeos de diff comunicados como verdes sobre el árbol declarado `2a0ad787c7`. No se han repetido.
- Formato, lint y tipado no configurados; no cuentan como verificaciones superadas.

No se han ejecutado pruebas. La aprobación evalúa su calidad y suficiencia para continuar la corrección; no convierte la evidencia RED en GREEN.

## Puntuaciones

| Criterio | Puntuación | Evaluación |
|---|---:|---|
| Cobertura | 9/10 | Se añade protección explícita del aislamiento POSIX en la captura por líneas, completando la carencia señalada. |
| Aserciones | 9/10 | Comprueban argumentos de creación, terminación, resultados, métricas, salida parcial y precedencia de configuración. |
| Rojo correcto | 9/10 | Los cuatro fallos comunicados corresponden a los comportamientos pendientes, sin errores de carga o fixtures. |
| Estabilidad | 8/10 | El margen de arranque aumenta a 2 s; permanece la dependencia acotada de planificación en las pruebas con procesos reales. |
| **Media** | **8,75/10** | **Cumple el umbral estricto superior a 8.** |

## Reevaluación de RT-01/RT-02

| Hallazgo | Gravedad original | Estado | Para | Destino |
|---|---|---|---|---|
| RT-01: falta de protección del aislamiento POSIX en captura por líneas | 🟠 ALTA | **Resuelto** | Desarrollador / Artemisa | Resolver en B-ADV-0032; corrección satisfecha |
| RT-02: timeout real de 0,2 s insuficiente para el arranque | 🟡 MEDIA | **Resuelto** | Desarrollador / Artemisa | Resolver en B-ADV-0032; corrección satisfecha |

**RT-01:** `test_captura_lineas_crea_sesion_posix_propia` simula POSIX, invoca el camino por líneas mediante `harness='codex'` e inspecciona los argumentos efectivos de `Popen`. Exige que `start_new_session` sea exactamente `True`. El doble no introduce ese argumento: la aserción falla si se elimina el aislamiento únicamente de este camino. Cubre la corrección solicitada de forma portable. Su resultado satisfactorio no acredita terminación real de grupos POSIX.

**RT-02:** `test_lanzar_agy_corta_por_timeout_cuando_proceso_se_cuelga_antes_del_json` amplía el timeout a **2 s**, manteniéndolo claramente por debajo del bloqueo de 60 s del hijo. Conserva las aserciones de código 124, métricas `timeout` y `error`, y recuperación de la salida parcial. Satisface el ajuste solicitado sin debilitar el comportamiento comprobado.

## Antecedentes y trazabilidad

- La revisión completa inicial aprobó las regresiones de H-01/H-02, pero detectó una interpretación insuficiente de errores de `ps` y dejó pendiente la ejecución POSIX real.
- La reevaluación posterior aprobó la corrección de las comprobaciones de `ps`. La validación POSIX quedó registrada en B-ADV-0038.
- La revisión inmediatamente anterior fue **RECHAZADA**, con media **8,25/10**, por falta de cobertura del aislamiento POSIX en el camino por líneas —RT-01— y señaló el margen de arranque de 0,2 s —RT-02—.
- Esa revisión consideró cubiertos en las pruebas H-03, sobre timeout explícitamente desactivado, y H-04, sobre timeout durante la espera posterior al EOF. Este dictamen conserva esa evaluación; no declara corregida su implementación.

Los identificadores RT-01/RT-02 de esta reevaluación corresponden al rechazo inmediatamente anterior; los informes históricos conservarán sus identificadores originales.

## Hallazgos nuevos

No se identifican hallazgos nuevos en el delta revisado. La ejecución POSIX real continúa pendiente en B-ADV-0038, sin duplicar el seguimiento.

## Dictamen

**APROBADO para el alcance de pruebas revisado.** RT-01 y RT-02 quedan resueltos por inspección del material adjunto, con evidencia comunicada de que la nueva prueba portable pasa. Puede continuar la corrección de producción pendiente. Este dictamen no aprueba producción ni acredita ejecución POSIX real.

---

## Informes anteriores

# Revisión de tests: B-ADV-0032

**Veredicto: RECHAZADO**

**Destino del informe:** `docs/review/test_reviews/B-ADV-0032-test-review.md`
**Revisor:** Hades
**Alcance:** exclusivamente `tests.test_orquestar.SubprocesoColgadoTests`, delta de reanudación y regresiones previas del bug. No se ha revisado producción.

## Evidencia y límites

Revisión estática de las instrucciones, ficha y pruebas adjuntas. Se acepta la evidencia RED comunicada mediante `adevv orquestar --verificar`: 10 tests, cuatro fallos de aserción esperados en los cuatro tests nuevos y un skip POSIX explícito; duración de 5,901 s. No se han repetido pruebas ni utilizado herramientas.

La ejecución RED acredita que las pruebas se cargan y alcanzan sus aserciones en ese entorno. No se atribuye una comprobación independiente de compilación. No hay lint ni tipado configurados.

La validación real POSIX sigue pendiente en **B-ADV-0038**; no se declara ejecutada. Los adjuntos no incluyen el diseño ni el informe previo completos: la reevaluación de H-01/H-03/H-04 utiliza los requisitos y resúmenes recogidos en la ficha.

## Puntuaciones

| Criterio | Puntuación | Evaluación |
|---|---:|---|
| Cobertura | 7/10 | Falta proteger el aislamiento POSIX del segundo camino de captura exigido por H-01. |
| Aserciones | 9/10 | Comprueban resultados, métricas, conservación de salida, terminación y precedencia de configuración. |
| Rojo correcto | 9/10 | Los cuatro fallos comunicados corresponden a comportamientos del delta, sin errores de carga o fixtures. |
| Estabilidad | 8/10 | Uso razonable de eventos y dobles; persiste un margen de arranque demasiado corto en una regresión real. |
| **Media** | **8,25/10** | **Existe un hallazgo ALTA que impide aprobar.** |

## Reevaluación de hallazgos previos

| Hallazgo | Estado en las pruebas | Evidencia |
|---|---|---|
| **H-01: terminar descendientes y supervisar pipes tras salir el padre** | **Persiste parcialmente** | El nuevo test simula padre terminado con streams abiertos y exige cierre forzado exitoso. La prueba POSIX combina padre vivo/salido y presencia/ausencia de JSON, pero solo recorre la captura JSON de `agy`. No protege el aislamiento del camino por líneas. |
| **H-03: distinguir timeout omitido y desactivado** | **Resuelto en el alcance probado** | Se contrasta `timeout=None` explícito con argumento omitido bajo el mismo entorno; otro test exige que el cero del perfil llegue como `None` a `lanzar()`. |
| **H-04: mantener timeout durante la espera posterior al EOF** | **Resuelto en el alcance probado** | El doble entrega EOF inmediatamente, mantiene bloqueada la espera y exige que intervenga la terminación, con código 124 y métrica `timeout`. |

Las regresiones previas conservan comprobaciones de métricas y respuesta tras JSON final, timeout antes del JSON, configuración no finita y propagación de entrada/timeout desde `agente()`. Esta última también comprueba una única invocación al reanudar una sesión que termina por timeout.

## Hallazgos nuevos

### RT-01 — 🟠 ALTA: H-01 no queda protegido en el camino de captura por líneas

**Para:** desarrollador / Artemisa
**Destino:** resolver en B-ADV-0032

**Localización:** `test_eof_no_cancela_timeout_antes_de_esperar_proceso`, `test_terminacion_posix_dirigida_al_grupo_aislado` y `test_descendiente_real_no_sobrevive_al_timeout_ni_a_gracia_json`.

La ficha exige aislar **ambos `Popen`** en una sesión POSIX propia. La prueba real de descendientes siempre utiliza `harness='agy'` con `--output-format json`. El test de `codex` sustituye `Popen` y no comprueba cómo se crea el proceso. El test de terminación comprueba `killpg(pid, SIGKILL)`, pero tampoco acredita que ese PID identifique un grupo aislado.

Por tanto, las pruebas podrían aprobar aunque el camino por líneas omitiera crear su sesión: H-04 quedaría cubierto, pero la terminación del grupo de ese camino seguiría sin protección.

**Corrección requerida:** añadir, dentro de esta clase, una prueba del camino por líneas que compruebe la creación de la sesión POSIX propia. Puede hacerse de forma portable simulando POSIX e inspeccionando los argumentos de `Popen`. La prueba debe fallar si se elimina ese aislamiento únicamente de dicho camino.

La ejecución real POSIX continúa bajo B-ADV-0038; este hallazgo no solicita declararla ejecutada ni ampliar la suite.

### RT-02 — 🟡 MEDIA: el timeout de 0,2 s incluye el arranque del intérprete

**Para:** desarrollador / Artemisa
**Destino:** resolver en B-ADV-0032

**Localización:** `test_lanzar_agy_corta_por_timeout_cuando_proceso_se_cuelga_antes_del_json`.

La prueba inicia un intérprete real, limita toda la ejecución a 0,2 s y exige recuperar `escribiendo informes...`. En un host cargado, especialmente Windows, el proceso puede agotar ese plazo antes de emitir la línea. El test fallaría por velocidad de arranque aunque el timeout funcionase correctamente.

**Corrección requerida:** ampliar el margen de este caso para permitir el arranque y la emisión de la línea, manteniéndolo claramente por debajo de los 60 s de bloqueo del hijo. Conservar las aserciones de código 124, timeout, error y salida parcial.

## Cierre

La revisión queda **RECHAZADA por RT-01**. Las aserciones nuevas de H-03 y H-04 discriminan los comportamientos requeridos; falta proteger el aislamiento POSIX del camino de captura por líneas. No se solicita revisar producción, ejecutar la suite completa ni ampliar el alcance a otros bugs.

---

## Informes anteriores

# B-ADV-0032 — Reevaluación de RT-01

**Veredicto: APROBADO. Media: 8,50/10. Sin hallazgos ALTA ni CRÍTICA.**

## Alcance y limitaciones

Revisión limitada a RT-01 y al delta de consulta de `ps` en `test_descendiente_real_no_sobrevive_al_timeout_ni_a_gracia_json`. No se revisa producción ni se reabren las demás pruebas.

Ante el fallo de acceso al disco registrado en esta sesión, se revisa exclusivamente el material adjunto. No se ha escrito el archivo de destino ni comprobado el árbol directamente. Tampoco se han podido leer las instrucciones instaladas de Hades y `/review-test`.

No se han ejecutado pruebas. Evidencia aportada por el solicitante:

- Tras la corrección, `--verificar`: **6 pruebas, 5 OK, 1 skip POSIX explícito; 1,065 s**.
- Compilación de los dos archivos Python correcta.
- Formato/lint omitidos y tipado no configurado; no cuentan como verificaciones superadas.
- RT-02 registrado como **B-ADV-0038**, sin versión, con origen en B-ADV-0032 y su informe de pruebas.

**No se acredita validación POSIX real.** El GREEN comunicado no ejecutó las nuevas aserciones de esta prueba omitida.

## Evaluación del delta

La corrección elimina el falso positivo identificado en RT-01:

- Rechaza códigos de salida distintos de `0` y `1`.
- Rechaza diagnósticos no vacíos en `stderr`.
- Exige un estado no vacío cuando `ps` devuelve `0`.
- Solo interpreta una salida vacía como ausencia del PID tras haber validado código `1` y ausencia de diagnóstico.

Un error de ejecución, un timeout de la consulta o una respuesta exitosa sin estado ya no se aceptan silenciosamente como desaparición del descendiente. Se conserva la aceptación del estado zombi como proceso que ya no ejecuta trabajo.

Con código `1` y salida no vacía, el flujo sigue evaluando el estado. Esto no reproduce el falso positivo de RT-01 por salida vacía ante un error de consulta y no constituye un bloqueo para este alcance.

## Puntuación

| Criterio | Nota | Justificación |
|---|---:|---|
| Cobertura | 9 | El delta distingue ausencia del PID, consulta exitosa sin estado, diagnóstico y código inesperado. |
| Aserciones | 9 | Las validaciones preceden a la decisión de desaparición y rechazan las respuestas que originaban RT-01. |
| Rojo correcto | 8 | La relación entre defecto y nuevas aserciones es clara por inspección. No se aporta RED específico del delta; el RED anterior corresponde a H-01/H-02. |
| Estabilidad | 8 | Conserva timeout y sondeo acotados. La interpretación real de `ps` sigue pendiente de ejecución POSIX. |
| **Media** | **8,50** | Supera el umbral estricto de 8. |

## Disposición de hallazgos

| ID | Severidad | Estado y acción | Para | Destino |
|---|---|---|---|---|
| RT-01 | MEDIA, resuelta | La inspección del delta confirma que un fallo de consulta con salida vacía ya no acredita desaparición. Cerrar el hallazgo, conservando la limitación de ejecución. | Desarrollador | Descartar como pendiente |
| RT-02 | BAJA | Seguimiento registrado en B-ADV-0038 según evidencia aportada. Mantener allí la validación POSIX pendiente; no duplicar la incidencia. | Humano | Registrar |

No se identifican nuevos hallazgos en el delta revisado.

## Dictamen

**APROBADO:** RT-01 queda resuelto por inspección del código adjunto. La ejecución POSIX real permanece pendiente y registrada en B-ADV-0038. Esta aprobación se limita a la corrección de la prueba.

---

## Revisión completa anterior y trazabilidad

# B-ADV-0032 — Revisión de pruebas

**Veredicto: APROBADO**
**Árbol declarado:** `3ce908601f`
**Media: 8,75/10. Sin hallazgos ALTA ni CRÍTICA.**

## Alcance y limitaciones

Reevaluación de las tres pruebas nuevas para H-01/H-02, exclusivamente sobre el código adjunto. No se revisa producción.

El acceso al disco falló previamente en esta sesión. No se han podido leer las instrucciones instaladas de Hades y `/review-test`, comprobar el árbol ni escribir este informe en `docs/review/test_reviews/B-ADV-0032-test-review.md`.

No se han ejecutado pruebas. Se acepta como evidencia aportada por el solicitante:

- **RED:** 6 pruebas, 4 fallos de aserción esperados —ausencia de `killpg` y tratamiento de `inf`, `-inf`, `nan`—, 1 skip POSIX y 3 regresiones anteriores verdes.
- **GREEN:** `python -m unittest tests.test_orquestar.SubprocesoColgadoTests`; 6 pruebas, 5 ejecutadas correctamente y 1 skip POSIX explícito.
- Windows sin WSL instalado. **No se acredita ejecución POSIX real.**
- Lint y tipado omitidos por ausencia de herramientas configuradas; no constan como comprobaciones superadas. Sin dependencias nuevas declaradas.

## Puntuación

| Criterio | Nota | Justificación |
|---|---:|---|
| Cobertura | 9 | H-02 cubre tres valores no finitos en configuración y ambas variables de entorno, más cero y positivo válido. H-01 combina contrato determinista con integración conservada para timeout y gracia tras JSON. |
| Aserciones | 9 | Comprueban valores seguros, señal y grupo exactos, espera acotada, códigos, métricas, aislamiento y estado del descendiente. Existe una debilidad en la interpretación del resultado de `ps`. |
| Rojo correcto | 9 | Los fallos comunicados corresponden a los defectos perseguidos y son de aserción. El GREEN aportado completa las ramas de entorno que el RED no alcanzó. |
| Estabilidad | 8 | Las pruebas deterministas evitan depender de POSIX. La integración usa temporales, plazos y limpieza; conserva dependencia de planificación, procesos reales y `ps`, pendiente de validación en POSIX. |
| **Media** | **8,75** | Cumple el umbral estricto de media superior a 8. |

## Evaluación de las tres pruebas

**`test_timeout_no_finito_conserva_valor_seguro`:** proporciona un oráculo concreto para H-02. Exige mantener `1800` ante cada entrada no finita y protege los comportamientos de cero y de un timeout positivo. El GREEN aportado implica que se recorrieron también las seis comprobaciones de entorno.

**`test_terminacion_posix_dirigida_al_grupo_aislado`:** representa ahora un padre finalizado mediante `returncode=0` y `poll()=0`. Exige `killpg(12345, 9)` incluso en ese estado y `wait(timeout=2)`. Permite detectar de forma determinista una terminación que omita el grupo cuando el padre ya salió. El mock no acredita aislamiento ni eliminación real de descendientes.

**`test_descendiente_real_no_sobrevive_al_timeout_ni_a_gracia_json`:** conserva ambos caminos de integración. Verifica duración, resultado, métrica correspondiente y que el descendiente desaparezca o quede zombi, estado que ya no ejecuta trabajo. Ahora registra el grupo del arnés, exige que difiera del grupo inicial del invocador y comprueba que este último se conserve. Su skip en Windows es explícito; su comportamiento real sigue pendiente de ejecución POSIX.

## Resolución de observaciones anteriores

| Observación | Estado | Para | Destino |
|---|---|---|---|
| El mock no representaba un padre finalizado. | Resuelta con `returncode=0` y `poll.return_value=0`. | Desarrollador | Descartar como pendiente |
| La comparación del grupo del invocador era tautológica. | Resuelta mediante registro del grupo del arnés y comparación con el grupo inicial del invocador. | Desarrollador | Descartar como pendiente |
| El primer fallo impedía recorrer las aserciones de entorno durante RED. | Cerrada con el GREEN aportado. No se atribuye retrospectivamente esa cobertura al RED. | Desarrollador | Descartar como pendiente |

## Hallazgos vigentes

| ID | Severidad | Hallazgo y acción | Para | Destino |
|---|---|---|---|---|
| RT-01 | MEDIA | La consulta `ps` ignora `returncode` y `stderr`. Una salida vacía debida a un error de consulta podría interpretarse como desaparición del descendiente. Distinguir ausencia del PID de errores de ejecución o de opciones de `ps`. | Desarrollador | Resolver |
| RT-02 | BAJA | La integración POSIX permanece omitida en la evidencia disponible. Registrar esa limitación y obtener evidencia en un host POSIX antes de afirmar validación real de grupos y descendientes. | Humano | Registrar |

## Dictamen

Las pruebas deterministas permiten corregir y proteger los contratos de H-01/H-02; la integración conservada complementa esos contratos con comprobaciones reales cuando se ejecute en POSIX. Las tres observaciones anteriores están resueltas en el material y la evidencia aportados.

**APROBADO para el alcance de pruebas revisado.** Este dictamen no aprueba producción ni acredita cobertura POSIX real ejecutada.
