---
id: B-ADV-0023
title: "Una tarea bloqueada deja sus cambios sin commitear a la siguiente tarea de la misma rama"
type: bug
weight: 1500
dificultad: media
version: ""
status: backlog
origen: "B-ADV-0012/B-ADV-0013 × B-ADV-0015; revisar-version v1.0 (docs/review/versions/v1.0-arquitectura.md), H-02 🟡"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0023: Una tarea bloqueada deja sus cambios sin commitear a la siguiente tarea de la misma rama

## 🎯 Descripción del Fallo

**Causa raíz:** `bloquear_sin_progreso` (`skills/orquestar/orquestar.py`, hacia la línea 3105) bloquea la tarea con un commit que solo incluye la tarea y la revisión de versión, y sigue con `continue`. La resolución de árbol sucio de B-ADV-0015 solo se ejecuta en `cambiar_de_rama` (línea ~2063), así que no se aplica si la siguiente tarea elegible está en la misma rama `release/`.

**Comportamiento observado:** un intento deja ediciones sin commitear (eso cuenta como progreso, porque `firma` incluye `git status`). Los siguientes intentos no cambian nada y la tarea se bloquea. La siguiente tarea empieza con el árbol sucio de la anterior: su delta de calidad (`base_calidad`, T-ADV-0022) incluye ficheros ajenos y su commit puede arrastrarlos.

**Comportamiento esperado:** tras cada bloqueo local (o antes de cada paso) se aplica la misma resolución de árbol sucio que en B-ADV-0015: Clio resuelve los cambios o se guardan en un stash, con aviso.

## 📋 Reproducir
1. Simular una tarea cuyo primer intento deja un fichero sin commitear y cuyos intentos siguientes no cambian nada, hasta que se bloquee.
2. Con otra tarea elegible en la misma rama, comprobar que el siguiente paso empieza con `git status` sucio.

## 📋 Evidencias
- `docs/review/versions/v1.0-arquitectura.md`, hallazgo H-02.
