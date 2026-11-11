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
