---
name: bug-fix
description: Resolución autónoma de anomalías con prueba discriminante, calidad determinista y revisión post-verde proporcional
inputs:
  - modo: (Opcional) interactivo | orquestado
  - bug_id: ID del bug (B-PRJ-XXXX)
outputs:
  - status: completed
  - version: versión de la rama release o hotfix
prerequisites:
  - branch: release/vX.Y o hotfix/vX.Y.Z activa
dependencies:
  - review-code
  - manage-docs
  - commit
---

# Skill: Resolución Autónoma de Bugs (/bug-fix)

Guía ligera para diagnosticar y corregir bugs sin burocracia intermedia.

## 1. Preparación y diagnóstico
- En modo interactivo confirma si es hotfix (`hotfix/vX.Y.Z`) o release (`release/vX.Y`); en modo orquestado trabaja en la rama activa.
- Marca `status: in_progress` y conserva `base_calidad` (`git rev-parse HEAD` previo al arreglo) durante todo el ciclo y sus reintentos. Retoma cualquier WIP o contexto previo existente.
- Localiza la causa raíz en el código real antes de tocar nada, sin subfases ceremoniales ni Gherkin obligatorio.

## 2. Prueba discriminante y corrección
- Añade o ajusta una prueba ejecutable directa (`unittest` con proveedores simulados) que discrimine el fallo original (en refactors de deuda sin fallo funcional, valida el contrato unificado).
- Implementa la corrección mínima y limpia, verificando con `adevv orquestar --verificar "<comando>"` hasta dejar en verde tanto la prueba nueva como las regresiones relacionadas.
- Ejecuta `adevv orquestar --calidad --base <base_calidad> --aplicar`: aplica escritura disponible y comprueba formato y lint mediante el verificador de evidencia. Si cambia contenido, repite las pruebas afectadas.

## 3. Revisión post-verde proporcional
- Si el arreglo toca superficies críticas (permisos, persistencia/recuperación, cuotas, publicación) o viene exigido por diagnóstico de cierre, ejecuta revisión conjunta post-verde con `adevv orquestar --agente hades --revision code --prompt-file <mandato>`.
- Si queda fuera de superficies críticas (o no toca código), documenta `docs/review/code_reviews/<ID>-code-review.md` con `**Veredicto:** N/A` y `Motivo: fuera de superficies críticas` (o `Motivo: sin cambios de código`) junto con la evidencia verificada.

## Cierre
1. Aplica el destino de eventuales hallazgos 🟡/🔵 (`resolver`, `registrar` con `/bug-add` sin versión, o `descartar`).
2. Repite `adevv orquestar --calidad --base <base_calidad> --aplicar` y acredita sin escritura el árbol final mediante `--verificar`. Solo en verde: pasa a `status: completed` (añadiendo nota en `docs/review/versions/vX.Y-revision.md` en modo orquestado), verifica el cambio final y ejecuta commit semántico `fix` (`/commit`); cualquier fallo devuelve el estado a `in_progress`.
