# Revisión de Especificación: T-ADV-0016

- **Tarea**: `docs/plan/tasks/T-ADV-0016-ejecucion-en-segundo-plano-de-telegram-gateway.md`
- **Especificación revisada**: `tests/features/telegram_gateway.feature` (escenarios `@T-ADV-0016`, líneas 184-225)
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.4 / 10**

## Comprobaciones Obligatorias

- ✅ **No regresión**: Los escenarios existentes en `tests/features/telegram_gateway.feature` (líneas 1-183) permanecen intactos.
- ✅ **Coherencia**: Los escenarios son coherentes con los criterios `CA-M-1` a `CA-M-4`, el triaje de `T-ADV-0016` y la decisión arquitectónica `DEC-P09` (gestión de `--fondo` y `--parar` en `gateway.py`, proceso identificable como `gateway.py` compatible con `adevv/processes.py` sin modificarlo, exclusión de `telegram.pid`, `telegram.log` y `telegram.parar` en git, parada cooperativa independiente del bucle, autoarranque no bloqueante en ejecución real de `orquestar.py` y actualización documental en `skills/`).
- ✅ **Trazabilidad**: Todas las etiquetas `@CA-M-1`, `@CA-M-2`, `@CA-M-3` y `@CA-M-4` existen en `T-ADV-0016` y corresponden exactamente a los criterios que cada escenario valida.
- ✅ **Delta real**: Describe únicamente el comportamiento nuevo de ejecución en segundo plano, parada cooperativa y autoarranque del gateway de Telegram, sin duplicar escenarios previos.

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Claridad** | 9.0/10 | Comportamiento inequívoco y bien delimitado; presenta únicamente erratas cosméticas de codificación (`?` en lugar de vocales acentuadas en seis palabras). |
| **Completitud** | 9.5/10 | Cubre caminos felices, prevención de duplicados con PID vivo, recuperación ante PID obsoleto/inválido, parada cooperativa sin afectar al bucle, repetición de `--parar` sin credenciales, limpieza ante fallos de arranque/escucha, autoarranque en primer y segundo plano, tolerancia a fallos y no arranque en consultas (`--estado`, verificación, revisión) o sin credenciales. |
| **Testeabilidad** | 9.5/10 | Resultados concretos y observables (archivos `telegram.pid`, `telegram.log`, `telegram.parar`, exclusión de git, identificación como `gateway.py` y conservación del estado del bucle). |
| **Estructura** | 9.5/10 | Integrado en el archivo funcional `tests/features/telegram_gateway.feature` junto al resto de escenarios del gateway. |

## Hallazgos

### 🔵 BAJA — Caracteres `?` en lugar de tildes en el texto de los escenarios añadidos
- **Ubicación**: `tests/features/telegram_gateway.feature` (líneas 191, 195, 197, 218, 223 y 225: `inv?lido`, `orquestaci?n`, `operaci?n`, `verificaci?n`, `revisi?n`).
- **para**: `especificador`
- **destino**: `descartar`
- **Detalle**: Se han introducido signos de interrogación literales en lugar de vocales acentuadas en seis palabras del bloque `@T-ADV-0016`. Al ser puramente cosmético y no afectar a la semántica ni a la trazabilidad de la especificación, se descarta.
