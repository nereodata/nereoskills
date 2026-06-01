---
name: task-dev
description: Ciclo de desarrollo completo para una tarea del backlog (BDD -> TDD -> Dev -> QA -> Doc)
inputs:
  - task_id: ID de la tarea padre (ej. T-PRJ-XXXX) o componente (ej. T-PRJ-COMP-XXXX)
outputs:
  - status: completed
  - version: versión del bloque funcional asociada a la tarea
prerequisites:
  - git_status: limpio (sin cambios no commiteados)
  - branch: release/vX.Y o hotfix/vX.Y.Z activa
dependencies:
  - generate-bdd
  - review-spec
  - review-test
  - review-code
  - manage-docs
  - commit
---

# Skill: Desarrollo de Tarea (/task-dev)

Playbook para el ciclo completo de desarrollo de una tarea.

## Modo de Trabajo

El flujo se ejecuta por defecto a nivel de tarea padre (`T-[PRJ]-XXXX`) consolidando la especificación y validación de todos los componentes afectados. Alternativamente, puede acotarse a un único componente usando la tarea hija correspondiente (`T-[PRJ]-[COMP]-XXXX`) como atajo de desarrollador.

## Flujo de Orquestación

### 1. Inicialización (inline)

- Validar rama de trabajo:
  - La rama activa debe seguir el patrón `release/vX.Y` o `hotfix/vX.Y.Z`.
  - Si la rama es `main`, **abortar**: "No se puede desarrollar directamente en main. Usa `/start-version` para crear un bloque funcional o crea una rama hotfix."
- Cargar metadatos de la tarea padre y de todas sus tareas hijas (componentes afectados).
- Cargar la versión actual del proyecto desde `task_config.yaml` (`project.version`).
- **Coherencia de versión:** Verificar que el campo `version` de la tarea (si ya tiene uno asignado) coincide con la versión de la rama activa. Si no coincide, advertir al usuario.
- Si es **Component Mode**, identificar `parent_id` para actualizar métricas globales.
- Si es **Master Mode**, cargar lista de tareas hijas pendientes.
- Cambiar `status` a `in_progress` en la padre y en las hijas. Confirmar `estimated_effort` y establecer `remaining_effort`.

### 2. Triaje de Alcance (inline — coordinador)

**Filosofía Delta-First (anti-reimplementación):** Antes de especificar o construir nada, analiza si la funcionalidad ya existe total o parcialmente en el código.

Si la funcionalidad ya existe total o parcialmente:

- Presentar al usuario lo identificado y proponer sincronizar el backlog (marcar como completada) o acotar la tarea al alcance real restante (triaje = omitir subfases de implementación innecesarias).

Si no está implementada, el coordinador evalúa el delta y decide **cuáles de las siguientes subfases de la Fase 3 (Implementación) son necesarias**:

- **¿Subfase A: Definición?** Requerida si hay comportamiento nuevo que especificar mediante BDD/evals.
- **¿Subfase B: Desarrollo (Red/Green)?** Requerida si hay cambios de código y tests.
- **¿Subfase C: QA (Revisión de Código)?** Requerida si se modifica código de negocio.
- **¿Subfase D: Documentación?** Requerida si impacta a la arquitectura o manuales.
- **¿Subfase E: Cierre y Commit?** Siempre obligatoria al finalizar.

**Gestión del Flujo (checklist externo):** Tras el triaje, crea un checklist explícito en `task.md` con solo las subfases de Implementación activadas. A lo largo del desarrollo, marca cada subfase anterior como completada. El flujo no está completo mientras queden ítems o HITL abiertos (incluyendo los diferidos). Esto re-ancla la atención y protege contra el olvido de fases.

### 3. Implementación (inline)

Ejecutar secuencialmente las subfases habilitadas durante el Triaje:

#### Subfase A: Definición (BDD + Evals)

- **Especificación (skill `/generate-bdd`):**
  - Revisar la tarea para detectar ambigüedades. Si algo es ambiguo, preguntar al usuario; si está claro, continuar.
  - **BDDs de la Aplicación:** Definir escenarios BDD a nivel feature (`.feature`) para el delta de comportamiento de la aplicación en español, integrándolos en archivos existentes (no crear archivos nominales a IDs de tarea).
