---
id: T-ADV-0007
title: "Detección y espera de cuota agotada en subagentes (--agente)"
type: funcional
weight: 100
version: "v0.1.0"
status: completed
depende_de: []
origen: "Hallazgo operativo en ejecución real de /orquestar (Afinn)"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0007: Detección y espera de cuota agotada en subagentes (--agente)

## 🎯 Objetivo de Negocio
Evitar que el agotamiento de cuota o créditos dentro de un rol delegado (`adevv orquestar --agente hades|clio|cronos`) se contabilice como falta de progreso del desarrollador y aborte el bucle desatendido.

### Hueco real (Delta sobre el código actual)
- **Ya existe:** La expresión regular `CUOTA`, el cálculo `espera_cuota(salida)` y la espera automática `esperar(root, cuota)` en `skills/orquestar/orquestar.py` cuando falla el arnés principal del paso.
- **Falta implementar:** Ampliar `CUOTA` para reconocer mensajes de agotamiento de créditos de Codex/OpenAI (`out of credits`, `credit balance`, `insufficient_quota`, `billing_hard_limit`); registrar `'sin_cuota': True` y `'espera_s': cuota` en `orquestar_metricas.jsonl` cuando falla `agente(root, rol, prompt)` por cuota e indicar al agente padre que termine el turno sin tocar estados; y hacer que `bucle(a, root)` detecte `sin_cuota` en las entradas de `agente` generadas durante el paso para entrar en `esperar(root, cuota)` sin incrementar `sin_progreso`.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1:** `CUOTA` y `espera_cuota` en `skills/orquestar/orquestar.py` reconocen los mensajes de falta de créditos (`Your workspace is out of credits. Add credits to continue.`, `credit balance`, `insufficient_quota`, `billing_hard_limit`).
- [x] **CA-M-2:** Cuando `agente(root, rol, prompt)` termina con código distinto de cero por falta de cuota, registra `'sin_cuota': True` y `'espera_s': cuota` en `orquestar_metricas.jsonl` e imprime la instrucción de terminar el paso sin modificar estados.
- [x] **CA-M-3:** Cuando un subagente registra `sin_cuota` durante un paso del bucle, `bucle(a, root)` entra en modo de espera de cuota (`esperar(root, cuota)`) y reintenta el paso aunque el arnés principal haya devuelto código `0` sin cambios en el árbol, sin incrementar `sin_progreso`.

## ⚙️ Triaje de Subfases
- [x] **Subfase A: Definición (BDD / Evals)** → `[SKIP]` (comportamiento determinista del motor de orquestación cubierto por pruebas unitarias en `tests/test_orquestar.py`)
- [x] **Subfase B: Diseño Técnico** → `[SKIP]` (cambio localizado en `CUOTA`, `agente` y `bucle` dentro de `skills/orquestar/orquestar.py`)
- [x] **Subfase C1: Pruebas (Red Phase)** → `[EXEC]` (`tests/test_orquestar.py`: `test_subagent_out_of_credits_triggers_quota_wait_in_loop`)
- [x] **Subfase C2: Implementación (Green Phase)** → `[EXEC]` (`skills/orquestar/orquestar.py`)
- [x] **Subfase D: Aseguramiento de Calidad (QA)** → `[EXEC]` (`docs/review/code_reviews/T-ADV-0007-code-review.md`)
- [x] **Subfase E: Documentación** → `[SKIP]` (no altera la interfaz CLI ni la documentación de usuario)
- [x] **Subfase F: Cierre** → `[EXEC]` (status: completed, commit e instalación local actualizada)

**Verificación al cierre:** `adevv orquestar --verificar "python -m unittest tests/test_orquestar.py"`.
