---
id: B-ADV-0045
title: "El ejecutor de Codex no inicia las herramientas de lectura y escritura de Hades"
type: bug
weight: 0
dificultad: dificil
version: "v1.1.3"
status: completed
depende_de: []
perfil: {artemisa: {harness: codex, model: gpt-6-astra, effort: high}, hades: {harness: codex, model: gpt-6-astra, effort: high}, atenea: {harness: codex, model: gpt-6-astra, effort: high}, estricto: true}
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Petición expresa del usuario; incidente B-ADV-0031 en release/v1.2 y revisiones de v1.1.2"
---

# B-ADV-0045 · Fallo de herramientas en el ejecutor de Hades

## Hechos observados

En sesiones Codex lanzadas como Hades por Adevv, la herramienta de ejecución de comandos y la alternativa Node fallan con registered Core launch requires an installed app. El revisor no logra leer sus instrucciones, la skill de revisión ni las fuentes del repositorio y tampoco puede escribir el informe canónico. Una salida del proceso con código cero puede carecer de dictamen. Aportar todo el material en el mandato permitió dictámenes independientes, pero deja sin resolver el fallo de las herramientas.

Evidencia accesible en el worktree principal C:/Users/Iván Moreno/SW/Adevv, rama release/v1.2, en la ficha y el informe de especificación de B-ADV-0031, orquestar.log y métricas. Las sesiones de Hades de v1.1.2 también documentan el mismo error. El lanzador de roles Codex usa exec o exec resume, approval_policy never y sandbox workspace-write. Estas opciones son contexto para diagnosticar, no una causa raíz confirmada.

## Alcance urgente y criterios de aceptación

- Reproducir el fallo mediante la entrada normal de Hades y recoger el comando efectivo, ejecutable resuelto, versión de CLI, directorio, entorno pertinente y error. Excluir credenciales y datos privados del registro.
- Determinar si el origen está en Adevv, la resolución de ejecutables, la configuración heredada o el runtime externo. Contrastar sesión nueva y reanudada e identificar el cambio histórico cuando sea posible. No afirmar una regresión sin evidencia.
- Corregir la causa identificada y demostrar que una sesión real de Hades puede leer el contenido exacto de un archivo del checkout y escribir su informe canónico por sus herramientas normales, con veredicto independiente sobre el alcance solicitado.
- Conservar el aislamiento y los permisos previstos del revisor. Cambiar a ejecución sin sandbox o desactivar herramientas no satisface este arreglo. Cualquier ajuste de entorno debe ser mínimo y compatible con otros proyectos, arneses y sesiones reanudadas.
- Añadir regresiones deterministas del defecto de lanzamiento o configuración y una comprobación real en este equipo. El uso de adjuntos por sí solo no acredita el arreglo del ejecutor.
- Si la causa requiere actualizar o reparar un componente externo, registrar la acción y verificar el recorrido real después. Mantener el bug abierto mientras no se pueda demostrar el arreglo.
- Verificar conjuntamente con B-ADV-0044 que un fallo operacional no produce una aprobación falsa ni una repetición ilimitada.

## Condición de publicación e instalación

El usuario exige resolver B-ADV-0044 y B-ADV-0045 en v1.1.3 antes de instalarla. Ambos deben estar completados con sus dictámenes y evidencias. Mantener la versión instalada 1.1.2 mientras quede cualquiera pendiente.

## Pistas del diagnóstico local

Get-Command codex -All resuelve primero AppData/Local/Programs/OpenAI/Codex/bin/codex.exe (CLI 0.167.0), y después el ejecutable del paquete WindowsApps. La configuración global declara windows.sandbox = elevated. El entorno del proceso padre contiene CODEX_WINDOWS_REGISTERED_CORE=1, CODEX_WINDOWS_SANDBOX_PACKAGE_FAMILY=OpenAI.Codex_2p2nqsd0c76g0 y CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop, además de CODEX_APP_RUNTIME_CLI_PATH, CODEX_APP_TOOLS_PIPE_PATH y otros metadatos del escritorio. Investigar si el hijo independiente hereda indebidamente el modo de lanzamiento de una aplicación registrada. Contrastar mediante prueba controlada conservando workspace-write y approval_policy never. Esta es una hipótesis, no autoriza a retirar el sandbox ni acredita la causa.

## Reproducción comparativa real del ejecutor

Directorio temporal de evidencia C:/Users/IVNMOR~1/AppData/Local/Temp/adevv-executor-diagnostic-2ygyuzyh. Dos invocaciones nuevas del mismo codex.exe 0.167.0, gpt-6-astra/high, exec --json --skip-git-repo-check --sandbox workspace-write -c approval_policy=never, mismo directorio y misma instrucción de copiar entrada.txt a salida.txt usando comandos. En heredado.log, la herramienta command_execution terminó con -1 y registered Core launch requires an installed app. El proceso Codex devolvió 0 pese al fallo. En sin_registered_core.log, se retiró exclusivamente CODEX_WINDOWS_REGISTERED_CORE del entorno del hijo, y command_execution devolvió 0 después de ReadAllBytes/WriteAllBytes. Se conservó el sandbox. El padre no pudo releer salida.txt por su ACL, por lo que aún queda comparar contenido mediante el ejecutor y verificar el canal real --agente hades, incluida reanudación. La diferencia controlada identifica esa variable como causa del fallo de lanzamiento en este equipo. Evitar eliminar indiscriminadamente todas las variables CODEX. Usar estas dos evidencias para el triaje, la regresión y el smoke real de Hades antes de cerrar.

