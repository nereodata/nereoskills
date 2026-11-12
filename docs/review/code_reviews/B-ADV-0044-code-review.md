**Veredicto:** RECHAZADO
Producto revisado: cbdfb81bd262de6d3f27f00d8b15bd0d5bdbab0b2e1d8e64499191591b657c00
Rechazo reevaluado: 71cb10159a304d318b389ae8ea25c1e06da76989

# B-ADV-0044 · Reevaluación D de D27–D29

**Media 7,67/10.** D27, D28 y D29 quedan resueltos. D30 impide aprobar el producto. Un `script` en mitad de un párrafo citado puede exponer la aprobación de la cita y permitir el cierre pese al rechazo propio de Hades.

## Hallazgos anteriores

| Hallazgo | Estado | Evidencia en proveedor y preflight |
|---|---|---|
| D27 · Segundo elemento numerado | **Resuelto** | El lector prepara el párrafo desde el primer elemento mientras dispone de su sangría. El marcador `2.` delimita el segundo elemento tanto si la continuación tiene cero o dos espacios como si tiene los tres del control. |
| D28 · Cadena JSON con una etiqueta literal | **Resuelto** | La preparación del párrafo consume el `script` completo. Tanto con `"<pre>"` como con `"<div>"`, el fragmento que empieza después de `</script>` oculta la aprobación de ejemplo. |
| D29 · Subrayado Setext | **Resuelto** | El subrayado de un guion con espacio final termina el encabezado, igual que el control de tres guiones. El acento grave del título queda separado del rechazo del párrafo siguiente. |

En las siete entradas, el arnés simulado registra una sola llamada al principal y su rechazo. El preflight mantiene pendiente la ficha completada `B-DEMO-0001` por «informe rechazado». C1 estaba aprobada con 9,75/10. Para los tres hallazgos, el destinatario era Artemisa (`desarrollador`) y el destino `resolver` quedó cumplido en C2.

## Hallazgo nuevo

### D30 · 🟠 Alta · Un script en una continuación citada expone la aprobación de la cita

````markdown
> Respuesta anterior del revisor
Incluye esta plantilla <script type="application/json">
{}
</script>
Veredicto: APROBADO

**Veredicto:** RECHAZADO
````

«Incluye esta plantilla» continúa el párrafo citado. La apertura del `script` aparece después de esas palabras. La línea de JSON, el cierre de la etiqueta y la aprobación siguen en el mismo párrafo. La línea vacía separa el rechazo propio.

En `adevv/revisiones.py`, la línea 51 incorpora `script` a `CitasHTML.etiquetas`. Al leer `{}`, `sin_citas` encuentra esa etiqueta en `abiertas`, activa `bloque` y devuelve `None`. La rama de `lineas_del_informe` que procesa ese resultado borra `parrafo_citado` aunque la línea original contiene JSON. Tras `</script>`, `cabecera_informe` acepta la aprobación anterior al rechazo. En el árbol previo, el contenido de `script` también se almacenaba hasta el cierre, pero la línea de JSON conservaba el estado de cita porque `script` no activaba `bloque`.

**Efecto en los consumidores.** En el recorrido de C1, `motor.agente` registraría la aprobación citada como dictamen del principal y terminaría en una llamada. Si el primer informe canónico se confirma junto con la ficha completada, `motivo_revision` atribuiría esa aprobación sin huella explícita al producto del commit de cierre. Con esa única ficha, `pendientes_cierre` devolvería una lista vacía.

**Para** Artemisa (`desarrollador`). **Destino** `resolver` en C2. Conservar el párrafo citado al ocultar el contenido del `script` en línea. Como control, unir la apertura, `{}` y el cierre en la línea «Incluye esta plantilla», manteniendo las demás líneas. En ambas presentaciones debe registrarse el rechazo del principal en una llamada y el preflight debe identificar la ficha por «informe rechazado».

## Alcance y evidencia

Comparé los árboles Git `4a9b1d2fb5d9ece9edeb5aeee0e61cedb5c4b92d` y `870a23e384ede126aca575b4441b0b45d377c7f8`. El único archivo de producción del delta es `adevv/revisiones.py`. Antes de escribir el informe, el contenido rastreado coincidía con el árbol final y la huella de producto recalculada coincidía con la cabecera. La revisión siguió el resultado del lector hasta las métricas y la decisión de reserva de `motor.agente`, y hasta la acreditación del informe en `pendientes_cierre`.

El diseño exige atribuir a Hades su declaración fuera de citas y ejemplos. D30 vulnera ese criterio y la barrera de cierre revisado. El delta conserva las interfaces, las capas y la librería estándar previstas en el plan de plataforma. Los contadores por paso e ID, la cuota, la recarga y la vigencia por producto siguen cubiertos por la verificación dirigida del triaje.

Reutilicé las siete pruebas focalizadas en verde (6,838 s) y las 223 pruebas del triaje en verde (249,717 s), acreditadas sobre el árbol final. D30 y su control proceden de la lectura de ambos árboles y de los consumidores. Su resultado está deducido por análisis estático y queda pendiente de reproducción ejecutada.

## Análisis estático

Sobre la base `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` constan en verde `git diff --check`, el escaneo de patrones de secretos y Ruff selectivo (`E9,F63,F7,F82`). La orden de calidad sin escritura terminó con código 0 y omitió las etapas automáticas de formato y lint por ausencia de herramientas detectadas. El proyecto carece de tipador configurado. Las dependencias permanecen iguales.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | D30 puede invertir el dictamen y liberar una ficha rechazada. |
| Seguridad | 9/10 | El cambio procesa texto local y el escaneo de secretos pasó. |
| Conformidad | 6/10 | La aprobación citada incumple el criterio de atribución y habilita el cierre. La arquitectura se conserva. |
| Calidad | 7/10 | El lector comparte el patrón de atributos, pero usa la misma marca para ocultar texto HTML y terminar la cita Markdown. |
| Eficiencia | 9/10 | La preparación sigue consumiendo el párrafo una vez. La evidencia de esta ronda mide el triaje, no el rendimiento aislado del lector. |
| Documentación | 10/10 | El diseño y la guía describen la declaración exigida, la reserva y la acreditación del cierre. |
