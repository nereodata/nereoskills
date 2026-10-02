---
name: orquestar
description: Lleva un producto de la idea a su última tarea sin parar. Invocada por una persona, lanza el bucle desatendido (orquestar.py), informa de cómo va o lo para; el bucle deduce la fase del disco y continúa desde donde toque. Invocada por el bucle, ejecuta el paso indicado en modo orquestado. El humano solo interviene al cerrar cada versión.
inputs:
  - accion: (Opcional, persona) lanzar (por defecto) | estado | parar
  - paso: (Lo pasa el bucle) paso a ejecutar
  - arg: (Lo pasa el bucle) ID de tarea/bug o versión
---

# Skill: Orquestador (/orquestar)

**Objetivo:** De una idea a un producto completo y funcional con la máxima agilidad. El humano revisa al cerrar cada versión, no antes.

## ▶️ Dos usos

**Te invoca el bucle** (el prompt indica un paso): ejecuta solo ese paso según el modo orquestado y termina.

**Te invoca una persona** (sin paso): no ejecutes pasos tú. El bucle (`orquestar.py`, junto a esta skill) es quien deduce el estado del disco y continúa desde donde toque. Desde la raíz del proyecto:

- **lanzar**:
  1. Comprueba que existe `<docs>/requirements.md` con commit y que el árbol está limpio. Si no hay requisitos, propón `/ciclo-requisitos` en modo interactivo (con su ronda de preguntas) y no lances.
  2. Averigua el comando de la suite del proyecto (manifiestos, README, CI); si no lo encuentras, pregúntalo.
  3. Ejecuta `python <ruta>/orquestar.py --fondo --harness <arnés> --test "<suite>"` (más `--presupuesto` si lo piden). Vuelve enseguida: el bucle sigue desacoplado, con la salida en `orquestar.log`.
  4. Avisa: los pasos corren sin confirmaciones de permisos (mejor en contenedor o VM), y si tu arnés usa sandbox, puede que el bucle necesite lanzarse fuera de él.
- **estado**: ejecuta `orquestar.py --estado` (fase actual, si hay bucle en marcha y consumo acumulado) y resume el final de `orquestar.log`. Si el bucle paró para la revisión humana, explica qué toca hacer (ver «Revisión de versión»).
- **parar**: ejecuta `orquestar.py --parar`; el bucle termina el paso en curso y para. Relanzar sigue donde iba.

Opciones del script: `--harness claude|codex|gemini|cursor` o `--cmd "<plantilla con {prompt}>"`, `--test`, `--idea`, `--max-pasos`, `--reintentos`, `--presupuesto`, `--espera-max`. Sin `--fondo` corre en primer plano.

**Métricas.** Cada paso añade una línea a `orquestar_metricas.jsonl`: paso, ID, rama, duración y, con `claude`, turnos, tokens por modelo, coste a precio de lista y subagentes. El consumo de una tarea es la suma de sus líneas. Los ficheros del bucle (`orquestar.log`, `.pid`, `.parar` y las métricas) quedan excluidos de git.

## 🧭 Estado

Pendiente = sin `completed`, `cancelled` ni `blocked`. Se deduce solo de artefactos, nunca de lo que el modelo diga que ha hecho (`<docs>` = `docs/requirements` por defecto):

| Estado en disco | Resultado |
|---|---|
| Falta `task_config.yaml` o `<docs>/requirements.md` | PARAR: falta configuración o idea |
| Sin `<docs>/req_analysis.md` | paso `ciclo-requisitos` |
| `req_analysis.md` con `REQUIERE_ACLARACION` | PARAR: preguntas sin valor por defecto seguro |
| Sin `platform_plan.md` | paso `platform-plan` |
| Sin `<docs>/platform_review.md` | paso `revisar-plataforma` |
| `platform_review.md` con `RECHAZADO` | PARAR: plataforma rechazada |
| Sin `work_plan.md` o backlog vacío | paso `work-plan` |
| Rama `release/vX.Y` recién abierta (ninguna tarea empezada), con deuda registrada pendiente y sin `docs/review/versions/vX.Y-deuda.md` | paso `revisar-deuda` |
| Rama `release/vX.Y` con un ID `completed` sin reporte en `docs/review/code_reviews/` | paso `revisar-tarea` |
| Rama `release/vX.Y` con tareas o bugs pendientes | paso `task-dev` / `bug-fix` del ID en curso o de menor `weight` |
| Rama `release/vX.Y` sin pendientes ni `docs/review/versions/vX.Y-arquitectura.md` | paso `revisar-version` |
| Rama `release/vX.Y` sin pendientes y revisada | PARAR: revisión de versión |
| Sin rama abierta y con pendientes | paso `start-version` de la menor versión pendiente |
| Todo cerrado (la deuda registrada, sin versión, no cuenta) | FIN, con el número de mejoras pendientes |

**Deuda registrada** = bug pendiente sin versión (lo crea `/bug-add` a partir de un hallazgo de Hades con destino `registrar`). El bucle no la trabaja hasta que `revisar-deuda` la incluye en una versión.

El bucle también para si un paso no avanza tras 2 intentos, si una tarea se cierra con la suite en rojo (`--test`) o al llegar a `--max-pasos`.

