# Orquestación Adevv

Vista general del flujo. Las reglas viven en las skills; si algo no coincide, mandan ellas.

## 0. Arranque desde un arnés

La conversación se limita a los requisitos. Después, `/orquestar` lanza el bucle desatendido y vuelve; el bucle deduce la fase del disco y continúa desde donde toque.

```mermaid
flowchart LR
  yo(["Tú, en el arnés"]) --> cr["/ciclo-requisitos interactivo<br/>ronda de preguntas + juez"]
  cr --> lz["/orquestar lanzar<br/>comprueba requisitos, árbol limpio y suite"]
  lz --> fondo["orquestar.py --fondo<br/>desacoplado, salida en orquestar.log"]
  fondo --> bucle["bucle general (sección 1)"]
  yo -. "/orquestar estado" .-> est["fase, bucle en marcha,<br/>pasos y coste acumulado"]
  yo -. "/orquestar parar" .-> par["para tras el paso en curso<br/>relanzar sigue donde iba"]
  est -.-> bucle
  par -.-> bucle

  classDef paso fill:#e4efe9,stroke:#2f6f5e,color:#1d2421
  classDef humano fill:#f7e3c4,stroke:#a8711c,color:#1d2421
  classDef pnuevo fill:#e4efe9,stroke:#b3541e,stroke-width:2px,stroke-dasharray:6 4,color:#1d2421
  class yo,cr humano
  class bucle paso
  class lz,fondo,est,par pnuevo
```

## 1. Bucle general (`orquestar.py`)

`--harness` elige el arnés principal de cada paso. Si ese principal agota cuota o falla, las reservas explícitas usan su propio arnés, modelo y esfuerzo en el orden configurado. Un cambio de arnés inicia sesión nueva; una reserva del mismo arnés puede reanudar la sesión tras agotar cuota. Las métricas reflejan el perfil ejecutado. Si el arnés forzado difiere del principal configurado, no hereda su modelo ni esfuerzo incompatibles; las reservas heredan los campos no redefinidos del principal efectivo. `--cmd` conserva su plantilla explícita.

Cada caja es una ejecución del arnés. Los análisis sin progreso prueban niveles superiores, escalada y reservas con `--reintentos` intentos por perfil (2 por defecto), independientemente por paso y argumento. Al agotarlos, `especificar` y `revisar-tarea` bloquean solo el ID y continúan con las independientes; los análisis globales paran con diagnóstico de perfiles e intentos. Un `task-dev`/`bug-fix` sin progreso conserva su promoción y bloqueo local. Los pasos restantes paran tras agotar `--reintentos`. También se para por suite roja que agota su recuperación de cierre, fallo persistente de todos los perfiles del arnés, `--parar` o `--max-pasos`. Las tareas con alguna `depende_de` sin completar esperan. La recarga conserva perfiles y contadores parciales de análisis. Una tarea o bug puede fijar su propio `perfil` (arnés, modelo y esfuerzo, único o por rol) por encima del perfil por dificultad: si no está disponible se usan las reservas con un aviso, con `estricto: true` se espera la cuota o se bloquea la tarea, y un perfil inválido para el bucle con el error del backlog. Pasos, roles, esperas y verificaciones quedan en `orquestar_metricas.jsonl`.

El bucle observa el entregable del paso. En desarrollo cuentan los cambios de producto, incluso sin commit, el estado operativo de la ficha y los dictámenes formales del ID. En análisis cuenta el artefacto del paso. Confirmar un commit vacío o reformular el diagnóstico en la ficha y el resumen de versión deja intacto el presupuesto de intentos.

Si Hades agota los perfiles autorizados sin emitir dictamen, cada intento sin avance cuenta para ese paso e ID. Al alcanzar `--reintentos`, el bucle identifica la revisión pendiente y se detiene con el trabajo en su sitio. Una reserva puede aportar el dictamen en la misma invocación. Si queda cuota pendiente, el bucle aplica su espera. La recarga automática conserva los contadores técnicos. Un arranque manual concede otra tanda y conserva el árbol Git, las preguntas y las métricas. Incorporar una respuesta renueva los intentos técnicos de su ID.

Ante un error del arnés, desarrollo continúa al paso siguiente si la ficha está completada, hay un commit nuevo, el árbol está limpio y la aprobación canónica cubre el producto confirmado. El trabajo parcial se conserva durante la recuperación del arnés.

