// turbo-all
---
description: Proxy para el workflow /bug-fix
---

> [!IMPORTANT]
> **TURBO**: Auto-ejecutados todos excepto cambios fuera workspace, `git push`, `git reset --hard`, o 3+ repeats sin progreso.

# /bug-fix [BUG_ID]

Lee y sigue `skills/bug-fix/SKILL.md`:

1. **Preparación y diagnóstico**: Rama `hotfix/vX.Y.Z` o `release/vX.Y`, `status: in_progress`, conserva `base_calidad` y localiza la causa raíz sin subfases ceremoniales.
2. **Prueba discriminante y corrección**: Prueba directa (`unittest`) que discrimine el fallo + corrección limpia, `--verificar` y `adevv orquestar --calidad --base <base_calidad> --aplicar`.
3. **Revisión post-verde proporcional**: Hades (`--agente hades --revision code`) si toca superficies críticas; `N/A` verificable si queda fuera.
4. **Cierre**: Deuda 🟡/🔵, calidad limpia sin escritura, `status: completed` y `/commit`.

