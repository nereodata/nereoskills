# Revisión de Especificación: T-ADV-0015

- **Tarea**: `docs/plan/tasks/T-ADV-0015-control-remoto-bucle-y-metricas-en-telegram.md`
- **Especificación revisada**: `tests/features/telegram_gateway.feature` (escenarios `@T-ADV-0015`, líneas 125-182)
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.4 / 10**

## Comprobaciones Obligatorias

- ✅ **No regresión**: Los escenarios existentes de `tests/features/telegram_gateway.feature` (líneas 1-123) se mantienen intactos.
- ✅ **Coherencia**: Los escenarios son plenamente coherentes con el objetivo de negocio, los criterios `CA-M-1` a `CA-M-4` y el triaje de `T-ADV-0015` (solicitud de parada diferida al fin del paso en curso, arranque en segundo plano con anuncio del siguiente paso previsto, reutilización de la consulta de métricas con filtro por defecto `ultima` y bloqueo a usuarios no autorizados).
- ✅ **Trazabilidad**: Todas las etiquetas `@CA-M-1`, `@CA-M-2`, `@CA-M-3` y `@CA-M-4` existen en `T-ADV-0015` y corresponden al criterio que cada escenario verifica.
- ✅ **Delta real**: Introduce únicamente el comportamiento nuevo de control remoto (`/parar`, `/stop`, `/lanzar`, `/run`) y consulta de métricas (`/metricas`, `/metrics`, `/ayuda`) sin duplicar escenarios previos.

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Claridad** | 9.5/10 | Lenguaje de negocio claro, inequívoco y orientado al usuario de Telegram, sin acoplarse a detalles internos de implementación. |
| **Completitud** | 9.5/10 | Cubre caminos felices, alias en español e inglés (incluido sufijo `@AdevvBot`), casos borde de bucle ya en marcha o ya parado, filtros de versión, errores de filtro o registro corrupto, ausencia de datos, `/ayuda` y rechazo a usuarios no autorizados. |
| **Testeabilidad** | 9.0/10 | Resultados observables y concretos para cada comando y condición de borde. |
| **Estructura** | 9.5/10 | Integrado limpiamente en el `.feature` funcional existente del gateway de Telegram (`tests/features/telegram_gateway.feature`). |

## Hallazgos

### 🔵 BAJA — Variantes de error agrupadas en cláusulas `Pero`/`Y` de un único escenario
- **Ubicación**: `tests/features/telegram_gateway.feature` (líneas 167-172).
- **para**: `especificador`
- **destino**: `descartar`
- **Detalle**: El escenario `Seleccionar versiones y tratar errores de consulta` condensa en cláusulas `Pero`/`Y` tres condiciones de entrada distintas (filtro inválido, registro corrupto con número de línea y ausencia de métricas) además de la consulta `v0.3,v0.4`. Al ser conciso e inequívoco para las pruebas unitarias previstas en el triaje, no requiere desglosarse.
