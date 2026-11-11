---
id: B-ADV-0040
title: "El acceso denegado de Claude interrumpe la revisión de Hades antes de probar sus reservas"
type: bug
weight: 15
dificultad: media
version: "v1.1.2"
status: planned
depende_de: []
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Q-ADV-0001 (B-ADV-0032) y Q-ADV-0002 (B-ADV-0033), motor instalado 1.1.1"
---

# B-ADV-0040 · Acceso denegado de Claude durante una revisión de Hades

## Fallo observado

**Reapertura durante la v1.1.2.** En B-ADV-0036, el registro de Hades del 11/11/2026 a las 13:06:04 conserva el código 1, `api_error_status: 403`, `api_error_code: oauth_not_allowed_for_organization` y el mensaje real `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`. El detector de `09e1dd6` exige un punto tras `Code` y termina sin probar la reserva. Reproducir esta variante con un doble del arnés y verificar que alcanza la reserva elegible, respeta el perfil estricto y sigue distinguiendo otros fallos de autenticación. La restauración de WIP ya se comprobó en B-ADV-0032 y B-ADV-0033. El ajuste provisional del motor de esta ejecución solo cubre esta variante hasta que la corrección quede revisada en el repositorio.

Al subir B-ADV-0032 y B-ADV-0033 a dificultad difícil, Hades pasó de revisar con Codex a usar Claude como principal, con agy y Codex de reserva. Claude terminó con código 1 y el mensaje `Your organization has disabled Claude subscription access for Claude Code.` La función `agente()` de la versión instalada 1.1.1 devolvió el error sin llegar a las reservas. Hades no emitió dictamen en esos intentos. El paso de desarrollo pidió al usuario elegir un perfil ya configurado o restaurar la suscripción y dejó ambas tareas bloqueadas. Codex emitió después dictámenes para B-ADV-0034.

## Reproducción sin cuentas ni llamadas a modelos

1. Invocar la ruta de `--agente hades` con el perfil difícil, reservas en orden agy y Codex, y ejecutables simulados disponibles. Preparar el error literal anterior para Claude y un dictamen válido para la primera reserva elegible.
2. Observar los lanzamientos y el resultado devuelto al paso. En 1.1.1 solo se invoca Claude y se devuelve 1. Repetir con agy en cuota y Codex disponible para cubrir la selección de la segunda reserva.
3. Alimentar el paso de desarrollo con ese resultado y comprobar el dictamen de la revisión, el estado de la tarea y las preguntas registradas.

## Criterios de aceptación

- Un error de suscripción deshabilitada permite continuar la misma revisión con la siguiente reserva autorizada y elegible. Se respetan el orden, las cuotas vigentes y los perfiles explícitamente estrictos. El registro identifica el fallo de acceso y el arnés que finalmente revisa.
- Con una reserva operativa, el dictamen real llega a la tarea con su destino. No se abre una pregunta para elegir esa reserva, habilitar Claude o cambiar la configuración. Un rechazo auténtico de Hades conserva su tratamiento habitual.
- Si todos los perfiles permitidos están indisponibles, se conserva la revisión pendiente y el trabajo realizado. El diagnóstico identifica el impedimento técnico y permite reintentar al recuperar un perfil. Repetir el mismo fallo no duplica preguntas ni acredita progreso de revisión.
- Verificar la recuperación con una copia del estado de Q-ADV-0001 y Q-ADV-0002: al disponer de una reserva, ambas tareas pueden retomar su revisión pendiente conservando su WIP, el historial y la respuesta ya recibida. La recuperación respeta el trabajo local ajeno y no exige contestar otra vez. Las regresiones usan lanzadores simulados.

## Evidencia y relación con otros bugs

- En `orquestar_metricas.jsonl` del 11 de noviembre se registran la promoción y el fallo de Claude para B-ADV-0032 a las 09:20:49 y 09:22:17, y para B-ADV-0033 la promoción a las 09:28:25 y los fallos a las 09:29:29 y 09:30:24. Las dos preguntas constan en `orquestar_preguntas.json`.
- B-ADV-0039 cubre la cuota que se propaga al bucle **después** de que una reserva complete el trabajo. Aquí se interrumpe la revisión **antes** de intentar una reserva operativa. B-ADV-0033 cubre la interpretación del destino cuando Hades sí ha emitido un hallazgo.

## Triaje

