**Veredicto:** APROBADO

# B-ADV-0040 · Reevaluación aislada de H1/H2 · 2026-11-11

- Revisor: Hades mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, salida 0, media 9/10.
- Transcripción del dictamen independiente por Atenea: el arnés no pudo leer ni escribir disco (`registered Core launch requires an installed app`). No se atribuye a Hades comprobación del árbol ni ejecución de verificaciones.

## Alcance y evidencia

Se revisan exclusivamente los dos bloques añadidos desde `38f3136`:

- «Conservar el tratamiento de errores genéricos al revisar con Hades».
- «Recuperar una revisión respondida desde una instantánea identificada».

Los cinco bloques previamente aprobados se utilizan como contexto, sin reauditarse. Se contrastan el diff, los criterios de aceptación, el contexto BDD y el informe anterior íntegro suministrados.

**Límite:** no fue posible leer el repositorio, las instrucciones instaladas ni las evidencias de verificación, o escribir este reporte. El dictamen se basa exclusivamente en los adjuntos exactos. Las conclusiones sobre conservación del contrato y ubicación corresponden al diff y las rutas adjuntos, sin comprobación independiente del árbol.

## Comprobaciones obligatorias

| Comprobación | Resultado | Evidencia |
|---|---|---|
| No regresión | Conforme sobre el diff adjunto | Solo se añaden dos bloques; no se eliminan ni modifican los cinco aprobados ni el contrato anterior de autenticación. |
| Coherencia | Conforme | Los errores genéricos conservan su fallo sin activar reservas. La recuperación respeta la incorporación entre pasos, la idempotencia y el trabajo ajeno. No contradice el tratamiento diferenciado del paso del bucle y del agente Hades. |
| Trazabilidad | Conforme | Ambos bloques llevan `@B-ADV-0040`, existente en el bug. El primero concreta H1 y el límite de la conmutación; el segundo concreta H2 y el cuarto criterio de aceptación. No añaden etiquetas `@CA-*`. |
| Delta real | Conforme | Se incorporan casos observables que faltaban en las afirmaciones generales: dos errores literales y dos estados iniciales de recuperación. La precisión complementa los bloques anteriores sin duplicarlos íntegramente. |

## Puntuaciones

| Dimensión | Puntuación | Motivo |
|---|---:|---|
| Claridad | 9/10 | Entradas literales, estados iniciales y transiciones determinadas. |
| Completitud | 9/10 | Cubre autenticación y red, recepción pendiente y respuesta incorporada, espera por trabajo ajeno y recuperación posterior. |
| Testeabilidad | 9/10 | Fija códigos, lanzamientos, dictamen, estados, bytes, referencias de comparación e idempotencia. |
| Estructura | 9/10 | Ambos esquemas se ubican en la feature funcional de orquestación; las filas distinguen variantes del mismo comportamiento. |
| **Media** | **9/10** | Supera el umbral de aprobación. |

## Hallazgos anteriores

| Hallazgo | Severidad anterior | Para | Destino | Resultado |
|---|---|---|---|---|
| H1 | Alta | especificador | resolver | **Resuelto.** Las filas provocan `authentication failed` y `network connection failed`, con código 1, sin sesión previa ni señales de cuota o suscripción deshabilitada. Exigen conservar el diagnóstico, lanzar únicamente Claude una vez y mantener la revisión pendiente sin progreso ficticio. |
| H2 | Alta | especificador | resolver | **Resuelto.** Cada fila identifica pregunta, tarea, respuesta y estado inicial. La revisión pendiente es `review-test`; se fijan historial RT-PREVIO, WIP W0 y trabajo ajeno A0. Se observa la espera ante árbol sucio, la recuperación tras guardarlo, la restauración exacta y el dictamen APROBADO de Codex sin hallazgos que enrutar. La continuación conserva historial y respuesta, evita restauraciones repetidas y no acredita cierre. |

## Hallazgos nuevos

No se identifican hallazgos críticos, altos, medios ni bajos en los dos bloques añadidos.

## Dictamen

**H1 y H2 quedan resueltos. APROBADO exclusivamente para especificación.**

