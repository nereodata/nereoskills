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

## Triaje operativo

- base_calidad: c29d8c67bdbdc8d587e78faf2dd2025007113ea8
- Se conserva hotfix/v1.1.2, rama autorizada ya abierta. No se publica ni etiqueta.
- A, B, C1, C2, D, E y F: [EXEC], con el alcance descrito arriba.
- Verificación al cierre: `python -m unittest tests.test_revision_release tests.test_orquestar.RevisionProductoTests tests.test_orquestar.OrquestarRegressionTests tests.test_orquestar.SuiteRecoveryTests skills.telegram_gateway.test_cierre_version skills.orquestar.test_metricas tests.test_orquestar.HallazgosHadesRoutingTests skills.orquestar.test_deuda_menor.DeudaMenorTests.test_version_numerica_y_lectura_jsonl_tienen_implementacion_comun`. Cobertura de informes, preflight y selector; métricas conservan su agrupación histórica.
- Calidad: `git diff --check` y `adevv orquestar --calidad --base c29d8c67bdbdc8d587e78faf2dd2025007113ea8`; no hay lint, tipado ni escáner configurados. No cambian dependencias.
- Delta-first CA3: ya existen informes formales RECHAZADO para B-ADV-0032 y B-ADV-0033, con hallazgos enrutados a artemisa en sus fichas. No se simula aprobación ni se duplica su desarrollo dentro de este bug.
- DEC: separar identidad operativa completa de versión de la agrupación estadística mayor/menor. vX.Y equivale a vX.Y.0; parches positivos se aíslan.

## Progreso del intento

- Hades /review-spec: RECHAZADO; H1 y H2 ALTA, H3 MEDIA (resolver), todos para especificador.
- Pruebas preliminares en tests/test_revision_release.py: 9 tests, 10 fallos de aserción esperados contra producción actual mediante `adevv orquestar --verificar "python -m unittest tests.test_revision_release"`; evidencia en orquestar_evidencias.jsonl. No constituyen review-test ni verificación de cierre; se conservan como borrador para ajustar a la nueva especificación.
- Diseño preliminar conservado; no se modificó producción. Subfase A pendiente de corrección por especificador; B/C1 no aprobadas, C2/D/E/F sin completar.

## Hallazgo de Hades enrutado
- Destino: `especificador`
- Decisión: ejecutar especificar
- Evidencia: Hades /review-spec RECHAZADO en docs/review/spec_reviews/B-ADV-0037-spec-review.md. H1 ALTA: concretar ausencia/RECHAZADO, tareas/bugs, entradas validar/cerrar/publicar y varios IDs pendientes. H2 ALTA: provocar indisponibilidad de Hades con pruebas verdes y observar ID, motivo y reanudacion; revalidar tras recuperacion. H3 MEDIA resolver: casos N/A justificado y sin motivo. Decision: ejecutar especificar. Delta y borradores conservados en wip/B-ADV-0037 (e44c13d); produccion sin modificar; pruebas preliminares rojas acreditadas por --verificar. No requiere pregunta humana.

## Resolución de especificación (Atenea, 2026-11-11)

- H1: matriz explícita de 12 ejemplos en `tests/features/publicacion.feature`:
  ausencia/RECHAZADO × tarea/bug maestro completado × preflight local/cierre
  Telegram/publicación por API. Escenario adicional exige enumerar todos los
  pendientes, excluyendo el aprobado. CA1/CA5.
- H2: un escenario provoca falta de cuota al ejecutar revisar-tarea con pruebas
  verdes; exige estado consultable y diagnóstico con ID, causa y reanudación.
  Otro recupera cuota, obtiene APROBADO y reejecuta preflight. CA2/CA5.
- H3: ejemplos N/A justificado por ausencia de código y N/A sin justificación,
  con resultados opuestos. Se retira la condición inejercitada del borrador.
- CA4/CA5: escenarios separados para aislamiento entre parches y equivalencia
  vX.Y/vX.Y.0. Los cinco escenarios anteriores a este bug quedan intactos.
- CA3: los informes formales RECHAZADO ya existentes de B-ADV-0032 y
  B-ADV-0033 satisfacen obtener revisión, pero NO autorizan cerrar sus versiones.
  Sus correcciones siguen en sus IDs; este bug no las implementa.

### Decisiones sin preguntar

- DEC-ESP-01: las tres entradas aplicables son el preflight local de release,
  cerrar por Telegram y publicar mediante la API de release (usada por CLI).
  Se descarta cubrir solo el preflight: una entrada directa podría eludirlo.
  Cada ejemplo parte del resto de condiciones válidas para discriminar el veto.