- `base_calidad: f751e6bdc7214b14509b64afcc53d8b3b1724ddd`.
- Causa: `agente()` retorna tras errores distintos de cuota, incluso con reservas elegibles. El acceso por suscripción deshabilitado es un caso identificable y recuperable mediante el perfil ya autorizado.
- Subfase A: [EXEC] escenarios de acceso denegado y recuperación en `skills/orquestar/features/orquestacion.feature`.
- Subfase B: [EXEC] clasificación acotada del fallo, métricas y preservación de revisión pendiente.
- Subfase C1: [EXEC] regresiones con lanzadores simulados, cuotas, perfil estricto y recuperación Git de dos preguntas respondidas con WIP y cambios ajenos.
- Subfase C2: [EXEC] conmutación en `agente()` y mandato del paso ante indisponibilidad técnica.
- Subfase D: [EXEC] Hades sobre todo el delta de este bug.
- Subfase E: [EXEC] contrato operativo de orquestar y changelog.
- Subfase F: [EXEC] cierre y commit.
- Verificación al cierre: `python -m unittest discover -s skills/orquestar -p test_acceso_agente.py` y regresiones `test_arnes_ausente.py`, `test_cuota_vigente.py`, `test_perfil_fijado.py` del mismo directorio; ejercitan clasificación, reservas y recuperación sin cuentas ni modelos. Estático: `git diff --check`, compilación de los Python del delta y calidad del delta con el coordinador. No hay linter/tipador configurado ni cambios de dependencias.
- DEC: conservar la rama hotfix activa y la versión 1.1.2; no cambiar perfiles, preguntas reales ni tareas B-ADV-0032/0033 durante la reproducción aislada.

## Intento interrumpido por enrutado de Hades

- `/review-spec`: RECHAZADO, RS-0040-01/02/03/04 para especificador, destino resolver; informe en `docs/review/spec_reviews/B-ADV-0040-spec-review.md`.
- Diseño y pruebas son borradores, sin aprobación de `/review-test` ni corrección de producción aplicada. Se conservaron mientras Hades revisaba la especificación.
- Rojo capturado mediante `adevv orquestar --verificar 'python -m unittest discover -s skills/orquestar -p test_acceso_agente.py'`: 7 pruebas, 4 fallos y 2 errores. Los fallos de reservas y reintento reproducen el bug. El error de espera refleja ausencia de la recuperación; la fixture Git de restauración también requiere corregirse antes de revisar pruebas (no se acredita como rojo válido del producto). No se ejecutó suite completa.
- Próximo paso: especificar los cuatro hallazgos y volver al ciclo; revisar desde cero conforme al modo orquestado.

## Hallazgo de Hades enrutado
- Destino: `especificador`
- Decisión: ejecutar especificar
- Evidencia: Hades /review-spec RECHAZADO (media 7,5): RS-0040-01 exige escenario propio con perfil estricto y reserva disponible; RS-0040-02 concretar rechazo real y tratamiento de su destino; RS-0040-03 registrar arnés revisor final; RS-0040-04 declarar Codex autorizado/elegible y omisión de agy agotado. Todos para especificador, destino resolver. Decisión: ejecutar especificar; conservar escenarios, diseño y pruebas en borrador, sin implementación ni cierre, y repetir revisiones desde cero. Informe docs/review/spec_reviews/B-ADV-0040-spec-review.md.

## Resolución del especificador · 2026-11-11

- DEC-ESP-0040-01: recuperar únicamente el contrato BDD del intento `b7b42e1` y resolver RS-0040-01/02/03/04 en `skills/orquestar/features/orquestacion.feature`. Se descarta restaurar diseño o pruebas en este paso: siguen en `wip/B-ADV-0040` como borradores que Artemisa debe revisar desde cero. El código actual retorna tras el error de acceso sin intentar reservas; el hueco sigue vigente.
- RS-0040-01: escenario propio con perfil fijado de Hades explícitamente estricto y reserva operativa; solo Claude se lanza y la revisión queda pendiente con diagnóstico.
- RS-0040-02: rechazo auténtico de agy, hallazgo alto para especificador y destino resolver; se exige `blocked`, `pendiente_de: especificador` y registro del hallazgo, sin pregunta humana ni confusión con fallo técnico.
- RS-0040-03/04: las dos filas exigen registro del arnés revisor final, Codex autorizado/disponible/sin cuota y secuencia exacta de lanzamientos; agy agotado se omite sin ejecución.
- DEC-ESP-0040-02: el paso documental verifica solo `git diff --check` mediante `adevv orquestar --verificar`. Las pruebas funcionales del triaje permanecen para bug-fix: no se recuperan ni ejecutan borradores defectuosos para aprobar especificación. No hay Python nuevo que compilar. Se descarta ejecutar la suite completa o usar el rojo del WIP como evidencia del árbol actual.
- Se conserva el informe rechazado como antecedente y se solicita nueva revisión aislada del contrato; no se modifican preguntas reales, perfiles, tareas dependientes ni B-ADV-0032/0033.
- Cierre de especificar: Hades `/review-spec` APROBADO, 9/10, cuatro hallazgos resueltos sin nuevos hallazgos. Informe actualizado con antecedente íntegro. Se devuelve a `planned` sin `pendiente_de`; siguiente paso bug-fix, sin acreditar diseño, pruebas ni implementación. La copia WIP conserva el intento antiguo y no debe sustituir este contrato aprobado.

