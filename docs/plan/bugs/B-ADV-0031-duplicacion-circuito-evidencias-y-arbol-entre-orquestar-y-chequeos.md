---
id: B-ADV-0031
title: "Duplicación del circuito de lectura/escritura de evidencias y huella de árbol entre orquestar.py y chequeos.py"
type: bug
weight: 1500
dificultad: media
version: ""
status: backlog
origen: "T-ADV-0032; revisar-version v1.1 (docs/review/versions/v1.1-arquitectura.md), H-01 🟡"
created_at: 2026-11-07
updated_at: 2026-11-07
---

# B-ADV-0031: Duplicación del circuito de lectura/escritura de evidencias y huella de árbol entre orquestar.py y chequeos.py

## 🎯 Descripción del Fallo

**Causa raíz:**
- `T-ADV-0032` introdujo en `skills/orquestar/chequeos.py` funciones centralizadas (`arbol_trabajo`, `comandos_verificados_arbol`, `ultimo_resultado_arbol_comando` y `_escribir_evidencia`, que sincroniza además con `<git-common-dir>/adevv-chequeos/orquestar_evidencias.jsonl`).
- Sin embargo, `skills/orquestar/orquestar.py` mantiene en `verificar()`, `arbol()` y `construir_prompt_agente()` su propia implementación paralela de cálculo de huella del árbol y su propia lectura/escritura directa sobre `root / EVIDENCIAS`.

**Comportamiento observado:** existen dos circuitos paralelos para calcular la huella `arbol` del repositorio y leer/escribir `orquestar_evidencias.jsonl`. Si una tarea futura amplía el contrato de evidencias o ejecuta `adevv orquestar --verificar` directamente dentro de un worktree secundario esperando compartir la evidencia con `<git-common-dir>/adevv-chequeos`, ambos almacenes pueden desincronizarse o requerir cambios duplicados.

**Comportamiento esperado:** `orquestar.py` delega `arbol()`, `verificar()` y la consulta de comandos verificados de `construir_prompt_agente()` en las funciones centralizadas de `skills/orquestar/chequeos.py`.

## 📋 Reproducir
1. Comparar `arbol()`, `verificar()` y `construir_prompt_agente()` en `skills/orquestar/orquestar.py` (líneas 495–515, 2242–2251 y 2270–2296) con `arbol_trabajo()`, `_escribir_evidencia()` y `comandos_verificados_arbol()` en `skills/orquestar/chequeos.py` (líneas 178–196, 618–633 y 1276–1294).

## 📋 Evidencias
- `docs/review/versions/v1.1-arquitectura.md`, hallazgo H-01.
