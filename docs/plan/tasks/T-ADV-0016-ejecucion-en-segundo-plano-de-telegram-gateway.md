---
id: T-ADV-0016
title: "Ejecución en segundo plano de adevv telegram (--fondo, --parar) y auto-arranque desde orquestar"
type: funcional
weight: 400
dificultad: media
version: "v0.4.0"
status: planned
depende_de: ["T-ADV-0015"]
origen: "Gestión desatendida del gateway de Telegram sin ocupar una terminal dedicada"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0016: Ejecución en segundo plano de adevv telegram (--fondo, --parar) y auto-arranque desde orquestar

## 🎯 Objetivo de Negocio
Permitir que el gateway de Telegram se gestione en segundo plano con `adevv telegram --fondo` y `adevv telegram --parar` igual que el bucle, que `adevv/processes.py` no confunda el proceso del gateway con un bucle de orquestación activo al actualizar/sincronizar, y que `adevv orquestar` levante automáticamente el gateway en segundo plano cuando el proyecto tenga credenciales de Telegram configuradas.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (`--fondo` y `--parar` en `gateway.py`):** `skills/telegram_gateway/gateway.py` añade `--fondo` (lanza el gateway desacoplado escribiendo su PID en `telegram.pid` y salida en `telegram.log`, verificando que no haya ya un `telegram.pid` vivo) y `--parar` (señaliza parada mediante `telegram.parar` o termina el proceso registrado y limpia `telegram.pid` / `telegram.parar`). `telegram.pid`, `telegram.log` y `telegram.parar` se incluyen en `PROPIOS` de `orquestar.py` para quedar excluidos de git.
- [ ] **CA-M-2 (Auto-arranque desde `orquestar.py`):** Al iniciar `bucle()` o `en_fondo()` en `skills/orquestar/orquestar.py` (en ejecución real, no en `--estado`), si `telegram(root)` devuelve credenciales válidas y no hay un `telegram.pid` con proceso vivo en `root`, lanza automáticamente el gateway en segundo plano (`gateway.py --fondo` o función equivalente) sin bloquear ni abortar el bucle si falla.
- [ ] **CA-M-3 (Compatibilidad con clasificación de procesos de gateway):** En `skills/telegram_gateway/gateway.py`, `--fondo` lanza el subproceso invocando `gateway.py` para que `adevv/processes.py` (que ya clasifica `gateway.py` y `adevv telegram` como `"gateway"` y no como `"bucle"` sin requerir modificar `adevv/processes.py`, conforme a `DEC-P09`) no reporte el gateway en escucha como «bucle en marcha» ni bloquee actualizaciones o sincronización de arneses.
- [ ] **CA-M-4 (Pruebas y documentación):** Pruebas unitarias en `skills/telegram_gateway/test_gateway_fondo.py` (o en `tests/test_telegram_gateway.py` y `tests/test_orquestar.py`, conforme a `DEC-P09` para operar dentro de `skills/`); documentación actualizada en `skills/telegram_gateway/SKILL.md` y `skills/orquestar/SKILL.md`.
