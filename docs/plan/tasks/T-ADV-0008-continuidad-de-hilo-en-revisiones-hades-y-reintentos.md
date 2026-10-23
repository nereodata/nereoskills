---
id: T-ADV-0008
title: "Continuidad de hilo en revisiones de Hades por tarea y reanudación tras espera de cuota"
type: funcional
weight: 100
version: "v0.2.0"
status: planned
depende_de: []
origen: "Mejora operativa sobre el ciclo de revisión de /orquestar"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0008: Continuidad de hilo en revisiones de Hades por tarea y reanudación tras espera de cuota

## 🎯 Objetivo de Negocio
Mantener un único hilo de conversación de Hades durante todo el ciclo de una misma tarea o bug (`ID`) —incluyendo todas sus fases (`review-spec`, `review-test`, `review-code`) y rondas de corrección— así como reanudar el hilo del desarrollador cuando un paso se interrumpe por agotamiento de cuota, evitando pérdida de contexto, contradicciones entre rondas y gasto repetido de tokens de lectura.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Captura de sesión por arnés):** `lanzar()` en `skills/orquestar/orquestar.py` extrae el identificador de sesión de la salida de cada arnés (`session_id` en Claude Code, `thread_id` del evento `thread.started` en Codex tras retirar `--ephemeral`, y `conversation_id` / `session_id` en Antigravity) y lo registra como `sesion` en `orquestar_metricas.jsonl` tanto en pasos principales (`tipo: "paso"`) como en invocaciones de roles (`tipo: "agente"`).
- [ ] **CA-M-2 (Hilo único de Hades por tarea/bug):** Cuando `agente(root, rol, prompt)` se ejecuta con `ORQUESTAR_ID` activo y existe en `orquestar_metricas.jsonl` una `sesion` previa para ese mismo `(rol, id, arnes)` dentro del intento en curso (sin reinicio por bloqueo ni escalada), `orquestar.py` reanuda esa sesión (`--resume <id>` en Claude, `codex exec resume <id>` en Codex, `--conversation <id>` en Antigravity) enviando únicamente el nuevo mandato y el estado de evidencias en verde del árbol actual, sin reinyectar la cabecera inicial de carga del agente. Si la reanudación falla en el arnés, hace fallback transparente abriendo una sesión nueva.
- [ ] **CA-M-3 (Reanudación del paso tras espera de cuota):** Cuando un paso del bucle (`ejecutar`) se interrumpe por falta de cuota (propia o de un subagente) y dejó registrada una `sesion` válida para ese mismo `(paso, id, arnes)`, el reintento inmediato tras `esperar(root, cuota)` reanuda dicha sesión para continuar desde el punto en que quedó, con fallback a sesión nueva si la reanudación falla.
- [ ] **CA-M-4 (Aislamiento entre tareas y tras bloqueos):** Cada nuevo `ID` de tarea/bug (o el relanzamiento de un `ID` tras haber pasado por `blocked` o por cambio de modelo en `escalada`) inicia un hilo limpio de Hades y del desarrollador.
