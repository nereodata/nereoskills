# Code Review: B-ADV-0001 · Corrección transversal v0.1

- **Veredicto**: **APROBADO**
- **Bug**: [`B-ADV-0001`](../../plan/bugs/B-ADV-0001-correccion-transversal-v01.md)
- **Diseño técnico**: [`docs/design/B-ADV-0001-design.md`](../../design/B-ADV-0001-design.md)
- **Reporte de origen**: [`docs/review/versions/v0.1-arquitectura.md`](../versions/v0.1-arquitectura.md)

---

## 1. Análisis Estático y Evidencia

- **Compilación (`python -m py_compile`)**: Limpio sobre todos los módulos del delta (`adevv/_build.py`, `adevv/sync.py`, `adevv/migrate.py`, `adevv/updater.py`, `adevv/cli.py`, `adevv/release_tools.py`, `skills/orquestar/orquestar.py`).
- **Formato y espaciado (`git diff --check`)**: Limpio, sin conflictos ni errores de espaciado.
- **Evidencia de verificación (`orquestar_evidencias.jsonl`)**: Verificación registrada en verde (`codigo: 0`, árbol `bc32075cc6e6877c79140c1f8d625f48957b06fa`, 88 tests ejecutados sobre `test_sync.py`, `test_updater.py`, `test_cli_commands.py`, `test_install_and_release.py` y `test_orquestar.py`).

---

## 2. Verificación de Resolución de Hallazgos Previos (`v0.1-arquitectura.md`)

| ID | Hallazgo original | Estado | Verificación en el delta |
|---|---|---|---|
| **H-01** (🔴) | `resolver_rutas_contenido` no resolvía las rutas relativas limpiadas en `T-ADV-0003` para Codex y Antigravity | `resuelto` | `adevv/sync.py` (l. 111–145) incorpora expresiones regulares con lookbehind negativo `(?<![/\w.-])` para transformar `agents/<rol>.md`, `skills/<nombre>/SKILL.md` y el placeholder `skills/<nombre>/SKILL.md` a `{posix_root}/...` sin duplicar prefijos existentes. |
| **H-02** (🔴) | Interferencia en la suite completa (`ORQUESTAR_PASO` en `instalar`, mutación de red en `--version`, formato de `last_checked_status` y falta de aislamiento de arneses) | `resuelto` | `adevv/cli.py` omite `evaluar_comprobacion_actualizacion` cuando no hay subcomando (`--version`) y traduce `last_checked_status` a minúsculas legibles (`al día`, `aplicada`, `aplazada`, `fallida`, `sin red`); `adevv/updater.py` permite evaluar cuando `es_instalar=True` o `forzada=True` aunque `ORQUESTAR_PASO` esté activo. |
| **H-03** (🟠) | `instalar_version_publicada` no filtraba por lista blanca y `adevv instalar` no materializaba `versions/<V>/` ni `active.json` cuando estaba al día | `resuelto` | `adevv/updater.py` implementa `filtrar_por_lista_blanca` y `materializar_version_local` usando `WHITELIST_DIRS`, `WHITELIST_FILES` e `is_forbidden` de `adevv._build`; `adevv/cli.py::comando_instalar` inicializa la versión local cuando falta `active.json` o `versions/<V>/`. |
| **H-04** (🟠) | Incumplimiento de la Regla 1 de capas (`evaluar_tabla` pura) y duplicación de lógica entre módulos | `resuelto` | `adevv/updater.py` extrae la función pura `evaluar_tabla`; `adevv/_build.py` expone `is_symlink_or_junction` reutilizada en `sync.py` y `migrate.py`; `release_tools.obtener_versiones_publicadas` delega en `updater.consultar_versiones_publicadas`; `orquestar.py::validar_lanzamiento_bucle` incluye `agents/codex/*.toml` y `telegram-gateway`. |
| **H-05** (🟡) | `README.md` incluía `pip install adevv` en §Integración en proyectos consumer | `resuelto` | `README.md` (l. 111) usa la URL Git con etiqueta fija `pip install --user git+https://github.com/nereodata/nereoskills.git@v0.1.0`. |
| **H-06** (🔵) | Imports sin uso en `adevv/cli.py` | `resuelto` | Eliminados los imports no utilizados en `adevv/cli.py`. |

---

## 3. Puntuaciones (1-10)

| Criterio | Puntuación | Justificación |
|---|---|---|
| **Corrección** | **9.5/10** | La resolución de rutas cubre todos los formatos de `agents/codex/*.toml` y `workflows/*.md`; la evaluación de la tabla de actualización es pura y determinista; la materialización inicial y el filtrado por lista blanca funcionan de extremo a extremo. |
| **Seguridad** | **9.5/10** | Uso consistente de `is_symlink_or_junction` sin seguir enlaces simbólicos ni junctions NTFS; filtrado estricto por lista blanca al materializar versiones en `~/.adevv/versions/<V>/`; llamadas a Git sin prompts interactivos (`GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`). |
| **Conformidad** | **9.5/10** | Cumple el diseño técnico `B-ADV-0001-design.md` (`DEC-D01` a `DEC-D06`) y las reglas de arquitectura de `platform_plan.md §4` (Regla 1 de función pura `evaluar_tabla` y Regla 2 de capas sin dependencias inversas). |
| **Calidad** | **9.0/10** | Código claro, cohesivo, sin duplicación de detección de enlaces ni de consulta de etiquetas remotas, y sin código muerto. |
| **Eficiencia** | **9.5/10** | `adevv --version` evita consultas de red innecesarias; operaciones acotadas con timeouts y escrituras atómicas. |
| **Documentación** | **9.5/10** | Docstrings claros en las funciones públicas nuevas y `README.md` alineado con el modelo de distribución sin PyPI. |
| **Media** | **9.42/10** | **APROBADO** (media > 8, 0 hallazgos 🔴/🟠). |

---

## 4. Hallazgos

### 🔵 [B-ADV-0001-C01] `migrate._obtener_nombres_distribuidos` no añade el alias `telegram-gateway`
- **Severidad**: 🔵 BAJA
- **destino**: `descartar`
- **Archivo afectado**: `adevv/migrate.py` (líneas 55–85)
- **Descripción**:
  Mientras que `skills/orquestar/orquestar.py::validar_lanzamiento_bucle` (líneas 259–260) añade `"telegram-gateway"` cuando `"telegram_gateway"` está en los nombres distribuidos (`DEC-P05`), `adevv/migrate.py::_obtener_nombres_distribuidos` solo añade el nombre de carpeta (`telegram_gateway`). Riesgo práctico nulo en los repositorios actuales porque la carpeta del submódulo siempre se llamó `telegram_gateway`.
