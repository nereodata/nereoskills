---
id: T-ADV-0008
title: "Continuidad de hilo en revisiones de Hades por tarea y reanudación tras espera de cuota"
type: funcional
weight: 100
version: "v0.2.0"
status: completed
depende_de: []
origen: "Mejora operativa sobre el ciclo de revisión de /orquestar"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0008: Continuidad de hilo en revisiones de Hades por tarea y reanudación tras espera de cuota

## 🎯 Objetivo de Negocio
Mantener un único hilo de conversación de Hades durante todo el ciclo de una misma tarea o bug (`ID`) —incluyendo todas sus fases (`review-spec`, `review-test`, `review-code`) y rondas de corrección— así como reanudar el hilo del desarrollador cuando un paso se interrumpe por agotamiento de cuota, evitando pérdida de contexto, contradicciones entre rondas y gasto repetido de tokens de lectura.

### Hueco real (Delta sobre el código actual)
- **Ya existe:** `lanzar()`, `agente()`, `ejecutar()` y `bucle()` en `skills/orquestar/orquestar.py`, captura de uso/coste en métricas, y espera por cuota agotada.
- **Falta implementar:**
  1. Extraer identificadores de sesión (`session_id`, `thread_id`, `conversation_id`) en `lanzar()` para Claude, Codex (sin `--ephemeral`) y Antigravity, registrándolos en `orquestar_metricas.jsonl` (`sesion`).
  2. Reanudación de sesión en `agente()` para Hades cuando existe sesión previa del mismo `(rol, id, arnes)` dentro del intento en curso, enviando únicamente evidencias y mandato sin cabecera inicial, con fallback a sesión nueva si falla la reanudación.
  3. Reanudación de sesión en `bucle()` / `ejecutar()` tras espera de cuota para el mismo `(paso, id, arnes)`, con fallback a sesión nueva si falla.
  4. Aislamiento estricto de sesión ante cambio de `ID`, paso por `blocked` o cambio de modelo por `escalada`.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Captura de sesión por arnés):** `lanzar()` en `skills/orquestar/orquestar.py` extrae el identificador de sesión de la salida de cada arnés (`session_id` en Claude Code, `thread_id` del evento `thread.started` en Codex tras retirar `--ephemeral`, y `conversation_id` / `session_id` en Antigravity) y lo registra como `sesion` en `orquestar_metricas.jsonl` tanto en pasos principales (`tipo: "paso"`) como en invocaciones de roles (`tipo: "agente"`).
- [x] **CA-M-2 (Hilo único de Hades por tarea/bug):** Cuando `agente(root, rol, prompt)` se ejecuta con `ORQUESTAR_ID` activo y existe en `orquestar_metricas.jsonl` una `sesion` previa para ese mismo `(rol, id, arnes)` dentro del intento en curso (sin reinicio por bloqueo ni escalada), `orquestar.py` reanuda esa sesión (`--resume <id>` en Claude, `codex exec resume <id>` en Codex, `--conversation <id>` en Antigravity) enviando únicamente el nuevo mandato y el estado de evidencias en verde del árbol actual, sin reinyectar la cabecera inicial de carga del agente. Si la reanudación falla en el arnés, hace fallback transparente abriendo una sesión nueva.
- [x] **CA-M-3 (Reanudación del paso tras espera de cuota):** Cuando un paso del bucle (`ejecutar`) se interrumpe por falta de cuota (propia o de un subagente) y dejó registrada una `sesion` válida para ese mismo `(paso, id, arnes)`, el reintento inmediato tras `esperar(root, cuota)` reanuda dicha sesión para continuar desde el punto en que quedó, con fallback a sesión nueva si la reanudación falla.
- [x] **CA-M-4 (Aislamiento entre tareas y tras bloqueos):** Cada nuevo `ID` de tarea/bug (o el relanzamiento de un `ID` tras haber pasado por `blocked` o por cambio de modelo en `escalada`) inicia un hilo limpio de Hades y del desarrollador.

## ⚙️ Triaje de Subfases
- [x] **Subfase A: Definición (BDD / Evals)** → `[SKIP]` (comportamiento determinista del orquestador cubierto con pruebas unitarias exhaustivas en `tests/test_orquestar.py`)
- [x] **Subfase B: Diseño Técnico** → `[SKIP]` (diseño acotado en `skills/orquestar/orquestar.py` sin alteración arquitectónica)
- [x] **Subfase C1: Pruebas (Red Phase)** → `[EXEC]` (`tests/test_orquestar.py`: tests de captura de sesión en `lanzar`, reanudación y fallback en `agente` y `bucle`, y aislamiento de sesión)
- [x] **Subfase C2: Implementación (Green Phase)** → `[EXEC]` (`skills/orquestar/orquestar.py`)
- [x] **Subfase D: Aseguramiento de Calidad (QA)** → `[EXEC]` (`docs/review/code_reviews/T-ADV-0008-code-review.md`)
- [x] **Subfase E: Documentación** → `[SKIP]` (comportamiento interno desatendido de orquestación)
- [x] **Subfase F: Cierre** → `[EXEC]` (status: completed, commit e instalación local actualizada)

**Verificación al cierre:** `adevv orquestar --verificar "python -m unittest tests/test_orquestar.py"`.
