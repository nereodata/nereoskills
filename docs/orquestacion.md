# Orquestación NereoSkills

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

Cada caja es una ejecución del arnés con contexto limpio. Paradas en cualquier punto: paso sin progreso tras 2 intentos, tarea cerrada con la suite en rojo (`--test`), fallo del arnés, `--parar` y `--max-pasos`. Cada paso deja una línea en `orquestar_metricas.jsonl`.

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
  qd -- no --> sel{"¿pendientes en vX.Y?"}
  sel -- sí --> td["task-dev / bug-fix del ID<br/>(en curso o menor weight)"]
  td --> rt["revisar-tarea<br/>solo si falta el reporte de review-code"]
  rt --> sel
  sel -- no --> rv["revisar-version<br/>Hades · review-code: duplicados y coherencia entre tareas<br/>Hades · review-design: solo si cambió el plan de plataforma"]
  rv --> q3{"¿🔴/🟠?"}
  q3 -- sí --> ba["bug-add en vX.Y"]
  ba --> sel
  q3 -- no --> hum["PARAR: revisión humana de vX.Y<br/>vX.Y-revision.md + vX.Y-arquitectura.md"]
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
  class rd,qd pnuevo
  class hum,ba2,desb,rel humano
  class s1,s2 stop
```

## 2. Dentro de una tarea (`task-dev` / `bug-fix` en modo orquestado)

Sin pausas para el humano: lo que se habría validado va a `vX.Y-revision.md`. Cada revisión admite hasta 3 iteraciones. Una desviación de la arquitectura se registra como `DEC` en el plan de plataforma; la revisa `review-design` en la revisión de versión.

```mermaid
flowchart TD
  ini["Init + triaje delta-first<br/>in_progress, subfases EXEC/SKIP"] --> bdd["A · generate-bdd<br/>escenarios del delta + evals"]
  bdd --> rs["Hades · review-spec<br/>solo lo añadido o modificado<br/>respecto a los escenarios de origen"]
  rs --> dis["B · /design<br/>mapa de impacto obligatorio si cambia un contrato"]
  dis --> red["C · Red<br/>tests que fallan por la funcionalidad"]
  red --> pre1["lint + tipado limpios en tests<br/>salida del rojo registrada"]
  pre1 --> rtst["Hades · review-test<br/>cobertura, aserciones, rojo correcto, estabilidad"]
  rtst --> green["Green<br/>implementación mínima + suite completa"]
  green --> pre2["lint + tipado limpios en todo el delta"]
  pre2 --> rc["Hades · review-code<br/>corrección, seguridad, calidad<br/>conformidad con el diseño de la tarea y la arquitectura"]
  rc --> q{"¿se desvía de la arquitectura?"}
  q -- "sin DEC" --> rojo["🔴 rechazo"]
  rojo --> green
  q -- "con DEC o no se desvía" --> docs["E · manage-docs"]
  docs --> deu["F · deuda según Hades<br/>resolver · registrar como bug · descartar"]
  deu --> cie["cierre + entrada en vX.Y-revision.md<br/>y commit"]
  rs -. "3 rechazos con 🔴/🟠" .-> blk["wip/ID + status: blocked"]
  rtst -. "3 rechazos con 🔴/🟠" .-> blk
  rc -. "3 rechazos con 🔴/🟠" .-> blk

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

Lo determinista (lint, tipado, rojo de la suite) se ejecuta antes de llamar a Hades. Cada 🟡/🔵 lleva un destino: `resolver` (por defecto), `registrar` (bug de deuda sin versión, peso > 1000, con su origen) o `descartar`. `revisar-deuda`, al abrir cada versión, decide qué deuda entra.