- DEC-ESP-02: pendiente por indisponibilidad significa estado de revisión
  observable y recuperable; no requiere un nuevo valor de status del backlog.
  Se descarta imponer un almacenamiento o estado interno nuevo desde BDD.
  Falta de cuota es el caso concreto reproducible de indisponibilidad; no se
  sustituye el informe por pruebas verdes ni por disponibilidad recuperada.
- DEC-ESP-03: N/A solo acredita revisión si explica ausencia de código; no basta
  la palabra N/A. Se descarta N/A incondicional por permitir cierre sin revisión.
- DEC-ESP-04: las versiones operativas incluyen parche; métricas mantienen su
  agrupación histórica. Se descarta migrar métricas por quedar fuera de CA4.
- DEC-ESP-05: se especifica el delta sobre el árbol actual, sin restaurar código
  ni tests del WIP. Los tres escenarios de e44c13d eran un borrador rechazado
  ausente de esta rama; se desarrollan sus casos aquí sin retirar escenarios
  aprobados. Artemisa debe adaptar diseño y pruebas preliminares al contrato
  corregido; el rojo anterior no acredita todavía todos los ejemplos nuevos.

### Resultado del paso especificar

- Hades /review-spec: APROBADO, media 9/10; H1, H2 y H3 resueltos,
  sin nuevos hallazgos. Informe guardado literalmente desde la salida del
  revisor, limitado a materiales adjuntos por fallo del acceso local del arnés.
- Verificación acotada mediante --verificar: 45 pruebas existentes del triaje,
  OK. No se ejecutó suite completa ni tests preliminares del WIP; el módulo
  tests.test_revision_release no existe aún en esta rama. La evidencia anterior
  roja se conserva como diagnóstico, no como validación de los ejemplos nuevos.
- Desarrollo pendiente: adaptar diseño y pruebas del WIP a esta especificación;
  completar las revisiones y la corrección con Artemisa. Este paso no implementa
  producción ni pruebas ejecutables ni cierra el bug.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades /review-spec APROBADO (9/10) en docs/review/spec_reviews/B-ADV-0037-spec-review.md: H1, H2 y H3 resueltos por Atenea, sin nuevos hallazgos. Decision: reanudar desarrollo desde la especificacion corregida; adaptar diseno y tests preliminares de wip/B-ADV-0037 sin sobreescribir los artefactos aprobados. Verificacion acotada: 45 pruebas OK; regresiones nuevas pendientes de adaptar.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades review-test RECHAZADO: RT-01 Mayor exige observar referencias locales/remotas y artefactos en preflight, cuota y recuperacion antes de revalidar; RT-02 Media exige diagnostico N/A sin justificacion. Ambos para Artemisa; decision: reanudar desarrollo y corregir pruebas sin cambiar especificacion.


## Resultado de este intento de desarrollo (2026-11-11)

- Se retomaron diseño y pruebas del WIP sin alterar el feature aprobado.
- C1: 15 pruebas ejecutadas mediante `--verificar`, 26 fallos de aserción
  esperados del contrato; sin errores de importación, sintaxis ni fixtures en
  la última ejecución. La matriz Telegram/API usa ocho repositorios/remotos
  bare independientes. El transporte de Hades se simula; no hay red real.
- Compilación de ambas pruebas y `git diff --check`: verdes con `--verificar`.
  No hay herramientas de lint/tipado configuradas. Suite completa no ejecutada.
- Hades `/review-test`: RECHAZADO. RT-01 Mayor y RT-02 Media, ambos para
  Artemisa; informe en `docs/review/test_reviews/B-ADV-0037-test-review.md`.
  El arnés no pudo acceder al disco; el informe se conserva a partir de stdout
  y solo acredita revisión estática de los materiales adjuntos.
- Se ejecutó `--enrutar-hallazgo B-ADV-0037 artemisa`; el comando dejó
  `status: planned` e indicó terminar el paso. No se solicita intervención humana.
- C1 pendiente: añadir snapshots locales/remotos/artefactos al preflight y a
  cuota/recuperación antes de revalidar, y diagnóstico específico N/A sin motivo;
  luego repetir review-test. Adaptar las fixtures operativas identificadas en
  el diseño. C2/D/E/F siguen pendientes, sin cambios de producción ni aprobación
  de código. Documentación pública del comportamiento futuro no se ha aplicado.
