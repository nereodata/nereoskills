---
name: work-plan
description: Crear la estrategia de desarrollo y generar tareas en el backlog.
---

# Skill: Plan de Trabajo (/work-plan)

**Objetivo:** Crear la estrategia de desarrollo basada en las tecnologías elegidas y automatizar la creación de tareas.

**Documentación necesaria:**
- `requirements.md`
- `req_analysis.md` (Resultado del paso 1).
- `needs_analysis.md` (Resultado del paso 2).
- `platform_plan.md` (Resultado del paso 3).

## Instrucciones del Prompt (Ejecutar en dos fases)

### Fase 1: Generación del Plan de Desarrollo
Genera un plan de desarrollo técnico detallado basado EXCLUSIVAMENTE en la arquitectura de plataforma aprobada. 

**Instrucciones:**
1. **Foco en Software**: No incluyas tareas de infraestructura (ya definidas en el plan anterior).
2. **Filosofía BDD/TDD**: Cada bloque funcional debe empezar por la definición de pruebas.
3. **Tecnologías**: Usa EXACTAMENTE las definidas en el plan de plataforma (ej. si dice React, usa React).
4. **Granularidad**: Tareas atómicas e independientes.

**SALIDA ESPERADA:**
Un resumen del plan de trabajo en un fichero Markdown de nombre `work_plan.md`, en el mismo directorio que los ficheros de entrada y que explique las fases de desarrollo, hitos principales y estrategia de integración continua.

### Fase 2: Automatización del Backlog (Task Creation)
Una vez generado el `work_plan.md`, procede a registrar cada una de las tareas identificadas en el sistema de backlog utilizando la skill `/task-add`.

**Asignación de Versión Target:**
- Solicitar al usuario la versión target para este plan de trabajo (ej. `v1.2`).
- Todas las tareas generadas se crearán con `version: "vX.Y.0"` y `status: planned`.
- Si el usuario no especifica versión, las tareas se crean con `version: ""` y `status: backlog` (por defecto).
- Agrupar las tareas en el resumen final por versión target para facilitar la trazabilidad con las ramas `release/`.

**Reglas de Priorización (Weighting):**
- La prioridad de las tareas debe ser **ascendente**.
- El peso inicial debe ser **superior a 100** (o el valor indicado por el usuario).
- Se debe dejar una separación de **10 puntos** entre cada tarea (ej. 110, 120, 130...).
- Para cada tarea del plan, invoca `/task-add` proporcionando el título, objetivo técnico y criterios de aceptación derivados del plan.

### Fase 3: Especificación del Contrato Técnico (Escenarios y Evals)
Tras registrar las tareas en el backlog, el planificador debe generar las especificaciones formales de comportamiento y calidad que guiarán al desarrollo técnico:

1. **Creación de Features BDD**:
   - Por cada tarea de componente que afecte a un flujo funcional, crear o actualizar los archivos `.feature` de Gherkin correspondientes en la ruta del componente (ej. `<componente>/tests/bdd/features/`).
   - Los escenarios deben redactarse en español y etiquetarse con `@pending` o `@unimplemented` para que sirvan como la base de la Fase Roja en el desarrollo.
2. **Definición de Evals / Golden Sets**:
   - Si la tarea involucra componentes de Inteligencia Artificial, NL2SQL o pipelines probabilísticos, añadir al menos **3-5 casos de prueba de evaluación** representativos al dataset de Golden Evals del proyecto (ej: registrando preguntas y salidas esperadas en los datasets de evaluación locales).

**SALIDA ESPERADA:**
- Confirmación del plan generado y lista de IDs de tareas maestras (`T-[PRJ]-XXXX`) y de componente (`T-[PRJ]-[COMP]-XXXX`) creadas.
- Listado de archivos `.feature` y datasets de evaluación inicializados como contratos de aceptación para el desarrollo técnico.

