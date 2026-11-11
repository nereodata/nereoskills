**Veredicto:** RECHAZADO
Producto revisado: 3fca7b09e1962dd3fb4521f634090ffab72a10338e96123ab11d0b9ced9629c9

# B-ADV-0044 · Reevaluación independiente de código (D)

**Media 7,00/10.** Rama `hotfix/v1.1.3`. Árbol `c311964fe4ef788c496c2f459de194ebbab85075`. Ronda D anterior `5f9b5ac7f3f63b8beb0717dc32dc8ced1c681141`.

H1, H4–H7, D1 y D2 quedan resueltos. Persisten H2, H3 y D3. Las seis regresiones que estaban en rojo en C1 ya pasan. Los tres casos siguientes alcanzan las mismas decisiones de producción por entradas distintas.

## Hallazgos que persisten

**H2 🔴 · Intercalar una nota puede acreditar producto nuevo con una aprobación antigua.** Estado **persiste**. Para `desarrollador` (Artemisa). Destino `resolver`. En `adevv/revisiones.py:137`, la reconstrucción de la emisión termina cuando cambia la pareja de veredicto y huella. Confirmé un informe que aprobaba A con su huella, cambié el producto a B y consulté el cierre contra HEAD. Devolvió «informe anterior al cambio de producto». Después inserté una línea de seguimiento entre el veredicto y la huella y confirmé solo esa edición. El informe seguía conteniendo la huella de A. El lector pasó a interpretarlo como histórico sin huella y atribuyó su emisión al commit de la nota. La misma consulta de cierre devolvió una cadena vacía y el preflight devolvió `[]`. La huella de un mandato cercado ya se descarta correctamente. Falta conservar la acreditación anterior cuando una edición administrativa desplaza o elimina la huella propia. B debe seguir pendiente hasta que una reevaluación lo acredite.

**H3 🟠 · Una respuesta técnica puede registrar como propio el veredicto de una cita.** Estado **persiste**. Para `desarrollador` (Artemisa). Destino `resolver`. En `adevv/revisiones.py:64`, el filtro de citas trabaja línea a línea. Pasé al lector una respuesta que empezaba con «No pude revisar.», seguida por este fragmento y un párrafo final «Sigue pendiente.»:

```markdown
> Transcribo el resultado anterior:
**Veredicto:** APROBADO
```

La segunda línea continúa el párrafo citado en Markdown. El lector devolvió `('APROBADO', None)`. Obtuve el mismo resultado encerrando el veredicto entre líneas `<blockquote>` y `</blockquote>`. Con retorno 0, `agente` registra la aprobación y omite la reserva elegible. El caso de la ronda anterior con cerco de tildes sí queda corregido. La respuesta técnica debe dejar la invocación sin dictamen propio y permitir la reserva. Debe seguir admitiéndose el informe actual entregado íntegro para transcripción.

**D3 🔴 · Restaurar una aprobación con huella puede revocar un rechazo posterior.** Estado **persiste**. Para `desarrollador` (Artemisa). Destino `resolver`. En `adevv/revisiones.py:150`, si el informe del WIP declara una huella, su igualdad con la del producto basta aunque el historial no acredite esa emisión como vigente. Confirmé una aprobación de A y después un rechazo del mismo A, ambos con su huella correcta. La consulta devolvió «informe rechazado». Restauré en el WIP la copia exacta del primer informe, sin modificar el código ni emitir otro dictamen. La consulta que utiliza el selector devolvió una cadena vacía y el preflight devolvió `[]`. La nueva guarda sí cubre el informe histórico sin huella sobre el rechazo de un producto distinto. Falta conservar la precedencia del rechazo confirmado ante la copia identificable de una aprobación anterior del mismo producto. Una reevaluación posterior acreditada debe poder levantarlo.

## Hallazgos resueltos

