# Revisión de pruebas: T-ADV-0025

- **Revisor:** Hades. **Fecha:** 2026-10-27. **Ronda:** 5, final.
- **Contrato:** CA-M-1..4 y triaje de `docs/plan/tasks/T-ADV-0025-limpieza-de-deuda-menor-v03-v06.md`; `docs/design/T-ADV-0025-design.md`.
- **Artefactos:** `skills/orquestar/test_deuda_menor.py`, `test_firma_telegram.py`, `test_recarga.py`, `test_metricas.py`, `test_estado_agentes.py` y `skills/telegram_gateway/test_gateway_fondo.py`.
- **Alcance:** los seis archivos indicados, incluida su preparación, y evidencia roja. Esta ronda comprueba la corrección de H-07 y su contexto en las pruebas; conserva H-01..H-06, la evaluación de los seis archivos de las rondas anteriores y la evidencia roja histórica. Sin inspección de producción. Sin `.feature` nuevo, conforme al triaje A `[SKIP]`.

## Veredicto: APROBADO

Media **9,00/10**, sin hallazgos pendientes. H-01..H-07 quedan **resueltos**. No se detectan hallazgos nuevos en la corrección.

## Puntuaciones

| Criterio | Nota | Evidencia |
|---|---:|---|
| Cobertura | 9 | Cubre ambos manifiestos, desconocida, precedencias, resolver compartido, PID, delegación de métricas e informe soportado. Incluye TOML malformado con respaldo YAML y U+2028 literal en lectura tolerante, lectura estricta y consulta agregada. |
| Aserciones | 9 | Resultados concretos y comprobaciones de delegación/identidad; oráculo numérico independiente y errores JSONL con línea. La cuota vencida se comprueba ahora en la línea del modelo y con el formato porcentual actual. |
| Rojo correcto | 9 | Salida previa detallada: siete pruebas, tres fallos y cuatro errores por contratos aún ausentes; carga y preparación alcanzadas. Las comprobaciones posteriores a la primera excepción y las nuevas regresiones se valoran por lectura, sin atribuirles rojo individual observado. |
| Estabilidad | 9 | Temporales, limpieza, reloj fijado y simulación de vida de PID. Los procesos reales de recarga son locales y tienen esperas acotadas. El PID ajeno se deriva del propio y no puede coincidir con él. |
| **Media** | **9,00** | Se cumple media > 8, sin críticos/altos. |

## Reevaluación de hallazgos anteriores

