# T-ADV-0024 · Revisión de pruebas · Segunda ronda

Fecha: 2026-10-27. Revisor: Hades, aplicando `/review-test`.

**Veredicto vigente: APROBADO. Media: 9,25/10.** Sin hallazgos pendientes.

## Alcance y evidencia

- Base de calidad: `5c4ffee9555a2efa5bdd2884a16073c396924f64`. Único artefacto revisado: `skills/telegram_gateway/test_autoarranque_windows.py`, nuevo respecto a la base. Reevaluación de H-01..H-04 y de las correcciones por posibles regresiones, frente a los escenarios `@T-ADV-0024`, sus DEC-ESP y su triaje. No se revisaron producción, diseño ni otros escenarios.
- Evidencia reutilizada de `orquestar_evidencias.jsonl`, árbol `b39d74934237cf7f7a09400c964f149e7df83cc9`: ejecución focalizada roja a las 00:43:13, compilación del test verde a las 00:43:14 y `git diff --check` verde a las 00:43:15, mediante `--verificar`. Sin lint ni tipado configurados.
- `.git/T-ADV-0024-red.log` actualizado: nueve pruebas, nueve errores `SystemExit: 2` por opción `--autoarranque on` todavía desconocida en argparse. El fallo corresponde a la funcionalidad ausente; no a importación, sintaxis o fixtures. La ejecución se detiene antes del recorrido nativo.
- Esta aprobación evalúa C1: calidad de las pruebas en rojo y de su preparación. No acredita un verde nativo; ese resultado corresponde a C2 tras implementar la funcionalidad. No se exige adelantarlo como condición de aprobación de C1.
- Revisión por lectura y evidencia existente. No se ejecutaron pruebas ni suite completa; no se modificaron pruebas o implementación.

## Puntuaciones

| Criterio | Nota | Fundamento |
| --- | ---: | --- |
| Cobertura | 9 | Representa registro idempotente, independencia de proyectos, consulta/baja, dos variantes válidas, cuatro inválidas y rechazo fuera de Windows. Los estados AUSENTE respetan el contrato. |
| Aserciones | 9 | Comprueba cardinalidad de invocaciones, argumentos, raíz efectiva, flags del hijo, procesos, escucha, PID, diagnósticos y salida aislada de estado. |
| Rojo correcto | 10 | Los nueve errores se deben a la ausencia de la opción pública en argparse. |
| Estabilidad | 9 | Temporales y entorno restaurable, rutas Unicode transmitidas por entorno, lanzador ASCII bajo página 850, observación acumulativa y ejecución síncrona sin esperas arbitrarias. |

## Reevaluación de hallazgos

| Hallazgo | Estado | Evidencia de la corrección | Destino | Para |
| --- | --- | --- | --- | --- |
| H-01 · ALTA · Página de códigos del lanzador | **resuelto** | El `.cmd` se escribe en ASCII, establece `chcp 850` y recibe las rutas mediante `ADEVV_TEST_PYTHON` y `ADEVV_TEST_FIXTURE`, expandidas entre comillas. Ya no contiene las rutas Unicode como bytes literales UTF-8. El recorrido conserva la ruta acentuada; su verde nativo se comprobará en C2. | `resolver`, completado en pruebas | `desarrollador` |
| H-02 · ALTA · Invocaciones repetidas invisibles | **resuelto** | El lanzador añade cada observación a JSONL. El helper común exige exactamente un registro en todos los arranques con proyecto existente y cero para el eliminado. Dos invocaciones síncronas ya no pueden ocultarse sobrescribiendo el último resultado. Se conserva la comprobación de ejecución con espera en la entrada y el retorno del intérprete nativo. | `resolver`, completado en pruebas | `desarrollador` |
| H-03 · MEDIA · Salida de estado registrado | **resuelto** | Se limpia la captura antes de `estado` y se afirman explícitamente `autoarranque registrado` y la raíz seleccionada, además de conservar la comparación de contenido y fecha de las entradas. | `resolver`, completado en pruebas | `desarrollador` |
| H-04 · MEDIA · AUSENTE preparado como vacío | **resuelto** | Las variables TELEGRAM ausentes se eliminan dentro del entorno restaurable. El `.env` omite claves cuyo valor es `None`; el entorno del proceso nativo omite las variables no suministradas. Se conservan los valores ficticios y la restauración ante fallos. | `resolver`, completado en pruebas | `desarrollador` |

## Hallazgos nuevos

Ninguno. Las correcciones mantienen Inicio temporal, cscript/PowerShell reales y lanzador ficticio que alcanza main con Popen y escucha mockeados, sin introducir red ni uso del Inicio real en los fixtures. No se necesita intervención del especificador ni un recurso humano.
