// turbo-all
---
description: Orchestrador determinista para desarrollo de tareas
---

> [!IMPORTANT]
> **DETERMINÍSTICO**: Orden obligatorio, validación hard, HITL explícito.

# /task-dev [TASK_ID] [--fast]

Ejecuta el orchestrador determinista con dos modos:

## Interactive (default)
```bash
python orchestrator.py run [TASK_ID]
```
- Pausa HITL después de cada fase validada
- **Tú controlas**: continuar, pausar o rechazar
- **Mejor para**: Control total, validación crítica, trabajo en equipo

Flujo con pausas:
```
[A] Especificación → validación → PAUSA
    ¿Continuar? [y/n/reject]
[B] Diseño → validación → PAUSA
    ¿Continuar? [y/n/reject]
```

## Fast
```bash
python orchestrator.py run [TASK_ID] --fast
```
- Sin pausas HITL, validación automática
- Ejecuta todas las fases de una vez
- **Mejor para**: Flujos confiables, cuando confías en validaciones

Ejecución continua:
```
[A] Especificación → validación → CONTINÚA
[B] Diseño → validación → CONTINÚA
[C] Tests → validación → CONTINÚA
... todo de un tirón
```

---

## Útiles

**Ver estado:**
```bash
python orchestrator.py status [TASK_ID]
```

**Reanudar desde pausa:**
```bash
python orchestrator.py resume [TASK_ID]
```
(Solo si quedó en pausa con Interactive mode)

---

## Flujo Canónico

1. **[INIT]** Valida rama, carga task, detecta versión
2. **[TRIAGE]** Decide [EXEC]/[SKIP] para cada fase (A-F)
3. **[A]** BDD: `generate-bdd` → Hades `review-spec` → Validar
4. **[B]** Diseño: `design` → Hades `review-design` → Validar
5. **[C]** Tests: Red/Green → Hades `review-test` → Validar
6. **[D]** QA: Hades `review-code` → Validar
7. **[E]** Docs: `manage-docs`
8. **[F]** Commit: `commit` → Close task
9. **[CLOSE]** Tarea completada

