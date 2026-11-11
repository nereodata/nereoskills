---
id: B-ADV-0036
title: "El agotamiento de reintentos de la suite de cierre bloquea al humano sin diagnóstico de Hades"
type: bug
weight: 20
dificultad: dificil
version: "v1.1.2"
status: blocked
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Caso observado en Afinn release/v0.7, B-AFN-0185, con Adevv 1.1.1"
pendiente_de: humano
---

# B-ADV-0036: El agotamiento de reintentos de la suite de cierre bloquea al humano sin diagnóstico de Hades

## 🎯 Descripción del fallo

**Causa raíz:** al registrar una suite roja, `registrar_suite_roja()` usa el
contador `suite_intentos` como decisión de enrutado. Al llegar a tres intentos
en dificultad `dificil`, actualiza directamente el bug de cierre a
`status: blocked` y `pendiente_de: humano`, sin solicitar una revisión de
diagnóstico a Hades ni distinguir si el último fallo pertenece al mismo grupo
causal que los anteriores.

**Comportamiento observado:** en Afinn, `release/v0.7`, `B-AFN-0185`, después
de tres recaídas de la suite en dificultad `dificil`, el bucle se detuvo,
notificó por Telegram y dejó el bug pendiente del humano. Quedaban siete
fallos técnicos de integración, sin una decisión, permiso o recurso pendiente
del usuario. Las recaídas agrupaban fallos de causas distintas que aparecían
al ir avanzando la suite bajo un único bug de cierre.

**Comportamiento esperado:** al agotar los reintentos se pide una revisión
finita a Hades con los fallos vigentes, los arreglos intentados y la evidencia
de cada intento. Hades clasifica el impedimento y el bucle aplica su destino:

- `desarrollador`: continúa con un diagnóstico y una estrategia de corrección
  revisada.
- `especificador`: resuelve contradicciones o ambigüedades del contrato por el
  flujo de especificación.
- `humano`: bloquea solo si falta una decisión, permiso o recurso humano
  concreto; persiste la pregunta y su justificación.

Si no es posible avanzar técnicamente tras la revisión, Hades debe cerrar el
diagnóstico con los intentos y evidencias realizados e indicar la intervención
concreta requerida. No se reinicia el ciclo de forma ilimitada.

## 📋 Reproducir

1. Crear o reutilizar un bug de cierre de suite con dificultad `dificil`.
2. Registrar tres recaídas de la suite roja con evidencia de fallos técnicos de
   integración y sin una solicitud humana concreta.
3. Comprobar que, en la tercera recaída, el estado pasa directamente a
   `blocked` con `pendiente_de: humano` y se avisa por Telegram.
4. Repetir con grupos de fallos distintos que emergen secuencialmente de la
   suite y comprobar que el contador actual los trata como tres recaídas del
   mismo impedimento.

## ✅ Criterios de aceptación

1. Al alcanzar el umbral de reintentos en `dificil`, el contador por sí solo
   no asigna `pendiente_de: humano` ni emite una pregunta o aviso humano.
2. El orquestador solicita una única revisión diagnóstica finita de Hades con
   los fallos actuales, su evidencia y el historial de arreglos e intentos.
3. Un diagnóstico con destino `desarrollador` mantiene el bug elegible y
   aporta una estrategia de corrección revisada; el bucle continúa el trabajo.
4. Un diagnóstico con destino `especificador` conserva la trazabilidad y
   enruta automáticamente al flujo de especificación, sin pregunta humana.
5. Solo un diagnóstico con destino `humano` bloquea el bug con
   `pendiente_de: humano`, y exige una pregunta que identifique la decisión,
   permiso o recurso solicitado y su justificación.
6. El diagnóstico identifica y diferencia los grupos causales de fallos de
   suite. Los nuevos grupos que aparecen tras resolver otros no consumen como
   recaídas del mismo problema el presupuesto de éste.
7. Cuando Hades determine imposibilidad técnica de continuar, su salida es
   terminal, enumera intentos y evidencias y pide una intervención concreta;
   el orquestador no reabre diagnósticos indefinidamente.
8. Existen regresiones deterministas que cubren los destinos `desarrollador`,
   `especificador` y `humano`, y demuestran que llegar al contador no basta
   para bloquear al humano.

## 📋 Evidencias

