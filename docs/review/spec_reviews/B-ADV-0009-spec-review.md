# Revisión de especificación — B-ADV-0009

**Veredicto: APROBADO.** H1, H2 y H3 quedan resueltos. Media: **9/10**. Sin hallazgos críticos ni altos pendientes.

## Alcance y evidencia

Reevaluación en modo orquestado, con Hades y `/review-spec` de la instalación 0.6.1, ignorando el modelo del frontmatter. Se revisa exclusivamente el delta respecto a `HEAD` de:

- `docs/requirements/requirements.md`.
- `docs/requirements/funcionalidades/F-01_instalacion_y_sincronizacion.md`.
- `docs/requirements/funcionalidades/F-03_actualizacion_automatica.md`.
- `tests/features/actualizacion_automatica.feature`.
- `tests/features/instalacion_y_sincronizacion.feature`.

Contexto: alcance y triaje de B-ADV-0009 y reporte anterior obtenido de `cd22e3f:docs/review/spec_reviews/B-ADV-0009-spec-review.md` en `wip/B-ADV-0009`. Los escenarios anteriores se usan como contexto, sin reabrir comportamientos ajenos al delta. La decisión humana autoriza sustituir los contratos de aplazamiento y sus escenarios; prevalece sobre la prohibición genérica de alterar escenarios existentes. DEC-P13 se toma exclusivamente como decisión normativa de separar instalación y copias globales, sin evaluar diseño.

Se reutiliza la verificación documental `adevv orquestar --verificar "git diff --check"`, registrada en `orquestar_evidencias.jsonl:418`: árbol `dcd26b25b3eee65ce14dbbba39ca8dbd7d253f57`, fecha `2026-10-27T06:01:09`, código 0. No se repite. Esta evidencia corresponde al delta recibido antes de añadir este informe; no acredita ejecución funcional ni verifica el informe nuevo. La evidencia roja del WIP no se atribuye a este árbol.

No se ha leído implementación, pruebas unitarias ni diseño; no se han ejecutado pruebas de desarrollo ni suite completa. El cotejo textual de Gherkin forma parte de la lectura documental.

## Comprobaciones obligatorias

| Criterio | Resultado | Motivo |
| --- | --- | --- |
| No regresión | ✅ | Las modificaciones de los escenarios de aplazamiento, gateway y vuelta atrás están autorizadas por el bug. No se eliminan escenarios ajenos a ese cambio. |
| Coherencia | ✅ | CE-3, R2, tabla de resultados, RF-F01-11 y RF-F03-06/11 separan instalación versionada de copias globales. La recarga se exige a motores desde v0.5.0; los anteriores requieren reinicio manual. RF-F03-07 remite a F-01, cuya guarda condiciona la sincronización. |
| Trazabilidad | ✅ | Se conservan las etiquetas CA-F03-01/03/04/05/13 revisadas en el informe anterior y su correspondencia con los criterios funcionales modificados por autorización del bug. No se crean etiquetas CA inexistentes. Las adiciones trazan RF-F03-06, RF-F03-08 y RF-F01-11, respectivamente: consumo heredado, conservación de versiones en uso y protección de copias globales. |
| Delta real | ✅ | Cambia la instalación con bucles, sin duplicar la resincronización anterior: el esquema nuevo añade las órdenes explícitas y `--forzar`; los escenarios añadidos observan el consumo heredado sin consulta y la reutilización sin sobrescritura. |

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Claridad | 9/10 | Se distingue instalación, recarga cooperativa y copia global; la precedencia excluye expresamente la fila transversal como resultado terminal. |
| Completitud | 9/10 | Incluye actualización automática y manual, rollback compatible, motores antiguos, gateway, recuperación heredada, conservación de versiones y sincronización posterior. La tabla conserva SIN_RED y FALLIDA también con bucles. |
| Testeabilidad | 9/10 | Versiones concretas, puntero activo, archivos y registros intactos y límites de recarga observables. El origen controlado estabiliza las tres variantes de sincronización. |
| Estructura | 9/10 | Los escenarios permanecen en los archivos de sus funcionalidades y las variantes de órdenes comparten un esquema. |

