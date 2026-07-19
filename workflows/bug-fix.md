// turbo-all
---
description: Orchestrador determinista para resolución de bugs
---

> [!IMPORTANT]
> **DETERMINÍSTICO**: Orden obligatorio, validación hard, HITL explícito.

# /bug-fix [BUG_ID] [--fast]

Ejecuta el orchestrador determinista para bugs con dos modos:

## Interactive (default)
```bash
python orchestrator.py run [BUG_ID]
```
- Pausa HITL después de cada fase validada
- **Tú controlas**: continuar, pausar o rechazar
- **Mejor para**: Bugs críticos, control total

## Fast
```bash
python orchestrator.py run [BUG_ID] --fast
```
- Sin pausas HITL, validación automática
- Ejecuta todas las fases de una vez
- **Mejor para**: Bugs simples, cuando confías en validaciones

---

## Útiles

**Ver estado:**
```bash
python orchestrator.py status [BUG_ID]
```

**Reanudar desde pausa:**
```bash
python orchestrator.py resume [BUG_ID]
```
(Solo si quedó en pausa con Interactive mode)

---

## Flujo Canónico

1. **[URGENCIA]**: ¿Hotfix (`hotfix/vX.Y.Z`) o Release (`release/vX.Y`)?
2. **[INIT]**: Valida rama, carga bug, detecta versión
3. **[TRIAGE]**: Decide [EXEC]/[SKIP] para cada fase (A-F)
4. **[A]** Reproducción: BDD → Hades `review-spec` → Validar
5. **[B]** Diseño del arreglo: `design` → Hades `review-design` → Validar
6. **[C]** Fix: Red (tests del fallo) → Hades `review-test` → Green (corrección)
7. **[D]** QA: Hades `review-code` → Validar
8. **[E]** Docs: Actualizar si es necesario
9. **[F]** Cierre: `commit fix([ID])` → close bug
10. **[CLOSE]**: Bug resuelto

