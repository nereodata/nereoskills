# Revisión de pruebas — B-ADV-0004

**Veredicto: APROBADO**

Fecha: 2026-10-25. Revisor: Hades. Skill aplicada: `/review-test` de Adevv 0.5.0. Segunda revisión.

## Alcance y evidencia

Reevaluación estática de los cambios de `skills/orquestar/test_codex_resume_usage.py` respecto de H1, H2 y H3 del reporte anterior, contrastados con el contrato de `docs/plan/bugs/B-ADV-0004-codex-resume-sandbox-y-doble-conteo-tokens-cache.md`. El triaje omite BDD por tratarse de un arreglo interno; el contrato de referencia es el propio bug. Se revisaron también la preparación de los nuevos casos y el helper de subsecuencias.

La salida roja aportada corresponde a cinco pruebas, con tres fallos por aserción: presencia indebida de `--sandbox`, entrada 1000 en vez de 200 y entrada 100 en vez de 0 cuando la caché supera la entrada. No presenta errores de importación ni de fixtures. Los controles de sesión nueva y de valores ausentes/nulos pasan; no necesitan fallar contra la versión previa.

No se ha inspeccionado el código de producción ni repetido la ejecución. No se aporta evidencia de lint o tipado sobre las pruebas; esta revisión no certifica esos controles.

## Puntuaciones

| Criterio | Nota | Evaluación |
| --- | ---: | --- |
| Cobertura | 9/10 | Cubre ambas reproducciones, sesión nueva, límite inferior, caché cero, ausente y nula, y entrada nula. Queda sin caso explícito la entrada ausente, pendiente de H2. |
| Aserciones | 9/10 | Verifica métricas observables, conservación de caché, salida y sesión. Los pares de argumentos se comprueban contiguos y con valor exacto. El caso 100/300 exige cero y distingue una resta simple, que devolvería -200. |
| Rojo correcto | 10/10 | Los tres fallos aportados corresponden al comportamiento del bug, sin fallos de preparación. La discriminación frente a una resta sin límite se deduce del valor esperado; no se afirma haber ejecutado esa mutación. |
| Estabilidad | 9/10 | JSONL fijo, iterador y mock nuevos por prueba o subcaso, y parche acotado de `subprocess.Popen`. No se invoca CLI real ni se depende de esperas o red. El helper es determinista y el módulo se localiza mediante `__file__`. |

**Media: 9,25/10.** Supera 8 y no quedan hallazgos críticos ni altos; procede aprobar con el pendiente medio indicado.

## Reevaluación de hallazgos anteriores

### H1 — 🟠 ALTA — Resuelto

`test_lanzar_codex_limite_max_cero_cuando_cache_supera_entrada` usa `input_tokens=100` y `cached_input_tokens=300`, exige `entrada == 0` y conserva `cache_leida == 300`. Una resta sin límite inferior no satisface la aserción. La evidencia roja confirma el fallo contra la contabilidad original (100 en vez de 0).

### H2 — 🟡 MEDIA — Persiste parcialmente

`test_lanzar_codex_casos_limite_ausentes_y_nulos` conserva caché cero y añade caché nula, caché ausente y entrada nula. Falta el caso de **clave `input_tokens` ausente**, pedido en la revisión anterior y contemplado por el contrato. Ninguno de los cuatro subcasos omite esa clave; una lectura obligatoria con `uso['input_tokens']` podría superar estos casos y fallar ante su ausencia.

- **Ubicación:** tabla `casos` de `test_lanzar_codex_casos_limite_ausentes_y_nulos`.
- **Destino:** resolver. **Responsable:** desarrollador.
- **Cambio recomendado:** añadir, por ejemplo, `({"cached_input_tokens": 50}, 0)` y conservar la comprobación del código de salida y de `entrada`.
- **Impacto en el veredicto:** no bloqueante por severidad media; no se declara H2 completamente resuelto.

### H3 — 🟡 MEDIA — Resuelto

`es_subsecuencia_contigua` compara ventanas consecutivas de la lista. Las dos pruebas lo aplican a `['--sandbox', 'workspace-write']` y `['-c', 'sandbox_mode="workspace-write"']`, respectivamente. Se conserva además la prohibición de `--sandbox` en reanudación. El `-c` de otra configuración ya no basta para satisfacer la aserción.

## Hallazgos nuevos

Ninguno en el delta revisado. Esta aprobación corresponde a la calidad de las pruebas; no certifica la implementación ni su ejecución en verde.
