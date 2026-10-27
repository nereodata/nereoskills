# Revisión de código: T-ADV-0025

- **Revisor:** Hades. **Fecha:** 2026-10-27. **Ronda:** 2, reevaluación del delta completo de producción.
- **Base:** `0f287d4`, declarada en el triaje.
- **Artefactos:** diff completo desde esa base de `skills/orquestar/orquestar.py`, `skills/orquestar/metricas.py` y `skills/telegram_gateway/gateway.py`, con contexto de sus consumidores de producción.
- **Contrato:** CA-M-1..4, triaje y `docs/design/T-ADV-0025-design.md`; reglas de capas y DEC-P03/P09/P10 de `docs/requirements/platform_plan.md`.
- **Aislamiento:** no se revisaron pruebas ni se reutilizan sus puntuaciones como juicio de producción. No se ejecutaron pruebas, suite, compilación ni verificador de calidad durante esta revisión.

## Veredicto: APROBADO

Media **9,00/10**, sin hallazgos pendientes. H-01 y H-02 quedan **resueltos**; no se identifican hallazgos nuevos en el delta completo revisado. Aprobación del delta de producción dentro del alcance indicado; no certifica CA-M-5 ni el cierre de versión.

## Análisis estático

Se acepta la evidencia aportada y anotada, sin repetir verificaciones:

| Control | Resultado y límites |
|---|---|
| Compilación | `python -m py_compile skills/orquestar/orquestar.py skills/orquestar/metricas.py skills/telegram_gateway/gateway.py`: verde registrado para el árbol `395ab182c4018f957e2b6e54fc077c1fcfdccf0b`, `2026-10-27T01:03:20`. Acredita sintaxis/compilación, no tipado. |
| Espacios y conflictos de diff | `git diff --check`: verde registrado para el mismo árbol, `2026-10-27T01:03:20`. No equivale a un formateador. |
| Calidad por tarea | Ejecución comunicada por el invocante: `python skills/orquestar/orquestar.py --calidad --base 0f287d4`, sin escritura. **Formato omitido y lint omitido por ausencia de herramientas configuradas/disponibles**, según la salida comunicada y la anotación en el triaje. No se presentan como herramientas ejecutadas en verde. |
| Motor usado | Se acepta el motor fuente del árbol para la orden de calidad: la CLI instalada activa es 0.6.0 y no reconoce `--calidad`, según el invocante. La sustitución conserva la base declarada y el modo de solo comprobación. No se solicita actualizar la instalación para esta revisión. |
| Tipado | No se aporta ejecución de un comprobador de tipos; no se infiere de `py_compile` ni se declara verde. |
| Secretos y seguridad | Inspección del delta: no se observan credenciales nuevas, interpolación en shell ni deserialización YAML insegura. No se aporta salida de un escáner de secretos; no se atribuye una ejecución inexistente. |
| Dependencias | Auditoría de dependencias N/A: no cambia ningún manifiesto de dependencias. `ctypes`, `pathlib` y `tomllib` pertenecen a stdlib; Python >= 3.11 es el runtime del plan de plataforma. |

La verificación verde localizada de pruebas se acepta como antecedente del invocante, sin examinar pruebas, repetirla ni extenderla a suite completa. El registro JSONL conserva esa ejecución con código 0 en el mismo árbol, `2026-10-27T01:03:37`.

## Puntuaciones

| Criterio | Nota | Evaluación |
|---|---:|---|
| Corrección | 9 | Fallback explícito, resolución compartida y semántica de PID coherente. La lectura física conserva U+2028 y el fallo de un candidato TOML ya no impide intentar YAML. |
| Seguridad | 9 | Conserva contención del destino de recarga, validación de versión activa y propiedad antes de limpiar/transferir PID; YAML seguro y procesos sin shell. |
| Conformidad | 9 | Extracciones y retirada implementadas en las rutas previstas; sin nuevas dependencias externas ni inversiones de capas. Las correcciones conservan los contratos de lectura y de respaldo previstos por el diseño. |
| Calidad | 9 | Una utilidad canónica por responsabilidad, wrappers finos de compatibilidad en gateway y retirada del helper sin consumidores de producción en los motores revisados. |
| Eficiencia | 9 | Comprobaciones de vida locales y resolución sin barridos del almacén. El lector común vuelve a iterar el archivo sin materializar texto y lista de líneas adicionales; conserva la lista de objetos requerida por los consumidores. Complejidad temporal lineal. |
| Documentación | 9 | Docstrings para las nuevas APIs y modos de lectura; el alcance no requiere instrucciones nuevas de usuario. El modo tolerante conserva el comportamiento previo del bucle, que omite registros inválidos, aunque su nombre destaque la última línea. |
| **Media** | **9,00** | 54 / 6; aprobación exige > 8 y ausencia de críticos/altos. |

## Conformidad por criterio

