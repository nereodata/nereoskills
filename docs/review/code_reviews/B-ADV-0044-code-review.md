**Veredicto:** RECHAZADO
Producto revisado: b4abe95ec95346d7e47b3378cb741454a5bb48ac18630de46199a4eb3aaf42d3
Rechazo reevaluado: e7aa06d5a8a1a10016551d80635a8f3318be18d7

# B-ADV-0044 · Reevaluación D de D20

**Media 7,00/10.** D20 queda resuelto. D21 y D22 impiden aprobar el cambio. En D21 el preflight admite una ficha cuyo revisor la ha rechazado. En D22 el motor invoca a la reserva pese al rechazo del principal. D23 afecta al coste de leer el informe.

## Hallazgo anterior

**D20 · Resuelto en ambos consumidores.** El lector oculta la apertura literal de `pre` con `@click` hasta el acento grave de cierre, incluso cuando el atributo está en la línea siguiente. Las seis pruebas focalizadas acreditan los tres casos siguientes.

| Entrada | `motor.agente` | `pendientes_cierre` |
|---|---|---|
| D20 · Apertura literal repartida en dos líneas | Una llamada al principal, rechazo registrado | ID pendiente por «informe rechazado» |
| Control D20 · Mismo literal en una línea | Una llamada al principal, rechazo registrado | ID pendiente por «informe rechazado» |
| Control D19 · Apertura HTML efectiva con `@click` dentro de un `div` | Una llamada al principal, rechazo exterior registrado | ID pendiente por «informe rechazado» |

D19 conserva su resolución. El informe anterior solo dejó D20 pendiente.

## Hallazgos nuevos

### D21 · 🟠 Alta · Un cierre literal de HTML da por aprobado un informe rechazado

````markdown
El primer ejemplo es <code>uno
</code>. Segundo ejemplo: <code>`</code>`
Veredicto: APROBADO
</code>

**Veredicto:** RECHAZADO
````

El segundo ejemplo muestra cómo se escribe la etiqueta de cierre. La aprobación pertenece a ese ejemplo hasta el cierre efectivo de la cuarta línea. En `adevv/revisiones.py:204`, el lector decide si protege los fragmentos Markdown según el estado HTML al **inicio** de la línea. Como el primer `code` sigue abierto en ese instante, entrega toda la segunda línea a `sin_citas`. Tras cerrar el primer ejemplo y abrir el segundo, el analizador interpreta el cierre entre acentos graves como efectivo. Así queda expuesta la aprobación que precede al rechazo propio.

Con el lector de `e7aa06d5`, `declaracion` devolvió `RECHAZADO`. En el árbol revisado, el proveedor principal registró `APROBADO` en una sola llamada y el preflight devolvió `[]` para la ficha completada. Como control, al eliminar únicamente el salto después de `uno`, el principal registró el rechazo en una llamada y el preflight devolvió «informe rechazado».

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Reconocer el contexto Markdown que sigue al cierre HTML dentro de la misma línea. Tanto el caso como el control deben conservar el rechazo del principal y mantener la ficha pendiente por ese motivo.

### D22 · 🟠 Alta · Un acento grave en un encabezado oculta el rechazo del párrafo siguiente

````markdown
## El separador `
**Veredicto:** RECHAZADO
Afecta a `lector`.
````

El encabezado termina al final de la primera línea. Su acento grave queda literal. En `adevv/revisiones.py:157`, `ocultar_codigo_markdown` comprueba si las líneas **siguientes** empiezan otro bloque, pero admite un encabezado como línea inicial de un párrafo multilínea. Empareja el acento del encabezado con el que precede a `lector` y retira también la declaración intermedia.

El lector de `e7aa06d5` devolvió `RECHAZADO`. En el árbol revisado, el principal quedó sin dictamen, el motor invocó a la reserva y registró su aprobación simulada. El preflight mantuvo el ID pendiente por «informe sin veredicto formal». Al insertar únicamente una línea vacía después del encabezado, el principal registró el rechazo en una sola llamada y el motivo pasó a «informe rechazado».

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Limitar la búsqueda del delimitador a la línea del encabezado. Con y sin línea vacía deben obtenerse el rechazo del principal en una llamada y el diagnóstico «informe rechazado».

### D23 · 🟡 Media · El lector recorre repetidamente el resto del mismo párrafo

En `adevv/revisiones.py:160`, cada línea con código en línea vuelve a recorrer y concatenar el resto del párrafo, incluso si su fragmento se cierra en esa misma línea. En una medición local en memoria repetí la línea «Se comprobo `archivo.py`.», seguida al final del párrafo por una línea vacía y un rechazo. Con 300, 600 y 1.200 líneas, `declaracion` tardó respectivamente 0,078 s, 0,325 s y 1,251 s. El lector anterior tardó unos 0,003 s con 1.200 líneas. Los dos devolvieron el rechazo. El recorrido de los sufijos explica el crecimiento cuadrático y también afecta a las consultas que releen informes históricos.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2 al corregir los límites de D21 y D22. Evitar reconstruir el párrafo por cada línea y conservar la lectura de los fragmentos que sí continúan en la línea siguiente.

## Evidencia, calidad y límites

El contenido rastreado del árbol de trabajo coincidía con el árbol Git `e0adec49b5a340d171503744fa1362fa09c4f37a` antes de escribir el informe. Recalculé la huella de producto indicada en la cabecera. El delta desde el rechazo cambia un único archivo de producción, `adevv/revisiones.py`. Los demás cambios corresponden a las pruebas de D20 y al seguimiento.

Reutilicé los resultados del árbol exacto: seis pruebas focalizadas en 4,052 s y las 202 pruebas del triaje en 226,766 s. Para D21 y D22 comparé ambos lectores en memoria y ejercité las entradas nuevas y sus controles con proveedores simulados y repositorios Git temporales. El preflight leyó el informe canónico confirmado junto con la ficha completada. Los tiempos de D23 corresponden a una medición local del lector.

La comprobación sin escritura `adevv orquestar --calidad --base 4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` consta con código 0. El motor omitió formato y lint por ausencia de herramientas detectadas. Por separado pasaron Ruff selectivo (`E9,F63,F7,F82`), `git diff --check` y el escaneo de secretos del delta. El proyecto carece de tipador declarado y esta ronda conserva las dependencias. El alcance dirigido permite dictaminar los defectos reproducidos.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | D21 admite un cierre rechazado y D22 sustituye el dictamen del principal. |
| Seguridad | 9/10 | El lector procesa texto local y el escaneo de secretos pasó. |
| Conformidad | 6/10 | D20 cumple el diseño. D21 y D22 incumplen la atribución del dictamen exigida para el cierre y la reserva. Se conservan las capas y dependencias previstas. |
| Calidad | 6/10 | El tratamiento de los delimitadores depende de decisiones tomadas por línea y por párrafo que discrepan en los dos límites reproducidos. |
| Eficiencia | 6/10 | D23 introduce trabajo cuadrático para un párrafo con fragmentos cortos. |
| Documentación | 10/10 | La guía y el diseño describen el dictamen propio, la aprobación vigente y la condición para invocar la reserva. |
