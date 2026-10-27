---
id: B-ADV-0014
title: "Las dependencias inválidas del backlog paran el bucle en vez de devolverlas a Cronos"
type: bug
weight: 40
dificultad: sencilla
version: "v1.0.0"
status: planned
depende_de: []
origen: "Revisión humana de los puntos de parada de orquestar.py (2026-10-27): para sin necesitar al humano"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0014: Las dependencias inválidas del backlog paran el bucle en vez de devolverlas a Cronos

## 🎯 Descripción del Fallo

**Causa raíz**: en `estado()` (`orquestar.py`, hacia la línea 893), si `errores_dependencias(items)` encuentra errores (un ID inexistente, un ciclo o una dependencia hacia una versión posterior), devuelve `('PARAR', 'Dependencias inválidas en el backlog: …')`.

**Comportamiento observado**: un error mecánico del backlog, que suelen introducir los propios pasos, exige que una persona lo corrija.

**Comportamiento esperado**:
1. `estado()` devuelve el paso `calcular-dependencias` y su prompt incluye los errores detectados. Cronos los corrige.
2. Si tras `--reintentos` siguen los mismos errores, entonces para, como ahora.
3. Pruebas con un backlog que tenga una dependencia hacia un ID inexistente y otro con un ciclo.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario ha pedido este cambio expresamente: el bucle solo debe pararse cuando haga falta una decisión humana. Si hay que cambiar requisitos o escenarios del bucle (orquestar), forma parte del alcance de este bug. Se puede tocar cualquier ruta necesaria.
