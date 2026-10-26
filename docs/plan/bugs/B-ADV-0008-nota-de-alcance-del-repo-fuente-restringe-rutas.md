---
id: B-ADV-0008
title: "La nota del prompt para el repositorio fuente de Adevv se lee como una restricción a skills/, agents/ y workflows/"
type: bug
weight: 5
dificultad: sencilla
version: "v0.6.1"
status: completed
depende_de: []
created_at: 2026-10-26
updated_at: 2026-10-26
---

# B-ADV-0008: La nota del prompt para el repositorio fuente de Adevv se lee como una restricción a skills/, agents/ y workflows/

## 🎯 Descripción del Fallo

**Causa raíz**: sobre el repositorio fuente de Adevv, `construir_prompt_paso()` y `construir_prompt_agente()` (`skills/orquestar/orquestar.py:267` y `:295`) añadían «Los cambios se hacen en "skills/", "agents/" y "workflows/" del árbol de trabajo.». La intención (@CA-F02-10) era distinguir el árbol de trabajo de la copia instalada, pero los agentes la leen como una lista cerrada de rutas autorizadas.

**Comportamiento observado**: en v1.0, Hades rechazó B-ADV-0007 (HC-01, `para: especificador`) porque su arreglo está en `tests/test_cli_commands.py`, «fuera del alcance autorizado». Atenea no pudo ampliar esa restricción y el bucle paró («"especificar" no avanza tras 2 intentos»). Bloquearía igual cualquier tarea que toque `adevv/`, `tests/`, `docs/` o los manifiestos.

**Comportamiento esperado**: la nota dice que se edita el árbol de trabajo en cualquier ruta necesaria, nunca la copia instalada.

## ✅ Resolución (hotfix v0.6.1)
- Nueva nota: «Edita el árbol de trabajo de este repositorio, en cualquier ruta que haga falta (skills/, agents/, workflows/, adevv/, tests/, docs/…), nunca la copia instalada desde la que lees skills y agentes.»
- Escenario @CA-F02-10 actualizado en `tests/features/uso_sin_rutas.feature` y `docs/requirements/funcionalidades/F-02_uso_sin_rutas.md`; aserción en `tests/test_cli_commands.py`.
