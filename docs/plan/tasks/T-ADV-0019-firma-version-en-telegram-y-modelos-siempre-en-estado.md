---
id: T-ADV-0019
title: "Firma con la versión de Adevv al pie de todos los mensajes de Telegram"
type: funcional
weight: 200
dificultad: sencilla
version: "v0.5.0"
status: completed
depende_de: ["T-ADV-0018"]
origen: "Identificar en cada mensaje de Telegram con qué versión de Adevv se ha generado para ver si algún proyecto aún no ha actualizado"
created_at: 2026-10-24
updated_at: 2026-10-24
---

# T-ADV-0019: Firma con la versión de Adevv al pie de todos los mensajes de Telegram

## 🎯 Objetivo de Negocio
Incluir al pie de cada mensaje enviado por Telegram (tanto respuestas del gateway a comandos y conversación libre como avisos del bucle) la versión de Adevv con la que se está ejecutando ese proceso, para detectar de un vistazo si algún proyecto sigue corriendo con una versión anterior.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Firma de versión en respuestas del gateway y avisos del bucle):** Todos los mensajes enviados a Telegram desde `skills/telegram_gateway/gateway.py` (comandos `/estado`, `/agentes`, `/metricas`, `/tarea`, `/bug`, `/lanzar`, `/parar`, `/nuevo`, `/ayuda` y conversación libre) y desde `avisar()` en `skills/orquestar/orquestar.py` añaden al final una línea de firma con la versión de Adevv del proceso en ejecución (p. ej. `— Adevv v0.5.0`, deducida de su ruta en `~/.adevv/versions/<ver>/` o de `adevv.__version__` / `pyproject.toml`), y en conversación libre añade además el `harness/model` que respondió (`— Adevv v0.5.0 · agy/gemini-4-argon-medium`).
- [x] **CA-M-2 (Idempotencia de firma):** Si un texto ya contiene la firma final `— Adevv v...`, no se duplica al enviarse.
- [x] **CA-M-3 (Pruebas unitarias y documentación):** Pruebas unitarias en `skills/orquestar/` y `skills/telegram_gateway/` (conforme a `DEC-P09`/`DEC-P10`, dentro de las rutas autorizadas en `skills/`) verifican que tanto los comandos y el chat libre del gateway como los avisos del bucle llevan la firma de versión al pie.

## 🔬 Triaje de Alcance
- **Subfase A: Definición** → `[SKIP]` Formato e idempotencia de firma de versión en Telegram y avisos del bucle especificados en CA-M-1..CA-M-3 y DEC-P10.
- **Subfase B: Diseño** → `[EXEC]` Documento `docs/design/T-ADV-0019-design.md` con la resolución de versión de Adevv, mecanismo de firma al pie para respuestas y avisos, formato específico para conversación libre (`harness/model`) e idempotencia.
- **Subfase C1: Pruebas (Red Phase)** → `[EXEC]` Pruebas unitarias en `skills/orquestar/test_firma_telegram.py` y `skills/telegram_gateway/test_firma_gateway.py` para firma en comandos del gateway, conversación libre con arnés/modelo, avisos del bucle en `avisar()` e idempotencia.
- **Subfase C2: Implementación (Green Phase)** → `[EXEC]` Implementación en `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py` dentro de las rutas autorizadas `skills/`.
- **Subfase D: QA** → `[EXEC]` Revisión de Hades (`/review-code`) sobre el delta completo con `adevv orquestar --agente hades`.
- **Subfase E: Documentación** → `[EXEC]` Documentación de la firma de versión al pie en `skills/telegram_gateway/SKILL.md` y `skills/orquestar/SKILL.md`.
- **Subfase F: Cierre** → `[EXEC]` Cierre de tarea y commit semántico.
- **Verificación al cierre:** `python -m unittest skills/orquestar/test_firma_telegram.py skills/telegram_gateway/test_firma_gateway.py`
