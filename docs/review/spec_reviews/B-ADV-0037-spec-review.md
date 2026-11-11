# B-ADV-0037 — Revisión de especificación

- **Revisor:** Hades.
- **Fecha:** 2026-11-11.
- **Modo:** orquestado, revisión estática del delta.
- **Veredicto: APROBADO.**
- **Informe:** docs/review/spec_reviews/B-ADV-0037-spec-review.md.

## Alcance y evidencia

Se revisan exclusivamente los siete bloques de escenarios añadidos con
`@B-ADV-0037` en `tests/features/publicacion.feature`, frente a CA1–5,
las decisiones de especificación documentadas y los hallazgos anteriores
H1, H2 y H3.

Los cinco escenarios originales se consideran aprobados y quedan fuera de
reevaluación. En el material suministrado se conservan íntegros. Los tres
escenarios del WIP e44c13d fueron un borrador rechazado, ausente de esta
rama; no se consideran una base aprobada que deba restaurarse.

La revisión utiliza exclusivamente el material completo proporcionado.
El acceso al filesystem falló con
`registered Core launch requires an installed app`, también mediante la
alternativa de acceso. No fue posible leer el perfil instalado, contrastar
el árbol con Git ni guardar este informe. Las conclusiones sobre
conservación de escenarios y documentos existentes quedan limitadas a
la evidencia aportada.

No se revisan diseño, producción ni implementación de pruebas. No se
ejecutan pruebas, no se hacen commits y no se cambian estados del backlog.

## Obligatorias

| Regla | Resultado | Motivo |
|---|---|---|
| No regresión | ✅ | El delta suministrado conserva los cinco escenarios originales y añade los casos de B-ADV-0037. El borrador rechazado del WIP no constituye una base aprobada. |
| Coherencia | ✅ | Se exige revisión válida para cerrar, se admite N/A justificado por ausencia de código y se separa la identidad operativa completa de versión de la agrupación histórica de métricas. |
| Trazabilidad | ✅ | Los nuevos escenarios llevan `@B-ADV-0037` y corresponden a los criterios del bug. No introducen etiquetas `@CA-*` inexistentes. CA3 se acredita mediante los informes existentes declarados en el expediente. |
| Delta real | ✅ | Los casos añaden el veto por revisión pendiente o rechazada, su diagnóstico y recuperación, la excepción N/A y la separación operativa entre parches. No duplican el comportamiento de los cinco escenarios anteriores. |

## Puntuaciones

| Dimensión | Puntuación | Motivo |
|---|---:|---|
| Claridad | 9/10 | Las entradas, estados de revisión, actores e identificadores están concretados; las decisiones documentadas delimitan el alcance. |
| Completitud | 9/10 | Cubre ausencia y rechazo, tareas y bugs, tres entradas de cierre, varios pendientes, indisponibilidad, recuperación, N/A y límites de identidad de versión. |
| Testeabilidad | 9/10 | Exige diagnósticos identificables, estados consultables, resultados opuestos para N/A y ausencia observable de cierre, etiquetas y publicación. |
| Estructura | 9/10 | El delta permanece en el feature funcional de publicación y expresa comportamiento sin imponer almacenamiento ni algoritmos internos. |
| **Media** | **9/10** | Supera 8 y no se identifican hallazgos críticos ni altos. |

## Reevaluación de H1/H2/H3

| Hallazgo anterior | Severidad anterior | Para | Destino para menores | Resultado |
|---|---|---|---|---|
| H1 — Alternativas de bloqueo sin cobertura discriminante | 🟠 ALTA | especificador | No aplica | RESUELTO |
| H2 — Estado pendiente presupuesto, sin provocar indisponibilidad | 🟠 ALTA | especificador | No aplica | RESUELTO |
| H3 — Excepción N/A sin ejercicio propio | 🟡 MEDIA | especificador | resolver — cumplido | RESUELTO |

### H1 — Resuelto

La matriz contiene los doce ejemplos de ausencia/RECHAZADO × tarea/bug
maestro completado × preflight local/cierre Telegram/publicación por API.
Cada fila presupone satisfechos los demás requisitos, lo que permite
atribuir el rechazo a la revisión formal.

El escenario adicional exige enumerar simultáneamente el ID sin informe y
el ID con informe rechazado, excluyendo al aprobado. Se mantienen el
diagnóstico, la vía de revisión y la prohibición de declarar el cierre,
crear etiquetas o publicar main.

### H2 — Resuelto

El caso de indisponibilidad provoca un intento de revisión con Hades sin
cuota y pruebas verdes. Exige consultar el estado y validar el cierre,
observando ID, causa concreta e instrucciones de recuperación y
reanudación. Las pruebas verdes no sustituyen la aprobación formal.

El caso de recuperación exige reanudar la revisión, obtener el informe
APROBADO y volver a ejecutar el preflight. También establece que obtener
el informe no cierra ni publica automáticamente la versión.

### H3 — Resuelto

El esquema N/A contiene dos ejemplos propios: justificación explícita de
ausencia de código y justificación vacía. Sus resultados son opuestos:
dejar de bloquear o mantener el bloqueo. Se elimina así la condición
inejercitada del borrador anterior.

## Cobertura de CA1–5

| Criterio | Evaluación |
|---|---|
| CA1 | Cubierto por la matriz de bloqueo y el diagnóstico de todos los pendientes, con prohibición explícita de etiquetar o declarar cerrada la versión. |
| CA2 | Cubierto por el intento con Hades sin cuota, el estado consultable y el diagnóstico con ID, motivo y forma de reanudar. |
| CA3 | Acreditado según el expediente aportado por los informes formales RECHAZADO de B-ADV-0032 y B-ADV-0033, trazados durante el saneamiento de v1.1.2. No se han leído independientemente esos archivos. Obtener revisión no equivale a obtener aprobación ni autoriza cerrar con rechazo pendiente. |
| CA4 | Cubierto por la selección del trabajo de v1.1.2 sin recuperar la revisión de v1.1.1 y por su exclusión del impedimento de cierre de ese parche. Se especifica además la equivalencia v1.1/v1.1.0. |
| CA5 | La especificación contiene casos discriminantes de rechazo, recuperación y aislamiento entre parches. La existencia y calidad de su implementación como regresiones corresponde a una revisión posterior de pruebas. |

## Resolución

APROBADO el delta de especificación suministrado. H1, H2 y H3 quedan
resueltos; no se identifican nuevos hallazgos.

El veredicto autoriza continuar el ciclo desde la especificación. No
acredita diseño, implementación, pruebas ni cierre de versión, y no
modifica los veredictos ni el trabajo pendiente de B-ADV-0032 y B-ADV-0033.
