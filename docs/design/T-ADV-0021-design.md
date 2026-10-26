# Diseño técnico: T-ADV-0021

Reutilizar `consumo_cuotas(root, fecha_estado(ahora()))[1]`, que ya excluye eventos futuros y agotamientos caducados. Un helper compartido seleccionará las configuraciones sin agotamiento vigente en orden original; conservará la última si todas están agotadas y el titular cuando no haya reservas. Una lectura del JSONL por selección, sin persistencia nueva.

## Cambios y mapa de impacto

- `skills/orquestar/orquestar.py`: nuevo helper usado por `agente()` (CLI `--agente`) y `bucle()` (pasos del motor). Ambos necesitan el comportamiento nuevo; no cambian firmas públicas ni formatos persistidos. Con `--harness` o `--cmd` el bucle conserva la selección previa: el comando efectivo puede ignorar los modelos del perfil, por lo que no se infiere su clave de cuota.
- `skills/orquestar/metricas.py`: `agregar()` incrementa llamadas de Hades solo sin marcas activas de cuota y sin `modelos: {}` explícito. Ausencia de `modelos` o `None` conserva compatibilidad histórica. Rechazos, tokens, costes, tiempos y veredictos permanecen como antes.
- Consumidores de `agregar()`: `consultar()` y pruebas directas; `mostrar()` publica el contador en tabla/CSV, también consumido por Telegram a través de la consulta de métricas. Todos requieren el contador corregido, sin cambio de esquema.
- Tests existentes: `tests.test_orquestar.ReservaCuotaTests`, `skills/orquestar/test_metricas.py` y `test_estado_agentes.py` siguen válidos y no se modifican. Nuevas regresiones en `test_cuota_vigente.py` con JSONL temporal, reloj fijo y lanzadores simulados.
- Decisiones contradichas: ninguna; se mantiene DEC-P09 y la conmutación por cuotas del motor.
- Referencia temporal: fechas conscientes de zona horaria normalizadas por `fecha_estado`; el límite exacto de expiración deja de estar vigente.
- Camino frecuente: comprobar por mock que cada selección con reservas lee cuotas una sola vez y que sin reservas no lee el JSONL; sin red ni nuevos procesos.

La validación cubrirá invocaciones consecutivas reales de `agente()` con persistencia del primer agotamiento, expiración, reservas intermedias agotadas, todas agotadas, ausencia de reservas y selección efectiva en `bucle()`. Se verificará el conteo de llamadas para cada marca de rebote y se conservarán los rechazos incluso en registros históricos con marcas de cuota.
