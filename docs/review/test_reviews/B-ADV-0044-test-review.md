**Veredicto:** APROBADO · **9,75/10**

# B-ADV-0044 · Reevaluación C1 de las pruebas de D11 y D13

El delta desde el C1 aprobado en `309d88d17a8364db18f1309b92cc72d9bb90cd09` añade cinco pruebas a `skills/orquestar/test_progreso.py` y parametriza el motivo esperado por el preflight. El archivo local coincide con el del árbol de la evidencia, `640b224994a709934494f039fbfeee24f38ae38f`.

## Recorridos y evidencia roja

D11 reproduce un párrafo HTML con las etiquetas de apertura y cierre de `code` sangradas cuatro espacios y una aprobación dentro del ejemplo. D13 reproduce un `<pre>` literal sangrado, separado por líneas en blanco dentro de `<details>`. El rechazo propio aparece en un párrafo posterior a `</details>`.

| Recorrido | Comportamiento exigido por la prueba | Primera discrepancia registrada |
|---|---|---|
| D11 · El principal solo cita la aprobación | Claude queda sin dictamen. Codex registra su rechazo en la misma invocación. Se comprueba el orden de los dos perfiles. | Las métricas solo contienen a Claude. |
| D11 · El principal añade un rechazo tras `</p>` | Claude registra su rechazo en una sola llamada. | Claude figura con la aprobación del ejemplo. |
| D11 · Informe canónico con la aprobación dentro del ejemplo | El preflight devuelve el ID con el motivo «sin veredicto formal». | La lista de pendientes está vacía. |
| D13 · El principal rechaza tras el desplegable | Claude registra su rechazo en una sola llamada. | Claude figura sin dictamen y Codex registra una aprobación. |
| D13 · Informe canónico con el rechazo tras el desplegable | El preflight devuelve el ID con el motivo «informe rechazado». | Devuelve el ID con «informe sin veredicto formal». |

En los casos de proveedor, el arnés simulado devuelve código cero. Las aserciones leen las métricas de Hades y las llamadas a los perfiles. En los dos casos de preflight, la prueba confirma en Git la ficha `completed` y su informe canónico antes de consultar `pendientes_cierre`. La aserción exige el ID y el motivo en la misma entrada, distinción decisiva en D13, donde ambos diagnósticos mantienen pendiente el cierre.

## Seguimiento

- **C1 · H1–H4 y N1–N10 resueltos.** Para N10, los tres controles previos siguen usando el motivo predeterminado «sin veredicto formal». Conservan la preparación y la condición de éxito del último C1.
- **C1 · Hallazgos nuevos de pruebas.** Ninguno.
- **Producto · D11 persiste en el párrafo HTML y D13 persiste en el desplegable con el literal sangrado.** Los cinco rojos corresponden a los defectos ya asignados al `desarrollador` en C2. D12, D9 y D10 constan como resueltos en las revisiones D anteriores.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Los cinco casos reproducen las decisiones de reserva, atribución del rechazo y cierre descritas para D11 y D13. |
| Aserciones | 9/10 | Se comprueban proveedores, perfiles, veredicto e identidad de invocación según el caso. El preflight identifica el motivo por una subcadena del diagnóstico. |
| Rojo correcto | 10/10 | Las cinco pruebas alcanzan el consumidor previsto y fallan en la aserción que distingue el defecto. |
| Estabilidad | 10/10 | Cada caso usa entradas literales, un repositorio Git temporal propio y, cuando procede, proveedores simulados. Las aserciones son independientes del reloj y del orden de ejecución. |

La ejecución focalizada aportada registró cinco fallos de aserción en 5,325 s. Las comprobaciones posteriores al primer fallo de cada caso se evaluaron por lectura. Se reutilizó el verde de Ruff selectivo (`E9,F63,F7,F82`). El proyecto carece de tipador configurado.
