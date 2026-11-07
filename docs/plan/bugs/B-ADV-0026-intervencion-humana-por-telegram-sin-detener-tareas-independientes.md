---
id: B-ADV-0026
title: "El orquestador espera una respuesta humana sin notificarla ni recogerla por Telegram y detiene tareas independientes"
type: bug
weight: 20
dificultad: dificil
version: "v1.1.0"
status: completed
depende_de: ["B-ADV-0023"]
origen: "Incidencia comunicada por el usuario y alcance acordado en conversación (2026-11-02)"
created_at: 2026-11-02
updated_at: 2026-11-07
---

# B-ADV-0026: Intervención humana por Telegram sin detener tareas independientes

## 🎯 Descripción del Fallo

**Comportamiento comunicado:** un paso del orquestador queda esperando una respuesta del usuario, sin enviar la pregunta por Telegram ni aceptar la respuesta por ese canal. La espera impide continuar con otras tareas independientes.

**Evidencia del código:** el modo orquestado ordena no hacer preguntas y ya contempla bloqueos con `pendiente_de: humano`. Los avisos de parada del motor usan el evento `respuesta`, pero no existe un circuito que vincule una pregunta del paso activo con la conversación del gateway, que mantiene sesiones separadas. No se ha inspeccionado la ejecución concreta afectada; la causa exacta de esa espera debe confirmarse durante el triaje.

**Comportamiento esperado:** cuando una tarea requiere una decisión o recurso humano sin valor por defecto seguro, conserva su trabajo, registra una pregunta concreta y queda bloqueada localmente. El usuario recibe el aviso por Telegram y puede responder por ese medio. Mientras llega la respuesta, el bucle continúa con las tareas elegibles independientes y retiene las dependientes. La respuesta se incorpora entre pasos y permite retomar la tarea cuando proceda.

## 📋 Reproducir

1. Ejecutar el bucle con Telegram habilitado, una tarea A que necesita intervención humana, otra B independiente y otra C dependiente de A.
2. Provocar una pregunta o necesidad de intervención en el paso de A y comprobar si queda esperando sin notificación ni liberación del bucle.
3. Responder desde un usuario autorizado por Telegram y comprobar si la respuesta se vincula a A y permite continuarla.

La reproducción debe usar arneses y transporte Telegram controlados, sin enviar mensajes reales durante las pruebas.

## 📋 Criterios de Aceptación

- [x] **CA-1 — Bloqueo local:** la necesidad de intervención se registra con ID de tarea y de pregunta, contexto suficiente y estado consultable. El paso libera el bucle; no queda esperando una entrada interactiva indefinidamente. Se mantienen las decisiones autónomas con valor por defecto seguro del modo orquestado.
- [x] **CA-2 — Conservación del trabajo:** el trabajo de A queda recuperable y aislado antes de empezar B, sin contaminar su árbol, delta ni commits. Coordinar con B-ADV-0023.
- [x] **CA-3 — Aviso accionable:** con Telegram configurado y el evento habilitado, los usuarios autorizados reciben la pregunta, su referencia y cómo responder. Si no hay canal disponible o falla el envío, el bloqueo y el diagnóstico quedan visibles y la pregunta sigue pendiente, sin perderse ni producir avisos duplicados por cada consulta o paso.
- [x] **CA-4 — Continuidad:** B puede ejecutarse mientras A espera; C permanece en espera por su dependencia. Solo cuando no hay trabajo elegible el bucle espera intervención, manteniendo el gateway disponible y mostrando el motivo. Los bloqueos globales se distinguen de los de una tarea.
- [x] **CA-5 — Respuesta vinculada:** Telegram permite responder inequívocamente a una pregunta pendiente del proyecto. Solo usuarios autorizados pueden hacerlo; respuestas ambiguas, referencias inexistentes, cerradas o de otro proyecto no se aplican a otra tarea. Varias preguntas simultáneas y entregas repetidas se gestionan sin mezclar ni duplicar decisiones.
- [x] **CA-6 — Incorporación entre pasos:** si la respuesta llega mientras corre B, se guarda de forma duradera y se incorpora al terminar el paso, sin editar concurrentemente el repositorio. La confirmación distingue respuesta recibida de tarea efectivamente reanudada. Una respuesta que no resuelva el impedimento conserva el bloqueo y explica qué falta.
- [x] **CA-7 — Reanudación:** una respuesta suficiente actualiza el contexto y devuelve A al circuito elegible cuando sus dependencias lo permitan; conserva el trabajo previo y continúa según la planificación. También funciona si el bucle ya quedó esperando por falta de tareas elegibles, sin exigir una segunda orden manual de lanzamiento. Una parada manual explícita se respeta.
- [x] **CA-8 — Recuperación y seguridad:** preguntas, respuestas y estado de incorporación sobreviven a reinicios y recargas, sin perder respuestas ni reanudar dos veces. Se mantienen la autorización por usuario, el aislamiento por proyecto, las restricciones de credenciales y la protección del repositorio durante otros pasos; responder una pregunta no concede permisos adicionales ni autoriza publicar una versión.
- [x] **CA-9 — Verificación:** pruebas con ejecutores y transporte controlados cubren A/B/C, respuesta durante B, varias preguntas, respuesta insuficiente, duplicados, reinicio, fallo de aviso, falta de trabajo elegible y parada manual. Se documenta el flujo de consulta y respuesta.

