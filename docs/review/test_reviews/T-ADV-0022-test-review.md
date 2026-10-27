# T-ADV-0022 — Reevaluación de pruebas

**Veredicto vigente: APROBADO** (9/10; incluye la reevaluación del delta de regresión de QA)

Revisión en modo orquestado conforme a Hades y `/review-test` de la versión 0.6.0. Alcance: `skills/orquestar/test_calidad.py` contra `skills/orquestar/features/calidad_delta.feature`, el triaje de `docs/plan/tasks/T-ADV-0022-formato-y-lint-en-cada-tarea.md` y los hallazgos de la revisión anterior. Se contrastan también el resumen de rojo y su captura. No se lee producción ni diseño. No se ejecutan comandos de verificación ni suite completa; se acepta la compilación en verde comunicada mediante `--verificar`. No hay linter ni tipador configurados.

## Puntuaciones

| Criterio | Nota | Fundamento |
| --- | ---: | --- |
| Cobertura | 9/10 | Delta, resolución, ejecución, contratos de ambos flujos y de Hades, reutilización e invalidación de evidencia cubiertos con casos relevantes. |
| Aserciones | 9/10 | Argumentos exactos, orden de ejecución, trazas independientes y condiciones normativas de cierre; comprobación efectiva de ausencia de nuevas invocaciones. |
| Rojo correcto | 9/10 | Captura real: 19 pruebas, 39 errores, sin fallos textuales; funcionalidad provisional con NotImplementedError y opciones CLI pendientes. |
| Estabilidad | 9/10 | Repositorios temporales, herramientas Python locales y trazas en `.git` que no alteran el contenido del árbol observado. Sin servicios ni esperas reales. |
| **Media** | **9/10** | Sin hallazgos críticos o altos pendientes. |

## Estado de los hallazgos anteriores

### H-01 — Resuelto — Reutilización e invalidación de evidencia

**Referencias:** `herramienta`, `llamadas`, `test_evidencia_reutiliza_e_invalida_contenido_base_y_comando` y `test_escritura_invalida_verde_anterior_sobre_arbol_resultante`.

La traza `.git/llamadas.jsonl` observa ejecuciones reales de formato y lint, independientemente del archivo de evidencia y del uso de shell. La primera ejecución exige ambas etapas; la repetición exige que el número de invocaciones permanezca en dos. Un commit vacío prepara otra base con el mismo árbol y se comprueba que usarla requiere nuevas ejecuciones sin modificar el contenido. Las variaciones posteriores de contenido y configuración exigen nuevas invocaciones. El caso específico de escritura parte de un verde, exige cambio de árbol y la secuencia formato → lint → escritura → formato → lint; la siguiente revisión sin escritura reutiliza el resultado sin nuevas llamadas. Se elimina la debilidad que permitía reejecutar y aun así satisfacer la prueba de reutilización.

**para:** desarrollador. **destino:** resolver. **Estado:** resuelto, sin acción pendiente.

### H-02 — Resuelto — Contratos de cierre y de Hades

**Referencias:** `test_instrucciones_de_ambos_flujos_y_hades_exigen_calidad`, `test_sin_escritura_conocida_solo_ejecuta_comprobadores` y pruebas de ejecución existentes.

Para ambos flujos, las aserciones se sitúan en la subfase de cierre, exigen el comando de calidad antes de `status: completed`, cierre solo en verde, retorno a `in_progress` ante fallos, escritura y uso de `--verificar`. Para Hades se exige ausencia de escritura, prohibición de `--aplicar`, comprobación de ambas etapas mediante `--verificar` y devolución al desarrollador con destino `resolver`, sin aprobación hasta corregir el fallo. Esto constituye cobertura de contrato textual para flujos expresados como skills, complementada por las pruebas de comportamiento del helper; no se presenta como ejecución de agentes. El nuevo caso sin escritura declarada solicita aplicación y exige únicamente formato y lint, con resultado satisfactorio.

**para:** desarrollador. **destino:** resolver. **Estado:** resuelto, sin acción pendiente.

### H-03 — Resuelto — Trazabilidad del rojo

