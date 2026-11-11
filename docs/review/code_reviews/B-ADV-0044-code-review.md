**Veredicto:** RECHAZADO
Producto revisado: 486cc9cae2950935e605c9824f865ab69a127fc970a7eb904b3d778f903ee903
Rechazo reevaluado: c5e390eba8f0a366a5bd64bcc42e197fa766a9d2

# B-ADV-0044 · Revisión independiente de código D

**7,33/10.** D3, D6 y D8 quedan resueltos en los casos del rechazo anterior. La corrección de D6 introduce D9, un cierre indebido reproducido con una ficha antigua. Confirmar una copia literal de la aprobación de A permite cerrar B después de que Hades haya rechazado B.

## Hallazgo nuevo

### D9 · 🔴 Crítico · Confirmar la restauración de un informe histórico libera el cierre de un producto rechazado

En un repositorio Git temporal creé un ID en estado `completed`. Confirmé el producto A, donde `doble(n)` devuelve `2*n`, junto con una aprobación histórica sin huella y con una comprobación concreta de que el doble de tres es seis. En el siguiente commit cambié la función para que devolviera `n` y confirmé el rechazo de B. Restauré el informe de A desde Git y después confirmé únicamente ese archivo. Verifiqué que su blob era idéntico al de la aprobación original.

| Estado observado | Selector | Preflight de cierre |
|---|---|---|
| Rechazo confirmado de B | `revisar-tarea` | Incluye el ID por informe rechazado |
| Informe de A restaurado en el árbol de trabajo | `revisar-tarea` | Incluye el ID por aprobación restaurada |
| El mismo informe tras confirmar solo la copia | `revisar-version` | Devuelve `[]` |

También consulté `cierre_revisado` para `bug-fix`, con el commit del rechazo como base. Devolvió `True`, de modo que el bucle puede dar por completado el paso tras un error del arnés. El código de B seguía devolviendo tres.

**Causa.** En `adevv/revisiones.py:248`, al faltar la huella declarada, el commit de la copia aporta la huella de B. En la línea 253 se descarta la aprobación de A por la diferencia de producto antes de comparar su cuerpo. En la línea 293 basta entonces con que la emisión y el objetivo sean el mismo commit. El acto de confirmar la copia le atribuye una revisión de B.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Conservar la procedencia de una aprobación histórica restaurada al confirmarla. El caso de aceptación debe mantener el ID en `revisar-tarea`, incluirlo en `pendientes_cierre` y devolver `False` en `cierre_revisado`. Como control positivo, la aprobación histórica de B con explicación propia debe seguir liberando ambos consumidores tras la aprobación escueta de A.

## Reevaluación del rechazo anterior

| Hallazgo | Estado | Fundamento |
|---|---|---|
| D3 · Cerco exterior | **Resuelto** | La cabecera y el comparador histórico usan `contenido_del_informe`. Quitar el cerco exterior conserva las palabras de la aprobación revocada. El selector y el preflight mantienen pendiente la copia del mismo producto y aceptan la reevaluación propia. |
| D6 · Aprobación histórica propia de B | **Resuelto** | El commit de emisión permite atribuir a B su aprobación sin huella y con explicación propia. Los dos recorridos de C1 liberan selector y preflight, tanto con rechazo previo de A como con rechazo de B. El control con huella explícita también pasa. D9 documenta por separado el efecto sobre una copia confirmada. |
| D8 · Respuesta durante la espera | **Resuelto** | La espera entrega las respuestas incorporadas. Tanto la espera como la cabecera del bucle llaman a `renovar_intentos_de_respuestas` con sus IDs. Con dos intentos por ID, A recibe una llamada antes de responder y dos después. B conserva su intento consumido. |
| H1–H7, D1, D2, D4, D5 y D7 | **Resueltos en los recorridos acreditados** | Se mantienen los controles de objetivo por ID, huella y referencia del informe, lectura de citas, reservas, consumo, índice y dependencias. |

## Alcance y verificación

Revisé el delta de producción de B-ADV-0044 desde `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`, con la atribución por commit de los cambios concurrentes. Contrasté la firma por paso con los entregables del diseño, el límite de reintentos con las salidas por error y cuota, y la vigencia del dictamen con sus tres consumidores. La recarga transfiere los contadores por paso e ID. El arranque manual abre otra tanda y conserva las métricas y el trabajo en Git. La marca del diagnóstico de suite conserva su contrato JSON.

Antes de escribir el informe comprobé que los archivos rastreados coincidían con el árbol de evidencia `0c523fc036bc554e0ade546389e173c3819c0e2b`, que su huella de producto coincidía con la cabecera y que el último commit del informe era el rechazo indicado. La reproducción de D9 utilizó el código de ese árbol en un repositorio temporal que se eliminó al terminar.

**Evidencia reutilizada.** C1 aprobó las regresiones con 9,50/10 tras observar cuatro fallos de comportamiento y dos controles verdes. En el árbol revisado pasaron los seis casos focalizados y las 165 pruebas del triaje. La suite completa corresponde al cierre de versión.

**Análisis estático.** Ruff selectivo (`E9,F63,F7,F82`), el escaneo de secretos y los controles de espacios del trabajo local y de las rutas del ID terminaron en verde. El control global desde la base devolvió 2 por espacios finales en la ficha histórica de B-ADV-0047. `--calidad` devolvió 0 con formato y lint omitidos por falta de configuración reconocida. El proyecto carece de tipado configurado y el delta conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | D9 libera tres decisiones de cierre con un rechazo aún vigente. |
| Seguridad | 9/10 | Las consultas Git usan argumentos separados. El escaneo de secretos está en verde. |
| Conformidad | 6/10 | El presupuesto por ID sigue el diseño. D9 incumple la barrera de cierre revisado de B-ADV-0039. Se mantiene la arquitectura de Python y Git del plan de plataforma. |
| Calidad | 8/10 | Los lectores comparten la normalización del informe y el bucle comparte la renovación por respuesta. La atribución histórica confunde el commit de copia con la emisión. |
| Eficiencia | 8/10 | La consulta de revisiones recorre la historia de la ruta canónica. Solo compara las huellas históricas cuando hay aprobaciones revocadas. |
| Documentación | 8/10 | La guía identifica el límite y el estado que persiste. D9 contradice la garantía documentada para una aprobación restaurada. |
