**Veredicto:** APROBADO

# Revisión de especificación: T-ADV-0030

- **Revisor:** Hades · **Fecha:** 2026-10-26 · **Modo:** orquestado, paso especificar.
- **Alcance:** únicamente el delta `@T-ADV-0030` de `skills/orquestar/features/orquestacion.feature:80` y `skills/telegram_gateway/features/telegram_gateway.feature:70`.
- **Referencias:** CA-M-1..4 y DEC-ESP-01..04 de `docs/plan/tasks/T-ADV-0030-token-de-telegram-del-entorno-como-respaldo-solo-para-avisos.md`.
- **Reevaluación:** H-01..H-05 del informe histórico leído mediante `git show wip/T-ADV-0030:docs/review/spec_reviews/T-ADV-0030-spec-review.md`. El WIP no se fusiona ni se usa como base de los escenarios previamente aprobados.
- **Base observada:** `release/v1.0`, HEAD `ad500ac`, con cambios locales. Lectura de los artefactos actuales y comparación del delta respecto a HEAD; sin inspeccionar código, pruebas ni diseño.

Media **9/10**. Los cinco hallazgos históricos están resueltos en la especificación vigente. No se detectan hallazgos críticos o altos ni hallazgos menores nuevos.

## Obligatorias

- ✅ **No regresión:** los dos features solo añaden escenarios: 66 líneas en orquestación y 62 en gateway, sin eliminaciones ni modificaciones de escenarios anteriores de release. La corrección del delta rechazado del WIP está dentro del alcance autorizado.
- ✅ **Coherencia:** la resolución independiente por campo, el origen efectivo del token, la autorización de escucha y el aviso único por ejecución coinciden con DEC-ESP-01..04. Se conserva la escucha con token local, incluidos IDs ambientales; el token ambiental solo permite avisos. La entrada gestionada aparece como entrada interna de Python, sin introducir una opción pública nueva.
- ✅ **Trazabilidad:** todas las etiquetas `@CA-M-1` a `@CA-M-4` existen en la tarea y corresponden a lo observado. CA-M-1 cubre resolución y origen; CA-M-2, envíos y prefijo; CA-M-3, autorización y diagnóstico; CA-M-4, matrices de fuentes y aislamiento. La automatización y actualización documental de CA-M-4 quedan para desarrollo y documentación según el triaje; su realización no se acredita aquí.
- ✅ **Delta real:** el cambio distingue avisar de escuchar según el origen del token. Los ejemplos de precedencia y prefijo conservan contratos necesarios para discriminar regresiones de esta política; no se presentan como funcionalidad nueva ni duplican los escenarios anteriores de reservas.

## Puntuaciones

| Criterio | Nota | Evidencia |
|---|---:|---|
| Claridad | 9 | Fuentes, valores efectivos y resultados explícitos; ramas permitidas y rechazadas separadas. |
| Completitud | 9 | Solo proyecto, solo entorno, ambos, combinaciones cruzadas, campos vacíos/ausentes, credenciales incompletas, tres entradas y reinicio del bucle. |
| Testeabilidad | 9 | Tokens y destinatarios ficticios discriminantes, prefijo exacto, salida no cero, conteos de avisos y ausencia observable de escucha, procesos y reserva de PID. |
| Estructura | 9 | Escenarios en los features de sus funcionalidades, trazados por tarea y criterio, sin crear features por fase o versión. |
| **Media** | **9** | Superior a 8 y sin hallazgos críticos o altos. |

## Reevaluación de hallazgos históricos

Las severidades de esta tabla identifican los hallazgos anteriores; ninguno permanece abierto.

| Hallazgo | Severidad histórica | Estado vigente | Evidencia de resolución | Para | Destino |
|---|---|---|---|---|---|
| H-01 · Precedencia independiente | ALTA | **Resuelto** | Orquestación 80–98 fija token, IDs y origen `proyecto`/`entorno`/`ninguno`, con fuentes distintas, cruces, vacío y ausencia. Orquestación 130–144 y gateway 70–112 discriminan autorización por token, independientemente de los IDs. Gateway 114–130 conserva rechazo y ausencia de avisos con credenciales incompletas. | especificador | resolver, completado en la especificación |
| H-02 · Aislamiento | ALTA | **Resuelto** | Todos los escenarios del delta excluyen `TELEGRAM_*` heredadas, restauran el entorno incluso ante fallos y exigen datos ficticios y observadores sin red ni procesos reales. Los envíos concretan token y destinatario. DEC-ESP-02 confirma el contrato común. | especificador | resolver, completado en la especificación |
| H-03 · Entradas de escucha | ALTA | **Resuelto** | Gateway 70–112 enumera `adevv telegram`, `adevv telegram --fondo` y `gateway.py --gestionado`, con rechazo ambiental no cero y cero escucha/procesos/PID, o escucha simulada con token local. Gateway 79 y orquestación 125 fijan el mismo motivo exacto. | especificador | resolver, completado en la especificación |
| H-04 · Autoarranque y aviso único | ALTA | **Resuelto** | Orquestación 118–128 solicita tres autoarranques por ejecución, exige una sola nota y cero efectos, y repite la comprobación en un bucle nuevo. Orquestación 130–144 exige un arranque positivo con token local, con y sin respaldo y con IDs ambientales. | especificador | resolver, completado en la especificación |
| H-05 · Nombre delante del aviso | MEDIA | **Resuelto** | Orquestación 100–116 fija evento `version`, texto `Versión terminada`, prefijo exacto `[ProyectoDemo] Versión terminada`, firma conservada, token y destinatario efectivo para las tres fuentes y los cruces. | especificador | resolver, completado en la especificación |

## Hallazgos nuevos

Ninguno. No hay correcciones pendientes ni deuda que registrar derivada de esta revisión.

## Verificación y límites

Revisión ágil por lectura, limitada al contrato BDD y los CA/DEC autorizados. La comparación con HEAD confirma que los escenarios previos permanecen intactos. El informe histórico se usa únicamente para reevaluar H-01..H-05; sus referencias a diseño no se consultan ni se convierten en requisitos adicionales.

No se ejecutó suite ni ningún comando de verificación. Según el triaje y el reparto indicado, Atenea ejecutará al cierre de este paso `adevv orquestar --verificar "git diff --check"`; este informe no atribuye un resultado en verde a esa comprobación pendiente. Desarrollo automatizará los ejemplos y acreditará su comportamiento posteriormente. La aprobación corresponde a la especificación, sin acreditar implementación, pruebas ejecutadas ni documentación de uso actualizada.

Se escribe únicamente este informe. Sin cambios en features, tarea, estado, código, pruebas o diseño; sin commit.
