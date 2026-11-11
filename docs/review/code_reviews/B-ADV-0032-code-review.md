# B-ADV-0032 — Revisión independiente de código tras H-05

**Veredicto: APROBADO**
**Revisor:** Hades
**Árbol declarado:** `0cdd8f63744580c4d920d9897e3d7e7f5502182c`
**Media: 8,67/10. Sin hallazgos ALTA ni CRÍTICA vigentes.**
**Destino:** `docs/review/code_reviews/B-ADV-0032-code-review.md`

## Alcance y límites

Una revisión estática independiente del delta completo de producción de B-ADV-0032: creación y terminación de procesos, captura JSON y por líneas, resolución y propagación del timeout y entrada de `agy`.

Se reevalúa H-05 y su interacción con H-01/H-02/H-03/H-04, contrastando el código y diff exactos adjuntos con la ficha, el diseño actualizado y la plataforma.

Se aplican las instrucciones adjuntas de Hades y `/review-code`. Los materiales proporcionados se utilizan desde el principio. No se afirma lectura directa del repositorio.

Se excluyen las pruebas como producción y las modificaciones de otros IDs, incluida la conmutación por acceso de suscripción. No se ejecutaron pruebas, calidad ni suite completa; tampoco se cambió código o perfiles.

Se consultó documentación oficial de Microsoft para contrastar la semántica de las APIs Windows. Esta consulta no constituye ejecución ni reproducción del código.

## Análisis estático y evidencia

| Comprobación | Resultado y límite |
|---|---|
| Regresión del triaje | Coordinador `--verificar`, árbol `0cdd8f6374`: 12 pruebas en 11,285 s, OK con un skip POSIX explícito. No se repite. |
| Compilación | `python -m py_compile skills/orquestar/orquestar.py tests/test_orquestar.py`, verde del mismo árbol. No se repite. |
| Integridad del diff | `git diff --check`, verde del mismo árbol. No se repite. |
| Calidad por tarea | `adevv orquestar --calidad --base 9a143486c663f2afe2bbe4e7ef3a30743c65532a`, código 0 del mismo árbol, sin escritura. Formato y lint explícitamente **OMITIDOS** por ausencia de herramientas; no se acreditan como ejecutados. |
| Tipado y secretos | Sin herramientas configuradas. No se observan secretos en el material revisado; no equivale a un escaneo automatizado. |
| Dependencias | Sin cambios declarados; no procede auditoría de dependencias nuevas. |
| Review-test | H-05 APROBADO, 8,75/10, sin hallazgos nuevos, según informe aportado. No se repite esa revisión. |
| POSIX real | No acreditado; seguimiento conservado en B-ADV-0038. |

Se distingue el RED de H-05 sobre `c6acc8eeb5` —tres fallos del watchdog— del GREEN actual. El GREEN intermedio sobre `7df1c12266` no sustituye a la evidencia aportada del árbol revisado.

## Puntuaciones

| Criterio | Nota | Justificación |
|---|---:|---|
| Corrección | 9 | El job conserva la terminación Windows tras salir el padre; se mantienen supervisión, precedencia y espera protegida. |
| Seguridad | 9 | El arnés se asigna suspendido, antes de permitir la creación de descendientes; comandos por argumentos y aislamiento POSIX conservados. |
| Conformidad | 9 | Implementa el diseño actualizado dentro del motor existente, con biblioteca estándar y sin contradicción identificada con las DEC. |
| Calidad | 8 | Centraliza creación y cierre; la integración Win32 añade complejidad localizada y firmas explícitas. |
| Eficiencia | 8 | Sin nuevo sondeo durante la ejecución; snapshot de hilos al arrancar, recursos cerrados y esperas de terminación acotadas. |
| Documentación | 9 | Diseño y changelog describen el mecanismo Windows y mantienen el alcance y las limitaciones de validación. |
| **Media** | **8,67** | **Supera 8, sin hallazgos bloqueantes.** |

## Reevaluación de hallazgos