Hades incluye la línea `Producto revisado: <huella>` justo después del veredicto de código. La huella cubre los mandatos rastreados. El archivo temporal que la CLI retira al terminar queda fuera de la huella y sigue contando para la evidencia exacta de las pruebas.

Si una nota desplaza o elimina la huella, Git conserva la del informe que la emitió, incluso cuando el mismo commit cambia el producto. Restaurar una aprobación revocada mantiene la revisión pendiente aunque cambie la sangría, se quite la etiqueta de lenguaje de un ejemplo o se añadan notas de seguimiento. Cuando Hades reevalúa el mismo producto y conserva el texto anterior, identifica el último rechazo en la cabecera con `Rechazo reevaluado: <SHA completo del commit>`, justo después de `Producto revisado`. Una vez confirmada esa reevaluación en Git, una nota puede desplazar la referencia. Un rechazo posterior vuelve a dejar pendiente la revisión. Una aprobación de un producto distinto se contrasta con su propia huella.

Al confirmar cambios durante un paso de desarrollo, el bucle registra el último commit del intento para ese ID en las métricas. El selector y el preflight recuperan ese objetivo al relanzar, aunque el paso haya fallado después de marcar la ficha como completada. Un paso de otro ID conserva la aprobación anterior. Para informes históricos se consulta el commit que emitió el veredicto. Confirmar una copia de la aprobación histórica de A después de un rechazo de B mantiene pendiente la revisión de B. Una aprobación histórica con una comprobación propia de B permite continuar. Las citas y las notas de seguimiento conservan la acreditación original. Si la aprobación ha caducado, el selector pide `revisar-tarea`. Una reevaluación vigente cuenta como avance incluso en el último intento.

```mermaid
flowchart TD
  idea(["requirements.md (idea)"]) --> req["ciclo-requisitos"]
  req --> q1{"¿REQUIERE_ACLARACION?"}
  q1 -- sí --> s1["PARAR: preguntas"]
  q1 -- no --> pp["platform-plan"]
  pp --> rp["revisar-plataforma<br/>Hades · review-design (arquitectura)"]
  rp --> q2{"¿RECHAZADO?"}
  q2 -- sí --> s2["PARAR: plataforma"]
  q2 -- no --> wp["work-plan<br/>versiones + backlog + .feature"]
  wp --> sv["start-version vX.Y"]
  sv --> qd{"¿deuda registrada?"}
  qd -- sí --> rd["revisar-deuda<br/>incluye la que toca vX.Y, cancela la resuelta,<br/>deja el resto como mejora"]
  rd --> sel
  qd -- no --> sel{"¿elegibles en vX.Y?<br/>(dependencias completadas)"}
  sel -- sí --> td["task-dev / bug-fix del ID<br/>(en curso, el que más desbloquea, menor weight)"]
  td --> rt["revisar-tarea<br/>solo si falta el reporte de review-code"]
  rt --> sel
  td -. "Hades: para el especificador" .-> ab["especificar<br/>ajusta requisito, escenarios o DEC"]
  ab --> sel
  td -. "Hades: para el humano · espera a la revisión de versión" .-> hum
  ab -. "falta un recurso externo" .-> hum
  sel -- no --> rv["revisar-version<br/>Hades · review-code: duplicados y coherencia entre tareas<br/>Hades · review-design: solo si cambió el plan de plataforma"]
  rv --> q3{"¿🔴/🟠?"}
  q3 -- sí --> ba["bug-add en vX.Y"]
  ba --> sel
  q3 -- no --> qp{"¿revisión de producto<br/>activa para vX.Y?"}
  qp -- sí --> rpr["revisar-producto<br/>revisores independientes usan el producto<br/>defectos → bug-add · propuestas → tabla con destino"]
  rpr --> hum
  qp -- no --> hum["PARAR: revisión humana de vX.Y<br/>vX.Y-revision.md + vX.Y-arquitectura.md<br/>(+ tabla de vX.Y-producto.md)"]
  hum -- "ajusta destinos y marca APLICAR" --> apl["aplicar-producto<br/>task-add desatendido por fila<br/>rechazadas → NO-xx"]
  apl --> hum
  hum -- defectos --> ba2["/bug-add (humano)"]
  ba2 --> sel
  hum -- bloqueadas --> desb["desbloquear / mover / cancelar"]
  desb --> sel
  hum -- conforme --> rel["/release (humano)"]
  rel --> q4{"¿quedan versiones?"}
  q4 -- sí --> sv
  q4 -- no --> fin(["FIN<br/>con el número de mejoras pendientes"])

  classDef paso fill:#e4efe9,stroke:#2f6f5e,color:#1d2421
  classDef hades fill:#e6e0f3,stroke:#5b4a8a,color:#1d2421
  classDef humano fill:#f7e3c4,stroke:#a8711c,color:#1d2421
  classDef stop fill:#f3d6d3,stroke:#a33a2f,color:#1d2421
  classDef nuevo fill:#e6e0f3,stroke:#b3541e,stroke-width:2px,stroke-dasharray:6 4,color:#1d2421
  classDef pnuevo fill:#e4efe9,stroke:#b3541e,stroke-width:2px,stroke-dasharray:6 4,color:#1d2421
  class req,pp,wp,sv,td,ba paso
  class rp hades
  class rt,rv nuevo
  class rd,qd,ab,rpr,apl,qp pnuevo
  class hum,ba2,desb,rel humano
  class s1,s2 stop
```

