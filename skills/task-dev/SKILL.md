---
name: task-dev
description: Ejecución autónoma de una tarea con verificación determinista directa y revisión post-verde proporcional
inputs:
  - modo: (Opcional) interactivo | orquestado
  - task_id: ID de la tarea (T-PRJ-XXXX)
outputs:
  - status: completed
  - version: versión asociada a la rama activa
prerequisites:
  - branch: release/vX.Y o hotfix/vX.Y.Z activa
dependencies:
  - review-code
  - manage-docs
  - commit
---

# Skill: Desarrollo Autónomo de Tarea (/task-dev)

Guía ligera para entregar una tarea (o bloque coordinado) con máxima autonomía en el camino e invariantes deterministas al cierre.

## 1. Preparación y contexto
- Valida que la rama activa sea `release/vX.Y` o `hotfix/vX.Y.Z` (nunca `main`), pon `status: in_progress` y anota el SHA inicial `base_calidad` (`git rev-parse HEAD`) si aún no consta; consérvalo entre commits y reintentos.
- Si existen cambios previos en el árbol, rama `wip/<ID>` o contexto portable del motor, retómalos en vez de empezar de cero.
- Inspecciona el código existente primero (*delta-first*): decide libremente cómo estructurar la solución sin subfases rígidas (A–E), sin Gherkin obligatorio y sin revisiones intermedias de spec ni de tests en rojo.

## 2. Implementación y verificación directa
- Construye la solución manteniendo módulos cohesivos y añade pruebas ejecutables directas (`unittest` por defecto, con entradas reales y proveedores simulados, sin efectos laterales reales como envíos a Telegram o publicaciones).
- Verifica iterativamente solo las pruebas afectadas mediante `adevv orquestar --verificar "<comando>"` (reutiliza evidencia en verde del mismo árbol).
- Ejecuta `adevv orquestar --calidad --base <base_calidad> --aplicar`: aplica formato en escritura y comprueba formato y lint mediante el verificador de evidencia. Si el formateo modifica archivos, repite las pruebas afectadas.
- Si el cambio afecta documentación viva del usuario, actualízala de forma minimalista (`/manage-docs`).

## 3. Revisión post-verde proporcional
- **Superficies críticas** (permisos, persistencia/recuperación, cuotas, publicación, o política explícita): con todo ya en verde, lanza una única revisión conjunta de código y pruebas con `adevv orquestar --agente hades --revision code --prompt-file <mandato>` y resuelve los 🔴/🟠 del desarrollador.
- **Cambios acotados fuera de superficies críticas** (o tareas sin cambios de código): registra `docs/review/code_reviews/<ID>-code-review.md` con `**Veredicto:** N/A` y `Motivo: fuera de superficies críticas` (o `Motivo: sin cambios de código`) citando los comandos verificados.

## Cierre
1. Si Hades señaló deuda 🟡/🔵: corrige `resolver`, registra `registrar` con `/bug-add` sin versión y omite `descartar`.
2. Tras todos los cambios de código, pruebas, documentación y reporte, repite `adevv orquestar --calidad --base <base_calidad> --aplicar` y acredita el estado limpio sin escritura mediante `--verificar`. Solo en verde: actualiza `status: completed` en la tarea (y anota el resumen en `docs/review/versions/vX.Y-revision.md` en modo orquestado), comprueba la calidad final y haz commit semántico (`/commit`); cualquier fallo devuelve el estado a `in_progress`.
