# Revisión de pruebas — B-ADV-0006

**Veredicto: APROBADO** — Reevaluación del delta completo de pruebas y de las cinco regresiones añadidas tras QA.

## Alcance y evidencia

Se aplica Hades y `/review-test` de la instalación 0.6.0. Revisado el delta completo de pruebas en `tests/test_orquestar.py`, incluidos fixtures, frente a los escenarios `@B-ADV-0006` aprobados y el triaje actualizado. La reevaluación se centra en las cinco regresiones añadidas por H1–H3 de QA. Los casos anteriores conservan su aprobación: las adiciones no invalidan sus aserciones ni su aislamiento. Se mantiene aceptada la sustitución explícita del test de parada inmediata: la petición cambia ese contrato.

Se reutilizan las evidencias, sin ejecutar comprobaciones:

- Rojo histórico `.git/B-ADV-0006-red.log`, ya examinado en la primera ronda: 9 pruebas, 1 fallo por no lanzar `bug-fix` y 8 errores por ausencia de captura de salida o del helper de recuperación. Acredita discriminación frente a la funcionalidad antigua, sin errores de sintaxis o fixtures; no se atribuye esa ejecución histórica a las aserciones añadidas después.
- Rojo de QA `.git/B-ADV-0006-hades-red.log`: 14 pruebas, 2 fallos y ningún error de fixtures o sintaxis. Las regresiones detectan el ID duplicado `B-DEM-0002` y un mensaje final de 10133 unidades UTF-16. Las otras tres regresiones protegen el cambio de rama ya implementado y no necesitan fallar por las correcciones de parser o aviso.
- La ejecución intermedia de `.git/B-ADV-0006-green.log` terminó con un fallo en la comparación de salida multilínea contra el Markdown indentado. No se contabiliza como verde. La corrección actual elimina exactamente las cuatro posiciones de indentación añadidas a cada línea y exige igualdad completa con la salida original; no sustituye la preservación por una comprobación parcial.
- `.git/B-ADV-0006-transport.log`: la prueba corregida del aviso largo pasa, 1 prueba, `OK`.
- `.git/B-ADV-0006-motor.log`: ejecución final ya completada, **70 pruebas, OK**. Consta en `orquestar_evidencias.jsonl` el comando `python -m unittest discover -s tests -p test_orquestar.py > .git/B-ADV-0006-motor.log 2>&1`, con código 0, sobre el árbol `0eb9722812373ec7da60513bca9aea4c0bec519a`.
- Sobre ese mismo árbol constan con código 0 la prueba limitada de transporte, `python -m py_compile tests/test_orquestar.py skills/orquestar/orquestar.py` y `git diff --check`. Se aceptan sin repetirlos. No hay linter ni tipado configurados para este delta.

No se ha leído producción ni revisado su corrección. No se han relanzado tests, compilación, comprobaciones ni suite completa. El verde se usa como evidencia de ejecución; el juicio sobre las aserciones se basa en su lectura.

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Cobertura | 9/10 | Se mantienen los casos aprobados y se añaden parser sin PyYAML, aviso largo y selección de rama PASO/PARAR con guardia de cambios pendientes. |
| Aserciones | 9/10 | Identidad y contadores reales; mensaje final con firma, ID, cola y límite UTF-16; preservación completa de salida; ramas y commits observables. |
| Rojo correcto | 9/10 | El rojo histórico discrimina la funcionalidad inicial y el rojo de QA reproduce dos defectos concretos. La corrección de formato conserva una igualdad completa de la evidencia. |
| Estabilidad | 9/10 | Repositorios temporales, ausencia de PyYAML forzada mediante mocks con restauración y transporte simulado. Sin esperas ni llamadas reales a servicios. |

**Media: 9/10.** Sin hallazgos críticos ni altos pendientes.

## Reevaluación de hallazgos anteriores

| Hallazgo | Estado | Evidencia | Para | Destino |
| --- | --- | --- | --- | --- |
| H1 — Orden del verde posterior al arreglo | **Resuelto** | `verify_suite` añade cada resultado a `events`; el ejecutor añade `bug-fix completado` después de completar el bug y guardar su revisión. La igualdad exacta exige `suite roja → bug-fix completado → suite verde → revisar-version`. Una verificación adelantada o una revisión antes del verde alteraría la secuencia y fallaría. Se mantiene la prueba de no ejecutar pasos al agotar intentos. | desarrollador | resolver — cerrado |
| H2 — Resultados persistidos en dificultad máxima | **Resuelto** | En cada recaída se comprueban `suite_intentos` 1/2/3, dificultad `dificil` y estado `planned` antes del umbral o `blocked` al tercero, además de la parada, el ID, la última salida y el destino humano. | desarrollador | resolver — cerrado |
| H3 — Conservación del bug de otro cierre | **Resuelto** | Se guardan los bytes del bug original y se comparan después de registrar otro comando y después de registrar otra versión. También se mantienen las aserciones de IDs distintos. | desarrollador | resolver — cerrado |

## Hallazgos nuevos

Ninguno. No se requiere intervención humana.

## Cobertura de las regresiones solicitadas por QA

Esta tabla evalúa las pruebas añadidas; no cierra los hallazgos de producción, cuya resolución corresponde a `/review-code`.

| Referencia de QA | Evaluación de las pruebas | Para | Destino |
| --- | --- | --- | --- |
| H1 — Identidad sin PyYAML | `test_escaped_command_reuses_id_without_pyyaml` fuerza `yaml_lite` y bloquea la importación de PyYAML. Usa un comando con comillas, espacios y barras invertidas; completa el bug entre recaídas, exige el mismo ID, contadores 1/2 y un único archivo. El resultado no está simulado. Cobertura satisfactoria. | desarrollador | resolver — cobertura incorporada |
| H2 — Aviso largo | `test_long_stop_output_fits_final_telegram_transport` llega al límite tras tres arreglos en `dificil`, usa 5000 caracteres no BMP y una última línea de error. Pasa por `parar` y `avisar`, simula únicamente configuración y envío de Telegram y mide el argumento final entregado a `enviar`, incluyendo prefijo y firma. Exige como máximo 4096 unidades UTF-16, ID, última línea y firma, además de reconstrucción exacta de la evidencia en disco quitando solo la indentación de Markdown. Cobertura satisfactoria. | desarrollador | resolver — cobertura incorporada |
| H3 — Rama seleccionada | Dos pruebas parten de `another` para estados de cierre PASO y PARAR. La suite y el ejecutor observan la rama real; se exige orden suite/bug-fix en la release, árbol limpio antes del agente, commit del bug en la release y rama original sin ese commit. La quinta regresión cubre ambos estados con árbol sucio: no verifica, no ejecuta, no registra y permanece en `another`. Cobertura satisfactoria. | desarrollador | resolver — cobertura incorporada |

Los estados de cierre se inyectan para aislar el camino bajo revisión; checkout, archivos y commits se observan en el repositorio temporal real. Las simulaciones no fijan por construcción esos resultados. Los hallazgos anteriores de `/review-test` H1–H3 siguen resueltos.