**Referencias:** `docs/review/test_reviews/T-ADV-0022-red.md` y `.git/T-ADV-0022-red.log`.

La captura tiene 66.042 bytes, contiene salida diagnóstica y termina con `Ran 19 tests` y `FAILED (errors=39)`. El resumen actual explica la captura directa de stdout/stderr. El rojo corresponde a funcionalidad provisional y opciones CLI pendientes; no se atribuye a imports, sintaxis ni fixtures. No hay fallos textuales en el resultado actual. La aprobación de estas pruebas no acredita que la funcionalidad esté implementada o en verde.

**para:** desarrollador. **destino:** resolver. **Estado:** resuelto, sin acción pendiente.

## Hallazgos nuevos

Ninguno. Las correcciones mantienen el aislamiento de las fixtures y aportan comprobaciones discriminantes de los contratos señalados. La cobertura restante de delta, argumentos, precedencia, deducción conservadora, filtrado, errores y omisiones conserva su validez dentro del alcance revisado.

## Reevaluación: regresiones exigidas por la revisión de código (delta desde `7696358`)

Alcance: solo `test_regresion_hades_delta_largo` y `test_regresion_hades_validation_vacio` de `skills/orquestar/test_calidad.py`, contrastadas con H-01 y H-03 de `docs/review/code_reviews/T-ADV-0022-code-review.md` y con `calidad_delta.feature`. No se ha leído producción ni diseño. No se ha relanzado nada; uso las evidencias en verde comunicadas para el árbol `bb5a4bd183` (triaje, compilación y `git diff --check`). La cobertura aprobada antes no se reabre.

| Criterio | Nota | Fundamento |
| --- | ---: | --- |
| Cobertura | 9/10 | H-01: 100 ficheros nuevos cuyos nombres llevan espacios y acentos, más un cambio en `uno.py`; se recorren formato y lint con el verificador real. H-03: `validation:` vacío. |
| Aserciones | 9/10 | Comprueban que la orden de evidencia tiene menos de 8191 caracteres en cada etapa, que la herramienta recibe los 100 nombres literales en ambas etapas y en orden formato → lint, y que una segunda ejecución reutiliza la evidencia: no hay llamadas nuevas y las órdenes son idénticas, así que identidad y reutilización se mantienen. En H-03, que el resultado es 0 en lugar de error. |
| Rojo correcto | 9/10 | `.git/T-ADV-0022-hades-red.log`: 2 fallos de aserción por la funcionalidad, no por import, sintaxis ni fixture. Uno es `17247 not less than 8191`; el otro, `1 != 0`. `.git/T-ADV-0022-hades-green.log`: 2 OK. |
| Estabilidad | 9/10 | Repositorio temporal y herramienta Python local que deja su traza en `.git`. El límite se comprueba por longitud, así que no depende del sistema operativo; sin red ni esperas. |
| **Media** | **9/10** | Sin hallazgos críticos ni altos. |

### Hallazgos nuevos

#### 🔵 BAJA — R-01: el caso de `validation` vacío no demuestra del todo que equivale a ausencia de configuración

**Referencia:** `test_regresion_hades_validation_vacio`.

Sin manifiestos, «ausencia» y «se omite todo» dan el mismo 0. Una implementación que tratara el bloque vacío como «no deducir» también pasaría. Basta con añadir `[tool.ruff]` (o un script npm reconocido) y comprobar que se deduce el comando. Otra opción es comprobar la omisión con el motivo «ausencia de herramientas».

**destino:** resolver (barato y sin riesgo). No bloquea.

**Estado: resuelto.** La prueba añade ahora `[tool.ruff]` con `validation:` vacío y exige exactamente `ruff format --check uno.py` y `ruff check uno.py`, así que distingue «vacío equivale a ausencia». Las pruebas siguen aprobadas, sin pendientes.

La cobertura aprobada antes conserva su validez. Las nuevas pruebas no alteran las fixtures compartidas.

Solo se actualiza este informe. Sin cambios en otros archivos ni commit.

**Veredicto actual: APROBADO.**
