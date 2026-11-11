**Veredicto:** RECHAZADO
Producto revisado: 5bce46986d72310b69f1b6e397f9af5623a849ba44588b260b525acde38cb916
Rechazo reevaluado: 21a5801a7972af118114f72406147a83bdd34d35

# B-ADV-0044 · Reevaluación de código D14 y D15

**Media 7,50/10.** D14 y D15 quedan resueltos. La corrección introduce tres regresiones en el lector compartido de dictámenes. En dos casos, el preflight permite cerrar una ficha cuyo informe contiene un rechazo propio. En el tercero, el motor consulta a la reserva después de que el principal haya rechazado el producto.

## Hallazgos anteriores

- **D14 · Resuelto.** El lector separa el marcador de lista antes de reconocer `<div>` y descuenta la sangría del elemento al procesar `<code>`. Las tres regresiones verdes acreditan que el ejemplo aislado activa la reserva y mantiene el ID pendiente por falta de dictamen. Al añadir el rechazo exterior, el principal registra su rechazo en una sola llamada.
- **D15 · Resuelto.** El lector entrega la apertura incompleta `<div` a `HTMLParser` y conserva el atributo hasta su cierre. Las dos regresiones verdes acreditan que el literal `<pre>` de `title` deja visible el rechazo posterior. El principal termina en una llamada y el preflight devuelve «informe rechazado».
- Los demás hallazgos de rondas anteriores conservan su resolución en los recorridos acreditados.

## Hallazgos nuevos y pendientes

### D16 · 🟠 Alta · Una continuación de cita dentro de una lista se atribuye al principal

```markdown
- Antecedente
  > Resultado del informe anterior:
Veredicto: APROBADO

**Veredicto:** RECHAZADO
```

La línea de aprobación continúa el párrafo citado. La línea en blanco separa el rechazo propio. Al encontrar la aprobación sin sangría, `contenido_de_lista` retira el nivel de lista y `lineas_del_informe` borra `parrafo_citado` antes de comprobar la continuación (`adevv/revisiones.py:153`). Con el rechazo exterior, el lector anterior devolvía `RECHAZADO`. Sin ese último párrafo, devolvía un veredicto vacío. En el árbol revisado, el proveedor principal registró `APROBADO` y el preflight devolvió cero pendientes en ambos casos.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Conservar el párrafo citado durante su continuación sin sangría. El fragmento con rechazo debe terminar en una sola llamada al principal y dejar el informe rechazado. El fragmento sin ese párrafo debe permitir la reserva y dejar el informe pendiente por ausencia de dictamen.

### D17 · 🟠 Alta · Una comparación en prosa oculta el rechazo del párrafo siguiente

```markdown
El caso x<y queda pendiente.

**Veredicto:** RECHAZADO
```

Al recibir `<y`, `HTMLParser.feed` deja una posible etiqueta en `rawdata`. El lector sigue enviándole las líneas posteriores hasta agotar el informe, sin recuperar el texto retenido (`adevv/revisiones.py:101`). El lector anterior reconocía el rechazo. En el árbol revisado, el principal quedó sin dictamen, la reserva simulada aprobó y el preflight diagnosticó «informe sin veredicto formal». Como control, escribir `x < y` en la misma frase permitió reconocer el rechazo.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Recuperar el texto cuando la supuesta etiqueta nunca llega a formarse, conservando el atributo multilínea válido de D15. El fragmento debe registrar el rechazo del principal en una sola llamada y producir «informe rechazado».

### D18 · 🟠 Alta · Un guion de texto dentro de HTML expone la aprobación de un ejemplo

```html
<div>
- Ejemplo del informe
    <code>
Veredicto: APROBADO
    </code>
</div>

**Veredicto:** RECHAZADO
```

Dentro del bloque HTML, el guion es texto y la aprobación pertenece a `<code>`. En `adevv/revisiones.py:151`, la decisión de interpretar marcadores de lista omite `en_bloque_html`. El guion abre una lista aparente. Cuando la línea de aprobación vuelve a la primera columna, el cambio de lista sustituye el analizador y pierde el `code` abierto. El lector anterior devolvía `RECHAZADO`. Con el actual, el principal registró `APROBADO` y el preflight devolvió cero pendientes para la ficha completada.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Respetar el contexto HTML al interpretar el guion. Conservar tanto la lista Markdown exterior de D14 como el texto interior del fragmento. Este último debe registrar el rechazo del principal en una sola llamada y mantener el ID pendiente por «informe rechazado».

## Alcance y evidencia

Revisé el cambio de producción desde el rechazo canónico en `adevv/revisiones.py` y sus efectos en `agente` y `pendientes_cierre`. La instantánea de trabajo en `hotfix/v1.1.3` coincidía con `68283b0ddb726545ee42b47eddf300451dbef6bb` antes de escribir el informe. Recalculé la huella de producto y comprobé el commit del rechazo. B-ADV-0045, B-ADV-0046 y B-ADV-0047 tienen sus propias revisiones.

Reutilicé la evidencia verde de las cinco regresiones focalizadas (3,592 s) y de las 186 pruebas dirigidas del triaje (214,638 s). Para D16–D18 comparé en memoria el lector del rechazo anterior con el del árbol actual. Con las entradas nuevas usé el arnés de `test_progreso` en repositorios Git temporales, proveedores simulados con retorno cero y fichas completadas cuyo informe estaba confirmado. Las llamadas, los veredictos registrados y la lista de pendientes descritos arriba se observaron en esos consumidores.

`--verificar` confirmó la reutilización de `adevv orquestar --calidad --base 4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` sobre el árbol exacto, con código 0. El primer intento falló al crear la instantánea Git. El reintento con objetos temporales recuperó la evidencia sin aplicar cambios al producto. El motor declaró omitidos formato y lint por ausencia de herramientas reconocidas. Por separado constan en verde Ruff selectivo (`E9,F63,F7,F82`), los dos controles de espacios y el escaneo de secretos. El proyecto carece de tipador configurado y esta corrección conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | Dos entradas permiten un cierre con rechazo propio y otra activa una reserva indebida. |
| Seguridad | 9/10 | El procesamiento permanece local, usa la biblioteca estándar y el escaneo de secretos pasó. |
| Conformidad | 6/10 | Las tres regresiones incumplen el requisito de atribuir el dictamen a quien lo emitió. La implementación respeta las capas y el stack. |
| Calidad | 7/10 | Proveedor y preflight comparten el lector, pero las transiciones de lista, cita y etiqueta incompleta pierden contexto. |
| Eficiencia | 9/10 | La corrección procesa las líneas en orden y conserva el estado entre ellas. |
| Documentación | 9/10 | El diseño y la guía describen la condición de reserva y la exigencia de aprobación vigente. |
