**Veredicto:** APROBADO · **9,75/10**

# B-ADV-0044 · Reevaluación C1 de las pruebas de D19

Las cuatro pruebas nuevas reproducen el caso del rechazo D y su control en los dos consumidores. Comparten el mismo fragmento. Dentro de un `<div>`, el ejemplo `<pre>` contiene una aprobación y, después de `</div>` y una línea en blanco, el revisor emite su rechazo. Entre el caso D19 y el control solo cambia el nombre del atributo, de `@click` a `title`.

| Consumidor | Resultado exigido en ambos casos | Rojo observado con `@click` | Control con `title` |
|---|---|---|---|
| `motor.agente` | Una única llamada a Claude con el modelo principal y una única métrica de Hades con su rechazo. | La métrica atribuyó a Claude la aprobación del ejemplo. | Claude registró el rechazo en una sola llamada. |
| `pendientes_cierre` | La ficha completada figura pendiente con su ID y el motivo «informe rechazado». | La lista de pendientes estaba vacía. | El ID figuró pendiente por «informe rechazado». |

El arnés simula la salida de los proveedores con código cero y registra por separado las llamadas efectivas. Con `@click`, la primera discrepancia de métricas detuvo la prueba antes de la aserción sobre las llamadas. Esa última aserción se revisó por lectura y sí se alcanzó con `title`. El preflight consulta un repositorio Git temporal después de confirmar la ficha y el informe en su ruta canónica.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | D19 y el control que cambia solo el atributo ejercitan ambos consumidores. Pasaron también las dos pruebas de D17 con `x<y` y las dos de D15 con `<pre>` literal dentro de un atributo multilínea. |
| Aserciones | 9/10 | El proveedor exige el dictamen y la secuencia exacta de llamadas. El preflight comprueba el ID y el motivo por subcadena en una misma entrada. |
| Rojo correcto | 10/10 | Ambos fallos alcanzaron la decisión observable que motivó el rechazo D. Los seis controles pasaron. |
| Estabilidad | 10/10 | Cada prueba usa su propio repositorio, configuración Git aislada y respuestas fijas. El resultado es independiente del reloj y del orden de ejecución. |

## Evidencia y seguimiento

El delta local desde el rechazo D coincide con el adjunto. El archivo de pruebas corresponde al blob `7123f085dcc65a99155f068d7dece7f8c1507bd7`. El registro del árbol `9cff851c2b14e88253f2b816f57de1972f3fbe4f` acredita ocho pruebas en 5,557 s, dos fallos de aserción con `@click` y Ruff selectivo en verde. Se reutilizó esa ejecución. El proyecto carece de tipador configurado.

- **Hallazgos nuevos de C1.** Ninguno. H1–H4 y N1–N10 siguen resueltos en los recorridos acreditados por la revisión de pruebas anterior.
- **Seguimiento de producto.** D16, D17 y D18 constan como resueltos en el último informe D. D19 persiste en ambos consumidores y ya está asignado a Artemisa (`desarrollador`, destino `resolver` en C2).
