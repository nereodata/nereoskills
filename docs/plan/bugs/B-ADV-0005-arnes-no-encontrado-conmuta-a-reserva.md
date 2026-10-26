---
id: B-ADV-0005
title: "Un arnés no encontrado en el PATH para el bucle en vez de avisar y conmutar a la siguiente reserva"
type: bug
weight: 50
dificultad: media
version: "v0.7.0"
status: planned
depende_de: []
created_at: 2026-10-26
updated_at: 2026-10-26
---

# B-ADV-0005: Un arnés no encontrado en el PATH para el bucle en vez de avisar y conmutar a la siguiente reserva

## 🎯 Descripción del Fallo

**Causa raíz**: cuando el ejecutable del arnés configurado (perfil principal o reserva) no se encuentra, `orquestar.py` termina con `sys.exit(...)` en lugar de tratarlo como un fallo recuperable de esa configuración:

- `comando()` (`skills/orquestar/orquestar.py:1055`), usado por `ejecutar()` en el bucle de pasos con reservas (`configs_a_probar`, ~línea 2101).
- Bucle de agentes con reservas (`skills/orquestar/orquestar.py:1278`).
- El gateway de Telegram tiene el mismo patrón (`skills/telegram_gateway/gateway.py:163`, `RuntimeError`).

**Comportamiento observado**: si p. ej. `codex` no está instalado o no está en el PATH, el bucle desatendido se detiene por completo aunque haya reservas con otros arneses disponibles.

**Comportamiento esperado**:
1. Si el arnés de una configuración no se encuentra, se emite un warning por consola (`[orquestar] no se encuentra el arnés "X"; conmutando a reserva...`) y se registra en métricas.
2. El mismo warning se envía por Telegram con `avisar()` (nuevo evento, filtrable como el resto).
3. Se pasa a la siguiente reserva, igual que al agotar cuota. La sesión anterior no se reutiliza si el arnés cambia.
4. Solo si **ninguna** configuración tiene un arnés disponible, el paso falla con un mensaje claro (y aviso por Telegram) en lugar de un `sys.exit` silencioso a mitad de reservas.

Fuera de alcance: el modo `--cmd` explícito (sin reservas) puede seguir abortando.

## 📋 Reproducir
1. En `orchestration.json`, configurar un rol con `harness: "codex"` y una `reserva` con `harness: "claude"`.
2. Quitar `codex` del PATH (o renombrar el ejecutable).
3. Lanzar `/orquestar` hasta un paso de ese rol.
4. Observado: el bucle termina con `No se encuentra el arnés "codex" en el PATH.`. Esperado: warning (consola + Telegram) y ejecución con la reserva `claude`.

## 📋 Evidencias
- `skills/orquestar/orquestar.py:1055` y `:1278` — `sys.exit` dentro del flujo con reservas.
- `skills/telegram_gateway/gateway.py:163` — mismo patrón en el gateway.
