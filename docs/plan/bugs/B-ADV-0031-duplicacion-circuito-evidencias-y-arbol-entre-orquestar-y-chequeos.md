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

## Reintento · 2026-11-11 16:40 (Europe/Madrid)

- Revisión `/review-spec` del alcance completo invocada con `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `00fb3410004340e185732865d98dabd9`, perfil efectivo Codex seleccionado por el lanzador.
- Consola y Node del revisor fallaron con `registered Core launch requires an installed app`. Hades declara que no pudo leer los archivos ni crear el informe; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y el estado `in_progress`. No hay hallazgos asignados que enrutar ni decisión humana requerida. No se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Se verifica únicamente la higiene del delta documental mediante `--verificar` y la calidad desde la base original; las pruebas funcionales del triaje siguen pendientes hasta implementar la corrección.

## Reintento · 2026-11-11 16:42 (Europe/Madrid)

- Revisión de especificación del alcance completo lanzada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, invocación `a1add8bda8bd47989d4ac08682626ae5` (Codex seleccionado por el lanzador).
- Hades informa que ejecución y Node no pueden iniciarse: `registered Core launch requires an installed app`. No existe informe canónico ni veredicto; el retorno cero del proceso no acredita aprobación.
- Se conserva la revisión independiente pendiente y `status: in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles ni se avanza a diseño, pruebas o implementación.
- La verificación de este intento se limita a higiene documental (`git diff --check`) y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes hasta implementar el arreglo.

## Reintento · 2026-11-11 16:44 (Europe/Madrid)

- `/review-spec` se lanzó para el alcance completo mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `7e8ef2e1ec2540fe828ec26a508e4b6c`, perfil efectivo Codex seleccionado por el lanzador.
- Hades declara que ejecución y acceso alternativo mediante Node fallan con `registered Core launch requires an installed app`. No escribió dictamen y se confirma que el informe canónico sigue ausente; el código cero del proceso no acredita aprobación.
- Se conserva `in_progress` y la revisión de especificación pendiente. No hay hallazgos asignados que enrutar ni decisión humana requerida. No se modifican perfiles ni se avanza a diseño, pruebas o implementación.
- El delta de este intento es documental: se comprueba con `--verificar` la higiene y la calidad desde la base original. Las pruebas funcionales del triaje permanecen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 16:46 (Europe/Madrid)

- `/review-spec` del alcance completo se invocó mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `4953eddbe7574091bd4a2f0a711446a1`, perfil efectivo Codex seleccionado por el lanzador.
- Hades informa que ejecución y acceso alternativo con Node fallan con `registered Core launch requires an installed app`. No pudo leer la especificación ni escribir el informe canónico, cuya ausencia se comprobó. El código cero del proceso no acredita aprobación.
- Se conserva la revisión independiente pendiente y `status: in_progress`. Sin dictamen ni hallazgos asignados, no procede enrutado ni pregunta humana. No se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- El delta de este intento es documental: se comprueba higiene mediante `--verificar` y calidad desde la base original. La validación funcional del triaje sigue pendiente y no se ejecuta la suite completa.

## Reintento · 2026-11-11 16:47 (Europe/Madrid)

- `/review-spec` del alcance completo invocada con `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `9697855532da49c990642ae7d7119f93`, perfil efectivo Codex seleccionado por el lanzador.
- Hades informa que comandos y Node fallan con `registered Core launch requires an installed app`. Se comprueba la ausencia del informe canónico; el retorno cero sin dictamen no acredita aprobación.
- Se conserva la revisión pendiente y `in_progress`, sin hallazgos que enrutar ni decisión humana requerida. No se cambian perfiles ni reservas y no se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental y calidad desde la base original. La validación funcional del triaje sigue pendiente; no se ejecuta la suite completa.

## Reintento · 2026-11-11 16:49 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `047f9805bae24ce79311197aa527f767`, perfil Codex seleccionado por el lanzador.
- Hades declara que comandos y Node fallan con `registered Core launch requires an installed app`. Se confirma que no existe informe canónico; el retorno cero no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. No hay hallazgos asignados que enrutar ni decisión humana requerida; no se modifican perfiles ni reservas y no se avanza a diseño, pruebas o implementación.
- Comprobación limitada a higiene documental mediante `--verificar` y calidad desde la base original. La validación funcional del triaje sigue pendiente; no se ejecuta la suite completa.

## Reintento · 2026-11-11 16:51 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `ff40a053207f4ab58300e1a500f777c4`, perfil Codex seleccionado por el lanzador.
- Hades declara que ejecución y Node fallan al iniciarse con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; el retorno cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. No hay hallazgos asignados que enrutar ni decisión humana requerida; no se modifican perfiles ni reservas y no se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar` y calidad desde la base original. La validación funcional del triaje sigue pendiente; no se ejecuta la suite completa.

## Reintento · 2026-11-11 16:52 (Europe/Madrid)

