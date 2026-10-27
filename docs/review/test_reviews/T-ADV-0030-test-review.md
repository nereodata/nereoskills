# Revisión de pruebas: T-ADV-0030

- **Revisor:** Hades. **Fecha:** 2026-10-27. **Modo:** orquestado. **Ronda:** 4.
- **Artefacto:** ampliación de `test_credenciales_incompletas_no_avisan_ni_arrancan` en `skills/telegram_gateway/test_gateway_fondo.py`, con su preparación y observadores como contexto. Se conserva la aprobación de la ronda 3 para el resto del delta.
- **Contrato:** escenarios `@T-ADV-0030` de `skills/orquestar/features/orquestacion.feature` y `skills/telegram_gateway/features/telegram_gateway.feature`; CA-M-1..4, DEC-ESP-01..04 y triaje de la tarea.
- **Aislamiento:** revisión de pruebas y evidencia, sin inspeccionar producción ni diseño.

## Veredicto: APROBADO

Media **9/10**, sin hallazgos vigentes. H-01..H-04 de pruebas siguen resueltos. El caso añadido acredita el contrato de diagnóstico que faltaba ante token ambiental sin destinatarios. No quedan pendientes asignados al desarrollador en esta revisión de pruebas; no se emite juicio sobre la corrección de producción H-01.

## Puntuaciones

| Criterio | Nota | Evidencia |
|---|---:|---|
| Cobertura | 9 | Se mantiene la cobertura aprobada y se añade token ambiental válido sin destinatarios efectivos, con diagnóstico de incompletas en las tres entradas. |
| Aserciones | 9 | Verifica token, destinatarios, origen, desempaquetado histórico, prefijo y firma; motivo literal; conteos por ejecución; escucha con usuario efectivo; ausencia de diagnóstico en permisos y ausencia de efectos en rechazos. |
| Rojo correcto | 9 | Se conserva la evidencia del rechazo ambiental. Por lectura, el caso nuevo falla si se devuelve solo avisos en lugar de credenciales incompletas; no se atribuye al nuevo caso una ejecución roja no aportada. |
| Estabilidad | 9 | Temporales independientes, credenciales ficticias, entorno restaurado con contextos, estado de deduplicación limpiado con addCleanup y fronteras de transporte/procesos/escucha simuladas según cada caso. Captura de salida compatible con reconfigure. |
| **Media** | **9** | |

## Reevaluación de hallazgos anteriores

| Hallazgo | Estado | Comprobación de la corrección |
|---|---|---|
| H-01 · Cobertura de fuentes y consumidores | **Resuelto** | La matriz distingue claves locales omitidas de vacías, elimina variables ambientales cuando corresponde y comprueba origen ninguno con IDs conservados. Avisos añade solo local. Autoarranque y permisos manuales cubren solo local, combinado y token local con IDs ambientales. Incompletas cubre las tres entradas, aviso y autoarranque. |
| H-02 · Observadores de efectos | **Resuelto** | Avisos observa cero run/Popen/escucha; autoarranque ambiental añade cero reservas a cero run/Popen/escucha. Rechazo manual e incompletas observan reserva, Popen y escucha; incompletas también envío y run. |
| H-03 · Ausencia de diagnóstico en permisos | **Resuelto** | Cada configuración local y cada modo captura su propia salida y exige ausencia del motivo ambiental. Se conservan motivo literal en rechazo, nota por ejecución, prefijo ProyectoDemo, firma y cleanup. |
| H-04 · Evidencia roja | **Resuelto** | El documento actualizado identifica base, prueba, preparación, doce variantes y trece fallos por aceptación del respaldo ambiental y creación de hijos simulada. |

## Cobertura y preparación de datos

### Delta de la ronda 4

