---
id: T-ADV-0001
title: "Publicación de versiones sin contenido interno"
type: funcional
weight: 110
version: "v0.1.0"
status: planned
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

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (`@CA-F05-01`, `@RF-F05-01`, `@RF-F05-03`):** Cuando se construye el paquete de la versión sobre el árbol del repositorio de Adevv (aunque existan `docs/plan/`, `tests/`, `task_config.yaml`, `orchestration.json`, `orquestar.log` o la junction `.agents`), el paquete resultante contiene únicamente archivos de la lista blanca (`adevv/`, `skills/`, `agents/` y `workflows/`, más metadatos de `pyproject.toml`), sin enlaces, junctions, `__pycache__`, `*.pyc`, `*.pid`, `*.log` ni `*.jsonl`.
- [ ] **CA-M-2 (`@CA-F05-02`, `@RF-F05-03`):** La suite de pruebas (`python -m unittest discover -s tests`) incluye una prueba que construye el paquete e inspecciona su contenido, y falla nombrando el archivo infractor si se introduce un elemento prohibido (como un `skills/orquestar/__pycache__/orquestar.cpython-312.pyc` versionado).
- [ ] **CA-M-3 (`@CA-F05-03`, `@RF-F05-05`):** Si en el repositorio fuente de Adevv la versión declarada del paquete (`A.B.C`) no coincide con la etiqueta `vX.Y.Z` que se intenta publicar, la validación de publicación falla antes de crear o empujar la etiqueta con el mensaje `La versión del paquete (A.B.C) no coincide con vX.Y.Z.`.
- [ ] **CA-M-4 (`@CA-F05-04`, `@RF-F05-05`):** Si la etiqueta `vX.Y.Z` ya existe publicada en el origen, la publicación falla antes de mover o sobrescribir la etiqueta con el mensaje `vX.Y.Z ya está publicada: publica vX.Y.(Z+1).`.
- [ ] **CA-M-5 (`@CA-F05-05`, `@RF-F05-06`, `@RF-F05-07`):** `pyproject.toml` queda registrado en `task_config.yaml::release.manifests` (con soporte TOML en el validador de manifiestos y en `/start-version`), de modo que abrir `release/v0.1` y publicar con `/release` actualiza sin pasos manuales tanto `project.version` como la versión del paquete a `0.1.0` y crea una etiqueta anotada `v0.1.0` en `main`.
