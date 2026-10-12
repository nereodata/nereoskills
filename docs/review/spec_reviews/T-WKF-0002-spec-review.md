# Revisión de especificación: T-WKF-0002 (Ronda 2)

- **Tarea:** `docs/plan/tasks/T-WKF-0002-telegram-gateway-integration.md`
- **Especificación:** `tests/features/telegram_gateway.feature`
- **Revisor:** Hades (`review-spec`)
- **Fecha:** 2026-10-12
- **Ronda anterior:** RECHAZADO (media 6,75; 1 🔴, 2 🟠)

## Veredicto: ✅ APROBADO

Media 8,5 (> 8), sin hallazgos 🔴 ni 🟠. Se corrigieron todos los hallazgos bloqueantes. Quedan dos 🟡 nuevos con destino `resolver`.

## Estado de los hallazgos anteriores

| ID | Severidad | Estado | Comprobación |
|---|---|---|---|
| H-1 | 🔴 | ✅ resuelto | Hay cuatro escenarios (tarea/bug × con/sin versión, líneas 22-60): con `v0.2.0` → `planned` y `version "v0.2.0"`; sin versión → `backlog` y `version ""`. Coincide con `skills/task-add/SKILL.md` y `skills/bug-add/SKILL.md`. |
| H-2 | 🟠 | ✅ resuelto | `/estado` tiene un backlog de ejemplo y la salida Markdown exacta, con la versión, la tarea en curso y la lista y el número de pendientes (líneas 74-105). Incluye el caso sin tarea en curso. |
| H-3 | 🟠 | ✅ resuelto | Esquema del escenario con `/estado`, `/status`, `/tarea` y `/bug` desde el ID `99999`, comprobando que no hay respuesta ni cambios en `docs/plan/` (líneas 8-20). Se quitó el escenario autorizado, que no tenía resultado observable. |
| H-4 | 🟡 | ✅ resuelto | El destino tiene nombre (`"12345,67890"`), el texto enviado es exacto y hay escenario de resiliencia ante fallos de Telegram (líneas 107-120). Queda un detalle de testeabilidad en ese escenario: ver N-1. |
| H-5 | 🟡 | ✅ resuelto | `/status` cubierto (líneas 18 y 91), Esquema de argumento vacío para `/tarea` y `/bug` (líneas 62-72) e IDs concretos (`T-WKF-0003`, `B-WKF-0002`) a partir del último existente. |
| H-6 | 🔵 | persiste (`descartar`) | Sigue sin especificarse el texto libre ni los comandos desconocidos. El destino era `descartar`, así que no bloquea: se decide en el diseño. |

## Obligatorias

| Comprobación | Resultado | Motivo |
|---|---|---|
| No regresión | ✅ | El `.feature` es nuevo y no toca otros escenarios. |
| Coherencia | ✅ | Los estados y versiones siguen Issue-as-Code v3.0. Las rutas `docs/plan/tasks/` y `docs/plan/bugs/` coinciden con `task_config.yaml`. |
| Trazabilidad `@CA-*` | ✅ | `@CA-M-1`…`@CA-M-4` existen en la tarea y cada escenario prueba el criterio de su etiqueta. |
| Delta real | ✅ | Todo es comportamiento nuevo y no hay duplicados: el Esquema de `/estado`/`/status` sustituye al solapamiento anterior. |

## Puntuaciones

| Criterio | Ronda 1 | Ronda 2 | Comentario |
|---|---|---|---|
| Claridad | 7 | 9 | Pasos concretos y mensajes literales. Ya no quedan «procesa el comando» ni «mensaje estructurado». |
| Completitud | 6 | 8 | Cubre el camino feliz, la versión, los argumentos vacíos, los no autorizados, los alias y el fallo de red. No se ve qué estados cuentan como «pendientes» (N-2). |
| Testeabilidad | 5 | 8 | Casi todo tiene valores exactos. El escenario de resiliencia todavía usa resultados vagos (N-1). |
| Estructura | 9 | 9 | Un único `.feature` por funcionalidad, con Esquemas donde aportan. |
| **Media** | **6,75** | **8,5** | |

## Hallazgos nuevos

### 🟡 MEDIA

**N-1. Resultados vagos en las notificaciones salientes** (líneas 112 y 119-120) — `resolver`
«la llamada finaliza con código de éxito», «captura el error sin interrumpir el flujo» y «registra el fallo en el log del sistema» no dicen qué se observa: ¿qué devuelve la función?, ¿qué nivel y qué texto tiene la entrada del log?
*Corrección:* fijar el contrato observable. Por ejemplo: «la función de notificación devuelve verdadero» / «devuelve falso sin lanzar ninguna excepción» y «se registra un aviso de nivel WARNING que contiene "Alerta de sistema"».

**N-2. No queda definido qué cuenta como «pendiente» en `/estado`** (líneas 76-105) — `resolver`
Los ejemplos tratan `backlog` y `planned` como pendientes, pero ninguno tiene una tarea terminada. Por eso no se comprueba que las tareas `done` (o cerradas) quedan fuera del recuento, ni que la tarea `in_progress` no se cuenta también como pendiente. Esto último sí se deduce del primer ejemplo.
*Corrección:* añadir al `Dado` del primer Esquema una tarea `"T-WKF-0001"` con estado `"done"` y mantener `*Pendientes (1):*` en la salida esperada.
