# T-ADV-0022 — Reevaluación de pruebas

**Veredicto vigente: APROBADO**

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

Solo se actualiza este informe. Sin cambios en otros archivos ni commit.

**Veredicto actual: APROBADO.**
