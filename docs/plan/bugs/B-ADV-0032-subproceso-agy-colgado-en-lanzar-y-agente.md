---
id: B-ADV-0032
title: "Subproceso de agy colgado tras emitir salida o escribir artefactos bloquea indefinidamente lanzar() y --agente"
type: bug
weight: 20
dificultad: media
version: "v1.1.2"
status: completed
created_at: 2026-11-08
updated_at: 2026-11-11
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
- Subfase D: QA — `[EXEC]`; revisión del delta completo de B-ADV-0032 y resolución de H-01/H-02.
- Subfase E: Documentación — `[EXEC]`; changelog de la versión parche.
- Subfase F: Cierre — `[EXEC]`; tras calidad y revisión.
- Verificación al cierre: `python -m unittest tests.test_orquestar.SubprocesoColgadoTests`, porque ejercita procesos reales que se cuelgan y la propagación de timeout.

- base_calidad: 9a143486c663f2afe2bbe4e7ef3a30743c65532a (padre del commit de corrección 314f3d8; recuperada para la revisión formal pendiente).

### Reanudación 2026-11-11

- Se conserva la rama activa `hotfix/v1.1.2`, destinada al saneamiento de revisiones pendientes; no se cambia de rama ni se amplía el alcance a otros bugs.
- H-01: aislar ambos Popen de lanzar en una sesión POSIX propia y terminar su grupo con SIGKILL; conservar taskkill /T en Windows y la espera acotada.
- H-02: valores no finitos se tratan como configuración inválida y recuperan el valor por defecto; cero y negativos finitos mantienen la desactivación explícita existente.
- C1 amplía exclusivamente SubprocesoColgadoTests: grupo POSIX, descendiente real con pipes heredados (timeout y gracia JSON), configuración no finita en perfil y entorno.
- RED: 6 tests, 4 fallos de aserción esperados, 1 omitido por requerir POSIX. Host Windows sin WSL instalado; la regresión real POSIX queda conservada con skip explícito, nunca se declara ejecutada.
- Chequeos adicionales del delta mediante --verificar: compilación de los dos Python afectados y git diff --check; calidad por --calidad con la base conservada. Sin herramientas de lint/tipado configuradas ni cambios de dependencias.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades RECHAZADO en docs/review/code_reviews/B-ADV-0032-code-review.md. H-01 ALTA para desarrollador: POSIX mata solo al padre, debe aislar y terminar el grupo y verificar descendiente real dentro de SubprocesoColgadoTests. H-02 MEDIA para desarrollador, resolver: rechazar inf/nan y conservar timeout seguro. Decisión: Artemisa reanuda desarrollo; no se requiere recurso ni decisión humana.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades review-code RECHAZADO. H-01 persiste ALTA: padre JSON sale pero descendiente conserva pipes; vigilar streams y terminar grupo. H-03 MEDIA resolver: distinguir timeout ausente y desactivado al propagar perfil y entorno. H-04 ALTA: temporizador de captura por lineas se cancela antes de esperar proceso tras EOF. Todos para desarrollador/artemisa. Decision: reanudar desarrollo y ampliar solo SubprocesoColgadoTests; sin pregunta humana. H-02 resuelto; evidencia POSIX pendiente registrada en B-ADV-0038.

### Reanudación H-01/H-03/H-04

- Se conserva base_calidad y la rama hotfix activa. A/B/C1/C2/D/E/F mantienen el alcance del triaje previo.
- C1 añade supervisión tras salida del padre, EOF anterior a salida y precedencia de timeout desactivado; solo SubprocesoColgadoTests.
- RED de reanudación: 10 tests, 4 fallos esperados (propagación None, EOF/wait, padre salido, entorno), 1 skip POSIX; 5,901 s. Ejecutado mediante --verificar antes de corregir producción.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades review-test RECHAZADO 8,25. RT-01 ALTA para desarrollador: verificar start_new_session en Popen de captura por lineas. RT-02 MEDIA resolver: ampliar timeout de 0,2s de prueba real para tolerar arranque. RED: 10 tests, 4 fallos esperados y 1 skip POSIX; produccion sin corregir. El motor ordena parar por dos rechazos consecutivos. Decision: reanudar Artemisa con perfil superior; sin pregunta humana.


## Intervención humana Q-ADV-0001
¿Qué perfil operativo debe usar Hades: restaurar el acceso a Claude Code o seleccionar una de las reservas ya configuradas?
C1 pendiente de review-test. La invocacion obligatoria adevv orquestar --agente hades --prompt-file fallo con codigo 1: Your organization has disabled Claude subscription access for Claude Code. No hubo veredicto nuevo y el lanzador no conmuta reservas ante este error. Se conservan RT-01 (prueba portable de sesion POSIX) y RT-02 (timeout real 2 s). RED: 11 tests, 4 fallos esperados, 1 skip POSIX. Compilacion y diff --check verdes; formato/lint omitidos por ausencia de herramientas. Produccion sin modificar; H-01/H-03/H-04 siguen pendientes. Se requiere recurso de acceso o decision de configuracion, no permiso de publicacion.
Responder: /responder Q-ADV-0001 <respuesta>


