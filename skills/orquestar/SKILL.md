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
  3. Ejecuta `adevv orquestar --fondo --harness <arnés> --test "<suite>"` (más `--presupuesto` si lo piden). Vuelve enseguida: el bucle sigue desacoplado, con la salida en `orquestar.log`.
  4. Avisa: los pasos corren sin confirmaciones de permisos (mejor en contenedor o VM), y si tu arnés usa sandbox, puede que el bucle necesite lanzarse fuera de él.
- **estado**: ejecuta `adevv orquestar --estado` (fase actual, si hay bucle en marcha y consumo acumulado) y resume el final de `orquestar.log`. Si el bucle paró para la revisión humana, explica qué toca hacer (ver «Revisión de versión»). Si hay propuestas de producto pendientes, presenta la síntesis y la tabla de `vX.Y-producto.md`, recoge los cambios del usuario («mueve P-03 al backlog, rechaza P-05»), escríbelos en la tabla y, cuando confirme, marca `**Decisión:** APLICAR`, haz commit y relanza: el bucle crea las tareas.
- **parar**: ejecuta `adevv orquestar --parar`; el bucle termina el paso en curso y para. Relanzar sigue donde iba.

Opciones del script: `--harness claude|codex|agy|gemini|cursor` (fuerza ese arnés en todos los pasos) o `--cmd "<plantilla con {prompt}>"`, `--test` (por defecto, `validation.command` de `task_config.yaml`), `--idea`, `--max-pasos`, `--reintentos`, `--presupuesto`, `--espera-max`.

**Roles** (`orchestration.json` en la raíz, opcional): `atenea`, `artemisa`, `hades`, `clio` y `cronos`, cada uno con `harness`, `model` y `effort` (y `instructions` si no es `agents/<rol>.md`). Los pasos del bucle los ejecutan dos roles: **Artemisa** (`task-dev`, `bug-fix` y `revisar-tarea`) y **Atenea** (todos los demás: definición, arquitectura, plan, especificación y decisiones de versión). Cada paso se lanza con el arnés y el modelo de su rol (`claude`, `codex`, `agy`, `gemini` o `cursor`; el esfuerzo solo con `claude`, `codex` y `agy`) y con el agente de `agents/<rol>.md`. Sin `artemisa` se usa la antigua clave `development`, y sin `atenea`, la de Artemisa. `pasos.<paso>` dentro de un rol ajusta su configuración para ese paso (p. ej. `"pasos": {"platform-plan": {"effort": "high"}}`; en Hades, el paso es el que lo lanza). `dificultad.<sencilla|media|dificil>` dentro de un rol ajusta su configuración (`model`, `effort`, `harness`) según la dificultad declarada en la tarea o bug (`sencilla`, `media` por defecto, o `dificil`), aplicándose tanto al paso principal como a subagentes (`ORQUESTAR_ID`); se combina con `pasos.<paso>`. **Subida automática de dificultad:** cuando una tarea o bug acumula más de 2 reintentos (ejecuciones de paso sobre ese `ID`, pasos seguidos sin progreso o rechazos seguidos de Hades desde la última subida), el bucle promueve su dificultad automáticamente un escalón (`sencilla` $\to$ `media`, `media` $\to$ `dificil`), actualizando el campo `dificultad:` en el frontmatter del fichero, reiniciando contadores e iniciando sesión limpia con el perfil del nuevo nivel antes de recurrir a la escalada o al bloqueo. **Escalada:** si la tarea ya está en `dificil` (o el rol no define niveles en `dificultad`), con `artemisa.escalada` (`rechazos`, por defecto 2, y la configuración superior, p. ej. otro `model`), el bucle cuenta los veredictos `RECHAZADO` seguidos de Hades sobre cada ID; al llegar al tope, Artemisa recibe la orden de commitear y terminar el paso, y el bucle relanza la tarea con la escalada. Si tras la escalada se repite el tope, se aplica la regla 5 y la tarea se bloquea. Los roles que se lanzan con `--agente` admiten `claude`, `codex` o `agy`. Si hay `hades`, las revisiones se lanzan con `adevv orquestar --agente hades --prompt-file <mandato>` o `--prompt "<mandato>"`, que usa su arnés y modelo y registra su consumo. Al usar `--prompt-file <ruta>`, si el fichero está en la raíz del proyecto y no está rastreado por git, el orquestador lo elimina automáticamente al terminar (incluso si hay fallo o falta de cuota); además, `orquestar_prompt.txt` queda excluido de git por defecto. La clave `reserva` (objeto único o lista ordenada, p. ej. `[{"model": "gemini-3.8-flash-medium"}, {"harness": "claude", "model": "sonnet"}]`) define modelos o arneses de reserva en roles o subbloques (`pasos`, `dificultad`), heredando del rol los campos no redefinidos (`harness`, `model`, `effort`). La clave `producto` (`true` o lista de versiones, p. ej. `["v0.3", "v1.0"]`) activa la revisión de producto al cerrar esas versiones; sin ella, el bucle no la hace.

