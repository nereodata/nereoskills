**Veredicto:** RECHAZADO
Producto revisado: 6ef599ea58239e6ae788d01340a16e61c2893bfacaf27a455a16af76ba1bf93b
Rechazo reevaluado: 216c5fb138d61d642846f16a6139e6649dafc8b0

# B-ADV-0044 · Reevaluación D

**Media 7,50/10.** D21, D22 y D23 quedan resueltos. D24 y D25 permiten cerrar una ficha con la aprobación que figura dentro de un ejemplo. D26 activa la reserva pese al rechazo expreso del principal.

## Hallazgos anteriores

| Hallazgo | Dictamen y evidencia | Responsable y destino |
|---|---|---|
| D21 · 🟠 Alta | **Resuelto.** Al cerrar el primer `code`, el lector protege el cierre literal del segundo ejemplo. Con el salto de línea y sin él, el principal registra su rechazo en una llamada y el preflight mantiene la ficha pendiente por «informe rechazado». | Artemisa (`desarrollador`), resuelto en C2. |
| D22 · 🟠 Alta | **Resuelto.** La búsqueda del acento de cierre termina en la propia línea del encabezado. El rechazo del párrafo siguiente llega a los dos consumidores tanto con separación en blanco como sin ella. | Artemisa (`desarrollador`), resuelto en C2. |
| D23 · 🟡 Media | **Resuelto.** El lector consume las líneas pendientes y reutiliza el párrafo preparado. En la medición aportada, para 300, 600 y 1.200 líneas, las medianas anteriores fueron 0,077490, 0,298481 y 1,193028 s. Las actuales fueron 0,001748, 0,003273 y 0,007283 s. Ambos lectores devolvieron el rechazo en los tres tamaños. | Artemisa (`desarrollador`), resuelto en C2 para la entrada medida. |

## Hallazgos nuevos

### D24 · 🟠 Alta · Un número dentro del ejemplo expone una aprobación

````markdown
La salida fue `
2. ejemplo
Veredicto: APROBADO
fin`.

**Veredicto:** RECHAZADO
````

En `adevv/revisiones.py:170`, el nuevo patrón corta el párrafo ante cualquier marcador ordenado de uno a nueve dígitos. Dentro de un párrafo en curso, `2. ejemplo` es una continuación. El corte deja sin emparejar los acentos que encierran la aprobación. El lector anterior recuperó el rechazo. El actual registró la aprobación en la única llamada al principal y `pendientes_cierre` devolvió `[]` con la ficha completada. Cambiar solo `2. ejemplo` por `paso 2. ejemplo` recuperó el rechazo del principal y el motivo «informe rechazado».

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Aplicar la regla de interrupción de un párrafo por una lista ordenada al buscar el cierre del fragmento. El caso y el control deben mantener la ficha pendiente por rechazo en una sola llamada.

### D25 · 🟠 Alta · Una continuación sin sangría de un elemento de lista expone su ejemplo

````markdown
- Se recibio `
Veredicto: APROBADO
fin`.

**Veredicto:** RECHAZADO
````

En `adevv/revisiones.py:166`, la búsqueda termina en cuanto falta la sangría del elemento. Las dos líneas de texto continúan el párrafo de la viñeta y cierran el fragmento antes de la línea vacía. El lector anterior devolvió el rechazo. El actual registró la aprobación del ejemplo como dictamen del principal y el preflight devolvió `[]`. Al añadir dos espacios delante de la segunda y la tercera línea, el principal registró el rechazo en una llamada y el preflight devolvió «informe rechazado».

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Conservar las continuaciones de párrafo válidas dentro del elemento de lista al emparejar los acentos. Ambas presentaciones deben producir el rechazo del principal y el mismo motivo de cierre pendiente.

### D26 · 🟠 Alta · Preparar el párrafo por adelantado elimina el cierre efectivo de un ejemplo HTML

````markdown
Se inspecciono `archivo.py`. Salida: <pre>
Marca literal: `
</pre>
**Veredicto:** RECHAZADO
Afecta a `lector`.
````

En `adevv/revisiones.py:174`, la sustitución se aplica al párrafo completo antes de entregar la primera línea a `CitasHTML`. El código en línea alrededor de `archivo.py` activa esa preparación. La sustitución empareja el acento literal del ejemplo `pre` con el que precede a `lector` y elimina tanto la etiqueta de cierre como el rechazo exterior. La guarda para un `pre` ya abierto en la línea 200 llega después de esa sustitución.

El lector anterior devolvió el rechazo. Con el actual, el principal quedó sin dictamen, se registró la aprobación de la reserva simulada y el preflight diagnosticó «informe sin veredicto formal». Quitar únicamente los acentos de `archivo.py` conservó el rechazo en la única llamada al principal y dejó la ficha pendiente por «informe rechazado».

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Respetar la apertura y el cierre efectivos de `pre` durante la preparación del párrafo. El marcado de un nombre de archivo anterior al ejemplo debe conservar el dictamen y el número de llamadas del control.

## Evidencia, análisis estático y límites

Antes de escribir este informe comprobé que el contenido del árbol de trabajo coincidía con el árbol Git `cdcee1cb4fbd493365a05c9bd46aa630ffb27472` y recalculé la huella de la cabecera. Desde `e0adec49b5a340d171503744fa1362fa09c4f37a`, el único archivo de producción modificado es `adevv/revisiones.py`. El alcance de D comprende el lector y las decisiones de sus consumidores. C1 ya estaba aprobada.

Reutilicé las ocho pruebas focalizadas en verde (5,456 s), las 210 del triaje (233,099 s) y la medición local de D23 (mediana de tres ejecuciones). Para D24–D26 comparé ambos lectores en memoria. Ejercité las entradas nuevas y sus controles con `motor.agente`, proveedores simulados y `pendientes_cierre` en repositorios Git temporales, confirmando el informe del principal junto con la ficha completada. La comprobación cubre la selección de proveedor, sus métricas y la decisión de cierre. La suite completa corresponde al cierre de versión.

Sobre la base `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` constan en verde `git diff --check`, el escaneo de patrones de secretos y Ruff selectivo (`E9,F63,F7,F82`). La orden de calidad terminó con código 0 y omitió sus etapas de formato y lint por ausencia de herramientas detectadas. El proyecto carece de tipador declarado. Esta ronda conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | Dos entradas permiten cerrar una ficha rechazada y otra sustituye el rechazo por el dictamen de la reserva. |
| Seguridad | 9/10 | El lector opera sobre texto local y el escaneo de secretos del delta pasó. |
| Conformidad | 6/10 | Los tres casos incumplen la atribución del dictamen propio exigida por el diseño. El cambio conserva las capas y dependencias previstas. |
| Calidad | 6/10 | La delimitación del párrafo y el estado de listas y ejemplos HTML producen decisiones incompatibles en las entradas reproducidas. |
| Eficiencia | 9/10 | La lectura del párrafo de D23 evita los recorridos repetidos y escala aproximadamente con la entrada medida. |
| Documentación | 10/10 | La guía y el diseño identifican el dictamen que acredita el cierre y la condición que habilita la reserva. |
