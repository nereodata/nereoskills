# Diseño Técnico: B-ADV-0001 · Corrección transversal v0.1

## 1. Resumen y Contexto
La revisión transversal de arquitectura y código de la versión `v0.1` (`docs/review/versions/v0.1-arquitectura.md`) identificó cuatro hallazgos de severidad alta/crítica (`H-01` a `H-04`) y dos hallazgos menores (`H-05` y `H-06`) derivados de la integración entre las tareas `T-ADV-0001` a `T-ADV-0005`.
El propósito de este diseño es resolver estos fallos de forma cohesiva, respetando los principios de diseño (SOLID, DRY, KISS, YAGNI), la Regla 1 de capas de `platform_plan.md §4` y el aislamiento total del entorno de pruebas frente al sistema del usuario.

---

## 2. Decisiones de Arquitectura y Diseño

### DEC-D01: Resolución canónica de rutas en agentes y workflows (`H-01`)
- En `adevv/sync.py::resolver_rutas_contenido`, las referencias relativas a `agents/<rol>.md` y `skills/<nombre>/SKILL.md` (limpiadas en `T-ADV-0003` para Codex y Gemini/Antigravity) deben transformarse a rutas absolutas POSIX dentro de la versión activa (`{posix_root}/agents/...` y `{posix_root}/skills/...`).
- Para evitar duplicar rutas si el contenido ya posee un prefijo (`.agents/`, `../skills/` o ruta absoluta `/` / `C:/`), se emplea lookbehind negativo:
  - `(?<![/\w.-])agents/([a-zA-Z0-9_\-]+)\.md`
  - `(?<![/\w.-])skills/([a-zA-Z0-9_\-]+)/SKILL\.md`
- Se preservan las reglas existentes de sustitución de `.agents/` y `../skills/` por retrocompatibilidad.

### DEC-D02: Pureza de `adevv --version` y desacoplamiento de red en orquestación (`H-02`)
- **Consulta pura**: Cuando la línea de órdenes es `adevv --version` o `adevv` sin subcomandos, el despachador ejecuta `comando_version` de forma directa sin llamar a `updater.evaluar_comprobacion_actualizacion` ni a `_resincronizar_desfasados_al_arrancar`. No hay llamadas a Git remoto ni modificaciones de `update_state.json`.
- **Traducción de estados**: `comando_version` traduce los códigos internos de `last_checked_status` a texto legible en minúsculas:
  - `AL_DIA` -> `"al día"`
  - `APLICADA` -> `"aplicada"`
  - `APLAZADA` -> `"aplazada"`
  - `FALLIDA` -> `"fallida"`
  - `SIN_RED` -> `"sin red"`
- **Prioridad en instalación**: `evaluar_comprobacion_actualizacion` evalúa `ORQUESTAR_PASO` y `ADEVV_BOOTSTRAPPED` únicamente cuando `not forzada and not es_instalar`. Si el usuario o el harness ejecuta explícitamente `adevv instalar`, la instalación/sincronización se procesa aunque el proceso esté bajo el bucle de orquestación.

### DEC-D03: Aislamiento hermético de arneses en pruebas unitarias e integración (`H-02`)
- Todas las suites de pruebas (`tests/test_install_and_release.py`, `tests/test_cli_commands.py`, `tests/test_updater.py`) deben garantizar en su `setUp`:
  - `ADEVV_HOME`: directorio temporal único por test case.
  - `CLAUDE_HOME`, `CODEX_HOME`, `AGY_HOME`: directorios temporales aislados para evitar escribir en `~/.claude`, `~/.codex` o `~/.gemini/config` del usuario real.
  - Desactivación o saneamiento de `ORQUESTAR_PASO` y `ADEVV_BOOTSTRAPPED` en el entorno simulado (salvo en pruebas que verifiquen explícitamente el comportamiento bajo orquestación).
  - Parcheo o stub de comandos remotos de red (`git ls-remote`, `git clone`) para evitar accesos remotos accidentales.

### DEC-D04: Materialización por lista blanca e inicialización en `adevv instalar` (`H-03`)
- `instalar_version_publicada` en `adevv/updater.py` aplica una función de saneamiento `filtrar_por_lista_blanca(staging_dir)`:
  - Conserva en la raíz únicamente los directorios en `WHITELIST_DIRS` (`adevv`, `skills`, `agents`, `workflows`) y archivos en `WHITELIST_FILES` (`pyproject.toml`, `README.md`, `LICENSE`).
  - Elimina de forma recursiva cualquier archivo o carpeta que cumpla `is_forbidden` (`__pycache__`, `.pyc`, `.pid`, `.log`, `.jsonl`).