- Caso comunicado: Afinn `release/v0.7`, `B-AFN-0185`, Adevv `1.1.1`.
- Tras tres recaídas en `dificil`, se observaron `status: blocked` y
  `pendiente_de: humano` sin clasificación de Hades.
- El caso conservaba siete fallos técnicos de integración y no requería
  decisión, permiso ni recurso humano.
- La implementación actual concentra la escalada directa en
  `skills/orquestar/orquestar.py`, en el registro de suite roja; las
  regresiones actuales comprueban precisamente la asignación humana al agotarse
  el contador.

## Triaje de alcance

- Subfase A: Definición — `[EXEC]`; especificar el contrato de diagnóstico
  terminal, destinos de Hades y agrupación causal de recaídas.
- Subfase B: Diseño — `[EXEC]`; definir el artefacto de diagnóstico, su
  identidad de grupo de fallo, los límites finitos y el enrutado.
- Subfase C1: Pruebas — `[EXEC]`; regresiones deterministas de los tres
  destinos, del umbral sin bloqueo humano y de grupos sucesivos de fallos.
- Subfase C2: Corrección — `[EXEC]`; sustituir la escalada directa por el
  diagnóstico de Hades y aplicar su salida de forma trazable.
- Subfase D: QA — `[PENDIENTE]`; revisión de código y del contrato de parada
  finita.
- Subfase E: Documentación — `[EXEC]`; actualizar la guía de recuperación de
  suites rojas y la semántica del contador.
- Subfase F: Cierre — `[PENDIENTE]`; tras la calidad y verificación completas.
- Verificación al cierre: pruebas de registro de suite roja y de enrutado de
  Hades en `tests/test_orquestar.py`, porque acreditan que el umbral no asigna
  el humano y que los tres destinos se procesan correctamente.

## Fuera de alcance

- No modificar Afinn, su rama `release/v0.7` ni sus requisitos como parte de
  esta corrección. El caso se conserva exclusivamente como evidencia de
  reproducción.

## Inicio del intento y conflicto de contrato

- `base_calidad`: `2213a304b6a48ec224caf32083c55152e7be4562` (conservar en los reintentos).
- Rama inicial: `hotfix/v1.1.2`; árbol limpio. Se conserva la rama de hotfix ya preparada por el bucle.
- Subfases D y F: `[EXEC]`, según el triaje existente.
- Verificación prevista: `python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests`; añadir únicamente regresiones de enrutado si el alcance final modifica ese módulo.
- Impedimento de Subfase A: `tests/features/uso_sin_rutas.feature:125` exige `blocked` y aviso humano en la tercera recaída en `dificil`, contradiciendo los criterios 1, 2 y 5 de este bug. El escenario completo empieza en la línea 115 y también exige contar salidas distintas sin clasificación causal. `tests/test_orquestar.py:1477` fija ese contrato anterior.
- `/generate-bdd` prohíbe eliminar o sustituir escenarios existentes y exige detenerse ante contratos contradictorios; `/review-spec` exige no alterar escenarios existentes. Se solicita a Hades clasificar este impedimento antes de modificar especificación o implementación. Propuesta: el especificador declare expresamente la sustitución del contrato de B-ADV-0006 por los criterios de B-ADV-0036 y determine la identidad causal y el presupuesto terminal finito; no hace falta ninguna decisión, permiso ni recurso humano.
- No se han ejecutado pruebas: no hay cambios de producción ni de tests y la fase de definición está detenida por el conflicto documentado.

## Impedimento operativo de revisión

- Se invocó `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt` para revisar el contrato completo y asignar el conflicto.
- Retorno: `1`. Salida: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- No se generó `docs/review/spec_reviews/B-ADV-0036-spec-review.md`; no existe veredicto ni destino de Hades. No se infiere un destino ni se abre una pregunta humana por este fallo del arnés.
- El paso queda incompleto en `in_progress`, con el delta documental conservado para reanudar. No se modifica código, tests ni la copia instalada; no se ejecuta la suite ni se declara completado.

## Reanudación del paso orquestado · 2026-11-11

