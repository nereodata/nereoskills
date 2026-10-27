---
id: B-ADV-0024
title: "El gateway trata las marcas de cuota sin hora como agotamiento de 30 min (lo que B-ADV-0020 corrigió en el bucle)"
type: bug
weight: 1500
dificultad: media
version: ""
status: backlog
origen: "T-ADV-0026 × B-ADV-0020; revisar-version v1.0 (docs/review/versions/v1.0-arquitectura.md), H-03 🟡"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0024: El gateway trata las marcas de cuota sin hora como agotamiento de 30 min

## 🎯 Descripción del Fallo

**Causa raíz:**
- `invocar()` (`skills/telegram_gateway/gateway.py`, hacia la línea 181) registra la cuota con `espera_cuota(salida)`, que sin hora devuelve 1800 s, y no usa `fallo_cuota`: no deja `cuota_tipo` ni avisa de créditos una vez por episodio.
- `conversar()` (línea ~212) descarta cualquier marca vigente de `consumo_cuotas`, también las supuestas.
- Es el tercer bucle de reservas paralelo, junto a `bucle()` y `agente()`.

**Comportamiento observado:** ante un `RESOURCE_EXHAUSTED` sin hora, la conversación evita ese modelo durante 30 min. Si es el único, responde «ningún arnés disponible» aunque la cuota ya se haya recuperado. El bucle, en cambio, vuelve a sondear el modelo cada `cuota_reintento_s` (300 s).

**Comportamiento esperado:** el gateway reutiliza `fallo_cuota` y la regla de sondeo de `configuraciones_con_cuota`, igual que el bucle. El contrato de `skills/telegram_gateway/SKILL.md` («salta cualquier modelo con cuota vigente») se alinea con la especificación de B-ADV-0020.

## 📋 Reproducir
1. Simular en la conversación de Telegram un arnés único que devuelve un agotamiento sin hora de reinicio.
2. Volver a escribir pasados 5 min con la cuota recuperada: el gateway sigue respondiendo «ningún arnés disponible».

## 📋 Evidencias
- `docs/review/versions/v1.0-arquitectura.md`, hallazgo H-03.
