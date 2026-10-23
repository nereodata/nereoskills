# Revisión de Código (`review-code` — Ronda 2): T-ADV-0004

- **Tarea**: T-ADV-0004 — Actualización automática de versiones publicadas
- **Diseño de referencia**: `docs/design/T-ADV-0004-design.md`
- **Plan de plataforma**: `docs/requirements/platform_plan.md` (`DEC-P01`, `DEC-P02`, `DEC-P06`, `DEC-P07`)
- **Archivos auditados**:
  - `adevv/updater.py`
  - `adevv/processes.py`
  - `adevv/cli.py`
- **Veredicto**: **APROBADO**

## Análisis Estático y Evidencias

- **`git diff --check`**: Limpio, sin errores de formato ni espacios en blanco residuales.
- **`python -m py_compile`**: Sintaxis e importaciones válidas en `adevv/updater.py`, `adevv/processes.py` y `adevv/cli.py`.
- **Comentarios y docstrings**: Sin comentarios inline en los tres módulos; docstrings presentes y precisos en todos los módulos, clases y funciones públicas.

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Corrección** | 9.5 / 10 | Máquina de estados de los 9 resultados conforme a `requirements.md §4`; distinción exacta entre `SIN_RED` y `FALLIDA`, actualización de `last_checked_at` y `last_checked_status`, y validación del commit descargado. |
| **Seguridad** | 9.5 / 10 | Invocaciones a Git sin `shell=True` ni prompts interactivos (`GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`, `GIT_ASKPASS=echo`), extracción con `filter="data"`, validación en directorio temporal `.staging-<version>-<pid>` y conmutación atómica. |
| **Conformidad** | 9.5 / 10 | Alineado con `docs/design/T-ADV-0004-design.md` y el plan de plataforma (`DEC-P01`, `DEC-P02`, `DEC-P06`, `DEC-P07`), incluyendo carga dinámica del `sync.py` entrante, tratamiento de `adevv instalar` y exclusión del árbol de ancestros. |
| **Calidad** | 9.0 / 10 | Separación clara de responsabilidades entre `updater.py`, `processes.py` y `cli.py`, tipado explícito y manejo controlado de errores. |
| **Eficiencia** | 9.0 / 10 | Consulta ligera mediante `git ls-remote --tags` con timeout de 5 s, clonado superficial (`--depth 1`) y limpieza selectiva de versiones antiguas sin uso. |
| **Documentación** | 9.5 / 10 | Docstrings completos en la API pública y cero comentarios inline residuales. |
| **Media** | **9.33 / 10** | **APROBADO** (media > 8, sin hallazgos 🔴 ni 🟠) |

---

## Reevaluación de Hallazgos de la Ronda 1

- **H-01 [CRÍTICO]**: `resuelto` — Se importa `tempfile` en `adevv/updater.py`, la descarga y la verificación de versión (`_read_package_version_from_dir`) se realizan en un directorio temporal de staging (`.staging-<target_version>-<pid>`), se verifica el `commit_hash` mediante `git rev-parse HEAD` tras clonar, y la promoción a `versions/<target_version>` se ejecuta con `os.replace` antes de actualizar `active.json`.
- **H-02 [CRÍTICO]**: `resuelto` — El timeout de 180 s en instalación se clasifica como `FALLIDA` y los errores de descarga (`CalledProcessError`) como `SIN_RED`; `FALLIDA` registra `last_checked_at` y `last_checked_status`; todos los estados contados (`AL_DIA`, `APLAZADA`, `APLICADA`, `FALLIDA`) persisten `last_checked_status`; y `comando_actualizar(target_version)` limpia `aplazada`.
- **H-03 [ALTA]**: `resuelto` — `main_cli` informa `es_instalar=(parsed.subcommand == "instalar")` a `evaluar_comprobacion_actualizacion`, omitiendo la fila `ESPERA` y emitiendo el aviso de `SIN_RED` en `adevv instalar`; `instalar_version_publicada` carga e invoca dinámicamente el módulo `sync.py` de la versión entrante instalada en `target_dir`.
- **H-04 [ALTA]**: `resuelto` — `detectar_procesos_adevv` construye el mapa `PID -> PPID` y excluye toda la cadena de procesos ancestros tanto en Windows como en POSIX; `_inferir_cwd_proceso` obtiene la carpeta de trabajo desde `runtime/<pid>.json`, `--root`, `--cwd` o la ruta de invocación de scripts `.agents/skills/...`.
- **H-05 [MEDIA]**: `resuelto` — `peeled_regex` exige prefijo estricto `v` (`refs/tags/v(\d+\.\d+\.\d+)\^\{\}`) y se eliminó el comentario inline residual en `adevv/processes.py`.

## Hallazgos Nuevos

Sin hallazgos nuevos.
