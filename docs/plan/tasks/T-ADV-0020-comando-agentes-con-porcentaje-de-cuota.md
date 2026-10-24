---
id: T-ADV-0020
title: "Comando independiente /agentes (--agentes) con porcentaje de cuota consumida por modelo y limpieza de /estado"
type: funcional
weight: 250
dificultad: media
version: "v0.5.0"
status: planned
depende_de: ["T-ADV-0019"]
origen: "Separar la información de agentes de /estado hacia /agentes mostrando el % de cuota consumida de cada modelo definido"
created_at: 2026-10-24
updated_at: 2026-10-24
---

# T-ADV-0020: Comando independiente /agentes (--agentes) con porcentaje de cuota consumida por modelo y limpieza de /estado

## 🎯 Objetivo de Negocio
Retirar el listado de agentes y modelos de `/estado` (`parte()` y `resumen()`) para que `/estado` vuelva a ser conciso, y mover toda la información de agentes, modelos por dificultad/reserva y cuota a un comando dedicado `/agentes` (y `/agents` en Telegram, más `adevv orquestar --agentes` / `--agents` en CLI), mostrando para cada modelo definido en `orchestration.json` el **porcentaje (`%`) de cuota consumida** en la ventana activa.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Limpieza de `/estado` y `--estado`):** `parte(root)` y `resumen(root)` en `skills/orquestar/orquestar.py` dejan de imprimir el bloque de agentes configurados y tokens por modelo de las últimas 5 h, manteniendo únicamente el estado del bucle, la fase, la versión abierta, el backlog y el resumen general.
- [ ] **CA-M-2 (Comando `/agentes` / `/agents` en Telegram y `--agentes` / `--agents` en `orquestar.py`):** Se añade en `skills/orquestar/orquestar.py` la función `informe_agentes(root, docs='docs/requirements')` expuesta mediante `--agentes` / `--agents` en CLI y mediante los comandos `/agentes` y `/agents` en `skills/telegram_gateway/gateway.py` (incluidos también en `/ayuda`). Muestra siempre —incluso cuando el bucle está parado en `FIN` o `PARAR`— los roles definidos en `orchestration.json` (`artemisa`, `hades`, `atenea`, `clio`, `cronos`), sus modelos por dificultad y sus reservas, indicando además cuáles aplican al paso/tarea actual si hay uno pendiente.
- [ ] **CA-M-3 (Porcentaje `%` de cuota consumida por cada modelo definido):** Para cada modelo único (`harness/model`) presente en `orchestration.json` (incluyendo dificultades y reservas), `informe_agentes(root)` muestra el **porcentaje de cuota consumido (`X.X%`)** y la hora de reinicio si aplica:
  1. Si el modelo tiene un evento de agotamiento (`sin_cuota` / `cuota_propia` / `orquestar.espera`) aún vigente en `orquestar_metricas.jsonl`, muestra `100.0% consumido (agotado hasta HH:MM, faltan X min)`.
  2. Para modelos de `codex`, si existe información reciente de `rate_limits.primary.used_percent` (y `resets_at` vigente) en `~/.codex/sessions/**/*.jsonl`, utiliza ese porcentaje real reportado por Codex (`X.X% consumido · resetea HH:MM`).
  3. Para el resto de modelos (`agy`, `claude` o cuando no hay `rate_limits` nativo vigente), calcula el porcentaje consumido en la ventana móvil de las últimas 5 horas (`min(100.0, round(tokens_5h * 100.0 / limite_tokens_5h, 1))`) frente al límite de referencia de 5 h del modelo (configurable opcionalmente con `cuota_tokens_5h` en el rol/modelo en `orchestration.json`, o usando topes de referencia por familia de modelo: p. ej. Flash 20M, Argon/Pro 5M, Opus/Sonnet 5M, GPT 10M), mostrando `X.X% consumido (tokens_5h / limite_5h tokens en 5 h)`.
- [ ] **CA-M-4 (Pruebas unitarias y documentación):** Pruebas unitarias en `skills/orquestar/` y `skills/telegram_gateway/` verifican que `/estado` ya no incluye el bloque de agentes, que `/agentes` y `--agentes` listan los roles y el `%` de cuota de cada modelo (tanto con `rate_limits` de Codex, como por cálculo de ventana de 5 h y al `100%` en agotamiento vigente), y se actualiza `SKILL.md` en ambas skills.
