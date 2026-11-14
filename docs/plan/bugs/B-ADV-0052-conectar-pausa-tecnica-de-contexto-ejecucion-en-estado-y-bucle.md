---
id: B-ADV-0052
title: "Contadores de pausa_tecnica en adevv/contexto_ejecucion.py no conectados como guarda efectiva en estado() y bucle()"
type: bug
weight: 1500
dificultad: media
version: ""
status: backlog
origen: "T-ADV-0041, T-ADV-0038; revisar-version v1.2 (docs/review/versions/v1.2-arquitectura.md), H-02 🟡"
created_at: 2026-11-14
updated_at: 2026-11-14
---

# B-ADV-0052: Contadores de pausa_tecnica en adevv/contexto_ejecucion.py no conectados como guarda efectiva en estado() y bucle()

## 🎯 Descripción del Fallo

**Causa raíz:**
- `adevv/contexto_ejecucion.py` (`cargar_politica` y `registrar_intento`, líneas 208–225) evalúa `execution.limits` (`no_progress`, `technical_retries`, `max_attempts`, `max_seconds`) en `orchestration.json` y calcula `action == "pausa_tecnica"`, estado que `construir_prompt_paso()` inyecta en el prompt e `intervencion._motivos_item_sin_pregunta()` (`/desbloquear` en `T-ADV-0038`, líneas 377–383) diagnostica explícitamente.
- Sin embargo, `skills/orquestar/orquestar.py` descarta el retorno de `contexto_ejecucion.registrar_intento()` en `bucle()` (línea 5036) y `estado()` (líneas 1521–1549) sigue gobernando la parada/promoción únicamente con `--reintentos`, `reintentos_acumulados` y `--reintentos-arnes`.

**Comportamiento observado:** si un consumidor configura `execution.limits.max_attempts` o `execution.limits.max_seconds` en `orchestration.json`, al superarse ese presupuesto `/desbloquear` diagnostica `pausa_tecnica`, mientras `estado()` sigue considerando elegible el ítem.

**Comportamiento esperado:** `estado()` y `bucle()` en `skills/orquestar/orquestar.py` respetan de forma coherente el estado `pausa_tecnica` calculado por `adevv/contexto_ejecucion.py` cuando se superan los topes configurados en `execution.limits`.

## 📋 Reproducir
1. Configurar `execution.limits.max_attempts` o `execution.limits.max_seconds` en `orchestration.json` y agotar el límite en un ítem.
2. Observar que `intervencion._motivos_item_sin_pregunta()` reporta `pausa_tecnica`, pero `orquestar.estado()` en `skills/orquestar/orquestar.py` no detiene ni retiene la elegibilidad del ítem por esa condición.

## 📋 Evidencias
- `docs/review/versions/v1.2-arquitectura.md`, hallazgo H-02.