- Releídos el mandato instalado de Artemisa, `/orquestar`, `/bug-fix`, `/generate-bdd` y `/review-spec`; se conserva `base_calidad` y el triaje del intento anterior.
- Reintentada la revisión aislada del conflicto completo mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, con mandato de clasificar el impedimento y asignar su destino sin modificar el contrato.
- Retorno `1`, antes de emitir dictamen: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- Sigue sin existir un veredicto de Hades para este bug. No se ejecuta `--enrutar-hallazgo` sin asignación ni `--preguntar` por un fallo operativo del arnés. No se cambia la configuración de los roles.
- No se ejecutan pruebas: no se han modificado código, tests ni escenarios; la definición permanece detenida por el conflicto documentado. La verificación de `SuiteRecoveryTests` mediante `--verificar` queda pendiente para cuando exista un arreglo que validar.
- Paso incompleto, bug conservado en `in_progress`; sin señal de cierre ni commit de finalización. El delta documental queda disponible para la siguiente reanudación.

## Reanudación y verificación focalizada · 2026-11-11

- Reintentada la revisión de Hades con `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, sobre el conflicto completo de definición y solicitando destino explícito.
- Retorno `1` antes del dictamen: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- No hay asignación de Hades que permita ejecutar `--enrutar-hallazgo`; tampoco existe una pregunta de producto o recurso que justifique `--preguntar`. Se conserva el impedimento operativo y `in_progress`, sin señal de cierre.
- Se verifica exclusivamente la base existente con `adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests"`. Esta evidencia no acredita el arreglo: no se han modificado implementación, pruebas ni escenarios y sigue pendiente resolver el conflicto de contrato.

## Resultado del reintento actual · 2026-11-11 10:15 CET

- Revisión requerida: `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, sobre el conflicto completo de definición, sin modificar contratos ni configuración.
- Retorno `1` antes de emitir dictamen: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- Verificación focalizada: `adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests"`, retorno `0`; 16 pruebas existentes en verde (22,412 s). Acredita la base existente, no el arreglo pendiente. Se solicita de nuevo la verificación tras actualizar esta evidencia documental para acreditar el árbol final.
- No existe reporte ni asignación de Hades: no se ejecuta `--enrutar-hallazgo` ni se registra una pregunta humana por el error operativo. Se conserva `in_progress`, la base de calidad y el delta previo. Paso incompleto, sin cambios de implementación ni señal o commit de finalización.

## Reanudación actual del paso orquestado · 2026-11-11

- Releídos Artemisa, `/orquestar`, `/bug-fix`, `/generate-bdd` y `/review-spec` de la instalación 1.1.1; se retoman el delta existente, el triaje y `base_calidad` sin descartarlos.
- Nueva invocación de revisión aislada: `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; retorno `1` antes de emitir dictamen: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- Sin reporte ni destino de Hades, no se puede resolver el conflicto de contrato por cuenta de Artemisa. No se ejecuta `--enrutar-hallazgo` sin asignación ni `--preguntar` por este fallo operativo. No se modifica la configuración de los roles.
- Se solicita sobre este delta documental la verificación focalizada del triaje mediante `adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests"`, reutilizando evidencia del mismo árbol si existe. Su resultado valida la base existente, no una corrección: todavía no hay cambios de producción, escenarios ni pruebas.
- Paso incompleto: se conserva `in_progress`, sin señal de cierre ni commit de finalización.

## Reintento de revisión aislada · 2026-11-11

- Invocación: `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, sobre el conflicto completo de definición de B-ADV-0036; retorno `1` antes del dictamen: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- No existe asignación de Hades ni reporte nuevo que permita enrutar el hallazgo. Se conserva el impedimento operativo, sin cambiar perfiles ni registrar una pregunta humana por el fallo del arnés.
- Se ejecuta únicamente la verificación del triaje con `adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests"`, reutilizando evidencia del mismo árbol cuando corresponda. El resultado duradero queda en el registro del verificador y acredita solo la base existente.
- Sin cambios de código, tests o escenarios. El paso permanece incompleto, `in_progress`, sin señal de cierre ni commit de finalización.

## Resultado de esta ejecución orquestada

- Revisión requerida relanzada con `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`, sobre el conflicto completo de definición. Retorno `1`: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- No se ha emitido dictamen ni destino. Se conserva el impedimento de definición, sin cambiar perfiles ni contratos, sin enrutar un hallazgo no asignado y sin abrir una pregunta humana por el fallo operativo.
- Verificación limitada a `adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests"`; su resultado queda en la evidencia duradera del verificador sobre este árbol. Valida la base, no el arreglo pendiente.
- Paso incompleto: `in_progress`, sin cambios de producción, escenarios o pruebas, sin señal de cierre ni commit de finalización.

