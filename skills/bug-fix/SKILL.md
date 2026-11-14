---
name: bug-fix
description: Diagnostica y corrige una anomalía conforme a la política del proyecto
---

# /bug-fix

Corrige la anomalía descrita en la ficha siguiendo `PROJECT.md` (si existe en la raíz del proyecto).

1. **Aislar la causa raíz**: Lee la ficha, `PROJECT.md` y el código o contexto previo afectado (en modo interactivo, confirma si va en rama `hotfix/` o `release/`). Cuando sea viable, reproduce o aísla primero el fallo para corregir la causa y no el síntoma.
2. **Corregir y verificar**: Aplica la solución más simple que resuelva el problema y verifícala según `PROJECT.md` (incluyendo comprobación automatizada que discrimine el fallo cuando proceda y regresiones del área tocada).
3. **Decidir o escalar**: Toma las decisiones técnicas necesarias; usa `adevv orquestar --preguntar <ID> "<pregunta>" --contexto "<contexto>"` solo ante bloqueos externos reales o dudas de negocio no deducibles.
4. **Cerrar limpio**: Marca `status: completed` en la ficha con una nota breve de causa, solución y verificación, actualiza documentación solo si quedó falsa (`/manage-docs`) y haz commit semántico `fix` (`/commit`).
