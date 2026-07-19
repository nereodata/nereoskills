// turbo-all
---
description: Proxy para el workflow /design
---

> [!IMPORTANT]
> **TURBO**: Auto-ejecutados todos excepto cambios fuera workspace, `git push`, `git reset --hard`, o 3+ repeats sin progreso.

# /design [TASK_ID]

Ejecuta solo los pasos definidos en `../skills/design/SKILL.md`:

1. **Analiza**: Código existente, requisitos (BDD), alcance del cambio.
2. **Diseña**: Cambios por archivo (`[NEW]`, `[MODIFY]`, `[DELETE]`), SOLID/DRY/KISS/YAGNI.
3. **Output**: `docs/design/[ID]-design.md`.
4. **Verifica**: Viabilidad, modularidad, testeabilidad.
