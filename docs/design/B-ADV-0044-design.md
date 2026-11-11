# B-ADV-0044 · Avance entre intentos del orquestador

El bucle observa el entregable del paso antes y después de invocar el arnés. Desarrollo observa el árbol de producto, incluidos código, pruebas, documentación y especificaciones sin confirmar. Las carpetas configuradas de fichas aportan su estado operativo. Los informes canónicos del ID aportan su dictamen formal. Las notas de la ficha y el resumen de versión quedan fuera de la comparación. Análisis observa los artefactos que produce cada paso. Una respuesta incorporada renueva los intentos de su ID.

Las métricas de Hades permiten distinguir una revisión sin dictamen de una reserva que sí lo emite. La comparación se hace dentro de cada invocación. La cuota mantiene su vía de espera. Los intentos con revisión técnica pendiente se cuentan por paso e ID, independientemente del proveedor. Al alcanzar `--reintentos` el motor devuelve una parada técnica con el ID y deja el WIP en su sitio. La recarga transmite esos contadores. Un arranque manual empieza otra tanda y conserva Git, el registro de preguntas y las métricas.

Ante un error del arnés, desarrollo exige estado completado, commit nuevo, árbol limpio y aprobación canónica vigente sobre el último cambio de producto. En análisis se comprueba la transición que satisface el paso. Un cambio parcial sigue la recuperación de errores de B-ADV-0011.

Selección, recuperación y preflight contrastan el dictamen con el producto al completar el ID o al emitir una revisión posterior. Hades recibe una huella SHA-256 de las entradas Git de producto y la declara en el informe de código. Para informes históricos se toma el producto del primer commit de la secuencia que mantiene el mismo veredicto. Así, una nota en el informe conserva la acreditación anterior y el cierre de otra tarea conserva las revisiones ya válidas.

El transporte entrega la respuesta de Hades para reconocer su declaración formal. La salida normal sin dictamen prueba la siguiente reserva elegible. Cada ejecución exterior que propaga un fallo de revisión conserva sus tokens y la marca técnica. El diagnóstico de suite mantiene su contrato de respuesta JSON y su validador propio.

## Impacto y comprobación

- `bucle` es el consumidor de producción de `firma`. Sus comparaciones de progreso deben observar el paso original aun cuando cambie la selección posterior. `arbol` y la identidad de las evidencias de verificación conservan el contrato exacto de contenido.
- La decisión compartida de cierre en desarrollo gobierna las salidas por error y por cuota del revisor. La prueba antigua `test_completado_en_disco_no_repite` debe aportar el cierre aprobado que da nombre al caso. La prueba de firma con índice Git real conserva su comprobación del WIP y del índice intacto.
- Se mantienen los perfiles y las cadenas de recuperación de análisis. El agotamiento sin evidencia de fallo técnico sigue su tratamiento anterior. Ninguna decisión de plataforma queda contradicha.
- En la ruta frecuente se obtiene una instantánea Git por observación, con índice temporal. Las regresiones ejercitan las comparaciones en repositorios temporales y acotan por conteo las invocaciones a proveedores. La verificación dirigida y los tiempos de ejecución quedan en la evidencia del triaje.