| Hallazgo | Estado | Evidencia y evaluación |
|---|---|---|
| H-01 · Centralización no discriminada | **resuelto** | `test_deuda_menor.py:53` añade un espía del resolver y exige dos llamadas al consultar firma y recarga, además de sus resultados concretos. En el caso de PID verifica delegación de propiedad/vida desde gateway a su motor con argumentos. En `:109` exige `vkey('v1.20.4') == (1, 20)` e identidad con la utilidad canónica. En `:118` observa `leer_registros` en los modos tolerante y estricto. `test_metricas.py:94` aporta además ordenación numérica independiente (`v0.10` frente a `v0.3`). Estas comprobaciones discriminan helpers añadidos sin consumidores; no se exige volver a demostrar por análisis de producción lo que corresponde a review-code. |
| H-02 · Matriz de PID insuficiente | **resuelto** | `test_deuda_menor.py:71` recorre ambos nombres y ambas APIs: archivo ausente, contenido inválido, entero muerto mediante doble, entero vivo mediante doble, propiedad ajena y propia. Exige consulta de vida con el entero esperado. `test_gateway_fondo.py` cubre reserva, rechazo de duplicados vivos, recuperación de marcas y limpieza del propietario incluso con error; `test_recarga.py` protege las marcas del sucesor. Se conserva la evaluación de la ronda 2. |
| H-03 · Causa del rojo no acreditada | **resuelto** | `T-ADV-0025-red.txt` conserva nombres, trazas, resumen y comando del rojo anterior a producción. Muestra literal `0.5.0` frente a YAML/desconocida, presencia del helper que debe retirarse y ausencia de las nuevas APIs de PID, resolver y clave canónica. Los módulos se cargan y las fixtures llegan a las comprobaciones del contrato. |
| H-04 · Respaldo YAML sin prueba | **resuelto** | `test_deuda_menor.py:34` crea únicamente `task_config.yaml` en una raíz temporal, bloquea la importación del paquete y exige `2.3.4` a partir de `project.version: v2.3.4`. No hay `pyproject.toml` en esa fixture. |
| H-05 · Negativa de cuota con formato antiguo | **resuelto** | `test_estado_agentes.py:94` selecciona mediante `next(...)` la línea que empieza por `codex/m1:`; su ausencia también falla. Exige `0.0% consumido (0 / 10000000 tokens en 5 h)` y rechaza `agotado` en esa misma línea. Conserva las aserciones de espera global y `15 min`. Ya discrimina una cuota vencida mostrada como agotada en el formato actual. **para:** `desarrollador` (resuelto). |
| H-06 · Posible colisión del PID ajeno | **resuelto** | `test_deuda_menor.py:83` define `pid_ajeno = os.getpid() + 1`, escribe ese valor y lo usa en los resultados y argumentos esperados de consulta de vida. Mantiene los dobles de proceso vivo/muerto y la propiedad falsa para ambas APIs; después verifica el PID propio. El valor ajeno es positivo y distinto del propio, sin depender de que exista un proceso externo. **para:** `desarrollador` (resuelto). |
| H-07 · Unicode válido sin comprobar en modo estricto | **resuelto** | `test_deuda_menor.py:113` escribe un U+2028 literal dentro de una cadena JSON y un LF al final. Antes de sobrescribir la fixture exige igualdad exacta del objeto y de la cadena tanto en `orquestar.leer_metricas` como en `metricas.leer_registros(self.root)` (modo estricto por defecto). Además, `metricas.consultar(self.root, [], 'todas')` debe devolver una fila. La conservación exacta de la cadena se comprueba en las lecturas; la consulta acredita aceptación e integración en el agregado, cuyo contrato no devuelve el campo `comando` original. Mantiene después el rechazo de JSONL parcial con línea 2 y las comprobaciones de delegación de ambos modos. **para:** `desarrollador`; **destino:** `resolver` (resuelto). |

## Cobertura del alcance completo

| Criterio | Pruebas y contratos protegidos |
|---|---|
| CA-M-1 · Versión de respaldo | `test_deuda_menor.py` comprueba TOML, YAML y desconocida sin paquete, y exige respaldo YAML ante TOML malformado. `test_firma_telegram.py` conserva almacén → paquete → manifiesto, usa fixtures TOML con sección `[project]` y sustituye el respaldo antiguo por desconocida. Las versiones sintéticas distintas (`1.7.3`, `2.3.4`, `0.8.0`) y el caso sin fuentes impiden perpetuar el literal antiguo sin acoplarse al número de release actual. Firma, idempotencia y envío simulado protegen el consumidor visible. |
| CA-M-2 · PID compartido y simétrico | Matriz y espías en `test_deuda_menor.py`; `test_gateway_fondo.py` verifica lanzamiento, no duplicación, marcas inválidas/muertas, fallo de lanzamiento, parada, reserva gestionada y limpieza. `test_recarga.py` verifica transferencia de propiedad, conservación del propietario si falla y no borrado de las marcas del sucesor. |
| CA-M-3 · Resolver único | Espía y resultados de firma/recarga en `test_deuda_menor.py`. `test_recarga.py` conserva detección y reversión, destinos/punteros inválidos, exclusión del checkout, transferencia de argumentos/estado/PID, fallos de publicación y lanzamiento, prioridad de parada y transferencia real entre procesos Python locales. |
| CA-M-4 · Compatibilidad y métricas | Ausencia de `detalle_estado`, identidad de clave y delegación de lectura en `test_deuda_menor.py`. `test_metricas.py` verifica filtros/orden, agregados con resultados numéricos, CSV, costes y rechazo íntegro de JSONL corrupto con línea. `test_estado_agentes.py` invoca ahora `informe_agentes`, mantiene dificultad/esfuerzo/reservas/escalada, cuota y espera global, consulta sin escrituras y registros del bucle/agente. La negativa de cuota vencida ya usa el formato soportado y comprueba específicamente la línea del modelo. La fixture U+2028 comprueba conservación exacta del registro y su cadena tanto en lectura tolerante como estricta, y aceptación mediante `metricas.consultar` con una fila agregada. |

