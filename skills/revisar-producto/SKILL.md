---
name: revisar-producto
description: Revisión funcional de una versión construida (utilidad, contenido, diseño, usabilidad y accesibilidad) por revisores independientes que usan el producto. Entrega un informe con una tabla de propuestas y destino recomendado; el usuario la ajusta y la creación de tareas es desatendida. Paso opcional de /orquestar al cerrar versión, o invocación manual.
inputs:
  - version: versión construida (vX.Y)
  - paso: (Lo pasa el bucle) revisar-producto | aplicar-producto
outputs:
  - informe: docs/review/versions/vX.Y-producto.md
---

# Skill: Revisión de producto (/revisar-producto)

**Objetivo:** Saber si lo construido es útil, coherente, atractivo y fácil de usar, no solo si cumple. Las revisiones técnicas y las pruebas no lo miden.

**Cuándo:** Al cerrar una versión, como paso de `/orquestar` si `orchestration.json` tiene `"producto": true` (todas las versiones) o una lista (`["v0.3", "v1.0"]`). También a mano sobre una versión ya construida. Sin esa clave, el bucle no cambia.

**No revisa** código, arquitectura ni pruebas (lo hace Hades), ni repite el ciclo de requisitos.

## Reglas

1. **Producto real.** Se juzga usándolo: los recorridos `R0..Rn` y los criterios de éxito `CE-x` de `requirements.md`, y la «Validación funcional» de `vX.Y-revision.md`. Lo que no se pudo probar se declara.
2. **Evidencia o hipótesis.** Cada hallazgo cita lo observado (pantalla, salida, paso, dato) o se marca `HIPÓTESIS`.
3. **Independencia.** Revisores aislados, con el mismo principio y prompt base que en `/ciclo-requisitos` (§Subagentes aislados): solo reciben rutas y su mandato, ni tus conclusiones ni las de otros revisores. Solo la síntesis lee sus informes. Si el arnés no permite subagentes aislados, dilo en el informe.
4. **Sin cupo ni relleno.** Todas las propuestas con valor concreto; ninguna genérica («mejorar la UX») ni duplicada.
5. **No insistir.** No se repite lo rechazado (`NO-xx` de `requirements.md`), lo que ya está en el backlog ni lo de informes anteriores, salvo evidencia nueva, que se cita.
6. **El usuario decide el alcance.** Nada cambia requisitos ni plan sin su decisión. La excepción son los **defectos** frente a requisitos ya acordados (`RF`/`CA`), que no amplían el alcance: van como bug a la versión.
7. **Proporcional.** No repitas pruebas cubiertas por la evidencia de `orquestar.py --verificar`. El detalle depende del tamaño del producto.

## Paso `revisar-producto`

**1. Preparación.** Lee `requirements.md` (encuadre, recorridos, `CE`, `NO`), `vX.Y-revision.md`, `work_plan.md` (qué traen las versiones siguientes) y el backlog sin versión. Arranca el producto como indique el proyecto (README, `/run`, scripts). Decide si cada revisor lo usa por su cuenta o si conviene capturar antes la evidencia en bruto (capturas o salidas por recorrido, sin valoraciones) en un directorio temporal fuera de git, para que la juzguen y la amplíen.

**2. Revisores, en paralelo.** Dos por defecto, con mandatos adaptados al dominio:
- **Producto:** utilidad frente al objetivo, calidad y veracidad del contenido, coherencia entre funcionalidades, tiempo hasta obtener valor.
- **Experiencia:** diseño visual, usabilidad, fricciones, estados vacíos y de error, accesibilidad (en una CLI o API: ergonomía, mensajes y documentación).

Añade un tercero solo si el dominio lo pide (p. ej. confianza en un producto financiero). Los revisores devuelven: tipo (`FORTALEZA` | `DEFECTO` | `PROPUESTA`), ID afectado (`R`, `RF`, `CE`), evidencia o `HIPÓTESIS`, problema u oportunidad, propuesta, valor 1-5 y esfuerzo S/M/L.

**3. Síntesis.** Une y elimina duplicados (regla 5). Registra los defectos con `/bug-add` en vX.Y. Asigna a cada propuesta un destino recomendado:
- **Siguiente versión:** mejora que conviene ya (alto valor, poco esfuerzo o que desbloquea otras).
- **Versión planificada posterior:** encaja con lo que esa versión ya trae o depende de ello (indica por qué).
- **backlog:** útil pero aún sin justificar trabajo comprometido.

Si los revisores discrepan en algo relevante, recoge ambas posturas y tu recomendación; no lances un juez: es una decisión de criterio y corresponde al usuario.

**4. Informe** en `docs/review/versions/vX.Y-producto.md`. Commit `docs(review): revisión de producto vX.Y`.

```markdown
**Decisión:** PENDIENTE

# Revisión de producto vX.Y

## Síntesis
Valoración general y las 3-5 recomendaciones principales.

## Decisiones
Cambia el Destino que quieras (una versión, `backlog` o `rechazar`), edita el texto o añade filas,
y cambia la primera línea a `**Decisión:** APLICAR`. Al relanzar /orquestar se crean las tareas.

| ID | Propuesta | Destino | Prioridad | Tarea |
|---|---|---|---|---|
| P-01 | Guardar los filtros entre sesiones | v0.3 | alta | |

## Fortalezas a conservar
## Defectos registrados (bugs de vX.Y)
## Desacuerdos entre revisores
## Detalle de propuestas
### P-01 · Título
- **Problema:** … **Evidencia:** … (o **Hipótesis:** …)
- **Beneficio:** … **Esfuerzo:** S/M/L (confianza) **Riesgos:** solo si los hay
- **Destino:** por qué ahí (alcance y dependencias)

## No probado
```

## Paso `aplicar-producto`

Con `**Decisión:** APLICAR`, recorre la tabla. Las filas con la columna Tarea rellena ya están hechas; con el resto:
- **Destino con versión:** `/task-add` con esa versión (`status: planned`), criterios de aceptación observables y `origen: P-nn (vX.Y-producto.md)`. Una propuesta que agrupe varias capacidades se convierte en varias tareas.
- **backlog:** `/task-add` sin versión, con el mismo `origen`.
- **rechazar:** `NO-xx` en `requirements.md §Encuadre`, con un motivo breve.

El texto del usuario manda sobre el del informe, y sus filas nuevas se tratan igual. Antes de crear, comprueba duplicados con el backlog y contradicciones con los requisitos. Si la tarea cambia un requisito aceptado, lo dice en sus criterios. Si una contradicción no se puede resolver sin el usuario, no crees la tarea: anota `⚠ motivo` en la columna Tarea y deja la decisión en `PENDIENTE`.

Escribe el ID en la columna Tarea en cuanto creas cada tarea, para poder reanudar sin duplicar. Al terminar, cambia la primera línea a `**Decisión:** APLICADA` y haz commit con `docs(plan): aplicar-producto vX.Y`. Las dependencias de las tareas nuevas las calcula el bucle.

## Uso manual

`/revisar-producto vX.Y` sobre una versión construida: ejecuta el paso `revisar-producto`, presenta en la conversación la síntesis y la tabla, recoge los cambios del usuario («mueve P-03 al backlog, rechaza P-05»), los escribe en la tabla y, cuando el usuario lo confirme, ejecuta `aplicar-producto`.
