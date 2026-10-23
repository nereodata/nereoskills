# Revisión de Pruebas: T-ADV-0014

- **Tarea**: `docs/plan/tasks/T-ADV-0014-agentes-configurados-y-estado-de-cuota-en-estado.md`
- **Archivo de pruebas**: `skills/orquestar/test_estado_agentes.py`
- **Especificación de referencia**: `tests/features/telegram_gateway.feature` (`@T-ADV-0014`, líneas 99-123)
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.5 / 10**

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Cobertura** | 9.5/10 | Los 8 tests cubren íntegramente los 3 escenarios `@T-ADV-0014` en ambas superficies (`parte()` y `resumen()`), incluyendo dificultad, ajustes por paso, reservas heredadas, escalada por rechazos, cambio a `atenea` en planificación, bordes exactos de la ventana de 5 h (`07:00:00`, `06:59:59`, `12:00:01`), no doble conteo de `razonamiento`, offsets ISO distintos (`+02:00` frente a `+00:00`), cuotas vencidas, espera global separada, estado `FIN` sin métricas, retrocompatibilidad con `sin_cuota`/`espera_s` y persistencia de `modelo_cuota`/`cuota_espera_s` al conmutar a reserva. |
| **Aserciones** | 9.5/10 | Comprueban valores concretos observables en la salida de texto de Telegram y CLI, el contenido exacto de `orquestar_metricas.jsonl` y que la consulta es de solo lectura en disco. |
| **Rojo correcto** | 10/10 | Los 8 tests ejecutan y fallan limpiamente por ausencia de la funcionalidad nueva (sin errores de sintaxis, importación ni fixtures). |
| **Estabilidad** | 9/10 | Uso de `tempfile.TemporaryDirectory`, reloj fijo (`motor.ahora`) y mocks de subprocesos/red; sin dependencia de red ni de orden de ejecución. |

## Hallazgos

### 🔵 BAJA — Hora formateada (`12:20`) sujeta a cómo se derive el huso horario respecto a `ahora()`
- **Ubicación**: `skills/orquestar/test_estado_agentes.py` (líneas 40, 76-82).
- **para**: `desarrollador`
- **destino**: `descartar`
- **Detalle**: El test fija `motor.ahora` en `'2026-10-23T12:00:00+00:00'`, inyecta el evento de cuota en `'2026-10-23T13:50:00+02:00'` (`11:50 UTC` + `1800 s` = `12:20 UTC`) y comprueba `self.assertIn('12:20', output)`. Siempre que la implementación formatee la hora de vencimiento en la zona horaria del instante devuelto por `ahora()` (y no llamando a `.astimezone()` del sistema operativo sin zona explícita), el test será 100 % independiente del huso horario de la máquina donde corra.
