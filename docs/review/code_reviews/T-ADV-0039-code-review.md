# T-ADV-0039 · Revisión de código

**Veredicto:** APROBADO
Producto revisado: 12406bc8ed00959d1c770f942b7a45aef8a9fd820e6e11d5052ca5542ca55eb4

Revisión independiente del delta respecto de `09b10c001aca10bc5426b986d087030680691a05`, incluido el módulo nuevo `adevv/llamadas.py`. Fecha: 2026-11-12. La huella de producto se ha reconstruido sin escritura desde el índice y el objeto Git calculado sin escritura para la última corrección de compatibilidad de `orquestar.py`, mediante las mismas entradas Git modo/tipo/objeto/ruta y exclusiones de `huella_producto()`: carpetas maestras de tareas y bugs, y `docs/review/`. Los informes y cambios posteriores de ficha no alteran esta identidad.


## Análisis estático

- `adevv orquestar --calidad --base 09b10c001aca10bc5426b986d087030680691a05`: retorno 0; **formato y lint omitidos por ausencia de herramientas**. No equivale a una ejecución verde de esas herramientas.
- `git diff --check`: correcto para el delta rastreado.
- No cambian manifiestos ni dependencias. No se han observado secretos nuevos.
- El invocante acredita comprobación AST y diff limpios. Sin tipado configurado; no se atribuye un verde a una auditoría automatizada de seguridad no ejecutada.
- No se ha ejecutado la suite completa. La matriz y las regresiones las ejecuta el invocante. Un intento adicional de reproducción mediante el fixture `ProgresoTests` no pudo inicializarse por `PermissionError` al entrar en el temporal del sandbox; no constituye una prueba ejecutada.
- La reproducción mínima en memoria de la precedencia concurrente se ejecutó sobre la versión anterior a la corrección y mostró la espera tardía como pendiente. Es evidencia histórica del defecto RC-3, cerrado después al ordenar por inicio de invocación.

## Contratos de las tres entradas

| Entrada | Contrato observado | Evaluación |
| --- | --- | --- |
| Paso principal `bucle()` | Conserva `ejecutar()` y sus tres valores; entrega canal e identificador padre por entorno, consulta resultados internos y publica un resultado de paso bajo `.git/adevv-llamadas/pasos`. | La adaptación conserva la firma, une resultados por canal con métricas no cubiertas y mantiene los fallos técnicos pendientes. |
| Rol interno `agente()` | Conserva retorno entero CLI; genera invocación, objetivo y huella de entradas; publica `Resultado` atómico cuando hay canal. Conserva métricas por intento y devuelve entrega formal válida de reserva sin propagar cuota anterior. | El resultado es observable por canal; el padre conserva los estados técnicos pendientes y las cuotas independientes. |
| Diagnóstico `diagnostico_suite.solicitar()` | Conserva retorno de dictamen; comunica resultado operativo en `DiagnosticoPendiente.resultado`, canal propio por solicitud y filtro por padre. El bucle usa la cuota de ese resultado. | Conserva el contrato externo y evita confundir otras solicitudes. Una respuesta válida se interpreta con `leer_dictamen`; una inválida conserva evidencia. |

La política `llamadas.recuperacion()` decide reserva, espera o conservación y se usa en las tres entradas. Los detectores y la selección de perfiles permanecen en los adaptadores, de acuerdo con el diseño. La independencia entre consumo del principal y entrega válida de reserva está representada. La revisión adicional incorporó la conservación de fallos técnicos y la combinación de resultados parciales del canal con métricas no cubiertas.

## Correcciones verificadas durante la revisión

- RC-1: el padre mantiene como revisión pendiente cualquier estado no recibido sin espera, incluido `fallo_tecnico`. Se elimina la pérdida de la incidencia al recibir un retorno 0 del transporte principal.
- RC-2: los resultados del canal se unen con las métricas de invocaciones que no publicaron canal. Un directorio histórico ya no borra las esperas nuevas de llamantes compatibles.
- RC-3: `Resultado.iniciada` recoge el comienzo de la invocación; la conciliación ordena por inicio y desempata por resultado. La espera tardía de una invocación anterior ya no sustituye una ratificación que comenzó después. Los datos antiguos conservan su orden previo cuando no acreditan el inicio.

La primera revisión detectó estos tres defectos de prioridad alta. Se han comprobado las correcciones en el código resultante, sin editar producción. La evidencia de la matriz y las regresiones corresponde al invocante.

## Reevaluación del delta final

RC-4 cerrado: también en la combinación canal + métricas se comunica correlación desconocida si el pendiente elegido carece de objetivo o entradas. No quedan hallazgos abiertos.

Se han revisado además estos ajustes finales:

- La huella excluye el archivo temporal del mandato; el objetivo procede únicamente del entorno explícito o de `--revision`, evitando deducir un alcance al mencionar otras revisiones en el texto.
- Las reservas conservan las fuentes anteriores si actualizan el informe, y la espera publica el perfil asociado al vencimiento más cercano.
- Se conserva la salida al publicar una espera y se publica también el resultado de un paso acreditado en disco tras error del transporte.
- `skills/orquestar/SKILL.md` explica el objetivo explícito, la ratificación y el alcance histórico desconocido; el changelog describe el comportamiento. `README.md` no tiene delta y no se ha encontrado una afirmación invalidada por este cambio.
- El invocante acredita una matriz de 12 pruebas correcta. La batería de 208 detectó incompatibilidades que se corrigieron: el fallback técnico nuevo requiere objetivo explícito para conservar el retorno legacy; el diagnóstico-suite activa `solo_respuesta` para validar el JSON propio extraído del envelope del proveedor. Ambas correcciones se han revisado y no introducen hallazgos. La repetición de regresiones tras ellas sigue bajo ejecución del invocante; no se atribuye un verde final todavía.
- Repetidos sobre el delta final: `git diff --check` correcto y puerta `--calidad` con retorno 0, manteniendo las omisiones expresas de formato/lint por ausencia de herramientas.

La identidad canónica del producto revisado figura inmediatamente después del veredicto e incluye las correcciones finales de compatibilidad.

## Puntuaciones

| Dimensión | Nota |
| --- | ---: |
| Corrección | 9 |
| Seguridad | 9 |
| Conformidad | 9 |
| Calidad | 9 |
| Eficiencia | 8 |
| Documentación | 9 |

Media: **8,83/10**. Sin hallazgos pendientes. La aprobación de código no atribuye un verde a las herramientas omitidas ni sustituye la ejecución final de regresiones del invocante.
