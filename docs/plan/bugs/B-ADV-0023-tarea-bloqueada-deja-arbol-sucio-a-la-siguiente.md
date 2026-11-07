---
id: B-ADV-0023
title: "Una tarea bloqueada deja sus cambios sin commitear a la siguiente tarea de la misma rama"
type: bug
weight: 1500
dificultad: media
version: "v1.1.0"
status: completed
origen: "B-ADV-0012/B-ADV-0013 × B-ADV-0015; revisar-version v1.0 (docs/review/versions/v1.0-arquitectura.md), H-02 🟡"
created_at: 2026-10-27
updated_at: 2026-11-07
---

# B-ADV-0023: Una tarea bloqueada deja sus cambios sin commitear a la siguiente tarea de la misma rama

## 🎯 Descripción del Fallo

**Causa raíz:** `bloquear_sin_progreso` (`skills/orquestar/orquestar.py`, hacia la línea 3105) bloquea la tarea con un commit que solo incluye la tarea y la revisión de versión, y sigue con `continue`. La resolución de árbol sucio de B-ADV-0015 solo se ejecuta en `cambiar_de_rama` (línea ~2063), así que no se aplica si la siguiente tarea elegible está en la misma rama `release/`.

**Comportamiento observado:** un intento deja ediciones sin commitear (eso cuenta como progreso, porque `firma` incluye `git status`). Los siguientes intentos no cambian nada y la tarea se bloquea. La siguiente tarea empieza con el árbol sucio de la anterior: su delta de calidad (`base_calidad`, T-ADV-0022) incluye ficheros ajenos y su commit puede arrastrarlos.

**Comportamiento esperado:** tras cada bloqueo local (o antes de cada paso) se aplica la misma resolución de árbol sucio que en B-ADV-0015: Clio resuelve los cambios o se guardan en un stash, con aviso.

## 📋 Reproducir
1. Simular una tarea cuyo primer intento deja un fichero sin commitear y cuyos intentos siguientes no cambian nada, hasta que se bloquee.
2. Con otra tarea elegible en la misma rama, comprobar que el siguiente paso empieza con `git status` sucio.

## 📋 Evidencias
- `docs/review/versions/v1.0-arquitectura.md`, hallazgo H-02.

## Triaje
- base_calidad: db73e8ed8abeb7beab1db80de30822284b6f3732
- A Definición: [SKIP] Contrato existente de aislamiento y resolución de árbol sucio; no cambia requisitos.
- B Diseño: [SKIP] Reutilización local del mecanismo Clio/stash existente, sin decisión arquitectónica nueva.
- C1 Pruebas: [EXEC] Regresión con Git real: tarea y bug dejan cambios, bloqueo y siguiente tarea en la misma rama; Clio, stash y fallo de limpieza.
- C2 Corrección: [EXEC] Extraer resolución común y exigir árbol limpio tras todos los bloqueos locales antes de continuar.
- D QA: [EXEC] Hades sobre el delta completo de B-ADV-0023.
- E Documentación: [EXEC] Contrato de orquestación y changelog.
- F Cierre: [EXEC] Revisión de versión, completed y commit.
- Verificación al cierre: `python -m unittest tests.test_orquestar.BloqueoSinProgresoTests tests.test_orquestar.RecuperacionAnalisisTests skills.orquestar.test_cambio_rama_sucia skills.orquestar.test_perfil_fijado.BucleTests` cubre bloqueos, recuperación y mecanismo compartido; `git diff --check` y calidad del delta. No hay tipador, linter ni escáner de secretos configurados; inspección del delta sin credenciales ni cambios de dependencias.

- Ampliación de verificación: BucleTests de perfil fijado porque dos puntos de bloqueo estricto también deben respetar el resultado de limpieza.
- Rojo confirmado: el test falla en la entrada de la independiente con `?? resto.txt`; evidencia conservada en `orquestar_evidencias.jsonl`.

## Resolución
- Mecanismo Clio/stash extraído a `resolver_arbol_sucio`; se aplica después de persistir cada bloqueo local y antes de cambiar de rama.
- Los cuatro llamadores del bloqueo comprueban el resultado y paran si persisten cambios, conservándolos para recuperación.
- Regresión con Git real, tarea y bug, transición media/difícil, stash de fichero nuevo, edición de revisión preservada y siguiente tarea limpia en la misma rama.
- Hades: pruebas APROBADO (9/10), código APROBADO (9.8/10). Único hallazgo cosmético bajo con destino descartar; sin deuda nueva.
- Verificación: 23 pruebas focalizadas en verde; diff sin errores; formato/lint omitidos por ausencia de herramientas, sin tipador configurado ni cambios de dependencias.
