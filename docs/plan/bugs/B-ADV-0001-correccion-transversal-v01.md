---
id: B-ADV-0001
title: "Corrección transversal v0.1: resolución de rutas en sync, aislamiento de suite, lista blanca en versions y evaluar_tabla pura"
type: bug
weight: 10
version: "v0.1.0"
status: completed
created_at: 2026-10-22
updated_at: 2026-10-22
depende_de: []
origen: "revisar-version v0.1 (docs/review/versions/v0.1-arquitectura.md)"
---

# B-ADV-0001: Corrección transversal v0.1: resolución de rutas en sync, aislamiento de suite, lista blanca en versions y evaluar_tabla pura

## 🎯 Descripción del Fallo

La revisión transversal de arquitectura y código de la versión `v0.1` (`docs/review/versions/v0.1-arquitectura.md`, sobre `git diff main...release/v0.1`) detectó 4 hallazgos bloqueantes (`H-01`, `H-02` 🔴 CRÍTICO; `H-03`, `H-04` 🟠 ALTA) y 2 hallazgos menores con `destino: resolver` (`H-05` 🟡 MEDIA; `H-06` 🔵 BAJA) derivados de la interacción entre las tareas `T-ADV-0001` a `T-ADV-0005`:

1. **[H-01 · 🔴 CRÍTICO] `resolver_rutas_contenido` en `adevv/sync.py` no resuelve las rutas relativas limpiadas en `T-ADV-0003` para Codex y Antigravity**:
   - **Causa raíz**: En `T-ADV-0003` se eliminaron los prefijos `.agents/` y `../` de `agents/codex/*.toml` y `workflows/*.md`, dejando rutas relativas a la raíz del paquete (`agents/<rol>.md` y `skills/<nombre>/SKILL.md`). Sin embargo, `adevv/sync.py::resolver_rutas_contenido` (líneas 99–133, implementada en `T-ADV-0002`) solo busca patrones con prefijo `\.agents/` o `\.\./skills/`.
   - **Comportamiento observado vs esperado**: Al sincronizar el contenido real hacia `~/.codex/agents/*.toml` y `~/.gemini/config/workflows/*.md`, las rutas `agents/<rol>.md` y `skills/<nombre>/SKILL.md` quedan sin resolver a rutas absolutas de la versión instalada (`~/.adevv/versions/<V>/...`), incumpliendo `RF-F01-04`, `CA-F01-03` y `platform_plan.md §4`.
   - **Corrección requerida**: Actualizar `resolver_rutas_contenido` en `adevv/sync.py` para que, además de `.agents/` y `../skills/`, reemplace las referencias relativas `agents/<rol>.md` y `skills/<nombre>/SKILL.md` (usando lookbehind negativo como `(?<![/\w.-])` para no duplicar el prefijo cuando ya llevan `.agents/`, `../` o ruta absoluta) por `{posix_root}/agents/<rol>.md` y `{posix_root}/skills/<nombre>/SKILL.md`. Actualizar `tests/test_sync.py` para verificar también el formato real de `agents/codex/*.toml` y `workflows/*.md`.

