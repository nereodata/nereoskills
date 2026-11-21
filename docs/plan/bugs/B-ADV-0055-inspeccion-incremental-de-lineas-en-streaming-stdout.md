---
id: B-ADV-0055
title: "Inspección incremental de líneas JSON en _leer_stream de perfiles.lanzar para salidas stream-json extensas"
type: bug
weight: 1500
dificultad: sencilla
version: ""
status: backlog
origen: "B-ADV-0054 (docs/review/code_reviews/B-ADV-0054-code-review.md)"
created_at: 2026-11-21
updated_at: 2026-11-21
---

# B-ADV-0055: Inspección incremental de líneas JSON en _leer_stream de perfiles.lanzar para salidas stream-json extensas

## 🎯 Descripción del Fallo

En `skills/orquestar/perfiles.py` (`lanzar` -> `_leer_stream`), cada bloque recibido con `\n` mientras `cierre_json[0]` es `None` une y decodifica el búfer acumulado (`b"".join(destino)`) y recorre con `_estado_cierre_json` las líneas previas. Para sesiones muy extensas de `claude --verbose --output-format stream-json` con numerosos `tool_result`, conviene mantener un resto de línea pendiente e inspeccionar únicamente las líneas recién completadas en el bloque actual.

## 📋 Evidencias
- `docs/review/code_reviews/B-ADV-0054-code-review.md`
