**Veredicto:** APROBADO

# Revisión de especificación: B-ADV-0026

- **Revisor:** Hades · **Fecha:** 2026-11-07 · **Skill:** `/review-spec`.
- **Alcance:** únicamente la especificación del delta etiquetada con `@B-ADV-0026`:
  - `skills/orquestar/features/orquestacion.feature` (líneas 389–450).
  - `skills/telegram_gateway/features/telegram_gateway.feature` (líneas 282–305).
- **Origen:** `docs/plan/bugs/B-ADV-0026-intervencion-humana-por-telegram-sin-detener-tareas-independientes.md` (`CA-1`..`CA-9` y triaje).

Media **9.25/10**. No se detectan hallazgos críticos (🔴), altos (🟠) ni menores (🟡/🔵).

## Obligatorias

- ✅ **No regresión:** el diff respecto a `base_calidad` (`cd1b3bdd452f4454bf5a28c620e3c38a52f918a1`) únicamente añade 66 líneas al final de `skills/orquestar/features/orquestacion.feature` y 28 líneas al final de `skills/telegram_gateway/features/telegram_gateway.feature`, sin eliminar ni modificar escenarios existentes.
- ✅ **Coherencia:** los escenarios respetan los contratos documentados del modo orquestado (decisiones con valor por defecto seguro, aislamiento en `wip/<ID>`, protección del árbol rastreado desde el gateway mientras corre el bucle, evento `respuesta`, autorización por `TELEGRAM_ALLOWED_USER_IDS`, aislamiento entre proyectos y prohibición de conceder permisos de publicación de versión).
- ✅ **Trazabilidad:** todas las etiquetas `@CA-1` a `@CA-9` existen en `B-ADV-0026` y cada escenario prueba fielmente los criterios declarados:
  - `@CA-1`: bloqueo local con ID de tarea y pregunta (`Q-ADV-0001`), contexto, liberación del paso sin lectura interactiva por `stdin` y estado consultable (`orquestacion.feature:389,401`, `telegram_gateway.feature:282`).
  - `@CA-2`: conservación y aislamiento del trabajo en `wip/T-ADV-0101` con `release/v1.1` y `base_calidad` limpios antes de iniciar `T-ADV-0102` (`orquestacion.feature:389`).
  - `@CA-3`: aviso único accionable del evento `respuesta` a usuarios autorizados e idempotencia y diagnóstico (`canal no disponible`, `evento desactivado`, `fallo de envío`) cuando el canal no está disponible o falla (`orquestacion.feature:389,401`).
  - `@CA-4`: continuidad con tarea independiente (`T-ADV-0102`), retención de dependiente (`T-ADV-0103`) y espera cuando no queda trabajo elegible distinguiendo bloqueo de tarea frente a bloqueo global (`orquestacion.feature:389,414,432`).
  - `@CA-5`: respuesta vinculada en Telegram validando autorización, ambigüedad con varias preguntas abiertas, referencias inexistentes/cerradas/de otro proyecto, vínculo por ID de pregunta o tarea, consulta con `/preguntas` y `/estado`, e idempotencia ante entregas repetidas (`telegram_gateway.feature:282,299`).
  - `@CA-6`: encolado duradero durante la ejecución de otra tarea sin tocar archivos rastreados, confirmación diferenciando recepción de reanudación efectiva, incorporación entre pasos y mantenimiento del bloqueo ante respuesta insuficiente explicando qué falta (`orquestacion.feature:414,425`).
  - `@CA-7`: reanudación conservando el trabajo previo de `wip/T-ADV-0101`, desbloqueo posterior de `T-ADV-0103`, continuación o relanzamiento automático cuando el bucle esperaba o se había detenido por falta de elegibles, y respeto a la parada manual explícita (`orquestacion.feature:414,432`).
  - `@CA-8`: persistencia tras reinicios o recargas sin perder respuestas ni reanudar dos veces, protección del repositorio durante otros pasos y mantenimiento de restricciones de seguridad y cierre de versión (`orquestacion.feature:414,432,445`, `telegram_gateway.feature:282,299`).
  - `@CA-9`: cobertura mediante escenarios y tablas de ejemplos de los casos de verificación exigidos por el triaje (`telegram_gateway.feature:282,299` junto con la batería de `orquestacion.feature:389-450`).
- ✅ **Delta real:** los 8 escenarios y esquemas describen el nuevo circuito de intervención humana por Telegram y su coordinación con el bucle sin solaparse ni duplicar escenarios previos.

## Puntuaciones

| Criterio | Nota | Justificación |
|---|---:|---|
| Claridad | 9 | Lenguaje inequívoco, centrado en el comportamiento observable por el usuario y en los estados de negocio (`planned`, `blocked`, `pendiente_de: humano`, referencias `Q-ADV-*`). |
| Completitud | 9 | Cubre el flujo principal A/B/C, fallos y ausencias de canal, concurrencia durante otra tarea, respuestas insuficientes, rechazos de validación/autorización/ambigüedad, falta de elegibles con y sin parada manual, duplicados y reinicios/recargas. |
| Testeabilidad | 10 | Entradas, actores (`111`, `222`, `999`), identificadores (`T-ADV-0101`..`0104`, `Q-ADV-0001`..`0009`, `Q-DOS-0001`), comandos (`/responder`, `/preguntas`, `/estado`) y salidas observables concretos y verificables determinísticamente. |
| Estructura | 9 | Escenarios repartidos limpiamente entre `orquestacion.feature` (motor y ciclo de vida del bloqueo/reanudación) y `telegram_gateway.feature` (interacción y validación en el gateway). |
| **Media** | **9.25** | Superior a 8 y sin hallazgos 🔴 ni 🟠. |

## Hallazgos

Sin hallazgos.
