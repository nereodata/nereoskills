# Revisión de Pruebas: T-ADV-0015

- **Tarea**: `docs/plan/tasks/T-ADV-0015-control-remoto-bucle-y-metricas-en-telegram.md`
- **Archivo de pruebas**: `skills/telegram_gateway/test_gateway_control.py`
- **Especificación de referencia**: `tests/features/telegram_gateway.feature` (`@T-ADV-0015`, líneas 125-182)
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.6 / 10**

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Cobertura** | 9.5/10 | Los 11 tests cubren los 8 escenarios `@T-ADV-0015` y el triaje: `/parar` y `/stop` con y sin bucle en marcha, orden entre `motor.excluir` y `orquestar.parar`, `/lanzar` y `/run@AdevvBot` con anuncio de paso y aislamiento de `sys.argv` del gateway, preservación de argumentos CLI en `motor.en_fondo`, propagación de `OSError` al lanzar, bloqueo si ya existe `orquestar.pid`, `/metricas` por defecto (`ultima`) y con filtros (`v0.3,v0.4`, `last:2`, `todas`, `v0.3`), errores de filtro/JSONL corrupto sin resultados parciales, `/ayuda` y rechazo previo a disco para usuarios no autorizados. |
| **Aserciones** | 9.5/10 | Verifican efectos reales y observables: orden temporal de `excluir` antes de crear la señal (`side_effect` comprobando `assertFalse(senal.exists())`), conservación del `PID`, inmutabilidad byte a byte del árbol al consultar `/metricas`, valores numéricos exactos (`2.00 min`, `Dev E/C/S=100/20/30`, `Hades E/C/S=40/5/6`, `USD≈2.000000`) y argumentos exactos pasados a `Popen`. |
| **Rojo correcto** | 10/10 | Ejecución en rojo limpia (`Ran 11 tests in 0.060s`, `FAILED (failures=15)`): fallan exactamente los 9 métodos de los nuevos comandos porque aún derivan a `conversar` (`'CONVERSACION'`) o no figuran en `/ayuda`, mientras que la autorización previa y la regresión CLI de `en_fondo` pasan. |
| **Estabilidad** | 9.5/10 | Totalmente deterministas: directorios temporales aislados (`TemporaryDirectory`), sin procesos reales, red ni reloj del sistema. |

## Hallazgos

### 🔵 BAJA — Simulación de error de E/S acoplada a `Path.open`
- **Ubicación**: `skills/telegram_gateway/test_gateway_control.py` (líneas 160-161).
- **para**: `desarrollador`
- **destino**: `descartar`
- **Detalle**: El caso de error de lectura en `test_metricas_sin_datos_y_errores` parchea `Path.open` (`patch.object(Path, 'open', side_effect=OSError('lectura denegada'))`), lo cual funciona siempre que el cargador de tareas/métricas abra los ficheros mediante `Path.open()` o `Path.read_text()`, pero no interceptaría una llamada directa a la función integrada `open(ruta)`. Al reutilizarse el módulo de métricas existente que opera con `Path`, no requiere cambios.