| Hallazgo | Estado | Para | Destino | Evidencia |
|---|---|---|---|---|
| H1 🔴 · Objetivo del intento al relanzar | Resuelto | desarrollador | resolver | El bucle registra el último HEAD del intento en `commit_producto`. La consulta recupera un commit del ID que es ancestro del HEAD actual. El cambio posterior del mismo intento mantiene la revisión pendiente al relanzar y el paso del segundo ID conserva la aprobación del primero. |
| H4 🟠 · Reserva tras salida normal sin dictamen | Resuelto | desarrollador | resolver | Al recibir una respuesta reconocida como técnica, el agente registra el consumo y prueba la siguiente configuración elegible de la invocación. H3 afecta a la clasificación previa. |
| H5 🟠 · Reintentos técnicos y promoción | Resuelto | desarrollador | resolver | La métrica del intento lleva `revision_pendiente` también antes de la conmutación. Los intentos técnicos sin avance quedan fuera del contador de promoción y conservan su consumo. |
| H6 🟠 · WIP rastreado e ignorado | Resuelto | desarrollador | resolver | La instantánea importa las entradas del índice real en un índice temporal antes de aplicar el WIP. Conserva el contenido preparado por el usuario. |
| H7 🟡 · Dependencias históricas | Resuelto | desarrollador | resolver | Selector y recuperación usan `faltan_dependencias` para decidir cuándo queda satisfecho el paso. |
| D1 🟠 · Reevaluación vigente en el último intento | Resuelto | desarrollador | resolver | La firma de desarrollo consulta `motivo_revision` para el informe de código. El paso de pendiente a vigente registra avance y conserva la ficha completada en el límite de intentos. |
| D2 🟠 · Mandato efímero en la huella | Resuelto | desarrollador | resolver | La CLI transmite la ruta del mandato de raíz que retirará. Solo esa entrada se omite al calcular la huella de producto. Los contenidos distintos de un mandato rastreado llegan con huellas distintas y la evidencia sigue usando el árbol exacto. |

## Hallazgos nuevos

Ninguno independiente de H2, H3 y D3.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | La recuperación por ID y el avance tras reevaluar funcionan en los casos acreditados. Hay dos cierres indebidos reproducidos y una clasificación errónea de la salida del revisor. |
| Seguridad | 9/10 | Las llamadas a Git separan los argumentos y la recuperación del commit valida su identificador y ascendencia. El escaneo de secretos del delta pasó. |
| Conformidad | 5/10 | Se respetan las capas y el stack del plan. H2, H3 y D3 incumplen la exigencia de dictamen propio y vigente del diseño. |
| Calidad | 8/10 | Selector, firma y preflight comparten el criterio de revisión. La interpretación histórica pierde información cuando deja de reconocer la huella de cabecera. |
| Eficiencia | 8/10 | La recuperación técnica está acotada. Acreditar un ID requiere leer las métricas y consultar versiones anteriores del informe en Git. |
| Documentación | 7/10 | La guía explica el límite, la recarga y el mandato temporal. Las garantías sobre citas y ediciones administrativas exceden el comportamiento reproducido. |

## Análisis estático, evidencia y límites

Reutilicé la evidencia del árbol revisado. Pasaron las **144 pruebas dirigidas en 154,613 s**, el control aislado de exclusión del mandato, Ruff selectivo (`E9,F63,F7,F82`), el escaneo de patrones de secretos y las dos comprobaciones de `git diff --check` indicadas para el WIP y las rutas de B-ADV-0044. La base de calidad fue `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`. El comando `--calidad` terminó con código 0 y omitió formato y lint automáticos por ausencia de herramientas configuradas. El proyecto carece de verificador de tipos configurado. La auditoría de dependencias no aplica al delta.

Contrasté las rutas de producción con el árbol Git solicitado y calculé sobre él la huella de la cabecera. Reproduje H2 y D3 en un repositorio Git temporal eliminado al terminar. En H3 ejecuté el lector de declaraciones y seguí por lectura la rama que registra el dictamen y decide la reserva. No invoqué proveedores reales, no repetí las pruebas acreditadas ni ejecuté la suite completa. El dictamen se limita al delta de producción de B-ADV-0044 y excluye B-ADV-0045, B-ADV-0046 y B-ADV-0047.
