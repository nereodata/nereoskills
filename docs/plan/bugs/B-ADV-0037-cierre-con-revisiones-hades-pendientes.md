---
id: B-ADV-0037
title: "El cierre permite publicar una versión con revisiones formales de Hades pendientes"
type: bug
weight: 10
dificultad: media
version: "v1.1.2"
status: planned
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Cierre local de v1.1.1: B-ADV-0032 y B-ADV-0033 quedaron sin informe formal de Hades"
---

# B-ADV-0037: El cierre permite publicar una versión con revisiones formales de Hades pendientes

## 🎯 Descripción del fallo

**Causa raíz:** el cierre local de versión permitió etiquetar `v1.1.1` con
bugs completados sin el informe de revisión formal de Hades. El documento de
cierre reconoció que B-ADV-0032 y B-ADV-0033 permanecían pendientes, pero no
convirtió esa condición en un bloqueo de cierre verificable.

**Comportamiento observado:** `v1.1.1` quedó etiquetada y cerrada localmente
con la suite verde, aunque faltan `docs/review/code_reviews/B-ADV-0032-*` y
`B-ADV-0033-*`. Al abrir `hotfix/v1.1.2`, el selector intenta recuperar esas
revisiones antes del trabajo nuevo porque normaliza las versiones por
mayor/menor y no distingue parches.

**Comportamiento esperado:** una versión no se puede cerrar ni etiquetar si
algún ID completado carece de su revisión formal requerida. Si Hades no está
disponible, la versión queda explícitamente pendiente, con la causa y una vía
de reanudación; no se declara cerrada. Las revisiones pendientes de v1.1.1 se
completan y quedan trazadas en v1.1.2 sin confundir la pertenencia de cada
parche.

## 📋 Reproducir

1. Completar un bug que requiera revisión de código de Hades.
2. Hacer indisponible el perfil de Hades antes de obtener el informe.
3. Intentar cerrar y etiquetar la versión.
4. Comprobar que el flujo actual puede registrar el cierre local pese a la
   revisión ausente y que una rama de parche posterior recupera el ID anterior.

## ✅ Criterios de aceptación

1. El preflight de cierre detecta cada tarea o bug completado sin su informe de
   revisión requerido y no permite etiquetar ni declarar cerrada la versión.
2. La indisponibilidad de Hades deja un estado de revisión pendiente con ID,
   motivo y forma de reanudar, sin simular aprobación con una suite verde.
3. B-ADV-0032 y B-ADV-0033 reciben revisiones formales de Hades trazables
   durante el saneamiento de v1.1.2.
4. El selector distingue `v1.1.1` de `v1.1.2` para no mezclar tareas ni
   revisiones de parches distintos.
5. Regresiones verifican el rechazo del cierre con revisión ausente, la
   reanudación al recuperar Hades y el aislamiento entre dos parches.

## 📋 Evidencias

- `docs/review/versions/v1.1.1-revision.md` reconoce expresamente que las
  revisiones formales de B-ADV-0032 y B-ADV-0033 quedaron pendientes.
- Solo existe el informe de código de B-ADV-0035 entre esos tres bugs.
- `skills/orquestar/metricas.py::clave_version_numerica()` reduce `vX.Y.Z` a
  `(X, Y)`, por lo que el selector asocia ambos parches al mismo bloque.

## Triaje de alcance

- Subfase A: Definición — `[EXEC]`; contrato de cierre bloqueado y semántica
  de pertenencia de parches.
- Subfase B: Diseño — `[EXEC]`; fuente de verdad de revisión requerida y
  modelo de claves de versión completo.
- Subfase C1: Pruebas — `[EXEC]`; regresiones de preflight, indisponibilidad y
  aislamiento `v1.1.1`/`v1.1.2`.
- Subfase C2: Corrección — `[EXEC]`; impedir el cierre incompleto y corregir
  el selector.
- Subfase D: QA — `[PENDIENTE]`; Hades revisa el delta y sanea los informes
  pendientes de B-ADV-0032 y B-ADV-0033.
- Subfase E: Documentación — `[EXEC]`; documentar el estado pendiente y la
  recuperación.
- Subfase F: Cierre — `[PENDIENTE]`; solo tras preflight con todas las
  revisiones acreditadas.
