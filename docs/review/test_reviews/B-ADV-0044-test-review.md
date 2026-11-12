**Veredicto:** APROBADO

# B-ADV-0044 · Reevaluación C1 de las pruebas de D27–D29

**Media 9,75/10.** Cuatro de las siete entradas reproducen el defecto en ambos consumidores. Los tres controles pasan en ambos. En D27, la continuación con dos espacios reproduce el mismo fallo que la continuación al margen. El control que conserva el rechazo tiene tres espacios, alineados con el texto del primer elemento.

| Hallazgo | Entrada que falla | Métricas de Hades en `motor.agente` | Resultado de `pendientes_cierre` | Control que pasa |
|---|---|---|---|---|
| D27 | Continuación con cero o dos espacios antes de `El separador` | Claude queda sin dictamen y Codex registra `APROBADO` en ambas variantes. | En ambas, la ficha queda pendiente por «informe sin veredicto formal». | Tres espacios antes de `El separador`. |
| D28 | Cadena JSON `"<pre>"` dentro de `script` | Claude registra el `APROBADO` del ejemplo posterior. | Devuelve `[]` y permite cerrar la ficha rechazada. | Cambiar solo la cadena a `"<div>"`. |
| D29 | Subrayado Setext de un guion seguido de un espacio | Claude queda sin dictamen y Codex registra `APROBADO`. | La ficha queda pendiente por «informe sin veredicto formal». | Tres guiones con el mismo espacio final. |

En los tres controles, el arnés observa una sola llamada a Claude con el modelo principal y una sola métrica de Hades con `RECHAZADO`. El preflight encuentra el ID `B-DEMO-0001` y «informe rechazado» en la misma entrada. Exigir ese motivo detecta la pérdida del rechazo en D27 y D29 incluso cuando el cierre sigue bloqueado.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Cada variante entrega el mismo informe a los dos consumidores en subpruebas separadas. Un fallo del proveedor permite observar también la decisión de cierre. |
| Aserciones | 9/10 | El arnés exige las métricas y llamadas esperadas por proveedor y modelo. El preflight lee el informe canónico confirmado junto con la ficha completada y comprueba el ID y el motivo mediante subcadenas. |
| Rojo correcto | 10/10 | Los ocho fallos son de aserción y muestran los resultados de la tabla. Los controles alcanzan las mismas comprobaciones con la misma preparación. |
| Estabilidad | 10/10 | Cada método usa un repositorio Git temporal propio, configuración Git aislada y respuestas fijas de los proveedores simulados. Las expectativas son independientes del reloj y del orden de ejecución. |

## Hallazgos y destino

**Anteriores.** H1–H4 y N1–N10 siguen resueltos en C1. El delta añade los siete métodos y sus datos de entrada. La revisión D aportada dio por resueltos D24–D26.

**Nuevos.** C1 queda sin hallazgos. D27, D28 y D29 persisten en el producto y quedan para Artemisa (`desarrollador`), con destino `resolver` en C2.

## Evidencia

El archivo de pruebas revisado coincide con el del árbol `a077777df66d23f488b9c129934602ec9d4ef75c`. La ejecución focalizada adjunta registró `FFFFFF.FF..`, `Ran 7 tests in 7.480s` y `FAILED (failures=8)`, con código 1. En las cuatro subpruebas rojas del proveedor, la aserción sobre métricas falló antes de alcanzar la de llamadas efectivas.

Se reutilizaron esa ejecución y el resultado de `python -m ruff check --select E9,F63,F7,F82 skills/orquestar/test_progreso.py` (`All checks passed!`, código 0). El proyecto carece de tipador configurado.