2. **[H-02 · 🔴 CRÍTICO] Fallo de la suite completa (`python -m unittest discover -s tests`) por interferencia entre `T-ADV-0004`, `T-ADV-0002` y `T-ADV-0003` y contaminación de carpetas reales del usuario**:
   - **Causa raíz y fallos observados**:
     1. `test_ca_f01_01_primera_instalacion_actualiza_y_sincroniza` (`tests/test_install_and_release.py` l. 241) falla cuando `ORQUESTAR_PASO` está definido en el entorno del proceso porque `adevv/updater.py::evaluar_comprobacion_actualizacion` (l. 337) devuelve `DENTRO_DE_ORQUESTACION` incluso con `es_instalar=True`, y el test no limpia `ORQUESTAR_PASO`/`ADEVV_BOOTSTRAPPED` en su entorno simulado.
     2. `test_ca_f01_12_ver_que_version_hay_en_cada_arnes` (`tests/test_install_and_release.py` l. 363) falla sin `ORQUESTAR_PASO` porque `main_cli(["--version"])` ejecuta `evaluar_comprobacion_actualizacion`, que al no poder parsear `"hace 3 h"` como ISO consulta GitHub en vivo y sobrescribe `update_state.json` con un timestamp ISO y `"AL_DIA"`. Además, `updater.py` guarda `last_checked_status` con códigos en mayúsculas (`"AL_DIA"`), mientras que `comando_version` (`adevv/cli.py` l. 258–260) y `CA-F01-12` requieren formato legible (`"al día"`, `"aplicada"`, `"aplazada"`, `"fallida"`, `"sin red"`). Asimismo, en `test_ca_f01_10` y `test_ca_f01_11` se definió `"ORQUESTAR_PASO": ""` (que en Python evalúa a `False`).
     3. `TestCliCommands.setUp` (`tests/test_cli_commands.py` l. 64–68), `TestUpdaterUnit.setUp` (`tests/test_updater.py` l. 38–58) y `TestUpdaterIntegrationAndCli.setUp` (`tests/test_updater.py` l. 328–350) no aíslan `CLAUDE_HOME`, `CODEX_HOME` ni `AGY_HOME` (y `TestCliCommands` no desactiva las consultas de red en `setUp`), provocando que `sincronizar_destinos` y `_resincronizar_desfasados_al_arrancar` escriban en las carpetas reales del usuario (`~/.claude`, `~/.codex`, `~/.gemini/config`) e impriman `Claude Code sincronizado con la 0.3.0.` por `stdout`, rompiendo `test_ca_f02_01_adevv_orquestar_estado_matches_orquestar_py`.
   - **Corrección requerida**:
     - En `adevv/cli.py`: en `comando_version`, traducir los códigos de `last_checked_status` a texto legible en minúsculas (`AL_DIA` -> `"al día"`, `APLICADA` -> `"aplicada"`, `APLAZADA` -> `"aplazada"`, `FALLIDA` -> `"fallida"`, `SIN_RED` -> `"sin red"`, conservando valores ya legibles); y cuando se invoca únicamente `adevv --version` (sin subcomando), no ejecutar `evaluar_comprobacion_actualizacion` ni `_resincronizar_desfasados_al_arrancar` para que `--version` sea una consulta pura de estado sin efectos secundarios de red ni mutación de `update_state.json`.
     - En `adevv/updater.py`: en `evaluar_comprobacion_actualizacion`, comprobar `ORQUESTAR_PASO` / `ADEVV_BOOTSTRAPPED` solo cuando `not forzada and not es_instalar`.
     - En `tests/test_install_and_release.py`, `tests/test_cli_commands.py` y `tests/test_updater.py`: aislar siempre en `setUp` las variables `ADEVV_HOME`, `CLAUDE_HOME`, `CODEX_HOME`, `AGY_HOME` en directorios temporales y eliminar `ORQUESTAR_PASO` / `ADEVV_BOOTSTRAPPED` del entorno de prueba salvo en los tests que prueban específicamente `ORQUESTAR_PASO="task-dev"`.

3. **[H-03 · 🟠 ALTA] Materialización por lista blanca en `~/.adevv/versions/<V>/` e inicialización de `~/.adevv/versions/<actual>/` (`platform_plan.md §2`, `RF-F05-01`)**:
   - **Causa raíz**:
     1. `adevv/updater.py::instalar_version_publicada` extrae el `git archive` o copia el `git clone` completo en `staging_dir` sin filtrar por la lista blanca de distribución (`RF-F05-01`, `adevv._build`), colando `docs/`, `tests/`, `task_config.yaml`, etc. en `~/.adevv/versions/<V>/`.
     2. Si el usuario ejecuta `adevv instalar` cuando ya está en la última versión (o sin versión remota más nueva), nunca se inicializan `~/.adevv/versions/<actual>/` ni `~/.adevv/active.json`, dejando las rutas sincronizadas apuntando fuera de `~/.adevv/versions/<V>/`.
   - **Corrección requerida**:
     - Filtrar el contenido de `staging_dir` en `instalar_version_publicada` conservando únicamente los archivos permitidos por la lista blanca de `adevv._build` (`WHITELIST_DIRS`: `adevv`, `skills`, `agents`, `workflows`; `WHITELIST_FILES`: `pyproject.toml`, `README.md`, `LICENSE`; excluyendo archivos prohibidos según `is_forbidden`).
     - En `adevv/cli.py::comando_instalar` (o al inicializar el almacén en `store.py`/`cli.py`), si tras la comprobación de actualización no existe `active.json` o no existe el directorio `~/.adevv/versions/<version>/` (y el origen no es `"desarrollo"`), materializar la versión actual filtrada por lista blanca en `~/.adevv/versions/<version>/` y escribir `active.json` antes de llamar a `sincronizar_destinos`.

