# T-ADV-0039 · Resultado de una llamada

## Responsabilidades

`adevv/llamadas.py` representa el resultado, la identidad lógica de una revisión y la decisión de reserva o espera. El identificador de invocación conserva cada ejecución. El objetivo, las entradas, el ítem, el paso y el rol identifican el trabajo que puede ratificarse. Una identidad incompleta conserva invocaciones independientes.

El proceso de un rol publica su resultado atómico en un canal estable del trabajo dentro del directorio Git. Cada invocación escribe un archivo distinto y registra su llamada padre. El padre recibe estos resultados al terminar su agente y los combina con los intentos antiguos que carecen de canal. Las métricas conservan los intentos y sus consumos. Una correlación incompleta queda indicada. Los canales permanecen disponibles para diagnóstico tras un corte. La precedencia sigue el inicio de la llamada para que una espera concurrente tardía conserve su posición anterior a una ratificación.

## Impacto

- `agente()` conserva su código de retorno CLI. Los lanzamientos de roles generan además un resultado y usan el objetivo explícito indicado por `--revision`. La huella de producto acredita las entradas y excluye el mandato temporal. Los dictámenes de diagnóstico utilizan el identificador de solicitud.
- `bucle()` suministra el canal y el identificador padre a cada paso y consume el resultado de sus revisiones. La ratificación reemplaza la espera anterior de la misma revisión. Las esperas de objetivos diferentes sobreviven.
- `diagnostico_suite.solicitar()` recibe el mismo contrato y conserva la solicitud y sus evidencias mientras espera cuota.
- Las firmas existentes de `ejecutar()`, `lanzar()`, `agente()` y los registros de consumo siguen siendo compatibles con los llamantes existentes y los proveedores simulados.
- La política común toma estados y segundos de espera. La detección del proveedor convierte su hora al margen restante. La persistencia usa escrituras atómicas por invocación y evita que dos roles escriban el mismo archivo.

## Verificación

La regresión de Afinn conserva las tres llamadas diferenciadas de especificación inicial, ratificación y rechazo de código. Una revisión de pruebas o un registro sin alcance acreditado conserva la espera de especificación. La matriz de las tres entradas comprueba reserva, cuota total, aclaración y fallo técnico. Las regresiones de progreso, perfiles estrictos, sesiones y cierre comprueban compatibilidad.