**Detalle de estado** (`--estado` y `/estado` de Telegram): cuando hay un paso pendiente muestran su dificultad, el ejecutor Artemisa/Atenea y Hades con arnés, modelo, esfuerzo y reservas efectivos; indican la escalada de Artemisa. También muestran tokens registrados en las últimas 5 h por arnés/modelo (entrada, caché leída/escrita y salida; razonamiento no se suma de nuevo), y los agotamientos conocidos con vencimiento y minutos restantes, en hora local con offset. La espera global se indica aparte. «Sin agotamiento registrado» expresa ausencia de evidencia, no disponibilidad garantizada del proveedor. Los nuevos intentos conservan su plazo de cuota incluso al conmutar a reserva; los registros antiguos sin plazo o modelo no permiten reconstruirlo.

**Verificación** (`adevv orquestar --verificar ["<comando>"]`): sin comando ejecuta la suite. Guarda el resultado ligado al contenido exacto del árbol (incluidos los cambios sin commitear) y, si ya pasó en verde sobre ese mismo árbol, lo reutiliza sin ejecutar nada. La usan el desarrollador y Hades con las pruebas que marca el triaje de cada tarea; el bucle pasa la suite completa una sola vez por versión, cuando no quedan tareas elegibles (antes de `revisar-version` y antes de parar para la revisión humana). Sin `--fondo` corre en primer plano.

**Recarga automática (desde v0.5).** Los motores ejecutados desde el almacén `~/.adevv/versions/` (o `$ADEVV_HOME/versions/`) comprueban `active.json` entre pasos. Si apunta a otra versión con el motor disponible, lanzan su sucesor conservando argumentos, raíz, contadores de pasos/reintentos y espera acumulada; transfieren `orquestar.pid` y escriben `[orquestar] recargado a versión X.Y.Z`. El paso actual siempre termina antes. Las señales de parada tienen prioridad y se conservan durante la transferencia. Un puntero inválido, destino ausente o fallo al lanzar mantiene el proceso anterior. Los árboles de desarrollo y las consultas no se recargan. La instalación conserva intactos los archivos en uso; las versiones anteriores a v0.5 siguen necesitando reinicio manual.

**Métricas.** Registro común en `orquestar_metricas.jsonl`, con `tipo`: `paso` (cada ejecución del bucle), `agente` (cada rol lanzado con `--agente`, ligado al paso y al ID en curso), `espera` (esperas de cuota) y `verificacion` (ejecutada o reutilizada). Incluye duración y, con `claude` y `codex`, turnos y tokens por modelo (`claude` informa además el coste a precio de lista). `--estado` lo resume y muestra las tareas que más consumen. Los ficheros del bucle (`orquestar.log`, `.pid`, `.parar`, `.espera`, las métricas y las evidencias) quedan excluidos de git.

### Consulta y exportación de métricas

