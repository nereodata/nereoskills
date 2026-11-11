**Veredicto:** APROBADO · **9,75/10**

# B-ADV-0044 · Reevaluación C1 de las pruebas de D11 y D12

Árbol revisado `309d88d17a8364db18f1309b92cc72d9bb90cd09`. Base de comparación `aeaf062aca2756d66ea66de44a32b270f9004102`. El archivo local de pruebas coincide con el del árbol solicitado. El delta de pruebas añade seis regresiones a `skills/orquestar/test_progreso.py` y extrae un auxiliar para el preflight.

## Qué discriminan las pruebas

D11 coloca la aprobación dentro de un ejemplo `<pre><code>` cuyas etiquetas tienen cuatro espacios de sangría dentro de `<details>`. D12 coloca `<code>bug-fix</code>` en una línea intermedia del párrafo citado en Markdown. En cada caso se prueba primero la cita como único posible dictamen y después se añade un rechazo propio. En D11 el rechazo sigue al cierre de `</details>`. En D12 una línea en blanco lo separa de la cita.

| Decisión observada para ambas entradas | Qué exige la prueba | Qué muestra el rojo adjunto |
|---|---|---|
| El principal devuelve código cero y solo cita una aprobación | Claude queda sin dictamen y la reserva Codex registra su rechazo en la misma invocación. Se comprueban los dos perfiles llamados y su orden. | En las métricas solo figura Claude. |
| El principal escribe su rechazo después de la cita | Se registra el rechazo de Claude y solo se llama al perfil principal. | Las métricas atribuyen a Claude la aprobación citada. |
| El informe canónico de una ficha `completed` solo contiene la cita | Tras confirmar el informe en Git, el preflight devuelve el ID y el motivo «sin veredicto formal» en la misma entrada. | El preflight devuelve una lista vacía. |

Los casos con rechazo propio también detectan una corrección que descarte todo el texto posterior a la cita. Las pruebas ejercitan la entrada de Hades con proveedores simulados y la lectura del informe desde un repositorio Git temporal.

## Hallazgos anteriores

- **N10 · 🟡 Media · Resuelto.** El control original conserva el ejemplo HTML sin sangría, la ficha completada, el commit del informe y la aserción sobre ID y motivo. El auxiliar aplica ahora el mismo control a D11 y D12. Destino `resolver`, cumplido por el desarrollador.
- **H1–H4 y N1–N9 de C1 · Resueltos.** El delta conserva sus pruebas. **D9 y D10 de producto · Resueltos** según las revisiones D precedentes. Las pruebas de procedencia histórica quedan fuera del cambio de esta ronda.
- **D11 · 🟠 Alta · Persiste en producto.** El ejemplo sangrado activa las tres decisiones erróneas de la tabla. Para `desarrollador` (Artemisa), destino `resolver` en C2. Mantener el límite del ejemplo hasta su cierre y reconocer el rechazo propio posterior.
- **D12 · 🟠 Alta · Persiste en producto.** La aprobación que continúa el párrafo citado produce los mismos tres fallos. Para `desarrollador` (Artemisa), destino `resolver` en C2. Conservar la continuidad de la cita a través del código en línea y reconocer el dictamen del párrafo siguiente.

**Hallazgos nuevos de pruebas:** ninguno.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Cada reproducción cubre la ausencia de dictamen propio, el rechazo explícito y el preflight de cierre. |
| Aserciones | 9/10 | Se observan llamadas, perfiles, veredictos y decisiones de cierre. El motivo del preflight se comprueba mediante una subcadena del diagnóstico. |
| Rojo correcto | 10/10 | Los seis fallos son de aserción en las tres decisiones previstas para cada entrada. Todas las pruebas alcanzan al consumidor que evalúan. |
| Estabilidad | 10/10 | Entradas literales, proveedores simulados y un repositorio Git temporal por prueba. Los resultados esperados son independientes del reloj y del orden de ejecución. |

**Límites y evidencia.** Revisión independiente de las pruebas del triaje de B-ADV-0044. La ejecución focalizada adjunta registró seis fallos de aserción en 4,491 s. Las trazas muestran la primera aserción fallida de cada caso. Las comprobaciones posteriores de perfiles e identidad de invocación se evaluaron por lectura. Se reutilizó el resultado verde de Ruff selectivo (`E9,F63,F7,F82`). El proyecto carece de comprobador de tipos configurado. Las 170 pruebas verdes corresponden a la ronda D anterior. La corrección del producto queda pendiente de C2 y de su revisión D. B-ADV-0045 a B-ADV-0047 tienen dictamen aparte.