No se revisaron diseño, pruebas ni código; no se ejecutaron verificaciones, no se modificaron estados y no se hicieron commits por Hades. La aprobación no acredita funcionamiento, implementación ni cierre de B-ADV-0040.

---

## Antecedente íntegro · Revisión anterior

**Veredicto:** RECHAZADO

# B-ADV-0040 · Revisión de Artemisa al reanudar · 2026-11-11

- Revisor: Hades mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; transcripción del dictamen independiente, media 7,75/10.
- Límite: el arnés no pudo acceder al disco (`registered Core launch requires an installed app`) ni escribir el informe. Revisó los cinco bloques completos adjuntos, sin código ni pruebas. No regresión no verificable por el revisor; coherencia conforme solo dentro del material recibido; trazabilidad y delta real conformes.
- Error de alcance de Artemisa: se reenviaron los cinco bloques previamente aprobados sin cambios, aunque `/review-spec` excluye los escenarios ya aprobados. No se adjuntó el informe aprobado anterior. Se conserva ese informe íntegro como antecedente; el especificador recibe también este límite para resolver el enrutado sin duplicar contratos. No se atribuye a Hades una comprobación del disco ni una revisión de pruebas o implementación.

| Dimensión | Puntuación |
|---|---:|
| Claridad | 8 |
| Completitud | 7 |
| Testeabilidad | 7 |
| Estructura | 9 |
| Media | 7,75 |

## Hallazgos recibidos

### H1 · Alta · para: especificador · destino: resolver

El escenario de indisponibilidad prepara únicamente el literal de suscripción deshabilitada y afirma que los errores genéricos conservan su tratamiento anterior, sin provocarlos. Hades pide casos independientes de autenticación y red con entradas representativas y resultados observables (lanzamientos y resultado/diagnóstico), referenciando el contrato vigente sin inventar otro.

### H2 · Alta · para: especificador · destino: resolver

La recuperación no fija para cada copia la respuesta recibida, revisión pendiente, dictamen y destino de la reserva ni estado observable de reanudación. Hades pide fixtures identificadas o instantáneas iniciales para comparar WIP, historial, respuestas y trabajo ajeno, además de esos resultados determinados.

## Decisión y evidencia del intento

Se enruta a especificador por asignación explícita; no se abre pregunta humana. El contrato BDD no se ha modificado. Diseño y pruebas siguen siendo borradores sin review-test ni implementación de producción. Rojo dirigido: 8 pruebas, 7 fallos, sin errores; seis fallos reproducen reservas/diagnóstico/espera y el séptimo reproduce restauración WIP LF con Git real en Windows. Se corrigió antes del último rojo la declaración de perfil estricto para usar `estricto` al nivel admitido por el parser. No se ha ejecutado la suite completa.

---

## Antecedentes íntegros

**Veredicto:** APROBADO

# B-ADV-0040 · Reevaluación con evidencia completa · 2026-11-11

- Revisor: Hades mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, aplicando las instrucciones completas de Hades y `/review-spec` adjuntas.
- Alcance: cinco bloques BDD exactos del árbol (seis casos contando las dos filas). No hay modificación BDD desde `d0f9471`; se suministraron los cuatro bloques omitidos en el rechazo anterior.
- Límite: el arnés falló al acceder al disco con `registered Core launch requires an installed app`. Hades revisó exclusivamente los adjuntos; no comprobó el árbol ni escribió el reporte, no modificó estados ni ejecutó pruebas. Atenea transcribe el dictamen y sintetiza las tablas, conservando íntegro el reporte anterior debajo.

## Comprobaciones obligatorias

| Comprobación | Resultado | Motivo del revisor |
|---|---|---|
| No regresión | Conforme sobre la garantía declarada | Escenarios anteriores intactos, sin cambios BDD desde aprobación previa. No contrastado contra disco por Hades. |
| Coherencia | Conforme en el contexto adjunto | Distingue acceso deshabilitado, cuotas, restricción estricta y rechazo auténtico; conserva tratamiento de errores genéricos de autenticación/red. |
| Trazabilidad | Conforme | Cinco bloques con `@B-ADV-0040`, correspondientes a los cuatro criterios; sin etiquetas CA adicionales. |
| Delta real | Conforme | Selección de reserva, rechazo con destino, perfil estricto, indisponibilidad repetida y recuperación son casos distintos; aportar bloques omitidos no duplica BDD. |