`adevv orquestar --metricas [FILTRO]` (alias `--metrics`) consulta el registro y el backlog sin arrancar ni detener el bucle. Sin filtro muestra todas las versiones; acepta `todas` / `all`, `ultima` / `last`, `ultimas:N` / `last:N` (N positivo), o una lista como `v0.2,v0.3.0`. `--version-filtro FILTRO` sustituye al filtro posicional. El orden es numérico; `v0.3` y `v0.3.0` representan el mismo bloque.

- Tabla con desglose y totales: `adevv orquestar --metricas ultima`.
- CSV por stdout: `adevv orquestar --metrics last:2 --csv` (también `--csv -`).
- Archivo UTF-8 con cabecera: `adevv orquestar --metricas v0.2,v0.3 --csv consumo.csv`.

Cada fila muestra ID, versión, tipo, dificultad actual, estimación por dificultad (7/12/25 minutos), duración real, modelos y tokens de desarrollo y Hades, llamadas/rechazos, verificaciones/reutilizaciones y coste USD. Los contadores de tokens reproducen `entrada`, `cache_leida`, `salida` y `razonamiento` tal como los registra cada arnés. La duración real suma solo los pasos principales: ya incluyen sus revisiones. El catálogo incluye el backlog aunque todavía no tenga consumo; los pasos de versión tienen estimación cero. La asociación usa el ID del backlog, después versión explícita, rama o ID de versión del registro. Lo que no puede atribuirse se conserva bajo `sin-version`, visible con `todas`.

Un `coste_usd` positivo prevalece sobre la estimación; sin él se estima por modelo, respetando también un coste positivo propio del modelo. Las tarifas son referencias ilustrativas fijas en USD por millón de tokens de entrada/caché/salida, no precios vigentes: Opus 5/0.5/25; Sonnet 3/0.3/15; Haiku 1/0.1/5; Gemini Argon/Pro 2/0.2/12; Flash 0.5/0.05/3; GPT/Codex y desconocidos 2.5/0.25/10. Razonamiento no se factura de nuevo. Se trata de una comparación aproximada, sin reconstruir cambios históricos de dificultad ni reinterpretar los contadores de los arneses. Un JSONL corrupto produce un error con número de línea y no exporta resultados parciales.

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
| Alguna tarea maestra abierta con versión y sin el campo `depende_de` | paso `calcular-dependencias` |
| `depende_de` con IDs inexistentes o ciclos | PARAR: dependencias inválidas |
| Rama `release/vX.Y` recién abierta (ninguna tarea empezada), con deuda registrada pendiente y sin `docs/review/versions/vX.Y-deuda.md` | paso `revisar-deuda` |
| Rama `release/vX.Y` con un ID `completed` sin reporte en `docs/review/code_reviews/` | paso `revisar-tarea` |
| Rama `release/vX.Y` con un ID `blocked` y `pendiente_de: especificador` | paso `especificar` (primero el que más tareas retiene) |
| Rama `release/vX.Y` con pendientes elegibles (todas sus `depende_de` completadas) | paso `task-dev` / `bug-fix`: el ID en curso, si no el que más tareas desbloquea, y a igualdad el de menor `weight` |
| Rama `release/vX.Y` sin elegibles ni `docs/review/versions/vX.Y-arquitectura.md` | paso `revisar-version` |
| Rama `release/vX.Y` revisada, con bloqueadas o en espera | PARAR: bloqueos de la versión, con cada tarea en espera y la causa raíz que la retiene |
| Rama `release/vX.Y` revisada, sin pendientes, con revisión de producto activa para vX.Y y sin `vX.Y-producto.md` | paso `revisar-producto` |
| `vX.Y-producto.md` con `**Decisión:** APLICAR` | paso `aplicar-producto` |
| Rama `release/vX.Y` revisada y sin pendientes | PARAR: revisión de versión (y decisiones de producto, si hay informe `PENDIENTE`) |
| Sin rama abierta y algún `vX.Y-producto.md` con `**Decisión:** PENDIENTE` | PARAR: decisiones de producto pendientes (no se abre otra versión) |
| Sin rama abierta y con pendientes | paso `start-version` de la menor versión pendiente |
| Todo cerrado (la deuda registrada, sin versión, no cuenta) | FIN, con el número de mejoras pendientes |

