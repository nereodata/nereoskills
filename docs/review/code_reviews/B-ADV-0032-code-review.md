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
