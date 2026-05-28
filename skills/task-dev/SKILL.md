---
name: task-dev
description: Ciclo de desarrollo completo para una tarea del backlog (BDD -> TDD -> Dev -> QA -> Doc)
---

# Skill: Desarrollo de Tarea (/task-dev)

Playbook de orquestación para el ciclo completo de desarrollo de una tarea. El hilo principal actúa como coordinador, delegando cada fase al agente especializado indicado.

## Modo de Trabajo

El flujo es **único y se ejecuta a nivel de tarea padre** (`T-[PRJ]-XXXX`), que representa el objetivo atómico con valor para el usuario. Una tarea padre puede afectar a varios componentes; cada uno tiene su tarea hija (`T-[PRJ]-[COMP]-XXXX`) en su backlog, pero **las hijas son unidades de contabilidad, no flujos separados**: Cronos las gestiona por debajo (estado, esfuerzo, cierre) mientras el ciclo de trabajo permanece unificado en la padre.

- **Foco principal (Product Owner)**: se trabaja siempre sobre la tarea padre. Las especificaciones y validaciones se presentan consolidadas, abarcando todos los componentes afectados de una vez.
- **Atajo de desarrollador (Component Mode)**: entrada `T-[PRJ]-[COMP]-XXXX`. Permite trabajar una tarea hija suelta sin el contexto de la padre. Sigue el mismo flujo de orquestación, acotado a un componente.

> La implementación de varios componentes puede realizarse en paralelo (componentes independientes a nivel de código) o en secuencia (cuando hay dependencias). Esto es un detalle de ejecución interno, invisible para el Product Owner.

## Gestión del Flujo (checklist externo)

El estado del flujo NO debe vivir solo en la memoria de contexto del coordinador (se diluye en flujos largos). Mantenerlo como **checklist externo y explícito**:

1. **Antes de empezar**, crear una lista de tareas (una por cada fase del flujo de orquestación) usando las herramientas de gestión de tareas del runtime.
2. **Entre cada fase**, consultar la lista para determinar la siguiente y marcar como completada la que acaba de terminar.
3. **Los HITL son ítems del checklist como cualquier otro.** Si el usuario difiere un HITL para más tarde, su ítem permanece **abierto** hasta que se realice — nunca se da por hecho ni se omite por descuido.
4. **El flujo no se considera completo** mientras queden ítems abiertos, incluidos los HITL diferidos.

Esto re-ancla la atención en cada paso y protege contra el olvido de fases en mitad del proceso.

## Flujo de Orquestación

### 1. Inicialización → Agente: `cronos`
- Validar rama de trabajo:
  - La rama activa debe seguir el patrón `release/vX.Y` o `hotfix/vX.Y.Z`.
  - Si la rama es `main`, **abortar** con mensaje: "No se puede desarrollar directamente en main. Usa `/start-version` para crear un bloque funcional o crea una rama hotfix."
- Cargar metadatos de la tarea padre y de todas sus tareas hijas (componentes afectados).
- Verificar coherencia de versión entre la tarea y `task_config.yaml`.
- Cambiar `status` a `in_progress` en la padre y en las hijas.
- Confirmar `estimated_effort` y establecer `remaining_effort`.

### 2. Especificación → Agente: `atenea`
Atenea usa las skills `/generate-bdd` y `/req-analysis`:
- Aclarar con el usuario cualquier ambigüedad en los requisitos.
- Definir escenarios BDD a nivel feature (`.feature`) para todos los componentes afectados, integrándolos en `.feature` de sistema existentes.
- Definir criterios de evaluación (evals).
- **Presentar la especificación de forma consolidada**: un resumen único con todas las BDD y evals de todos los componentes, listo para revisión ágil (sin obligar a abrir cada archivo por separado).

### 3. Revisión de Especificación → Agente: `hades`
Hades opera en contexto aislado usando la skill `/review-spec`:
- Evaluar claridad, completitud y testeabilidad de las BDD y evals. Puntuación mínima 8/10.
- **Bucle de auto-corrección (máx. 3 iteraciones)**: si Hades rechaza → `atenea` corrige → Hades re-evalúa.

### 4. HITL — Validación de especificación (consolidada)
Solicitar confirmación del usuario sobre la especificación completa de la tarea padre. Propósito: verificar que los escenarios BDD y evals de todos los componentes capturan correctamente el requisito antes de construir la solución.

### 5. Fase Roja → Agente: `artemisa`
Para cada componente afectado (en paralelo si son independientes, en secuencia si hay dependencias):
- Implementar step definitions y fixtures de los escenarios BDD definidos por Atenea.
- Implementar las evaluaciones (evals) definidas por Atenea.
- Crear tests unitarios en `<componente>/tests/unit/` que cubran el cambio.
- Confirmar que los tests fallan inicialmente (Estado Rojo).

### 6. Revisión de Tests → Agente: `hades`
Hades opera en contexto aislado usando la skill `/review-test`:
- Auditar calidad de la suite (aislamiento, cobertura, mocking) y confirmar que los tests fallan correctamente. Puntuación mínima 8/10.
- **Bucle de auto-corrección (máx. 3 iteraciones)**: si Hades rechaza → `artemisa` corrige los tests → Hades re-evalúa.

### 7. Fase Verde → Agente: `artemisa`
- Implementar la lógica de negocio siguiendo estándares (docstrings obligatorios, no comentarios inline).
- Refactorizar hasta que todos los tests pasen (Estado Verde).

### 8. HITL — Validación funcional
Solicitar confirmación del usuario. Propósito: el usuario valida que el resultado funciona correctamente en conjunto (integración visual, UX, efectos secundarios) — lo que los tests BDD/unitarios no cubren.

### 9. Revisión de Código → Agente: `hades`
Hades opera en contexto aislado usando la skill `/review-code`:
- Evaluar código según las 8 áreas de `/review-code`. Puntuación mínima 8/10.
- **Bucle de auto-corrección (máx. 3 iteraciones)**: si Hades rechaza → `artemisa` corrige el código → Hades re-evalúa.
- Si algún bucle no converge en 3 iteraciones → presentar reporte al usuario y solicitar decisión.

### 10. Documentación y Commit → Agente: `clio`
Clío usa las skills `/manage-docs` y `/commit`:
- Generar o actualizar los documentos definidos en `docs_config.yaml`.
- Generar commit semántico estandarizado.

### 11. Cierre → Agente: `cronos`
- Actualizar `actual_effort` y `remaining_effort` en la padre y en las hijas.
- Marcar `status: completed` en todas las hijas completadas.
- Si todas las hijas están completadas, cerrar la tarea padre (`completed`) y verificar coherencia de `version`.
