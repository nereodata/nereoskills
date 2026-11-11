**Veredicto:** RECHAZADO
Producto revisado: b107cb5fec8a7787e6607b604a60229695b3dd4c143643b16bdcd2ac20a4e662
Rechazo reevaluado: 3d7c803e8403da1f8a6aab8cb34f87637706e9a0

# B-ADV-0044 · Revisión de código de la fase D

**Media 7,33/10.** D9 queda resuelto en sus tres consumidores. D10 permite cerrar un producto rechazado mediante una nota de archivo. D11 permite registrar como propio el veredicto de un ejemplo y omitir la reserva de Hades.

## Reevaluación de D9

Al confirmar la copia literal del informe sin huella de A, `acreditacion_anterior` encuentra las palabras de la aprobación revocada incluso cuando el commit de la copia ya contiene B. La regresión pasó de tres aserciones fallidas en C1 a tres decisiones correctas sobre el producto revisado. El selector pide `revisar-tarea`, el preflight incluye el ID y `cierre_revisado` devuelve `False` tras el error de `bug-fix`.

El control positivo también pasa. Tras la aprobación escueta de A y el rechazo de B, la primera emisión histórica de B contiene su propia comprobación. El selector avanza a `revisar-version` y el preflight devuelve `[]`. **D9 resuelto** por Artemisa en C2. H1–H7 y D1–D8 conservan su resolución en los recorridos acreditados, incluidos la restauración del cuerpo con cambios de marcado, la referencia al rechazo y la renovación de intentos por ID durante la espera.

## Hallazgos nuevos

### D10 · 🔴 Crítico · Una nota posterior a la copia confirmada de una aprobación escueta permite cerrar B

Secuencia con una ficha `completed` y el informe canónico del mismo ID. Los resultados de esta tabla se deducen de las ramas del código. La evidencia ejecutada de C1 cubre la copia con cuerpo y el control positivo descritos arriba.

| Commit | Cambio en Git | Efecto en la revisión |
|---|---|---|
| A | Aprobar A con la única línea `**Veredicto:** APROBADO`, sin huella ni cuerpo. | La aprobación pertenece a A. |
| R | Introducir un defecto en B y confirmar su rechazo. | B queda pendiente. |
| C | Restaurar desde A únicamente el informe y confirmar la copia literal. | Ambos cuerpos están vacíos. El comparador reconoce la restauración y mantiene pendiente B. |
| N | Añadir al informe de C la línea «Se archiva el expediente el 11 de noviembre» y confirmar solo ese archivo. | El selector avanza a `revisar-version`, el preflight queda vacío y `cierre_revisado` para `bug-fix` con base R devuelve `True`. El defecto de B sigue presente. |

En `adevv/revisiones.py:249`, las palabras se extraen del texto actual de N. La emisión sigue siendo C porque N conserva el veredicto y carece de huella nueva. En la línea 252, la nota activa `not anteriores and bool(palabras)`. Al diferir los productos de A y C, se descarta la aprobación revocada. La validación final acepta la emisión de C sobre B. El historial permite distinguir ambos casos: en C quedó registrada la copia escueta y la explicación apareció un commit después. En el control positivo, la comprobación de B ya figuraba en la primera emisión.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Mantener la procedencia de la copia durante las ediciones de seguimiento. En C y N los tres consumidores deben conservar B pendiente. Preservar el control positivo de una aprobación propia de B sin huella.

### D11 · 🟠 Alta · Un ejemplo HTML de la respuesta técnica cuenta como dictamen de Hades

Una respuesta normal del proveedor puede contener este texto literal:

```text
No pude leer el repositorio. El informe anterior contenía este ejemplo:

<pre><code>
Veredicto: APROBADO
</code></pre>

La revisión sigue pendiente.
```

En `adevv/revisiones.py:106`, `lineas_del_informe` conserva la línea interior. El lector reconoce cercos Markdown, sangría y citas, pero las etiquetas `<pre><code>` no abren un bloque de ejemplo para ese lector. En la línea 140, `cabecera_informe` acepta la declaración interior. Con código de salida cero, `skills/orquestar/orquestar.py:2379` registra la aprobación en métricas y la llamada termina antes de probar la reserva autorizada. El mismo recorrido en un informe canónico puede tomar el ejemplo por su declaración formal. Este hallazgo se identifica por lectura del delta acumulado. Los controles anteriores de citas HTML ejercitan `blockquote`.

**Para** `desarrollador` (Artemisa). **Destino** `resolver` en C2. Excluir del lector compartido las declaraciones encerradas en bloques de código HTML. La respuesta anterior debe dejar al principal sin dictamen y permitir la reserva. Un rechazo propio escrito después de cerrar el ejemplo debe seguir registrándose como rechazo del principal.

## Alcance, evidencia y limitaciones

Revisé el delta de producción del ID desde `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` y el cambio de esta ronda respecto del árbol D anterior. Contrasté el cálculo de progreso con el triaje y el diseño, el presupuesto por paso e ID con las vías de cuota y recarga, la lectura del dictamen con la selección de reservas y la acreditación histórica con las tres decisiones de cierre. Los cambios intercalados de B-ADV-0045, B-ADV-0046 y B-ADV-0047 tienen revisión independiente. El delta del ID mantiene el stack Python/Git y las capas del plan de plataforma.

Antes de escribir el informe, los archivos rastreados coincidían con el árbol de evidencia `e40be2b764ee04736af04642d760d44a5c0b056d`. Comprobé su huella de producto y el último commit del informe canónico. C1 está aprobada con 9,75/10. Reutilicé el verde de los dos casos focalizados (4,095 s) y de las 166 pruebas del triaje (205,746 s). D10 y D11 son recorridos estáticos. La suite completa corresponde al bucle al cierre de versión.

Ejecuté `adevv orquestar --calidad --base 4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` sin escritura. Devolvió 0 y comunicó la omisión de formato y lint por ausencia de herramientas reconocidas. La evidencia separada de Ruff cubre `E9,F63,F7,F82`. Pasaron los controles de espacios del WIP y de las rutas del ID desde la base. El primer intento del escaneo de secretos falló por las comillas de PowerShell y el comando corregido devolvió 0 sobre el mismo árbol. El proyecto carece de comprobador de tipos configurado y el ID conserva las dependencias.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | D9 pasa en los tres consumidores. D10 permite un cierre indebido y D11 omite una reserva autorizada. |
| Seguridad | 9/10 | Las consultas Git usan argumentos separados y el escaneo de secretos del delta pasó. |
| Conformidad | 6/10 | Se respetan el presupuesto por ID y la arquitectura. D10 incumple la barrera de cierre y D11 la exigencia de un dictamen propio. |
| Calidad | 8/10 | Los consumidores comparten la decisión de vigencia. Esa decisión mezcla el cuerpo de la emisión con el de su edición posterior. |
| Eficiencia | 8/10 | La revisión recorre el historial de la ruta canónica y consulta árboles Git para atribuir productos. |
| Documentación | 8/10 | La guía explica el límite de reintentos y la persistencia. La garantía de conservar la acreditación ante notas falla en D10. |