Se añade la fila `(None, None, 'token-entorno-ficticio', None)` a la matriz de incompletas. La construcción omite las claves locales y escribe un `.env` vacío; el contexto fija token ambiental ficticio y mantiene los IDs ambientales en cadena vacía. Por tanto, prepara ausencia de destinatarios efectivos sin heredar IDs reales. Aunque el parámetro usa None, en este helper la variable ambiental de IDs queda definida vacía, no eliminada: ambas situaciones carecen de IDs utilizables bajo DEC-ESP-01.

La fila atraviesa aviso y autoarranque, y después las tres entradas CLI, --fondo y --gestionado. Se exige aviso falso, SystemExit con el diagnóstico de credenciales incompletas y cero llamadas a enviar, run, Popen, reservar y escuchar, además de ausencia de telegram.pid. Los dobles sustituyen las fronteras y no la resolución de credenciales ni la selección del diagnóstico. Así, una salida con el motivo solo avisos no satisface la aserción, aun cuando también termine sin efectos. Las comprobaciones acumuladas de cero llamadas detectan un efecto producido por cualquier fila.

La preparación usa contextos que restauran el entorno incluso ante fallo. No añade reloj, red ni procesos reales. El delta es una fila de datos sobre un caso ya aprobado y no requiere reabrir el resto de las pruebas. No se identifica ningún hallazgo nuevo.

### Cobertura conservada de la ronda 3

La resolución comprueba token e IDs por separado, con valores ficticios 111/222 y tokens locales/ambientales distintos. Incluye respaldo de campos ausentes o vacíos, prioridad local cuando ambas fuentes existen y ausencia de token sin perder destinatarios. Las aserciones esperadas son valores explícitos y comprueban también el desempaquetado histórico de dos valores.

Los avisos usan ProyectoDemo, evento version y texto Versión terminada. Cada variante exige exactamente un envío al usuario efectivo, prefijo exacto y firma de versión fijada; los observadores negativos impiden que el aviso pase inadvertidamente a escucha o lanzamiento.

El autoarranque ambiental mide cada ejecución del bucle por separado: exige una nota literal tras el inicio y mantiene ese conteo después de tres solicitudes adicionales. La siguiente ejecución debe volver a informar. El autoarranque local alcanza la frontera de lanzamiento con configuración efectiva y comprueba el proyecto y --fondo. Los permisos manuales verifican por separado la escucha simulada con token/usuario esperados en primer plano y gestionado, y Popen en fondo. Esta composición comprueba las fronteras sin ejecutar hijos reales.

El rechazo cruza cuatro configuraciones locales (ausentes, token ausente con IDs, token vacío y espacios) con las tres entradas. Exige SystemExit con el motivo completo y ninguna reserva, escucha o creación de hijo. Incompletas exige ausencia de avisos/arranques y conserva el diagnóstico de falta de credenciales. Las comprobaciones negativas acumuladas detectan cualquier efecto en cualquiera de sus variantes.

## Evidencia y límites

Se reutilizan las entradas verdes de `orquestar_evidencias.jsonl` del árbol exacto `e00cebcd09565dbf9e62bae1b182e036caec8765`: `python -m unittest tests.test_orquestar tests.test_telegram_gateway skills.telegram_gateway.test_gateway_fondo` (116 pruebas OK según el invocante) y `python -m py_compile skills/orquestar/orquestar.py skills/telegram_gateway/gateway.py skills/telegram_gateway/test_gateway_fondo.py && git diff --check`. No se relanzan.

Se acepta `docs/review/test_reviews/T-ADV-0030-red.md`: una prueba copiada al estado previo `869d9e9` en worktree aislado, trece fallos, doce por permitir token ambiental y uno por cuatro Popen, sin red ni procesos reales. Acredita el rojo funcional del rechazo; no se presenta como ejecución roja de toda la matriz. Precedencia, prefijo y demás regresiones del contrato previo no necesitan forzarse a rojo.

No se identifican hallazgos nuevos. Revisión estática proporcional a las correcciones y al riesgo. Solo se actualiza este informe; no se modifican pruebas ni producción, no se ejecutan comprobaciones y no se crea commit. La aprobación corresponde a la calidad de las pruebas, sin emitir veredicto sobre producción.
