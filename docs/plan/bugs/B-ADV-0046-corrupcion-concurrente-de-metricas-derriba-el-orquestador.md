---
id: B-ADV-0046
title: "Un fragmento inválido en métricas provoca la caída del orquestador"
type: bug
weight: 0
dificultad: dificil
version: "v1.1.3"
status: blocked
depende_de: []
perfil: {artemisa: {harness: codex, model: gpt-6-astra, effort: high}, hades: {harness: codex, model: gpt-6-astra, effort: high}, atenea: {harness: codex, model: gpt-6-astra, effort: high}, estricto: true}
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Incidente Aprexx, bug-fix B-APX-0262, Adevv 1.1.2; petición expresa del usuario"
pendiente_de: especificador
---

# B-ADV-0046 · Robustez y recuperación del registro de métricas

## Hechos confirmados y reproducción

Aprexx sufrió una caída en bucle() al ejecutar la comprensión directa json.loads sobre las líneas nuevas de orquestar_metricas.jsonl (línea 3727 del motor instalado 1.1.2). Se evita leer_metricas(), que usa metricas.leer_registros(..., tolerar_ultima=True). El registro original tiene 2369 líneas. La línea 2367 contiene exactamente `_s": 0}` entre registros válidos. Las otras 2368 son JSON válido. Se ha reproducido JSONDecodeError: Expecting value: line 1 column 1 (char 0) aplicando esa lectura a una copia íntegra en C:/Users/IVNMOR~1/AppData/Local/Temp/adevv-metricas-repro-0046/orquestar_metricas.original.jsonl, fuera del checkout. SHA256 de la copia y original: 3233e90ef1a56e744326774efe37d5e1488ff14c1c394d01dc93d358f9428cd2.

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

## Triaje

- base_calidad: `aaf7a5e7c1402141e3df6bcf8dbdf3e6a9a6517d`
- A [EXEC] Especificar cola en curso, corrupción visible, recuperación y continuidad en orquestacion.feature.
- B [EXEC] Diseñar bloqueo multiproceso, publicación, recuperación y cursores.
- C1 [EXEC] Regresiones con registros sintéticos y con el bucle sobre un repositorio temporal.
- C2 [EXEC] Centralizar lectores y escritores. El bucle cuenta líneas físicas y decodifica el delta directamente. Las búsquedas de sesión y el diagnóstico de revisión también leen por separado. Motor, agentes, verificador y gateway escriben mediante registrar sin exclusión mutua. No consta qué produjo el fragmento del incidente.
- D [EXEC] Hades revisa contrato, pruebas y corrección en sus fases respectivas.
- E [EXEC] Documentar el diagnóstico y el procedimiento de recuperación local.
- F [EXEC] Cerrar en la rama hotfix/v1.1.3 tras verificar el delta y el dictamen canónico.
- Verificación al cierre: `python -m unittest skills.orquestar.test_registro_metricas skills.orquestar.test_metricas skills.orquestar.test_deuda_menor.DeudaMenorTests.test_version_numerica_y_lectura_jsonl_tienen_implementacion_comun skills.orquestar.test_progreso.ProgresoTests.test_reanuda_con_metricas_corruptas`. Cubre lectura, exportación estricta, recuperación concurrente, contabilidad y selección del paso tras el cierre.

## Hallazgo del lector compartido actual

metricas.leer_registros(root, tolerar_ultima=True) actualmente hace continue ante cualquier JSONDecodeError o fila no objeto, incluso en una línea intermedia. Sustituir la comprensión directa por ese lector sin corregir su semántica incumpliría el requisito de diagnóstico y conservación de corrupción intermedia. La copia íntegra privada está fuera del checkout para impedir su inclusión accidental en un commit; las pruebas distribuidas deben usar fixtures mínimos sin contenido privado.

## Reproducción sintética concurrente en este equipo

Ocho procesos Python 3.12 escribieron 400 filas cada uno en un archivo temporal común, siguiendo exactamente open(a, encoding=utf-8), write(json.dumps(ensure_ascii=False) más salto de línea) y close, sin otros escritores ni reescrituras. Cada objeto llevaba worker, seq, texto Unicode y duracion_s. Todos los procesos devolvieron 0. De 3200 filas esperadas, el archivo tiene 2737 líneas, 2339 objetos válidos únicos, 398 líneas inválidas y 313 líneas con UTF-8 roto. Se reprodujo primero UnicodeDecodeError al leer el archivo completo como UTF-8. Evidencia sintética y writer.py en C:/Users/IVNMOR~1/AppData/Local/Temp/adevv-metricas-escritores-llr8esky; SHA256 de metrics-0.jsonl: 94ab875357f4e07cbc4b613a0abfdd0ccb99e7554af4fc70321b85736bb68f5e. Esto confirma que la concurrencia basta para corromper el patrón actual en este equipo, sin atribuir retrospectivamente el fragmento de Aprexx a un escritor concreto. Extender el contrato de diagnóstico y conservación a UnicodeDecodeError y bytes parciales, con línea y evidencia binaria exactas. La regresión debe usar identidades únicas y contrastar cardinalidad y contenido, no solo que el JSON sea parseable. Ningún archivo de Aprexx fue modificado.

## Hallazgo de Hades enrutado
- Destino: `especificador`
- Decisión: ejecutar especificar
- Evidencia: Hades rechazó /review-spec (8,0/10). H-01 alta: distinguir la recogida antes de recuperar (diagnóstico con archivo y línea, cierre conservado) del relanzamiento; una ejecución total del paso. H-02 alta: con V1 ya observada, recuperar acortando el registro, añadir V2 y observar exactamente V2 una vez. H-03 alta: solapar recuperación y escritura confirmada; preservar todos los eventos válidos una sola vez y la evidencia binaria del fragmento. H-04 media, resolver: cuantificar y conservar un coste distinto de cero tras dos recuperaciones. Ejecutar especificar sobre los escenarios y triaje conservados en wip/B-ADV-0046, commit 58b5774, con el dictamen literal en docs/review/spec_reviews/B-ADV-0046-spec-review.md. Mantener base_calidad aaf7a5e7c1402141e3df6bcf8dbdf3e6a9a6517d.
