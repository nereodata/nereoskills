**Veredicto:** RECHAZADO
Producto revisado: db127ad623c3723ffe4ef42571c7e0f5c1f1aeb8242723fade1ff056cbd4682a

# Code Review · B-ADV-0049

## Resumen de verificación

- **Calidad determinista (`adevv orquestar --calidad --base 5d5f035`)**: verificada en verde reutilizando las evidencias vigentes sobre el árbol `94f518b6d4`, sin escrituras ni relanzamiento redundante de la batería de pruebas ya acreditada.
- **Reevaluación de hallazgos previos (`5d5f035..8e59fbe`)**:
  - **H-01 (Resuelto)**: `lector_proyecto.py` construye desde disco un índice fresco y priorizado por turno (`indice_ficheros_conversacion` / `formatear_indice_conversacion`) excluyendo `.env*`, `.git`, binarios y enlaces simbólicos/junctions; `gateway.py::construir_prompt()` lo inyecta en cada mensaje advirtiendo que `read_file` exige ruta de fichero regular; `SKILL.md` documenta el contrato real por arnés y `fake_harness.py` descubre rutas exclusivamente del índice del prompt tras comprobar `IsADirectoryError` sobre directorios en `agy`.
  - **H-02 (Resuelto)**: coerción explícita de `None`/`null` a valores por defecto, validación de tipos (`bool`, cadenas no enteras, no-strings) y captura de `TypeError` en `_procesar_mensaje_mcp()`, verificada sobre el proceso MCP stdio sin caída.
  - **H-04 (Resuelto)**: eliminado `evaluar_permiso_conversacion()` del módulo de producción y evaluadas directamente las políticas `--settings` reales en las pruebas.
  - **H-03 (Parcial — introduce regresión H-05)**: añadidos `--ignore-user-config`, `--ignore-rules`, `features.hooks=false` y `features.skip_host_skill_discovery=true` en `codex`, pero la neutralización añadida para `.codex/config.toml` provoca un fallo fatal de arranque en el binario real de `codex`.

## Hallazgos

- **H-05 · 🟠 ALTA (`para: desarrollador`) — `config_mcp_codex()` rompe el arranque de `codex` con `Error loading config.toml: invalid transport` cuando existe `.codex/config.toml` con `mcp_servers`**
  - **Ubicación**: `skills/telegram_gateway/lector_proyecto.py:526-550` y `tests/test_conversacion_telegram_lectura.py:160-163,832-836,885-895`.
  - **Detalle**: `config_mcp_codex()` añade `<servidor>={enabled=false}` sin campo de transporte (`command` o `url`) por cada entrada detectada en `<root>/.codex/config.toml`. Al invocar `codex exec` o `codex exec resume` con `--ignore-user-config`, Codex no carga `$CODEX_HOME/config.toml` (donde reside la confianza del repositorio) y, por tanto, tampoco carga `<root>/.codex/config.toml`; al deserializar el override inline `-c mcp_servers={..., "peligroso"={enabled=false}}`, el validador TOML de Codex exige un transporte válido en toda entrada de `mcp_servers` incluso con `enabled=false`, abortando de inmediato con `rc=1` y `Error loading config.toml: invalid transport in mcp_servers.<nombre>` (comprobado contra el binario real `codex`). Además, al ser un fallo con `codigo=1` sin marca de cuota, `gateway.conversar()` lanza `RuntimeError` sin conmutar a las reservas. Para que el override sea válido en `codex` tanto si `.codex/config.toml` se ignora como si llegara a fusionarse, no debe emitirse una tabla `mcp_servers.<extra>` sin transporte válido (p. ej., incluir un `command` inocuo junto a `enabled=false` y `args=[]`, o no inyectar entradas huérfanas), y el test simulado debe validar que toda entrada emitida en `mcp_servers` cumple el esquema de transporte de Codex.