- `/review-spec` del alcance completo lanzada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `2644b68fcf174629a891b4fd4c243ef0`, perfil Codex seleccionado por el lanzador.
- Hades no pudo leer los archivos ni escribir el informe: terminal y acceso alternativo fallan con `registered Core launch requires an installed app`. Se confirma que el informe canónico no existe; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- El delta documental se comprueba mediante `--verificar "git diff --check"` y calidad desde la base original. La validación funcional del triaje sigue pendiente; no se ejecuta la suite completa.
## Reintento · 2026-11-11 16:54 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `0d03e99fc2f04bd58552703c7e1d8c67`, perfil Codex seleccionado por el lanzador.
- Hades declara que ejecución de comandos y acceso mediante Node fallan con `registered Core launch requires an installed app`. Se confirma que no existe informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`, sin hallazgos que enrutar ni decisión humana requerida. No se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Se comprueba únicamente higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 16:56 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `506277aafba3486ca84a555758e9f184`, perfil Codex seleccionado por el lanzador.
- Hades declara que ejecución y Node fallan al iniciarse con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se modifican perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- El delta documental se comprueba mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 16:57 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `c25a394d9ea947ec9c643ed9f3061317`, perfil Codex seleccionado por el lanzador.
- Hades declara que terminal y lector alternativo fallan con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; el retorno cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se modifican perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 16:59 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `18b3b5b599904695875cd559ee0a0028`, perfil Codex seleccionado por el lanzador.
- Hades declara que ejecución local y acceso alternativo con Node fallan con `registered Core launch requires an installed app`. Se comprueba que no existe informe canónico; el retorno cero del proceso no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles ni reservas y no se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:01 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `5472c54548ae4d749f54e47e4bd13bbf`, perfil Codex seleccionado por el lanzador.
- Hades declara que consola y entorno alternativo fallan con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; el retorno cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:02 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `fa80d928cdd948a193edd4ed53aafc9e`, perfil Codex seleccionado por el lanzador.
- Hades declara que comandos y Node fallan con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; el retorno cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:04 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `e42bf7cb77d24c1195f29292383f73e4`, perfil Codex seleccionado por el lanzador.
- Hades declara que ejecución de comandos y entorno Node fallan con `registered Core launch requires an installed app`. Se confirma que no existe informe canónico; el retorno cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:05 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `ebafad492e52489fbb458a872692afdf`, perfil Codex seleccionado por el lanzador.
- Hades declara que PowerShell y el lector alternativo fallan con `registered Core launch requires an installed app`. Se confirma que no existe informe canónico; el retorno cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:07 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `852af4acb538483abb1ce8976382f7f5`, perfil Codex seleccionado por el lanzador.
- Hades declara que ejecución de comandos y entorno Node fallan al iniciarse con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:09 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `247f83c67e1d4526bd43b956ddb674ea`, perfil Codex seleccionado por el lanzador.
- Hades declara que ejecución y Node fallan al iniciarse con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:11 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `df6a3d684965495b8acf4942ce7bfd76`, perfil Codex seleccionado por el lanzador.
- Hades declara que consola y entorno alternativo fallan con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:12 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `9e131b8425634aef856544a5f0293259`, perfil Codex seleccionado por el lanzador.
- Hades declara que comandos y acceso alternativo mediante Node fallan con `registered Core launch requires an installed app`. Se confirma que no existe informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:14 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `e110c009dd5f4383a1b0deb991a5f169`, perfil Codex seleccionado por el lanzador.
- Hades declara que terminal y entorno alternativo fallan con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles ni reservas y no se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:16 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `c0d4d6d5146442108cfe87881534d96f`, perfil Codex seleccionado por el lanzador.
- Hades no pudo leer las fuentes con consola ni Node (`registered Core launch requires an installed app`) y también falló al escribir el informe. Se confirma que el informe canónico no existe; código cero sin dictamen no acredita aprobación.
- El revisor indicó «humano» para restablecer el acceso técnico, sin evaluar la especificación. Se aplica la regla explícita de conservar la revisión pendiente ante indisponibilidad técnica: no se abre pregunta para restaurar el acceso ni elegir reservas. No hay hallazgos de especificación que enrutar.
- Se conserva `in_progress`, la base original y el trabajo existente. No se avanza a diseño, pruebas o implementación. Verificación limitada a higiene documental y calidad; las pruebas funcionales del triaje siguen pendientes.

## Reintento · 2026-11-11 17:17 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `28faadd95a2d4546af5aa2ef85cf570d`, perfil Codex seleccionado por el lanzador.
- Hades declara que terminal y alternativa Node fallan con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:19 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `fdfa4ac314f84e79ad9cd5406c0f1899`, perfil Codex seleccionado por el lanzador.
- Hades declara que ejecución local y acceso mediante Node fallan con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.

## Reintento · 2026-11-11 17:21 (Europe/Madrid)

- `/review-spec` del alcance completo invocada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; invocación `76733ab2c2684a40881cbaa4202cbcef`, perfil Codex seleccionado por el lanzador.
- Hades declara que ejecución de comandos y entorno Node fallan al arrancar con `registered Core launch requires an installed app`. Se confirma la ausencia del informe canónico; código cero sin dictamen no acredita aprobación.
- Se conserva la revisión independiente pendiente y `in_progress`. Sin hallazgos asignados que enrutar ni decisión humana requerida; no se cambian perfiles o reservas ni se avanza a diseño, pruebas o implementación.
- Verificación limitada a higiene documental mediante `--verificar "git diff --check"` y calidad desde la base original. Las pruebas funcionales del triaje siguen pendientes; no se ejecuta la suite completa.
