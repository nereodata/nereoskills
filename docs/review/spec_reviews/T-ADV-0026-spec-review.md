# Revisión de especificación: T-ADV-0026

- **Revisor:** Hades · **Fecha:** 2026-10-26 · **Modo:** orquestado · **Ronda:** reevaluación.
- **Artefacto:** los seis escenarios del delta en `skills/telegram_gateway/features/telegram_gateway.feature`.
- **Referencia:** `docs/plan/tasks/T-ADV-0026-reservas-en-la-conversacion-de-telegram.md`, CA-M-1 a CA-M-6, triaje y DEC-ESP-01/02/03; H-01, H-02 y H-03 del reporte anterior.
- **Alcance:** resolución de los tres hallazgos y revisión de las correcciones por posibles problemas nuevos. Los escenarios aprobados de `skills/orquestar/features/orquestacion.feature` se consultan exclusivamente como contrato de coherencia. Sin revisión de diseño, código, pruebas automatizadas ni del resto del WIP.

## Veredicto: APROBADO

Media **9,25/10**, sin hallazgos críticos ni altos. Los tres hallazgos anteriores están **resueltos**. No se detectan hallazgos nuevos en el delta revisado.

## Obligatorias

- ✅ **No regresión:** el delta incorpora un feature nuevo bajo `skills/telegram_gateway/features/`; no elimina ni modifica escenarios existentes. La ubicación responde a DEC-ESP-02 y a la instrucción del usuario. No requiere cambios en `tests/features/`.
- ✅ **Coherencia:** DEC-ESP-01 explicita que CA-M-3 amplía la continuidad de sesiones de la conversación: una reserva puede reanudar la sesión de su propio usuario y arnés. Esto conserva la prohibición aprobada de reutilizar sesiones de otros arneses; no modifica las sesiones de pasos ni agentes. DEC-ESP-03 concreta el salto del único modelo con cuota vigente y conserva el tratamiento de errores ordinarios. No hay contradicción con los contratos aprobados.
- ✅ **Trazabilidad:** todas las etiquetas `@CA-M-*` existen en la tarea y corresponden al comportamiento descrito. CA-M-1 aporta el contexto de configuración heredada; su cobertura previa en B-ADV-0005 no requiere escenarios duplicados. CA-M-6 se aborda en las subfases posteriores de pruebas y documentación, sin exigir aquí escenarios sobre la existencia de archivos.
- ✅ **Delta real:** se concreta la conmutación de la conversación por cuota o indisponibilidad, la vigencia compartida del agotamiento, la continuidad y separación de sesiones, el retorno al titular y el diagnóstico cuando no queda ninguna configuración disponible. La herencia y ausencia ya aprobadas se usan como contexto, sin volver a especificarlas de forma independiente.

## Puntuaciones

| Criterio | Nota | Motivo |
|---|---:|---|
| Claridad | 9 | Candidatos, orden, causas de conmutación y resultados identificados; errores ordinarios separados de cuota y arranque. |
| Completitud | 9 | Cubre conmutación, salto de cuota vigente, retorno, aislamiento de usuarios, agotamiento de candidatos y el límite sin reservas. Se conserva la cobertura previa indicada por el triaje. |
| Testeabilidad | 9 | Identificadores concretos de sesiones y usuarios, recuperación exacta y resultados observables en firma, diagnóstico, consultas y lanzamientos. |
| Estructura | 10 | Feature de la funcionalidad del gateway, con escenarios organizados por comportamiento y trazabilidad mediante etiquetas. |
| **Media** | **9,25** | |

## Resolución de hallazgos anteriores

### H-01 · 🟠 ALTA · Resuelto

- **Para original:** `especificador`. **Destino original:** `resolver`.
- **Evidencia:** el escenario «Conservar las sesiones de cada arnés al usar reservas y regresar al titular» prepara `codex-s1` y `agy-s1` para el usuario `12345`. La reserva reanuda exactamente `agy-s1`, conserva `agy-s2` y lo reanuda en el mensaje siguiente; después guarda `agy-s3` sin reemplazar `codex-s1`. A las 12:31 UTC el titular reanuda exactamente `codex-s1`, responde sin reservas y se conserva `agy-s3`.
- **Aislamiento:** «Aislar las sesiones de otro usuario durante la conmutación» prepara `67890` sin sesiones; agy y después codex responden sin reanudar sesiones ajenas. `agy-u2` queda únicamente para `67890`, mientras `codex-s1` y `agy-s3` permanecen para `12345`.
- **Conclusión:** los resultados distinguen la conservación por usuario y arnés de la sobrescritura de una sesión única o la transferencia entre usuarios/arneses. La ampliación está expresamente recogida en DEC-ESP-01 y no reabre el contrato de pasos y agentes.

### H-02 · 🟡 MEDIA · Resuelto

- **Para original:** `especificador`. **Destino original:** `resolver`.
- **Evidencia:** «Conmutar por cuota y compartir su recuperación exacta» fija todos sus instantes en UTC el 26 de octubre de 2026. El fallo de `codex/m1` a las 12:00:00 durante 1800 segundos produce una recuperación compartida exacta a las 12:30:00. Tanto `/agentes` como la consulta de cuotas del bucle reconocen esa vigencia a las 12:15:00 y dejan de considerarla vigente a las 12:30:00.
- **Conclusión:** el agotamiento consultado es explícitamente el generado por la conversación y tiene un resultado temporal discriminante. El fallo de arranque de `agy/m2` no altera esa recuperación ni genera cuota para agy.

### H-03 · 🟡 MEDIA · Resuelto

- **Para original:** `especificador`. **Destino original:** `resolver`.
- **Evidencia:** «No lanzar el único modelo cuando su cuota sigue vigente» configura únicamente `codex/m1`, sin reservas propias ni heredadas, con cuota vigente hasta las 12:30:00 UTC. Un mensaje a las 12:00:00 exige cero lanzamientos y un diagnóstico que identifica el modelo y la recuperación, sin esperar a que se recupere la cuota.
- **Conclusión:** el límite tiene preparación y ejecución propias, separado del diagnóstico de tres configuraciones indisponibles y conforme a DEC-ESP-03.

## Hallazgos nuevos

Ninguno. No quedan hallazgos pendientes de esta revisión ni acciones que asignar con `para` y `destino`.

## Verificación y límites

Revisión por lectura de la especificación y sus referencias autorizadas. No se ejecutaron pruebas ni suite completa; no son necesarias para este veredicto de especificación. No se revisaron diseño ni pruebas, ni se recuperó o auditó el WIP completo. Esta aprobación no acredita implementación ni pruebas en verde. Solo se sobrescribe este reporte; no se modifican escenarios, código ni tests y no se crea commit.
