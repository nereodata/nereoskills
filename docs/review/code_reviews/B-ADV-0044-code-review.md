**Veredicto:** APROBADO
Producto revisado: f8206ba55eb54fe3eef7e0c83a17fa649073de41907363f6c392648ee2004ce5
Rechazo reevaluado: 489edd627f4a5743e15e8b714ecbad45ca292a44

# B-ADV-0044 · Reevaluación D de D30

**Media 9,33/10.** D30 queda resuelto. El proveedor y el preflight reconocen el rechazo propio de Hades en las dos presentaciones del mismo informe.

## Hallazgos anteriores

**D30 · 🟠 Alta · Resuelto.** Destinataria original, Artemisa (`desarrollador`). Destino `resolver`, cumplido en C2. D27–D29 ya constaban como resueltos en el dictamen anterior.

En `adevv/revisiones.py`, `CitasHTML` sigue ocultando el contenido de `script` y `style`. Reserva la marca `bloque` para `blockquote` y `pre`. Al consumir el JSON y el cierre del `script` de D30, las líneas ocultas conservan el párrafo citado. Mientras el analizador HTML lee texto literal, `lineas_del_informe` también prescinde de interpretar ese texto como inicio de otro bloque. La aprobación que sigue a la etiqueta permanece en la cita. La línea vacía posterior termina el párrafo y deja visible el rechazo propio.

| Entrada de C1 | Proveedor simulado | Preflight de la versión |
|---|---|---|
| JSON en su propia línea entre la apertura y el cierre del `script` | Una llamada a Claude con el modelo `principal`. Su única métrica de Hades registra `RECHAZADO`. | `pendientes_cierre` identifica la ficha completada `B-DEMO-0001` por «informe rechazado». |
| Apertura, JSON y cierre en una línea | Una llamada al mismo principal, con el mismo rechazo. | La misma ficha queda pendiente por el mismo motivo. |

En `motor.agente`, ese rechazo formal termina la invocación antes de la reserva. Al leer el informe canónico confirmado junto con la ficha, `motivo_revision` devuelve el rechazo antes de evaluar la vigencia de una aprobación. Se cumplen los criterios de atribuir el dictamen a su emisor y de exigir una revisión válida para cerrar el trabajo.

## Hallazgos nuevos

Ninguno en el delta reevaluado. No queda ningún hallazgo pendiente de asignación.

## Alcance y evidencia

Comparé los árboles Git `870a23e384ede126aca575b4441b0b45d377c7f8` y `bfbeb8d6c9dc9268090e7819cc112c4ace57de56`. El único archivo de producción modificado es `adevv/revisiones.py`. La corrección afecta al lector compartido del dictamen y conserva las interfaces y la librería estándar previstas en el diseño y el plan de plataforma. Antes de emitir el informe, el contenido rastreado coincidía con el árbol final y la huella calculada coincidía con la cabecera.

C1 estaba aprobada con 9,75/10. Antes de C2, el caso multilínea fallaba en los dos consumidores y el control de una línea pasaba. En el árbol final, la verificación acreditada pasó las dos pruebas focalizadas en 1,837 s y las 225 pruebas dirigidas del triaje en 251,676 s. Estas últimas cubren también progreso por paso e ID, cuota, recarga, perfiles y cierre revisado. Reutilicé ambas ejecuciones.

## Análisis estático

Sobre la base de calidad `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`, constan en verde `git diff --check`, el escaneo de patrones de secretos y Ruff selectivo (`E9,F63,F7,F82`). La orden de calidad sin escritura terminó con código 0 y omitió el formato y el lint automáticos por ausencia de herramientas detectadas. El proyecto carece de tipador configurado y el delta conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 9/10 | La reproducción y el control preservan el rechazo en la métrica y en la decisión de cierre. |
| Seguridad | 9/10 | El lector trata el contenido del script como datos. El escaneo de secretos del delta pasó. |
| Conformidad | 10/10 | La declaración propia gobierna la reserva y el cierre conforme al diseño y a los criterios de aceptación. |
| Calidad | 9/10 | Una colección explícita identifica las etiquetas que marcan bloque tanto en la apertura como en las líneas siguientes. |
| Eficiencia | 9/10 | La corrección consulta el estado del analizador durante el recorrido existente, sin añadir otra pasada al informe. |
| Documentación | 10/10 | El diseño y la guía describen correctamente qué dictamen admite el motor y cuándo queda pendiente una revisión. |
