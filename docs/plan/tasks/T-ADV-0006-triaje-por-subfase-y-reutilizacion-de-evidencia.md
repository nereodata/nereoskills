---
id: T-ADV-0006
title: "Triaje por subfase y alcance sin doble validación en desarrollo y revisión"
type: funcional
weight: 100
version: "v0.1.0"
status: completed
depende_de: []
origen: "Hallazgo operativo en ejecución real de /orquestar (Afinn)"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0006: Triaje por subfase y alcance sin doble validación en desarrollo y revisión

## 🎯 Objetivo de Negocio
Hacer que el Triaje de Alcance de `/task-dev` y `/bug-fix` gobierne de verdad qué subfases se ejecutan y sobre qué parte concreta de la tarea, evitando bucles de revisiones redundantes y la doble ejecución de lint, tipado, validadores y chequeos de seguridad entre el desarrollador y Hades.

### Hueco real (Delta sobre el código actual)
- **Ya existe:** El esqueleto de subfases en `skills/task-dev/SKILL.md` y `skills/bug-fix/SKILL.md`, la caché de verificación por árbol en `skills/orquestar/orquestar.py` (`--verificar`) y las instrucciones de Hades (`agents/hades.md` y `skills/review-code/SKILL.md`).
- **Falta implementar:** Separar `Subfase C1 (Pruebas / Red Phase)` y `Subfase C2 (Implementación / Green Phase)` en el triaje indicando en cada `[EXEC]` a qué parte de la tarea aplica; acotar las revisiones de Hades a una invocación por subfase `[EXEC]`; eliminar rigideces (números cerrados de Evals y rutas fijas de tests); registrar lint, tipado y seguridad con `--verificar` al cierre de `C2`; inyectar en el prompt de `--agente` los comandos ya verificados en verde sobre el árbol actual para que Hades no los relance; y aplicar el tope de rechazos seguidos también sin `escalada` configurada.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1:** El Triaje de Alcance en `skills/task-dev/SKILL.md` y `skills/bug-fix/SKILL.md` separa `C1: Pruebas (Red Phase)` y `C2: Implementación/Corrección (Green/Fix Phase)`, exige indicar en cada `[EXEC]` a qué parte de la tarea aplica, establece una única revisión de Hades por subfase `[EXEC]` y registra lint, tipado y chequeos de seguridad aplicables al delta mediante `adevv orquestar --verificar`.
- [x] **CA-M-2:** `skills/review-code/SKILL.md` y `agents/hades.md` evalúan la conformidad frente al triaje de la tarea (sin exigir `docs/design/[ID]-design.md` cuando la Subfase B se omitió), no relanzan chequeos ya en verde en `--verificar` y dan por cierto todo lo garantizado por validadores, esquemas o tests deterministas en verde.
- [x] **CA-M-3:** `construir_prompt_agente` en `skills/orquestar/orquestar.py` informa en el mandato del rol los comandos verificados en verde sobre el árbol actual (`orquestar_evidencias.jsonl`), y `tope_de_rechazos` corta tras 3 rechazos seguidos aplicando la regla 5 cuando el proyecto no tiene configurada `escalada`.

## ⚙️ Triaje de Subfases
- [x] **Subfase A: Definición (BDD / Evals)** → `[SKIP]` (ajuste operativo acotado sobre instrucciones de skills y funciones puras de `orquestar.py`, cubierto directamente por tests unitarios)
- [x] **Subfase B: Diseño Técnico** → `[SKIP]` (sin cambios de arquitectura ni nuevas dependencias)
- [x] **Subfase C1: Pruebas (Red Phase)** → `[EXEC]` (`tests/test_orquestar.py`: `test_without_escalation_three_rejections_block_the_task`, `test_agent_prompt_lists_verified_commands_for_current_tree`)
- [x] **Subfase C2: Implementación (Green Phase)** → `[EXEC]` (`skills/task-dev/SKILL.md`, `skills/bug-fix/SKILL.md`, `skills/review-code/SKILL.md`, `agents/hades.md`, `skills/orquestar/orquestar.py`)
- [x] **Subfase D: Aseguramiento de Calidad (QA)** → `[EXEC]` (`docs/review/code_reviews/T-ADV-0006-code-review.md`)
- [x] **Subfase E: Documentación** → `[SKIP]` (las propias skills documentan el flujo operativo)
- [x] **Subfase F: Cierre** → `[EXEC]` (status: completed, commit e instalación local actualizada)

**Verificación al cierre:** `adevv orquestar --verificar "python -m unittest tests/test_orquestar.py tests/test_instructions_cleanliness.py"`.
