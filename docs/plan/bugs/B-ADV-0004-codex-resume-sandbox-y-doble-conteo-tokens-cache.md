---
id: B-ADV-0004
title: "Fallo de reanudación codex exec resume por flag --sandbox y doble conteo de tokens cacheados en codex"
type: bug
weight: 10
dificultad: sencilla
version: "v0.6.0"
status: backlog
depende_de: []
created_at: 2026-10-25
updated_at: 2026-10-25
---

# B-ADV-0004: Fallo de reanudación codex exec resume por flag --sandbox y doble conteo de tokens cacheados en codex

## 🎯 Descripción del Fallo

En producción (`Afinn`, con `Adevv 0.5.0`) se han detectado dos fallos en la integración del arnés `codex` dentro de `skills/orquestar/orquestar.py`:

1. **[CRÍTICO] `codex exec resume` falla siempre en `base_comando_agente` por pasar `--sandbox` (`skills/orquestar/orquestar.py`, líneas 1180-1185)**:
   - **Síntoma**: Cuando un agente (`hades`, `clio`, `cronos`) o `gateway.py` (`invocar`) usa el arnés `codex`, nunca reutiliza la sesión (`sesion`) entre llamadas de la misma tarea y abre una sesión nueva en cada invocación.
   - **Causa raíz**: En `base_comando_agente` (líneas 1181-1183) se construye el comando de reanudación pasando `'--sandbox', 'workspace-write'`:
     `['codex', 'exec', 'resume', sesion, '--json', '-c', 'approval_policy="never"', '--sandbox', 'workspace-write', '-']`.
     El subcomando `codex exec resume` de la CLI de Codex no acepta el flag `--sandbox` (termina inmediatamente con `unexpected argument '--sandbox' found`). Al devolver `codigo != 0`, el bloque de la línea 1224 (`if es_reanudacion and codigo != 0 and espera_cuota(salida) is None:`) captura el fallo en silencio y relanza `codex exec` desde cero (`sesion=None`).
   - **Comportamiento esperado**: En `base_comando_agente(harness, prompt, sesion=None)`, dentro de la rama `if sesion:` de `codex`, sustituir `'--sandbox', 'workspace-write'` por `'-c', 'sandbox_mode="workspace-write"'` (soportado por `codex exec resume`).

2. **[CONTABILIDAD] Doble conteo de tokens cacheados e inflación ×8 del coste USD en el arnés `codex` (`skills/orquestar/orquestar.py`, líneas 1098-1101)**:
   - **Síntoma**: En `orquestar_metricas.jsonl` y en `--metricas`, todas las ejecuciones de `codex` muestran `dev_tokens_originales` casi idéntico a `dev_tokens_cache` (ej. `entrada: 7624556`, `cache_leida: 7469568`), duplicando el total de tokens (también en la ventana de 5 h de `consumo_cuotas`) y multiplicando por ~8 el coste estimado en USD.
   - **Causa raíz**: En la salida JSONL de OpenAI/Codex (`turn.completed` -> `usage`), `input_tokens` es el total de tokens de entrada (incluyendo `cached_input_tokens`), a diferencia de Claude (`inputTokens`) y `agy` (`input_tokens`), donde el campo reporta únicamente la entrada no cacheada. En `lanzar()` (líneas 1098-1101) se guarda `uso.get('input_tokens')` directamente en `'entrada'`, por lo que `metricas.py` suma los tokens cacheados dos veces y los tarifica tanto a precio de entrada sin caché ($2.50/M) como a precio de caché ($0.25/M).
   - **Comportamiento esperado**: Al construir el diccionario de uso de `codex` en `lanzar()` (`skills/orquestar/orquestar.py`, línea 1099), restar `cached_input_tokens` de `input_tokens`: guardar en `'entrada'` el valor `max(0, (uso.get('input_tokens') or 0) - (uso.get('cached_input_tokens') or 0))`.

## 📋 Reproducir

1. Invocar `base_comando_agente('codex', 'hola', sesion='th-123')` y comprobar que incluye `--sandbox workspace-write`, rechazado por `codex exec resume`.
2. Simular en `lanzar()` un evento JSONL `turn.completed` de `codex` con `{"type": "turn.completed", "usage": {"input_tokens": 1000, "cached_input_tokens": 800, "output_tokens": 50}}` y comprobar que `m['modelos'][modelo]['entrada']` vale `1000` en lugar de `200`.

## 📋 Evidencias

- Registros de `orquestar_metricas.jsonl` en `Afinn` (`Adevv 0.5.0`) con `entrada: 7624556` y `cache_leida: 7469568` en ejecuciones de `codex`, y ausencia de reutilización de `sesion` en llamadas sucesivas a `hades` con `codex`.