## 📋 Evidencias

- Relato del usuario en esta conversación (2026-11-02).
- `skills/orquestar/SKILL.md`: modo sin preguntas, bloqueos humanos y avisos del evento `respuesta`.
- `skills/orquestar/orquestar.py`: ejecución de pasos y circuito de avisos; confirmar durante el triaje cómo se produce la espera en el arnés afectado.
- `skills/telegram_gateway/gateway.py`: sesiones conversacionales por usuario/arnés y protección del repositorio mientras existe el PID del bucle.

## Triaje
- base_calidad: cd1b3bdd452f4454bf5a28c620e3c38a52f918a1
- Subfase A: Definición: [EXEC] Escenarios BDD `@B-ADV-0026` (`@CA-1`..`@CA-9`) en `skills/orquestar/features/orquestacion.feature` y `skills/telegram_gateway/features/telegram_gateway.feature` para el circuito de bloqueo local, aviso accionable, respuesta vinculada, continuidad A/B/C e incorporación entre pasos.
- Subfase B: Diseño: [EXEC] Diseño técnico en `docs/design/B-ADV-0026-design.md` cubriendo persistencia atómica de preguntas y cola de respuestas, aislamiento/recuperación en `wip/<ID>`, comandos de consulta/respuesta en Telegram, validación de suficiencia, espera sin trabajo elegible y reanudación respetando parada manual.
- Subfase C1: Pruebas: [EXEC] Suite `skills/orquestar/test_intervencion_humana.py` con ejecutores y transporte Telegram controlados verificando en rojo `CA-1`..`CA-9`.
- Subfase C2: Corrección: [EXEC] Módulo `skills/orquestar/intervencion.py` e integración en `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py`.
- Subfase D: QA: [EXEC] Revisión de Hades (`/review-code`) sobre el delta completo.
- Subfase E: Documentación: [EXEC] Documentación del flujo de consulta y respuesta en `skills/orquestar/SKILL.md`, `skills/telegram_gateway/SKILL.md` y `CHANGELOG.md`.
- Subfase F: Cierre: [EXEC] Calidad del delta, registro en `docs/review/versions/v1.1-revision.md`, estado `completed` y commit semántico.
- Verificación al cierre: `python -m unittest skills.orquestar.test_intervencion_humana tests.test_orquestar.BloqueoSinProgresoTests tests.test_orquestar.RecuperacionAnalisisTests tests.test_orquestar.AvisosTelegramTests tests.test_telegram_gateway skills.telegram_gateway.test_gateway_control skills.telegram_gateway.test_cierre_version tests.test_instructions_cleanliness tests.test_package_and_instructions` porque ejercita el circuito completo de intervención humana, aislamiento de bloqueos, avisos, gateway, cierre de versión y empaquetado.

- Rojo acreditado: 8 pruebas, fallo del prompt sin `--preguntar` y API `solicitar_intervencion` ausente; salida conservada por `--verificar`.
- Revisión de pruebas: Hades solicitó espera activa, aserciones de permisos y contexto, eliminación de API exclusiva de fixtures; corregido y segunda revisión APROBADO (9/10), con 9 pruebas focalizadas en verde.
- Análisis estático: `git diff --check` mediante `--verificar`; formato/lint del delta con `--calidad --base` (omitidos por ausencia de herramientas). Sin tipador ni escáner de secretos configurados; no se cambian dependencias ni credenciales.
- Diseño concretado: cola de respuestas y preguntas en un único JSON atómico con bloqueo del sistema operativo; ver ajustes en el diseño. No se crea una cola JSONL separada.
- Hades RC-01/02/03: regresiones añadidas y reproducidas en rojo para selección de pregunta actual, rama de incorporación y corte previo al bloqueo. Corrección de resolución inequívoca, rama persistida con guarda de limpieza y recuperación por fases con contenidos de escritura preparados.
- RT-05 resuelto: recuperación del corte con módulo recién cargado y comprobaciones del registro en disco previo. Revisión final de pruebas APROBADO (9/10), sin hallazgos pendientes; suite específica ampliada a 12 pruebas.
- Extensión RC-03 y RC-04: prueba 13 reproduce que el bucle ejecuta una tarea con bloqueo sin persistir y trabajo ajeno; guarda global de persistencia hasta recuperación segura. El arranque reconcilia también el diagnóstico de envío iniciado sin reenviar el aviso.