**En espera** = pendiente con alguna `depende_de` sin completar. Se calcula en cada vuelta; no se escribe ni se lanza nada para ella: cuando su dependencia se completa, vuelve a ser elegible sola.

**Deuda registrada** = bug pendiente sin versión (lo crea `/bug-add` a partir de un hallazgo de Hades con destino `registrar`). El bucle no la trabaja hasta que `revisar-deuda` la incluye en una versión.

El bucle también para si un paso no avanza tras 2 intentos, si la suite está en rojo al terminar la versión (`--test`) o al llegar a `--max-pasos`.

**Sin cuota** (Claude, Codex u otro arnés): si un paso o subagente falla y su salida indica límite de uso, el bucle conmuta inmediatamente a la siguiente `reserva` configurada (iniciando sesión nueva si cambia de arnés) y registra cada intento en métricas. Si se agotan el principal y todas las reservas, el bucle no para: espera hasta la hora de recuperación más temprana entre las cuotas reportadas (o 30 min si no la da), reintenta el mismo paso y sigue; `--estado` muestra «esperando cuota hasta…». Para si la espera seguida supera `--espera-max` horas (12 por defecto; 0 = no esperar) o si le piden `--parar`. Cualquier otro fallo del arnés para el bucle.

**Avisos por Telegram** (opcional): con `TELEGRAM_BOT_TOKEN` y `TELEGRAM_ALLOWED_USER_IDS` (IDs separados por comas) en el `.env` local o en el entorno, el bucle avisa a esos usuarios de lo que pasa mientras nadie mira. Son las mismas variables del gateway (`/telegram-gateway`), que además atiende `/estado`, `/tarea` y `/bug`. El token nunca va en un fichero. En `orchestration.json`, la clave `telegram` solo elige los eventos (`eventos`; por defecto, todos) o los apaga (`"telegram": false`):

Al arrancar el bucle en primer o segundo plano, esas credenciales también activan el gateway automáticamente en segundo plano. Se conserva un `telegram.pid` vivo y se recuperan marcas obsoletas; si falla el arranque se informa y el bucle continúa. `"telegram": false` desactiva avisos y autoarranque. Las consultas (`--estado`, métricas, verificaciones y revisiones) no lo arrancan. `adevv telegram --fondo` permite iniciarlo manualmente y `adevv telegram --parar` solicita su parada al acabar la operación actual. PID, salida y señal quedan en `telegram.pid`, `telegram.log` y `telegram.parar`, excluidos de git. El gateway sigue escuchando después de parar o terminar el bucle.

| Evento | Cuándo |
|---|---|
| `version` | La versión no tiene más tareas elegibles (terminada, con bloqueos o con la suite en rojo) y FIN del producto |
| `cuota` | Empieza una espera por falta de cuota, o el bucle para porque la espera supera `--espera-max` |
| `respuesta` | Cualquier otra parada que necesita al humano: requisitos con preguntas, plataforma rechazada, dependencias inválidas, decisiones de producto pendientes |
| `error` | Fallo del arnés, paso sin progreso, cambios sin commitear o `--max-pasos` |

```json
"telegram": {"eventos": ["version", "cuota", "respuesta"]}
```

`adevv orquestar --aviso-prueba` envía un mensaje de prueba. Un aviso que no se puede enviar se anota en el log y el bucle sigue. Parar con `adevv orquestar --parar` no avisa. Todos los avisos enviados a Telegram por el bucle añaden al pie la firma con la versión de Adevv en ejecución (`— Adevv vX.Y.Z`).

