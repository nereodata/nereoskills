---
id: B-ADV-0032
title: "Subproceso de agy colgado tras emitir salida o escribir artefactos bloquea indefinidamente lanzar() y --agente"
type: bug
weight: 20
dificultad: media
version: "v1.1.1"
status: completed
created_at: 2026-11-08
updated_at: 2026-11-10
---

# B-ADV-0032: Subproceso de agy colgado tras emitir salida o escribir artefactos bloquea indefinidamente lanzar() y --agente

## 🎯 Descripción del Fallo

**Causa raíz:**
1. En `skills/orquestar/orquestar.py`, `lanzar()` invoca `agy` y `claude` con `--output-format json` mediante `subprocess.run(..., capture_output=True)` sin límite de tiempo (`timeout`) ni cierre forzado tras recibir la línea JSON final en `stdout`. Si `agy.EXE` (o un hijo que heredó los descriptores de `stdout`/`stderr`) no cierra el proceso al terminar su turno y tras escribir los artefactos o el JSON de salida, `lanzar()` permanece bloqueado indefinidamente esperando `EOF` y la salida del proceso.
2. En `agente()`, `base_comando_agente('agy', ...)` pasa el mandato por línea de comandos (`-p <prompt>`), pero `agente()` invoca igualmente `lanzar(cmd, root, harness, entrada=prompt_texto)` abriendo un pipe `stdin` y volcando de nuevo el prompt completo en lugar de cerrarlo con `stdin=subprocess.DEVNULL` como hace `ejecutar()`.

**Comportamiento observado:** durante ejecuciones desatendidas (p. ej. rondas de revisión de Hades en `ciclo-requisitos`), `agy.EXE` escribe todos los informes en disco y queda colgado sin terminar el proceso, dejando al agente invocador esperando toda la noche hasta que se mata manualmente el PID de `agy.EXE`.

**Comportamiento esperado:**
1. `agente()` invoca `lanzar()` con `entrada=None` cuando `harness == 'agy'`, asegurando `stdin=subprocess.DEVNULL`.
2. En `lanzar()`, cuando `agy` o `claude` con `--output-format json` ya han emitido su línea JSON final por `stdout` pero el proceso no termina dentro de un margen de gracia corto (`GRACIA_CIERRE_JSON_S = 10` s), se termina el árbol del proceso (`taskkill /F /T` en Windows / `kill` en POSIX) y se devuelve el resultado exitoso con sus métricas.
3. Si el subproceso supera el tiempo máximo de espera (`timeout`, por defecto `TIMEOUT_AGENTE_S = 1800` s en `agente()`, configurable mediante `timeout_s` en `orchestration.json` o `ORQUESTAR_TIMEOUT_AGENTE_S` / `ORQUESTAR_TIMEOUT_S`), se termina el árbol del proceso sin bloquear en `communicate()`, se registra `timeout: True` en las métricas y se devuelve el control inmediatamente.

## 📋 Reproducir
1. Invocar `adevv orquestar --agente hades` con arnés `agy` cuando el subproceso `agy.EXE` escribe los informes o el JSON final en `stdout` pero no finaliza el proceso ni cierra los descriptores de salida.
2. Observar que `lanzar()` bloquea indefinidamente sin devolver el control al proceso padre.

## 📋 Resolución
- En `skills/orquestar/orquestar.py`:
  - Añadido `_ejecutar_captura_json()` con lectura no bloqueante de `stdout`/`stderr` en hilos y detección inmediata de la línea JSON final (`_extraer_json_final()`): si el proceso no sale por sí solo tras `GRACIA_CIERRE_JSON_S` (`10` s), termina el árbol de procesos (`_terminar_arbol_proceso()` con `taskkill /F /T /PID` en Windows) y conserva la respuesta y métricas con `cierre_forzado: True`.
  - Añadido soporte de `timeout` en `lanzar()`, `ejecutar()` y `agente()` (por defecto `TIMEOUT_AGENTE_S = 1800` s en `agente()`, configurable mediante `timeout_s` en `orchestration.json` o `ORQUESTAR_TIMEOUT_AGENTE_S` / `ORQUESTAR_TIMEOUT_S`), devolviendo `codigo = 124` y `timeout: True` sin bloquear en descriptores abiertos ni relanzar en falso sesiones reanudadas.
  - Ajustado `agente()` para pasar `entrada=None` cuando `harness == 'agy'` (`stdin=subprocess.DEVNULL`).
- En `tests/test_orquestar.py`:
  - Añadida la clase `SubprocesoColgadoTests` con pruebas de regresión sobre subprocesos reales colgados tras emitir el JSON final, colgados antes del JSON final y paso de `entrada=None` y `timeout_s` en `agente()`.

## 📋 Evidencias
- Incidencia real en ronda 2 de A10 de `ciclo-requisitos`: `agy.EXE` (PID 25844) escribió los 10 informes `APROBADO` a las 21:11:53 y quedó colgado a las 21:12:42 hasta ser terminado manualmente a las 07:58:57.

## Triaje de alcance

- Subfase A: Definición — `[SKIP]`; el contrato es operativo y queda cubierto por pruebas deterministas de subproceso.
- Subfase B: Diseño — `[EXEC]`; cambia el ciclo de vida de procesos compartido.
- Subfase C1: Pruebas — `[EXEC]`; regresiones para JSON final, timeout y entrada de `agy`.
- Subfase C2: Corrección — `[EXEC]`; lectura no bloqueante, terminación acotada y timeout propagado.
- Subfase D: QA — `[PENDIENTE]`; revisión del delta completo al finalizar ambas correcciones del hotfix.
- Subfase E: Documentación — `[EXEC]`; changelog de la versión parche.
- Subfase F: Cierre — `[PENDIENTE]`; tras calidad y revisión.
- Verificación al cierre: `python -m unittest tests.test_orquestar.SubprocesoColgadoTests`, porque ejercita procesos reales que se cuelgan y la propagación de timeout.
