# Revisión de especificación — T-ADV-0024

**Fecha:** 2026-10-27  
**Revisor:** Hades · `/review-spec` · modo orquestado  
**Veredicto: APROBADO** — media 9,25/10, sin hallazgos CRÍTICOS ni ALTOS.

## Alcance y evidencia

Reevaluación exclusiva del delta `@T-ADV-0024` en `skills/telegram_gateway/features/telegram_gateway.feature` (líneas 215–280), frente a CA-M-1..5 de `docs/plan/tasks/T-ADV-0024-autoarranque-gateway-con-la-sesion-de-windows.md` y al contrato de credenciales de `skills/telegram_gateway/SKILL.md`.

Se consultaron el informe anterior y el borrador `autoarranque_windows.feature` mediante `git show wip/T-ADV-0024:<ruta>`. Son antecedentes de revisión, no un contrato aprobado ni una fuente que deba fusionarse. El diff del feature actual añade únicamente los cinco bloques del delta; los escenarios anteriores se conservan sin reevaluarlos.

La revisión se resuelve por lectura. No se revisaron producción, pruebas, diseño ni justificaciones del autor. No se ejecutaron pruebas funcionales ni suite completa. Se consultó `orquestar_evidencias.jsonl`; no se atribuye al árbol actual una verificación histórica sin comprobar su identidad. No se necesitó una verificación adicional para juzgar esta especificación.

## Obligatorias

| Regla | Resultado y motivo |
| --- | --- |
| No regresión | ✅ El diff solo añade el delta al final del feature funcional; no elimina ni modifica escenarios previos. |
| Coherencia | ✅ Exige token local para escuchar, admite IDs ambientales y rechaza el token exclusivamente ambiental con el motivo de solo avisos, antes de escucha, proceso de gateway o PID. |
| Trazabilidad | ✅ Todas las etiquetas CA-M-1..4 del delta existen y corresponden al comportamiento descrito. CA-M-5 exige pruebas simuladas y documentación: el delta fija Inicio y lanzador simulados; la entrega de pruebas y documentación se comprobará en sus fases, sin inventar un escenario de comportamiento para esos entregables. |
| Delta real | ✅ Especifica la gestión del registro y su ejecución con la sesión de Windows, distinta del arranque desde el bucle y de la escucha en segundo plano ya contratados. Los casos de credenciales verifican esta nueva entrada de Inicio. |

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Claridad | 9/10 | Las órdenes públicas, el proyecto seleccionado, los estados y las causas de rechazo son explícitos. |
| Completitud | 9/10 | Cubre alta repetida, separación entre proyectos, consulta sin cambios, baja idempotente, sesión válida, proyecto eliminado, token ausente o ambiental, IDs ausentes y rechazo fuera de Windows. |
| Testeabilidad | 9/10 | Fija códigos de salida, número de entradas y lanzamientos, raíz absoluta con espacios, ventana oculta, conservación de la entrada ajena y ausencia de escucha, PID y reintentos en errores. |
| Estructura | 10/10 | El delta está integrado en el feature existente del gateway, identificado por etiquetas, sin crear un archivo por tarea. |
| **Media** | **9,25/10** | Superior a 8 y sin hallazgos CRÍTICOS ni ALTOS. |

## Reevaluación de hallazgos anteriores

| Hallazgo | Estado | Evidencia del delta actual |
| --- | --- | --- |
| H-01 · ALTA · Orden y baja propia no verificables | **Resuelto** | Líneas 215–239: `on`, `estado` y `off` se ejecutan desde la raíz seleccionada; se concretan código cero y estados registrado/no registrado. La baja elimina la entrada propia, conserva exactamente la ajena y puede repetirse; las consultas no modifican entradas. |
| H-02 · ALTA · Falta ejecución satisfactoria de sesión sin administrador | **Resuelto** | Líneas 241–256: tras registrar con la orden pública se ejecuta la entrada simulando el inicio de sesión. Se observa una única solicitud de `adevv telegram --fondo`, con raíz absoluta de Proyecto Uno, sin ventana ni elevación ni rutas al almacén de versiones. Se incluyen IDs locales y ambientales con token local. |
| H-03 · MEDIA · Fallos agrupados y diagnóstico indeterminado | **Resuelto** | Líneas 258–272: cuatro ejemplos independientes distinguen proyecto eliminado, token ausente, token exclusivamente ambiental e IDs ausentes. Cada intento termina con error y diagnóstico de la causa, sin escucha, proceso de gateway, PID ni reintentos. |

No quedan hallazgos persistentes; no procede reasignar `para` ni destino a los ya resueltos.

## Hallazgos nuevos

Ninguno. La aprobación corresponde a la especificación del delta; no certifica la implementación ni el cumplimiento material de las pruebas y documentación de CA-M-5.
