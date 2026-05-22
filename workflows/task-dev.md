// turbo-all
---
description: Proxy para el workflow /task-dev
---

> [!IMPORTANT]
> Este workflow es **TURBO**. Todos los pasos serán auto-ejecutados EXCEPTO:
> - Cambios fuera del entorno (workspace)
> - Comandos git peligrosos (ej. `git push`, `git reset --hard`)
> - **Control de Bucles:** Si una secuencia de comandos se repite más de 3 veces sin progreso, detened el modo turbo y pedid permiso manual.

# /task-dev

Has sido invocado para desarrollar una tarea. Sigue estrictamente la skill correspondiente en `../skills/task-dev/SKILL.md`.

### ⚡ Directivas Turbo de Ejecución Asíncrona:
1.  **Fase Roja (TDD)**: Ejecuta automáticamente la validación roja con `python .agents/scripts/auto_dev_loop.py --phase red --test-cmd "<comando-de-test>" --cwd "<ruta-componente>"`.
2.  **Fase Verde y QA**: Escribe la implementación y ejecuta la validación verde con:
    ```bash
    python .agents/scripts/auto_dev_loop.py --phase green --test-cmd "<comando-de-test>" --cwd "<ruta-componente>" --lint-cmd "<linter>" --typecheck-cmd "<typechecker>"
    ```
3.  **Bucle de Feedback Cerrado**: Si el comando anterior falla (Exit 1), no solicites asistencia manual. Abre y lee el reporte generado en `.agents/scratch/qa_feedback.md`, corrige el código y vuelve a ejecutar el comando hasta un máximo de 3 intentos.
4.  **Bloqueos**: Detén el modo turbo y notifica al usuario humano únicamente si superas los 3 intentos sin éxito o necesitas definir requisitos de diseño adicionales.


