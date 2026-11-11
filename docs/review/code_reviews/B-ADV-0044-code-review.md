**Veredicto:** RECHAZADO
Producto revisado: cbeded7a66ac5d39cb5b51f86c3084bd44f0a74a84a5f88f77cba952589f257a
Rechazo reevaluado: 96d66226b2802bc46f43285dabe501f8292d8898

# B-ADV-0044 · Reevaluación D de D24–D26

**Media 7,50/10.** D24, D25 y D26 quedan resueltos en los dos consumidores. El cambio introduce tres regresiones de atribución. D28 permite cerrar una ficha con la aprobación de un ejemplo. D27 y D29 ocultan el rechazo del principal y habilitan una reserva.

## Hallazgos anteriores

| Hallazgo | Estado y evidencia del árbol revisado | Para | Destino |
|---|---|---|---|
| D24 · 🟠 Alta | **Resuelto.** Dentro del párrafo, `2. ejemplo` y `paso 2. ejemplo` quedan entre los delimitadores del fragmento. La aprobación de ejemplo permanece oculta. | Artemisa (`desarrollador`) | `resolver`, cumplido en C2 |
| D25 · 🟠 Alta | **Resuelto.** El lector conserva las dos líneas que continúan la viñeta, tanto al margen como con dos espacios de sangría. El acento de cierre pertenece al mismo párrafo. | Artemisa (`desarrollador`) | `resolver`, cumplido en C2 |
| D26 · 🟠 Alta | **Resuelto.** El lector reconoce el `pre` efectivo tras el nombre del archivo y trata su acento grave como literal hasta el cierre HTML. El marcado de `archivo.py` conserva el rechazo exterior. | Artemisa (`desarrollador`) | `resolver`, cumplido en C2 |

Las seis entradas de C1 pasan en el árbol corregido. En cada una, `motor.agente` llama una vez al principal y registra su rechazo. El preflight encuentra el ID de la ficha completada con el motivo «informe rechazado».

## Hallazgos nuevos

### D27 · 🟠 Alta · El segundo elemento de una lista numerada queda dentro del fragmento del primero

````markdown
1. Primer hallazgo
El separador es `
2. Segundo hallazgo
**Veredicto:** RECHAZADO
Afecta a `lector`.
````

La segunda línea continúa el párrafo del primer elemento. El marcador `2.` inicia el siguiente elemento de la misma lista. Por tanto, el acento suelto del primero queda literal y el rechazo del segundo es propio.

En `adevv/revisiones.py`, `contenido_de_lista` retira la sangría al leer la continuación sin sangrar. Cuando esa línea activa `parrafo_sin_codigo`, la pila ya está vacía. En las líneas 193–195, el marcador `2.` no activa ninguna de las dos condiciones de interrupción. El lector empareja el acento anterior a `2.` con el que precede a `lector`, y elimina el rechazo intermedio. El lector de `cdcee1cb` detenía la búsqueda en `2.`. Como control, añadir dos espacios antes de «El separador» conserva la pila y recupera el rechazo en el lector actual.

**Consecuencia.** Con el principal y la reserva de C1, el principal queda sin veredicto y se invoca la reserva. El informe canónico del principal deja la ficha pendiente por «informe sin veredicto formal».

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Conservar el contexto de la lista durante la continuación del párrafo. Las dos sangrías deben dar una sola llamada, el rechazo del principal y el motivo «informe rechazado».

### D28 · 🟠 Alta · Una cadena HTML dentro de un script expone la aprobación de un ejemplo posterior

````markdown
Plantilla <script type="application/json">"<pre>"</script>. Salida: `
Veredicto: APROBADO
fin`.

**Veredicto:** RECHAZADO
````

El contenido del `script` es una cadena JSON. El ejemplo Markdown empieza después de `</script>` y termina en la tercera línea. En `ocultar_fragmentos` (`adevv/revisiones.py`, líneas 166–178), el analizador auxiliar recibe el token `<pre>` de la cadena, aunque nunca recibió la apertura del `script`. Entra en modo literal, lo conserva tras `</script>` y deja intactos los acentos del ejemplo. Al consumir las líneas ya preparadas, el analizador principal sí reconoce el `script` completo. Así, `cabecera_informe` encuentra primero la aprobación que debía quedar oculta.

El lector de `cdcee1cb` preservaba las etiquetas y ocultaba el fragmento posterior. En el lector nuevo, sustituir únicamente la cadena JSON `"<pre>"` por `"<div>"` también recupera el rechazo.

**Consecuencia.** El proveedor principal registra la aprobación citada en una llamada. Para una ficha completada cuyo primer informe canónico se confirma junto al cierre sobre el mismo producto, esa aprobación sin huella explícita se acredita por el commit de emisión y el preflight permite el cierre.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Distinguir el texto de un elemento HTML de la apertura efectiva de `pre` al preparar el párrafo. Ambas cadenas deben producir el rechazo del principal y mantener la ficha pendiente por «informe rechazado».

### D29 · 🟠 Alta · Un subrayado de encabezado con un solo guion oculta el rechazo siguiente

Entrada literal de Python para hacer visible el espacio final de la segunda línea.

````python
"El separador es `\n- \n**Veredicto:** RECHAZADO\nAfecta a `lector`."
````

