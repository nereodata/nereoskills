---
name: bug-fix
description: Ciclo completo para la resolución de anomalías (bugs) detectadas.
---

# Skill: Resolución de Anomalías (/bug-fix)

Playbook de orquestación para la resolución de bugs. El hilo principal actúa como coordinador, delegando cada fase al agente especializado indicado.

## Modo de Trabajo

El flujo es **único y se ejecuta a nivel de bug padre** (`B-[PRJ]-XXXX`), que representa la anomalía con impacto para el usuario. Un bug padre puede afectar a varios componentes; cada uno tiene su bug hijo (`B-[PRJ]-[COMP]-XXXX`) en su backlog, pero **los hijos son unidades de contabilidad, no flujos separados**: Cronos los gestiona por debajo mientras el ciclo de trabajo permanece unificado en el padre.

- **Foco principal (Product Owner)**: se trabaja siempre sobre el bug padre. Las especificaciones de reproducción y validaciones se presentan consolidadas, abarcando todos los componentes afectados.
- **Atajo de desarrollador (Component Mode)**: entrada `B-[PRJ]-[COMP]-XXXX`. Permite corregir un componente suelto sin el contexto del padre.

> La corrección de varios componentes puede realizarse en paralelo (independientes) o en secuencia (con dependencias). Es un detalle de ejecución interno, invisible para el Product Owner.

> **Alcance condicional**: el flujo y las revisiones son idénticos a los de `/task-dev` — misma lógica, mismas skills de revisión. La diferencia es que en un bug **no todas las fases producen cambios**. Por eso el flujo arranca con un **paso de triaje** (fase 2) en el que el coordinador decide qué fases entran en juego antes de gastar spawns. Cada fase (y su revisión asociada) se ejecuta solo si el triaje la incluye.

## Gestión del Flujo (checklist externo)

El estado del flujo NO debe vivir solo en la memoria de contexto del coordinador (se diluye en flujos largos). Mantenerlo como **checklist externo y explícito**:

1. **Tras el triaje (fase 2)**, crear una lista de tareas con **solo las fases que el triaje ha incluido**, usando las herramientas de gestión de tareas del runtime.
2. **Entre cada fase**, consultar la lista para determinar la siguiente y marcar como completada la que acaba de terminar.
3. **Los HITL son ítems del checklist como cualquier otro.** Si el usuario difiere un HITL para más tarde, su ítem permanece **abierto** hasta que se realice — nunca se da por hecho ni se omite por descuido.
4. **El flujo no se considera completo** mientras queden ítems abiertos, incluidos los HITL diferidos.

Esto re-ancla la atención en cada paso y protege contra el olvido de fases en mitad del proceso.

## Flujo de Orquestación

### 0. Clasificación de Urgencia y Rama de Trabajo
Preguntar al usuario: **"¿Este bug es urgente y necesita llegar a producción inmediatamente (hotfix), o puede resolverse dentro del bloque funcional actual (release)?"**
- **Si hotfix**:
  - Identificar la versión de producción afectada (último tag en `main`).
  - Calcular la versión patch: si el último tag es `vX.Y.Z`, la rama será `hotfix/vX.Y.(Z+1)`.
  - Crear la rama desde el tag correspondiente.
  - Actualizar la versión en los manifiestos al patch correspondiente.
  - Commit inicial: `chore(hotfix): start hotfix vX.Y.Z`
- **Si release**:
  - Verificar que la rama activa es `release/vX.Y`.
  - Si no lo es, advertir al usuario y sugerir cambiar a la rama release activa.
- En ambos casos, actualizar el campo `version` del bug con la versión de la rama de trabajo.

### 1. Inicialización → Agente: `cronos`
- Cargar metadatos del bug padre y de todos sus hijos (componentes afectados).
- Cambiar `status` a `in_progress` en el padre y en los hijos.
- Establecer `actual_effort` y actualizar `remaining_effort`.

### 2. Triaje de Alcance → Coordinador (hilo principal)
Antes de lanzar ningún agente, el coordinador analiza el bug y decide **qué fases son necesarias**. Esta decisión la toma el coordinador, no los agentes, porque solo él tiene el panorama completo. El objetivo es no gastar spawns en fases que no producen cambios.

Analizar y clasificar:
- **¿Necesita especificación nueva?** ¿El fallo está ya cubierto por un escenario BDD existente (solo falla la implementación) o hace falta un escenario de reproducción nuevo?
- **¿Qué artefactos cambian?** Código, tests, documentación, o una combinación.
- **¿Qué componentes toca?**

