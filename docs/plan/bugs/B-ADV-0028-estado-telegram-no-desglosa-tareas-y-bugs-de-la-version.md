---
id: B-ADV-0028
title: "/estado en Telegram no indica por separado las tareas y los bugs de la versión"
type: bug
weight: 100
dificultad: sencilla
version: "v1.1.0"
status: completed
origen: "Incidencia comunicada por el usuario (2026-11-06)"
created_at: 2026-11-06
updated_at: 2026-11-07
---

# B-ADV-0028: `/estado` en Telegram no indica por separado las tareas y los bugs de la versión

## 🎯 Triaje de Alcance

- **base_calidad:** `c6ecf75e57cf0edb6751cd9c22179f323bd5bd7d`
- **Subfase A: Definición** → `[SKIP]` (El fallo no añade ni altera requisitos funcionales de alto nivel; es una corrección de formato y agrupación en la función `parte` de Telegram).
- **Subfase B: Diseño** → `[SKIP]` (Solución localizada en `skills/orquestar/orquestar.py::parte`, sin decisiones arquitectónicas no obvias).
- **Subfase C1: Pruebas** → `[EXEC]` (Tests unitarios en `tests/test_telegram_gateway.py` reproduciendo la agrupación por `vkey` con versiones mixtas y la distinción explícita de tareas y bugs cerrados/totales).
- **Subfase C2: Corrección** → `[EXEC]` (Ajuste de `parte()` en `skills/orquestar/orquestar.py` para agrupar por `vkey` y desglosar tareas cerradas/totales y bugs cerrados/totales).
- **Subfase D: QA** → `[EXEC]` (Revisión de Hades sobre el delta completo).
- **Subfase E: Documentación** → `[SKIP]` (No altera guías de usuario ni interfaces públicas de comandos).
- **Subfase F: Cierre** → `[EXEC]` (Verificación en verde, calidad del delta y commit semántico `fix(B-ADV-0028)`).
- **Verificación al cierre**: `python -m unittest tests.test_telegram_gateway` (garantiza el comportamiento íntegro del gateway de Telegram, `/estado`, desglose de tareas y bugs y agrupación por `vkey`).

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
