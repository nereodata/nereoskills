**Veredicto:** RECHAZADO
Producto revisado: 0af070a922bef82092f9cf10ca53ac72694ce958e4e544e1b5608f1b20338be2
Rechazo reevaluado: 7f2afb6533ba9b300d38114054a8c9ac5833480f

# B-ADV-0044 · Reevaluación D de D19

**Media 7,67/10.** D19 queda resuelto. El hallazgo nuevo D20 impide aprobar el cambio. Un ejemplo Markdown que muestra una etiqueta de apertura en dos líneas oculta el rechazo posterior del principal y activa la reserva.

## Hallazgo anterior

**D19 · Resuelto.** Dentro de un `<div>`, el patrón de `CitasHTML.etiqueta` admite ahora `@click`. La apertura de `<pre>` llega íntegra a `HTMLParser`, que oculta la aprobación del ejemplo hasta el cierre de la etiqueta. Tanto con `@click` como con `title`, el principal registra su rechazo en una sola llamada y el preflight mantiene el ID pendiente por «informe rechazado». Las ocho pruebas focalizadas acreditan también los controles D17 y D15. D16–D18 conservan el resultado de la revisión anterior.

## Hallazgo nuevo

### D20 · 🟠 Alta · Una etiqueta literal entre acentos graves oculta el dictamen propio al partirla en dos líneas

```markdown
La apertura es `<pre
@click="copiar">`.

**Veredicto:** RECHAZADO
```

Los dos acentos graves delimitan un único fragmento de código Markdown. Este muestra únicamente la etiqueta de apertura. El rechazo pertenece al párrafo siguiente.

En `adevv/revisiones.py:57`, el patrón ampliado reconoce la etiqueta con `@click` incluso a través del salto de línea. En la línea 159, `inicio_incompleto` procesa el informe entero. En cambio, `sin_citas` protege los fragmentos entre acentos graves dentro de una sola línea antes de llamar a `feed`. Así, `HTMLParser` acumula la apertura y la completa en la segunda línea. El lector mantiene abierto un `pre` literal y oculta el párrafo del rechazo. Para la entrada reproducida, `declaracion` devolvía `RECHAZADO` en el commit del rechazo anterior y ahora devuelve un veredicto vacío.

| Entrada en el árbol revisado | Llamadas y métricas de Hades | Preflight del informe del principal |
|---|---|---|
| Fragmento anterior, con salto de línea | Claude quedó sin dictamen. Se invocó a Codex y se registró la aprobación de la reserva simulada. | `B-DEMO-0001` pendiente por «informe sin veredicto formal». |
| Mismo texto, sustituyendo únicamente el salto entre `pre` y `@click` por un espacio | Una llamada a Claude, con rechazo. | `B-DEMO-0001` pendiente por «informe rechazado». |

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Conservar el contexto del fragmento Markdown entre líneas al decidir qué etiquetas recibe el analizador HTML. En ambos casos de la tabla se exige una sola llamada al principal con rechazo y el motivo «informe rechazado» para el ID. Conservar el caso D19 de una etiqueta HTML efectiva dentro de un `div`.

## Evidencia, análisis estático y límites

Contrasté el delta completo desde el rechazo con el árbol `e5146fc231ecc69c2fa3bb74f3443708624d2d11` y recalculé la huella de producto de la cabecera. La única modificación de producción es el patrón de nombres de atributo en `adevv/revisiones.py`. También cambiaron el estado de la ficha, las pruebas de D19 y su informe C1.

Reutilicé la evidencia de las ocho pruebas focalizadas (5,284 s) y de las 198 pruebas dirigidas del triaje (224,274 s). Para D20 comparé ambos lectores en memoria y ejercité las dos entradas de la tabla con `motor.agente` y `pendientes_cierre` en repositorios Git temporales. Los proveedores eran simulados y devolvían código cero. El preflight leyó el informe del principal confirmado junto con la ficha completada. La suite completa queda para el cierre de versión.

Sobre la base de calidad `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`, constan en verde Ruff selectivo (`E9,F63,F7,F82`), el control de espacios y el escaneo de secretos con el argumento corregido. El primer intento del escaneo terminó por un error de comillas. La orden de calidad terminó con código cero y omitió formato y lint por ausencia de herramientas detectadas. El proyecto carece de tipador configurado y el delta conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | D20 pierde el dictamen del principal y permite registrar el de la reserva en su lugar. |
| Seguridad | 9/10 | El lector procesa los atributos como datos locales. El escaneo de secretos pasó. |
| Conformidad | 6/10 | D20 incumple la condición de probar la reserva solo si falta el dictamen propio. Se conserva el lector común previsto en el diseño. |
| Calidad | 7/10 | La gramática del atributo se comparte en un punto, pero la protección de código Markdown y la detección de etiquetas operan sobre límites de línea distintos. |
| Eficiencia | 9/10 | La ampliación del patrón conserva las pasadas existentes sobre el informe. |
| Documentación | 10/10 | El diseño y la guía expresan el criterio de atribución y la condición para recurrir a la reserva. |