## Hallazgo de Hades enrutado
- Destino: `especificador`
- Decisión: ejecutar especificar
- Evidencia: Hades review-spec RECHAZADO sobre adjunto incompleto: RS-0040-01/02/05/06 altos para especificador, destino resolver. Artemisa omitió por error cuatro escenarios al extraer el mandato; Hades no pudo leer disco. Los escenarios sí existen en el contrato aprobado: reenviar los cinco bloques completos sin duplicarlos ni alterar requisitos. Borradores y diagnóstico rojo conservados en wip/B-ADV-0040 (0e24407); anterior WIP preservado en wip/B-ADV-0040-anterior-20261111. Sin implementación ni cierre; sin pregunta humana.

## Resolución del especificador · Evidencia completa · 2026-11-11

- DEC-ESP-0040-03: conservar sin cambios los cinco bloques BDD aprobados en `d0f9471`. El diff de `skills/orquestar/features/orquestacion.feature` contra ese commit está vacío. El último rechazo se refiere a un adjunto truncado, no a escenarios ausentes del repositorio; se descarta duplicar o reformular el contrato para corregir un fallo de extracción.
- Se entrega a Hades el esquema con sus dos filas y los cuatro escenarios completos: continuación con reservas, rechazo auténtico, perfil estricto, indisponibilidad repetida y recuperación de ambas preguntas. La extracción recorre todas las etiquetas exactas `@B-ADV-0040` y comprueba cinco bloques; no termina en la segunda etiqueta del mismo ID.
- RS-0040-01/02/05/06: la evidencia de reevaluación incluye respectivamente los escenarios ya existentes de perfil estricto, rechazo y destino, indisponibilidad total repetida y recuperación aislada de Q-ADV-0001/Q-ADV-0002 con WIP, historial, respuestas y trabajo ajeno. Se adjuntan instrucciones completas de Hades y `/review-spec` para permitir un dictamen sobre la evidencia aunque falle el acceso del arnés al disco.
- DEC-ESP-0040-04: mantener el alcance documental y la verificación `git diff --check` mediante el coordinador conforme a DEC-ESP-0040-02. Las regresiones funcionales del triaje corresponden al siguiente bug-fix; no se restauran los borradores del WIP `0e24407`, no se acredita su rojo como evidencia del árbol actual y no se ejecuta la suite completa. El hueco de producción sigue vigente: `agente()` continúa solo por cuota y retorna en otros errores.

- Cierre de esta reevaluación: Hades `/review-spec` APROBADO, media 8,75/10, RS-0040-01/02/05/06 resueltos y sin nuevos hallazgos. Se devuelve a `planned` sin `pendiente_de` para retomar bug-fix. Informe transcrito con límite de acceso al disco y antecedentes íntegros; sin acreditar diseño, pruebas o implementación.

## Hallazgo de Hades enrutado
- Destino: `especificador`
- Decisión: ejecutar especificar
- Evidencia: Hades review-spec RECHAZADO 7,75/10: H1 alto para especificador pide casos observables de autenticación/red; H2 alto para especificador pide fixtures y estados observables de recuperación de ambas preguntas. Decisión: ejecutar especificar conforme al destino explícito. Advertencia de alcance: Artemisa reenvió por error el contrato ya aprobado sin modificaciones ni el informe anterior; resolver este contexto sin duplicar requisitos. Informe docs/review/spec_reviews/B-ADV-0040-spec-review.md conserva antecedentes. Borradores sin implementación ni review-test en wip/B-ADV-0040 db71195; WIP previo preservado en wip/B-ADV-0040-previo-0949. Último rojo dirigido: 8 pruebas, 7 fallos sin errores; restauración Git LF falla en Windows. Sin pregunta humana ni suite completa.

## Resolución del especificador · H1/H2 · 2026-11-11

