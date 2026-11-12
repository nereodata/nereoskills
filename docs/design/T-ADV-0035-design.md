# T-ADV-0035 · Decisión y espera por tarea

El paso entrega una decisión estructurada en su respuesta final cuando encuentra un impedimento. El motor comprueba el destino y aplica la transición junto al resultado correlacionado de Hades. Una entrega técnica sin responsable, mandato o condición de salida vuelve al agente que la propuso con una solicitud de aclaración. La pregunta humana identifica una elección o recurso del usuario y lleva una clave estable por tarea. Las entradas explícitas de CLI siguen admitiendo sus argumentos históricos.

## Persistencia y despacho

- El motor conserva la transición por rama e ítem en el directorio Git del árbol. La identidad incluye la clave del impedimento y, para una llamada, su objetivo y entradas. El diagnóstico libre puede variar. Una nueva redacción conserva la espera y los contadores de avance.
- El registro de llamadas sigue siendo la autoridad sobre el dictamen y la cuota. Agotar los ejecutables autorizados produce una pausa comprobable mediante la resolución de esos mismos perfiles. La suscripción deshabilitada y la caída del servicio externo permiten volver a probar la condición. El agente recibe la revisión original y su condición al reintentar. Solo una entrega del mismo alcance resuelve la revisión.
- El selector filtra cada ítem en espera antes de ordenar candidatos y mantiene las dependencias. Durante el intervalo de espera se ejecuta trabajo independiente con capacidad. Si debe ceder un árbol modificado, el motor guarda el WIP del ítem en Git y lo recupera antes de volver a despacharlo. Una comprobación de disponibilidad fallida conserva el WIP.
- El registro de preguntas existente serializa la creación y la recepción. Conserva las respuestas incorporadas por clave y admite registros antiguos con identidad basada en la pregunta. Las consultas de preguntas incluyen las respuestas incorporadas. El resumen de estado de cada canal usa el mismo detalle de la decisión.

## Mapa de impacto

`orquestar.bucle` recibe el mensaje del paso y las entregas de `agente`. El punto de aplicación comparte las operaciones de `intervencion` con `--preguntar`, `--enrutar-hallazgo`, el diagnóstico de la suite y la detección posterior al paso. `estado` alimenta bucle, parte de Telegram, controles del gateway y preflight. Una espera vigente impide pasar al cierre. La consulta no lanza proveedores ni ejecuta instrucciones del mensaje. La firma de progreso conserva su alcance sobre el producto. Los plazos se guardan como instantes absolutos y se comparan con el reloj del motor.

`intervencion.consulta` sirve a ambas consultas de preguntas y al resumen de bloqueos. Este último solo incluye preguntas abiertas. El cambio amplía la consulta pública de preguntas al historial respondido. Los consumidores de `listar(root, True)` conservan su filtro. Las revisiones sin objetivo acreditado conservan su tratamiento anterior. El diseño sigue DEC-P09 y el apartado 6 del plan de trabajo. Las reglas de espera global por cuota del revisor pasan a aplicarse cuando se agota el trabajo independiente.

## Pruebas

El bucle trabaja sobre un repositorio temporal real con tres tareas y proveedores simulados. Las pruebas comprueban la selección desde ambos canales, la ejecución de B, la conservación del alcance y el WIP de A y la dependencia de C. Reloj, ejecutables y salida del proveedor se controlan en la frontera. Las consultas del camino frecuente leen las transiciones del árbol una vez por selección y no consultan al proveedor.
