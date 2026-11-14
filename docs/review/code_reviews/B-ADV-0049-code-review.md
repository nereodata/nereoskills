**Veredicto:** APROBADO
Producto revisado: f05cccb0cee8093eeb459a5ff545a81ccf30aee047938a812fb9bf3ad83b93e6
Rechazo reevaluado: 0b0cf36f0e206978cb09cb780fd581a239ff17a4

# Code Review · B-ADV-0049

## Resumen de verificación

- **Calidad determinista (`adevv orquestar --calidad --base 5d5f035`)**: comprobada en verde sin `--aplicar`, reutilizando las evidencias vigentes sobre el árbol `ae6d1a1da6` sin relanzar la batería ya acreditada.
- **Reevaluación del rechazo previo (`0b0cf36f0e206978cb09cb780fd581a239ff17a4`, rango `5d5f035..55322a9`)**:
  - **H-05 (Resuelto)**: `_servidores_mcp_proyecto_codex()` clasifica cada servidor externo declarado en `.codex/config.toml` según su transporte (`http` frente a `stdio`) y `config_mcp_codex()` emite entradas deshabilitadas con transporte válido y sin colisión de esquema (`{enabled=false,url="http://127.0.0.1:1"}` o `{enabled=false,command=<python>,args=[]}`), acompañadas de `--skip-git-repo-check` bajo `--ignore-user-config`. Verificado también contra el validador real de `codex-cli` con `--strict-config` tanto en `codex exec` y `codex exec resume` como en escenario de fusión con `.codex/config.toml`. En `tests/test_conversacion_telegram_lectura.py`, `_validar_esquema_mcp_codex()` exige transporte válido y sin mezcla `stdio`/`http` en todas las tablas de `mcp_servers` (incluidas `enabled=false`), y `test_ca4`/`test_ca5` cubren servidores locales y remotos además del control negativo de regresión (`invalid transport`).
  - **H-01, H-02 y H-04 (Se mantienen resueltos)**: índice fresco y priorizado de ficheros legibles por turno para `agy` sin enlaces simbólicos/binarios/secretos, tolerancia a `null` y validación de tipos en el servidor MCP stdio sin derribar el proceso, y evaluación directa de las políticas `--settings` reales sin código muerto en producción.
- **Criterios de aceptación (`CA1`–`CA6`) y bordes de seguridad**:
  - Consulta de solo lectura confinada a la raíz del proyecto en `claude`, `codex` y `agy`, con citación de fuentes y relectura efectiva desde disco en turnos sucesivos, denegando escrituras, borrados, ejecución de comandos, control de procesos, red, enlaces simbólicos/junctions y lectura de `.env*`/`.git`.
  - Limpieza aislada de `CODEX_WINDOWS_REGISTERED_CORE` en el entorno hijo de `codex` en Windows, conmutación a reservas ante cuota, suscripción deshabilitada, arnés ausente/no soportado o respuesta vacía, y comunicación honesta de `GatewayNoDisponible` cuando caen todos los candidatos.
  - `/estado`, el resto de comandos explícitos del gateway y `motor.base_comando_agente()` para roles internos permanecen intactos, sin tráfico real hacia Telegram en las pruebas.

Sin hallazgos abiertos.