| Hallazgo | Gravedad original | Estado | Para | Destino |
|---|---|---|---|---|
| H-01: supervisión tras salir el padre y terminación del grupo POSIX | ALTA | **Resuelto; se mantiene cerrado** | Desarrollador | Resolver; corrección satisfecha |
| H-02: timeout no finito | MEDIA | **Resuelto; se mantiene cerrado** | Desarrollador | Descartar como pendiente |
| H-03: distinguir timeout omitido y desactivado | MEDIA | **Resuelto; se mantiene cerrado** | Desarrollador | Resolver; corrección satisfecha |
| H-04: proteger la espera posterior al EOF | ALTA | **Resuelto; se mantiene cerrado** | Desarrollador | Resolver; corrección satisfecha |
| H-05: terminación Windows después de salir el padre | ALTA | **Resuelto** | Desarrollador / Artemisa | Resolver en B-ADV-0032; corrección satisfecha |

### H-05 — Resuelto: terminación independiente del PID raíz

`_proceso_agrupado()` crea el Job Object antes del lanzamiento Windows, activa `KILL_ON_JOB_CLOSE` y crea el proceso con `CREATE_SUSPENDED`. Asigna el proceso al job antes de reanudar su hilo. La capacidad de terminación queda en un handle del invocador y sobrevive a la salida del padre.

`_terminar_arbol_proceso()` utiliza `TerminateJobObject` cuando existe ese trabajo, antes del respaldo de terminación y la espera acotada. La operación termina los miembros asociados al job, incluidos los de sus jobs hijos; no necesita localizar nuevamente el árbol mediante el PID raíz. [Microsoft, TerminateJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-terminatejobobject).

