---
id: B-ADV-0025
title: "/cerrar publica la release por una segunda ruta con validaciones propias, al margen de release_tools"
type: bug
weight: 2000
dificultad: media
version: ""
status: backlog
origen: "T-ADV-0023; revisar-version v1.0 (docs/review/versions/v1.0-arquitectura.md), H-08 🟡"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0025: /cerrar publica la release por una segunda ruta con validaciones propias

## 🎯 Descripción del Fallo

**Causa raíz:** `skills/telegram_gateway/cierre_version.py` (hacia las líneas 37–135) reimplementa la merge a `main`, la comprobación de etiquetas local y remota, el changelog y el push. Su push es atómico, mejor que `--follow-tags`. Solo reutiliza `check_manifests_versions.py`, no `adevv/release_tools.py` (`validar_publicacion`, `publicar_version`).

**Comportamiento observado:** hay dos rutas de publicación con validaciones distintas. Cualquier cambio futuro en la política de publicación (RF-F05-05/06) tendrá que hacerse dos veces, en contra de la regla 3 de capas (`NO-04`), que pide las validaciones de release en un único sitio.

**Comportamiento esperado:** una única implementación de las validaciones y de la publicación, que usen tanto `adevv release` como `/cerrar`, conservando el push atómico.

## 📋 Reproducir
1. Comparar `cierre_version.publicar` con `release_tools.publicar_version` y `validar_publicacion`.

## 📋 Evidencias
- `docs/review/versions/v1.0-arquitectura.md`, hallazgo H-08.
