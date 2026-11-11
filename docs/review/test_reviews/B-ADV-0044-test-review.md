**Veredicto:** APROBADO · **9,75/10**

# B-ADV-0044 · Reevaluación C1 de las pruebas de D16, D17 y D18

Las ocho pruebas reproducen cuatro entradas en los dos consumidores exigidos. Las cuatro de `motor.agente` comprueban a qué proveedor se atribuye el dictamen y cuándo interviene la reserva. Las cuatro de `pendientes_cierre` comprueban qué motivo mantiene pendiente la ficha completada.

## Reproducciones y rojo observado

Cada celda de consumidor corresponde a una prueba. La columna de entrada recoge el detalle que distingue cada reproducción.

| Entrada | Proveedor de Hades | Preflight de release |
|---|---|---|
| D16 · Lista con cita. La aprobación continúa el párrafo citado desde la primera columna. | Se exige que Claude quede sin dictamen y que Codex rechace en la misma invocación. Las métricas solo registraron a Claude. | Se exige el ID por «sin veredicto formal». La lista de pendientes estaba vacía. |
| D16 · Misma cita con un rechazo propio tras una línea en blanco. | Se exige una única llamada a Claude con rechazo. Las métricas atribuyeron a Claude la aprobación citada. | Se exige el ID por «informe rechazado». La lista estaba vacía. |
| D17 · La prosa contiene `x<y` y el rechazo abre el párrafo siguiente. | Se exige una única llamada a Claude con rechazo. Claude quedó sin dictamen y Codex aprobó. | Se exige el ID por «informe rechazado». El ID figuraba por «informe sin veredicto formal». |
| D18 · El guion está dentro de `<div>`, las etiquetas `<code>` y `</code>` llevan cuatro espacios y la aprobación empieza en la primera columna. El rechazo sigue al bloque tras una línea en blanco. | Se exige una única llamada a Claude con rechazo. Las métricas atribuyeron a Claude la aprobación del ejemplo. | Se exige el ID por «informe rechazado». La lista estaba vacía. |

## Aserciones y controles previos

Los proveedores simulados devuelven código cero. Las pruebas leen las métricas escritas por `motor.agente` y capturan el proveedor y el modelo al lanzar cada llamada. En D16 sin rechazo exterior, el arnés enmarca la cita entre dos párrafos neutrales y comprueba también que ambas filas comparten invocación. En el preflight, cada prueba confirma en Git la ficha `completed` y el informe en su ruta canónica antes de consultar los pendientes. Exigir el ID y el motivo en la misma entrada permite detectar el diagnóstico incorrecto de D17 aunque el cierre siga bloqueado.

El delta conserva los controles de continuación de cita y los cinco casos D14–D15. D14 cubre una lista Markdown que contiene HTML y D18 sitúa el guion dentro del bloque HTML. D15 exige reconocer el rechazo después de un atributo multilínea válido que contiene el literal `<pre>`. Ese control complementa la comparación en prosa de D17. El informe D previo también documenta el caso de control `x < y` con espacios.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Las cuatro entradas ejercitan ambos consumidores. Las dos variantes de D16 difieren únicamente en el rechazo exterior dentro del fragmento reproducido. |
| Aserciones | 9/10 | Las métricas y las llamadas permiten detectar una aprobación mal atribuida, una reserva omitida y una reserva indebida. El preflight comprueba el ID y el motivo por subcadena. |
| Rojo correcto | 10/10 | Los ocho casos alcanzaron la aserción de comportamiento del consumidor correspondiente. |
| Estabilidad | 10/10 | Cada caso usa un repositorio Git temporal propio, configuración Git aislada y respuestas fijas. Las decisiones comprobadas son independientes del reloj y del orden de ejecución. |

## Evidencia y seguimiento

El archivo local de pruebas coincide con el del árbol verificado `f9bf920b045f95ceb484762bf77b511e5d2ff7de` (blob `04fe7d373ee53e5125a1932fa82695409e4710d0`). La evidencia de ese árbol registra ocho fallos de aserción en 5,945 s con los filtros `continuacion_citada_en_lista`, `comparacion_en_prosa` y `guion_en_html`, y Ruff selectivo en verde. Las aserciones posteriores al primer fallo de cada prueba se evaluaron por lectura. El verde de los cinco controles D14–D15 y de las 186 pruebas dirigidas corresponde a la revisión anterior. El proyecto carece de tipador configurado.

- **C1.** H1–H4 y N1–N10 siguen resueltos en los recorridos acreditados. Sin hallazgos independientes nuevos de pruebas.
- **Seguimiento de producto.** D14 y D15 constan como resueltos en el informe D previo. D16, D17 y D18 persisten en el rojo aportado. Los tres ya están asignados a `desarrollador` (Artemisa), con destino `resolver` en C2.
