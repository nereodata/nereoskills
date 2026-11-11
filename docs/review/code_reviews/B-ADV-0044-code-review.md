**Veredicto:** RECHAZADO
Producto revisado: 07ec80d1c2c16d2d03753ffe2db75b1d37d2941afc8c439a530379b73643c102
Rechazo reevaluado: b63fc9ccc4754db2d2d1b43251f89e9833baec8d

# B-ADV-0044 · Reevaluación D de código

**Media 7,67/10.** Las cinco regresiones verdes acreditan la corrección de los recorridos anteriores de D11 y D13. El cambio introduce dos regresiones en el lector compartido. Una atribuye al principal la aprobación de un ejemplo y la otra pierde un rechazo propio. Ambas requieren corrección en C2.

## Hallazgos anteriores

- **D11 · Resuelto en el recorrido del rechazo.** La apertura de `<p>` activa el bloque HTML y permite reconocer el `<code>` sangrado hasta su cierre. Las tres regresiones acreditan que la aprobación del ejemplo deja paso a la reserva, que un rechazo posterior pertenece al principal y que el informe que solo contiene el ejemplo sigue pendiente por ausencia de veredicto formal.
- **D13 · Resuelto.** La línea en blanco dentro de `<details>` termina el bloque HTML. El `<pre>` literal sangrado queda dentro del ejemplo Markdown. Las dos regresiones acreditan una única llamada al principal que rechaza y el diagnóstico canónico «informe rechazado».
- D12 y los demás hallazgos cerrados en rondas anteriores conservan su resolución para los recorridos acreditados.

## Hallazgos nuevos

### D14 · 🟠 Alta · Una lista Markdown convierte la aprobación de un ejemplo en dictamen propio

```markdown
- <div>
      <code>
  Veredicto: APROBADO
      </code>
  </div>

**Veredicto:** RECHAZADO
```

El marcador de lista precede a `<div>`. En `adevv/revisiones.py:94` el detector busca la apertura al principio de la línea y deja inactivo el bloque HTML. Descarta después el `<code>` sangrado y expone la aprobación interior. Probé el fragmento con y sin el último párrafo. Sin ese párrafo, `declaracion` pasó de veredicto vacío en el rechazo anterior a `APROBADO` en el árbol revisado. Con el párrafo, pasó de `RECHAZADO` a `APROBADO`. En ambos casos el `motivo_informe` actual devuelve la cadena vacía.

Con retorno cero, el principal registra la aprobación y omite la reserva. En el informe canónico la aprobación pasa al control de vigencia. **Para** `desarrollador` (Artemisa), **destino** `resolver` en C2. Reconocer el bloque HTML dentro del elemento de lista. El fragmento aislado debe dejar la revisión pendiente y permitir la reserva. Al añadir el rechazo exterior debe prevalecer el rechazo del principal.

### D15 · 🟠 Alta · Una etiqueta mencionada en un atributo multilínea oculta el rechazo propio

```html
<div
  title="Etiqueta de ejemplo: <pre>">
</div>

**Veredicto:** RECHAZADO
```

El analizador HTML de la biblioteca estándar recibe aquí una única apertura `div` con el texto `<pre>` dentro de `title`. En `adevv/revisiones.py:101` el filtro devuelve la línea `<div` sin entregarla al analizador. Al procesar la segunda línea, interpreta el contenido del atributo como apertura de un ejemplo y oculta el rechazo posterior.

Con este texto, `declaracion` pasó de `RECHAZADO` en el rechazo anterior a veredicto vacío. El `motivo_informe` actual devuelve «informe sin veredicto formal». Con retorno cero y reserva disponible, el motor llama a otro perfil pese al rechazo del principal. **Para** `desarrollador` (Artemisa), **destino** `resolver` en C2. Conservar el contexto de la etiqueta hasta completar sus atributos. Esta entrada debe registrar el rechazo en una sola llamada y obtener «informe rechazado» en la ruta canónica.

## Alcance y verificación

Antes de escribir el informe comprobé que las rutas rastreadas coincidían con el árbol `a26fcef1631e03e6e5f108b7f79f3b24c3a5e1dc`, recalculé la huella de producto y confirmé que el último commit del informe canónico era el rechazo indicado en la cabecera. Desde ese rechazo, el único cambio de producción está en `adevv/revisiones.py`. Las rutas compartidas con B-ADV-0045, B-ADV-0046 y B-ADV-0047 conservan sus revisiones propias.

Para D14 y D15 comparé en memoria los dos lectores y ejecuté `motivo_informe` con los textos reproducidos. En D15 contrasté también la apertura y los atributos con `HTMLParser`. El efecto sobre las llamadas a proveedores se determinó por lectura de `skills/orquestar/orquestar.py:2379` y `:2388`. La decisión canónica posterior depende además de la vigencia del informe.

Reutilicé las cinco regresiones verdes (7,223 s) y las 181 pruebas dirigidas verdes (351,869 s) del árbol. La suite completa corresponde al cierre de versión. La verificación de calidad sin escritura sobre la base `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` devolvió 0 y declaró omitidos formato y lint por ausencia de herramientas reconocidas. Ruff selectivo (`E9,F63,F7,F82`), ambos controles de espacios y el escaneo de secretos pasaron por separado. El proyecto carece de tipador configurado y el delta conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 6/10 | D14 acepta una aprobación ajena y D15 pierde un rechazo propio. |
| Seguridad | 9/10 | El lector trata texto local con la biblioteca estándar. El escaneo de secretos pasó. |
| Conformidad | 6/10 | Las dos entradas incumplen el contrato de atribución del dictamen que gobierna la reserva. Se respetan el stack y las capas del plan. |
| Calidad | 8/10 | Los consumidores reutilizan el mismo lector. El filtro previo pierde el contexto de lista y de atributo en las líneas identificadas. |
| Eficiencia | 9/10 | La corrección conserva el recorrido por líneas y el estado del analizador entre ellas. |
| Documentación | 8/10 | El diseño y la guía describen cuándo procede la reserva. Los dos casos reproducidos contradicen ese comportamiento. |