## Puntuaciones

| Dimensión | Puntuación | Motivo del revisor |
|---|---:|---|
| Claridad | 9/10 | Desencadenante literal, resultados diferenciados para revisión completada, rechazo y bloqueo técnico. |
| Completitud | 9/10 | Ambas reservas, orden, omisión por cuota, perfil estricto, rechazo auténtico, fallo repetido y recuperación de ambas tareas. |
| Testeabilidad | 9/10 | Secuencias exactas, dictámenes, destinatario, estado y preservación de trabajo y respuestas. |
| Estructura | 8/10 | Bloques separados y esquema para variantes equivalentes; ubicación en feature funcional no comprobada por el revisor. |
| **Media** | **8,75/10** | Supera el umbral de 8. |

## Reevaluación

| Hallazgo | Severidad anterior | Para | Destino | Resultado y evidencia |
|---|---|---|---|---|
| RS-0040-01 | Alta | especificador | resolver | Resuelto: perfil Claude con estricto true, reserva operativa, solo Claude se lanza; revisión pendiente, conservación del perfil sin preguntar por reserva. |
| RS-0040-02 | Alta | especificador | resolver | Resuelto: RECHAZADO auténtico de agy, hallazgo alto para especificador, tarea blocked y pendiente_de especificador con hallazgo registrado, sin confundirlo con indisponibilidad técnica. |
| RS-0040-05 | Alta | especificador | resolver | Resuelto: ambos perfiles fallan con diagnóstico literal en dos solicitudes; revisión pendiente, trabajo y preguntas conservados sin duplicación ni progreso ficticio; último escenario cubre recuperación con reserva operativa. |
| RS-0040-06 | Alta | especificador | resolver | Resuelto: copias aisladas de ambas preguntas con respuestas y WIP; dictamen real, conservación del WIP, historial y respuestas, respeto al trabajo ajeno sin exigir otra respuesta. |

RS-0040-03/04 mantienen su resolución previa: registro del arnés final y elegibilidad de Codex con omisión de agy agotado.

## Cobertura

| Criterio | Evidencia |
|---|---|
| Reserva elegible, orden, cuotas, restricción estricta y registro | Esquema Claude/agy y Claude/Codex; escenario de perfil estricto. |
| Dictamen real y destino sin preguntas de configuración | APROBADO sin preguntas; RECHAZADO con destinatario, estado y siguiente paso. |
| Conservación, recuperación, ausencia de duplicación y progreso ficticio | Dos solicitudes fallidas y recuperación posterior con reserva disponible. |
| Recuperación de ambas tareas y preservación del estado | Copias aisladas de ambas preguntas con WIP, historial, respuestas y trabajo ajeno; las regresiones posteriores usarán lanzadores simulados. |

## Hallazgos nuevos y dictamen

Hades no identifica hallazgos críticos, altos, medios ni bajos nuevos.

Dictamen recibido: «Los cuatro hallazgos del rechazo por adjunto incompleto quedan **resueltos** al aportar los escenarios omitidos. El contrato completo satisface los criterios suministrados y queda **APROBADO para especificación**».

La aprobación no acredita diseño, implementación, pruebas funcionales ni cierre del bug. La comprobación de disco de Atenea confirma un diff BDD vacío contra `d0f9471`; no se atribuye esa comprobación a Hades.

---

## Antecedente íntegro · Rechazo sobre adjunto incompleto

**Veredicto:** RECHAZADO

# B-ADV-0040 · Revisión aislada del intento de bug-fix · 2026-11-11