**Buzón.** Las tareas y bugs pedidos por Telegram con el bucle en marcha esperan en `orquestar_buzon.jsonl`. Al empezar cada paso, el bucle los registra sin versión (`status: backlog`), los commitea solos (`docs(plan): altas desde Telegram (…)`) y avisa del ID. No entran en la versión en curso: les pones versión tú, o `revisar-deuda` si son bugs.

## ⚙️ Modo orquestado

1. **Un paso por ejecución.** Ejecuta solo el paso indicado y termina: el bucle decide el siguiente.
2. **Sin preguntas.** Donde una skill pida algo al usuario, elige la opción recomendada o el valor por defecto y regístralo (DEC/SUP en el documento de la fase, o en la revisión de versión).
3. **Sin HITL.** `/task-dev` y `/bug-fix` no se detienen en sus HITL: lo que se habría validado va a la revisión de versión. Las revisiones de Hades se mantienen.
4. **Árbol limpio y señal al final.** El artefacto de «Hecho cuando» se escribe lo último, justo antes del commit con que termina cada paso. Las fases de planificación commitean en la rama actual (`docs(plan): <paso>`).
5. **Enrutado de Hades.** Cada 🔴/🟠 llega con quién lo resuelve (`para:`). Lo del `desarrollador` lo corriges y repites la revisión. Si alguno es del `especificador` o del `humano`: guarda los cambios en la rama `wip/<ID>`, devuelve `release/vX.Y` al estado previo a la tarea, pon `status: blocked` y `pendiente_de: especificador` (o `humano` si alguno es suyo) y anota los hallazgos en la revisión de versión, con la pregunta de Hades si es para el humano. Si solo quedan 🟡/🔵, cierra y aplica su destino (`resolver`, `registrar` o `descartar`). No toques las tareas que dependen de ella: el bucle las deja en espera y sigue con el resto.
6. **Reportes con el ID maestro.** Pasa a Hades el ID de la tarea o bug maestro, para que el reporte sea `docs/review/code_reviews/<ID>-code-review.md`.
7. **Sin fingir.** Si no puedes completar el paso, explica el bloqueo en tu salida y no cambies estados: el bucle lo detectará.

| Paso | Sigue | Ajuste | Hecho cuando |
|---|---|---|---|
| `ciclo-requisitos` | `/ciclo-requisitos` sobre `<docs>/requirements.md` | sin ronda de preguntas de la fase 0 | existe `req_analysis.md` |
| `platform-plan` | `/platform-plan` | — | existe `platform_plan.md` |
| `revisar-plataforma` | Hades `/review-design` sobre `platform_plan.md`, frente a los requisitos; corrige lo que no deje al humano y repite; lo que deje al humano, `RECHAZADO` con su pregunta | — | `platform_review.md` con primera línea `**Veredicto:** APROBADO` o `RECHAZADO` |
| `work-plan` | `/work-plan` | — | `work_plan.md` y tareas con versión y `depende_de` en el backlog |
| `calcular-dependencias` | Lee `work_plan.md` y todas las tareas maestras abiertas y declara en cada una `depende_de` (ver `/task-add`), una sola vez para todo el backlog | sin ciclos ni dependencias a versiones posteriores; las tareas `blocked` solo por depender de otra (bloqueo en cascada anterior) vuelven a `planned` y pierden esa nota de bloqueo | todas las maestras abiertas con versión tienen `depende_de` |
| `start-version` | `/start-version` con la versión indicada | — | existe `release/vX.Y` |
| `revisar-deuda` | Repasa la deuda registrada frente al código actual y a las tareas de vX.Y | **incluir** la que afecta a lo que toca esta versión (mismos módulos o una tarea citada en `origen`): `version: vX.Y.0`, `status: planned` y peso que la ordena antes de las tareas a las que afecta; **cancelar** con motivo la ya resuelta o irrelevante; **dejar** el resto como mejora futura. La deuda no relacionada con la versión no se incluye: la decide el humano | existe `vX.Y-deuda.md` con las tres listas |
| `task-dev` | `/task-dev <ID>` en modo orquestado | — | tarea `completed` y commit |
| `bug-fix` | `/bug-fix <ID>` en modo orquestado | — | bug `completed` y commit |
| `revisar-tarea` | Hades `/review-code` sobre los commits del ID; corrige y repite (regla 5) | sin cambios de código: reporte `N/A` | existe el reporte, o `blocked` |
| `especificar` | Eres el especificador, no el desarrollador ni Hades: resuelve los hallazgos que Hades dejó al especificador (en la revisión de versión) ajustando el requisito, los escenarios o la `DEC` que fallan | si lo que falta es un recurso externo, `pendiente_de: humano` con la pregunta concreta (qué hace falta y por qué) | el ID en `planned` sin `pendiente_de`, o con `pendiente_de: humano` |
| `revisar-version` | Hades `/review-code` sobre `git diff main...release/vX.Y`, solo lo transversal: duplicados entre tareas, patrones incoherentes y capas mezcladas. Si el plan de plataforma cambió en la versión, además Hades `/review-design` sobre esas `DEC` | 🔴/🟠 → `/bug-add` en vX.Y; 🟡/🔵 → su destino (`registrar` → deuda registrada) | existe `vX.Y-arquitectura.md` |
| `revisar-producto` | `/revisar-producto` sobre vX.Y | defectos frente a lo acordado → `/bug-add` en vX.Y | existe `vX.Y-producto.md` con `**Decisión:** PENDIENTE` |
| `aplicar-producto` | `/revisar-producto`, paso `aplicar-producto`: crea las tareas de la tabla según el destino que dejó el usuario | idempotente por fila (columna Tarea) | `**Decisión:** APLICADA`, o `PENDIENTE` con `⚠` si alguna fila necesita al usuario |

