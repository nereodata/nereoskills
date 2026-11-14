---
name: task-dev
description: Resuelve un objetivo o tarea de principio a fin conforme a la política del proyecto
---

# /task-dev

Entrega el objetivo descrito en la ficha siguiendo `PROJECT.md` (si existe en la raíz del proyecto).

1. **Entender antes de tocar**: Lee la ficha, `PROJECT.md` y el código o contexto previo relacionado (incluidos cambios en curso o notas de relevo). Elige el enfoque proporcional a la naturaleza de la tarea (funcionalidad, refactor, configuración, documentación o investigación).
2. **Verificar con honestidad**: Comprueba que el resultado funciona y no introduce regresiones usando las herramientas y criterios de `PROJECT.md` (pruebas automatizadas, análisis estático o comprobación directa cuando no sea código).
3. **Decidir o escalar**: Resuelve las decisiones técnicas con criterio propio; usa `adevv orquestar --preguntar <ID> "<pregunta>" --contexto "<contexto>"` únicamente si falta un recurso externo o una decisión de producto que no deba asumirse.
4. **Cerrar limpio**: Deja el repositorio limpio en su rama de trabajo, marca `status: completed` en la ficha con una nota breve de qué hiciste y cómo lo verificaste, actualiza documentación de usuario solo si quedó desfasada (`/manage-docs`) y haz commit semántico (`/commit`).
