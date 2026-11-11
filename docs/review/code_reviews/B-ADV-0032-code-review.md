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
