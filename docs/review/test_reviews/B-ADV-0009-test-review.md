# Revisión de pruebas — B-ADV-0009

**Veredicto: APROBADO. Puntuación media: 9/10.** Sin hallazgos nuevos ni pendientes en las pruebas.

## Alcance y aislamiento

Reevaluación en modo orquestado, 2026-10-27, aplicando Hades y `/review-test` de `C:/Users/Iván Moreno/.adevv/versions/0.6.1/` e ignorando el modelo del frontmatter.

Objeto: delta completo respecto a HEAD de `tests/test_updater.py` y `tests/test_sync.py`, incluidos fixtures, preparación de estados y aserciones. Se reutiliza el análisis de la ronda aprobada 9/10 y se coteja el delta desde su árbol `73acedd5f47b715a71dc974bfca100a24f624fb4`: solo añade `test_instalar_reutiliza_version_sin_puntero_y_no_la_limpia`; sync permanece idéntico. No se reabre cobertura ya aprobada sin cambios.

Contratos de contraste: especificación aprobada, alcance y triaje de B-ADV-0009 y F-01. Se contrasta la nueva recuperación local con RF-F01-01 y la conservación de versiones del bug, sin leer producción, diseño ni el informe de código. H1 de review-code se recibe únicamente como contexto de la regresión que debe discriminar la prueba.

No se ejecutaron pruebas, imports ni comprobaciones estáticas. No se relanzaron `py_compile`, `git diff --check` ni suite completa. Solo se actualiza este informe, sin modificar pruebas o estados ni crear commit.

## Evidencia reutilizada

Fuentes: `docs/review/test_reviews/B-ADV-0009-red.md` y `orquestar_evidencias.jsonl`.

| Evidencia | Árbol y fecha | Resultado y alcance |
| --- | --- | --- |
| `python -m unittest tests.test_updater.TestUpdaterIntegrationAndCli.test_instalar_reutiliza_version_sin_puntero_y_no_la_limpia` | `6fe10f18e9af657bccc9e9a02e4e95ccc8a7269d`, 06:34:22 | Código 1; el resumen acredita una prueba con un fallo por activo None, esperado no nulo. |
| `python -m py_compile tests/test_updater.py tests/test_sync.py` | `9033896c0f6c93bebed043f200cec516a203c9fa`, 06:34:43 | Código 0, reutilizado. |
| `git diff --check` | Mismo árbol, 06:34:44 | Código 0, reutilizado; anterior a este informe actualizado. |

Los comandos constan mediante `--verificar`. Se cotejaron los dos archivos actuales con el árbol estático: updater `65df45c1f4e2c6f8b6399045f6bdc7e1bc118e43`, sync `9ae17d28fb2ffb7de4f13ba3a6f29574536e4d6c`; coinciden. También se cotejaron los tests con el árbol de la ejecución roja: no hay diferencias. El fallo rojo corresponde así a la prueba actual, sin depender de una ejecución antigua de otra variante del caso.

Se conserva la evidencia de discriminación anterior del resto del delta, resumida en el documento rojo y evaluada en la ronda previa: instalación con bucles, consumo heredado, protección de copias, rollback CLI compatible, paso ancestro y materialización local. No se presenta esa evidencia como una nueva ejecución íntegra de los dos módulos. No hay linter ni tipado configurados según la información entregada.

## Puntuaciones

| Dimensión | Nota | Valoración |
| --- | --- | --- |
| Cobertura | 9/10 | Mantiene instalación con bucles, puntero, copias y versiones intactas, recuperación heredada, rollback y recarga. Añade el efecto compuesto de instalar localmente sobre carpeta existente sin puntero, incluida su conservación tras la orden. |
| Aserciones | 9/10 | Comprueba código de salida, puntero no nulo, versión concreta y bytes del marcador. Mantiene las comprobaciones previas de registros, configuración, avisos en stderr y archivo sobrescribible. |
| Rojo correcto | 9/10 | La regresión nueva falla por ausencia del puntero exigido; el fixture crea expresamente la carpeta y retira el puntero. No hay fallo de sintaxis, carga o preparación documentado. |
| Estabilidad | 9/10 | Hogar temporal, autoactualización desactivada, detector de bucles controlado y versión de la CLI fijada a la del fixture. Sin reloj, red ni proceso hijo real añadidos. |

**Media: (9 + 9 + 9 + 9) / 4 = 9/10**, superior a 8 y sin hallazgos críticos ni altos.

## Revisión de la regresión añadida

`test_instalar_reutiliza_version_sin_puntero_y_no_la_limpia` parte del fixture existente: carpeta `versions/0.1.0` con manifiesto válido y estado aislado. Añade un archivo marcador, elimina `active.json`, desactiva la actualización automática y fija la versión local de la CLI a 0.1.0. Ejecuta `main_cli(["instalar"])` sin sustituir materialización, activación ni limpieza.

El marcador no se recrea durante la acción. Por tanto, exigir su contenido intacto después de la orden discrimina una eliminación o sustitución destructiva de la carpeta. Exigir `get_active_info()` no nulo y versión 0.1.0 discrimina devolver la carpeta sin reconstituir el puntero. El código de salida 0 exige completar la operación, no solo tolerar una excepción.

El contrato es coherente con F-01: la instalación debe quedar utilizable y RF-F01-01 conserva la versión cuando la actualización automática está desactivada. El escenario CA-F01-01 describe la primera instalación con búsqueda de una versión posterior; el nuevo caso desarrolla un límite local de recuperación, sin sustituir ese camino ni exigir consulta remota. Restaurar el puntero a la misma versión y conservar su carpeta desarrolla la política de conservación de versiones del bug, sin introducir un requisito incompatible.

La evidencia roja falla primero por puntero None. La aserción posterior del marcador sigue siendo necesaria aunque ese fallo impida alcanzarla en la ejecución roja: comprueba de forma independiente la conservación tras la orden cuando la activación se corrija.

## Reevaluación y enrutado

| Hallazgo de review-test anterior | Estado | Para | Destino |
| --- | --- | --- | --- |
| H1 — Avisos nuevos exigidos en stdout | Resuelto; corrección conservada | `desarrollador` | `resolver`: satisfecho, sin pendiente |
| H2 — Falta rollback CLI con bucle vivo | Resuelto; caso compatible conservado | `desarrollador` | `resolver`: satisfecho, sin pendiente |
| H3 — Archivo sobrescribible no observado | Resuelto; aserciones conservadas | `desarrollador` | `resolver`: satisfecho, sin pendiente |

El nuevo caso cubre el contrato comunicado como H1 de review-code. Esta aprobación de pruebas no declara resuelto el defecto de producción: esa resolución corresponde a la corrección y revisión de código posteriores.

## Hallazgos nuevos y salida orquestada

Ninguno. No hay acciones pendientes en las pruebas para `desarrollador`, `especificador` o `humano`, ni hallazgos con destino `registrar` o `descartar`. El delta completo de pruebas permanece aprobado para continuar la corrección. No se exige suite completa ni se acredita implementación en verde con este veredicto.
