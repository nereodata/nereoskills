---
id: B-ADV-0054
title: "Subprocesos de arnés colgados bloquean indefinidamente el orquestador sin señales de vida ni salto a reserva"
type: bug
weight: 5
dificultad: media
version: "v1.3.6"
status: completed
created_at: 2026-11-21
updated_at: 2026-11-21
---

# B-ADV-0054: Subprocesos de arnés colgados bloquean indefinidamente el orquestador sin señales de vida ni salto a reserva

## 🎯 Descripción del Fallo

**Causa raíz:**
1. En `skills/orquestar/perfiles.py`, `lanzar()` ejecutaba `proc.communicate()` bloqueante sin límite de tiempo por defecto (`timeout=None` en `_invocar_con_reservas`) ni lectura en streaming. Cuando `codex` (o `claude`/`agy`) completaba su turno y emitía su evento JSON final pero él o algún subproceso descendiente mantenía abierto el descriptor de `stdout`, `proc.communicate()` quedaba colgado indefinidamente esperando `EOF` (incluso el bloque `except subprocess.TimeoutExpired` ejecutaba un segundo `proc.communicate()` sin timeout, y en Windows `taskkill /T` fallaba en terminar nietos si el proceso raíz ya había salido).
2. `claude` y `agy` se invocaban con `--output-format json` (salida única al final), sin emitir eventos de actividad durante el turno que permitieran vigilar inactividad uniforme entre los tres arneses (`codex`, `claude`, `agy`).
3. En `skills/orquestar/orquestar.py`, `_invocar_con_reservas` devolvía directamente `codigo == 124` ante un timeout en vez de conmutar al siguiente candidato de `reserva`.

**Comportamiento esperado:**
- `claude` (`-p --verbose --output-format stream-json`), `agy` (`--output-format stream-json`) y `codex` (`--json`) emiten todos eventos JSONL de actividad en tiempo real durante el turno.
- `lanzar()` aísla el árbol de procesos (`Job Object` en Windows con `KILL_ON_JOB_CLOSE` / nueva sesión en POSIX), lee `stdout` y `stderr` de forma no bloqueante en hilos actualizando el latido de actividad y aplica tres cortafuegos:
  1. **Gracia tras evento JSON final o tras salida del proceso padre (`10 s` por defecto):** termina descendientes que retengan los pipes abiertos y devuelve el resultado ya emitido sin bloquear.
  2. **Watchdog de inactividad (`inactividad_s`, `900 s` por defecto):** si el arnés deja de emitir cualquier señal de vida durante el umbral configurado, termina el árbol y devuelve `124` (`inactividad: True`).
  3. **Tope total por paso (`timeout_s`, `2700 s` por defecto):** corta cualquier bucle infinito que siga emitiendo salida y devuelve `124` (`timeout: True`).
- Si un intento termina con `124` y el objetivo del paso aún no quedó completado en disco, `_invocar_con_reservas` registra la métrica y conmuta automáticamente al siguiente agente de `reserva` (igual que `gateway.invocar` en conversación de Telegram).

## 📋 Reproducir
1. Ejecutar un paso con `codex` (o `claude`/`agy`) cuyo subproceso emite el evento final (`turn.completed` / `result`) pero deja un proceso hijo con `stdout` heredado abierto, o queda congelado sin emitir eventos.
2. Antes de este cambio, `orquestar.py` permanecía detenido indefinidamente sin devolver el control ni probar la `reserva`.

## Resolución
- **Causa:** pérdida en `v1.3.0` del aislamiento por `Job Object`/grupo, de la lectura en streaming con gracia post-JSON y de límites por defecto, más ausencia de `stream-json` en `claude`/`agy` y de conmutación a `reserva` ante `124`.
- **Solución:** activado `stream-json` en `claude` y `agy` (manteniendo compatibilidad con `json`), implementados `_TrabajoWindows`, `_proceso_agrupado`, lectura en streaming con latido de inactividad, gracia post-JSON y tope por defecto en `skills/orquestar/perfiles.py`, y añadida conmutación automática a `reserva` ante `124` en `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py`.
- **Verificación:** regresiones reales con subprocesos y nietos heredando pipes, inactividad, `stream-json` de los tres arneses y conmutación a `reserva` en `tests/test_orquestar.py` y `tests/test_telegram_gateway.py`, más suite completa y `ruff`.
