// turbo-all
---
description: Generador de mensajes de commit estándar
---

> [!IMPORTANT]
> Este workflow es **TURBO**. Todos los pasos serán auto-ejecutados EXCEPTO:
> - Cambios fuera del entorno (workspace)
> - Comandos git peligrosos (ej. `git push`, `git reset --hard`)
> - **Control de Bucles:** Si una secuencia de comandos se repite más de 3 veces sin progreso, detened el modo turbo y pedid permiso manual.

# /commit-message-generate

Has sido invocado para generar una propuesta de mensaje de commit analizando los cambios actuales.

1. Usa la herramienta `view_file` en `../skills/commit-message-generate/SKILL.md` (o la ruta correspondiente si estás en un proyecto consumidor) para leer las instrucciones.
2. Basándote únicamente en el hilo de conversación actual, identifica la tarea/bug y los cambios realizados.
3. Genera una única propuesta de mensaje siguiendo el estándar **Aprexx v3.0**.

