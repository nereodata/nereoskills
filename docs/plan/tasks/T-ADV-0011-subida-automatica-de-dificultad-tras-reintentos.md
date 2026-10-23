---
id: T-ADV-0011
title: "Subida automática de dificultad de la tarea tras más de 2 reintentos"
type: funcional
weight: 110
dificultad: media
version: "v0.3.0"
status: planned
depende_de: []
origen: "Mejora operativa de adaptación dinámica de dificultad en /orquestar"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0011: Subida automática de dificultad de la tarea tras más de 2 reintentos

## 🎯 Objetivo de Negocio
Promover automáticamente la dificultad de una tarea o bug (`sencilla` $\to$ `media` $\to$ `dificil`) cuando supera 2 reintentos o rechazos seguidos de Hades, de modo que el orquestador aplique el perfil de modelo/esfuerzo del nivel superior sin quedar atrapado con un modelo insuficiente.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Detección de reintentos y promoción de nivel):** En `skills/orquestar/orquestar.py`, cuando una tarea o bug (`ID`) acumula más de 2 reintentos (ejecuciones de paso sobre ese `ID` o rechazos seguidos de Hades desde la última subida), su dificultad sube automáticamente un escalón (`sencilla` $\to$ `media`, `media` $\to$ `dificil`), actualizando el campo `dificultad:` en el frontmatter del fichero de la tarea/bug e informándolo por consola.
- [ ] **CA-M-2 (Integración con `tope_de_rechazos` y `escalada`):** Si el rol tiene configurados niveles en `dificultad` y la tarea aún puede subir de dificultad (`sencilla` o `media`), al alcanzar el tope de rechazos `tope_de_rechazos` indica a Artemisa que commitee y termine el paso para que el bucle suba la dificultad de la tarea y la relance con el perfil del nuevo nivel (iniciando sesión limpia). Si ya está en `dificil`, aplica `escalada` si existe o la regla 5 de bloqueo.
- [ ] **CA-M-3 (Reintentos de paso sin avance):** En `bucle()`, si un paso `task-dev` o `bug-fix` sobre un `ID` con dificultad `sencilla` o `media` llega al límite de reintentos sin progreso, antes de parar el bucle promueve la dificultad del `ID` al nivel inmediato superior, reinicia el contador `sin_progreso` para ese nuevo nivel y reintenta con la configuración superior.
- [ ] **CA-M-4 (Documentación en `/orquestar`):** `skills/orquestar/SKILL.md` documenta la subida automática de `dificultad` tras más de 2 reintentos/rechazos.