**Sin cuota** (Claude, Codex u otro arnés): si un paso falla y su salida indica límite de uso, el bucle no para. Espera hasta la hora de recuperación que indique el arnés (o 30 min si no la da), reintenta el mismo paso y sigue; `--estado` muestra «esperando cuota hasta…». Para si la espera seguida supera `--espera-max` horas (12 por defecto; 0 = no esperar) o si le piden `--parar`. Cualquier otro fallo del arnés para el bucle.

## ⚙️ Modo orquestado

1. **Un paso por ejecución.** Ejecuta solo el paso indicado y termina: el bucle decide el siguiente.
2. **Sin preguntas.** Donde una skill pida algo al usuario, elige la opción recomendada o el valor por defecto y regístralo (DEC/SUP en el documento de la fase, o en la revisión de versión).
3. **Sin HITL.** `/task-dev` y `/bug-fix` no se detienen en sus HITL: lo que se habría validado va a la revisión de versión. Las revisiones de Hades se mantienen.
4. **Árbol limpio y señal al final.** El artefacto de «Hecho cuando» se escribe lo último, justo antes del commit con que termina cada paso. Las fases de planificación commitean en la rama actual (`docs(plan): <paso>`).
5. **Bloqueo tras 3 rechazos de Hades.** Si solo quedan hallazgos 🟡/🔵, cierra y aplica su destino (`resolver`, `registrar` o `descartar`). Si persisten 🔴/🟠: guarda los cambios en la rama `wip/<ID>`, devuelve `release/vX.Y` al estado previo a la tarea, pon `status: blocked` y anota el motivo y los hallazgos en la revisión de versión. Una tarea que dependa de una bloqueada se bloquea sin intentarla.
6. **Reportes con el ID maestro.** Pasa a Hades el ID de la tarea o bug maestro, para que el reporte sea `docs/review/code_reviews/<ID>-code-review.md`.
7. **Sin fingir.** Si no puedes completar el paso, explica el bloqueo en tu salida y no cambies estados: el bucle lo detectará.

| Paso | Sigue | Ajuste | Hecho cuando |
|---|---|---|---|
| `ciclo-requisitos` | `/ciclo-requisitos` sobre `<docs>/requirements.md` | sin ronda de preguntas de la fase 0 | existe `req_analysis.md` |
| `platform-plan` | `/platform-plan` | — | existe `platform_plan.md` |
| `revisar-plataforma` | Hades `/review-design` sobre `platform_plan.md`, frente a los requisitos; corrige y repite (máx. 3) | — | `platform_review.md` con primera línea `**Veredicto:** APROBADO` o `RECHAZADO` |
| `work-plan` | `/work-plan` | — | `work_plan.md` y tareas con versión en el backlog |
| `start-version` | `/start-version` con la versión indicada | — | existe `release/vX.Y` |
| `revisar-deuda` | Repasa la deuda registrada frente al código actual y a las tareas de vX.Y | **incluir** la que afecta a lo que toca esta versión (mismos módulos o una tarea citada en `origen`): `version: vX.Y.0`, `status: planned` y peso que la ordena antes de las tareas a las que afecta; **cancelar** con motivo la ya resuelta o irrelevante; **dejar** el resto como mejora futura. La deuda no relacionada con la versión no se incluye: la decide el humano | existe `vX.Y-deuda.md` con las tres listas |
| `task-dev` | `/task-dev <ID>` en modo orquestado | — | tarea `completed` y commit |
| `bug-fix` | `/bug-fix <ID>` en modo orquestado | — | bug `completed` y commit |
| `revisar-tarea` | Hades `/review-code` sobre los commits del ID; corrige y repite (máx. 3, regla 5) | sin cambios de código: reporte `N/A` | existe el reporte, o `blocked` |
| `revisar-version` | Hades `/review-code` sobre `git diff main...release/vX.Y`, solo lo transversal: duplicados entre tareas, patrones incoherentes y capas mezcladas. Si el plan de plataforma cambió en la versión, además Hades `/review-design` sobre esas `DEC` | 🔴/🟠 → `/bug-add` en vX.Y; 🟡/🔵 → su destino (`registrar` → deuda registrada) | existe `vX.Y-arquitectura.md` |

`/release` no es un paso del bucle: lo ejecuta el humano tras la revisión.

## 👤 Revisión de versión

Cuando el bucle para con «Versión vX.Y terminada»:
1. Lee `docs/review/versions/vX.Y-revision.md` (y `vX.Y-arquitectura.md` y `vX.Y-deuda.md`) y prueba el producto siguiendo sus pasos de validación.
2. **Defectos:** regístralos con `/bug-add` en la rama `release/vX.Y` y relanza; el bucle los corrige con `/bug-fix`.
3. **Bloqueadas:** desbloquéala (pista o simplificación, `status: planned`), muévela de versión o cancélala.
4. **Mejoras:** para meter en una versión deuda que el bucle no incluyó, ponle esa versión.
5. **Conforme:** ejecuta `/release` y relanza; el bucle abre la siguiente versión.

Formato de cada entrada (una por tarea o bug, la añade `/task-dev` o `/bug-fix`):

```markdown
## T-PRJ-XXXX · Título
- **Especificación**: escenarios añadidos (archivo) y resumen
- **Diseño**: decisiones relevantes (enlace a docs/design/…)
- **Hades**: veredictos y bugs de deuda registrados
- **Validación funcional**: pasos concretos para comprobarlo (comando, URL, datos)
- **Decisiones sin preguntar**: opciones tomadas por defecto
```
