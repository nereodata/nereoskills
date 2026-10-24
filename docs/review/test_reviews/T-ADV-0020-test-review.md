# Test Review: T-ADV-0020

- **Veredicto**: APROBADO
- **Media**: 9.5 / 10

## Puntuaciones

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Cobertura** | 9.5 / 10 | Cubre CA-M-1..4: limpieza de `parte()` y `resumen()`, listado completo de los 5 roles con variantes de dificultad/paso/reserva incluso en `FIN` y `PARAR`, precedencia de cuota (agotamiento vigente > `rate_limits` nativo de Codex > ventana móvil de 5 h con límites configurados y por familia), flags CLI (`--agentes`, `--agents`) y comandos en Telegram (`/agentes`, `/agents`, `/ayuda` y control de autorización). |
| **Aserciones** | 9.5 / 10 | Comprueban valores concretos de porcentaje, conteo de tokens sin duplicar `razonamiento`, unicidad por modelo (`harness/model`), ausencia de bloques de agentes en `/estado` e inmutabilidad del árbol de archivos en consultas. |
| **Rojo correcto** | 10 / 10 | Las 7 pruebas fallan exclusivamente por ausencia de la funcionalidad bajo desarrollo (5 `AttributeError` por `informe_agentes` aún no definido y 2 `AssertionError` por flags CLI y rutas de comando en el gateway pendientes), sin errores de sintaxis, importación ni fixtures. |
| **Estabilidad** | 9.0 / 10 | Directorios temporales aislados, `CODEX_HOME` redirigido al entorno temporal y reloj fijado mediante mock (`motor.ahora`). |

## Hallazgos

- **[🔵 BAJA] Aserción positiva en `parte()` y `resumen()` tras limpiar agentes** (`skills/orquestar/test_informe_agentes.py`, `test_effective_step_and_read_only_status`, líneas 111-114) — `destino: descartar`
  Además de verificar con `assertNotIn` que desaparecen `'codex/'`, `'Agentes para'` y `'tokens (5 h)'`, convendría comprobar que sigue presente algún dato básico del estado general (p. ej. `'T-ADV-0020'` o `'task-dev'`), aunque el resto de la suite de estado ya lo cubre.

- **[🔵 BAJA] Timestamp de reinicio en prueba de `NaN` no derivado del reloj simulado** (`skills/orquestar/test_informe_agentes.py`, `test_expired_invalid_native_and_invalid_limits_fall_back`, línea 97) — `destino: descartar`
  Se usa el epoch literal `9999999999` en lugar de un timestamp relativo a la fecha fijada en `motor.ahora` (`2026-10-24T12:00:00+00:00`) como sí hace `test_native_latest_valid_and_exhaustion_precedence`. No afecta al determinismo actual.