4. **[H-04 · 🟠 ALTA] Cumplimiento de la Regla 1 de capas (`updater.evaluar_tabla` pura) y eliminación de duplicación transversal**:
   - **Causa raíz**:
     1. `platform_plan.md §4` (Regla 1) exige que `updater.evaluar_tabla` reciba el estado y el reloj (`ahora`) por parámetro y devuelva estructuras de datos puras antes de tocar red o disco. Actualmente solo existe `evaluar_comprobacion_actualizacion` acoplada a E/S.
     2. `adevv/release_tools.py::obtener_versiones_publicadas` duplica `git ls-remote --tags` aceptando etiquetas ligeras y ordenando lexicográficamente (`sorted`), divergiendo de `updater.consultar_versiones_publicadas` (que filtra etiquetas anotadas `^{}` y ordena por semver).
     3. La detección de symlinks/junctions NTFS está triplicada en `adevv/_build.py::_is_symlink_or_junction`, `adevv/sync.py::es_enlace` y `adevv/migrate.py::info_enlace`.
     4. En `skills/orquestar/orquestar.py::validar_lanzamiento_bucle` (l. 238–254), `nombres_distribuidos` no incluye el alias con guion `telegram-gateway` (`DEC-P05`) ni escanea `agents/codex/*.toml`.
   - **Corrección requerida**:
     - Extraer y exponer en `adevv/updater.py` la función pura `evaluar_tabla(state, config, active_info, ahora, forzada=False, es_instalar=False, dentro_orquestacion=False)` que evalúe las condiciones previas a la red y devuelva una estructura pura (`dict` con la decisión), invocándola desde `evaluar_comprobacion_actualizacion`.
     - Hacer que `release_tools.obtener_versiones_publicadas` reutilice la lógica de etiquetas anotadas y ordenación semver (o comparta helper en `store.py`/`_build.py`).
     - Centralizar la detección de enlaces simbólicos y junctions NTFS en `adevv/_build.py` (o `adevv/store.py`) y reutilizarla desde `_build.py`, `sync.py` y `migrate.py`.
     - En `skills/orquestar/orquestar.py::validar_lanzamiento_bucle`, añadir `"telegram-gateway"` cuando exista `"telegram_gateway"` en `nombres_distribuidos` (`DEC-P05`) e incluir `agents/codex/*.toml`.

5. **[H-05 · 🟡 MEDIA (`destino: resolver`)] `README.md` incluye `pip install adevv` desde PyPI**:
   - En `README.md` (líneas 109–112, sección `## 🛠️ Integración en proyectos consumer`), sustituir `pip install adevv` por la orden de instalación desde el origen Git fijo (`pip install --user git+https://github.com/nereodata/nereoskills.git@v0.1.0 && adevv instalar`).

6. **[H-06 · 🔵 BAJA (`destino: resolver`)] Imports sin usar en `adevv/cli.py`**:
   - Eliminar los imports no utilizados en `adevv/cli.py` (`obtener_versiones_publicadas`, etc.).

## 📋 Triaje de Alcance

- [x] **Subfase A: Definición** [SKIP]: Criterios de aceptación y BDD existentes cubren los requisitos.
- [x] **Subfase B: Diseño** [EXEC]: Estructurado en `docs/design/B-ADV-0001-design.md`.
- [x] **Subfase C: Desarrollo** [EXEC]: Fase Red verificada y aprobada por Hades (`review-test` APROBADO 9.5/10), y Fix completado con verde limpio.
- [x] **Subfase D: QA** [EXEC]: Revisión por Hades completada (`review-code` APROBADO 9.42/10 en `docs/review/code_reviews/B-ADV-0001-code-review.md`).
- [x] **Subfase E: Documentación** [EXEC]: Corregida instrucción de instalación consumer en `README.md`.
- [x] **Subfase F: Cierre** [EXEC]: Bug cerrado a `completed` y commit semántico `fix(B-ADV-0001)`.

**Verificación al cierre**: `python -m unittest tests/test_sync.py tests/test_updater.py tests/test_cli_commands.py tests/test_install_and_release.py tests/test_orquestar.py` (ejercita la resolución de rutas en sync, la pureza y aislamiento del updater, los comandos de la CLI sin efectos colaterales, los criterios de aceptación E2E y el validador de orquestación).

## 📋 Reproducir

1. Ejecutar la suite completa con `ORQUESTAR_PASO` definido:
   `python skills/orquestar/orquestar.py --verificar "python -m unittest discover -s tests"`
   → Falla `test_ca_f01_01_primera_instalacion_actualiza_y_sincroniza`.
2. Ejecutar la suite completa sin `ORQUESTAR_PASO`:
   `$env:ORQUESTAR_PASO = $null; python -m unittest discover -s tests`
   → Fallan `test_ca_f02_01_adevv_orquestar_estado_matches_orquestar_py` y `test_ca_f01_12_ver_que_version_hay_en_cada_arnes`.
3. Inspeccionar el resultado de `resolver_rutas_contenido("agents/codex/hades.toml", Path("agents/codex/hades.toml").read_bytes(), Path("/tmp/v0.1.0"))`:
   → Mantiene `agents/hades.md` y `skills/<nombre>/SKILL.md` relativos en lugar de `/tmp/v0.1.0/agents/hades.md` y `/tmp/v0.1.0/skills/<nombre>/SKILL.md`.

## 📋 Evidencias

- Reporte transversal de Hades: `docs/review/versions/v0.1-arquitectura.md`
- Registro de evidencias: `orquestar_evidencias.jsonl` (líneas 20 y 21 con `codigo: 1` en `python -m unittest discover -s tests`).
