**Veredicto:** APROBADO · **9,75/10**

# B-ADV-0044 · Reevaluación C1 de las pruebas de D14 y D15

Las cinco pruebas reproducen las dos entradas del informe D y comprueban sus efectos en la selección del proveedor y en el preflight de release. El archivo local `skills/orquestar/test_progreso.py` coincide con el del árbol verificado `0f1f6df4aba12d31e3d82318f697891ff46a85c6` de `hotfix/v1.1.3`. El delta de pruebas añade dos textos de entrada y cinco métodos a `ProgresoTests`. Conserva los controles anteriores.

## Reproducciones y rojo observado

D14 conserva el marcador `- ` antes de `<div>`, los seis espacios antes de las etiquetas `code` y los dos antes de la aprobación citada. El caso con rechazo añade un párrafo después de la lista. En D15, `<div` termina la primera línea, el literal `<pre>` aparece entre las comillas de `title` en la segunda y el rechazo propio sigue a `</div>` tras una línea en blanco.

| Caso | Resultado exigido | Primera discrepancia en la evidencia |
|---|---|---|
| D14 · Proveedor, solo ejemplo | Claude queda sin dictamen y Codex rechaza en la misma invocación. | Las métricas solo registran a Claude. |
| D14 · Proveedor, rechazo tras la lista | Claude registra su rechazo en una única llamada. | Claude figura con la aprobación del ejemplo. |
| D14 · Informe canónico, solo ejemplo | El preflight mantiene pendiente el ID por «sin veredicto formal». | La lista de pendientes está vacía. |
| D15 · Proveedor, rechazo tras el atributo | Claude registra su rechazo en una única llamada. | Claude figura sin dictamen y Codex aprueba. |
| D15 · Informe canónico, rechazo tras el atributo | El preflight mantiene pendiente el ID por «informe rechazado». | Devuelve el ID por «informe sin veredicto formal». |

Los proveedores simulados devuelven código cero en los tres casos. Las aserciones consultan las métricas producidas por `motor.agente` y las llamadas capturadas al lanzar cada perfil. En los dos casos de preflight se confirman en Git la ficha `completed` y el informe canónico antes de consultar `pendientes_cierre`. Exigir el ID y el motivo en la misma entrada distingue los dos resultados de D15, aunque ambos bloqueen el cierre.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Los cinco casos cubren la reserva, la atribución del rechazo propio y los dos motivos de cierre pendiente que exigen las reproducciones. |
| Aserciones | 9/10 | Se comprueban proveedor, veredicto, orden de llamadas e identidad de invocación cuando hay reserva. El preflight comprueba el ID y la parte significativa del diagnóstico por subcadena. |
| Rojo correcto | 10/10 | Los cinco fallos son discrepancias de comportamiento en el consumidor previsto. Todos alcanzan la aserción correspondiente. |
| Estabilidad | 10/10 | Cada caso usa entradas fijas y un repositorio Git temporal propio. Las respuestas simuladas son deterministas y las decisiones comprobadas son independientes del reloj y del orden de ejecución. |

## Seguimiento y evidencia

- **C1.** H1–H4 y N1–N10 siguen resueltos en los recorridos acreditados. Sin hallazgos nuevos ni pendientes de pruebas. D11 y D13 constan como resueltos en la revisión D anterior.
- **D14 · 🟠 Alta · Persiste en producto.** Para `desarrollador` (Artemisa), destino `resolver` en C2. La aprobación dentro de la lista debe dejar disponible la reserva y mantener pendiente el informe. Si el principal añade su rechazo exterior, debe registrarse ese rechazo en una sola llamada.
- **D15 · 🟠 Alta · Persiste en producto.** Para `desarrollador` (Artemisa), destino `resolver` en C2. El literal del atributo debe permitir reconocer el rechazo exterior, terminar con el principal y devolver «informe rechazado» en el preflight.

La evidencia adjunta de `--verificar` registra cinco fallos de aserción en 3,749 s con los filtros `ejemplo_html_en_lista` y `tras_atributo_multilinea` del módulo de triaje `skills.orquestar.test_progreso`. Los filtros seleccionan las cinco pruebas añadidas. Las aserciones posteriores a la primera discrepancia de cada caso se evaluaron por lectura. Se reutilizó el verde de Ruff selectivo del mismo árbol. El proyecto carece de tipador configurado. Las 181 pruebas dirigidas verdes corresponden al árbol anterior.
