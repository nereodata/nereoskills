**Veredicto:** APROBADO · **9,75/10**

# B-ADV-0044 · Reevaluación C1 de las pruebas de D20

Las cuatro pruebas nuevas reproducen D20 y su control en los dos consumidores. El informe del principal muestra la apertura de `<pre>` con el atributo `@click` entre acentos graves y emite un rechazo en el párrafo siguiente. Entre las dos entradas solo cambia el separador entre `pre` y `@click`. Los controles de D19 conservan la etiqueta HTML efectiva dentro de un `<div>`, con una aprobación dentro del ejemplo y el rechazo del principal fuera de él.

| Entrada | Resultado observado en `motor.agente` | Resultado observado en `pendientes_cierre` |
|---|---|---|
| D20 · Literal con salto de línea | **Falla.** Las métricas registran a Claude sin dictamen y a Codex con la aprobación de reserva. | **Falla.** El ID figura pendiente por «informe sin veredicto formal». La prueba exige «informe rechazado». |
| Control D20 · Mismo literal con espacio | Pasa. Una llamada a Claude con el modelo principal y una única métrica de Hades con su rechazo. | Pasa. El ID figura pendiente por «informe rechazado». |
| Control D19 · HTML efectivo con `@click` | Pasa. El principal registra su rechazo en una sola llamada. | Pasa. El ID figura pendiente por «informe rechazado». |

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Las pruebas ejercitan la selección de la reserva y el motivo de cierre pendiente para el literal en ambas presentaciones. El control D19 protege la interpretación de HTML efectivo en ambos recorridos. |
| Aserciones | 9/10 | El arnés registra las llamadas por proveedor y modelo, y comprueba aparte las métricas de Hades. El preflight exige el ID y el motivo por subcadena en la misma entrada después de confirmar la ficha completada y el informe canónico. |
| Rojo correcto | 10/10 | Los dos fallos son de aserción y reproducen las decisiones observadas en D20. Cambiar el salto por un espacio hace pasar las dos pruebas con los mismos datos y comprobaciones. |
| Estabilidad | 10/10 | Cada caso crea su propio repositorio Git temporal con configuración aislada. Las respuestas de ambos proveedores son fijas y el resultado esperado es independiente del reloj. |

## Seguimiento

- **Hallazgos anteriores de C1.** H1–H4 y N1–N10, resueltos en las rondas anteriores. El delta añade cuatro pruebas y su generador de texto. Conserva las aserciones y la preparación ya revisadas.
- **Hallazgos nuevos de C1.** Ninguno.
- **D19 · Resuelto.** Los dos controles del árbol revisado acreditan el rechazo exterior con `@click`.
- **D20 · Persiste en el producto.** Prioridad 🟠 alta. Destino `resolver` en C2. Responsable ya asignada en D, Artemisa (`desarrollador`). La corrección debe conservar el rechazo del principal en una sola llamada y el motivo «informe rechazado» para `B-DEMO-0001`.

## Evidencia y alcance

El archivo de pruebas local coincide con el del árbol `ebe54c0b8d89513fb0ce67cad9b0d903c6a10855`. El registro de ese árbol acredita seis pruebas en 4,211 s, con dos fallos de aserción y cuatro controles verdes. En el caso multilínea, la discrepancia de métricas detuvo la prueba antes de comparar la lista de llamadas efectivas. Esa comparación sí se ejecutó en ambos controles de proveedor.

Se reutilizaron la ejecución focalizada del triaje y el resultado verde de Ruff selectivo (`E9,F63,F7,F82`). El proyecto carece de tipador configurado.
