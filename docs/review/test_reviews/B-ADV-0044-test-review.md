**Veredicto:** APROBADO · **9,25/10**

# B-ADV-0044 · Reevaluación independiente de pruebas (C1)

Rama `hotfix/v1.1.3`. Árbol revisado `118e5e5ed1280b019580d1df22efcd4127a576ea`. Ronda anterior `d541cedb12000f740bd29d3f9ff9bd405c579e06`.

## Hallazgos pendientes de la ronda anterior

| Hallazgo | Estado | Destinatario | Destino |
|---|---|---|---|
| N5 🟠 · Huella del mandato rastreado | Resuelto | desarrollador | resolver |
| N6 🟡 · Atribución del cambio posterior a otro ID | Resuelto | desarrollador | resolver |

**N5.** La prueba captura la huella que recibe el proveedor en dos llamadas a la CLI con la misma ruta rastreada. Confirma la primera redacción y cambia únicamente el contenido de ese fichero en el WIP para la segunda. Exige dos huellas distintas. Excluir globalmente la ruta produciría dos valores iguales y fallaría esa aserción, incluso si `huella_producto` compartiera el defecto. En el subcaso temporal se mantiene la comprobación de que retirar el mandato cambia el árbol exacto y de que el proveedor debe recibir la huella del producto limpio. El único fallo acreditado de esta prueba corresponde a esa última igualdad.

**N6.** Tras acreditar la aprobación de `B-DEMO-0001`, el caso crea una ficha planificada para `B-DEMO-0002`. El arnés comprueba el paso y el segundo ID antes de confirmar el código, su ficha completada y su informe. La prueba exige una sola llamada a `bug-fix` para el segundo ID, que el selector pase a `revisar-version` y que el preflight quede vacío. La variante con huella anterior alcanza estas comprobaciones. La variante histórica sin huella propia se detiene antes, al aceptar la huella citada. Se conserva el caso inverso de dos commits del mismo intento e ID, que exige volver a `revisar-tarea`.

## Seguimiento de los demás hallazgos de pruebas

| Hallazgo | Estado | Destinatario | Destino | Comprobación conservada |
|---|---|---|---|---|
| H1 · Perfiles | Resuelto | desarrollador | resolver | Modelo estricto y secuencia principal–reserva en la recarga y el arranque manual. |
| H2 · Cuota | Resuelto | desarrollador | resolver | Llamada a la espera con la demora registrada y consumo de ambos intentos. |
| H3 · Notas | Resuelto | desarrollador | resolver | Dos commits limpios reformulan el impedimento con fechas fijas. El bucle para en la segunda llamada e identifica el paso y el ID. |
| H4 · Informe | Resuelto | desarrollador | resolver | La ausencia del informe se comprueba con el ID del paso ejecutado. |
| N1 · Aprobación caducada | Resuelto | desarrollador | resolver | La huella del producto anterior mantiene pendiente el actual. Declarar la huella vigente permite el cierre. |
| N2 · Diagnóstico | Resuelto | desarrollador | resolver | El lector consume la salida de `agente` y debe recuperar los cinco campos con sus valores. |
| N3 · Índice Git | Resuelto | desarrollador | resolver | HEAD, índice y WIP contienen versiones distintas. Se exige conservar las entradas preparadas. |
| N4 · Cierre por ambas entradas | Resuelto | desarrollador | resolver | La misma aprobación vigente debe permitir el cierre por `bug-fix` y por `revisar-tarea`. |

## Hallazgos nuevos de pruebas

Ninguno.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 9/10 | Se conservan los seis escenarios de B-ADV-0044. Los controles añadidos distinguen el mandato temporal del rastreado y el cambio del mismo intento del atribuido a un segundo ID. |
| Aserciones | 9/10 | Las diferencias se observan en el mandato recibido por el proveedor, el ID ejecutado, el siguiente paso seleccionado y los pendientes de release. |
| Rojo correcto | 10/10 | Los seis fallos llegan a aserciones sobre el comportamiento previsto. La ejecución dirigida registra cero errores de preparación. |
| Estabilidad | 9/10 | Los casos usan Git en repositorios temporales con configuración aislada, contenidos fijos y proveedores simulados. |

## Evidencia y límites

La verificación dirigida aportada para este árbol ejecutó 124 pruebas en 139,650 s. Persisten seis fallos de producto reproducidos por aserción. En H1 y D3 el selector adelanta la revisión de versión. En H2 se acepta una huella citada y en H3 falta la llamada a la reserva tras un veredicto citado. En D1 la reevaluación registra `progreso=False`. En D2 el mandato temporal altera la huella entregada. Los seis corresponden al desarrollador, con destino `resolver` en la corrección de producto. Las aserciones posteriores al primer fallo de cada caso quedan pendientes de ejecución en esa rama.

Se contrastó el delta de B-ADV-0044 entre ambos árboles y se reutilizó la evidencia aportada de unittest, Ruff selectivo y `git diff --check`. El proyecto carece de verificador de tipos configurado. La revisión se limita a C1. Se excluyeron B-ADV-0045, B-ADV-0046 y B-ADV-0047. No se inspeccionó la implementación ni se repitieron comprobaciones o la suite completa.
