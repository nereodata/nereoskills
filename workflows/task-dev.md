// turbo-all
---
description: Proxy para el workflow /task-dev
---

> [!IMPORTANT]
> **TURBO**: Auto-ejecutados todos excepto cambios fuera workspace, `git push`, `git reset --hard`, o 3+ repeats sin progreso.

# /task-dev [TAREA_ID]

Lee y sigue `skills/task-dev/SKILL.md`:

1. **Preparación**: Valida rama (`release/vX.Y` o `hotfix/vX.Y.Z`), `status: in_progress`, registra `base_calidad` y retoma WIP/contexto previo si existe (*delta-first*, sin subfases A–F ni Gherkin obligatorio).
2. **Implementación y verificación directa**: Código cohesivo + pruebas directas (`unittest`), `--verificar` sobre las pruebas afectadas y `adevv orquestar --calidad --base <base_calidad> --aplicar`.
3. **Revisión post-verde proporcional**: Hades (`--agente hades --revision code`) solo si toca superficies críticas; informe `N/A` verificable si queda fuera.
4. **Cierre**: Deuda 🟡/🔵, calidad limpia sin escritura, `status: completed` y `/commit`.

