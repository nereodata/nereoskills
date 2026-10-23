# Test Review: B-ADV-0001 (Ronda 2)

- **Bug**: B-ADV-0001 — Corrección transversal v0.1: resolución de rutas en sync, aislamiento de suite, lista blanca en versions y evaluar_tabla pura
- **Archivos auditados**:
  - `tests/test_sync.py`
  - `tests/test_updater.py`
  - `tests/test_cli_commands.py`
  - `tests/test_install_and_release.py`
- **Veredicto**: **APROBADO**

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Cobertura** | 10 / 10 | Cubre íntegramente H-01, H-02, H-03 (incluyendo `instalar_version_publicada` y `adevv instalar` cuando está al día) y todos los puntos de H-04 (`evaluar_tabla` pura con sus ramas, `obtener_versiones_publicadas` con filtro y orden semver, y alias `telegram-gateway` en colisión local). |
| **Aserciones** | 9 / 10 | Aserciones precisas y consistentes con el resto de la suite: se resolvió la colisión con `@CA-F01-11` en `test_h02` y se añadieron comprobaciones de delimitadores y conteo exacto de prefijo en `test_h01`. |
| **Rojo correcto** | 9 / 10 | Todas las pruebas nuevas y ampliadas fallan por ausencia del comportamiento esperado sin errores espurios de sintaxis o colección. |
| **Estabilidad** | 10 / 10 | Entorno de pruebas completamente aislado (`ADEVV_HOME`, `CLAUDE_HOME`, `CODEX_HOME`, `AGY_HOME`, `ORQUESTAR_PASO`, `ADEVV_BOOTSTRAPPED` y `auto_update: False` en `TestCliCommands.setUp`). |
| **Media** | **9.5 / 10** | **APROBADO** (sin hallazgos 🔴 ni 🟠 pendientes) |

---

## Reevaluación de Hallazgos de la Ronda 1

- **[H-01] 🔴 CRÍTICO — Contradicción bloqueante entre `test_h02_version_es_consulta_pura_sin_efectos_secundarios` y `test_ca_f01_10` / `test_ca_f01_11` (`@CA-F01-11`)**: `resuelto`. Se retiró la aserción sobre `_resincronizar_desfasados_al_arrancar` y se verifica que `adevv --version` no invoca `evaluar_comprobacion_actualizacion`, manteniendo la compatibilidad con `@CA-F01-11`.
- **[H-02] 🟠 ALTA — Cobertura incompleta de `H-03` y `H-04`**: `resuelto`. Se añadieron `test_h03_adevv_instalar_materializa_version_local_cuando_esta_al_dia` (`tests/test_updater.py`), las ramas `DESARROLLO`, `APLAZADA` y `ESPERA` (< 24 h y < 1 h) en `test_h04_evaluar_tabla_pura` (`tests/test_updater.py`), `test_h04_obtener_versiones_publicadas_filtro_y_orden_semver` (`tests/test_install_and_release.py`) y el caso `(".claude/skills/telegram-gateway", True)` en `test_ca_f02_07` (`tests/test_cli_commands.py`).
- **[H-03] 🟡 MEDIA — `assertIn` de ruta en `test_h01` daría falso positivo ante duplicación de prefijo**: `resuelto`. Se comprueban delimitadores exactos, conteo de ocurrencias del prefijo y un caso mixto con `.agents/`, ruta ya absoluta y `../` (`tests/test_sync.py`).
- **[H-04] 🔵 BAJA — `TestCliCommands.setUp` no fija `auto_update: False` en el almacén temporal**: `resuelto`. Se inicializa `set_config({"auto_update": False})` en `TestCliCommands.setUp` (`tests/test_cli_commands.py`).

## Hallazgos Nuevos

Sin hallazgos nuevos.
