---
id: B-ADV-0045
title: "El ejecutor de Codex no inicia las herramientas de lectura y escritura de Hades"
type: bug
weight: 0
dificultad: dificil
version: "v1.1.3"
status: planned
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
