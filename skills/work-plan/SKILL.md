---
name: work-plan
description: Crear la estrategia de desarrollo y generar tareas en el backlog.
---

# Skill: Plan de Trabajo (/work-plan)

**Objetivo:** Crear la estrategia de desarrollo basada en las tecnologías elegidas y registrar sus tareas en el backlog.

**Documentación necesaria:**
- `requirements.md`
- `req_analysis.md` (Resultado del paso 1).
- `platform_plan.md` (Resultado del paso 2).

## Fase 1: Plan de Desarrollo

Genera un plan de desarrollo basado EXCLUSIVAMENTE en la arquitectura de plataforma aprobada:
- **Foco en Software**: Sin tareas de infraestructura (ya definidas en `platform_plan.md`).
- **Tecnologías**: EXACTAMENTE las del plan de plataforma (si dice React, React).
- **Filosofía BDD/TDD**: Cada bloque funcional empieza por la definición de pruebas.
- **Bloques = tareas padre**: Cada bloque es una capacidad con valor de usuario según `/task-add` (si se describe como "permite X y además Y", son dos), descompuesta por componente afectado.
  Si `requirements.md` viene de `/ciclo-requisitos`, cada `F-xx` es un bloque.
- **Versiones = bloques funcionales** (`Y` de `branch_strategy.md`): agrupa las tareas padre en versiones. Cada versión reúne varias funcionalidades que juntas dan un nuevo nivel de capacidad, demostrable de principio a fin; una sola funcionalidad no justifica versión. La primera es el núcleo mínimo usable. Si hay olas de `/ciclo-requisitos`, parte de ellas.

**Salida:** `work_plan.md`, en el mismo directorio que los ficheros de entrada: versiones, hitos y estrategia de integración continua. Lo justo para registrar las tareas, sin repetir lo que ya dicen los requisitos o el plan de plataforma.

## Fase 2: Backlog

1. **Versiones**: El reparto lo propone el plan; no se pregunta una versión única. Cada tarea se registra con la `vX.Y.0` de su bloque. La revisión humana se hace al cerrar cada versión, no antes.
2. **Registro** con `/task-add`, por bloque:
   - **Maestra**: título, objetivo de negocio y criterios `CA-M-n` (si hay `CA-Fxx-nn` de origen, cítalo en el criterio).
   - **Hijas**, una por componente afectado: objetivo técnico y criterios `CA-n` en forma de escenario.
3. **Peso**: Ascendente, desde un valor **superior a 100** (o el indicado por el usuario), con **10 puntos** de separación (110, 120, 130...).

## Fase 3: Contrato de Aceptación

Para cada tarea hija que afecte a un flujo funcional, aplica `/generate-bdd` con sus `CA-n` como etiquetas `@CA-*`. Si involucra IA, NL2SQL o pipelines probabilísticos, añade **3-5 evals** como Golden Tests en Gherkin, en su suite aislada.

`/task-dev` reutiliza estos escenarios en su Subfase A (delta-first) y los audita con `/review-spec`.

## Salida Esperada

- IDs de tareas maestras (`T-[PRJ]-XXXX`) y de componente (`T-[PRJ]-[COMP]-XXXX`) creadas, agrupadas por versión target (trazabilidad con ramas `release/`).
- `.feature` y evals creados o actualizados.
