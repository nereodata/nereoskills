---
id: T-ADV-0015
title: "Control remoto del bucle (/lanzar, /parar) y consulta de /metricas desde Telegram"
type: funcional
weight: 300
dificultad: media
version: "v0.4.0"
status: planned
depende_de: ["T-ADV-0013", "T-ADV-0014"]
origen: "Operación remota completa del orquestador desde el bot de Telegram"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0015: Control remoto del bucle (/lanzar, /parar) y consulta de /metricas desde Telegram

## 🎯 Objetivo de Negocio
Permitir al usuario autorizado controlar el ciclo de vida del bucle (`/lanzar` y `/parar`) y consultar el resumen de métricas (`/metricas`) directamente desde Telegram sin necesitar acceso a la terminal del ordenador.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Comando `/parar` / `/stop` en Telegram):** Cuando un usuario autorizado envía `/parar` o `/stop` en `skills/telegram_gateway/gateway.py`, si existe `orquestar.pid` crea el fichero `orquestar.parar` (tras `motor.excluir(root)`) y confirma que el bucle se detendrá al terminar el paso en curso; si no hay bucle en marcha, informa de que ya está parado.
- [ ] **CA-M-2 (Comando `/lanzar` / `/run` en Telegram):** Cuando un usuario autorizado envía `/lanzar` o `/run`, si ya existe `orquestar.pid` informa de que el bucle ya está en marcha; si no, invoca el arranque en segundo plano del bucle (`motor.en_fondo(root)`) y responde confirmando el lanzamiento y el siguiente paso previsto.
- [ ] **CA-M-3 (Comando `/metricas [filtro]` / `/metrics [filtro]` en Telegram):** Cuando un usuario autorizado envía `/metricas` o `/metrics` (con argumento opcional de versión, por defecto `ultima`), el gateway devuelve un resumen compacto con los tiempos, tokens y coste estimado por tarea de las versiones solicitadas reutilizando el módulo de métricas de `T-ADV-0013`.
- [ ] **CA-M-4 (Actualización de `/ayuda`, documentación y pruebas):** `AYUDA` en `gateway.py` y `skills/telegram_gateway/SKILL.md` documentan `/lanzar`, `/parar` y `/metricas`; `tests/test_telegram_gateway.py` cubre los tres nuevos comandos y sus casos borde (bucle ya en marcha, bucle ya parado).
