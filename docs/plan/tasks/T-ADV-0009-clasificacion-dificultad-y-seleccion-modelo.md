---
id: T-ADV-0009
title: "Clasificación de dificultad al crear tareas/bugs y selección de agente/modelo por dificultad"
type: funcional
weight: 110
version: "v0.2.0"
dificultad: media
status: completed
depende_de: []
origen: "Mejora operativa de enrutado de modelos en /orquestar"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0009: Clasificación de dificultad al crear tareas/bugs y selección de agente/modelo por dificultad

## 🎯 Objetivo de Negocio
Asignar la dificultad (`sencilla`, `media`, `dificil`) sin coste adicional en el momento de crear cada tarea o bug (`/work-plan`, `/task-add`, `/bug-add`) y permitir que el orquestador ajuste automáticamente el arnés, modelo y nivel de esfuerzo de Artemisa y Hades según dicha dificultad, manteniendo la escalada por rechazos como red de seguridad.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Clasificación en creación sin llamadas extra):** Las skills `skills/task-add/SKILL.md`, `skills/bug-add/SKILL.md` y `skills/work-plan/SKILL.md` incluyen en la plantilla de frontmatter el campo `dificultad: sencilla | media | dificil` con criterio conciso de asignación (`sencilla`: contenido declarativo, documentación, configuración o cambio mecánico localizado; `media`: funcionalidad o corrección estándar en uno o pocos módulos; `dificil`: algoritmos complejos, concurrencia, seguridad crítica o cambio transversal multi-componente). Si una tarea o bug preexistente no declara `dificultad` (o la declara en el arranque de `/task-dev` / `/bug-fix`), se trata por defecto como `media`.
- [x] **CA-M-2 (Resolución de configuración por dificultad en `orquestar.py`):** `backlog(root)` lee el campo `dificultad` del frontmatter (normalizado a `sencilla`, `media` o `dificil`, por defecto `media`). `ajustes(cfg, paso, dificultad)` aplica sobre la configuración base del rol los overrides definidos en `cfg.get("dificultad", {}).get(dificultad, {})` además de `pasos.<paso>`, tanto al lanzar el paso principal (`rol_de` / `ejecutar`) como al invocar subagentes (`agente`, leyendo la dificultad del `ORQUESTAR_ID` activo).
- [x] **CA-M-3 (Convivencia con `escalada`):** Si una tarea `sencilla` o `media` alcanza el tope de rechazos seguidos de Hades, `escalada(root, rol, cfg, iid)` sigue elevando la configuración al modelo/esfuerzo de `escalada` por encima del ajuste de dificultad.
- [x] **CA-M-4 (Documentación en `/orquestar`):** `skills/orquestar/SKILL.md` documenta la clave opcional `dificultad` dentro de los roles de `orchestration.json`.

## 🔬 Triaje de Alcance
- **Subfase A: Definición** → `[SKIP]` Lógica interna de orquestación en Python sin interfaz BDD ni Gherkin; verificación mediante suite de tests unitarios en `tests/test_orquestar.py`.
- **Subfase B: Diseño** → `[EXEC]` Documento `docs/design/T-ADV-0009-design.md` con las decisiones técnicas de precedencia (`dificultad` vs `pasos` vs `escalada`) y resolución de metadatos.
- **Subfase C1: Pruebas (Red Phase)** → `[EXEC]` Nuevos tests en `tests/test_orquestar.py` para lectura de dificultad en `backlog`, overrides en `ajustes`, propagación en `rol_de` / `agente` y prioridad de `escalada`.
- **Subfase C2: Implementación (Green Phase)** → `[EXEC]` Implementación en `skills/orquestar/orquestar.py`, plantillas de frontmatter en `skills/task-add/SKILL.md`, `skills/bug-add/SKILL.md`, `skills/work-plan/SKILL.md` y actualización en `skills/task-dev/SKILL.md` y `skills/bug-fix/SKILL.md`.
- **Subfase D: QA** → `[EXEC]` Revisión de Hades (`review-code`) sobre el delta con `adevv orquestar --agente hades`.
- **Subfase E: Documentación** → `[EXEC]` Documentación de la clave opcional `dificultad` en `skills/orquestar/SKILL.md`.
- **Subfase F: Cierre** → `[EXEC]` Cierre de tarea y commit semántico.
- **Verificación al cierre:** `python -m unittest tests/test_orquestar.py` (garantiza que el motor de orquestación, resolución de dificultad y regresiones pasan limpias).
