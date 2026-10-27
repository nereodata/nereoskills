# Revisión de especificación — B-ADV-0013

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Modo orquestado. **Media: 9/10. Sin hallazgos pendientes.**

## Alcance

Reevaluación del delta sin commit respecto a HEAD `811cca063fc8808d685b776ce9a97fa5acdb38ea`: nuevos escenarios `@B-ADV-0013` de `tests/features/uso_sin_rutas.feature` y contrato, configuración común, DEC y triaje de `docs/plan/bugs/B-ADV-0013-pasos-de-analisis-sin-escalada.md`. Contraste con H-01/H-02/H-03 del informe anterior.

Se aplican Hades y `/review-spec` de la instalación 0.6.1, ignorando el modelo del frontmatter. Los escenarios previos de release solo se contrastan con el diff para comprobar su conservación. El cambio del contrato de parada está expresamente autorizado en el bug. No se revisan diseño, implementación ni tests ejecutables; no se recupera la rama WIP.

## Comprobaciones obligatorias

| Comprobación | Resultado | Motivo |
| --- | --- | --- |
| No regresión | ✅ | El delta del `.feature` es aditivo y conserva intactos los escenarios anteriores. |
| Coherencia | ✅ | Los resultados concuerdan con el contrato autorizado y DEC-ESP-13-01 a DEC-ESP-13-05: cadena finita por par, bloqueo local con continuidad y parada global tras agotamiento. Se conserva el aislamiento declarado de B-ADV-0012. |
| Trazabilidad | ✅ | Los escenarios llevan `@B-ADV-0013` y verifican comportamientos del bug y sus decisiones explícitas. No se incorporan etiquetas `@CA-*`. |
| Delta real | ✅ | Se especifica la recuperación de los siete pasos de análisis, sus desenlaces y el ciclo de vida de sus recuperaciones. Éxito, agotamiento e intercalado discriminan comportamientos distintos. |

## Puntuaciones

| Criterio | Nota | Motivo |
| --- | --- | --- |
| Claridad | 9/10 | La configuración común fija perfiles efectivos, duplicado, límite y condiciones del arnés; los esquemas identifican cada paso y argumento. |
| Completitud | 9/10 | Cubre éxito por escalada y reserva, agotamiento de los siete pasos, continuidad local, aislamiento por paso y argumento, reinicio por progreso y recarga con contadores parciales. El contrato delimita alternativas ausentes y excluye fallos operacionales y cuota. |
| Testeabilidad | 9/10 | Secuencias exactas, intentos, sesiones, estados, diagnósticos y siguientes ejecuciones distinguen omisiones, repeticiones, bloqueos prematuros y pérdida de recuperación mediante arneses simulados. |
| Estructura | 9/10 | Amplía el archivo de la funcionalidad existente; los esquemas agrupan variaciones y remiten a una configuración común explícita en el bug. |

**Media: 9/10 (> 8). Sin hallazgos críticos ni altos.**

## Reevaluación de hallazgos anteriores

### H-01 — ALTA — Resuelto

**Para:** especificador. **Destino:** resolver. **Estado vigente:** resuelto; sin acción pendiente.

La configuración distingue cuatro perfiles efectivos y declara una reserva idéntica al nivel superior. Los resultados de éxito y agotamiento exigen el orden inicial → nivel superior → escalada → reserva restante, con dos ejecuciones sin progreso por perfil y sin repetir la reserva duplicada. Cada cambio de perfil exige una sesión nueva.

El esquema de recuperación incluye éxito en `claude/escalado-demo/high` y en `agy/reserva-demo/medium`: los perfiles anteriores consumen sus dos intentos, el exitoso ejecuta una vez y no se prueban los posteriores. Se exige continuar sin bloqueo ni parada por falta de progreso. Quedan observables el orden, la deduplicación, los intentos y el éxito por reserva que faltaban en la revisión anterior.

### H-02 — ALTA — Resuelto

**Para:** especificador. **Destino:** resolver. **Estado vigente:** resuelto; sin acción pendiente.

El esquema de intercalado distingue dos argumentos de `especificar` y dos pasos para el mismo argumento. El otro par empieza en base mientras el primero conserva su segundo intento superior; al volver al otro par se conserva también su contador parcial. Un contador o perfil compartido no satisface esas secuencias.

El escenario de progreso exige que solo el par que avanza recupere sus dos intentos iniciales y después pase al superior, mientras el segundo par conserva el superior pendiente. El escenario de recarga exige que dos pares mantengan tanto su perfil como sus intentos parciales: segundo intento superior para uno y segundo intento base para el otro, con sus transiciones posteriores. Reiniciar al intercalar, reiniciar ambos al avanzar o conceder intentos por recarga incumple resultados explícitos.

### H-03 — MEDIA — Resuelto

**Para:** especificador. **Destino:** resolver. **Estado vigente:** resuelto; sin acción pendiente.

El agotamiento local parametriza `especificar` y `revisar-tarea`, declara una tarea independiente `planned` elegible y otra dependiente. Exige bloquear solo el ID agotado, completar la independiente y no ejecutar ni modificar la dependiente antes de informar del bloqueo de versión.

Todos los casos fijan la configuración común con `--reintentos=2`. El agotamiento global parametriza los otros cinco pasos con sus argumentos, exige la cadena completa y un diagnóstico con perfiles e intentos, sin cambios de estado de tareas. El local exige esos mismos datos en tarea, revisión de versión y avisos de consola y Telegram simulado. Desaparecen la alternativa ambigua entre pasos y el límite implícito.

## Hallazgos nuevos y pendientes

Ninguno. H-01, H-02 y H-03 quedan resueltos en esta revisión documental. No se proponen derivaciones ni cambios de estados del backlog.

## Evidencia y límites

Revisión por lectura del delta respecto a HEAD, del contrato y del reporte anterior. Se reutiliza la verificación documental verde indicada para este árbol: `adevv orquestar --verificar "git diff --check"`, registrada en `orquestar_evidencias.jsonl` el 2026-10-27 a las 09:16:25, código 0, árbol `20627fb10835bb39170ddc0653bd3534e87c3225`. Esta evidencia cubre el chequeo documental previo al informe; el juicio sobre el comportamiento especificado procede de la lectura.

El triaje separa esta fase documental del desarrollo posterior y reserva para este último las verificaciones del bucle simulado y de recarga. No hay delta de capas ejecutables que requiera esas pruebas en este paso. No se reutiliza el rojo de WIP como evidencia del árbol actual ni se ejecutan suite completa, pruebas funcionales o proveedores reales. Los perfiles son ficticios y los arneses y Telegram están simulados.

La aprobación corresponde exclusivamente a la especificación; no certifica una implementación. Solo se escribe este informe en el árbol de trabajo, sin modificar estados, la copia instalada ni crear commits.
