---
id: B-ADV-0015
title: "Los cambios sin commitear impiden cambiar de rama y paran el bucle"
type: bug
weight: 40
dificultad: sencilla
version: "v1.0.0"
status: completed
depende_de: []
origen: "Revisión humana de los puntos de parada de orquestar.py (2026-10-27): para sin necesitar al humano"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0015: Los cambios sin commitear impiden cambiar de rama y paran el bucle

## 🎯 Descripción del Fallo

**Causa raíz**: en `bucle()` (`orquestar.py`, hacia las líneas 2306 y 2323), si un paso deja el árbol con cambios (archivos generados, restos de pruebas o un commit olvidado) y el siguiente paso es en otra rama, el bucle para con «cambios sin commitear; no puedo cambiar a <rama>». En `orquestar.log` ha pasado 2 veces.

**Comportamiento esperado**:
1. Antes de cambiar de rama, si hay cambios, se intenta resolverlos sin una persona: un paso corto de Clio que los commitee en la rama actual si pertenecen al trabajo hecho, o los descarte si son restos (archivos temporales o ignorables).
2. Si no se pueden resolver, se guardan con `git stash push -u -m "orquestar: <rama> <fecha>"`, se avisa por Telegram con el nombre del stash y se sigue. Nunca se pierde trabajo.
3. Pruebas con un árbol sucio y un cambio de rama pendiente.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario ha pedido este cambio expresamente: el bucle solo debe pararse cuando haga falta una decisión humana. Si hay que cambiar requisitos o escenarios del bucle (orquestar), forma parte del alcance de este bug. Se puede tocar cualquier ruta necesaria.

## Triaje
- A Definición `[SKIP]`: el comportamiento esperado ya está en el bug.
- B Diseño `[SKIP]`: helper único `cambiar_de_rama`.
- C1 Pruebas `[EXEC]`: `skills/orquestar/test_cambio_rama_sucia.py` y ajuste de `tests/test_orquestar.py`.
- C2 Corrección `[EXEC]`: `cambiar_de_rama` en `orquestar.py`.
- D QA `[EXEC]`: Hades APROBADO (`docs/review/code_reviews/B-ADV-0015-code-review.md`).
- E Documentación `[EXEC]`: `skills/orquestar/SKILL.md`, `CHANGELOG.md`.
- F Cierre `[EXEC]`.
- Verificación: `python -m unittest skills.orquestar.test_cambio_rama_sucia tests.test_orquestar`.
