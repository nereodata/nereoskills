**Veredicto:** RECHAZADO
Producto revisado: 7cf062d491e09d27e31ac43fba3b6011c7db0afc81f5384f9eef74dbd893890c
Rechazo reevaluado: 025371b61feee239fc0764733c8fef812ca6fe2d

# B-ADV-0044 · Reevaluación D de D16, D17 y D18

**Media 7,67/10.** D16, D17 y D18 quedan resueltos en las reproducciones del rechazo. D19 impide aprobar el cambio. Una etiqueta `<pre>` con un atributo `@click` deja visible la aprobación de un ejemplo. El proveedor la registra como propia y el preflight permite cerrar una ficha cuyo informe rechaza el producto.

## Hallazgos anteriores

| Hallazgo | Resultado | Comportamiento acreditado |
|---|---|---|
| D16 · Continuación de cita en una lista | Resuelto | Al retirar la sangría sin abrir otro elemento, el lector conserva el párrafo citado. Con la aprobación citada como único dictamen aparente, el principal queda sin dictamen, interviene la reserva y el informe canónico queda pendiente por «sin veredicto formal». Con el rechazo exterior, basta una llamada al principal y el preflight indica «informe rechazado». |
| D17 · Comparación en prosa | Resuelto | El lector escapa la apertura incompleta de `x<y queda pendiente.`. El rechazo del párrafo siguiente llega al principal en una llamada y al preflight como «informe rechazado». El control D15 conserva el atributo multilínea con el literal `<pre>`. |
| D18 · Guion dentro del bloque HTML | Resuelto | El estado de bloque HTML mantiene literal el guion dentro de `<div>`. El ejemplo de `<code>` queda oculto hasta su cierre. El principal registra su rechazo en una llamada y el preflight mantiene pendiente la ficha. El control D14 conserva la lista Markdown que contiene HTML. |

Los hallazgos de rondas anteriores y los de otros IDs conservan el resultado de sus respectivos informes.

## Hallazgo nuevo

### D19 · 🟠 Alta · Un atributo de HTML hace pasar el dictamen de un ejemplo por propio

```html
<div>
<pre @click="copiar">
Veredicto: APROBADO
</pre>
</div>

**Veredicto:** RECHAZADO
```

En `adevv/revisiones.py:57`, la expresión de nombres de atributo excluye `@`. La sustitución global de la línea 159 convierte el inicio de esa etiqueta en `&lt;pre` antes de entregarlo a `HTMLParser`. El analizador recibe texto, nunca abre el ejemplo y entrega su aprobación a `cabecera_informe`.

| Entrada | Lector del rechazo anterior | Métrica del principal en el árbol actual | Preflight de la ficha completada |
|---|---|---|---|
| Fragmento reproducido | RECHAZADO | APROBADO, una llamada | Cero pendientes |
| Mismo fragmento, cambiando únicamente `@click` por `title` | RECHAZADO | RECHAZADO, una llamada | ID pendiente por «informe rechazado» |

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. La recuperación de comparaciones como `x<y` debe conservar las aperturas de ejemplos que el analizador reconoce dentro de HTML. En ambos fragmentos el principal debe registrar el rechazo exterior en una llamada y el preflight debe mantener el ID pendiente por «informe rechazado».

## Evidencia y limitaciones

Contrasté el delta con el rechazo canónico, comprobé la coincidencia del checkout con el árbol verificado `1a134d9bcb834658906fcf5b7ec08d49efeb65c1` antes de escribir el informe y recalculé la huella de producto de la cabecera. La única modificación de producción desde el rechazo está en `adevv/revisiones.py`.

Para D16–D18 utilicé la lectura del código, el informe C1 y la evidencia del mismo árbol. Las ocho regresiones focalizadas pasaron en 5,572 s y las 194 pruebas dirigidas del triaje en 220,561 s. Para D19 comparé ambos lectores en memoria y ejercité las dos entradas de la tabla en repositorios Git temporales, con proveedores simulados de retorno cero y el informe canónico confirmado junto a la ficha completada. Las métricas y los pendientes de la tabla son resultados observados. La suite completa corresponde al cierre de versión.

Ejecuté `adevv orquestar --verificar "adevv orquestar --calidad --base 4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5"` en una copia temporal con el mismo árbol Git. El motor confirmó la reutilización del resultado con código 0. La deducción automática omitió formato y lint por ausencia de herramientas reconocidas. El registro separado acredita Ruff selectivo (`E9,F63,F7,F82`), el control de espacios del delta y el escaneo de secretos. El proyecto carece de tipador configurado y el delta conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | D19 permite dar por revisada una ficha con rechazo propio. |
| Seguridad | 9/10 | El lector procesa el HTML localmente como datos. El control de secretos pasó. |
| Conformidad | 6/10 | D19 incumple la atribución del dictamen exigida para el cierre revisado. Se conservan las capas y el stack del diseño. |
| Calidad | 7/10 | Ambos consumidores comparten el lector. El filtro previo y el analizador discrepan sobre qué abre un ejemplo. |
| Eficiencia | 9/10 | La corrección añade una pasada al texto y conserva el recorrido por líneas sin operaciones externas. |
| Documentación | 10/10 | El diseño y la guía identifican cuándo procede la reserva y qué aprobación exige el cierre. |