`/release` no es un paso del bucle: lo ejecuta el humano tras la revisión.

## 👤 Revisión de versión

Cuando el bucle para con «Versión vX.Y terminada»:
0. **Suite en rojo** (si paró por eso): corrige iterando solo sobre las pruebas que fallan y relanza; el bucle repasa la suite una vez.
1. Lee `docs/review/versions/vX.Y-revision.md` (y `vX.Y-arquitectura.md` y `vX.Y-deuda.md`) y prueba el producto siguiendo sus pasos de validación.
   **Propuestas de producto** (si hay `vX.Y-producto.md`): la tabla trae el destino recomendado de cada propuesta. Cambia lo que no te convenza (versión, `backlog` o `rechazar`), edita o añade filas, marca `**Decisión:** APLICAR` y relanza; el bucle crea las tareas sin preguntar. Puedes hacerlo editando el archivo o diciéndoselo a `/orquestar` en la conversación. Mientras siga `PENDIENTE`, el bucle no abre la siguiente versión.
2. **Defectos:** regístralos con `/bug-add` en la rama `release/vX.Y` y relanza; el bucle los corrige con `/bug-fix`.
3. **Bloqueadas** (`pendiente_de: humano`): responde a su pregunta en `vX.Y-revision.md` o consigue el recurso y pon `status: planned`; o muévela de versión o cancélala.
4. **Mejoras:** para meter en una versión deuda que el bucle no incluyó, ponle esa versión.
5. **Conforme:** ejecuta `/release` y relanza; el bucle abre la siguiente versión.

Formato de cada entrada (una por tarea o bug, la añade `/task-dev` o `/bug-fix`):

```markdown
## T-PRJ-XXXX · Título
- **Especificación**: escenarios añadidos (archivo) y resumen
- **Diseño**: decisiones relevantes (enlace a docs/design/…)
- **Hades**: veredictos y bugs de deuda registrados
- **Bloqueos**: a quién los envió Hades, por qué y cómo se resolvieron, si los hubo
- **Validación funcional**: pasos concretos para comprobarlo (comando, URL, datos)
- **Decisiones sin preguntar**: opciones tomadas por defecto
```
