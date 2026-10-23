---
id: T-ADV-0017
title: "Canal limpio de prompts en --agente (--prompt y limpieza automática de temporales)"
type: funcional
weight: 150
dificultad: sencilla
version: "v0.4.0"
status: planned
depende_de: []
origen: "Evitar que ficheros temporales de mandato a Hades ensucien git status si un paso se interrumpe"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0017: Canal limpio de prompts en --agente (--prompt y limpieza automática de temporales)

## 🎯 Objetivo de Negocio
Evitar que la invocación de subagentes (`adevv orquestar --agente hades ...`) deje ficheros temporales de prompt (`hades_review_*.txt`, `mandato_*.txt`) sin rastrear en la raíz del proyecto que puedan bloquear cambios de rama o contaminar commits si un paso se interrumpe.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Argumento `--prompt` y fichero excluido `orquestar_prompt.txt`):** `skills/orquestar/orquestar.py` acepta `--prompt <texto>` además de `--prompt-file <ruta>` y `stdin` al usar `--agente <rol>`, e incluye `orquestar_prompt.txt` en `PROPIOS` para que quede excluido de git si se usa como fichero de mandato.
- [ ] **CA-M-2 (Auto-limpieza de `--prompt-file` temporal en la raíz):** Cuando se invoca `--agente` con `--prompt-file <ruta>`, una vez leído el contenido, si el fichero está en el directorio raíz del proyecto y no está rastreado por git (`git ls-files --error-unmatch` falla), `orquestar.py` lo elimina automáticamente en un bloque `finally` para garantizar que el árbol de trabajo queda limpio incluso si el subagente falla o se interrumpe por cuota.
- [ ] **CA-M-3 (Pruebas y documentación):** `tests/test_orquestar.py` verifica `--prompt` directo y el borrado automático de `--prompt-file` no rastreado tras ejecutar `--agente`; `skills/orquestar/SKILL.md` documenta `--prompt` y el uso limpio de `--prompt-file`.
