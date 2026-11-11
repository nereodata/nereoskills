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
