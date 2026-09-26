---
name: orquestar
description: Lleva un producto de la idea a su última tarea sin parar. Deduce la fase del disco y ejecuta el siguiente paso del ciclo (requisitos, arquitectura, plan, versiones y task-dev) en modo orquestado; el humano solo interviene al cerrar cada versión.
inputs:
  - paso: (Opcional) paso a ejecutar; si falta, se deduce del estado
  - arg: (Opcional) ID de tarea/bug o versión
---

# Skill: Orquestador (/orquestar)

**Objetivo:** De una idea a un producto completo y funcional con la máxima agilidad. El humano revisa al cerrar cada versión, no antes.

## ▶️ Ejecución

- **En bucle (recomendado).** Desde la raíz del proyecto:
  ```bash
  python .agents/skills/orquestar/orquestar.py --harness claude|codex|gemini|cursor [--test "<suite>"] [--idea "<texto>"]
  ```
  Cada paso es una ejecución nueva del arnés, con contexto limpio. El script deduce el estado del disco, lanza el paso, comprueba que hubo progreso y repite. `--estado` solo muestra la fase; `--cmd "<plantilla con {prompt}>"` admite otro arnés.
- **A mano.** En cualquier arnés: deduce el paso con la tabla de estado y ejecuta **uno**.

Los arneses se lanzan sin confirmaciones de permisos: ejecútalo en un contenedor o VM.

## 🧭 Estado

Pendiente = sin `completed`, `cancelled` ni `blocked`. Se deduce solo de artefactos, nunca de lo que el modelo diga que ha hecho (`<docs>` = `docs/requirements` por defecto):

| Estado en disco | Resultado |
|---|---|
| Falta `task_config.yaml` o `<docs>/requirements.md` | PARAR: falta configuración o idea |
| Sin `<docs>/req_analysis.md` | paso `ciclo-requisitos` |
| `req_analysis.md` con `REQUIERE_ACLARACION` | PARAR: preguntas sin valor por defecto seguro |
| Sin `needs_analysis.md` / `platform_plan.md` | paso `needs-analysis` / `platform-plan` |
| Sin `<docs>/platform_review.md` | paso `revisar-plataforma` |
| `platform_review.md` con `RECHAZADO` | PARAR: plataforma rechazada |
| Sin `work_plan.md` o backlog vacío | paso `work-plan` |
| Rama `release/vX.Y` con un ID `completed` sin reporte en `docs/review/code_reviews/` | paso `revisar-tarea` |
| Rama `release/vX.Y` con tareas o bugs pendientes | paso `task-dev` / `bug-fix` del ID en curso o de menor `weight` |
| Rama `release/vX.Y` sin pendientes ni `docs/review/versions/vX.Y-arquitectura.md` | paso `revisar-version` |
| Rama `release/vX.Y` sin pendientes y revisada | PARAR: revisión de versión |
| Sin rama abierta y con pendientes | paso `start-version` de la menor versión pendiente |
| Todo cerrado | FIN |

El bucle también para si un paso no avanza tras 2 intentos, si una tarea se cierra con la suite en rojo (`--test`) o al llegar a `--max-pasos`.

## ⚙️ Modo orquestado

1. **Un paso por ejecución.** Ejecuta solo el paso indicado y termina: el bucle decide el siguiente.
2. **Sin preguntas.** Donde una skill pida algo al usuario, elige la opción recomendada o el valor por defecto y regístralo (DEC/SUP en el documento de la fase, o en la revisión de versión).
3. **Sin HITL.** `/task-dev` y `/bug-fix` no se detienen en sus HITL: lo que se habría validado va a la revisión de versión. Las revisiones de Hades se mantienen.
4. **Árbol limpio.** Termina cada paso con commit. Las fases de planificación commitean en la rama actual (`docs(plan): <paso>`).
5. **Bloqueo tras 3 rechazos de Hades.** Si solo quedan hallazgos 🟡/🔵, cierra y llévalos como deuda a la revisión de versión. Si persisten 🔴/🟠: guarda los cambios en la rama `wip/<ID>`, devuelve `release/vX.Y` al estado previo a la tarea, pon `status: blocked` y anota el motivo y los hallazgos en la revisión de versión. Una tarea que dependa de una bloqueada se bloquea sin intentarla.
6. **Reportes con el ID maestro.** Pasa a Hades el ID de la tarea o bug maestro, para que el reporte sea `docs/review/code_reviews/<ID>-code-review.md`.
7. **Sin fingir.** Si no puedes completar el paso, explica el bloqueo en tu salida y no cambies estados: el bucle lo detectará.

| Paso | Sigue | Ajuste | Hecho cuando |
|---|---|---|---|
| `ciclo-requisitos` | `/ciclo-requisitos` sobre `<docs>/requirements.md` | sin ronda de preguntas de la fase 0 | existe `req_analysis.md` |
| `needs-analysis` | `/needs-analysis` | — | existe `needs_analysis.md` |
| `platform-plan` | `/platform-plan` | — | existe `platform_plan.md` |
| `revisar-plataforma` | Hades con los pilares de `/review-design` sobre `platform_plan.md`, frente a requisitos y `needs_analysis.md`; corrige y repite (máx. 3) | — | `platform_review.md` con primera línea `**Veredicto:** APROBADO` o `RECHAZADO` |
| `work-plan` | `/work-plan` | — | `work_plan.md` y tareas con versión en el backlog |
| `start-version` | `/start-version` con la versión indicada | — | existe `release/vX.Y` |
| `task-dev` | `/task-dev <ID>` en modo orquestado | — | tarea `completed` y commit |
| `bug-fix` | `/bug-fix <ID>` en modo orquestado | — | bug `completed` y commit |
| `revisar-tarea` | Hades `/review-code` sobre los commits del ID (y `/review-design` si no hubo diseño); corrige y repite (máx. 3, regla 5) | sin cambios de código: reporte `N/A` | existe el reporte, o `blocked` |
| `revisar-version` | Hades con `/review-design` y `/review-code` sobre `git diff main...release/vX.Y`: duplicados entre tareas, patrones incoherentes, capas mezcladas | 🔴/🟠 → `/bug-add` en vX.Y; 🟡/🔵 → deuda en la revisión | existe `vX.Y-arquitectura.md` |

`/release` no es un paso del bucle: lo ejecuta el humano tras la revisión.

## 👤 Revisión de versión

Cuando el bucle para con «Versión vX.Y terminada»:
1. Lee `docs/review/versions/vX.Y-revision.md` (y `vX.Y-arquitectura.md`) y prueba el producto siguiendo sus pasos de validación.
2. **Defectos:** regístralos con `/bug-add` en la rama `release/vX.Y` y relanza; el bucle los corrige con `/bug-fix`.
3. **Bloqueadas:** desbloquéala (pista o simplificación, `status: planned`), muévela de versión o cancélala.
4. **Conforme:** ejecuta `/release` y relanza; el bucle abre la siguiente versión.

Formato de cada entrada (una por tarea o bug, la añade `/task-dev` o `/bug-fix`):

```markdown
## T-PRJ-XXXX · Título
- **Especificación**: escenarios añadidos (archivo) y resumen
- **Diseño**: decisiones relevantes (enlace a docs/design/…)
- **Hades**: veredictos y deuda técnica pendiente
- **Validación funcional**: pasos concretos para comprobarlo (comando, URL, datos)
- **Decisiones sin preguntar**: opciones tomadas por defecto
```