## 2. Dentro de una tarea (`task-dev` / `bug-fix` en modo orquestado)

Sin pausas para el humano: lo que se habría validado va a `vX.Y-revision.md`. Cada revisión se repite mientras Hades deje algo al desarrollador; lo que deja al especificador o al humano bloquea la tarea y el bucle sigue con el resto. Una desviación de la arquitectura se registra como `DEC` en el plan de plataforma; la revisa `review-design` en la revisión de versión.

```mermaid
flowchart TD
  ini["Init + triaje delta-first<br/>in_progress, subfases EXEC/SKIP<br/>pruebas a verificar"] --> bdd["A · generate-bdd<br/>escenarios del delta + evals"]
  bdd --> rs["Hades · review-spec<br/>solo lo añadido o modificado<br/>respecto a los escenarios de origen"]
  rs --> dis["B · /design<br/>mapa de impacto obligatorio si cambia un contrato"]
  dis --> red["C · Red<br/>tests que fallan por la funcionalidad"]
  red --> pre1["lint + tipado limpios en tests<br/>salida del rojo registrada"]
  pre1 --> rtst["Hades · review-test<br/>cobertura, aserciones, rojo correcto, estabilidad"]
  rtst --> green["Green<br/>implementación mínima + verificación del triaje"]
  green --> pre2["lint + tipado limpios en todo el delta"]
  pre2 --> rc["Hades · review-code<br/>corrección, seguridad, calidad<br/>conformidad con el diseño de la tarea y la arquitectura"]
  rc --> q{"¿se desvía de la arquitectura?"}
  q -- "sin DEC" --> rojo["🔴 rechazo"]
  rojo --> green
  q -- "con DEC o no se desvía" --> docs["E · manage-docs"]
  docs --> deu["F · deuda según Hades<br/>resolver · registrar como bug · descartar"]
  deu --> cie["cierre + entrada en vX.Y-revision.md<br/>y commit"]
  rs -. "🔴/🟠 para especificador o humano" .-> blk["wip/ID + status: blocked<br/>pendiente_de: especificador o humano"]
  rtst -.-> blk
  rc -.-> blk

  classDef paso fill:#e4efe9,stroke:#2f6f5e,color:#1d2421
  classDef hades fill:#e6e0f3,stroke:#5b4a8a,color:#1d2421
  classDef stop fill:#f3d6d3,stroke:#a33a2f,color:#1d2421
  classDef nuevo fill:#e4efe9,stroke:#b3541e,stroke-width:2px,stroke-dasharray:6 4,color:#1d2421
  classDef hnuevo fill:#e6e0f3,stroke:#b3541e,stroke-width:2px,stroke-dasharray:6 4,color:#1d2421
  class ini,bdd,red,green,docs,cie paso
  class dis,pre1,pre2,deu nuevo
  class rs,rtst,rc hnuevo
  class rojo,blk stop
```

## 3. Quién revisa qué

