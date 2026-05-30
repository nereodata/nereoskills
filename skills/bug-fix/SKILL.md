---
name: bug-fix
description: Ciclo completo para la resolución de anomalías (bugs) detectadas.
inputs:
  - bug_id: ID del bug padre (ej. B-PRJ-XXXX) o componente (ej. B-PRJ-COMP-XXXX)
outputs:
  - status: completed
  - version: versión de la rama de trabajo asociada al hotfix o release
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

# Skill: Resolución de Anomalías (/bug-fix)

Playbook para la resolución de bugs.



## Modo de Trabajo

El flujo se ejecuta por defecto a nivel de bug padre (`B-[PRJ]-XXXX`) consolidando la reproducción y validación de todos los componentes afectados. Alternativamente, puede acotarse a un único componente usando el bug hijo correspondiente (`B-[PRJ]-[COMP]-XXXX`) como atajo de desarrollador.





## Flujo de Orquestación

### 0. Clasificación de Urgencia y Rama de Trabajo (inline)
Preguntar al usuario: **"¿Este bug es urgente y necesita llegar a producción inmediatamente (hotfix), o puede resolverse dentro del bloque funcional actual (release)?"**
- **Si hotfix**:
  - Identificar la versión de producción afectada (último tag en `main`).
  - Calcular la versión patch: si el último tag es `vX.Y.Z`, la rama será `hotfix/vX.Y.(Z+1)`.
  - Crear la rama desde el tag correspondiente y actualizar la versión en los manifiestos al patch.
  - Commit inicial: `chore(hotfix): start hotfix vX.Y.Z`
- **Si release**:
  - Verificar que la rama activa es `release/vX.Y`. Si no, advertir y sugerir cambiar a la rama release activa.
- En ambos casos, actualizar el campo `version` del bug con la versión de la rama de trabajo.

### 1. Inicialización (inline)
- Cargar metadatos del bug padre y de todos sus hijos (componentes afectados).
- Cambiar `status` a `in_progress` en el padre y en los hijos.
- Establecer `actual_effort` y actualizar `remaining_effort`.

### 2. Triaje de Alcance (inline — coordinador)
**Filosofía Delta-First (anti-reimplementación):** Antes de reproducir o corregir, observa el estado actual del código y la causa raíz real para determinar *"¿qué hay ya y qué falta?"*. Tocar solo lo necesario para la corrección, testeando solo lo que cambia, sin reescribir código aledaño fuera de alcance.

Antes de gastar esfuerzo, el coordinador analiza el bug y decide **cuáles de las siguientes subfases de la Fase 3 (Implementación) son necesarias** (solo él tiene el panorama completo):
- **¿Subfase A: Definición?** Requerida si hace falta un escenario de reproducción nuevo mediante BDD/evals.
- **¿Subfase B: Desarrollo (Red/Fix)?** Requerida si hay cambios de código y tests.
- **¿Subfase C: QA (Revisión de Código)?** Requerida si se modifica código de negocio.
- **¿Subfase D: Documentación?** Requerida si el bug requiere actualizar manuales o docs del proyecto.
- **¿Subfase E: Cierre y Commit?** Siempre obligatoria al finalizar.

**Gestión del Flujo (checklist externo):** Tras el triaje, crea un checklist explícito en `task.md` con solo las subfases de Implementación activadas. A lo largo de la corrección, marca cada subfase anterior como completada. El flujo no está completo mientras queden ítems o HITL abiertos (incluyendo los diferidos). Esto re-ancla la atención y protege contra el olvido de fases.

### 3. Implementación (inline)
Ejecutar secuencialmente las subfases habilitadas durante el Triaje:

#### Subfase A: Definición (BDD + Evals de Reproducción)
- **Especificación de Reproducción (skill `/generate-bdd`):**
  - Aclarar con el usuario cualquier dato que falte para reproducir el fallo.
  - **BDDs de la Aplicación:** Definir escenarios BDD que capturen el fallo de la aplicación en español, integrándolos en archivos existentes (no crear archivos nominales al bug o ID de tarea).
  - **Evals de IA (Golden Tests):** Si el fallo concierne a la salida de modelos de lenguaje (LLMs), definir criterios de evaluación de IA (comportamiento esperado, Golden Tests) también en **formato BDD/Gherkin**, pero **aislados de los BDD de la app** en su propia suite de pruebas de modelos.
  - Presentar la especificación (BDDs de app y BDDs de evals de IA) de forma consolidada para revisión ágil.
- **Revisión de Especificación → Agente: hades:**
  - Hades opera en contexto aislado usando la skill `/review-spec` para evaluar claridad, completitud y testeabilidad.
  - **Bucle de auto-corrección (máx. 3 iteraciones):** Si la revisión detecta hallazgos, el hilo principal corrige y re-evalúa. Es obligatorio resolver las mejoras críticas/altas. Las medias/bajas se resuelven todas salvo que impliquen riesgo o gran complejidad de desarrollo, en cuyo caso se proponen al usuario como deuda técnica.
- **HITL — Validación de reproducción:**
  - Solicitar confirmación del usuario antes de implementar la corrección.

#### Subfase B: Desarrollo (Red / Fix Phase)
- **Red Phase (Fase Roja):**
  - **Tests preexistentes:** No modificarlos a menos que sea estrictamente necesario para la tarea.
  - Implementar step definitions y fixtures de los escenarios de reproducción, y las evals si las hay.
  - Crear tests unitarios que capturen el fallo (no más).
  - Confirmar que los tests fallan inicialmente ejecutando solo los tests relevantes al fallo.
  - **Revisión de Tests → Agente: hades:**
    - Hades opera en contexto aislado usando la skill `/review-test` para auditar la suite y confirmar que los tests fallan.
    - **Bucle de auto-corrección (máx. 3 iteraciones):** Es obligatorio resolver hallazgos críticos/altos. Las mejoras medias/bajas se resuelven todas salvo que impliquen riesgo de desarrollo, en cuyo caso se proponen al usuario como deuda técnica.
- **Fix Phase (Fase de Corrección):**
  - Implementar la corrección mínima de la causa raíz (docstrings obligatorios, no comentarios inline).
  - Durante el desarrollo, ejecutar solo los tests relevantes; al terminar, ejecutar la suite completa una vez para descartar regresiones.

#### Subfase C: QA (Revisión de Código y Validación Funcional)
- **Revisión de Código → Agente: hades:**
  - Hades opera en contexto aislado usando la skill `/review-code` para evaluar la calidad de la corrección.
  - **Bucle de auto-corrección (máx. 3 iteraciones):** Es obligatorio resolver hallazgos críticos/altos. Las mejoras medias/bajas se resuelven todas salvo que impliquen riesgo de regresión o gran complejidad de desarrollo, en cuyo caso se proponen al usuario como deuda técnica. Si el bucle no converge tras 3 iteraciones, reportar y solicitar decisión.
- **HITL — Validación funcional:**
  - Solicitar confirmación del usuario: valida que la corrección funciona en conjunto (integración, UX, efectos secundarios).

#### Subfase D: Documentación
- **Actualizar Documentos (skill `/manage-docs`):**
  - Documentar la solución y actualizar la documentación del proyecto.

#### Subfase E: Cierre y Commit
- **Commit Semántico (skill `/commit`):**
  - Generar commit con el prefijo `fix([ID])`.
- **Cierre de Tareas:**
  - Actualizar `actual_effort` y `remaining_effort` en el bug padre y sus hijos.
  - Marcar `status: completed` en todos los bugs hijos. Si todos están resueltos, cerrar el bug padre (`completed`) y verificar coherencia de `version`.
