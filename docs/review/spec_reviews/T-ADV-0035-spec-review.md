# Revisión de especificación · T-ADV-0035

**Veredicto: APROBADO**

Fecha: 2026-11-12. Modo orquestado. Segunda revisión del mismo objetivo de subfase A. Rama: `release/v1.2`.
Base de calidad: `8efac2293421d1190f2fb57724aa6e932d964427`. Rechazo anterior y WIP: `6923ca6`.

## Alcance

Reevaluación de S1 y S2 del rechazo anterior y del delta corregido de `skills/orquestar/features/orquestacion.feature:739-788`, contrastado con CA-M-1..6, el triaje y las decisiones de especificación de la ficha, los contratos previos de canales y proveedores y `docs/requirements/work_plan.md §6`.

Se han consultado el diff respecto a `6923ca6` y el diff respecto a la base de calidad: este último añade 51 líneas sin eliminar ni modificar escenarios anteriores a T-ADV-0035. Se revisa únicamente especificación; no se juzgan diseño, código ni pruebas de implementación y no se ejecuta la verificación de producción. La aprobación corresponde a A, no acredita las entregas B–F.

## Reevaluación del rechazo anterior

| Hallazgo | Estado | Evidencia de la corrección |
| --- | --- | --- |
| S1 · ALTA · Observación por canales existentes | Resuelto | La aclaración con proveedor simulado exige que `--estado` y `/estado` identifiquen responsable y siguiente paso, y ambas consultas de preguntas muestren la cola vacía. El recorrido humano ahora produce la pregunta como resultado: comprueba elección concreta, tarea y referencia antes de responder; después de incorporar la respuesta y reiniciar conserva una sola entrada con referencia y respuesta originales y elimina la espera humana. La matriz de esperas y el caso de suscripción observan estado, revisión pendiente, B ejecutable y ausencia de pregunta en CLI y Telegram. La ficha referencia las regresiones reutilizadas de recepción y transporte. |
| S2 · MEDIA · Clase de fallo de acceso y reservas | Resuelto | Se elimina la fila ambigua «acceso temporal denegado tras reservas». El escenario separado fija Claude principal, una única reserva Claude de otro modelo autorizada y elegible, sin perfil estricto, y el código 1 con el diagnóstico literal de suscripción deshabilitada en ambos intentos. Exige espera recuperable, continuidad de B y recepción del dictamen al recuperar acceso. No extiende las reservas a errores genéricos de autenticación o red ni altera el contrato de perfil estricto. |

La corrección permanece dentro de lo señalado. El escenario separado de suscripción añade la observación del despacho independiente y de los canales al contrato previo de agotamiento de reservas; no es una duplicación sin comportamiento nuevo.

## Obligatorias

| Comprobación | Resultado |
| --- | --- |
| No regresión | ✅ El delta respecto a la base es exclusivamente aditivo; los escenarios previos están intactos. |
| Coherencia | ✅ La aclaración conserva los destinos técnicos existentes. El caso de suscripción respeta las reservas autorizadas y mantiene diferenciados los contratos previos de perfil estricto y errores genéricos. Las consultas existentes observan el resultado sin anticipar las explicaciones nuevas de T-ADV-0040. |
| Trazabilidad | ✅ Las etiquetas CA-M-1..6 existen en la ficha y corresponden a las conductas descritas. |
| Delta real | ✅ Especifica asignación tras aclaración, continuidad de identidad y respuesta, ausencia de falso avance y despacho independiente durante esperas o pausas. |

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | ---: | --- |
| Claridad | 9 | Destinos, elección humana y clase de fallo técnico quedan determinados. |
| Completitud | 9 | Cubre los tres recorridos y separa cuota, recurso externo, ausencia de ejecutables y suscripción deshabilitada; reutiliza los contratos previos de canales y reservas. |
| Testeabilidad | 9 | Exige resultados por CLI y Telegram, referencia y respuesta estables, ausencia de avance, despacho de B y recuperación de la revisión pendiente. |
| Estructura | 9 | El delta reside en la feature de orquestación existente. |

**Media: 9/10. Sin hallazgos críticos ni altos pendientes.**

## Cobertura y triaje

| Criterio | Evidencia y límite de esta revisión |
| --- | --- |
| CA-M-1 | La aclaración devuelve el conflicto al especificador o a Artemisa con mandato y salida; el caso de suscripción agota principal y única reserva autorizada y conserva una espera técnica recuperable. El enrutado de dictámenes y la reserva que sí revisa mantienen sus contratos previos. |
| CA-M-2 | La elección norte/sur solo corresponde al usuario. Ambos canales muestran pregunta concreta, tarea y referencia antes de la respuesta, y conservan una sola entrada y su respuesta tras reiniciar y reaparecer el impedimento, con un único aviso. |
| CA-M-3 | Reformular el diagnóstico no cambia estado ni contador de avance. Se ejecuta B, C permanece pendiente y recuperar la condición retoma la revisión de A. |
| CA-M-4 | Proveedores simulados cubren conflicto de especificación, decisión humana y fallo técnico. Los resultados especifican estado, cola y destino por las consultas existentes de CLI y Telegram. La ficha identifica las regresiones reutilizadas para recepción y transporte. |
| CA-M-5 | La aclaración confirma responsable, mandato y condición de salida; las pausas y esperas conservan impedimento y condición verificable al relanzar. La aplicación en un único punto de la decisión técnica y del resultado de T-ADV-0039 es una propiedad estructural que debe acreditarse en B/C2 y revisarse en D, no mediante inspección de código en A. |
| CA-M-6 | La matriz separa cuota del rol, recurso externo y ausencia de todo ejecutable autorizado. Cada caso conserva A, despacha B independiente con capacidad y mantiene C pendiente. El caso de suscripción añade la misma continuidad durante el agotamiento de las vías de revisión. |

A queda cubierta por los escenarios corregidos. Los recorridos ejecutables con proveedores simulados corresponden a C1; integración y selección a B/C2, revisión de producción a D y documentación y cierre a E/F. Esta revisión no adelanta su validación ni exige que el módulo futuro `tests.test_decision_item` exista ya en A.

## Hallazgos nuevos y continuación

Sin hallazgos nuevos. S1 y S2 quedan resueltos; no hay destinos `resolver`, `registrar`, `descartar` ni intervención humana que aplicar. El orquestador puede continuar desde la aprobación de la especificación de la subfase A. No se han cambiado escenarios, ficha, estados ni implementación durante esta revisión.

## Limitación de acceso a instrucciones

El entorno denegó la lectura de `C:\Users\Iván Moreno\.adevv\versions\1.2.0.dev20261112+7b6f133\agents\hades.md` y de `skills/review-spec/SKILL.md` de esa instalación. Se aplicaron las instrucciones accesibles de `agents/hades.md`, `skills/review-spec/SKILL.md` y el enrutado de `skills/orquestar/SKILL.md` del repositorio, ignorando el modelo del frontmatter. No se afirma haber leído ni comprobado la equivalencia exacta de la copia instalada. El repositorio, el rechazo previo y los dos deltas sí fueron accesibles.
