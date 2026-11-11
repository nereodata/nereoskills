**Veredicto:** APROBADO · **9,75/10**

# B-ADV-0044 · Reevaluación C1 de D21, D22 y D23

Las ocho pruebas nuevas distinguen dos errores de atribución del dictamen de Hades en los dos puntos donde cambian una decisión del motor. En D21 se acepta una aprobación citada. En D22 se pierde el rechazo del principal y se acepta la aprobación de la reserva. Cada control modifica únicamente un salto de línea y conserva el mismo rechazo esperado.

| Entrada | Dictamen registrado por `motor.agente` | Resultado de `pendientes_cierre` para `B-DEMO-0001` |
|---|---|---|
| D21 · El primer ejemplo contiene un salto antes de su cierre. El segundo contiene un cierre literal entre acentos graves. | Falla. Claude registra la aprobación del ejemplo. | Falla. La lista vacía permite cerrar la ficha rechazada. |
| Control D21 · Se suprime el salto antes del primer cierre. | Pasa. Una llamada a Claude con el modelo principal y una única métrica con su rechazo. | Pasa. La ficha queda pendiente por «informe rechazado». |
| D22 · El encabezado termina en un acento grave y el rechazo abre el párrafo siguiente. | Falla. Claude queda sin dictamen y Codex registra la aprobación de reserva. | Falla. La ficha queda pendiente por «informe sin veredicto formal». |
| Control D22 · Se añade una línea vacía tras el encabezado. | Pasa. Una llamada a Claude con el modelo principal y una única métrica con su rechazo. | Pasa. La ficha queda pendiente por «informe rechazado». |

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Cada defecto y su control llegan tanto al proveedor como al preflight de cierre. La verificación dirigida del triaje incluye el módulo completo `skills.orquestar.test_progreso` y recoge las ocho pruebas. |
| Aserciones | 9/10 | El arnés registra las llamadas efectivas por proveedor y modelo y contrasta las métricas de Hades. El preflight lee el informe canónico confirmado junto con la ficha completada y exige ID y motivo en la misma entrada mediante subcadenas. |
| Rojo correcto | 10/10 | Los cuatro fallos son de aserción. Identifican el veredicto atribuido al proveedor o la decisión de cierre equivocada. Los cuatro controles pasan con la misma preparación. |
| Estabilidad | 10/10 | Cada prueba usa su propio repositorio Git temporal, configuración Git aislada y respuestas fijas de proveedor. Las aserciones funcionales son independientes de la duración. |

## Seguimiento

Los hallazgos anteriores de pruebas H1–H4 y N1–N10 siguen resueltos. D20 quedó resuelto en la revisión D anterior. Esta ronda añade dos generadores de informes y ocho pruebas en `test_progreso.py`. **Hallazgos nuevos o pendientes de C1: ninguno.**

| Hallazgo de producto | Estado | Para | Destino y comprobación |
|---|---|---|---|
| D21 · 🟠 Alta | Persiste, reproducido en ambos consumidores. | Artemisa (`desarrollador`) | `resolver` en C2. Con ambas presentaciones, registrar el rechazo del principal en una llamada y mantener la ficha pendiente por «informe rechazado». |
| D22 · 🟠 Alta | Persiste, reproducido en ambos consumidores. | Artemisa (`desarrollador`) | `resolver` en C2. Reconocer el rechazo que sigue al encabezado, con y sin línea vacía, y conservar la llamada única y el motivo «informe rechazado». |
| D23 · 🟡 Media | Persiste como pendiente de rendimiento según la medición de D. | Artemisa (`desarrollador`) | `resolver` en C2. Repetir por separado la medición comparativa de `declaracion` descrita abajo. |

Para D23, la referencia de D es un solo párrafo que repite la línea «Se comprobo `archivo.py`.», seguido de una línea vacía y el rechazo. Con 300, 600 y 1.200 líneas se midieron 0,078 s, 0,325 s y 1,251 s. Al duplicar la entrada, el tiempo casi se cuadruplica. En C2 corresponde comparar antes y después con las mismas entradas y condiciones, comprobar que las tres devuelven el rechazo y contrastar cómo crece el tiempo. La medición queda separada de las pruebas funcionales, que no dependen de un umbral de reloj.

## Evidencia

La evidencia adjunta de `--verificar` corresponde al árbol `7449b14424d6198eabcc5aa09396c8389a96a5de` de `hotfix/v1.1.3`. El archivo de pruebas del árbol de trabajo coincide con el revisado. La ejecución focalizada registró `FF..FF..` en 5,872 s. En los dos rojos de proveedor, la discrepancia de métricas detuvo la prueba antes de la aserción sobre llamadas efectivas. Los dos controles de proveedor sí alcanzaron esa aserción.

Se reutilizaron la ejecución focalizada y el resultado verde de Ruff selectivo (`E9,F63,F7,F82`). El proyecto carece de tipador configurado. Para C2 quedan la repetición de la medición D23 y la ejecución dirigida del triaje sobre el árbol corregido.