- **Naming Conventions:** Los archivos `.feature` deben nombrarse según la funcionalidad (p.ej., `login.feature`, `checkout.feature`) y organizarse en carpetas que reflejen la arquitectura funcional (e.g., `features/auth/`, `features/cart/`). No usar IDs de tarea ni versiones en los nombres. Tampoco usar nombres de archivos de BDD para identificar tareas. El objetivo es que el nombre del archivo refleje la funcionalidad de manera independiente a la tarea.
- **Functional Queue:** Mantener siempre una cola funcional de ejecuciones BDD/evals para asegurar que los tests se procesen en orden determinista.
- **Enfoque de Escenarios:** Los escenarios BDD describen **necesidades del usuario**, no soluciones técnicas. Las decisiones técnicas son de diseño, salvo que constituyan una necesidad explícita del usuario (p. ej., integración con API de SAP).
  - **Evals de IA (Golden Tests):** Si la tarea implica comportamiento de modelos de lenguaje (LLMs), definir los criterios de evaluación de IA (formato esperado, precisión, tono) también en **formato BDD/Gherkin**, pero **aislados de los BDD de la app** en su propia suite de pruebas de modelos.
  - Presentar la especificación (BDDs de app y BDDs de evals de IA) de forma consolidada en un resumen único.
- **Revisión de Especificación → Agente: hades:**
  - Hades opera en contexto aislado usando la skill `/review-spec` para evaluar claridad, completitud y testeabilidad.
  - **Bucle de auto-corrección (máx. 3 iteraciones):** Si la revisión detecta hallazgos, el hilo principal corrige y re-evalúa. Es obligatorio resolver las mejoras críticas/altas. Las medias/bajas se resuelven todas salvo que impliquen riesgo o gran complejidad de desarrollo, en cuyo caso se proponen al usuario como deuda técnica.
- **HITL — Validación de especificación:**
  - Solicitar confirmación del usuario sobre la especificación completa y consolidada.

#### Subfase B: Desarrollo (Red / Green Phase)

- **Red Phase (Fase Roja):**
  - **Tests preexistentes:** No modificarlos a menos que sea estrictamente necesario para la tarea.
  - Implementar step definitions y fixtures de los escenarios BDD, y las evals si las hay.
  - Crear tests unitarios en `<componente>/tests/unit/` que cubran el cambio (no más).
  - Confirmar que los tests fallan inicialmente ejecutando solo los tests relevantes al cambio.
  - **Revisión de Tests → Agente: hades:**
    - Hades opera en contexto aislado usando la skill `/review-test` para auditar la suite y confirmar que los tests fallan.
    - **Bucle de auto-corrección (máx. 3 iteraciones):** Es obligatorio resolver hallazgos críticos/altos. Las mejoras medias/bajas se resuelven todas salvo que impliquen riesgo de desarrollo, en cuyo caso se proponen al usuario como deuda técnica.
- **Green Phase (Fase Verde):**
  - Implementar lo mínimo para satisfacer los escenarios definidos (docstrings obligatorios, no comentarios inline).
  - Durante el desarrollo, ejecutar solo los tests relevantes; al terminar, ejecutar la suite completa una vez para descartar regresiones.

#### Subfase C: QA (Revisión de Código y Validación Funcional)

- **Revisión de Código → Agente: hades:**
  - Hades opera en contexto aislado usando la skill `/review-code` para evaluar la calidad del código.
  - **Bucle de auto-corrección (máx. 3 iteraciones):** Es obligatorio resolver hallazgos críticos/altos. Las mejoras medias/bajas se resuelven todas salvo que impliquen riesgo de regresión o gran complejidad de desarrollo, en cuyo caso se proponen al usuario como deuda técnica. Si el bucle no converge tras 3 iteraciones, reportar y solicitar decisión.
- **HITL — Validación funcional:**
  - Solicitar confirmación del usuario para validar la integración visual, UX y comportamiento conjunto no cubierto por tests.

#### Subfase D: Documentación

- **Actualizar Documentos (skill `/manage-docs`):**
  - Generar o actualizar los documentos definidos en `docs_config.yaml` de forma minimalista.

#### Subfase E: Cierre y Commit

- **Commit Semántico (skill `/commit`):**
  - Generar commit semántico estandarizado.
- **Cierre de Tareas:**
  - Actualizar `actual_effort` y `remaining_effort` en la tarea padre y sus hijas.
  - Marcar `status: completed` en todas las tareas hijas. Si todas están listas, cerrar la tarea padre (`completed`) y verificar coherencia de `version`.
