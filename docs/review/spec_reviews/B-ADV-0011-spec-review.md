# B-ADV-0011 — Revisión de especificación (reevaluación)

**Veredicto: APROBADO**

Reevaluación en modo orquestado sobre la especificación actual del árbol de trabajo, tras releer la skill instalada `review-spec`. Alcance: delta de `skills/orquestar/features/orquestacion.feature`, bug de origen `docs/plan/bugs/B-ADV-0011-fallo-transitorio-del-arnes-para-el-bucle.md` y cierre de los hallazgos anteriores. El informe previo describía una instantánea anterior a los cambios concurrentes; esta evaluación lo sustituye.

No se ha revisado diseño, código ni pruebas. No se han ejecutado suites ni realizado commits.

## Comprobaciones obligatorias

| Criterio | Resultado | Motivo |
| --- | --- | --- |
| No regresión | ✅ | La única modificación del escenario previo restringe la prohibición de reservas a agente y gateway, conservando sus resultados. La sustitución para pasos está expresamente autorizada por Alcance y DEC-11; no constituye una regresión indebida. Los demás escenarios previos permanecen fuera de la reevaluación. |
| Coherencia | ✅ | El escenario de error operacional ya no incluye pasos. Los nuevos escenarios establecen su recuperación mediante reintentos y reservas, preservando cuota y progreso conforme a DEC-11–13. |
| Trazabilidad | ✅ | Los siete escenarios nuevos llevan `@B-ADV-0011` y corresponden al comportamiento esperado y sus decisiones. No se introducen etiquetas `@CA-*` sin criterio de origen. |
| Delta real | ✅ | Se especifica recuperación operacional de pasos, con límites y diagnóstico propios; no se duplica el contrato de ausencia de ejecutables. |

## Puntuaciones

| Criterio | Nota | Justificación |
| --- | --- | --- |
| Claridad | 9/10 | Quedan diferenciados los contratos de pasos y de agente/gateway. Los resultados describen el comportamiento observable de recuperación. |
| Completitud | 9/10 | Cubre fallo transitorio y persistente, reservas, límite cero y predeterminado, saturación de esperas, entradas inválidas, parada cooperativa, progreso en disco, falta de progreso y prioridad de cuota. |
| Testeabilidad | 9/10 | Los conteos, intervalos y ejemplo de salida permiten discriminar los límites acordados y la cola exacta de 2000 caracteres. |
| Estructura | 9/10 | El delta permanece en el archivo de su funcionalidad, sin archivos por tarea o fase. |

**Media: 9,0/10.** Sin hallazgos críticos ni altos pendientes.

## Reevaluación de hallazgos anteriores

| Hallazgo | Estado | Evidencia actual | Enrutamiento anterior |
| --- | --- | --- | --- |
| H-01 — Contrato previo incluyendo pasos | **Resuelto** | El escenario «Un error distinto de ausencia no habilita reservas» solo contempla agente Hades y conversación del gateway, tanto en antecedentes como en resultados. La recuperación de pasos queda en los escenarios nuevos, conforme a la sustitución autorizada por DEC-11. | `para: especificador`; `destino: resolver`; cerrado. |
| H-02 — Límites de DEC-12 sin ejemplos discriminantes | **Resuelto** | «Aplicar el límite por defecto y saturar la espera» exige cuatro intentos con 60/300/900 segundos al omitir la opción, y cuarta espera de 900 al configurar cuatro reintentos. También rechaza valores negativos y no enteros. «Recuperar un fallo transitorio del paso» sitúa el contador de falta de progreso a un intento del límite y exige que los reintentos no lo incrementen. Se conserva el caso de límite cero. | `para: especificador`; `destino: resolver`; cerrado. |
| H-03 — Cola del aviso sin límite concreto | **Resuelto** | El ejemplo de salida contiene 3000 letras A, seguidas de 1997 letras B y FIN; exige exactamente las 1997 letras B y FIN del último arnés como fragmento del aviso. Distingue los últimos 2000 caracteres del texto completo o de una cola más corta. | `para: especificador`; `destino: resolver`; cerrado. |

## Hallazgos nuevos

Ninguno. La corrección del escenario previo y los ejemplos añadidos no introducen contradicciones relevantes en el delta revisado. No queda trabajo que enrutar desde esta revisión de especificación.

## Identificación de la instantánea revisada

SHA-256 de los artefactos leídos, para distinguir esta reevaluación de cambios concurrentes posteriores:

- `skills/orquestar/features/orquestacion.feature`: `D98D20EF04395ADA28E65EEE413F7C25760A3049F359A2DAE508E140ED41E0BD`.
- `docs/plan/bugs/B-ADV-0011-fallo-transitorio-del-arnes-para-el-bucle.md`: `81979C6D0D4CED7E13668C3FCD84BADFA00C84FC1A5B5892907BB16F020B0CC7`.
