# Revisión de pruebas — B-ADV-0007

**Veredicto: APROBADO**
**Revisor:** Hades · `/review-test` · modo orquestado
**Fecha:** 2026-10-26

## Alcance y criterio

Revisado el delta completo de `tests/test_cli_commands.py`: incorporación de `TestCliEnvironment.test_telegram_environment_is_isolated_and_restored`. Se ha leído el archivo para entender la preparación y limpieza del fixture, sin revisar implementación de producto ni exigir que la regresión pase antes de corregirlo.

Contrato tomado del triaje de B-ADV-0007 y de `docs/review/test_reviews/B-ADV-0007-red.md`: aislar las dos variables Telegram en el fixture CLI, también para sus subprocesos, y restaurarlas mediante cleanup. A/B SKIP: contrato existente, sin nuevo requisito ni diseño. El alcance `tests/` está autorizado por HC-01 para v1.0.

## Puntuaciones

| Criterio | Puntuación | Evaluación |
| --- | --- | --- |
| Cobertura | 9/10 | Comprueba ambas variables ausentes, token solo, IDs solos y ambas presentes; observa fixture, hijo Python y restauración. Cubre el contrato del triaje sin necesitar un nuevo `.feature`. |
| Aserciones | 9/10 | Exige ausencia real de las claves en el proceso y su hijo, y compara los valores finales con el estado previo a `setUp`. La restauración se comprueba antes de que el parche exterior restaure el entorno, por lo que no se cumple por construcción. |
| Rojo correcto | 10/10 | Evidencia registrada: un test, cuatro subcasos, tres fallos en la aserción de aislamiento con variables presentes; el caso sin variables pasa. El fallo discrimina la omisión del aislamiento, sin depender de Telegram ni del motor. |
| Estabilidad | 9/10 | Cada subcaso prepara explícitamente las dos claves con valores ficticios y contiene las mutaciones mediante `patch.dict`. El hijo usa `sys.executable`, termina de forma síncrona y tiene timeout. La limpieza se intenta mediante bloques `finally`, incluido `doCleanups` aunque falle `tearDown`. |

**Media: 9,25/10.** Sin hallazgos críticos ni de severidad alta.

## Evidencia utilizada

- `orquestar_evidencias.jsonl`: ejecución mediante `--verificar` de `python -m unittest discover -s tests -p test_cli_commands.py -k telegram_environment`, árbol `c532bf072fcab59a8439c447a0248622a4bfdcd7`, código 1. El detalle de los tres fallos consta en el reporte de rojo.
- Sobre el árbol revisado `0642767008e688e488d18c80794a5d070c045871`, constan en verde mediante `--verificar` `python -m py_compile tests/test_cli_commands.py` y `git diff --check` (código 0 en ambos).
- Lint y tipado no configurados; dependencias sin cambios según el triaje.

No se han repetido verificaciones ni ejecutado pruebas, suite completa, motor o reproducciones con credenciales reales. En el rojo, la aserción del fixture interrumpe los tres subcasos con variables presentes antes de alcanzar el hijo y la comprobación final; esto es coherente con la fase previa a la corrección y no acredita todavía su ejecución en verde.

## Hallazgos e impedimentos

Sin hallazgos; no procede asignar `para` ni `destino`. Sin impedimentos reales para esta revisión.

La aprobación inicial evaluó la calidad de la regresión antes de corregir el fixture. La siguiente ampliación completa la revisión del estado final.

## Ampliación final — fixture corregido

**Veredicto: APROBADO. Media mantenida: 9,25/10.** Revisión en modo orquestado del delta posterior a la aprobación en rojo: cinco líneas añadidas al principio de `TestCliCommands.setUp`. Las aserciones de la regresión permanecen sin cambios; se mantiene su revisión anterior sin repetirla.

`patch.dict(os.environ)` captura el entorno previo antes de las mutaciones del fixture. Tras iniciar el parche se registra inmediatamente `isolated_environment.stop` con `addCleanup`, antes de eliminar ambas claves Telegram y antes de crear temporales o preparar la CLI. No se sustituyen los valores por cadenas vacías: las claves quedan ausentes. El resto del entorno sigue disponible durante la prueba.

El cleanup restaura el estado anterior completo, incluidos los valores de otras variables que el fixture modifica o elimina. En el ciclo de `unittest` se ejecuta después de `tearDown`, también ante fallos del test, de `tearDown` o del resto de `setUp`; no depende de alcanzar una sentencia de restauración al final del test. La regresión manual llama a `doCleanups` mediante `finally` y comprueba la restauración de Telegram antes de salir de su parche exterior.

Los subprocesos lanzados durante el fixture heredan el entorno sin ambas claves; las copias de `os.environ` preparadas dentro de las pruebas también parten de ese estado aislado. La restauración posterior en el padre no modifica el entorno ya heredado por los hijos. La regresión observa esa herencia con un hijo Python inocuo y valores ficticios en las cuatro combinaciones previstas, sin necesitar arrancar un gateway para demostrarla.

### Evidencia final

En `orquestar_evidencias.jsonl`, sobre el árbol `168aedb935d090c246706b279a44d9f50bd3ca83`, constan mediante `--verificar`, todos con código 0:

- `python -m unittest discover -s tests -p test_cli_commands.py`: 10 tests en 36.724 s según la salida aportada; el registro JSONL redondea a 37 s. Cubre todos los consumidores del fixture y alcanza las comprobaciones del hijo y la restauración también en los subcasos con variables presentes.
- `python -m py_compile tests/test_cli_commands.py`.
- `git diff --check`.

Se conserva la evidencia roja anterior como demostración de discriminación. No se han repetido comandos ni ejecutado suite completa, gateways o pruebas con credenciales reales. Lint y tipado no configurados; sin cambios de dependencias.

**Hallazgos nuevos: ninguno. Impedimentos reales: ninguno.** No procede asignar `para` ni `destino` al no existir hallazgos. La revisión de pruebas cubre ahora el delta completo final, incluida su preparación; no quedan verificaciones del triaje pendientes para este reporte.
