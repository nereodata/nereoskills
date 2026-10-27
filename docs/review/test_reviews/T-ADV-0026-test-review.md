# Revisión de pruebas: T-ADV-0026

- **Revisor:** Hades. **Fecha:** 2026-10-26. **Modo:** orquestado. **Ronda:** única revisión del delta completo.
- **Artefacto:** `skills/telegram_gateway/test_reservas.py` completo, archivo nuevo de siete pruebas.
- **Contrato:** los seis escenarios APROBADOS de `skills/telegram_gateway/features/telegram_gateway.feature`, la tarea `docs/plan/tasks/T-ADV-0026-reservas-en-la-conversacion-de-telegram.md` y DEC-ESP-01/02/03.
- **Alcance:** preparación, aserciones, capacidad discriminante, rojo y estabilidad de las pruebas. Sin revisión de producción ni del diseño. El WIP se considera histórico y no fusionado.

## Veredicto: APROBADO

Media **8,75/10**, sin hallazgos críticos ni altos. Un hallazgo medio, para `desarrollador`, destino `resolver`.

## Puntuaciones

| Criterio | Nota | Evidencia |
|---|---:|---|
| Cobertura | 9 | Los seis escenarios tienen pruebas identificables; se añade integración de reserva propia objeto/lista y herencia de esfuerzo. |
| Aserciones | 8 | Verifican lanzamientos, continuidad y aislamiento de sesiones, persistencia y consultas de cuota, firmas y diagnóstico por perfil. Falta comprobar el modelo real enviado en los comandos del caso de conmutación encadenada. |
| Rojo correcto | 9 | La evidencia aportada alcanza las ejecuciones y falla por comportamientos ausentes, sin errores de carga, sintaxis o preparación. La regresión de error ordinario ya pasa. |
| Estabilidad | 9 | Directorios temporales por prueba, reloj fijado y avances explícitos, lanzador y búsqueda de ejecutables simulados, parches restaurados al terminar. Sin red, modelos ni credenciales reales. |
| **Media** | **8,75** | |

## Cobertura del contrato aprobado

| Escenario | Prueba | Evaluación |
|---|---|---|
| Conmutar por cuota y compartir su recuperación exacta | `test_cuota_cruda_arranque_reserva_y_metricas` | Simula cuota en salida cruda, error de arranque y éxito de la segunda reserva; exige orden codex → agy → claude, firma de reserva, sesión propia y conservación del consumo. Consulta el agotamiento compartido a las 12:15 y exactamente al vencer a las 12:30; exige recuperación exacta para codex y ausencia de cuota para agy. Comprueba también `/agentes` y su hora de recuperación adaptada a la zona local. Véase H-01. |
| Conservar las sesiones de cada arnés al usar reservas y regresar al titular | `test_salta_cuota_y_vuelve_al_titular` | Prepara codex-s1 y agy-s1; exige reanudar agy-s1 y después agy-s2, conservar agy-s3 y codex-s1, volver a codex-s1 tras vencer la cuota y responder sin marca de reserva. Los conteos acumulados impiden lanzamientos adicionales. Conforme a DEC-ESP-01. |
| Aislar las sesiones de otro usuario durante la conmutación | `test_aislamiento_otro_usuario` | Prepara sesiones de 12345 y actúa como 67890. Comprueba almacenamiento de agy-u2 para 67890, ausencia de sesiones ajenas y de `--resume` en ambas llamadas, retorno a codex y conservación de las sesiones de 12345. |
| Diagnosticar todas las configuraciones indisponibles | `test_todos_indisponibles_diagnostico_al_usuario` | Prepara cuota vigente, ejecutable agy ausente y fallo de arranque de claude. Exige un único lanzamiento de claude y diagnóstico que asocia cada perfil con su motivo, más la recuperación de cuota. |
| No lanzar el único modelo cuando su cuota sigue vigente | `test_unico_agotado_no_se_lanza` | Elimina las reservas de la configuración heredada, registra cuota vigente y exige cero lanzamientos junto al modelo, motivo y recuperación en la respuesta al usuario. Conforme a DEC-ESP-03. |
| No ocultar un fallo ordinario como indisponibilidad | `test_error_ordinario_no_conmuta` | Prepara sesión previa y reserva disponible. Exige dos llamadas al titular, primera con sesión y segunda sin ella, y propagación del error ordinario sin invocar reservas. Conforme a DEC-ESP-03. |

La séptima prueba, `test_herencia_objeto_lista_y_reserva_propia`, aporta cobertura de integración para CA-M-1: reserva propia objeto/lista sobre configuración heredada, selección de m4 y esfuerzo high en el comando. No se exige duplicar la cobertura previa de B-ADV-0005.

## Hallazgos

### H-01 · 🟡 MEDIA · Comprobar el modelo enviado en la conmutación encadenada

- **Para:** `desarrollador`.
- **Destino:** `resolver`.
- **Ubicación:** `skills/telegram_gateway/test_reservas.py:39`, aserciones de las líneas 43–45.
- **Evidencia:** el lanzador devuelve resultados por posición, sin discriminar el comando recibido. La prueba exige los arneses `codex`, `agy`, `claude` y que la respuesta contenga `claude/m3`, pero no inspecciona los argumentos de modelo de esos tres comandos.
- **Efecto:** una regresión que construya los comandos de reserva con un modelo incorrecto y conserve la firma de la configuración esperada no queda detectada por este caso. La prueba adicional de m4 sí inspecciona su comando, pero no los de agy/m2 y claude/m3 de este escenario.
- **Corrección concreta:** añadir aserciones sobre los argumentos de modelo de las tres llamadas registradas, exigiendo m1, m2 y m3 respectivamente, o hacer que el doble de lanzamiento valide esos argumentos antes de devolver cada resultado. Mantener las aserciones de firma y orden existentes.
- **Carácter:** mejora localizada y no bloqueante; la cobertura de selección, orden y continuidad ya discrimina la funcionalidad principal.

## Evidencia y límites

Se acepta la compilación verde comunicada mediante `--verificar` para el árbol identificado por el invocante como `ce7bb12220`: `python -m py_compile skills/telegram_gateway/test_reservas.py`. No se repite. No hay linter ni tipado configurado para este delta stdlib.

Se revisa `docs/review/test_reviews/T-ADV-0026-red.txt`: siete pruebas, tres fallos y cuatro errores. Los cuatro errores incluyen dos subcasos de reserva propia objeto/lista. La salida muestra cuota que termina en error ordinario, falta de conmutación, falta de salto del titular agotado y propagación del fallo de arranque; son rojos coherentes con la funcionalidad pendiente. No hay fallos de importación, sintaxis ni fixtures. Que la prueba de error ordinario ya pase es correcto: protege el comportamiento conservado, no una función nueva.

Revisión realizada por lectura, sin ejecutar pruebas, compilación ni suite completa. No se inspeccionó producción, no se fusionó WIP ni se modificaron pruebas o producción. Los posibles signos `?` de codificación en docstrings no afectan a la semántica y no se consideran un defecto de esta revisión. Solo se crea este informe; no se crea commit. La aprobación valora las pruebas y no acredita una implementación en verde.

## Aplicación por Artemisa

H-01 resuelto: se comprueban m1, m2 y m3 en los tres comandos y effort high heredado en cada arnés. Correcciones editoriales: docstrings UTF-8 y aserción de texto `arranque` (antes `arranc`, que no es subcadena de arranque). Siete pruebas verdes tras implementar; no se cambia ningún escenario ni se retira ninguna aserción funcional.