- Revisor: Hades mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`.
- Transcripción resumida del dictamen independiente. El arnés no pudo leer disco ni escribir el informe (`registered Core launch requires an installed app`); tampoco pudo leer las instrucciones instaladas de Hades/review-spec. Dictaminó exclusivamente sobre los adjuntos.
- Hades recibió por error solo el primer esquema BDD. Artemisa cortó la extracción en la siguiente etiqueta del mismo ID. El rechazo no demuestra un defecto del contrato completo del repositorio y no invalida por sí mismo los escenarios previamente aprobados. La siguiente revisión requiere todos los bloques completos y las instrucciones de la skill adjuntas.
- No hubo revisión de diseño, pruebas ni código, ni implementación de producción.

## Dictamen recibido

**RECHAZADO sobre el contrato BDD adjunto**. Hallazgos para **especificador**, tratamiento **resolver**.

| Hallazgo | Severidad | Evidencia recibida por Hades | Para | Destino |
|---|---|---|---|---|
| RS-0040-01 | Alta | No se aporta el escenario de perfil explícitamente estricto. | especificador | resolver |
| RS-0040-02 | Alta | No se aporta el escenario de rechazo auténtico y tratamiento de su destino. | especificador | resolver |
| RS-0040-05 | Alta | No se especifica la indisponibilidad total ni la repetición del mismo fallo. | especificador | resolver |
| RS-0040-06 | Alta | No se especifica la recuperación de Q-ADV-0001 y Q-ADV-0002 con conservación del estado. | especificador | resolver |

Hades dio por resueltos RS-0040-03/04 en el esquema adjunto: registro del arnés revisor, Codex elegible y omisión de agy agotado. Indicó que, si los escenarios restantes ya existen, deben incorporarse a la evidencia sin duplicarlos. No emitió puntuaciones numéricas en esta respuesta.

## Decisión y límites

Se ejecutó `--enrutar-hallazgo B-ADV-0040 especificador` conforme al destino explícito. Sin pregunta humana. Se preservó el intento en `wip/B-ADV-0040` (0e24407), con el WIP anterior en `wip/B-ADV-0040-anterior-20261111`. El árbol de trabajo volvió al estado previo al intento antes de registrar el enrutado.

La prueba dirigida dio 8 casos, 6 fallos y 1 error; la fixture de recuperación Git aún falla en Windows y no acredita rojo válido del producto. No se ejecutó suite completa ni se aprobó review-test, implementación o cierre.

---

## Antecedente previo íntegro

**Veredicto:** APROBADO

# B-ADV-0040 · Revisión aislada de especificación · 2026-11-11

- Revisor: Hades, invocado mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`.
- Alcance: exclusivamente el delta BDD adjunto: un esquema con dos ejemplos y cuatro escenarios, contrastados con los criterios de aceptación de B-ADV-0040.
- Antecedente: rechazo anterior con media 7,5/10 y hallazgos RS-0040-01/02/03/04, conservado íntegro debajo.
- Límite de evidencia: el acceso al disco falló con `registered Core launch requires an installed app`. Hades revisó los adjuntos exactos; no pudo comprobar el diff ni escribir el informe. Atenea transcribe su dictamen y sintetiza sus tablas a continuación. No es una revisión propia.
- Exclusiones: no se revisaron diseño, código ni tests; no se ejecutaron pruebas funcionales, no se modificaron estados y no se hicieron commits por Hades.

## Comprobaciones obligatorias

| Comprobación | Resultado | Evidencia |
|---|---|---|
| No regresión | Conforme sobre la entrada declarada | Permanecen intactos los escenarios anteriores aprobados; los tres borradores rechazados se precisan y amplían. Hades no verificó esta garantía contra disco. |
| Coherencia | Conforme | Diagnóstico literal, reservas autorizadas, orden, cuotas, perfil estricto, rechazo auténtico y tratamiento anterior de errores genéricos. |
| Trazabilidad | Conforme | Todos los bloques llevan el ID existente `@B-ADV-0040`; no hay etiquetas CA adicionales y los cuatro criterios tienen cobertura explícita. |
| Delta real | Conforme | Continuación tras fallo de acceso y recuperación; aprobación, rechazo, perfil estricto, indisponibilidad y recuperación tienen condiciones y resultados distintos. |

## Puntuaciones

