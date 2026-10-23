---
id: T-ADV-0009
title: "Clasificación de dificultad al crear tareas/bugs y selección de agente/modelo por dificultad"
type: funcional
weight: 110
version: "v0.2.0"
status: planned
depende_de: []
origen: "Mejora operativa de enrutado de modelos en /orquestar"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0009: Clasificación de dificultad al crear tareas/bugs y selección de agente/modelo por dificultad

## 🎯 Objetivo de Negocio
Asignar la dificultad (`sencilla`, `media`, `dificil`) sin coste adicional en el momento de crear cada tarea o bug (`/work-plan`, `/task-add`, `/bug-add`) y permitir que el orquestador ajuste automáticamente el arnés, modelo y nivel de esfuerzo de Artemisa y Hades según dicha dificultad, manteniendo la escalada por rechazos como red de seguridad.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Clasificación en creación sin llamadas extra):** Las skills `skills/task-add/SKILL.md`, `skills/bug-add/SKILL.md` y `skills/work-plan/SKILL.md` incluyen en la plantilla de frontmatter el campo `dificultad: sencilla | media | dificil` con criterio conciso de asignación (`sencilla`: contenido declarativo, documentación, configuración o cambio mecánico localizado; `media`: funcionalidad o corrección estándar en uno o pocos módulos; `dificil`: algoritmos complejos, concurrencia, seguridad crítica o cambio transversal multi-componente). Si una tarea o bug preexistente no declara `dificultad` (o la declara en el arranque de `/task-dev` / `/bug-fix`), se trata por defecto como `media`.
- [ ] **CA-M-2 (Resolución de configuración por dificultad en `orquestar.py`):** `backlog(root)` lee el campo `dificultad` del frontmatter (normalizado a `sencilla`, `media` o `dificil`, por defecto `media`). `ajustes(cfg, paso, dificultad)` aplica sobre la configuración base del rol los overrides definidos en `cfg.get("dificultad", {}).get(dificultad, {})` además de `pasos.<paso>`, tanto al lanzar el paso principal (`rol_de` / `ejecutar`) como al invocar subagentes (`agente`, leyendo la dificultad del `ORQUESTAR_ID` activo).
- [ ] **CA-M-3 (Convivencia con `escalada`):** Si una tarea `sencilla` o `media` alcanza el tope de rechazos seguidos de Hades, `escalada(root, rol, cfg, iid)` sigue elevando la configuración al modelo/esfuerzo de `escalada` por encima del ajuste de dificultad.
- [ ] **CA-M-4 (Documentación en `/orquestar`):** `skills/orquestar/SKILL.md` documenta la clave opcional `dificultad` dentro de los roles de `orchestration.json`.
