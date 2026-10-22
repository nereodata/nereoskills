# Diseño Técnico: T-ADV-0001 - Publicación de versiones sin contenido interno

## 🏗️ Arquitectura
- **Componentes creados/modificados:**
  - `pyproject.toml` (raíz): Manifiesto PEP 621 (`project.version = "0.1.0"`) y configuración de build backend PEP 517 in-tree (`adevv._build`).
  - `task_config.yaml`: Registro de `pyproject.toml` en `release.manifests`.
  - `adevv/__init__.py`: Metadatos del paquete (`__version__ = "0.1.0"`), constantes de origen remoto por defecto y definición de listas blancas/negras.
  - `adevv/yaml_lite.py`: Parser/emisor YAML minimalista para `task_config.yaml` y frontmatters (usa `PyYAML` si está disponible, stdlib en caso contrario).
  - `adevv/_build.py`: Backend PEP 517 in-tree (`build_wheel`, `build_sdist`, hooks PEP 517) con empaquetado por lista blanca estricta e inspección de contenido prohibido.
  - `adevv/release_tools.py`: Validaciones de publicación (`RF-F05-05/06/07`): verificación de coincidencia entre versión del paquete y tag `vX.Y.Z`, e inmutabilidad de tags ya publicados en el origen.
  - `skills/start-version/SKILL.md`: Documentación del bump en `pyproject.toml` raíz.
  - `tests/test_package_and_instructions.py`: Pruebas de empaquetado por lista blanca (`CA-M-1`, `CA-M-2`, `@CA-F05-01`, `@CA-F05-02`).
  - `tests/test_install_and_release.py`: Pruebas de validación de publicación (`CA-M-3`, `CA-M-4`, `CA-M-5`, `@CA-F05-03`, `@CA-F05-04`, `@CA-F05-05`).

## 🛠️ Cambios
- **[NEW]** `pyproject.toml`: Configuración de empaquetado PEP 621/517.
- **[NEW]** `adevv/__init__.py`: Versión del paquete y constantes.
- **[NEW]** `adevv/yaml_lite.py`: Soporte YAML seguro sin dependencias obligatorias.
- **[NEW]** `adevv/_build.py`: Empaquetado estricto por lista blanca y detector de contenido prohibido.
- **[NEW]** `adevv/release_tools.py`: Funciones de validación de tag vs versión y verificación remota de etiquetas.
- **[NEW]** `tests/test_package_and_instructions.py`: Pruebas de lista blanca e inspección de archivos infractores.
- **[NEW]** `tests/test_install_and_release.py`: Pruebas de precondiciones de release y manifiestos.
- **[MODIFY]** `task_config.yaml`: Añadir `pyproject.toml` a `release.manifests`.
- **[MODIFY]** `skills/start-version/SKILL.md`: Asegurar mención explícita a `pyproject.toml` raíz.

## 🎯 Mapa de impacto
- **Llamantes:**
  - Sistema de build estándar (`pip install`, `python -m build`, backend PEP 517): consume `pyproject.toml` y `adevv._build`.
  - Skill `/release`: consume `adevv.release_tools.validar_publicacion` antes de crear o empujar etiquetas.
  - Scripts de release (`check_manifests_versions.py`): consume `pyproject.toml` declarado en `task_config.yaml`.
- **Escenarios/tests afectados:**
  - Ningún test previo se invalida. Se añaden nuevos módulos a `tests/`.
- **Decisiones contradichas:**
  - Ninguna. Cumple `DEC-P03` (stdlib + backend in-tree sin dependencias obligatorias) y `DEC-P08` (`pyproject.toml` en `release.manifests` y validaciones en release).
- **Sistema de referencia:**
  - Versiones SemVer `X.Y.Z` en código/TOML/JSON y etiquetas Git con prefijo `vX.Y.Z`.
- **Camino caliente:**
  - La construcción del paquete solo se invoca en release o empaquetado; la validación de tags ejecuta una sola llamada `git ls-remote --tags` con timeout de 5 segundos.

## 🧩 Patrones
- **PEP 517 / PEP 621 Standard Compliance**:
  - `adevv._build` implementa `build_wheel`, `build_sdist`, `get_requires_for_build_wheel`, `get_requires_for_build_sdist`.
  - Generación estándar de metadata `.dist-info` (WHEEL, METADATA, RECORD, entry_points.txt).
  - Empaquetado de wheel como archivo `.whl` (ZIP).
- **Lista blanca estricta**:
  - Permitido: `adevv/**`, `skills/**`, `agents/**`, `workflows/**`, metadatos (`pyproject.toml`, `README.md`).
  - Prohibido: `docs/**`, `tests/**`, `.github/**`, `task_config.yaml`, `orchestration.json`, `__pycache__/**`, `*.pyc`, `*.pid`, `*.log`, `*.jsonl`, symlinks y junctions.
  - Si un archivo prohibido se encuentra en el árbol de origen distribuible durante la construcción/inspección, se lanza error nombrando el archivo exacto.
- **Validación de publicación (`release_tools`)**:
  - `validar_publicacion(repo_dir, target_tag, origin_url=None)`
  - Si no coincide versión: `La versión del paquete ({pkg_ver}) no coincide con {target_tag}.`
  - Si tag ya existe en origin: `{target_tag} ya está publicada: publica {next_tag}.`

## 🧪 Testeabilidad
- `tests/test_package_and_instructions.py`:
  - Construcción del paquete en árbol limpio: verifica contenido ZIP/wheel solo con la lista blanca.
  - Inserción de un archivo prohibido en `skills/orquestar/__pycache__/orquestar.cpython-312.pyc`: la prueba falla nombrando explícitamente dicho archivo.
- `tests/test_install_and_release.py`:
  - Repositorio bare local en `tempfile` (`git init --bare`): simula el origen remoto sin red.
  - Validación de versión discordante (`0.1.0` vs `v0.2.0`).
  - Validación de tag ya publicado (`v0.1.0` existente en remoto).
  - Validación de manifiestos alineados con `check_manifests_versions.py`.
