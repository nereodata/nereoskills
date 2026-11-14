---
id: B-ADV-0051
title: "Desajuste entre la opción CLI --decision documentada en SKILL.md y el parser real de orquestar.py"
type: bug
weight: 1500
dificultad: sencilla
version: "v1.3.0"
status: cancelled
origen: "T-ADV-0041; absorbido por la reescritura minimalista del motor en v1.3 (T-ADV-0042)"
created_at: 2026-11-14
updated_at: 2026-11-14
---

# B-ADV-0051: Desajuste entre la opción CLI --decision documentada en SKILL.md y el parser real de orquestar.py

## 🎯 Descripción del Fallo

**Causa raíz:**
- `skills/orquestar/SKILL.md` (línea 166) afirma que el motor admite enrutados o esperas locales por ítem mediante `adevv orquestar --decision <ID> "<json>"` (`DECISION_ITEM {...}`).
- En `skills/orquestar/orquestar.py` (líneas 4293–4320), `--decision` está definido en realidad como un modificador de un único argumento (`action="append"`) subordinado a `--checkpoint`, mientras que `adevv/decision_item.py` (`extraer_decision`) extrae `DECISION_ITEM {...}` desde la salida estándar (`stdout`) del paso.
- Además, a diferencia de `--base`/`--aplicar` y `--csv`/`--version-filtro`, pasar `--resumen`, `--siguiente` o `--decision` sin `--checkpoint` no emite `ap.error(...)`.

**Comportamiento observado:** la documentación de `skills/orquestar/SKILL.md` atribuye a `--decision <ID> "<json>"` el canal de `DECISION_ITEM`, y el parser CLI ignora en silencio `--resumen`, `--siguiente` o `--decision` si se invocan sin `--checkpoint`.

**Comportamiento esperado:** `skills/orquestar/SKILL.md` documenta con exactitud el mecanismo real de `DECISION_ITEM {...}` por salida estándar y el papel de `--decision` junto a `--checkpoint` (o bien se expone el subcomando explícito si procede), y `orquestar.py` rechaza con `ap.error(...)` el uso huérfano de `--resumen`, `--siguiente` o `--decision` sin `--checkpoint`.

## 📋 Reproducir
1. Revisar `skills/orquestar/SKILL.md` (línea 166) frente a `skills/orquestar/orquestar.py` (líneas 4293–4320) y `adevv/decision_item.py` (`extraer_decision`, líneas 96–107).
2. Comprobar que `--decision` pertenece a `--checkpoint` y que no existe guarda `ap.error(...)` cuando falta `--checkpoint`.

## 📋 Evidencias
- `docs/review/versions/v1.2-arquitectura.md`, hallazgo H-01.