Producir un **plan de fases** explícito. Ejemplos:
- Typo en documentación → solo fase 10 (Clío). Se omiten Atenea, Artemisa y Hades.
- Fallo cubierto por BDD existente → se omiten especificación (fase 3) y su review (fase 4); se ejecutan fase roja, fix, review-test, review-code, docs y cierre.
- Fallo que requiere reproducción nueva → flujo completo.

Las fases siguientes se ejecutan **solo si el plan de triaje las incluye**. Si una fase se omite, su revisión asociada también.

### 3. Especificación de Reproducción → Agente: `atenea`
Atenea usa las skills `/generate-bdd` y `/req-analysis`:
- Aclarar con el usuario cualquier dato que falte para reproducir el fallo.
- Definir escenarios BDD que capturen el fallo a nivel feature, integrándolos en `.feature` de sistema existentes. No crear archivos `.feature` nominales al bug o ID de tarea.
- Definir criterios de evaluación (evals) para verificar que el fallo se ha resuelto.
- **Presentar la especificación de forma consolidada**: un resumen único con todas las BDD y evals de todos los componentes, listo para revisión ágil.

### 4. Revisión de Especificación → Agente: `hades`
Hades opera en contexto aislado usando la skill `/review-spec`:
- Evaluar claridad, completitud y testeabilidad de las BDD y evals de reproducción. Puntuación mínima 8/10.
- **Bucle de auto-corrección (máx. 3 iteraciones)**: si Hades rechaza → `atenea` corrige → Hades re-evalúa.

### 5. HITL — Validación de reproducción (consolidada)
Solicitar confirmación del usuario sobre la especificación completa del bug padre. Propósito: verificar que los escenarios BDD y evals capturan correctamente el fallo antes de implementar la corrección.

### 6. Fase Roja → Agente: `artemisa`
Para cada componente afectado (en paralelo si son independientes, en secuencia si hay dependencias):
- Implementar step definitions y fixtures de los escenarios de reproducción definidos por Atenea.
- Implementar las evaluaciones (evals) definidas por Atenea.
- Crear tests unitarios que capturen el fallo.
- Confirmar que los tests fallan inicialmente (Estado Rojo).

### 7. Revisión de Tests → Agente: `hades`
Hades opera en contexto aislado usando la skill `/review-test`:
- Auditar calidad de los tests de reproducción y confirmar que fallan correctamente. Puntuación mínima 8/10.
- **Bucle de auto-corrección (máx. 3 iteraciones)**: si Hades rechaza → `artemisa` corrige los tests → Hades re-evalúa.

### 8. Fase de Corrección (Fix) → Agente: `artemisa`
- Implementar la corrección siguiendo estándares (docstrings obligatorios, no comentarios inline).
- Verificar que todos los tests pasan y no se rompen tests existentes.

### 9. HITL — Validación funcional
Solicitar confirmación del usuario. Propósito: el usuario valida que la corrección funciona correctamente en conjunto (integración visual, UX, efectos secundarios) — lo que los tests BDD/unitarios no cubren.

### 10. Revisión de Código → Agente: `hades`
Hades opera en contexto aislado usando la skill `/review-code`:
- Evaluar calidad del código de la corrección. Puntuación mínima 8/10.
- La ausencia de regresiones se verifica ejecutando la suite completa (los BDD de reproducción que pasan confirman que el fallo está resuelto).
- Incluir en la evaluación: descripción del bug original y criterios de aceptación.
- **Bucle de auto-corrección (máx. 3 iteraciones)**: si Hades rechaza → `artemisa` corrige → Hades re-evalúa.
- Si algún bucle no converge en 3 iteraciones → presentar reporte al usuario y solicitar decisión.

### 11. Documentación y Commit → Agente: `clio`
Clío usa las skills `/manage-docs` y `/commit`:
- Documentar la solución y actualizar la documentación del proyecto.
- Generar commit con el prefijo `fix([ID])`.

### 12. Cierre → Agente: `cronos`
- Actualizar `actual_effort` y `remaining_effort` en el padre y en los hijos.
- Marcar `status: completed` en todos los hijos resueltos.
- Si todos los hijos están resueltos, cerrar el bug padre (`completed`) y verificar coherencia de `version`.