La comprobación reanudada posterior también pasó: reanudada.log en el mismo directorio conserva una llamada real de comandos que compara bytes y calcula SHA256 de entrada.txt y salida.txt. Ambos hashes coinciden con el hash calculado por el padre sobre entrada.txt. Código de proceso 0, ausencia del error de registered core y sandbox workspace-write conservado. La carpeta temporal requirió --skip-git-repo-check tanto en exec como en exec resume por estar fuera de un checkout. Esta opción solo corresponde al diagnóstico temporal; el lanzamiento real de Hades debe conservar la validación del checkout. Ya hay evidencia real de lectura/escritura y reanudación del ejecutor saneado; queda demostrarlo por --agente hades tras implementar el ajuste.

## Triaje

- base_calidad: 280eaf84a76230cd961ed2dd5d80fe60f4a3abe8
- A [SKIP] El contrato de lectura y escritura dentro de workspace-write ya existe. La reproducción comparativa concreta el defecto de lanzamiento.
- B [SKIP] La diferencia controlada localiza una única variable heredada en el proceso hijo Codex de roles en Windows. Se conservan el ejecutable, el perfil y el sandbox.
- C1 [EXEC] Regresión determinista desde el lanzador de rol hasta el entorno del subproceso. Cubrir sesión nueva, reanudación y recuperación con sesión nueva, preservación del padre, entorno restante y controles de alcance.
- C2 [EXEC] Retirar únicamente CODEX_WINDOWS_REGISTERED_CORE del entorno del rol Codex independiente en Windows.
- D [EXEC] Hades revisa las pruebas y el delta. Smoke real por --agente hades en este checkout, con lectura exacta verificable y escritura del informe canónico por el revisor. Contrastar sesión nueva y reanudada.
- E [SKIP] El arreglo conserva la configuración y el modo de uso existentes.
- F [EXEC] Registrar evidencias, comprobar calidad y cerrar solo tras dictamen independiente y smoke satisfactorio.
- Verificación dirigida: `python -m unittest skills.orquestar.test_codex_resume_usage skills.orquestar.test_progreso.ProgresoTests.test_commits_de_diagnostico_bug skills.orquestar.test_progreso.ProgresoTests.test_cita_no_emite_dictamen_y_reserva_revisa`. Comprueba el lanzamiento y las dos protecciones de B-ADV-0044 (dictamen ausente y parada por repetición). Para el rojo, solo la clase de regresión del lanzador. Chequeos del delta: git diff --check y --calidad.

## Diagnóstico y rojo

En el checkout hotfix/v1.1.3, la entrada normal de Hades con Adevv 1.1.2 resolvió %LOCALAPPDATA%/Programs/OpenAI/Codex/bin/codex.exe (codex-cli 0.167.0). Comando efectivo de la sesión nueva: codex exec -m gpt-6-astra -c model_reasoning_effort="high" --json -c approval_policy="never" --sandbox workspace-write -. Con CODEX_WINDOWS_REGISTERED_CORE=1 heredada de Desktop, la lectura de task_config.yaml falló antes de crear el proceso: «Failed to create unified exec process: registered Core launch requires an installed app». La CLI devolvió 0, sin hash ni dictamen. La comparación previa con el mismo ejecutable y perfil aisló esa variable; la familia del sandbox y el resto del entorno se conservaron. El sandbox del rol está en el historial desde 59b01a0 y la reanudación desde deac2c7. No se ha identificado qué actualización externa introdujo la incompatibilidad.

Rojo C1 anterior a la corrección: seis pruebas ejecutadas, tres fallos de aserción por la presencia de la marca (nueva, reanudada y reintento nuevo); tres controles verdes (sin marca, POSIX y Claude). La cola completa está en la evidencia de --verificar del comando de la clase EntornoRolTests.

## Corrección y comprobación real

C1 obtuvo 9,25/10. Se incorporaron ambos ajustes de Hades al doble de proceso y se volvió a obtener el mismo rojo antes de C2. En Windows, el lanzador de roles copia el entorno solo para un Codex que herede la marca y la retira de la copia. La reanudación y su recuperación reutilizan ese entorno.

Sesión nueva por la CLI del checkout en un clon local de la misma rama sin historial de sesiones. Se seleccionó el código corregido con PYTHONPATH y un almacén Adevv de prueba vacío. El padre aún tenía CODEX_WINDOWS_REGISTERED_CORE=1. Con el perfil fijado, Hades leyó 48 bytes aleatorios cuyo valor no recibió en el mandato, escribió su SHA256 en la ruta canónica y releyó el informe. El padre comprobó la coincidencia con su propio cálculo: 66b8a0351891130ef8609312de8578962879ad4a913f365f00c93ec9df772e26. La sesión fue 01a1cbbd-ace6-7041-9b45-5dbcbea222b0. El diagnóstico en el clon no emitió un dictamen formal de producto. La revisión D corresponde al checkout de trabajo.

La sesión reanudada 01a1cbb8-d772-7ec0-97a1-89e0d2ef14ca revisó el delta en el árbol de trabajo con la CLI corregida y el padre marcado. Hades leyó el archivo de producción y escribió y releyó su [informe de código](../../review/code_reviews/B-ADV-0045-code-review.md). El SHA256 de los bytes de skills/orquestar/orquestar.py coincidió con el cálculo independiente del padre. Veredicto APROBADO, 10/10. Los dos hallazgos menores del [informe de pruebas](../../review/test_reviews/B-ADV-0045-test-review.md) quedaron resueltos. Las 13 pruebas dirigidas pasaron, incluidas las dos de B-ADV-0044. Formato y lint omitidos por ausencia de herramientas.