- Al invocar `adevv instalar`, si el origen no es `"desarrollo"` y no existe aún el directorio `~/.adevv/versions/<version>/` o falta `active.json`, se materializa la versión base filtrada por lista blanca desde el paquete local en `~/.adevv/versions/<version>/` y se crea `active.json` antes de sincronizar los arneses.

### DEC-D05: Regla 1 de capas: función pura `evaluar_tabla` (`H-04`)
- De acuerdo con `platform_plan.md §4`, se extrae en `adevv/updater.py` la función pura:
  `evaluar_tabla(state, config, active_info, ahora, forzada=False, es_instalar=False, dentro_orquestacion=False) -> Dict[str, Any]`
  que calcula la decisión (estado resultante, mensaje, versión objetivo, si debe consultar remoto) sin realizar ninguna operación de entrada/salida (ni lectura de disco, ni llamadas a subprocess/Git, ni mutación de reloj).
- `evaluar_comprobacion_actualizacion` recopila los datos impuros (disco, entorno, reloj) y delega la decisión en `evaluar_tabla`.

### DEC-D06: Unificación de lógica transversal y DRY (`H-04`, `H-05`, `H-06`)
- **Detección de enlaces NTFS/POSIX**: Centralizada en `is_symlink_or_junction(path: Path) -> bool` en `adevv/_build.py`. Reutilizada por `adevv/sync.py::es_enlace` y `adevv/migrate.py::info_enlace`.
- **Consulta de versiones remotas**: `release_tools.obtener_versiones_publicadas` reutiliza `updater.consultar_versiones_publicadas` garantizando orden numérico semver y filtrado de etiquetas anotadas (`refs/tags/vX.Y.Z^{}`).
- **Alias de gateways y agentes en orquestador**: `skills/orquestar/orquestar.py::validar_lanzamiento_bucle` incluye `"telegram-gateway"` y escanea `agents/codex/*.toml`.
- **Integración consumer**: `README.md` se actualiza con `pip install --user git+https://github.com/nereodata/nereoskills.git@v0.1.0`.
- **Código muerto**: Eliminación de imports sin usar en `adevv/cli.py`.

---

## 3. Matriz de Cambios por Módulo

| Módulo | Tipo | Cambios Principales |
|---|---|---|
| `adevv/_build.py` | `[MODIFY]` | Exponer `is_symlink_or_junction(path)` de forma pública. |
| `adevv/sync.py` | `[MODIFY]` | Usar `is_symlink_or_junction`; actualizar regex en `resolver_rutas_contenido` con lookbehind negativo para `agents/<rol>.md` y `skills/<nombre>/SKILL.md`. |
| `adevv/migrate.py` | `[MODIFY]` | Reutilizar `is_symlink_or_junction` en `info_enlace`. |
| `adevv/updater.py` | `[MODIFY]` | Implementar función pura `evaluar_tabla`; ajustar evaluación de orquestación; implementar `filtrar_por_lista_blanca` y aplicarla en `instalar_version_publicada`. |
| `adevv/cli.py` | `[MODIFY]` | Limpiar imports; hacer `--version` consulta pura; traducir `last_checked_status` a minúsculas legibles; inicializar materialización en `comando_instalar` si falta `versions/<V>`. |
| `adevv/release_tools.py` | `[MODIFY]` | Reutilizar `consultar_versiones_publicadas` en `obtener_versiones_publicadas`. |
| `skills/orquestar/orquestar.py` | `[MODIFY]` | Incluir `telegram-gateway` y `agents/codex/*.toml` en `validar_lanzamiento_bucle`. |
| `README.md` | `[MODIFY]` | Corregir instrucción de instalación consumer en §Integración. |
| `tests/test_sync.py` | `[MODIFY]` | Probar resolución de rutas para formato real de `agents/codex/*.toml` y `workflows/*.md`. |
| `tests/test_updater.py` | `[MODIFY]` | Test unitario de `evaluar_tabla` pura; aislar variables de arneses y red en `setUp`. |
| `tests/test_cli_commands.py` | `[MODIFY]` | Aislar `CLAUDE_HOME`, `CODEX_HOME`, `AGY_HOME` y red en `setUp`; verificar `--version` pura. |
| `tests/test_install_and_release.py` | `[MODIFY]` | Aislar arneses y entorno en `setUp`. |
