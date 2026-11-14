---
id: B-ADV-0031
title: "Duplicación del circuito de lectura/escritura de evidencias y huella de árbol entre orquestar.py y chequeos.py"
type: bug
weight: 70
dificultad: dificil
version: "v1.2.0"
status: planned
depende_de: []
origen: "T-ADV-0032; revisar-version v1.1 (docs/review/versions/v1.1-arquitectura.md), H-01 🟡"
created_at: 2026-11-07
updated_at: 2026-11-14
---

# B-ADV-0031: Duplicación del circuito de lectura/escritura de evidencias y huella de árbol entre orquestar.py y chequeos.py

## 🎯 Descripción del Fallo

**Causa raíz:**
- `T-ADV-0032` introdujo en `skills/orquestar/chequeos.py` funciones centralizadas (`arbol_trabajo`, `comandos_verificados_arbol`, `ultimo_resultado_arbol_comando` y `_escribir_evidencia`, que sincroniza además con `<git-common-dir>/adevv-chequeos/orquestar_evidencias.jsonl`).
- Sin embargo, `skills/orquestar/orquestar.py` mantiene en `verificar()`, `arbol()` y `construir_prompt_agente()` su propia implementación paralela de cálculo de huella del árbol y su propia lectura/escritura directa sobre `root / EVIDENCIAS`.

**Comportamiento observado:** existen dos circuitos paralelos para calcular la huella `arbol` del repositorio y leer/escribir `orquestar_evidencias.jsonl`. Si una tarea futura amplía el contrato de evidencias o ejecuta `adevv orquestar --verificar` directamente dentro de un worktree secundario esperando compartir la evidencia con `<git-common-dir>/adevv-chequeos`, ambos almacenes pueden desincronizarse o requerir cambios duplicados.

**Comportamiento esperado:** `orquestar.py` delega `arbol()`, `verificar()` y la consulta de comandos verificados de `construir_prompt_agente()` en las funciones centralizadas de `skills/orquestar/chequeos.py`.

## 📋 Reproducir
1. Comparar `arbol()`, `verificar()` y `construir_prompt_agente()` en `skills/orquestar/orquestar.py` con `arbol_trabajo()`, `_escribir_evidencia()` y `comandos_verificados_arbol()` en `skills/orquestar/chequeos.py`.

## 📋 Evidencias
- `docs/review/versions/v1.1-arquitectura.md`, hallazgo H-01.

## Criterios de aceptación de v1.2.0

- [ ] El comando `--verificar`, la evidencia suministrada a Hades y el preflight consultan el mismo historial aplicable, también desde un worktree secundario.
- [ ] Los tres identifican el último resultado real aplicable. Verificar y preflight explican la reutilización de un verde por coincidencia de comando, entradas y entorno, o la nueva ejecución por fallo anterior, entradas modificadas o entorno distinto o desconocido. Si ya se ejecuta una comprobación equivalente, la solicitud indica el motivo de la espera y al terminar comparte su resultado. El mandato de Hades solo acredita resultados verdes aplicables. Un preflight fallido termina tras el primer fallo y una verificación posterior solicitada puede ejecutar de nuevo el comando.
- [ ] La identidad respeta las entradas y el entorno acreditables de la etapa. Si faltan datos en registros históricos, se conserva su trazabilidad y se vuelve a ejecutar cuando corresponda.

## Contexto técnico previo

- **DEC (H-01, 2026-11-12):** Se conserva la espera del segundo criterio (`T-ADV-0032`, CA-M-4: las solicitudes equivalentes comparten la ejecución en curso entre worktrees para no duplicar comprobaciones).
- **Diagnóstico previo:** Cálculo Git y acceso JSONL duplicados entre `skills/orquestar/orquestar.py` (`arbol()`, `verificar()`, `construir_prompt_agente()`) y `skills/orquestar/chequeos.py`; el lector central priorizaba el archivo local sobre el común y los consumidores por árbol no acreditaban entorno ni cambios en vuelo; el preflight solo persistía éxitos.
- **Pruebas relacionadas existentes:** `tests/test_evidencias_compartidas.py`, `tests/test_publicacion_compartida.py` y los tests de verificación/prompts de `tests/test_orquestar.py`.
