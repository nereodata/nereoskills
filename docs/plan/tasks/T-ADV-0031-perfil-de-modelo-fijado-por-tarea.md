---
id: T-ADV-0031
title: "Fijar en una tarea o bug el arnés, el modelo y el esfuerzo con que se ejecuta"
type: funcional
weight: 150
dificultad: media
version: "v1.0.0"
status: completed
depende_de: []
origen: "Petición del usuario (2026-10-27): además de la dificultad, poder indicar que una tarea concreta se lance con un modelo y un razonamiento determinados"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# T-ADV-0031: Fijar en una tarea o bug el arnés, el modelo y el esfuerzo con que se ejecuta

## 🎯 Objetivo de Negocio
Hoy el modelo de cada paso sale de `orchestration.json`: el rol, su perfil por dificultad, las reservas y la escalada. Las tareas no indican modelo, y eso debe seguir siendo lo normal. Pero a veces la persona sabe que una tarea concreta necesita un modelo y un esfuerzo determinados, por ejemplo Opus con esfuerzo alto para un diseño delicado, o un modelo barato para un cambio mecánico. Esa elección no encaja con ninguna dificultad. Debe poder indicarse en la propia tarea, sin tocar la configuración del proyecto.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Campo opcional en el frontmatter):** una tarea o bug puede declarar un campo opcional `perfil`, con dos formas:
  - Perfil único, que se aplica al rol que ejecuta el paso de la tarea (Artemisa en `task-dev` y `bug-fix`): `perfil: {harness: claude, model: claude-opus-5-5, effort: high}`.
  - Perfiles por rol, para fijar también la revisión, la especificación o la documentación de esa tarea: `perfil: {artemisa: {...}, hades: {...}, atenea: {...}}`.

  Si falta `harness`, `model` o `effort`, se toman del perfil que correspondería por dificultad. Sin el campo, el comportamiento es exactamente el actual.
- [x] **CA-M-2 (Precedencia):** el perfil fijado sustituye al que tocaría por dificultad (`rol_de()`), en los pasos del bucle y en los subagentes del paso (Hades, Clio…) cuando se fija para su rol. `--agentes` y el registro de métricas lo muestran como «fijado por la tarea».
- [x] **CA-M-3 (Reservas y escalada):** el perfil fijado se intenta primero.
  - **Si no está disponible** (por cuota o porque el arnés no existe): se sigue con las reservas del perfil por dificultad y se avisa una vez («T-XXX: perfil fijado claude/claude-opus-5-5 sin cuota; uso la reserva …»).
  - **Con `perfil.estricto: true`:** no se cambia de modelo. Si falta cuota se espera, y si el arnés no existe la tarea se bloquea para la persona.
  - **Escalada y promoción:** se aplican como hoy, porque son la salida cuando la tarea no avanza. Con `estricto`, la tarea se bloquea en lugar de cambiar de modelo.
- [x] **CA-M-4 (Validación):** al leer el backlog, un `perfil` con un arnés no soportado, un esfuerzo no válido o un rol desconocido se informa como error del backlog con un mensaje claro, igual que las dependencias inválidas, sin lanzar el paso. Ningún paso del bucle puede añadir ni cambiar el `perfil` de una tarea: solo lo hace la persona, con `/task-add`, `/bug-add` o a mano.
- [x] **CA-M-5 (Registro de tareas):** `/task-add` y `/bug-add`, tanto las skills como las órdenes de Telegram, documentan el campo opcional y aceptan indicarlo al crear la tarea.
- [x] **CA-M-6 (Pruebas y documentación):** pruebas de que, sin `perfil`, nada cambia; de que se aplica un perfil único y un perfil por rol; de que se completa a partir del perfil por dificultad; de que se conmuta a la reserva con aviso; de que `estricto` espera o bloquea; y de que un perfil inválido se rechaza. Documentación en `docs/orquestacion.md` y en `skills/orquestar/SKILL.md`.

## Triaje (task-dev, modo orquestado)
- **Subfase A: Definición** [EXEC]: escenarios `@T-ADV-0031` en `skills/orquestar/features/orquestacion.feature`, trasladados de los CA-M-1..6 sin ampliarlos; sin `/review-spec` aparte porque no añaden nada a los criterios aprobados.
- **Subfase B: Diseño** [SKIP]: sin decisiones de arquitectura fuera del plan; las de implementación están en DEC-DEV-01..04.
- **Subfase C1: Pruebas** [EXEC]: `skills/orquestar/test_perfil_fijado.py`; se revisan junto al código en D.
- **Subfase C2: Implementación** [EXEC]: `orquestar.py` (lectura, validación, precedencia, reservas, estricto, métricas, alta) y `gateway.py` (`--perfil`, `--estricto`).
- **Subfase D: QA** [EXEC]: una revisión `/review-code` de Hades sobre el delta completo, incluidas las pruebas.
- **Subfase E: Documentación** [EXEC]: `skills/orquestar/SKILL.md`, `docs/orquestacion.md`, `task-add`, `bug-add`, `telegram_gateway` y CHANGELOG.
- **Subfase F: Cierre** [EXEC].
- **Verificación al cierre**: `python -m unittest skills.orquestar.test_perfil_fijado` más las pruebas de reservas, cuotas, agentes, métricas y gateway que tocan `rol_de`, `registrar` y las altas; la suite completa la pasa el bucle.

## Decisiones de desarrollo
- **DEC-DEV-01**: el perfil único se aplica solo a Artemisa (rol que ejecuta `task-dev` y `bug-fix`); Atenea, Hades y el resto lo reciben únicamente con la forma por rol. `estricto` va en el nivel superior y vale para todos los roles fijados.
- **DEC-DEV-02**: las reservas de un perfil fijado se expanden desde el perfil por dificultad, no desde el fijado, para que no hereden su arnés o modelo.
- **DEC-DEV-03**: un perfil inválido en una tarea pendiente para el bucle (`PARAR`, evento `respuesta`) porque solo una persona puede corregirlo; las cerradas no cuentan.
- **DEC-DEV-04**: con `estricto`, el bloqueo registra un evento `promocion` con la misma dificultad para reiniciar los contadores de reintentos si la persona la desbloquea.
- **DEC-DEV-05**: esfuerzos admitidos: `minimal`, `low`, `medium`, `high`, `xhigh`, `max`. En Telegram: `--perfil arnés/modelo[/esfuerzo]` y `--estricto`.
