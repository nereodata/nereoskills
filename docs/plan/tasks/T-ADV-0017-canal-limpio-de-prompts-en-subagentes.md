---
id: T-ADV-0017
title: "Canal limpio de prompts en --agente (--prompt y limpieza automática de temporales)"
type: funcional
weight: 150
dificultad: sencilla
version: "v0.4.0"
status: completed
depende_de: []
origen: "Evitar que ficheros temporales de mandato a Hades ensucien git status si un paso se interrumpe"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0017: Canal limpio de prompts en --agente (--prompt y limpieza automática de temporales)

## 🎯 Objetivo de Negocio
Evitar que la invocación de subagentes (`adevv orquestar --agente hades ...`) deje ficheros temporales de prompt (`hades_review_*.txt`, `mandato_*.txt`) sin rastrear en la raíz del proyecto que puedan bloquear cambios de rama o contaminar commits si un paso se interrumpe.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Argumento `--prompt` y fichero excluido `orquestar_prompt.txt`):** `skills/orquestar/orquestar.py` acepta `--prompt <texto>` además de `--prompt-file <ruta>` y `stdin` al usar `--agente <rol>`, e incluye `orquestar_prompt.txt` en `PROPIOS` para que quede excluido de git si se usa como fichero de mandato.
- [x] **CA-M-2 (Auto-limpieza de `--prompt-file` temporal en la raíz):** Cuando se invoca `--agente` con `--prompt-file <ruta>`, una vez leído el contenido, si el fichero está en el directorio raíz del proyecto y no está rastreado por git (`git ls-files --error-unmatch` falla), `orquestar.py` lo elimina automáticamente en un bloque `finally` para garantizar que el árbol de trabajo queda limpio incluso si el subagente falla o se interrumpe por cuota.
- [x] **CA-M-3 (Pruebas y documentación):** Pruebas unitarias en `skills/orquestar/test_agente_prompt.py` (o `tests/test_orquestar.py`, conforme a `DEC-P09` dentro de `skills/`) verifican `--prompt` directo y el borrado automático de `--prompt-file` no rastreado tras ejecutar `--agente`; `skills/orquestar/SKILL.md` documenta `--prompt` y el uso limpio de `--prompt-file`.

## 🔬 Triaje de Alcance
- **Subfase A: Definición** → `[SKIP]` Opciones CLI y lógica interna de auto-limpieza en `skills/orquestar/orquestar.py` detalladas en CA-M-1..CA-M-3 (`DEC-P09`); sin escenarios Gherkin en el motor de orquestación.
- **Subfase B: Diseño** → `[EXEC]` Documento `docs/design/T-ADV-0017-design.md` con las decisiones técnicas de `--prompt`, exclusión de `orquestar_prompt.txt` y auto-limpieza de temporales no rastreados en la raíz en bloque `finally`.
- **Subfase C1: Pruebas (Red Phase)** → `[EXEC]` Pruebas unitarias en `skills/orquestar/test_agente_prompt.py` cubriendo `--prompt`, precedencia/fallback, exclusión de `orquestar_prompt.txt` en git y limpieza automática de `--prompt-file` no rastreado en raíz (preservando rastreados y externos).
- **Subfase C2: Implementación (Green Phase)** → `[EXEC]` Soporte de `--prompt`, inclusión de `orquestar_prompt.txt` en `PROPIOS` y auto-limpieza en `finally` en `skills/orquestar/orquestar.py`.
- **Subfase D: QA** → `[EXEC]` Revisión de Hades (`/review-code`) sobre el delta de la tarea con `adevv orquestar --agente hades`.
- **Subfase E: Documentación** → `[EXEC]` Documentación de `--prompt` y el uso limpio de `--prompt-file` en `skills/orquestar/SKILL.md` y nota de versión en `docs/review/versions/v0.4-revision.md`.
- **Subfase F: Cierre** → `[EXEC]` Cierre de tarea y commit semántico.
- **Verificación al cierre:** `python -m unittest skills/orquestar/test_agente_prompt.py`, `python -m unittest skills/orquestar/test_estado_agentes.py`, `python -m unittest tests/test_orquestar.py -k RolesTests`; verificación estática con `python -m py_compile skills/orquestar/orquestar.py skills/orquestar/test_agente_prompt.py` y `git diff --check`. No hay linter/tipado configurados ni dependencias nuevas.

## 🏁 Resultado y decisiones sin preguntar
- **Verificación en verde:** 20 pruebas unitarias en `skills/orquestar/test_agente_prompt.py`, 8 en `test_estado_agentes.py` y 5 en `RolesTests`; compilación Python limpia y `git diff --check` limpio. Reutilización de evidencia con `adevv orquestar --verificar`.
- **Hades:** `/review-test` APROBADO (8.75/10 en `docs/review/test_reviews/T-ADV-0017-test-review.md`), `/review-code` APROBADO (9.0/10 en `docs/review/code_reviews/T-ADV-0017-code-review.md`).
- **Decisiones sin preguntar:** Precedencia `--prompt` > `--prompt-file` > `stdin`; delimitador `--` en la consulta `git ls-files --error-unmatch -- <ruta>` y discriminación estricta de `res.stderr` para preservar archivos rastreados con guiones iniciales o ante fallos operacionales de git; documentación en `skills/orquestar/SKILL.md` y seguimiento en `docs/review/versions/v0.4-revision.md`.