| Dimensión | Puntuación | Motivo |
|---|---:|---|
| Claridad | 9/10 | Desencadenante literal y distinción entre dictamen real, rechazo e indisponibilidad técnica. |
| Completitud | 9/10 | Ambas reservas, omisión por cuota, rechazo, restricción estricta, fallo repetido y recuperación de ambas preguntas. |
| Testeabilidad | 9/10 | Elegibilidad, secuencias exactas, veredictos, estados y preservación de WIP, historial, respuestas y trabajo ajeno. |
| Estructura | 9/10 | Escenarios en la funcionalidad de orquestación; esquema para las dos selecciones de reserva. |
| **Media** | **9/10** | Supera el umbral de aprobación de 8. |

## Resolución de los hallazgos anteriores

| Hallazgo | Severidad anterior | Para | Destino | Resultado y evidencia |
|---|---|---|---|---|
| RS-0040-01 | Media | especificador | resolver | Resuelto: perfil de Hades Claude con estricto true y agy operativa; solo se lanza Claude, diagnóstico de acceso/restricción y revisión pendiente, sin pregunta ni cambio de perfil. |
| RS-0040-02 | Media | especificador | resolver | Resuelto: agy emite RECHAZADO con hallazgo alto para especificador; se exige blocked, pendiente_de especificador y registro para ejecutar especificar, sin pregunta humana ni confusión con indisponibilidad. |
| RS-0040-03 | Media | especificador | resolver | Resuelto: ambas filas exigen historial con fallo de Claude y arnés revisor final. |
| RS-0040-04 | Baja | especificador | resolver | Resuelto: Codex disponible, autorizado y sin cuota; secuencia exacta Claude, Codex cuando agy tiene cuota vigente, y Claude, agy en la otra fila. |

## Cobertura de los criterios

| Criterio | Cobertura |
|---|---|
| Reserva elegible, orden, cuotas, perfil estricto y registro | Esquema de continuación y escenario de perfil estricto. |
| Dictamen real sin preguntas y tratamiento del rechazo | Esquema APROBADO y escenario RECHAZADO con destinatario y estado. |
| Preservación, reintento, ausencia de duplicación y progreso ficticio | Dos solicitudes con ambos perfiles indisponibles; escenario siguiente recupera con reserva operativa. |
| Recuperación de ambas respuestas con WIP, historial y trabajo ajeno | Copias aisladas de ambas preguntas, dictamen real y ausencia de nueva respuesta requerida. |

## Hallazgos nuevos

No se identifican hallazgos críticos, altos, medios ni bajos en el delta adjunto.

## Dictamen y verificación

La resolución satisface RS-0040-01/02/03/04. La aprobación se limita al contrato BDD; no acredita implementación ni validación funcional. Hades no ejecutó diff-check por el fallo del arnés. Las regresiones con lanzadores simulados corresponden al desarrollador conforme al triaje.

---

## Antecedente íntegro · Revisión rechazada

**Veredicto:** RECHAZADO

# B-ADV-0040 · Revisión aislada de especificación