**Media: 9/10**, superior a 8; todas las obligatorias se cumplen.

## Reevaluación de hallazgos anteriores y enrutado

| Hallazgo | Gravedad anterior | Estado | Para | Destino |
| --- | --- | --- | --- | --- |
| H1 — Capacidad de recarga incompatible con versiones de partida | 🔴 CRÍTICO | **Resuelto** | `especificador` | `resolver` — corrección satisfecha, sin acción pendiente |
| H2 — Condiciones y avisos incoherentes en la tabla normativa | 🔴 CRÍTICO | **Resuelto** | `especificador` | `resolver` — corrección satisfecha, sin acción pendiente |
| H3 — Versión final del esquema dependiente del origen | 🟡 MEDIA | **Resuelto** | `especificador` | `resolver` — corrección satisfecha, sin acción pendiente |

### H1 — Resuelto

En `tests/features/actualizacion_automatica.feature:38` el bucle parte de 0.5.0 y adopta 0.6.1; en `:57` el gateway también parte explícitamente de 0.5.0 y adopta 0.6.1 entre vueltas de polling, preservando la respuesta en curso. El rollback de `:117` parte de un bucle 0.6.1 y vuelve a 0.5.0: tanto origen como destino soportan la recarga. El caso antiguo de `:48` fija un motor anterior a v0.5.0 y pide reinicio manual, conservando sus archivos. Las copias de estos escenarios en F-03 reflejan las mismas precondiciones y resultados.

El escenario añadido «Volver a una versión que sigue en uso» usa 0.1.0, pero solo exige conmutar el puntero sin sobrescribir su carpeta: no exige recarga cooperativa a ese motor antiguo y no reproduce H1.

### H2 — Resuelto

`requirements.md:100` establece que la fila 7 es transversal y no detiene la evaluación hacia 8/9. En `:110` solo aplaza la copia global; APLICADA y FALLIDA (`:111` y `:112`) admiten expresamente instalación con o sin bucles. Se conserva la precedencia de SIN_RED y el tratamiento de errores, plazo y discrepancia de versión.

El aviso de APLICADA distingue copias globales pendientes de sesiones que pueden usar copias ya sincronizadas, y recarga desde v0.5.0 de reinicio manual de motores anteriores, identificando los procesos afectados. El consumo heredado de `:114` intenta instalar aunque haya bucles, no vuelve a consultar la lista y borra el estado en APLICADA/FALLIDA; SIN_RED sigue siendo un resultado independiente. F-03 E8/E10 y el caso del gateway antiguo E11 están alineados con esta tabla.

### H3 — Resuelto

`tests/features/instalacion_y_sincronizacion.feature:119` fija un origen controlado accesible cuya última versión publicada es 0.2.0. La precondición se aplica a `instalar`, `instalar --forzar` y `actualizar`, y se mantiene en la segunda orden del escenario. Ninguna variante puede actualizar a una publicada superior a la esperada. Se observan archivos y registros en 0.1.0 mientras existe el bucle y la sincronización con 0.2.0 tras terminar el último.

## Coherencia de las copias Gherkin

El bloque Gherkin de F-03, desde CA-F03-01 hasta CA-F03-16, coincide con sus escenarios en `tests/features/actualizacion_automatica.feature`, salvo la sangría. Esto incluye versiones de partida y destino, avisos, ejemplos de la ventana y rollback corregidos.

Los dos escenarios añadidos de recuperación heredada y reutilización de una versión figuran solo en el `.feature`; desarrollan RF-F03-06 y RF-F03-08 sin contradecir el bloque documental. La diferencia de cobertura entre copias no introduce expectativas incompatibles ni deja sin definir esos contratos.

## Hallazgos nuevos

Ninguno. No quedan correcciones pendientes ni recursos externos que solicitar. La aprobación se limita a la especificación del delta; no acredita implementación ni pruebas funcionales. Solo se añade este informe, sin modificar estados, requisitos, escenarios ni crear commit.
