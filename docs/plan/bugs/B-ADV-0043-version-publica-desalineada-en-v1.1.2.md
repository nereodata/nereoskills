---
id: B-ADV-0043
title: "El módulo y la CLI sin versión activa anuncian 1.1.1 en la distribución 1.1.2"
type: bug
weight: 100
dificultad: sencilla
version: "v1.1.2"
status: planned
depende_de: []
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Revisión transversal de v1.1.2, hallazgo 2"
---

# B-ADV-0043 · Versión pública desalineada en v1.1.2

En `1bab7c5`, el wheel toma su versión de `pyproject.toml` y declara 1.1.2. El módulo incluido declara `adevv.__version__ = "1.1.1"`. La CLI usa ese valor cuando no hay una versión activa, tanto para informar de su versión como para materializar una instalación local.

## Reproducción y criterio de aceptación

1. Consultar `adevv.__version__` desde el módulo de este árbol y compararlo con `project.version` de `pyproject.toml`.
2. Consultar `adevv --version` con un `ADEVV_HOME` temporal sin versión activa. Comprobar también el valor que `comando_instalar` entrega a `materializar_version_local` en ese estado.
3. Los metadatos de la distribución, el módulo y ambos consumidores deben identificar la versión 1.1.2.

[Dictamen transversal](../../review/versions/v1.1.2-arquitectura.md).

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades H2, media, resolver en v1.1.2. Alinear adevv.__version__ con 1.1.2 y comprobar los consumidores de la CLI sin versión activa y los metadatos del paquete.
