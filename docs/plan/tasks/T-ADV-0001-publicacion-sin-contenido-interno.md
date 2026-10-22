---
id: T-ADV-0001
title: "Publicación de versiones sin contenido interno"
type: funcional
weight: 110
version: "v0.1.0"
status: completed
depende_de: []
origen: "F-05 (docs/requirements/funcionalidades/F-05_publicacion.md)"
created_at: 2026-10-22
updated_at: 2026-10-22
---

# T-ADV-0001: Publicación de versiones sin contenido interno

## 🎯 Objetivo de Negocio
Lograr que al cerrar y publicar una versión de Adevv con `/release` se construya un paquete distribuible limpio (sin backlog, tests, configuración interna ni archivos de ejecución del bucle), cuya versión suba automáticamente con `project.version`, coincida siempre con la etiqueta anotada `vX.Y.Z` y sea inmutable una vez publicada en el origen.

### Hueco real (Delta sobre el código actual)
- **Ya existe:** `task_config.yaml` con `release.manifests` apuntando solo a sí mismo, y los scripts `skills/release/scripts/{check_manifests_versions.py, check_release_completeness.py, generate_changelog_section.py}`.
- **Falta implementar:** `pyproject.toml` en la raíz (y su registro en `task_config.yaml::release.manifests`), la estructura base del paquete `adevv/` (`__init__.py`, `yaml_lite.py`, `_build.py` con backend PEP 517 in-tree y filtrado por lista blanca estricta, `release_tools.py` con validaciones `RF-F05-05/06/07`) y las pruebas de empaquetado y publicación en `tests/`.

## 🚦 Triaje de Alcance (Delta-First)
- [x] **Subfase A: Definición [EXEC]** Traslado 1:1 de escenarios `@CA-F05-01` a `@CA-F05-05` a `tests/features/publicacion.feature`.
- [x] **Subfase B: Diseño [EXEC]** Diseño técnico en `docs/design/T-ADV-0001-design.md` cubriendo PEP 517 in-tree, lista blanca, `release_tools.py` y registro en `task_config.yaml`.
- [x] **Subfase C: Desarrollo [EXEC]** Red Phase (tests en `tests/test_package_and_instructions.py` y `tests/test_install_and_release.py` en rojo) -> Hades `review-test` -> Green Phase (implementación en `adevv/` y raíz).
- [x] **Subfase D: QA [EXEC]** Hades `review-code` sobre el código de producción.
- [x] **Subfase E: Documentación [EXEC]** Registro en `docs/review/versions/v0.1-revision.md`.
- [x] **Subfase F: Cierre [EXEC]** Marcar `completed` y commit semántico.

**Verificación al cierre:** `python -m unittest tests/test_package_and_instructions.py tests/test_install_and_release.py` (ejercita la construcción por lista blanca, detección de archivos prohibidos y reglas de publicación de etiquetas/versión).

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (`@CA-F05-01`, `@RF-F05-01`, `@RF-F05-03`):** Cuando se construye el paquete de la versión sobre el árbol del repositorio de Adevv (aunque existan `docs/plan/`, `tests/`, `task_config.yaml`, `orchestration.json`, `orquestar.log` o la junction `.agents`), el paquete resultante contiene únicamente archivos de la lista blanca (`adevv/`, `skills/`, `agents/` y `workflows/`, más metadatos de `pyproject.toml`), sin enlaces, junctions, `__pycache__`, `*.pyc`, `*.pid`, `*.log` ni `*.jsonl`.
- [x] **CA-M-2 (`@CA-F05-02`, `@RF-F05-03`):** La suite de pruebas (`python -m unittest discover -s tests`) incluye una prueba que construye el paquete e inspecciona su contenido, y falla nombrando el archivo infractor si se introduce un elemento prohibido (como un `skills/orquestar/__pycache__/orquestar.cpython-312.pyc` versionado).
- [x] **CA-M-3 (`@CA-F05-03`, `@RF-F05-05`):** Si en el repositorio fuente de Adevv la versión declarada del paquete (`A.B.C`) no coincide con la etiqueta `vX.Y.Z` que se intenta publicar, la validación de publicación falla antes de crear o empujar la etiqueta con el mensaje `La versión del paquete (A.B.C) no coincide con vX.Y.Z.`.
- [x] **CA-M-4 (`@CA-F05-04`, `@RF-F05-05`):** Si la etiqueta `vX.Y.Z` ya existe publicada en el origen, la publicación falla antes de mover o sobrescribir la etiqueta con el mensaje `vX.Y.Z ya está publicada: publica vX.Y.(Z+1).`.
- [x] **CA-M-5 (`@CA-F05-05`, `@RF-F05-06`, `@RF-F05-07`):** `pyproject.toml` queda registrado en `task_config.yaml::release.manifests` (con soporte TOML en el validador de manifiestos y en `/start-version`), de modo que abrir `release/v0.1` y publicar con `/release` actualiza sin pasos manuales tanto `project.version` como la versión del paquete a `0.1.0` y crea una etiqueta anotada `v0.1.0` en `main`.