El triaje C1 y su comando final incluyen ahora los seis módulos revisados. No se exige un escenario BDD adicional ni la suite completa en esta fase. CA-M-5 y la corrección de producción no se certifican mediante este veredicto.

## Nuevas regresiones revisadas

- **TOML malformado → YAML**, `test_deuda_menor.py:43`: crea un script temporal, un TOML con cabecera `[project` sin cierre y un YAML válido con `project.version: v2.3.4`. Bloquea la importación del paquete y exige exactamente `2.3.4`. No simula el parser ni la función evaluada; discrimina tanto propagación de errores como retorno prematuro de desconocida. El nombre menciona imposibilidad de lectura, pero el caso ejercitado específicamente es sintaxis TOML inválida, no permisos del sistema. Es estable y pertinente a CA-M-1 y su diseño de respaldos.
- **U+2028 dentro de JSONL físico**, `test_deuda_menor.py:113`: el escape Python `\u2028` se materializa como carácter literal al escribir UTF-8; no queda como escape JSON ASCII en el archivo. Hay un solo objeto y un LF final. Exige que `leer_metricas` devuelva el objeto completo con la cadena `uno\u2028dos` intacta. La aserción detecta pérdida del registro o fragmentación de su cadena. Después reescribe el archivo con la fixture parcial previa y conserva sus comprobaciones de delegación/modos. La raíz temporal, los datos fijos y la ausencia de procesos/red adicionales mantienen estabilidad. La cobertura Unicode alcanza ahora ambas lecturas con igualdad exacta y la consulta mediante una fila agregada; H-07 queda resuelto. Las llamadas añadidas no simulan el lector ni modifican la fixture entre consultas, por lo que ejercitan realmente cada vía y mantienen el aislamiento temporal.

## Hallazgos restantes

Ninguno. H-01..H-06 conservan su estado resuelto y H-07 se cierra por las aserciones concretas descritas en la tabla. No se revisa ni se determina aquí el estado de hallazgos de review-code.

## Evidencia y límites

El rojo detallado previo contiene **7 tests, 3 failures y 4 errors**. Los cuatro errores son dos subcasos de PID sin API compartida, resolver ausente y clave canónica ausente. Los tres fallos son retirada de `detalle_estado`, respaldo YAML y desconocida. No hay error de sintaxis, importación del módulo de pruebas o preparación de temporales; los `AttributeError` señalan APIs nuevas exigidas por el diseño. El caso TOML ya pasa como preservación de comportamiento. No se afirma que todas las aserciones posteriores a esos errores se ejecutaran en rojo. La evidencia histórica no incluye el nuevo test de TOML malformado ni la aserción Unicode añadida: su capacidad discriminante se evalúa por las fixtures y resultados exigidos, y su ejecución actual queda respaldada por el verde anotado. No se atribuye a estas dos regresiones un rojo observado que el archivo no contiene.

Se acepta la verificación verde actual aportada y registrada mediante `adevv orquestar --verificar`, sin repetirla. Los tres registros corresponden al mismo árbol **`395ab182c4018f957e2b6e54fc077c1fcfdccf0b`**:

- `2026-10-27T01:03:20`: `git diff --check`, código 0.
- `2026-10-27T01:03:20`: `python -m py_compile skills/orquestar/orquestar.py skills/orquestar/metricas.py skills/telegram_gateway/gateway.py`, código 0.
- `2026-10-27T01:03:37`: `python -m unittest skills.orquestar.test_deuda_menor skills.orquestar.test_firma_telegram skills.orquestar.test_recarga skills.orquestar.test_metricas skills.orquestar.test_estado_agentes skills.telegram_gateway.test_gateway_fondo`, código 0, 17 s.

Esta evidencia actual sustituye como referencia verde final a los registros citados en las rondas anteriores. La compilación y `diff --check` no se presentan como lint ni tipado. Se conserva íntegra la valoración de la evidencia roja previa y no se modifica `T-ADV-0025-red.txt`.

Solo se actualiza este informe. No se ejecutaron pruebas, compilación, lint ni chequeos adicionales; no se inspeccionó ni modificó producción, no se modificaron pruebas y no se creó commit.


