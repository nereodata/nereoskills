// turbo-all
---
description: Proxy para el workflow /bug-fix
---

> [!IMPORTANT]
> **TURBO**: Auto-ejecutados todos excepto cambios fuera workspace, `git push`, `git reset --hard`, o 3+ repeats sin progreso.

# /bug-fix [BUG_ID]

Ejecuta solo los pasos definidos en `../skills/bug-fix/SKILL.md`:

1. **Urgencia**: Hotfix (`hotfix/vX.Y.(Z+1)` from latest tag) o Release (`release/vX.Y`).
2. **Init**: Carga metadatos, status → `in_progress`.
3. **Triaje**: Checklist de subfases (`[EXEC]`/`[SKIP]`).
4. **Fase A-F**: Según triaje.
   - **A (Reproduc.)**: `generate-bdd` (si destapa requisito) → Hades `/review-spec`.
   - **B (Diseño)**: `/design` → Hades `/review-design`.
   - **C (Fix)**: Red (tests que fallan) → Hades `/review-test` → Fix (corrección).
   - **D (QA)**: Hades `/review-code` → HITL.
   - **E (Docs)**: `/manage-docs`.
   - **F (Cierre)**: `/commit fix([ID])` → status `completed`.