Ambos caminos reales, JSON y líneas, usan el helper. El cierre del contexto libera el job; con `KILL_ON_JOB_CLOSE` termina los miembros residuales. Los hijos creados normalmente mediante `CreateProcess` pertenecen al job por defecto, y el código no habilita las opciones de breakaway. [Microsoft, Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

Los fallos de asignación o reanudación abortan el lanzamiento, intentan matar y esperar al proceso suspendido y pasan por el cierre del job. No se degradan silenciosamente al mecanismo anterior. El snapshot y el handle del hilo se cierran mediante `finally`.

La reanudación utiliza `OpenThread` con permiso de suspensión/reanudación y comprueba el indicador de error de `ResumeThread`. Es coherente con el proceso recién creado suspendido. [Microsoft, ResumeThread](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-resumethread).

La inspección resuelve la dependencia anterior de `taskkill` sobre un padre desaparecido. La evidencia GREEN aportada complementa esta conclusión con los tres casos Windows del triaje. No se atribuye reproducción propia.

### H-01 — Se mantiene resuelto

La captura JSON continúa supervisando proceso y lectores conjuntamente. Conserva timeout y gracia después de salir el padre y aplica un plazo de cierre desde esa salida.

Ambos consumidores conservan `start_new_session` en POSIX. El helper mantiene `killpg` aunque el líder haya terminado. La introducción del contexto compartido no elimina esa lógica.

La validación POSIX real continúa pendiente; no se transforma la inspección estática ni el GREEN Windows en evidencia POSIX.

### H-02 — Se mantiene resuelto

`timeout_de_rol()` conserva `math.isfinite` antes de aceptar valores positivos o interpretar valores finitos no positivos como desactivación.

Las entradas no finitas recuperan el valor por defecto. La corrección Windows no altera esta resolución.

### H-03 — Se mantiene resuelto

Se conserva `_TIMEOUT_OMITIDO`: `None` explícito no recupera el timeout del entorno.

`ejecutar()` y `agente()` propagan el valor resuelto, incluida la desactivación. No se identifica una regresión de precedencia introducida por H-05.

### H-04 — Se mantiene resuelto

El temporizador de captura por líneas permanece activo durante `p.wait()` y se cancela después.

Su callback alcanza ahora el job Windows incluso con el padre terminado. Esto resuelve la interacción que anteriormente podía mantener abiertos los pipes pese al vencimiento del temporizador.

## Revisión del conjunto

La captura JSON conserva la lectura concurrente de stdout/stderr, la supervisión mediante reloj monotónico y la recuperación de salida y métricas tras cierre forzado.

El handle Windows permanece disponible durante la supervisión y se libera al abandonar el contexto. Ambos consumidores comparten la misma creación agrupada; no queda un segundo lanzamiento real que conserve únicamente la estrategia anterior.

`agente()` sigue pasando `entrada=None` para `agy`, tanto inicialmente como en el reintento sin sesión. Los consumidores conservan la exclusión del reintento por sesión cuando las métricas indican timeout.

La implementación permanece en el motor existente, usa biblioteca estándar y no introduce dependencias inversas ni un motor duplicado. El diseño actualizado documenta la agrupación Windows, sus consumidores y su limpieza. No se identifica una desviación arquitectónica que requiera una DEC adicional.

El changelog describe el mecanismo implementado y no afirma validación POSIX real.

## Hallazgos nuevos

No se identifican hallazgos nuevos en el delta revisado.

## Antecedentes conservados

- **Revisión anterior: RECHAZADO, media 7,17/10.** H-01 persistía parcialmente porque la supervisión JSON terminaba al salir el padre. H-02 estaba resuelto. Se incorporaron H-03, por perder la desactivación explícita del timeout, y H-04, por cancelar el temporizador antes de esperar al proceso.
- **Revisión inmediatamente anterior, árbol `fff2e720d2`: RECHAZADO, media 7,50/10.** Reconoció H-01/H-03/H-04 resueltos y mantuvo H-02 cerrado. Identificó H-05 ALTA: `taskkill` sobre el PID del padre terminado no garantizaba terminar descendientes con pipes heredados.
- **Review-test de H-05: APROBADO, media 8,75/10.** Evaluó los tres modos Windows con RED específico. Posteriormente, el coordinador aportó GREEN, incluido el del árbol actual.
- La ejecución POSIX real permanece registrada en **B-ADV-0038**, sin duplicar su seguimiento.

Este dictamen debe incorporarse por delante de los informes históricos, conservando íntegramente sus textos.

## Dictamen

**APROBADO para el delta de producción de B-ADV-0032 revisado.**

H-05 queda resuelto. Se mantienen cerrados H-01/H-02/H-03/H-04 y no se identifican regresiones nuevas en su interacción.

La validación POSIX real continúa pendiente en B-ADV-0038. No se declara ejecutada ni se solicita repetir las verificaciones verdes o la suite completa.

## Entrega del informe

El intento de escritura en `docs/review/code_reviews/B-ADV-0032-code-review.md` falló. Se entrega aquí el contenido íntegro para su transcripción por el coordinador, conservando los informes anteriores. No se atribuye escritura satisfactoria ni lectura directa del árbol.

---

## Informes anteriores

# B-ADV-0032 — Reevaluación de código

**Veredicto: RECHAZADO**
**Revisor:** Hades
**Árbol declarado:** `fff2e720d2`
**Media: 7,50/10. Existe un hallazgo ALTA.**

## Alcance y límites

Revisión estática del delta completo de producción de B-ADV-0032: captura JSON, terminación de árboles, configuración de timeout y consumidores `ejecutar()`/`agente()`. Se contrastan las funciones exactas adjuntas con la ficha, el diseño y la plataforma proporcionados.

Se excluyen cambios de otros IDs y las pruebas como código de producción. La conmutación por acceso de suscripción se considera contexto ajeno al bug.

El arnés impidió ejecutar comandos y acceder a archivos por la vía alternativa. Se utilizaron las instrucciones, skill y materiales adjuntos. No se comprobó directamente el árbol, no se ejecutaron pruebas y no se modificaron archivos.

## Análisis estático y evidencia

| Comprobación | Evidencia y límite |
|---|---|
| Regresiones específicas | Coordinador `--verificar`: 11 pruebas, GREEN, 3,209 s, un skip POSIX explícito. No se repiten. |
| Review-test | APROBADO, 8,75/10, según informe aportado. |
| Compilación | `py_compile` de los dos Python afectados comunicado como verde sobre el árbol declarado. No se repite. |
| Integridad del diff | `git diff --check` comunicado como verde. No se repite. |
| Calidad aportada | `--calidad --base 9a143486c663f2afe2bbe4e7ef3a30743c65532a --aplicar`: código 0; formato/lint **OMITIDOS**, sin acreditar ejecución de esas herramientas. |
| Calidad de esta revisión | Intentada sin escritura y sin `--aplicar`; el arnés rechazó el lanzamiento. No produjo resultado de calidad. |
| Tipado y secretos | Herramientas no configuradas. No se observan secretos en el material revisado; no equivale a un escaneo automatizado. |
| Dependencias | Sin cambios declarados. |
| POSIX real | No ejecutado; seguimiento en B-ADV-0038. |

## Puntuaciones

| Criterio | Nota | Justificación |
|---|---:|---|
| Corrección | 6 | Corrige supervisión, precedencia y espera final; queda terminación incompleta en Windows con padre ya terminado. |
| Seguridad | 8 | Comandos por argumentos y aislamiento POSIX; persiste trabajo residual posible en Windows. |
| Conformidad | 8 | Respeta diseño, motor y biblioteca estándar; la garantía operativa de terminar el árbol queda incompleta. |
| Calidad | 8 | Sentinel explícito y supervisión legible; la estrategia Windows depende de conservar vivo al padre. |
| Eficiencia | 7 | Sondeo y esperas limitados en captura JSON; el caso Windows puede conservar procesos y bloquear captura por líneas. |
| Documentación | 8 | Documenta las correcciones y limitaciones POSIX, pero sigue prometiendo terminación del árbol sin cubrir el caso señalado. |
| **Media** | **7,50** | Existe un hallazgo ALTA que impide aprobar. |

## Reevaluación de hallazgos anteriores

| Hallazgo | Gravedad original | Estado | Para | Destino |
|---|---|---|---|---|
| H-01: supervisión tras salir el padre y terminación del grupo POSIX | ALTA | **Resuelto en el camino POSIX señalado anteriormente** | Desarrollador | Resolver; corrección satisfecha |
| H-02: rechazo de timeout no finito | MEDIA | **Resuelto; se mantiene cerrado** | Desarrollador | Descartar como pendiente |
| H-03: distinguir timeout omitido y desactivado | MEDIA | **Resuelto** | Desarrollador | Resolver; corrección satisfecha |
| H-04: proteger espera posterior al EOF | ALTA | **Resuelto respecto a la cancelación prematura** | Desarrollador | Resolver; corrección satisfecha |

**H-01:** la captura JSON vigila conjuntamente proceso y lectores. La salida del padre ya no abandona la supervisión: conserva timeout y gracia, y añade un plazo desde su salida. Ambos `Popen` crean sesión POSIX propia y el helper llama a `killpg` incluso con el líder terminado. La inspección resuelve el defecto previo; la ejecución POSIX real continúa pendiente.

**H-02:** `math.isfinite` sigue rechazando valores no finitos antes de interpretar cero o negativos finitos como desactivación.

**H-03:** `_TIMEOUT_OMITIDO` distingue omisión de `None` explícito. `ejecutar()` propaga también `None`; `agente()` conserva el valor resuelto. El perfil desactivado ya no recupera involuntariamente el timeout del entorno.

**H-04:** el temporizador permanece activo durante `p.wait()` y se cancela después. Esto corrige la cancelación anterior al cierre del proceso. Su eficacia sigue dependiendo de que la terminación del árbol funcione; el defecto Windows siguiente es independiente de esa corrección.

## Hallazgos nuevos

### H-05 — 🟠 ALTA: Windows no termina descendientes cuando el padre ya salió

**Para:** desarrollador / Artemisa
**Destino:** resolver en B-ADV-0032
**Ubicación:** `_terminar_arbol_proceso()`, invocado desde la supervisión JSON y el temporizador de captura por líneas.

La rama Windows utiliza exclusivamente `taskkill /F /T /PID <pid_del_padre>` para terminar descendientes. Si el padre ya terminó y su PID dejó de existir, esa orden no dispone del proceso raíz desde el que localizar el árbol. El posterior `p.kill()` tampoco alcanza a los descendientes. Además, se ignora el código de salida de `taskkill`.

**Caso concreto:**

1. El arnés crea un hijo que hereda stdout/stderr.
2. El padre emite JSON final y termina.
3. El hijo permanece ejecutándose con los pipes abiertos.
4. La nueva supervisión agota la gracia e invoca el helper con el PID del padre terminado.
5. `taskkill` falla y el helper no conserva otro mecanismo para terminar al hijo.

En captura JSON puede devolverse éxito con `cierre_forzado=True` aunque el descendiente continúe trabajando. En captura por líneas, el temporizador puede encontrar igualmente al padre terminado y dejar al lector esperando EOF del descendiente, sin resolver el bloqueo.

**Impacto:** incumple la terminación del árbol en Windows, entorno principal del producto. Puede conservar trabajo que modifica artefactos después del retorno y mantener bloqueado el camino por líneas.

**Corrección requerida:** conservar una capacidad de terminación de descendientes que sobreviva a la salida del padre, por ejemplo mediante una agrupación Windows gestionada desde el lanzamiento. No basta con repetir `taskkill` sobre el PID desaparecido. Proteger específicamente el caso de padre terminado con hijo vivo y pipes heredados, sin exigir proveedores externos ni la suite completa.

Este hallazgo se deduce del flujo adjunto. No se presenta como reproducción ejecutada ni corresponde al seguimiento POSIX de B-ADV-0038.

## Antecedentes conservados

La revisión anterior fue **RECHAZADA**, con media **7,17/10**: H-01 persistía parcialmente; H-02 estaba resuelto; H-03 y H-04 eran nuevos.

Esta reevaluación reconoce las tres correcciones pendientes y mantiene H-02 cerrado. H-05 identifica una limitación adicional de la terminación Windows dentro del alcance completo solicitado.

## Dictamen

**RECHAZADO por H-05.** Resolver la terminación de descendientes Windows tras la salida del padre. No se requiere decisión humana ni ampliación a otros IDs. La ejecución POSIX real permanece registrada en B-ADV-0038.

---

## Informes anteriores

# B-ADV-0032 — Revisión independiente de código

**Veredicto: RECHAZADO**
**Media: 7,17/10. Persisten defectos de gravedad ALTA.**

## Alcance y limitaciones

Revisión del delta completo de producción atribuible a B-ADV-0032 y de las correcciones de H-01/H-02, contrastado con las funciones vigentes adjuntas, la ficha del bug, el diseño y la plataforma.

Se excluyen B-ADV-0033, B-ADV-0037, cualquier otro delta histórico y las pruebas como código de producción.

El acceso al disco falló previamente en esta sesión. Esta revisión utiliza exclusivamente los materiales adjuntos: no se han leído las instrucciones instaladas de Hades y `/review-code`, comprobado el árbol ni escrito el archivo de destino. **No he ejecutado herramientas, pruebas ni modificaciones.**

## Evidencia aportada

| Comprobación | Resultado y límite |
|---|---|
| Triaje autorizado mediante `--verificar` | 6 pruebas: 5 OK y 1 skip POSIX explícito; 0,897 s. Se reutiliza la evidencia. |
| Compilación | `py_compile` de los dos Python afectados: OK. |
| Integridad del diff | `git diff --check HEAD`: OK; comparación con base limitada a archivos de B-ADV-0032: OK. |
| Comparación histórica global | Espacios finales preexistentes en informe de B-ADV-0033; excluidos de este alcance. |
| Calidad | `--calidad --base 9a143486c663f2afe2bbe4e7ef3a30743c65532a --aplicar`: código 0 comunicado, con formato/lint **OMITIDOS**. No acredita su ejecución. |
| Tipado y seguridad automatizada | Tipado no configurado; sin escáner de seguridad configurado. |
| Dependencias y secretos | Sin dependencias nuevas declaradas. No se observan secretos en el material de producción revisado. |
| Validación POSIX | No ejecutada. Seguimiento registrado como B-ADV-0038 según información aportada. |

La aprobación de las pruebas no acredita los caminos de producción señalados a continuación.

## Puntuación

| Criterio | Nota | Justificación |
|---|---:|---|
| Corrección | 6 | Corrige stdin y valores no finitos, pero quedan caminos de descendientes supervivientes y espera indefinida. |
| Seguridad | 8 | Grupo POSIX aislado y comandos por argumentos; el cierre incompleto permite trabajo residual. |
| Conformidad con diseño/arquitectura | 7 | Respeta motor y biblioteca estándar; no completa la garantía de terminación acotada. |
| Calidad | 7 | Helpers separados, pero el ciclo de vida depende de la salida del padre y `None` tiene significados incompatibles. |
| Eficiencia | 7 | Esperas y sondeo acotados en parte del flujo; persisten procesos residuales y una espera sin límite. |
| Documentación | 8 | Diseño y changelog describen la intención y las limitaciones de validación; la garantía de cierre excede el comportamiento implementado. |
| **Media** | **7,17** | No supera 8 y existen hallazgos ALTA. |

## Reevaluación de hallazgos anteriores

### H-01 — ALTA — PERSISTE parcialmente: salir el padre evita terminar el grupo

**Para:** desarrollador
**Destino:** resolver
**Ubicación:** `skills/orquestar/orquestar.py`, `_ejecutar_captura_json()`, bucle `while p.poll() is None` y finalización de lectores.

**Corrección reconocida:** ambos `Popen` crean sesión propia en POSIX. `_terminar_arbol_proceso()` señaliza el grupo mediante `killpg(pid, SIGKILL)` incluso si el líder ya salió, siempre que se invoque.

**Defecto restante:** la captura JSON deja de vigilar timeout y gracia en cuanto termina el proceso directo. Si el padre crea un descendiente que hereda stdout/stderr, emite el JSON y sale, el bucle termina sin llamar al helper. Tras los `join` limitados se cierran los streams y se devuelve el resultado, pero el descendiente continúa vivo.

Esto también puede ocurrir si el padre sale durante la gracia posterior al JSON. La capacidad del helper de matar un grupo cuyo líder terminó no resuelve la ausencia de llamada desde este camino.

**Impacto:** permanece el incumplimiento de terminación del árbol identificado en H-01. El descendiente puede seguir consumiendo recursos o modificando artefactos después del retorno.

**Corrección requerida:** mantener la supervisión del cierre de los streams y del grupo tras la salida del padre, con plazo acotado y terminación del grupo cuando corresponda. Conservar respuesta y métricas.

### H-02 — MEDIA — RESUELTO: rechazo de timeouts no finitos

**Para:** desarrollador
**Destino:** descartar como pendiente
**Ubicación:** `timeout_de_rol()`.

`math.isfinite(num)` rechaza `inf`, `-inf` y `nan` antes de interpretar valores no positivos como desactivación. En `agente()`, estas entradas recuperan el valor seguro de 1800 segundos.

La resolución se acredita por inspección y por la evidencia de regresión aportada. No implica validación POSIX real.

## Hallazgos nuevos

### H-03 — MEDIA — La desactivación explícita del timeout se pierde al propagarse

**Para:** desarrollador
**Destino:** resolver
**Ubicación:** `timeout_de_rol()`, `ejecutar()`, `agente()` y comienzo de `lanzar()`.

Un cero o negativo finito del perfil produce `None`, conforme al diseño. Sin embargo, `lanzar(timeout=None)` vuelve a consultar el entorno porque interpreta ese mismo valor como ausencia de configuración.

**Caso concreto:** perfil con `timeout_s: 0` y `ORQUESTAR_TIMEOUT_S=60`. El perfil solicita desactivación, pero `lanzar()` recupera 60 y termina el arnés por timeout. En `ejecutar()` además se omite el argumento cuando el resultado es `None`.

**Impacto:** se incumple la precedencia del perfil y la desactivación explícita documentada, pudiendo interrumpirse trabajo válido.

**Corrección requerida:** distinguir «timeout no especificado» de «timeout desactivado» y conservar esa distinción entre los consumidores.

### H-04 — ALTA — La captura por líneas cancela el timeout antes de esperar al proceso

**Para:** desarrollador
**Destino:** resolver
**Ubicación:** `lanzar()`, rama de captura por líneas, `finally` y salida del contexto `Popen`.

El temporizador se cancela al terminar la lectura de stdout, antes de abandonar el contexto `Popen`, cuya salida espera al proceso.

**Caso concreto:** un arnés de esta rama cierra stdout/stderr y continúa ejecutándose. La iteración recibe EOF, el `finally` cancela el temporizador y la salida del contexto espera indefinidamente. También puede alcanzarse EOF por una excepción antes de completar el proceso.

**Impacto:** el timeout incorporado por B-ADV-0032 deja de proteger la espera final y permite reproducir un bloqueo indefinido.

**Corrección requerida:** mantener el límite durante todo el ciclo de vida, incluida la espera posterior a EOF, y cancelar el temporizador únicamente tras confirmar la terminación o completar una finalización acotada.

## Aspectos conformes

`agy` recibe `entrada=None` tanto en la invocación inicial como en el reintento. La captura JSON lee ambos streams concurrentemente, conserva métricas tras cierre forzado y los llamantes evitan reiniciar una sesión cuando se informa timeout.

La implementación mantiene el stack y las capas existentes, sin nuevas dependencias ni necesidad identificada de una decisión arquitectónica adicional.

## Dictamen

**RECHAZADO.** H-02 queda resuelto; H-01 persiste en el camino donde el padre termina antes que sus descendientes. H-03 y H-04 son hallazgos nuevos del delta revisado.

La validación POSIX pendiente permanece registrada en B-ADV-0038. Su ausencia no es el motivo del rechazo: los defectos descritos se deducen del flujo de producción adjunto.
