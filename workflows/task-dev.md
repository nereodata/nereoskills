// turbo-all
---
description: Orchestrador determinista para desarrollo de tareas
---

> [!IMPORTANT]
> **DETERMINÍSTICO**: El orchestrador obliga orden, validación y persistencia.
> - No se salta fases
> - No avanza sin validar
> - Se recupera si se interrumpe
> - HITL pausa explícita

# /task-dev [TASK_ID]

Ejecuta el orchestrador determinista:

```bash
python orchestrator.py run [TASK_ID]
```

**Flujo automático:**

1. **[INIT]** Valida rama, carga task, detecta versión
2. **[TRIAGE]** Decide [EXEC]/[SKIP] para cada fase (A-F)
3. **[A]** BDD: `generate-bdd` → Hades `review-spec` → Validar
4. **[HITL]** Pausa: ¿Continuar a fase B?
5. **[B]** Diseño: `design` → Hades `review-design` → Validar
6. **[HITL]** Pausa: ¿Continuar a fase C?
7. **[C]** Tests: `tests` → Hades `review-test` → Validar
8. **[HITL]** Pausa: ¿Continuar a fase D?
9. **[D]** QA: Hades `review-code` → Validar
10. **[HITL]** Pausa: ¿Continuar a fase E?
11. **[E]** Docs: `manage-docs`
12. **[F]** Commit: `commit` → Close task
13. **[CLOSE]** Tarea completada

**Estados:**

- En cualquier momento, ver estado: `python orchestrator.py status [TASK_ID]`
- Si se interrumpe: `python orchestrator.py resume [TASK_ID]` continúa donde quedó

**HITL (Human-In-The-Loop):**

Después de cada fase, el orchestrador pausa:
```
=== HITL PAUSE ===
Phase A completada y validada.
Siguiente: Phase B (Diseño)

Continuar? [responde en el chat]
```

Tú simplemente responde "sí", "continuar" o similar. El orchestrador sigue.

