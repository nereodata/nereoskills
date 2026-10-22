---
id: T-ADV-0005
title: "Migración de proyectos con submódulo"
type: funcional
weight: 150
version: "v0.1.0"
status: planned
depende_de: [T-ADV-0003]
origen: "F-04 (docs/requirements/funcionalidades/F-04_migracion.md)"
created_at: 2026-10-22
updated_at: 2026-10-22
---

# T-ADV-0005: Migración de proyectos con submódulo

## 🎯 Objetivo de Negocio
Proporcionar un diagnóstico exacto y de solo lectura (`adevv migrar`) junto con los pasos documentados en el `README.md` y `branch_strategy.md` para retirar de forma segura el submódulo `.agents/`, enlaces/junctions, copias congeladas y referencias en adaptadores tanto en los proyectos consumidores como en el propio repositorio de Adevv.

### Hueco real (Delta sobre el código actual)
- **Ya existe:** Las reglas de detección de elementos locales que ocultan (`RF-F02-07` en `T-ADV-0003`), el `README.md` y `branch_strategy.md §8` (que hoy todavía regula el submódulo).
- **Falta implementar:** El módulo `adevv/migrate.py` y la suborden `adevv migrar` en `adevv/cli.py`, las pruebas unitarias de diagnóstico (`tests/test_migrate.py`), la guía paso a paso de migración en `README.md` (proyectos consumidores y el propio Adevv con su junction hacia `~/.adevv/congelado`) y el reemplazo de `branch_strategy.md §8` por un enlace a dichos pasos.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (`@CA-F04-01`, `@CA-F04-02`, `@CA-F04-03`, `@CA-F04-05`, `@RF-F04-01`, `@RF-F04-02`, `@RF-F04-03`):** `adevv migrar` diagnostica la raíz de un proyecto sin modificar ningún archivo ni recorrer enlaces/junctions ni el interior de `.agents`, listando cada pendiente una sola vez agrupado por archivo (máximo 20 mostrados más `… y M más (total T).`): entrada `.agents` en `.gitmodules`, carpeta o enlace `.agents` (con tipo y destino), `.git/modules/.agents`, enlaces en `.claude/`, `.codex/` y `.agent/` que apunten a `.agents`, claves `instructions` en `orchestration.json` que citen `.agents/`, elementos locales que oculten los instalados (`RF-F02-07`), copias de Adevv en el proyecto (carpetas con `skills/orquestar/SKILL.md` fuera de la raíz y de `.agents`), y líneas con `.agents/` en archivos en uso (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md` salvo en el repo de Adevv, `orchestration.json`, `task_config.yaml`, `scripts/**`, `.claude/**`, `.codex/**`, `.agent/**`, `.github/**`), terminando con `T pendientes.` o `Sin pendientes (N citas históricas).`.
- [ ] **CA-M-2 (`@CA-F04-04`, `@RF-F04-02`, `@RF-F04-03`):** Ejecutado sobre el repositorio fuente de Adevv con la junction `.agents` hacia `~/.adevv/congelado` y el `README.md` que documenta los comandos de migración, `adevv migrar` reporta como único pendiente `.agents → <destino> (junction)`, y tras quitar la junction sin seguirla reporta `Sin pendientes` conservando intacto el contenido de `~/.adevv/congelado`.
- [ ] **CA-M-3 (`@RF-F04-06`):** El `README.md` documenta en el orden exigido los pasos de migración de un proyecto consumidor y los del propio repositorio de Adevv (incluyendo la orden `cmd /c rmdir <ruta>` en Windows para quitar enlaces/junctions sin seguirlos, la advertencia expresa contra `Remove-Item -Recurse` y `rm -rf`, y la condición para borrar `~/.adevv/congelado`), y `branch_strategy.md §8` queda sustituido por un enlace a esa sección del `README.md`.
