---
id: B-ADV-0024
title: "El gateway trata las marcas de cuota sin hora como agotamiento de 30 min (lo que B-ADV-0020 corrigió en el bucle)"
type: bug
weight: 1500
dificultad: media
version: "v1.1.0"
status: completed
origen: "T-ADV-0026 × B-ADV-0020; revisar-version v1.0 (docs/review/versions/v1.0-arquitectura.md), H-03 🟡"
created_at: 2026-10-27
updated_at: 2026-11-07
---

# B-ADV-0024: El gateway trata las marcas de cuota sin hora como agotamiento de 30 min

## 🎯 Triaje de Alcance

- **base_calidad:** `3f122a1835c25ba7424b98c60c6c4f69845733d2`
- **Subfase A: Definición** → `[EXEC]` (Escenario BDD en `skills/telegram_gateway/features/telegram_gateway.feature` especificando el comportamiento del gateway ante fallos de cuota sin hora: clasificación como cuota supuesta, sondeo tras vencer `cuota_reintento_s` y recuperación tras respuesta exitosa).
- **Subfase B: Diseño** → `[EXEC]` (`docs/design/B-ADV-0024-design.md`: documentar la unificación del ciclo de cuotas en `invocar()` y `conversar()` mediante `motor.fallo_cuota`, `motor.configuraciones_con_cuota`, `motor.recuperar_cuota`, y alineación con B-ADV-0020).
- **Subfase C1: Pruebas** → `[EXEC]` (Pruebas unitarias en `skills/telegram_gateway/test_reservas.py` reproduciendo la clasificación con `fallo_cuota` en `invocar()`, el descarte temporal y posterior sondeo según `cuota_reintento_s` en `conversar()`, el registro de `cuota_recuperada` al responder con éxito, y el aviso de créditos una vez por episodio. Fase roja y revisión de pruebas de Hades).
- **Subfase C2: Corrección** → `[EXEC]` (Modificación en `skills/telegram_gateway/gateway.py` para invocar `motor.fallo_cuota`, filtrar candidatos con `motor.configuraciones_con_cuota` respetando sondeos supuestos, y llamar a `motor.recuperar_cuota` en respuestas exitosas).
- **Subfase D: QA** → `[EXEC]` (Revisión de Hades sobre el delta completo).
- **Subfase E: Documentación** → `[EXEC]` (Actualizar `skills/telegram_gateway/SKILL.md` para alinear la redacción con el sondeo de cuotas supuestas e intervalo de sondeo de B-ADV-0020).
- **Subfase F: Cierre** → `[EXEC]` (Verificación en verde, calidad con `adevv orquestar --calidad --base <base_calidad> --aplicar`, `status: completed` y commit semántico `fix(B-ADV-0024)`).
- **Verificación al cierre**: `python -m unittest skills/telegram_gateway/test_reservas.py tests/test_telegram_gateway.py` (garantiza el funcionamiento íntegro de reservas, cuotas, sesiones y comandos del gateway).

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