## Intervención humana Q-ADV-0001
Q-ADV-0001: Decisión humana de local:Iván Moreno: Continuar con las reservas de Hades ya configuradas, en su orden, usando el motor corregido de B-ADV-0040. Para las pruebas de la conmutación usar dobles locales. Sigue pendiente el dictamen real de review-test.

### Reanudación Q-ADV-0001: review-test pendiente por impedimento técnico

- Se conserva el delta de pruebas de RT-01/RT-02: sesión POSIX propia del camino por líneas y margen de arranque de 2 s en el proceso real. Producción sin modificar; H-01/H-03/H-04 pendientes de corrección después de review-test.
- RED actual mediante `adevv orquestar --verificar "python -m unittest tests.test_orquestar.SubprocesoColgadoTests"`: 11 pruebas en 7,864 s, cuatro fallos de aserción esperados y un skip POSIX explícito. No es evidencia GREEN ni validación POSIX real.
- Se invocó `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt` con ORQUESTAR_ID=B-ADV-0032, sin cambiar perfiles ni elegir reservas manualmente. El motor ejecutó codex/gpt-6.1-sol; su retorno 0 es operacional y no constituye aprobación.
- Hades informó: «Revisión pendiente por impedimento técnico: tanto la ejecución local como el acceso alternativo a archivos fallaron con “registered Core launch requires an installed app”. No pude leer Hades, la skill, el delta ni el reporte previo, ni escribir el dictamen. No ejecuté pruebas ni modifiqué archivos. La evidencia RED aportada queda sin evaluación; no emito un veredicto sin revisar las pruebas».
- Se conserva el informe anterior y la revisión pendiente. Paso terminado sin completar el bug ni cambiar su estado, sin preguntas nuevas. Al disponer de acceso técnico, retomar C1 con el dictamen real de Hades antes de corregir producción.

### Reanudación con dictamen de pruebas

- Hades review-test APROBADO 8,75/10 sobre materiales exactos adjuntos tras fallo de acceso del arnés al disco; informe transcrito literalmente con espacios finales normalizados y antecedentes conservados. RT-01/RT-02 resueltos.
- RED del árbol inicial: 11 pruebas, cuatro fallos esperados, un skip POSIX; 8,138 s. Compilación reutilizada del mismo árbol y diff-check verdes mediante --verificar. Se retoma C2 para H-01/H-03/H-04, manteniendo base_calidad y triaje.
- GREEN tras corrección: 11 pruebas en 3,209 s, un skip POSIX explícito. Captura JSON supervisa streams tras salir el padre, sentinel conserva None explícito y captura por líneas mantiene el temporizador durante wait. Validación POSIX real pendiente en B-ADV-0038.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades review-code RECHAZADO 7,50/10. H-01/H-03/H-04 resueltos y H-02 cerrado. H-05 ALTA para desarrollador/Artemisa: en Windows taskkill sobre PID del padre ya salido no termina descendiente con pipes heredados; conservar capacidad de terminacion desde el lanzamiento que sobreviva al padre y proteger ese caso sin proveedores externos. Decision: reanudar desarrollo con diseno y pruebas dirigidas dentro de SubprocesoColgadoTests, sin decision ni recurso humano. Review-test actual APROBADO 8,75/10; 11 pruebas GREEN con 1 skip POSIX no cubren H-05. Conservar informes y delta, no completar el bug.

### Reanudación H-05

- Diseño y pruebas se amplían solo a la terminación Windows tras salir el padre. Se mantienen base_calidad y el comando de SubprocesoColgadoTests.
- C1 añade proceso local con padre terminado e hijo real con pipes heredados en JSON/gracia, JSON/timeout y líneas/timeout, aislando la llamada en un worker con watchdog de 12 s y limpieza por PID. No usa proveedores.

- RED H-05: 12 tests, tres fallos de aserción del watchdog, un skip POSIX; 41,394 s. Review-test real APROBADO 8,75/10 sobre adjuntos exactos, transcrito desde la sesión de Hades conservando los antecedentes y normalizando espacios finales. Sin hallazgos nuevos.

- GREEN H-05: 12 tests en 11,151 s, un skip POSIX. Los tres subcasos Windows completan y comprueban la desaparición real del hijo antes de limpiar. Creación suspendida, Job Object con KILL_ON_JOB_CLOSE y reanudación con APIs Win32 documentadas; sin nuevas dependencias.

- QA H-05: review-code real APROBADO 8,67/10. H-05 resuelto, H-01/02/03/04 cerrados, sin hallazgos nuevos. Informe transcrito desde la sesión de Hades por fallo de escritura del arnés, normalizando espacios finales y conservando íntegros los informes anteriores. Triaje completo satisfecho, sin preguntas nuevas ni cambios de perfiles. Validación POSIX real sigue B-ADV-0038.
