// turbo-all
---
description: Proxy para el workflow /task-dev
---

> [!IMPORTANT]
> **TURBO**: Auto-ejecutados todos excepto cambios fuera workspace, `git push`, `git reset --hard`, o 3+ repeats sin progreso.

# /task-dev [TAREA_ID]

Ejecuta solo los pasos definidos en `../skills/task-dev/SKILL.md`:

1. **Init**: Valida rama, carga metadatos, status → `in_progress`.
2. **Triaje**: Checklist de subfases (`[EXEC]`/`[SKIP]`).
3. **Fase A-F**: Según triaje.
   - **A (BDD)**: `generate-bdd` → Hades `/review-spec` (solo lo añadido o modificado).
   - **B (Diseño)**: `/design` (sin revisión; la conformidad la mira `/review-code`).
   - **C (Dev)**: Red (tests) → lint/tipado → Hades `/review-test` → Green (code) → lint/tipado.
   - **D (QA)**: Hades `/review-code` → HITL.
   - **E (Docs)**: `/manage-docs`.
   - **F (Cierre)**: deuda (resolver/registrar/descartar) → status `completed` → `/commit`.