- H1: se añade un esquema de regresión con entradas literales `authentication failed` y `network connection failed`, sin sesión previa, y resultados observables: código 1, diagnóstico conservado, solo Claude, revisión pendiente y sin cuota ni ausencia ficticias. Precisa el límite ya declarado; no amplía la conmutación a errores genéricos. El contrato anterior de autenticación en la misma feature permanece intacto.
- H2: se añade un esquema complementario con dos instantáneas sintéticas identificadas por pregunta/tarea, respuesta literal, revisión review-test pendiente, historial RT-PREVIO, WIP W0 y cambio ajeno A0. Q-ADV-0001 parte con recepción en cola; Q-ADV-0002 ya incorporada. Se fija la espera ante árbol ajeno sucio, el reintento tras guardarlo, la incorporación idempotente, restauración exacta, dictamen APROBADO de Codex sin hallazgos y continuación de bug-fix sin cerrar las tareas.
- DEC-ESP-0040-05: añadir precisión mediante escenarios complementarios sin eliminar ni alterar los cinco bloques aprobados. Los casos genéricos son regresión del límite preexistente; el delta funcional que debe discriminar sigue siendo conmutación por suscripción deshabilitada y recuperación con WIP. Se descarta extender las reservas a cualquier fallo de autenticación o red.
- DEC-ESP-0040-06: las instantáneas de recuperación son datos sintéticos reproducibles, no una afirmación de que Q-ADV-0001 haya recibido respuesta real. No se edita el registro real, los perfiles, las tareas B-ADV-0032/0033 ni sus WIP. El trabajo ajeno se conserva y se espera a que su propietario lo guarde; no se autoriza al motor a confirmarlo automáticamente.
- DEC-ESP-0040-07: se conserva el alcance documental y `git diff --check` mediante `--verificar`, conforme al triaje y DEC-ESP-0040-02/04. No hay código ni tests nuevos; el siguiente bug-fix debe ejecutar las regresiones dirigidas del triaje y corregir la fixture Git en Windows. No se restaura el borrador `db71195` ni se usa su rojo como evidencia del árbol actual.
- La reevaluación de Hades recibe el informe anterior íntegro, el diff nuevo y el contexto BDD completo; revisará H1/H2 y los dos bloques añadidos, sin reabrir los cinco bloques aprobados.

- Cierre de especificar H1/H2: Hades `/review-spec` APROBADO, media 9/10, ambos hallazgos resueltos sin nuevos hallazgos. Dictamen sobre adjuntos exactos por fallo de acceso a disco, transcrito con antecedentes íntegros. Se devuelve a planned sin pendiente_de para continuar bug-fix; no acredita diseño, pruebas, implementación ni cierre funcional.

## Reanudación de bug-fix · 2026-11-11

- Se conserva base_calidad y el contrato aprobado (siete bloques BDD); no se reabre review-spec sin delta. Diseño y pruebas recuperados del WIP como borradores para revisar desde cero. Se amplía C2 al transporte binario del parche Git que discrimina la regresión LF en Windows.

- Review-test desde cero: primer dictamen RECHAZADO (8/10), RT-01/02 para desarrollador. Corregidos consumo del dictamen observable y preservación exacta de HEAD/índice/diff/stash; reevaluación APROBADO (9/10). Se añadió propagación restaurar=False al bucle. Al superar el rojo se corrigieron dos fixtures ocultas: parser normalizado para perfil estricto y mock Popen limitado a Codex, delegando Git al proceso real. Se solicita reevaluación limitada de esas dos correcciones.
- Rojo válido previo a producción: 10 pruebas, 13 fallos contando subTests, sin errores. Verde tras corrección: 10 pruebas de acceso/recuperación, 9 de arnés ausente, 8 de cuotas vigentes y 27 de perfil fijado, mediante el coordinador. No se han ejecutado pruebas fuera del triaje ni la suite completa.
- Implementación: clasificador literal exclusivo de Claude antes del reintento de sesión, reservas ya filtradas por cuota/estricto, métricas sin veredicto técnico ni cuota inventada; mandato conserva revisión pendiente sin nuevas preguntas. Restauración exige destino limpio y transporta parche binario íntegro. No se modificaron perfiles, preguntas ni WIP reales de las otras tareas.

- QA: Hades `/review-code` RECHAZADO (8,5/10), RC-01 alto para desarrollador: asegurar_destino toleraba un índice ajeno AJENO cancelado por worktree=HEAD. Se añade regresión al mismo comando del triaje: rojo de 11 tests con un fallo por restauración indebida. Hades `/review-test` aprueba el delta de prueba con 9/10 sin nuevos hallazgos. Corrección: barrera estricta de `git status --porcelain` antes del helper en restauración de respuestas incorporadas; no cambia la recuperación de escrituras preparadas de incorporar. Reevaluación de código pendiente.

- Cierre: Hades review-code APROBADO 9/10, RC-01 resuelto sin nuevos hallazgos; review-test APROBADO 9/10 conserva RT-01/02 resueltos. Informes transcritos con límite de acceso a disco. Verificación dirigida final: 55 pruebas, compilación y diff-check; calidad omite formato/lint por ausencia de herramientas. Sin deuda ni intervenciones nuevas; validación funcional y decisiones trasladadas a v1.1.2-revision.md.
