---
id: B-ADV-0053
title: "El bucle lanzado desde un agente IA muere al cerrarse el comando y nadie avisa de la caída"
type: bug
weight: 5
dificultad: media
version: "v1.3.5"
status: completed
created_at: 2026-11-18
updated_at: 2026-11-18
---

# B-ADV-0053: El bucle lanzado desde un agente IA muere al cerrarse el comando y nadie avisa de la caída

## 🎯 Descripción del Fallo

**Causa raíz:**
1. `skills/orquestar/SKILL.md` documentaba únicamente `adevv orquestar --fondo`. En los arneses de agentes IA (Antigravity, Claude Code, Codex), `--fondo` lanza un hijo y termina el proceso padre de inmediato (`exit 0`), provocando que el recolector del arnés mate todo el árbol de subprocesos (`TerminateProcess` / `SIGKILL`) al dar por cerrado el comando — incluso si la herramienta se invocó con `IsDaemon: true` / `run_in_background: true`. Además, al ejecutar `adevv orquestar` sin `--fondo` como demonio del arnés, `bucle()` solo escribía en `stdout` y no en `orquestar.log`.
2. Cuando el bucle moría de forma abrupta (`TerminateProcess` / `SIGKILL` o excepción no controlada), `orquestar.pid` quedaba huérfano en disco apuntando a un PID inexistente: ni `adevv orquestar --estado` ni `parte()` distinguían `parado` de `caído`, ni `gateway.py` notificaba la caída inesperada por Telegram durante el polling.

**Comportamiento esperado:**
- `SKILL.md` (y `README.md`) instruyen explícitamente a los agentes IA a lanzar `adevv orquestar` sin `--fondo` mediante el modo demonio/background nativo de su herramienta y verificar el estado tras arrancar, reservando `--fondo` para terminales humanas.
- `bucle()` en primer plano vuelca también su salida a `orquestar.log` (sin duplicar cuando `stdout` ya apunta a `orquestar.log`).
- `adevv orquestar --estado` y `parte()` informan explícitamente cuando existe un `orquestar.pid` huérfano (`caído`), y `bucle()` notifica errores no controlados vía `avisar`.
- `gateway.py` detecta en su bucle de escucha cualquier `orquestar.pid` huérfano, envía aviso inmediato por Telegram y limpia la marca huérfana para no repetir el aviso.

## 📋 Reproducir
1. Invocar `adevv orquestar --fondo` desde la herramienta de comandos de un agente IA: el comando padre retorna `0` con `lanzado en segundo plano (pid X)` y el arnés termina inmediatamente el árbol de procesos dejando `orquestar.pid` huérfano.
2. Consultar `adevv orquestar --estado` o esperar al gateway de Telegram: antes del fix se mostraba `parado` sin aviso de caída; al relanzarlo sin `--fondo` como demonio, no se actualizaba `orquestar.log`.

## Resolución
- **Causa:** uso de `--fondo` en sesiones efímeras de agentes IA (cuyo arnés mata el árbol al salir el proceso raíz), ausencia de escritura en `orquestar.log` en modo primer plano y falta de detección/notificación de `orquestar.pid` huérfano.
- **Solución:** actualizadas instrucciones en `skills/orquestar/SKILL.md`, `skills/telegram_gateway/SKILL.md` y `README.md`; añadido `_salida_con_log`, `pid_huerfano`, diagnóstico de caída en `--estado`/`parte()` y aviso ante excepción en `skills/orquestar/orquestar.py`; añadida vigilancia `vigilar_caida_bucle` en `skills/telegram_gateway/gateway.py`.
- **Verificación:** pruebas unitarias de regresión en `tests/test_orquestar.py`, `tests/test_telegram_gateway.py` y `tests/test_instructions_cleanliness.py`, más formato/lint con `ruff`.
