**Veredicto:** RECHAZADO
Producto revisado: fa4b3126f80928adc8d4c5aaba14f4c24bd1f8003db566407c6afc0841d038b4
Rechazo reevaluado: aeaf062aca2756d66ea66de44a32b270f9004102

# B-ADV-0044 · Reevaluación D de código

**Media 7,67/10.** D12 queda resuelto. D11 persiste cuando el ejemplo de código está dentro de un párrafo HTML. D13 es una regresión que impide registrar un rechazo propio del principal. Ambos hallazgos abiertos corresponden al desarrollador en C2.

## Hallazgos anteriores

**D12 · 🟠 Alta · Resuelto.** En `adevv/revisiones.py:130`, ocultar la línea `<code>bug-fix</code>` conserva el párrafo citado. La aprobación que continúa ese párrafo queda fuera del dictamen. Las tres regresiones verdes acreditan las decisiones de los consumidores. Si solo hay cita, el principal deja paso a la reserva en la misma invocación. Si hay un rechazo propio tras la línea en blanco, se registra el del principal. Si el informe canónico solo contiene la cita, el preflight conserva el ID pendiente.

**D11 · 🟠 Alta · Persiste.** Las otras tres regresiones verdes acreditan esas mismas decisiones para el ejemplo sangrado de `<pre><code>` dentro de `<details>` del rechazo anterior. El lector sigue exponiendo el contenido de un elemento `code` sangrado dentro de un párrafo HTML. Esta entrada usa etiquetas emparejadas y la única aprobación está dentro del ejemplo.

```html
<p>
    <code>
Veredicto: APROBADO
    </code>
</p>
```

Comparé el lector anterior y el actual en memoria. Ambos devuelven `APROBADO` con este fragmento, incluso al añadir una línea en blanco y un rechazo formal después de `</p>`. En el lector actual, `motivo_informe` devuelve la cadena vacía en ambos casos. La lista `CitasHTML.contenedores` omite `p`. En `adevv/revisiones.py:92`, la sangría impide que la apertura de `code` llegue a la pila. Con retorno cero, `agente` registra la aprobación del ejemplo y termina antes de probar la reserva. En la ruta canónica, el fragmento supera la comprobación de veredicto formal y pasa al control de vigencia.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Conservar el límite del ejemplo dentro del párrafo HTML. El fragmento aislado debe activar la reserva y dejar pendiente el informe. Con el rechazo posterior, debe registrarse el rechazo del principal.

## Hallazgo nuevo

**D13 · 🟠 Alta · Un ejemplo Markdown con sangría dentro de un desplegable oculta el rechazo posterior.** Un informe puede mostrar literalmente la etiqueta de apertura de un ejemplo. Las líneas en blanco separan el bloque de código Markdown por sangría. El dictamen pertenece a un párrafo posterior al cierre del desplegable.

```markdown
<details>
<summary>Etiqueta de apertura</summary>

    <pre>

</details>

**Veredicto:** RECHAZADO
```

Con esta entrada, el lector del rechazo anterior devuelve `RECHAZADO`. El actual devuelve un veredicto vacío y `motivo_informe` devuelve «informe sin veredicto formal». Como controles, el actual reconoce el rechazo si se muestra la misma etiqueta dentro de un cerco Markdown o si se sustituye la etiqueta sangrada por texto.

En `adevv/revisiones.py:92`, la pila conserva `details` tras la línea en blanco. Esto permite interpretar el literal sangrado `<pre>` como apertura HTML. La pila de ejemplos queda a la espera de `</pre>` y consume tanto `</details>` como el veredicto posterior. Con retorno cero y reserva disponible, `skills/orquestar/orquestar.py:2388` probará otro perfil pese a que el principal ya rechazó el producto. Ese rechazo también se pierde al leer el informe canónico.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Distinguir el ejemplo Markdown por sangría del HTML anidado de D11. Para esta entrada, el principal debe registrar su rechazo en una sola llamada y el informe debe diagnosticarse como rechazado.

## Alcance y verificación

Comprobé que las rutas rastreadas coincidían con el árbol `959e9a5d3aaa87b07058d2218288c40baf1527c7` antes de escribir el informe, calculé su huella de producto y verifiqué el commit del rechazo canónico. El delta de producción de esta ronda se limita al lector compartido de `adevv/revisiones.py`. Los hallazgos cerrados en rondas anteriores conservan su resolución en los recorridos acreditados. B-ADV-0045, B-ADV-0046 y B-ADV-0047 tienen revisión aparte.

Reutilicé las 176 pruebas dirigidas verdes del árbol (344,486 s), incluidas las seis regresiones que fallaban en C1. Para las dos entradas adicionales comparé `declaracion` en ambas versiones y ejecuté `motivo_informe` del árbol actual sobre el texto en memoria. El efecto de esas variantes sobre las llamadas a proveedores y el preflight se determinó por lectura de sus consumidores.

Apliqué el resultado registrado de `adevv orquestar --calidad --base 4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` sin escritura. Devolvió 0 y comunicó la omisión de formato y lint por ausencia de herramientas reconocidas. Ruff selectivo (`E9,F63,F7,F82`), los dos controles de espacios y el escaneo de secretos pasaron por separado sobre este árbol. El proyecto carece de verificador de tipos configurado. El delta del ID conserva las dependencias. La suite completa corresponde al cierre de versión.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 6/10 | El lector puede atribuir una aprobación ajena al principal u omitir su rechazo. |
| Seguridad | 9/10 | El cambio procesa texto local con la biblioteca estándar. El escaneo de secretos pasó. |
| Conformidad | 6/10 | D11 y D13 incumplen el requisito de reconocer el dictamen propio que gobierna las reservas. Se mantienen el stack y las capas del plan. |
| Calidad | 8/10 | Los consumidores comparten el lector. La lista de contenedores y la regla de sangría pierden el contexto en las dos entradas reproducidas. |
| Eficiencia | 9/10 | El análisis mantiene el estado de las etiquetas entre líneas y conserva un único recorrido del informe. |
| Documentación | 8/10 | El diseño y la guía describen la reserva y el dictamen propio. Las dos entradas documentadas aquí incumplen ese comportamiento. |
