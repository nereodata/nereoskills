---
id: B-ADV-0046
title: "Un fragmento inválido en métricas provoca la caída del orquestador"
type: bug
weight: 0
dificultad: dificil
version: "v1.1.3"
status: planned
depende_de: []
perfil: {artemisa: {harness: codex, model: gpt-6-astra, effort: high}, hades: {harness: codex, model: gpt-6-astra, effort: high}, atenea: {harness: codex, model: gpt-6-astra, effort: high}, estricto: true}
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Incidente Aprexx, bug-fix B-APX-0262, Adevv 1.1.2; petición expresa del usuario"
---

# B-ADV-0046 · Robustez y recuperación del registro de métricas

## Hechos confirmados y reproducción

Aprexx sufrió una caída en bucle() al ejecutar la comprensión directa json.loads sobre las líneas nuevas de orquestar_metricas.jsonl (línea 3727 del motor instalado 1.1.2). Se evita leer_metricas(), que usa metricas.leer_registros(..., tolerar_ultima=True). El registro original tiene 2369 líneas. La línea 2367 contiene exactamente `_s": 0}` entre registros válidos. Las otras 2368 son JSON válido. Se ha reproducido JSONDecodeError: Expecting value: line 1 column 1 (char 0) aplicando esa lectura a una copia íntegra en build/adevv-metricas-repro-0046/orquestar_metricas.original.jsonl de este worktree. SHA256 de la copia y original: 3233e90ef1a56e744326774efe37d5e1488ff14c1c394d01dc93d358f9428cd2.

El diagnóstico original y la copia before-recovery están en C:/Users/Iván Moreno/SW/Aprexx/build/adevv-recovery-20261111/. Solo lectura. La recuperación ya realizada allí conservó el original y retiró exclusivamente el fragmento; el proyecto reanudó sin cambiar la instalación.

registrar() usa append y write(JSON más salto de línea), sin bloqueo visible. Investigar todos los escritores, incluidas verificaciones y gateway, y posibles reescrituras, buffers o escrituras parciales. La concurrencia es una hipótesis, no causa confirmada. No añadir al Git de Adevv las métricas privadas de Aprexx. Usar fixtures mínimos para las regresiones.

## Requisitos del usuario

1. Centralizar las lecturas y evitar que una lectura concurrente de un registro incompleto derribe el bucle.
2. Diferenciar una última línea en escritura de corrupción intermedia.
3. Ante corrupción intermedia, diagnosticar archivo y número de línea, conservar evidencia y permitir recuperación controlada. No ignorar ni borrar datos silenciosamente.
4. Garantizar escrituras completas y serializadas entre motor, agentes, verificaciones y gateway, con protección multiproceso y comportamiento coherente ante fallo parcial.
5. Preservar consumo, costes, verificaciones y estados. No inventar ni duplicar registros durante la recuperación. Revisar cursores basados en número de líneas al tolerar una cola parcial o al recuperar un archivo.
6. Añadir regresiones para cola parcial, fragmento intermedio, escritores concurrentes y reanudación sin repetir trabajo completado. Incluir consumidores normales del motor y pasos completados antes de un fallo de lectura.

## Restricciones y cierre

No modificar los archivos activos de Aprexx ni su copia de evidencia. Trabajar exclusivamente en Adevv y copias o fixtures. Mantener las causas del productor y del lector diferenciadas hasta tener evidencia. Hades debe revisar los contratos, pruebas y corrección con el perfil potente fijado, manteniendo el alcance del hotfix. Este bug forma parte de v1.1.3 y debe quedar corregido y validado junto a B-ADV-0044 y B-ADV-0045 antes de instalarla.
