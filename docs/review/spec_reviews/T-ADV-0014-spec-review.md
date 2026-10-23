# Revisión de Especificación: T-ADV-0014

- **Tarea**: `docs/plan/tasks/T-ADV-0014-agentes-configurados-y-estado-de-cuota-en-estado.md`
- **Especificación revisada**: `tests/features/telegram_gateway.feature` (escenarios `@T-ADV-0014`, líneas 99-123)
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.0 / 10**

## Comprobaciones Obligatorias

- ✅ **No regresión**: Los escenarios previos de `tests/features/telegram_gateway.feature` (líneas 1-98) permanecen intactos.
- ✅ **Coherencia**: Los tres escenarios son coherentes con el objetivo de negocio, `CA-M-1`, `CA-M-2` y las decisiones documentadas en `T-ADV-0014` (ventana móvil de 5 h, no inferir límites del proveedor mostrando «sin agotamiento registrado», conservar semántica de espera global sin atribuirla a un modelo desconocido y persistir plazo de cuota incluso al conmutar a reserva).
- ✅ **Trazabilidad**: Las etiquetas `@CA-M-1` y `@CA-M-2` existen en `T-ADV-0014` y corresponden exactamente a los criterios de aceptación funcionales que prueban (`CA-M-3` cubre pruebas unitarias y documentación).
- ✅ **Delta real**: Describe comportamiento nuevo y específico de `T-ADV-0014` sin duplicar el escenario básico previo `Consultar el estado`.

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Claridad** | 8/10 | El comportamiento esperado es inequívoco y orientado al usuario de CLI/Telegram, aunque el bloque añadido presenta pérdida de tildes UTF-8 (`?` por vocales acentuadas). |
| **Completitud** | 9.5/10 | Cubre el camino feliz (agentes efectivos, dificultad, escalada, reservas, distinción Artemisa/Atenea), bordes temporales de la ventana de 5 h (08:00 dentro, 06:59 fuera a las 12:00), no doble conteo de razonamiento, cuota activa tras conmutar a reserva, cuota vencida, espera global separada y ausencia de métricas o paso activo. |
| **Testeabilidad** | 9.5/10 | Emplea valores concretos y verificables (`100 + 20 + 30 = 150 tokens`, exclusión de `900 tokens` a las `06:59`, `1800 s` desde `11:50` -> `12:20` y `20 min`, espera global hasta `12:15` -> `15 min`). |
| **Estructura** | 9/10 | Ubicado en el `.feature` funcional existente (`telegram_gateway.feature`) junto al resto de comportamientos de `/estado`. |

## Hallazgos

### 🟡 MEDIA — Caracteres acentuados sustituidos por `?` en los escenarios del delta
- **Ubicación**: `tests/features/telegram_gateway.feature` (líneas 104-123) y secciones `Triaje` / `Decisiones sin preguntar` de `docs/plan/tasks/T-ADV-0014-agentes-configurados-y-estado-de-cuota-en-estado.md` (líneas 26-38).
- **para**: `desarrollador`
- **destino**: `resolver`
- **Detalle**: En los tres escenarios `@T-ADV-0014` se han escrito signos de interrogación `?` en lugar de caracteres UTF-8 acentuados (`arn?s`, `planificaci?n`, `consumi?`, `cach?`, `?ltimas`, `agot?`, `venci?`, `m?tricas`), rompiendo la uniformidad ortográfica del fichero `.feature` (que está en UTF-8 correcto en las líneas 1-98). Conviene restaurar las tildes en ambos ficheros.

### 🔵 BAJA — Casos adicionales acoplados en cláusulas `Entonces`
- **Ubicación**: `tests/features/telegram_gateway.feature` (líneas 105 y 123).
- **para**: `desarrollador`
- **destino**: `descartar`
- **Detalle**: Las líneas `Y para un paso de planificaci?n veo Atenea en lugar de Artemisa` y `Y un estado sin paso ni m?tricas sigue siendo consultable` introducen una variación del estado inicial dentro del `Entonces`. Al ser totalmente comprensibles y acotadas, no requieren separar escenarios adicionales.
