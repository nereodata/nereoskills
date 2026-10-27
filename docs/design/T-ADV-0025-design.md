# Diseño técnico: T-ADV-0025

## Arquitectura y cambios

- **[MODIFY]** `skills/orquestar/orquestar.py`: extraer en un resolver único la carpeta `ADEVV_HOME/versions/<ver>`; usarlo para la firma de versión y la recarga. Leer versiones de `pyproject.toml` y `task_config.yaml` antes de devolver `desconocida`, continuando con YAML si un candidato TOML no se puede leer. Centralizar comprobación de PID vivo y propiedad, parametrizada por nombre de archivo, para ambos motores. Delegar la lectura compatible de métricas y la clave de versión a `metricas.py`. Retirar `detalle_estado`.
- **[MODIFY]** `skills/orquestar/metricas.py`: definir las utilidades canónicas de clave de versión y lectura JSONL, conservando el modo tolerante para registros incompletos que usa el bucle y el modo estricto de la exportación. Delimitar por saltos físicos LF para preservar separadores Unicode válidos dentro de cadenas JSON.
- **[MODIFY]** `skills/telegram_gateway/gateway.py`: usar las utilidades de PID de `orquestar.py`, manteniendo los nombres públicos del módulo como alias finos para compatibilidad de sus llamantes y pruebas.
- **[MODIFY]** pruebas unitarias de orquestar/gateway: cubrir manifiestos, resolver compartido, PID vivo/propiedad simétricos, lectura de métricas y sustituir pruebas del helper retirado por `informe_agentes`.

## Mapa de impacto

- `version_adevv` y `version_activa_distinta` consumen el resolver de almacén; se conserva su contrato de retorno. Solo cambia el último fallback de firma: la versión de manifiestos o `desconocida`.
- `gateway.pid_vivo`, `gateway.es_propietario_pid`, reserva/limpieza/escucha y los puntos de arranque/cierre en `orquestar.py` comparten helpers parametrizados. Los dos PID conservan la misma semántica para PID inválidos, muertos, vivos y propiedad del proceso actual.
- `orquestar.vkey` conserva su firma como alias de `metricas.clave_version_numerica`; `leer_metricas` conserva su tolerancia a una última línea parcial. La exportación sigue rechazando JSONL inválido con número de línea.
- `detalle_estado` no tiene llamantes de producción. `skills/orquestar/test_estado_agentes.py` deja de invocarlo y valida el informe operativo soportado `informe_agentes`.
- No se contradice ninguna decisión de plataforma. No cambian escenarios funcionales ni salidas, salvo la versión de firma cuando no se puede leer ninguna fuente instalada.
- Sin conversiones de unidades ni trabajo adicional en el camino caliente: los resolvers solo inspeccionan rutas al consultar versión; lectura JSONL mantiene un único recorrido.

## Pruebas

Ejecutar las pruebas localizadas del triaje: firma/manifiestos, recarga/resolución, métricas/JSONL (incluido U+2028), informe de agentes y ciclo de PID del gateway. La verificación final del árbol está anotada en la tarea.