- Revisor: Hades, invocado mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`.
- Alcance: exclusivamente los tres escenarios añadidos con etiqueta `@B-ADV-0040`, contrastados con los criterios de aceptación y el triaje suministrados.
- La primera invocación no pudo leer disco por `registered Core launch requires an installed app`. La segunda recibió criterios y escenarios completos en el mandato y emitió este dictamen sin herramientas. Este archivo transcribe su veredicto, puntuaciones y hallazgos; no es una revisión propia de Artemisa.
- Hades no examinó diseño ni código ni ejecutó pruebas. La no regresión se evaluó sobre la garantía expresa del mandato; no se comprobó un diff del repositorio.

## Comprobaciones obligatorias

| Comprobación | Resultado | Evidencia |
|---|---|---|
| No regresión | Conforme sobre la entrada declarada | Ningún escenario anterior se modifica. El segundo escenario exige conservar el tratamiento de errores genéricos de autenticación o red. |
| Coherencia | Parcial | La conmutación por el diagnóstico literal de suscripción deshabilitada respeta el alcance. La aserción de perfil estricto carece de una precondición que active ese perfil. |
| Trazabilidad | Parcial | Hay cobertura de reservas, cuota vigente, indisponibilidad repetida y recuperación de ambas preguntas. Faltan resultados explícitos para el rechazo auténtico y la identificación del revisor final en el registro. |
| Delta real | Conforme | Se especifica la recuperación ante el diagnóstico concreto de suscripción deshabilitada y la reanudación de revisiones pendientes. No se redefine el contrato de `authentication failed`. |

## Puntuaciones

| Dimensión | Puntuación | Motivo |
|---|---:|---|
| Claridad | 8/10 | El desencadenante principal y los resultados esperados son claros; algunos estados quedan implícitos. |
| Completitud | 7/10 | Faltan garantías explícitas del tratamiento de un rechazo auténtico y de la trazabilidad del revisor final. |
| Testeabilidad | 7/10 | El perfil estricto no se establece y la selección de Codex presupone su disponibilidad. |
| Estructura | 8/10 | Los tres bloques separan los flujos principales, pero el segundo incorpora una variante que necesita preparación propia. |
| Media | 7,5/10 | No supera el umbral de aprobación de 8. |

## Hallazgos

### RS-0040-01 · El perfil estricto se afirma sin establecerlo

- Severidad: media.
- Para: especificador.
- Destino: resolver.
- Ubicación: «Conservar la revisión cuando ningún perfil autorizado puede revisar».
- Evidencia: el escenario concluye que «un perfil fijado estricto nunca ejecuta reservas», pero sus precondiciones no establecen que se haya fijado un perfil estricto.
- Impacto: una ejecución con configuración ordinaria podría satisfacer esa aserción sin ejercitar la restricción. No queda demostrada la garantía de respetar perfiles explícitamente estrictos.
- Corrección requerida: añadir un escenario o variante con un perfil fijado estricto y una reserva disponible; comprobar que, ante el diagnóstico literal, no se lanza ninguna reserva y la revisión permanece pendiente.

### RS-0040-02 · No se exige conservar el tratamiento del rechazo auténtico

- Severidad: media.
- Para: especificador.
- Destino: resolver.
- Ubicación: «Continuar la revisión con una reserva tras acceso por suscripción deshabilitado».
- Evidencia: se exige recibir el dictamen con veredicto y destino, pero no se concreta ningún caso con un rechazo auténtico ni su tratamiento habitual en la tarea.
- Impacto: transportar un dictamen no demuestra que el paso aplique correctamente un rechazo. El segundo criterio de aceptación exige ambas garantías.
- Corrección requerida: incluir una variante en la que la reserva emita un rechazo real con destino y exigir que la tarea siga el tratamiento habitual de ese rechazo, sin confundirlo con indisponibilidad técnica.

### RS-0040-03 · El registro no identifica explícitamente al revisor final

- Severidad: media.
- Para: especificador.
- Destino: resolver.
- Ubicación: primer esquema, resultados esperados.
- Evidencia: el historial debe identificar el fallo de Claude; la identidad de `<revisor>` solo aparece vinculada al dictamen recibido.
- Impacto: podría cumplirse el escenario sin dejar registrado qué arnés completó la revisión, aunque el primer criterio exige esa identificación en el registro.
- Corrección requerida: exigir que el historial o registro identifique también el arnés que finalmente revisa, para ambas filas de ejemplos.

### RS-0040-04 · La elegibilidad de Codex queda implícita

- Severidad: baja.
- Para: especificador.
- Destino: resolver.
- Ubicación: primer esquema, fila `cuota vigente → Codex`.
- Evidencia: se define la disponibilidad de agy, pero no la disponibilidad y autorización efectiva de Codex para ese intento.
- Impacto: el resultado depende de una condición no declarada. Tener una reserva configurada no establece por sí solo que sea elegible.
- Corrección requerida: explicitar que Codex está disponible y autorizado; para la fila con cuota vigente, exigir que agy se omita sin ejecutarlo.

## Condiciones para aprobar

Resolver los hallazgos en los escenarios del delta y repetir la revisión aislada. Mantener intactos los escenarios anteriores y el comportamiento de `authentication failed`: la nueva conmutación corresponde exclusivamente al diagnóstico literal de suscripción deshabilitada.

Las verificaciones posteriores deben usar lanzadores simulados y copias aisladas del estado, conforme al triaje.
