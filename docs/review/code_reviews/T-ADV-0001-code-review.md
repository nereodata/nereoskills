# Revisión de Código (`review-code`): T-ADV-0001

- **Tarea**: T-ADV-0001 — Publicación de versiones sin contenido interno
- **Diseño de referencia**: `docs/design/T-ADV-0001-design.md`
- **Plan de plataforma**: `docs/requirements/platform_plan.md` (`DEC-P03`, `DEC-P08`)
- **Archivos auditados**:
  - `pyproject.toml`
  - `task_config.yaml`
  - `adevv/__init__.py`
  - `adevv/yaml_lite.py`
  - `adevv/_build.py`
  - `adevv/release_tools.py`
  - `skills/start-version/SKILL.md`
  - `skills/release/scripts/check_manifests_versions.py`
- **Veredicto**: **APROBADO**

## Análisis Estático y Evidencias

- **`git diff --check`**: Limpio, sin errores de formato ni conflictos de espacio en blanco.
- **`py_compile`**: Limpio sobre todos los módulos Python del delta.
- **Auditoría de dependencias**: `pyproject.toml` declara `requires = []` y cero dependencias externas en `[project]`, cumpliendo estrictamente `DEC-P03`.
- **Evidencia de pruebas (`orquestar_evidencias.jsonl`)**: Verificación en verde registrada mediante `orquestar.py --verificar` (`python -m unittest tests/test_package_and_instructions.py tests/test_install_and_release.py`).

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Corrección** | 9.5 / 10 | Lógica de empaquetado PEP 517 por lista blanca estricta, detección de archivos prohibidos (versionados vía `git ls-files` o en árbol) y validaciones de versión y etiqueta en `release_tools.py` conformes con `RF-F05-01`..`07`. |
| **Seguridad** | 9.5 / 10 | Invocaciones a `subprocess.run` sin `shell=True`, variables `GIT_TERMINAL_PROMPT=0` y `GCM_INTERACTIVE=never`, uso de `yaml.safe_load` y detección de symlinks/junctions NTFS (`os.lstat` y `0x0400`) sin seguir enlaces. |
| **Conformidad** | 9.5 / 10 | Alineación completa con `docs/design/T-ADV-0001-design.md` y con las decisiones arquitectónicas `DEC-P03` (stdlib + backend PEP 517 in-tree + `yaml_lite`) y `DEC-P08` (`pyproject.toml` en `release.manifests`), respetando la dirección de dependencias entre capas. |
| **Calidad** | 9.0 / 10 | Código claro, tipado y bien estructurado; ligera redundancia menor en el bucle de búsqueda de ruta en `check_manifests_versions.py`. |
| **Eficiencia** | 9.5 / 10 | Empaquetado directo en memoria/disco sobre árbol acotado y validación remota en una única operación `git ls-remote --tags`. |
| **Documentación** | 9.5 / 10 | Docstrings presentes en módulos y funciones públicas; `skills/start-version/SKILL.md` documenta el bump en `pyproject.toml` raíz. |
| **Media** | **9.42 / 10** | **APROBADO** (media > 8, sin hallazgos 🔴 ni 🟠) |

---

## Hallazgos

### 🔵 BAJA

- **H-01 [BAJA]** (`skills/release/scripts/check_manifests_versions.py`, líneas 55-79) — `destino: descartar`
  - **Descripción**: En `load_yaml`, el bloque `except ImportError` (líneas 68-78) repite el recorrido hacia los directorios padre buscando `adevv/` que ya se ejecutó en las líneas 55-62. No afecta al comportamiento ni al rendimiento.

- **H-02 [BAJA]** (`adevv/release_tools.py`, líneas 73-79 y 118-124) — `destino: descartar`
  - **Descripción**: El documento de diseño (§ Mapa de impacto) menciona un `timeout` de 5 segundos para `git ls-remote --tags`, mientras que `subprocess.run` en `release_tools.py` se invoca sin parámetro `timeout`. En el flujo de publicación local/CI el impacto es despreciable (el requisito estricto de 5 s de `RF-F03-03` aplica al autoactualizador en `F-03`).
