---
id: B-ADV-0019
title: "Las pruebas envían avisos reales a Telegram con el token del entorno"
type: bug
weight: 10
dificultad: sencilla
version: "v1.0.0"
status: planned
depende_de: []
origen: "Reporte del usuario (2026-10-27): siguen llegando mensajes «[tmp…]» al bot de Afinn mientras el bucle trabaja en v1.0"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0019: Las pruebas envían avisos reales a Telegram con el token del entorno

## 🎯 Descripción del Fallo

**Causa raíz**: `tests/test_orquestar.py:943` (`test_bucle_promotes_difficulty_on_sin_progreso_and_retries`) ejecuta `motor.bucle()` sobre un proyecto temporal hasta `FIN`. Parchea `config`, `ejecutar`, `git`, `firma` y `estado`, pero no `enviar` ni `avisar`. El proyecto temporal no tiene `.env`, así que `credenciales()` usa `TELEGRAM_BOT_TOKEN` del entorno, que desde T-ADV-0030 sirve de respaldo para los avisos. Resultado: se envía `[tmpXXXX] ✅ Producto terminado: v0.1` de verdad.

**Comportamiento observado**: el bucle de v1.0 heredó del proceso que lo lanzó el token de `NereodataAfinnBot`, aunque la variable de usuario ya apunta al bot de Adevv. Cada vez que pasa la suite (cientos de verificaciones), llega un mensaje «[tmp…]» al chat de Afinn. B-ADV-0007 solo aisló `tests/test_cli_commands.py`.

**Diagnóstico**: se ejecutó la suite completa (`tests/`, `skills/orquestar`, `skills/telegram_gateway`) con un token falso y un `sitecustomize` que bloquea y registra cualquier llamada a `api.telegram.org`, también en los subprocesos. Solo esa prueba llamó a `sendMessage`.

**Comportamiento esperado**:
1. Ninguna prueba puede llegar a Telegram, venga de donde venga el token. Hace falta una protección común: por ejemplo, un `tests/__init__.py` o un módulo de soporte cargado por todas las suites (incluidas `skills/*/test_*.py`) que quite `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USER_IDS` y `TELEGRAM_CHAT_ID` del entorno y haga que `enviar()` falle en voz alta si se le llama sin parchear. Las pruebas que necesiten token lo definen ellas mismas, con el envío simulado.
2. Se corrige `test_bucle_promotes_difficulty_on_sin_progreso_and_retries` para que no dependa de esa protección (parchea `avisar` o `enviar`).
3. Prueba de regresión: con un token del entorno definido, ejecutar el bucle de prueba hasta `FIN` no hace ninguna petición de red.
4. La suite pasa en verde con y sin las variables `TELEGRAM_*` del entorno.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario lo ha pedido expresamente. Se puede tocar cualquier ruta necesaria (`tests/`, `skills/*/test_*.py`, `skills/orquestar/`).