| Revisión | Cuándo | Mira | Nunca mira |
|---|---|---|---|
| `review-spec` | Cada tarea, antes del diseño | Solo lo que la tarea añade o modifica en escenarios y evals; trazabilidad que existe y corresponde | Diseño ni código |
| `review-design` | `revisar-plataforma` y `revisar-version` | Plan de plataforma y sus `DEC` | Código ni diseños por tarea |
| `review-test` | Cada tarea, tras el rojo | Cobertura, aserciones, rojo correcto, estabilidad y preparación de las pruebas | Código de producción |
| `review-code` | Cada tarea, tras el verde, y transversal en `revisar-version` | Corrección, seguridad, calidad, eficiencia, docs y conformidad con el diseño y la arquitectura (incluye build, CI y configuración) | Pruebas |
| `revisar-producto` | Al cerrar la versión, si está activa (`producto` en `orchestration.json`), o a mano | El producto en uso: utilidad, contenido, diseño, usabilidad y accesibilidad frente a recorridos y criterios de éxito | Código, arquitectura ni pruebas |

Lo determinista (lint, tipado, rojo de la suite) se ejecuta antes de llamar a Hades. Cada 🟡/🔵 lleva un destino: `resolver` (por defecto), `registrar` (bug de deuda sin versión, peso > 1000, con su origen) o `descartar`. `revisar-deuda`, al abrir cada versión, decide qué deuda entra.


## Recuperación de errores del arnés en pasos

Las marcas con hora real de reinicio conservan su plazo. Las respuestas sin hora y los errores de créditos generan marcas supuestas: el trabajo pendiente sirve de comprobación al relanzar y cada `cuota_reintento_s` segundos (300 por defecto, valor positivo finito en `orchestration.json`). Los errores de créditos avisan una vez por episodio; una respuesta satisfactoria o un reset permite avisar de nuevo si vuelven a faltar créditos.

`adevv orquestar --cuota-reset codex/m1` recupera un modelo; `--cuota-reset codex`, todo el arnés; `--cuota-reset`, todas las marcas. Se añaden eventos de recuperación sin borrar histórico ni tokens. Un bucle esperando cuota continúa en su siguiente comprobación, como máximo 30 segundos, y respeta `--parar`. Las consultas `--estado` y `--agentes` muestran la certeza (real/supuesto) y el origen de las marcas vigentes. El reset es una orden independiente que no arranca el bucle ni el gateway.

`adevv orquestar --reintentos-arnes 3` permite tres reintentos adicionales por perfil ante errores ajenos a cuota, con esperas de 60, 300 y 900 segundos. Para límites mayores se repite la espera de 900 segundos. El límite debe ser entero no negativo; cero pasa a la reserva sin esperar. Al agotarlo se prueba la siguiente reserva en orden y con sesión nueva. No consume pasos ni intentos por falta de progreso. Las esperas respetan `--parar`.

Cada ejecución conserva sus métricas. Solo se detiene por este error cuando se agotan todos los perfiles; consola y aviso incluyen los últimos 2000 caracteres de la salida del último arnés ejecutado. Un paso completado y commiteado no se repite por un retorno erróneo. La cuota mantiene su circuito, incluida su recuperación si otra reserva falla por red. Esta recuperación corresponde a pasos del bucle; no cambia el tratamiento de errores operacionales de los roles ni de la conversación del gateway.

### Acceso deshabilitado durante revisiones

`adevv orquestar --agente hades` prueba las reservas autorizadas y elegibles cuando Claude devuelve `Your organization has disabled Claude subscription access for Claude Code.`. Respeta el orden, las cuotas vigentes y el perfil estricto. Las métricas distinguen el fallo de acceso del dictamen emitido por la reserva; este fallo no inventa cuota. Los errores genéricos de autenticación y red conservan su tratamiento.

Si no puede revisar ningún perfil permitido, el paso conserva su trabajo y la revisión pendiente y termina sin abrir otra pregunta para elegir proveedores. Puede reintentarse al recuperar un perfil. Las respuestas existentes se incorporan entre pasos; un WIP pendiente solo se restaura sobre destino limpio. Si hay trabajo ajeno sin confirmar, el motor espera a que su propietario lo guarde antes de lanzar la tarea. La restauración conserva los bytes del parche, incluidos los saltos de línea en Windows.
