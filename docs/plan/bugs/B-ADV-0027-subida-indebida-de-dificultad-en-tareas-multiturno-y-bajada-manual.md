---
id: B-ADV-0027
title: "reintentos_acumulados sube la dificultad en tareas multiturno con progreso y deshace las bajadas manuales en el Markdown"
type: bug
weight: 50
dificultad: media
version: "v1.1.0"
status: planned
origen: "Incidencia detectada en Afinn (T-AFN-0139) y comunicada por el usuario (2026-11-06)"
created_at: 2026-11-06
updated_at: 2026-11-06
---

# B-ADV-0027: `reintentos_acumulados` sube la dificultad en tareas multiturno con progreso y deshace las bajadas manuales en el Markdown

## 🎯 Descripción del Fallo

**Causa raíz:** En `skills/orquestar/orquestar.py` (`reintentos_acumulados`, líneas 1370–1393, y `comprobar_promocion`, líneas 1396–1411):
1. **Acumulación incondicional de `pasos` aunque haya progreso o `APROBADO` de Hades:** Mientras que `rech` se pone a `0` cuando Hades emite un veredicto distinto de `RECHAZADO` (`APROBADO`), el contador `pasos` suma toda entrada `tipo == 'paso'` sin cuota agotada (`not f.get('sin_cuota')`) y solo se reinicia al encontrar un evento `tipo == 'promocion'`.
2. **Ignorancia de bajadas manuales de `dificultad` en el frontmatter del Markdown:** `reintentos_acumulados` y `rechazos` solo reinician sus contadores cuando leen un evento `tipo == 'promocion'` en `orquestar_metricas.jsonl`. Si una persona rebaja manualmente `dificultad:` en el fichero `.md` de la tarea o bug (por ejemplo, de `dificil` o `media` a `sencilla`), en el siguiente turno se siguen leyendo las ejecuciones y rechazos acumulados en el histórico (incluidos los ocurridos tras la última promoción), provocando que `comprobar_promocion` vuelva a subir la dificultad inmediatamente.

**Comportamiento observado:**
- En cualquier tarea que se ejecute en varios lotes/turnos (como `T-AFN-0139`, donde cada turno cierra un lote con `APROBADO` de Hades y realiza un commit parcial dejando la tarea `in_progress`), al tercer turno exitoso (`pasos > 2`) el bucle la sube de `sencilla` a `media`, y tras otros 3 turnos exitosos la sube de `media` a `dificil`.
- Cuando se corrige manualmente `dificultad: sencilla` en el Markdown de una tarea que ya tenía promociones y decenas de pasos registrados en `orquestar_metricas.jsonl`, el siguiente turno del bucle deshace el cambio manual y la vuelve a subir.

**Comportamiento esperado:**
1. **Criterio de subida:** no contabilizar como atasco los turnos de desarrollo que producen progreso o aprobación. En concreto, `pasos` solo debe reflejar ejecuciones de paso sin progreso ni aprobación (reiniciando `pasos = 0` cada vez que un paso produzca progreso en el árbol o un `APROBADO` de Hades), o bien promover en `comprobar_promocion` por `rech >= tope` y pasos seguidos sin progreso.
2. **Respeto al cambio manual en el Markdown:** si `dificultad_de(root, iid)` en el Markdown es menor que la dificultad registrada en el último evento `tipo == 'promocion'` (o en las últimas ejecuciones) de esa tarea en `orquestar_metricas.jsonl`, tratarlo como un reinicio de contadores (`pasos = 0`, `rech = 0`) y persistir/respetar ese nuevo nivel base para que los pasos históricos previos a la bajada manual no vuelvan a disparar una promoción automática.

## 📋 Reproducir

1. **Subida indebida en tarea multiturno con progreso:**
   - Crear una tarea con `dificultad: sencilla` y `status: in_progress`.
   - Registrar en `orquestar_metricas.jsonl` 3 turnos de `task-dev` donde cada turno tiene progreso en disco y `veredicto: APROBADO` de Hades, manteniendo la tarea `in_progress`.
   - Invocar `comprobar_promocion(root, iid)`: devuelve `(True, '3 ejecuciones de paso')` a pesar de que todos los turnos avanzaron y fueron aprobados.
2. **Reversión de bajada manual de dificultad:**
   - Promover una tarea de `sencilla` a `media` y luego a `dificil`, y registrar 3+ ejecuciones de paso en `dificil`.
   - Editar manualmente el frontmatter del fichero `.md` de la tarea a `dificultad: sencilla`.
   - Ejecutar el siguiente turno de `bucle()` o `comprobar_promocion(root, iid)`: lee las ejecuciones posteriores a la última promoción y vuelve a subir la tarea automáticamente.

## 📋 Evidencias

- `skills/orquestar/orquestar.py`: funciones `rechazos` (líneas 1358–1367), `reintentos_acumulados` (líneas 1370–1393), `comprobar_promocion` (líneas 1396–1411), `agotado_estricto` (líneas 866–875) y llamada en `bucle` (líneas 2868–2873).
- Caso real reportado en el proyecto Afinn (`T-AFN-0139`).