| Criterio | Evaluación del código de producción |
|---|---|
| CA-M-1 · Versión de respaldo | `version_adevv` conserva prioridad almacén → paquete y sustituye el literal por `version_de_manifiestos` → `desconocida`. La lectura TOML usa `[project].version`; YAML acepta el parser disponible del proyecto. El número deja de necesitar actualización manual en este fallback. El manejo de errores por candidato TOML permite continuar el recorrido y alcanzar YAML si aquel falla; H-02 queda resuelto. La existencia/calidad de regresiones corresponde a review-test y no se revisa aquí. |
| CA-M-2 · Propiedad y vida de PID | `es_propietario_pid` centraliza el contraste con el proceso actual en transferencia, recepción y limpieza. `pid_vivo` parametriza el archivo y reutiliza la comprobación de vida extraída del gateway: Windows conserva cierre del handle y criterio conservador ante acceso denegado; POSIX conserva `kill(pid, 0)` y proceso vivo ante falta de permiso. Gateway mantiene nombres públicos como wrappers con `telegram.pid` por defecto. El bucle usa la misma lógica con `orquestar.pid` en estado, arranque y parada, recuperando marcas muertas/inválidas. Estos cambios ante marcas obsoletas responden a la simetría solicitada por CA-M-2. |
| CA-M-3 · Ruta de versiones | `directorio_version_almacen` concentra la pertenencia a `ADEVV_HOME/versions/<ver>` y la versión de la carpeta; firma y recarga lo consumen. La recarga conserva validación del puntero activo, archivo homólogo existente y destino resuelto dentro de la versión objetivo. No realiza enumeración de versiones ni usa el directorio activo para sustituir la firma del proceso que aún corre la versión anterior. |
| CA-M-4 · Compatibilidad y métricas | Se elimina `detalle_estado`; no hay llamadas restantes en los tres módulos revisados. `vkey` es alias de `metricas.clave_version_numerica`; la normalización de métricas reutiliza esa clave mayor/menor. `leer_metricas` delega al lector canónico en modo tolerante y `consultar` lo usa en modo estricto, conservando errores con número de línea y sin resultados parciales. Gateway comparte `motor.metricas`. La iteración por líneas físicas preserva U+2028 dentro de las cadenas JSON en ambas modalidades, resolviendo H-01. |

Se revisaron también los consumidores modificados de arranque, parada, resumen, parte, recarga y espera de publicación de PID. No se exige nueva DEC para estas extracciones dentro de los motores existentes: siguen las capas y DEC-P03/P09/P10. La adaptación de pruebas antiguas queda expresamente fuera de esta revisión.

## Reevaluación de hallazgos anteriores

### H-01 · 🟡 MEDIA · Delimitación Unicode — resuelto

- **para:** `desarrollador`.
- **destino:** `resolver` (completado).
- **Ubicación actual:** `skills/orquestar/metricas.py:43`, `leer_registros`.
- **Corrección comprobada:** sustituye `read_text(...).splitlines()` por `with ruta.open(encoding='utf-8') as entrada` y `enumerate(entrada, 1)`. La iteración del archivo delimita por saltos físicos, sin tratar U+2028 ni U+0085 dentro de una cadena JSON como nuevos registros. La cadena se entrega intacta a `json.loads` en ambos modos.
- **Preservación del contrato:** conserva archivo ausente → lista vacía, omisión de líneas vacías, aceptación solo de objetos y numeración física de errores. El modo tolerante sigue omitiendo registros inválidos; el estricto sigue rechazándolos antes de agregar o emitir resultados parciales. `leer_metricas` y `consultar` delegan en la misma utilidad con sus modos respectivos. No se materializan copias completas del texto y de sus líneas, por lo que también se elimina el sobrecoste señalado en la ronda anterior.
- **Veredicto del hallazgo:** resuelto por lectura de la solución y de sus consumidores, sin ejecutar experimentos ni revisar pruebas.

### H-02 · 🟡 MEDIA · Un TOML fallido impedía el respaldo YAML — resuelto

- **para:** `desarrollador`.
- **destino:** `resolver` (completado).
- **Ubicación actual:** `skills/orquestar/orquestar.py:98`, `version_de_manifiestos`.
- **Corrección comprobada:** la resolución de padres tiene su propio manejo de errores. Cada candidato TOML se lee y analiza dentro de un `try` local; un error de lectura, decodificación TOML o estructura capturado provoca `continue`, no el retorno que antes abortaba ambos recorridos. Tras agotar TOML, se recorre `task_config.yaml` con su manejo local de errores.
- **Preservación del contrato:** mantiene prioridad de los candidatos TOML frente a YAML, lectura segura del parser disponible y validación de una versión textual no vacía; devuelve `None` solo si no obtiene una fuente utilizable. `version_adevv` conserva almacén → paquete → manifiestos → `desconocida`. En particular, un TOML malformado ya no oculta un YAML válido cuando no hay otra fuente prioritaria.
- **Veredicto del hallazgo:** resuelto. La corrección es local a la cadena de respaldos y no cambia el despacho de versiones ni incorpora dependencias.

## Hallazgos restantes

Ninguno. La reevaluación incluye todos los hunks de producción desde `0f287d4` de los tres módulos, además de las dos soluciones; no se detectan nuevos problemas críticos, altos, medios o bajos que consignar en este alcance.

## Límites y entrega

Segunda revisión solicitada expresamente, realizada sobre el delta completo actualizado de los tres módulos por lectura de diff y contexto de producción. Se comprueban H-01/H-02 y se conserva la conformidad de las extracciones de PID, resolver de versiones, clave numérica, lectura común y retirada del helper. Las conclusiones se deducen del código, sin presentar experimentos ejecutados. No se inspeccionaron archivos de pruebas ni se solicitaron verificaciones redundantes.

Solo se actualiza este reporte. No se modifica código, diseño, configuración, pruebas ni el informe de review-test; no se crea commit.

