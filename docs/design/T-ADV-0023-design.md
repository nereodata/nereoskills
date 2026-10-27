# T-ADV-0023 · Cierre confirmado desde Telegram

Se conservan sin cambios los escenarios aprobados. El gateway autoriza al remitente antes de interpretar `/cerrar`. Sin `confirmo` devuelve el resumen compartido con los avisos de versión. Una función de cierre recibe el motor, valida rama exacta, PID, señal de parada, backlog completed/cancelled, revisiones, estado PARAR final de esa versión, manifiestos, changelog y preflight.

## Cambios

- Nuevo `skills/telegram_gateway/cierre_version.py`: resumen, precondiciones y transacción Git no interactiva con timeout. Usa el parser YAML disponible del paquete y el validador existente de manifiestos.
- Gateway: comando y ayuda; motor de orquestación: adjuntar resumen a los avisos finales. La lógica del resumen vive en un único módulo.
- Pruebas en `skills/telegram_gateway/test_cierre_version.py`, con Git y remoto bare locales; solo arranque y transporte simulados.

## Publicación y recuperación

Preparar el merge en un worktree temporal separado del checkout del usuario, basado en main local actualizado por fast-forward contra main remoto. Crear etiqueta anotada y publicar mediante un único push atómico explícito de main y etiqueta, sin force. Ante fallo eliminar solo la etiqueta recién creada y el worktree; main, release, índice y archivos originales no cambian. Tras éxito actualizar main local, cambiar a main y eliminar release. No revertir una publicación por fallo de arranque; responder con `/lanzar`. FIN no crea procesos. El preflight se ejecuta en el worktree para aislar sus escrituras.

## Mapa de impacto

- `responder`: consumidores `escuchar`, CLI y tests del gateway conservan los contratos anteriores; se añade una rama de comando después de autorización.
- `avisar`: consumidores del bucle y tests conservan firma, filtrado y transporte; solo evento version cuyo texto anuncia revisión final adjunta resumen. No añade lecturas al polling ni a otros eventos. La regresión dirigida comprueba consumidores existentes.
- `estado`, `backlog`, `decision_producto`, `en_fondo` se reutilizan sin cambiar sus contratos. Como el gateway, `estado` se invoca desde la raíz del proyecto; las pruebas restauran el cwd. Todas las operaciones Git del nuevo módulo sí llevan cwd explícito.
- Ninguna decisión de arquitectura contradicha. DEC-T23-03 sustituye únicamente el push separado del ejemplo manual de release para esta entrada automática. No hay conversiones horarias.

## Verificación

Ajustes menores de QA: carga del módulo de cierre bajo demanda y parser YAML del motor, sin dependencia nueva para el bucle. Timeout de preflight configurable mediante `release.preflight_timeout` (600 s por defecto, positivo y finito); Git mantiene 120 s. No se altera el mecanismo de credenciales almacenadas.

Solo el comando del triaje y compilación/diff. Pruebas de rechazo discriminan cada motivo sobre base elegible, comparan refs, archivos e índice; éxito verifica merge, etiqueta anotada y remoto, y continuación. Conflicto y rechazo remoto deben preservar el estado original.
