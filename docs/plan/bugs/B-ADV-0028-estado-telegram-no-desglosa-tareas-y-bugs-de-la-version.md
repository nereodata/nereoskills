---
id: B-ADV-0028
title: "/estado en Telegram no indica por separado las tareas y los bugs de la versión"
type: bug
weight: 100
dificultad: sencilla
version: "v1.1.0"
status: planned
origen: "Incidencia comunicada por el usuario (2026-11-06)"
created_at: 2026-11-06
updated_at: 2026-11-06
---

# B-ADV-0028: `/estado` en Telegram no indica por separado las tareas y los bugs de la versión

## 🎯 Descripción del Fallo

**Causa raíz:** En `skills/orquestar/orquestar.py` (`parte`, líneas 2574–2600), el resumen que devuelve `/estado` (`/status`) en Telegram:
1. No distingue tareas (`paso == 'task-dev'`) de bugs (`paso == 'bug-fix'`) en la línea de la versión activa: solo imprime un único contador `*{v}:* {len(cuenta("completed"))}/{len(suyas)} cerradas`, sin indicar las tareas y los bugs de la versión.
2. Además, agrupa y filtra la versión con comparación literal `i['version'] == v` en lugar de `vkey(i['version']) == vkey(v)` (a diferencia de `estado()` en la línea 1181), por lo que si un bug de la versión se registra con formato corto (`v1.1` frente a `v1.1.0`, como hace `registrar_fallo_suite`), ni siquiera entra en `suyas`.

**Comportamiento observado:** Al consultar `/estado` en Telegram, solo aparece un conteo genérico (`X/Y cerradas`) que no muestra cuántos bugs tiene la versión (y omite los que usen `vX.Y` si las tareas usan `vX.Y.0`).

**Comportamiento esperado:** `/estado` debe agrupar la versión por `vkey` y mostrar explícitamente tanto las tareas como los bugs de la versión (por ejemplo, tareas cerradas/totales y bugs cerrados/totales de la versión, además de los que estén en curso o bloqueados).

## 📋 Reproducir

1. Tener en un proyecto tareas (`T-*`) y bugs (`B-*`) asignados a la versión activa (incluyendo variantes `v1.1` y `v1.1.0`).
2. Ejecutar `/estado` en Telegram (o `orquestar.parte(root)`).
3. Observar que la salida no indica los bugs de la versión junto con las tareas.

## 📋 Evidencias

- `skills/orquestar/orquestar.py`: función `parte` (líneas 2583–2592).
- `skills/telegram_gateway/gateway.py`: comando `/estado` / `/status` (línea 276–277).
