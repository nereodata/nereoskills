// turbo-all
---
description: Orchestrador determinista para resolución de bugs
---

> [!IMPORTANT]
> **DETERMINÍSTICO**: Orden obligatorio, validación hard, HITL explícito.

# /bug-fix [BUG_ID] [--mode]

Ejecuta el orchestrador determinista para bugs con tres modos:

## Modo Interactive (default)
```bash
python orchestrator.py run [BUG_ID]
```
- Pausa HITL después de cada fase validada
- **Tú controlas**: continuar, pausar o rechazar
- **Mejor para**: Bugs críticos, control total

## Modo Fast
```bash
python orchestrator.py run [BUG_ID] --fast
```
- Ejecuta todas las fases sin pausas (no HITL)
- Validación automática entre fases
- Captura artefactos reales
- **Mejor para**: Bugs simples, cuando confías en validaciones

## Modo Mock
```bash
python orchestrator.py run [BUG_ID] --mock
```
- Simula todas las fases sin intervención
- **Mejor para**: Testing, prototipos

---

## Flujo Canónico

1. **[URGENCIA]**: ¿Hotfix (`hotfix/vX.Y.Z`) o Release (`release/vX.Y`)?
2. **[INIT]**: Valida rama, carga bug, detecta versión
3. **[TRIAGE]**: Decide [EXEC]/[SKIP] para cada fase (A-F)
4. **[A]** Reproducción: BDD → Hades `review-spec` → Validar → **PAUSA** (si Interactive)
5. **[B]** Diseño del arreglo: `design` → Hades `review-design` → Validar → **PAUSA**
6. **[C]** Fix: Red (tests del fallo) → Hades `review-test` → Green (corrección)
7. **[D]** QA: Hades `review-code` → Validar → **PAUSA**
8. **[E]** Docs: Actualizar si es necesario
9. **[F]** Cierre: `commit fix([ID])` → close bug
10. **[CLOSE]**: Bug resuelto

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

