// turbo-all
---
description: Orchestrador determinista para desarrollo de tareas
---

> [!IMPORTANT]
> **DETERMINÍSTICO**: Orden obligatorio, validación hard, HITL explícito.

# /task-dev [TASK_ID] [--mode]

Ejecuta el orchestrador con tres modos:

## Modo Interactive (default)
```bash
python orchestrator.py run [TASK_ID]
```
- Pausa HITL después de cada fase
- **Tú controlas**: continuar, pausar o rechazar
- **Mejor para**: Control total, validación crítica, trabajo en equipo

Ejemplo:
```
[A] Especificación → validación → PAUSA
    ¿Continuar? [y/n/reject]
[B] Diseño → validación → PAUSA
    ¿Continuar? [y/n/reject]
```

## Modo Fast
```bash
python orchestrator.py run [TASK_ID] --fast
```
- Ejecuta todas las fases sin pausas (no HITL)
- **Validación automática** entre fases
- **Captura artefactos reales** (no mocks)
- **Mejor para**: Flujos confiables, cuando confías en validaciones

Ejecución sin interrupciones:
```
[A] Especificación → validación automática → CONTINÚA
[B] Diseño → validación automática → CONTINÚA
[C] Tests → validación automática → CONTINÚA
... todo se ejecuta hasta completar
```

## Modo Mock
```bash
python orchestrator.py run [TASK_ID] --mock
```
- Simula todas las fases sin pedir nada
- **Sin intervención humana**, resultados vacíos
- **Mejor para**: Testing del orchestrador, prototipos rápidos

---

## Útiles

**Ver estado en cualquier momento:**
```bash
python orchestrator.py status [TASK_ID]
```

**Reanudar desde pausa:**
```bash
python orchestrator.py resume [TASK_ID]
```
(Solo si quedó en pausa con modo Interactive)

---

## Flujo Canónico (Interactive mode)

1. **[INIT]** Valida rama, carga task, detecta versión
2. **[TRIAGE]** Decide [EXEC]/[SKIP] para cada fase (A-F)
3. **[A]** BDD: `generate-bdd` → Hades `review-spec` → Validar → **PAUSA**
4. **[B]** Diseño: `design` → Hades `review-design` → Validar → **PAUSA**
5. **[C]** Tests: Red/Green → Hades `review-test` → Validar → **PAUSA**
6. **[D]** QA: Hades `review-code` → Validar → **PAUSA**
7. **[E]** Docs: `manage-docs`
8. **[F]** Commit: `commit` → Close task
9. **[CLOSE]** Tarea completada

