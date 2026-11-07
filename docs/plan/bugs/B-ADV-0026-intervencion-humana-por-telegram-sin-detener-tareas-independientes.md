---
id: B-ADV-0026
title: "El orquestador espera una respuesta humana sin notificarla ni recogerla por Telegram y detiene tareas independientes"
type: bug
weight: 20
dificultad: dificil
version: "v1.1.0"
status: planned
depende_de: ["B-ADV-0023"]
origen: "Incidencia comunicada por el usuario y alcance acordado en conversación (2026-11-02)"
created_at: 2026-11-02
updated_at: 2026-11-02
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

- [ ] **CA-1 — Bloqueo local:** la necesidad de intervención se registra con ID de tarea y de pregunta, contexto suficiente y estado consultable. El paso libera el bucle; no queda esperando una entrada interactiva indefinidamente. Se mantienen las decisiones autónomas con valor por defecto seguro del modo orquestado.
- [ ] **CA-2 — Conservación del trabajo:** el trabajo de A queda recuperable y aislado antes de empezar B, sin contaminar su árbol, delta ni commits. Coordinar con B-ADV-0023.
- [ ] **CA-3 — Aviso accionable:** con Telegram configurado y el evento habilitado, los usuarios autorizados reciben la pregunta, su referencia y cómo responder. Si no hay canal disponible o falla el envío, el bloqueo y el diagnóstico quedan visibles y la pregunta sigue pendiente, sin perderse ni producir avisos duplicados por cada consulta o paso.
- [ ] **CA-4 — Continuidad:** B puede ejecutarse mientras A espera; C permanece en espera por su dependencia. Solo cuando no hay trabajo elegible el bucle espera intervención, manteniendo el gateway disponible y mostrando el motivo. Los bloqueos globales se distinguen de los de una tarea.
- [ ] **CA-5 — Respuesta vinculada:** Telegram permite responder inequívocamente a una pregunta pendiente del proyecto. Solo usuarios autorizados pueden hacerlo; respuestas ambiguas, referencias inexistentes, cerradas o de otro proyecto no se aplican a otra tarea. Varias preguntas simultáneas y entregas repetidas se gestionan sin mezclar ni duplicar decisiones.
- [ ] **CA-6 — Incorporación entre pasos:** si la respuesta llega mientras corre B, se guarda de forma duradera y se incorpora al terminar el paso, sin editar concurrentemente el repositorio. La confirmación distingue respuesta recibida de tarea efectivamente reanudada. Una respuesta que no resuelva el impedimento conserva el bloqueo y explica qué falta.
- [ ] **CA-7 — Reanudación:** una respuesta suficiente actualiza el contexto y devuelve A al circuito elegible cuando sus dependencias lo permitan; conserva el trabajo previo y continúa según la planificación. También funciona si el bucle ya quedó esperando por falta de tareas elegibles, sin exigir una segunda orden manual de lanzamiento. Una parada manual explícita se respeta.
- [ ] **CA-8 — Recuperación y seguridad:** preguntas, respuestas y estado de incorporación sobreviven a reinicios y recargas, sin perder respuestas ni reanudar dos veces. Se mantienen la autorización por usuario, el aislamiento por proyecto, las restricciones de credenciales y la protección del repositorio durante otros pasos; responder una pregunta no concede permisos adicionales ni autoriza publicar una versión.
- [ ] **CA-9 — Verificación:** pruebas con ejecutores y transporte controlados cubren A/B/C, respuesta durante B, varias preguntas, respuesta insuficiente, duplicados, reinicio, fallo de aviso, falta de trabajo elegible y parada manual. Se documenta el flujo de consulta y respuesta.

## 📋 Evidencias

- Relato del usuario en esta conversación (2026-11-02).
- `skills/orquestar/SKILL.md`: modo sin preguntas, bloqueos humanos y avisos del evento `respuesta`.
- `skills/orquestar/orquestar.py`: ejecución de pasos y circuito de avisos; confirmar durante el triaje cómo se produce la espera en el arnés afectado.
- `skills/telegram_gateway/gateway.py`: sesiones conversacionales por usuario/arnés y protección del repositorio mientras existe el PID del bucle.
