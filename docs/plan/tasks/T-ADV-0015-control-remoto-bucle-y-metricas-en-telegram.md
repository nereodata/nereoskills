---
id: T-ADV-0015
title: "Control remoto del bucle (/lanzar, /parar) y consulta de /metricas desde Telegram"
type: funcional
weight: 300
dificultad: media
version: "v0.4.0"
status: completed
depende_de: ["T-ADV-0013", "T-ADV-0014"]
origen: "Operación remota completa del orquestador desde el bot de Telegram"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0015: Control remoto del bucle (/lanzar, /parar) y consulta de /metricas desde Telegram

## 🎯 Objetivo de Negocio
Permitir al usuario autorizado controlar el ciclo de vida del bucle (`/lanzar` y `/parar`) y consultar el resumen de métricas (`/metricas`) directamente desde Telegram sin necesitar acceso a la terminal del ordenador.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Comando `/parar` / `/stop` en Telegram):** Cuando un usuario autorizado envía `/parar` o `/stop` en `skills/telegram_gateway/gateway.py`, si existe `orquestar.pid` crea el fichero `orquestar.parar` (tras `motor.excluir(root)`) y confirma que el bucle se detendrá al terminar el paso en curso; si no hay bucle en marcha, informa de que ya está parado.
- [x] **CA-M-2 (Comando `/lanzar` / `/run` en Telegram):** Cuando un usuario autorizado envía `/lanzar` o `/run`, si ya existe `orquestar.pid` informa de que el bucle ya está en marcha; si no, invoca el arranque en segundo plano del bucle (`motor.en_fondo(root)`) y responde confirmando el lanzamiento y el siguiente paso previsto.
- [x] **CA-M-3 (Comando `/metricas [filtro]` / `/metrics [filtro]` en Telegram):** Cuando un usuario autorizado envía `/metricas` o `/metrics` (con argumento opcional de versión, por defecto `ultima`), el gateway devuelve un resumen compacto con los tiempos, tokens y coste estimado por tarea de las versiones solicitadas reutilizando el módulo de métricas de `T-ADV-0013`.
- [x] **CA-M-4 (Actualización de `/ayuda`, documentación y pruebas):** `AYUDA` en `gateway.py` y `skills/telegram_gateway/SKILL.md` documentan `/lanzar`, `/parar` y `/metricas`; pruebas unitarias en `skills/telegram_gateway/test_gateway_control.py` (o `tests/test_telegram_gateway.py`, conforme a `DEC-P09` para operar dentro de `skills/`) cubren los tres nuevos comandos y sus casos borde (bucle ya en marcha, bucle ya parado).

## Triaje
- Subfase A: [EXEC] Escenarios de control remoto y consulta de métricas en el feature existente de Telegram.
- Subfase B: [EXEC] Integración con arranque desacoplado y consulta existente; argumentos del gateway aislados del hijo.
- Subfase C1: [EXEC] Pruebas aisladas en skills/telegram_gateway/test_gateway_control.py, sin Telegram ni procesos reales.
- Subfase C2: [EXEC] Gateway y parámetro opcional del arranque del motor, conservando el contrato CLI.
- Subfase D: [EXEC] Hades sobre el delta completo.
- Subfase E: [EXEC] Skill del gateway y revisión de versión; changelog delegado a /release.
- Subfase F: [EXEC] Cierre y commit.
- Verificación al cierre: `python -m unittest discover -s skills/telegram_gateway -p test_gateway_control.py`, `python -m unittest discover -s tests -p test_telegram_gateway.py`, `python -m unittest discover -s skills/orquestar -p test_metricas.py` cubren comandos, regresión del gateway, métricas y arranque; compilación Python del delta y `git diff --check`. No hay herramientas de lint/tipado/secretos configuradas ni cambios de dependencias; inspección de secretos sobre el delta.

## Resultado y decisiones sin preguntar
- 40 pruebas del triaje verdes (11 nuevas, 19 gateway y 10 métricas), compilación Python y whitespace verificados con `adevv orquestar --verificar`; evidencia reutilizada para el mismo árbol `6085703d6f` y aceptada por Hades.
- Rojo inicial: 11 tests y 15 fallos de aserción por comandos ausentes; salida en `%TEMP%/T-ADV-0015-red.txt`, resumida en el reporte de pruebas.
- Hades: especificación 9.4/10, pruebas 9.6/10 y código 9.7/10, todos APROBADO. Observaciones bajas con destino descartar aplicadas; sin deuda adicional.
- Se conserva detección por PID; se aíslan argumentos del gateway en el arranque compartido; métricas reutilizan lectura/agregación CLI y filtro `ultima`. Diseño y validación humana diferida en docs/design/T-ADV-0015-design.md y docs/review/versions/v0.4-revision.md. Changelog delegado a /release.
