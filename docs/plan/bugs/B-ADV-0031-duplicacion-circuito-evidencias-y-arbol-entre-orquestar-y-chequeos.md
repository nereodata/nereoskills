---
id: B-ADV-0031
title: "Duplicación del circuito de lectura/escritura de evidencias y huella de árbol entre orquestar.py y chequeos.py"
type: bug
weight: 70
dificultad: media
version: "v1.2.0"
status: in_progress
depende_de: []
origen: "T-ADV-0032; revisar-version v1.1 (docs/review/versions/v1.1-arquitectura.md), H-01 🟡"
created_at: 2026-11-07
updated_at: 2026-11-11
---

# B-ADV-0031: Duplicación del circuito de lectura/escritura de evidencias y huella de árbol entre orquestar.py y chequeos.py

## 🎯 Descripción del Fallo

**Causa raíz:**
- `T-ADV-0032` introdujo en `skills/orquestar/chequeos.py` funciones centralizadas (`arbol_trabajo`, `comandos_verificados_arbol`, `ultimo_resultado_arbol_comando` y `_escribir_evidencia`, que sincroniza además con `<git-common-dir>/adevv-chequeos/orquestar_evidencias.jsonl`).
- Sin embargo, `skills/orquestar/orquestar.py` mantiene en `verificar()`, `arbol()` y `construir_prompt_agente()` su propia implementación paralela de cálculo de huella del árbol y su propia lectura/escritura directa sobre `root / EVIDENCIAS`.

**Comportamiento observado:** existen dos circuitos paralelos para calcular la huella `arbol` del repositorio y leer/escribir `orquestar_evidencias.jsonl`. Si una tarea futura amplía el contrato de evidencias o ejecuta `adevv orquestar --verificar` directamente dentro de un worktree secundario esperando compartir la evidencia con `<git-common-dir>/adevv-chequeos`, ambos almacenes pueden desincronizarse o requerir cambios duplicados.

**Comportamiento esperado:** `orquestar.py` delega `arbol()`, `verificar()` y la consulta de comandos verificados de `construir_prompt_agente()` en las funciones centralizadas de `skills/orquestar/chequeos.py`.

## 📋 Reproducir
1. Comparar `arbol()`, `verificar()` y `construir_prompt_agente()` en `skills/orquestar/orquestar.py` (líneas 495–515, 2242–2251 y 2270–2296) con `arbol_trabajo()`, `_escribir_evidencia()` y `comandos_verificados_arbol()` en `skills/orquestar/chequeos.py` (líneas 178–196, 618–633 y 1276–1294).

## 📋 Evidencias
- `docs/review/versions/v1.1-arquitectura.md`, hallazgo H-01.

## Criterios de aceptación de v1.2.0

- [ ] El comando `--verificar`, la evidencia suministrada a Hades y el preflight consultan el mismo historial aplicable, también desde un worktree secundario.
- [ ] Los tres identifican el último resultado real de la comprobación. Un fallo posterior impide reutilizar el verde anterior y se explica por qué procede ejecutar, esperar o reutilizar.
- [ ] La identidad respeta las entradas y el entorno acreditables de la etapa. Si faltan datos en registros históricos, se conserva su trazabilidad y se vuelve a ejecutar cuando corresponda.

## Triaje · 2026-11-11

- base_calidad: `32d567cb8e1ad1c881a460b09e6742f3b3f2c6cc` (conservar en reintentos).
- Causa confirmada: cálculo Git y acceso JSONL duplicados en el motor; el lector central prioriza el archivo local sobre el común y los consumidores por árbol no acreditan entorno ni cambios en vuelo. El preflight solo persiste éxitos.
- Subfase A: [EXEC] Casos de historial compartido, último resultado real y entorno/históricos en `tests/features/publicacion.feature`.
- Subfase B: [EXEC] Centralizar identidad, persistencia y consulta aplicable sin cambiar arquitectura.
- Subfase C1: [EXEC] Regresiones focalizadas en `tests/test_evidencias_compartidas.py`; conservar pruebas de prompts, verificación y publicación existentes.
- Subfase C2: [EXEC] `skills/orquestar/orquestar.py` y `skills/orquestar/chequeos.py`.
- Subfase D: [EXEC] Hades sobre el delta completo del bug.
- Subfase E: [EXEC] Nota de corrección en changelog y revisión de versión; ajustar guía de evidencias si procede.
- Subfase F: [EXEC] Calidad, señal final y commit semántico tras aprobación.
- Verificación al cierre: `python -m unittest discover -s tests -p test_evidencias_compartidas.py` y `python -m unittest discover -s tests -p test_publicacion_compartida.py`, más los tests de prompt y verificación de `tests.test_orquestar` identificados en el diseño. Ejercitan historial, worktrees, integración CLI/Hades/preflight y publicación sin ejecutar la suite completa.
- Chequeos: `git diff --check` y `python -m compileall -q skills/orquestar tests/test_evidencias_compartidas.py`; calidad del delta mediante `--calidad --base`.
- DEC: no urgente; release activa v1.2, sin publicación. No se modifica ningún perfil de agente.

## Reanudación pendiente · revisión de especificación

- Invocación realizada: `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, con `ORQUESTAR_ID=B-ADV-0031` y `ORQUESTAR_PASO=bug-fix`.
- El arnés terminó sin poder leer archivos ni ejecutar comandos: `registered Core launch requires an installed app`.
- Hades no emitió veredicto ni escribió informe. La revisión de especificación queda pendiente; no se considera aprobada ni rechazada.
- Se conservan el triaje y los escenarios propuestos. No hay implementación ni pruebas nuevas todavía; su discriminación contra el código actual queda pendiente de la fase C1. No se ejecuta la suite completa.
- Próximo intento: obtener la revisión independiente de los escenarios antes de continuar con diseño, pruebas y corrección. Las reservas y perfiles siguen bajo control de `--agente`, sin cambios manuales ni pregunta humana.
- El bug permanece `in_progress`, sin señal de completado.
- Chequeos del intento: `adevv orquestar --verificar "git diff --check"` verde; `--calidad --base 32d567cb8e1ad1c881a460b09e6742f3b3f2c6cc --aplicar` sin errores, formato y lint omitidos por ausencia de herramientas configuradas. No acredita funcionalidad implementada.

## Reintento · 2026-11-11 16:38 (Europe/Madrid)

- Se repitió `/review-spec` mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, sobre todos los escenarios del bug y con su ID maestro. Invocación registrada: `e79f4d7b6aeb432d9417cf23254a066f`.
- El lanzador seleccionó Codex conforme a los perfiles autorizados. Hades volvió a informar que no pudo acceder a archivos: tanto ejecución de comandos como Node fallaron con `registered Core launch requires an installed app`.
- Aunque el proceso devolvió código cero, no existe dictamen ni informe canónico: no acredita revisión aprobada. Se conserva `/review-spec` pendiente y el estado `in_progress`.
- Sin hallazgos asignados que enrutar, preguntas humanas, implementación ni nuevas pruebas. La siguiente acción sigue siendo obtener la revisión independiente antes de diseño y fase roja.
