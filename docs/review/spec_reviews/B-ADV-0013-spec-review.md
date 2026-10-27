# Revisión de especificación — B-ADV-0013

**Veredicto: RECHAZADO**

Fecha: 2026-10-27. Revisor: Hades. Modo orquestado.

## Alcance

Solo los tres escenarios nuevos `@B-ADV-0013` de `tests/features/uso_sin_rutas.feature` y el contrato/triaje de `docs/plan/bugs/B-ADV-0013-pasos-de-analisis-sin-escalada.md`. Se aplican Hades y `/review-spec` de la instalación 0.6.1, ignorando el modelo del frontmatter. Los escenarios anteriores solo se contrastan con el diff para comprobar su conservación. El cambio de regla de parada está expresamente autorizado y no constituye un hallazgo.

## Comprobaciones obligatorias

| Comprobación | Resultado | Motivo |
| --- | --- | --- |
| No regresión | ✅ | El diff añade tres escenarios y no altera los existentes. |
| Coherencia | ✅ | La escalada, el bloqueo local y la parada global concuerdan con el contrato autorizado. Las omisiones de cobertura se detallan abajo. |
| Trazabilidad | ✅ | Los tres escenarios remiten a `@B-ADV-0013` y a comportamientos del bug. No incorporan etiquetas `@CA-*`. |
| Delta real | ✅ | Extienden la recuperación a pasos de análisis y distinguen su alcance local o global, sin duplicar los escenarios de desarrollo existentes. |

## Puntuaciones

| Criterio | Nota | Motivo |
| --- | --- | --- |
| Claridad | 8/10 | Se distinguen los desenlaces, pero faltan perfiles concretos y configuración explícita en los casos de agotamiento. |
| Completitud | 6/10 | Faltan garantías de orden, recuperación mediante reservas y ciclo de vida de la cadena por paso/argumento. |
| Testeabilidad | 7/10 | Los estados finales son observables; la ejecución efectiva de la cadena queda mayoritariamente en el antecedente del agotamiento. |
| Estructura | 9/10 | Amplía el archivo funcional existente. |

**Media: 7,5/10.** Dos hallazgos de severidad alta impiden aprobar.

## Hallazgos

### H-01 — 🟠 ALTA — La cadena de recuperación no queda exigida como resultado observable

**Para:** especificador. **Destino:** resolver.

**Evidencia:** el primer escenario solo exige pasar de base a escalada. Los otros dos sitúan el agotamiento de niveles superiores, escalada y reservas en el `Cuando`; no exigen observar su ejecución en el orden contractual. «Sin duplicarlos» tampoco define perfiles efectivos repetidos con los que comprobar la deduplicación.

**Impacto:** una recuperación que omita niveles o reservas, los pruebe en otro orden o repita el mismo perfil efectivo puede satisfacer los desenlaces descritos. La ruta de éxito con una reserva tampoco queda especificada, aunque forma parte del comportamiento esperado del bug.

**Corrección requerida:** concretar una configuración con perfiles distinguibles, un duplicado efectivo y el límite de reintentos; exigir como resultado la secuencia de ejecuciones e intentos, en orden niveles superiores → escalada → reservas y sin repetir perfiles efectivos. Incluir un caso en que una reserva permita completar el paso y continuar sin bloqueo ni parada. Puede hacerse con un esquema compacto, sin imponer detalles internos de implementación.

### H-02 — 🟠 ALTA — Falta cobertura del aislamiento y del ciclo de vida de la recuperación

**Para:** especificador. **Destino:** resolver.

**Evidencia:** «Decisiones sin preguntar» exige que la cadena pertenezca al par paso/argumento, se reinicie al avanzar y se conserve en la recarga cooperativa. Ninguno de los tres escenarios describe esos cambios de contexto ni sus efectos.

**Impacto:** los escenarios aceptarían que una tarea heredase perfiles agotados de otra, que una recarga perdiese la recuperación pendiente o que el progreso dejase agotamientos antiguos activos. Esto puede causar bloqueos prematuros o reintentos reiterados y frustrar la continuidad autónoma que persigue el bug.

**Corrección requerida:** añadir ejemplos con dos argumentos del mismo paso y con pasos distintos, progreso y recarga cooperativa. Expresar mediante las siguientes ejecuciones observables que cada par conserva su recuperación independiente, que avanzar reinicia la cadena correspondiente y que recargar mantiene el punto pendiente sin volver al perfil base agotado.

### H-03 — 🟡 MEDIA — Los casos de agotamiento no fijan suficientemente su contexto

**Para:** especificador. **Destino:** resolver.

**Evidencia:** el segundo escenario usa «especificar o revisar-tarea», no declara una tarea independiente en los antecedentes y fija dos intentos sin indicar la configuración. El tercero tampoco declara el límite. El contrato establece que cada perfil dispone de `--reintentos` intentos.

**Impacto:** queda abierta la selección del paso que se verifica y la procedencia del límite, y la continuidad se afirma sobre una tarea cuya elegibilidad no se establece.

**Corrección requerida:** parametrizar `especificar` y `revisar-tarea`, declarar la tarea independiente elegible y fijar `--reintentos=2` en los ejemplos de agotamiento. Identificar los perfiles esperados en el diagnóstico con los mismos valores usados en la configuración.

## Evidencia y límites

Revisión por lectura del contrato, del triaje y de los escenarios, con contraste del diff respecto a HEAD. El triaje prevé verificación del bucle simulado y de sus contratos colindantes; no se solicita ampliar a la suite completa. No se revisan código, diseño ni pruebas de implementación, ni se ejecutan pruebas. Los hallazgos requieren cambios de especificación, no concluyen defectos en una implementación.

Solo se escribe este informe en el árbol de trabajo. No se modifica la instalación ni se crean commits.