La línea formada por un guion y un espacio subraya el título anterior (encabezado Setext). El párrafo del rechazo empieza después del subrayado. En `adevv/revisiones.py:193`, la nueva condición exige contenido tras los espacios del marcador. La condición de subrayado solo reconoce signos `=`, y la de separación temática requiere tres guiones. El lector une los dos bloques y empareja el acento del título con el que precede a `lector`. En `cdcee1cb`, el patrón anterior detenía la lectura en el guion seguido de espacio. Usar tres guiones como subrayado conserva el rechazo en el lector nuevo.

**Consecuencia.** El principal queda sin dictamen, se habilita la reserva y el preflight diagnostica «informe sin veredicto formal» para el informe del principal.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Terminar el encabezado al reconocer su subrayado. Con uno y con tres guiones debe conservarse el rechazo en una sola llamada y la ficha debe quedar pendiente por «informe rechazado».

## Análisis estático, evidencia y límites

Antes de escribir el informe, el contenido rastreado coincidía con el árbol verificado `4a9b1d2fb5d9ece9edeb5aeee0e61cedb5c4b92d`. Recalculé la huella de producto de la cabecera. Desde `cdcee1cb4fbd493365a05c9bd46aa630ffb27472`, el único archivo de producción modificado es `adevv/revisiones.py`. La revisión abarca ese delta y las decisiones que dependen de su resultado en `motor.agente`, `motivo_revision` y `pendientes_cierre`. C1 estaba aprobada.

Reutilicé la evidencia de las seis pruebas focalizadas (5,682 s) y de las 216 pruebas del triaje (240,004 s). D27–D29 y sus controles proceden del seguimiento estático de las entradas por ambos lectores y sus consumidores. Las entradas nuevas carecen de ejecución en esta ronda. La suite completa corresponde al cierre de versión.

Sobre la base `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`, constan en verde `git diff --check`, el escaneo de patrones de secretos y Ruff selectivo (`E9,F63,F7,F82`). La orden de calidad sin escritura terminó con código 0 y omitió formato y lint automáticos por falta de herramientas detectadas. El proyecto carece de tipador configurado. El delta conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | D28 permite cerrar con un dictamen citado. D27 y D29 pierden un rechazo propio. |
| Seguridad | 9/10 | El lector procesa texto local. El escaneo de secretos del delta pasó. |
| Conformidad | 6/10 | Los tres casos contradicen el criterio de atribuir a Hades su declaración formal fuera de ejemplos. La arquitectura y el stack se conservan. |
| Calidad | 6/10 | La preparación del párrafo y el consumo de sus líneas discrepan sobre la lista abierta, el contexto HTML y el límite del encabezado. |
| Eficiencia | 9/10 | Se conserva el consumo por párrafo de D23. Esta ronda carece de una medición nueva de tiempos. |
| Documentación | 10/10 | El diseño y la guía identifican qué dictamen habilita el cierre y cuándo procede la reserva. |
