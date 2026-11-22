---
id: B-ADV-0056
title: "Recuperar reintentos periódicos con espera creciente ante fallos técnicos del arnés y sondeo de cuotas sin hora"
type: bug
weight: 10
dificultad: media
version: "v1.3.7"
status: completed
created_at: 2026-11-22
updated_at: 2026-11-22
---

# B-ADV-0056: Recuperar reintentos periódicos con espera creciente ante fallos técnicos del arnés y sondeo de cuotas sin hora

## 🎯 Descripción del Fallo

**Causa raíz:**
Al reescribir el motor en `v1.3.0` (`T-ADV-0042`) se perdieron dos protecciones de resiliencia de `v1.0.0` (`B-ADV-0011` y `B-ADV-0020`):
1. En `_invocar_con_reservas`, un fallo técnico del arnés (`codigo != 0` distinto de cuota, suscripción denegada o `124`, como un error de red o `5xx`) no probaba los candidatos de `reserva`.
2. Cuando todos los candidatos fallaban por causa técnica (red caída, `5xx` o timeout `124`), `bucle()` reintentaba al instante sin pausa e incrementaba el contador de `sin progreso`, llegando a marcar la tarea como `status: blocked` en pocos segundos durante un microcorte temporal.
3. Las respuestas de cuota sin hora explícita aplicaban una espera fija de `1800 s` (`30 min`) en lugar del sondeo periódico de `300 s` (`cuota_reintento_s` en `orchestration.json`), y `espera_cuota` no reconocía formatos compuestos `XhYmZs` (ej. `56h48m9s`).

**Comportamiento esperado:**
1. En `_invocar_con_reservas`, cualquier fallo técnico (`codigo != 0`) sin haber dejado el objetivo completado en disco prueba en orden los candidatos de `reserva` (salvo `estricto: true`).
2. Si todos los candidatos devuelven fallo técnico (`codigo != 0`), `bucle()` ejecuta reintentos periódicos con espera creciente (`60 s`, `300 s`, `900 s` por defecto; configurable con `--reintentos-arnes` / `reintentos_arnes` y `esperas_reintento_s` en `orchestration.json`), publicando el estado en `orquestar.espera`, respetando `--parar` y **sin consumir `--max-pasos` ni el contador de `sin progreso` de la ficha**. Solo si agota los reintentos periódicos detiene el bucle y envía aviso por Telegram con la cola de salida del arnés.
3. Para errores de cuota sin hora explícita, se usa `cuota_reintento_s` (`300 s` por defecto) y se soporta el parseo de duraciones compuestas `XhYmZs`.

## Resolución
- **Solución:** actualizados `espera_cuota` y `fallo_cuota` en `skills/orquestar/perfiles.py` (`CUOTA_REINTENTO_S = 300`, soporte `XhYmZs` y `cuota_reintento_s`); generalizada la conmutación a `reserva` ante cualquier `codigo != 0` en `_invocar_con_reservas` y añadido backoff periódico cooperativo (`_dormir_con_espera`, `--reintentos-arnes`, `ESPERAS_REINTENTO_ARNES_S = (60, 300, 900)`) en `skills/orquestar/orquestar.py`.
- **Verificación:** pruebas unitarias en `tests/test_orquestar.py`, revisión independiente, suite completa y `ruff`.