## Reintento del mandato actual · 2026-11-11

- Revisión de definición completa solicitada mediante `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; retorno `1` previo a dictamen: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- Se conserva el conflicto entre el escenario de B-ADV-0006 y los criterios de B-ADV-0036. No existe reporte ni asignación de Hades; no se ejecutan `--enrutar-hallazgo` ni `--preguntar` y no se modifican perfiles, contratos, implementación ni tests.
- Verificación solicitada exclusivamente mediante `adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests"`; el resultado y la posible reutilización quedan en la evidencia duradera del verificador. Solo acredita la base existente, no un arreglo.
- Paso incompleto, conservando `in_progress`, el delta previo y `base_calidad`; sin señal de cierre ni commit de finalización.

## Reanudación de este mandato · revisión no disponible

- Revisión aislada del conflicto completo solicitada con `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`; retorno `1` antes del dictamen: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- No existe asignación nueva de Hades. Se conserva el impedimento de definición y `in_progress`, sin cambiar perfiles, contratos, implementación ni tests y sin señal de cierre. No procede enrutar sin destino ni abrir una pregunta humana por el error operativo.
- Se solicita exclusivamente `adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests"` sobre este árbol final, reutilizando evidencia si existe. El resultado duradero acredita solo la base existente, no el arreglo pendiente.

## Reintento vigente · Hades sin dictamen

- Releídos Artemisa, `/orquestar`, `/bug-fix`, `/generate-bdd` y `/review-spec` de la instalación 1.1.1; conservados el delta previo, el triaje y `base_calidad`.
- Revisión completa del conflicto de definición solicitada con `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`. Retorno `1` antes del dictamen: `Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access`.
- Sin asignación de Hades: no procede `--enrutar-hallazgo` ni una pregunta humana por el fallo operativo. Se conserva `in_progress`, sin cambiar contratos, perfiles, implementación ni tests, sin señal de cierre ni commit de finalización.
- Se solicita sobre este árbol únicamente `adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests"`. Su resultado queda en la evidencia duradera del verificador y acredita la base existente, no el arreglo pendiente.

## Bloqueo sin progreso
- B-ADV-0036 bloqueada para el humano: 2 intentos sin progreso en dificil; fecha: 2026-11-11T10:28:04
- Cola de la última salida:

    completed","item":{"id":"item_7","type":"agent_message","text":"La revisión de Hades falla antes de emitir dictamen: la organización tiene deshabilitado el acceso de Claude Code por suscripción. Sin una asignación no puedo enrutar el conflicto. Ejecutaré la verificación focalizada del triaje; su resultado solo acredita la base existente, no la corrección pendiente."}}
    {"type":"item.started","item":{"id":"item_8","type":"command_execution","command":"\"C:\\\\Program Files\\\\WindowsApps\\\\OpenAI.CodexPrimaryRuntime.v26-1104-2876-0_26.1104.2876.0_x64__3k8sg7r9htsxt\\\\dependencies\\\\native\\\\powershell\\\\pwsh.exe\" -Command 'adevv orquestar --verificar \"python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests\"'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
    {"type":"item.completed","item":{"id":"item_8","type":"command_execution","command":"\"C:\\\\Program Files\\\\WindowsApps\\\\OpenAI.CodexPrimaryRuntime.v26-1104-2876-0_26.1104.2876.0_x64__3k8sg7r9htsxt\\\\dependencies\\\\native\\\\powershell\\\\pwsh.exe\" -Command 'adevv orquestar --verificar \"python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests\"'","aggregated_output":"[orquestar] verificación reutilizada: python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests ya pasó sobre este mismo árbol (991d498416).\r\n","exit_code":0,"status":"completed"}}
    {"type":"item.completed","item":{"id":"item_9","type":"agent_message","text":"Paso incompleto: Hades no pudo emitir dictamen porque la organización tiene deshabilitado Claude Code por suscripción.\n\nLa verificación focalizada reutilizó evidencia verde del mismo árbol (`991d498416`). B-ADV-0036 permanece `in_progress`, sin corrección ni commit de cierre. No se enrutó ningún hallazgo sin asignación de Hades."}}
    {"type":"turn.completed","usage":{"input_tokens":262918,"cached_input_tokens":223872,"cache_write_input_tokens":0,"output_tokens":1246,"reasoning_output_tokens":46}}
