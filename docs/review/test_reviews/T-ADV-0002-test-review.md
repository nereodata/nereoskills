# Revisión de Pruebas (`review-test`): T-ADV-0002

- **Tarea**: T-ADV-0002 — Instalación y sincronización con los arneses
- **Especificación BDD**: `tests/features/instalacion_y_sincronizacion.feature`
- **Diseño técnico**: `docs/design/T-ADV-0002-design.md`
- **Archivos auditados**:
  - `tests/test_sync.py`
  - `tests/test_install_and_release.py`
- **Veredicto**: **APROBADO**

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Cobertura** | 9.0 / 10 | Los 13 escenarios (`@CA-F01-01` a `@CA-F01-13`) están cubiertos entre `tests/test_sync.py` y `tests/test_install_and_release.py`, además de pruebas unitarias para la persistencia atómica y lectura tolerante en `adevv/store.py`. |
| **Aserciones** | 9.0 / 10 | Las aserciones verifican efectos reales en disco (creación/preservación/borrado no recursivo de archivos, ausencia de `.agents/` y `../`, rutas absolutas inyectadas, registros de huellas y salidas exactas de CLI). |
| **Rojo correcto** | 9.5 / 10 | Las 16 pruebas nuevas fallan limpiamente con `NotImplementedError` por ausencia de implementación en `adevv/store.py`, `adevv/sync.py`, `adevv/processes.py` y `adevv/cli.py`, manteniendo las pruebas de `T-ADV-0001` en verde. |
| **Estabilidad** | 9.5 / 10 | Uso consistente de `tempfile.TemporaryDirectory()`, repositorios Git `--bare` locales, aislamiento por variables de entorno (`ADEVV_HOME`, `CLAUDE_HOME`, `CODEX_HOME`, `AGY_HOME`) y mocks para procesos vivos. |
| **Media** | **9.25 / 10** | **APROBADO** (media > 8, sin hallazgos 🔴 ni 🟠) |

---

## Hallazgos

### 🔵 [H-01] `test_ca_f01_02` y `test_ca_f01_09`: cobertura directa de CLI en "sin confirmar" y caso de registro corrupto en sincronización
- **Severidad**: 🔵 BAJA
- **Destino**: `descartar`
- **Ubicación**: `tests/test_sync.py:162-180`, `tests/test_sync.py:323-346`
- **Detalle**:
  1. En `test_ca_f01_02_destino_sin_carpetas_confirmadas` se verifica `res["agy"]["detalle"] == "sin confirmar"` sobre el motor `sincronizar_destinos`, sin invocar `main_cli(["--version"])` para comprobar el formateo `"Antigravity: sin confirmar"` en la salida de CLI.
  2. En `test_ca_f01_09_destino_sin_registro_o_corrupto_adopta_identicos` se ejercita la variante sin registro (`no existe`), delegando la variante `está corrupto` del `Esquema del escenario` a la prueba unitaria `TestStore.test_corrupted_json_returns_default`.
- **Impacto**: Mínimo; ambos comportamientos subyacentes están verificados unitariamente y en las pruebas de CLI de `--version`.

### 🔵 [H-02] Imports no utilizados en `test_ca_f01_01_primera_instalacion_actualiza_y_sincroniza`
- **Severidad**: 🔵 BAJA
- **Destino**: `descartar`
- **Ubicación**: `tests/test_install_and_release.py:195-196`, `tests/test_install_and_release.py:229`
- **Detalle**: Se importan localmente `get_sync_registry`, `EstadoDestino`, `redirect_stdout` y `redirect_stderr` sin llegar a utilizarse dentro del método de prueba.
