**Veredicto:** RECHAZADO

# B-ADV-0044 · Reevaluación independiente de pruebas

Rama `hotfix/v1.1.3`. Árbol `d541cedb12000f740bd29d3f9ff9bd405c579e06`. Ronda de pruebas anterior `5ff63caabd43347c22539f87f87c8c827a72db6e`. **Media 8,50/10.** El hallazgo alto N5 impide aprobar C1. El control de D2 permite excluir de la huella un archivo rastreado cuyo contenido debe quedar cubierto por la revisión.

## Seguimiento de la ronda anterior

| Hallazgo de pruebas | Estado | Comprobación conservada |
|---|---|---|
| H1 · Perfiles | Resuelto | Se observan el modelo estricto y la secuencia principal–reserva antes y después de la recarga y en el arranque manual. |
| H2 · Cuota | Resuelto | La espera recibe la demora registrada para la reserva agotada. Se comprueba el consumo de ambos intentos. |
| H3 · Notas de diagnóstico | Resuelto | Dos invocaciones confirman redacciones y fechas distintas en la ficha y el resumen. Se comprueban los dos commits, la parada y el ID. |
| H4 · Informe del ID correcto | Resuelto | La comprobación de ausencia del informe usa el ID seleccionado para cada paso. |
| N1 · Aprobación caducada | Resuelto | La huella de A mantiene B pendiente. Sobre el mismo B, declarar su huella permite el cierre por `bug-fix` y libera el preflight. |
| N2 · Diagnóstico estructurado | Resuelto | El lector de diagnósticos recibe la salida de `agente` y debe recuperar los cinco campos con sus valores. |
| N3 · Índice de Git | Resuelto | HEAD, índice y WIP contienen tres versiones distintas. Se exige conservar las entradas preparadas. |
| N4 · Entrada por `revisar-tarea` | Resuelto | Tras confirmar la aprobación de B se exige el cierre por `bug-fix` y por `revisar-tarea` con el mismo ID, base e informe. |

## Regresiones solicitadas en la revisión de código

Las seis pruebas dirigidas fallaron por aserción en 8,820 s. La tabla identifica la primera divergencia observada en cada caso. Las aserciones posteriores describen lo que se exigirá al corregirla.

| Hallazgo de código | Rojo observado en este árbol | Comportamiento exigido por la prueba |
|---|---|---|
| H1 · Relanzamiento | Tras confirmar el cierre de A y la corrección B del mismo ID en dos commits y salir con código 1, el selector eligió `revisar-version`. | Volver a `revisar-tarea` para ese ID, mantenerlo pendiente en el preflight y liberarlo tras reevaluar B. El control para otro ID se valora en N6. |
| H2 · Huella citada | El cierre por `bug-fix` aceptó el informe histórico sin huella propia después de añadirle la huella de B dentro de un mandato citado. | Mantener el cierre pendiente hasta que el revisor declare la huella de B en su propio dictamen. |
| H3 · Veredicto citado | Solo se registró el proveedor principal al devolver una cita cercada con `~~~markdown` y código 0. | Registrar el principal sin veredicto y el rechazo propio de la reserva dentro de la misma invocación. |
| D1 · Reevaluación como avance | La prueba independiente alcanzó la fila del paso y encontró `progreso=False` después de aprobar B en el último intento. | Registrar avance, conservar `completed` y dejar vacío el preflight. El caso reproduce D1 aunque el caso combinado se detenga antes en H1. |
| D2 · Mandato efímero | Con `--prompt-file` y un nombre libre, la huella recibida por el proveedor difería de la calculada tras retirar el temporal. | Excluir el temporal de la huella revisada y conservar la diferencia entre los árboles exactos antes y después de retirarlo. La rama rastreada tiene la carencia N5. |
| D3 · Informe histórico restaurado | Al restaurar en el WIP la aprobación histórica de A sobre el rechazo confirmado de B, el selector eligió `revisar-version`. | La aprobación histórica permite el preflight de A. La copia restaurada sobre B debe dejar ese ID pendiente tanto en selección como en preflight. |

## Hallazgos nuevos de pruebas

**N5 🟠 ALTA · El control de D2 puede pasar aunque el producto pierda un archivo rastreado.** Para `desarrollador`. Destino `resolver`. En `test_mandato_efimero_fuera_de_huella_pero_dentro_de_evidencia`, la rama rastreada comprueba que el árbol exacto se conserva. Para validar el valor entregado al proveedor, obtiene el esperado de `huella_producto` sobre ese mismo árbol. Una corrección que excluyera siempre `mandato temporal.txt` en esa función pasaría ambas ramas. Editar únicamente ese archivo versionado podría entonces conservar una aprobación caducada. Mantener la pareja actual y capturar la huella enviada para dos contenidos distintos del mismo mandato rastreado, dejando igual el resto del producto. Exigir que esas huellas difieran y que el temporal siga dando la huella del producto limpio. Este contraste detecta la exclusión global sin reproducir el algoritmo en el test.

**N6 🟡 MEDIA · El control positivo de H1 carece de un segundo ID identificable.** Para `desarrollador`. Destino `resolver`. En `comprobar_reevaluacion`, el commit posterior modifica `otro.py` y lleva el mensaje `otra tarea`. La única ficha del repositorio sigue siendo la del primer bug. La aserción cubre un cambio posterior ajeno al informe, pero la preparación no permite comprobar la atribución del cambio a otro ID que pidió H1. Preparar dos fichas, producir el cambio posterior durante el paso del segundo ID y exigir que el primero conserve su aprobación al consultar selector y preflight. Conservar el caso en rojo de los dos commits del mismo intento.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 8/10 | Se conservan los seis escenarios de B-ADV-0044 y se reproducen los seis defectos de la última revisión de código. N5 y N6 limitan dos controles positivos. |
| Aserciones | 7/10 | Selección, preflight, progreso y perfiles se observan en sus salidas. La igualdad de huellas en la rama rastreada de D2 admite el defecto descrito en N5. |
| Rojo correcto | 10/10 | Los seis casos fallan al observar el comportamiento que motivó cada regresión. Todos alcanzan su aserción sin errores de preparación. |
| Estabilidad | 9/10 | Git trabaja en repositorios temporales con configuración aislada. Los casos controlan las respuestas de los proveedores, la espera y los contenidos comparados. |

Se contrastó el delta de pruebas con el árbol indicado y se reutilizaron sus registros de `unittest` y Ruff selectivo. Las 119 pruebas de la ronda previa corresponden a otro árbol. Se excluyeron los commits de B-ADV-0045 y B-ADV-0046, incluido el caso de métricas corruptas que comparte fichero con B-ADV-0044. El dictamen se limita a las pruebas y deja la corrección de producto para la revisión de código.
