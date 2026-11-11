**Veredicto:** RECHAZADO
Producto revisado: e395e3b443c65679be4a54420402ff6a2e4fa08190b62d975a7cbab303927242
Rechazo reevaluado: 63286be7fd1b3d0ca5e84c732b9e61ecd19649c2

# B-ADV-0044 · Reevaluación D de código

**Media 7,67/10.** D10 y el control N10 quedan resueltos. D11 persiste en un ejemplo HTML con sangría. D12 es una regresión de esta ronda. En ambos casos, el lector atribuye a Hades una aprobación ajena, incluso cuando Hades emite después su propio rechazo.

## Hallazgos anteriores y control de C1

**D10 · 🔴 Crítico · Resuelto.** En `adevv/revisiones.py:254`, la comparación histórica sin huella usa el cuerpo guardado al emitirse el veredicto. Si se confirma una copia escueta de la aprobación de A sobre el B rechazado, añadir después una nota de archivo conserva el cuerpo vacío de aquella emisión. La evidencia verde cubre ambas etapas. El selector pide `revisar-tarea` para el ID, el preflight incluye el ID y `cierre_revisado` devuelve `False` tras el error de `bug-fix`. También pasa el control positivo histórico sin huella: si la primera emisión de B ya contenía su propia comprobación, el selector avanza a versión y el preflight queda vacío. **Asignación** `desarrollador` (Artemisa). **Destino** `resolver`, cumplido en C2.

**D11 · 🟠 Alta · Persiste.** Para la apertura sin sangría de la reproducción original, la pila de `CitasHTML` excluye el texto de `<pre><code>`. El principal sin dictamen da paso a la reserva en la misma invocación. Si emite un rechazo después del cierre, se registra ese rechazo y termina la llamada al principal. Los dos casos tienen evidencia verde. Sin embargo, esta entrada también contiene una aprobación exclusivamente dentro de un ejemplo:

```html
<details>
<summary>Salida anterior</summary>
    <pre><code>
Veredicto: APROBADO
    </code></pre>
</details>
```

En `adevv/revisiones.py:80`, los cuatro espacios de la apertura hacen que la línea salga antes de llegar a `HTMLParser`. El lector descarta esa línea por sangría y procesa la siguiente como texto propio. Reproduje en memoria que `declaracion` devuelve `APROBADO` tanto con ese fragmento aislado como al añadir un rechazo formal después de `</details>`. El árbol del rechazo anterior daba el mismo resultado. En `skills/orquestar/orquestar.py:2379`, esa aprobación con retorno cero se registra y evita la reserva. En disco, `motivo_informe` acepta el mismo texto como aprobación formal.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Conservar los límites del ejemplo cuando sus etiquetas están sangradas dentro del bloque HTML. El fragmento aislado debe dejar al principal sin dictamen y el informe canónico pendiente. Un rechazo propio posterior debe prevalecer.

**N10 · 🟡 Media · Resuelto.** El control asignado en C1 guarda el ejemplo original como único posible dictamen en el informe canónico de una ficha `completed`, lo confirma en Git y llama a `pendientes_cierre`. La prueba verde exige el ID y el motivo «sin veredicto formal». D11 conserva la variante con sangría como hallazgo de producto. **Asignación** `desarrollador` (Artemisa). **Destino** `resolver`, cumplido en C2.

## Hallazgo nuevo

**D12 · 🟠 Alta · Una línea de código HTML en una cita Markdown expone la aprobación citada.** Esta cita contiene un único párrafo. La línea en blanco separa el rechazo propio:

```markdown
> El informe anterior de
<code>bug-fix</code>
Veredicto: APROBADO

**Veredicto:** RECHAZADO
```

Comparé las dos versiones de `declaracion` en memoria con la misma entrada. La versión del rechazo anterior devuelve `RECHAZADO`. La actual devuelve `APROBADO`. Al retirar el rechazo propio, la anterior devuelve un veredicto vacío y la actual sigue devolviendo `APROBADO`.

En `adevv/revisiones.py:89`, ocultar el contenido de `<code>` convierte la segunda línea en `None`. En la línea 118, ese valor desactiva `parrafo_citado` aunque el párrafo citado continúe en la línea siguiente. El primer veredicto que llega a `cabecera_informe` es el citado. El arnés puede registrar la aprobación, omitir la reserva o perder el rechazo propio. El informe canónico comparte el lector.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Conservar la continuidad de la cita al ocultar un elemento de código en línea. Verificar con la entrada anterior que el principal registra su rechazo y que, cuando falta la declaración propia, queda disponible la reserva.

## Alcance y análisis estático

La comparación con Git confirmó que las rutas del árbol de trabajo coincidían con `cba87a86f9fd1ded147ddf0a341e648f521b9710` antes de escribir este informe. Comprobé la huella de producto y el commit del rechazo canónico. El delta de producción de esta ronda se concentra en `CitasHTML` y `acreditacion_anterior`. Revisé sus consumidores de selección, preflight, cierre tras error y registro del veredicto. H1–H7 y D1–D9 conservan su resolución previa. B-ADV-0045, B-ADV-0046 y B-ADV-0047 tienen revisión independiente.

Reutilicé las cinco pruebas focalizadas verdes (7,369 s) y las 170 del triaje (211,847 s). Las reproducciones adicionales se ejecutaron sobre el lector en memoria. Los efectos en los consumidores para esas variantes se determinaron por lectura del código.

Ejecuté `adevv orquestar --calidad --base 4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` sin escritura. Devolvió 0 y comunicó que omitía formato y lint por ausencia de herramientas reconocidas. Ruff selectivo (`E9,F63,F7,F82`) pasó por separado sobre el mismo árbol. Pasaron los dos controles de espacios y el escaneo corregido de secretos tras el fallo inicial de comillas. El proyecto carece de verificador de tipos configurado. El delta del ID conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 6/10 | La acreditación histórica conserva la emisión de la copia. Dos entradas reproducibles convierten una aprobación ajena en propia. |
| Seguridad | 9/10 | La ronda procesa texto local con la biblioteca estándar. El escaneo corregido de secretos pasó. |
| Conformidad | 6/10 | Se respeta la arquitectura Python/Git. D11 y D12 incumplen la exigencia de un dictamen propio para dar por atendida la revisión. |
| Calidad | 8/10 | Los consumidores comparten el lector. Un mismo valor representa contenido oculto y provoca el fin del párrafo citado. |
| Eficiencia | 9/10 | La pila sigue las etiquetas en una pasada. Conservar el cuerpo de la emisión aprovecha el recorrido Git existente. |
| Documentación | 8/10 | La guía describe la vigencia de la aprobación y el uso de reservas. La garantía del dictamen propio queda pendiente en D11 y D12. |
