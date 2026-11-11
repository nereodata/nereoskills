**Veredicto:** RECHAZADO
Producto revisado: e50708ae4f3aa13fb7bb180a592ccc043c1c126bed2f9a837fa4486f2994b0ac
Rechazo reevaluado: 6a4dd527fcd249ac06dca44a702bb7779aa8a8e5

# B-ADV-0044 · Reevaluación independiente de código D

**Media 6,83/10.** Rama `hotfix/v1.1.3`. Revisé el delta desde `45f708880b084d9ebddbf88a5a092b9a06c41c98` hasta el árbol de evidencia `8923fe8e39557265a1ca358caa8cc80d6fd785b3` y comprobé la huella de producto de la cabecera. **D4 está resuelto. D3 y H3 persisten en dos entradas concretas.** La nueva reconstrucción del historial también invalida dos aprobaciones legítimas. Los cuatro hallazgos abiertos corresponden al **desarrollador (Artemisa)**, con destino **`resolver` en C2**.

## Hallazgos anteriores

**D3 🔴 · Persiste. La sangría permite cerrar con una aprobación revocada.** En un repositorio Git temporal confirmé la aprobación de A y después su rechazo con la misma huella. Restaurar la aprobación exacta en el WIP dejó el ID pendiente. Al insertar una línea vacía y cuatro espacios delante del único párrafo, `Primera evaluación de A.`, `pendientes_cierre` pasó a devolver `[]`. La cabecera, las palabras, el producto y el historial eran los mismos. En `adevv/revisiones.py:104` la línea sangrada se excluye de las declaraciones y en `adevv/revisiones.py:163` también desaparece de la comparación histórica. La solución debe conservar ese texto al identificar una copia revocada y seguir exigiendo una declaración propia para emitir un veredicto. Las variantes de C1 de línea vacía y nota añadida ya pasan.

**H3 🟠 · Persiste. Una cita HTML abierta después de texto se atribuye a Hades.** Pasé esta respuesta técnica al lector del árbol revisado:

```text
No pude revisar. El informe anterior dice: <blockquote
 cite="archivo">
**Veredicto:** APROBADO
</blockquote>
Sigue pendiente.
```

`declaracion` devolvió `('APROBADO', None)`. En `adevv/revisiones.py:63`, el lector solo inicia el análisis HTML si el primer carácter de la línea tras la sangría es `<`. Con retorno 0, `agente` registra esa aprobación y omite la reserva autorizada. Debe reconocer la apertura tras el texto introductorio y mantener el estado de la cita hasta su cierre. La apertura multilínea al principio de línea que reprodujo C1 ya funciona.

**D4 · Resuelto.** Ante `> # Acta` seguido inmediatamente del rechazo formal, el lector devolvió `('RECHAZADO', None)`. La regresión dirigida acredita que las métricas atribuyen el rechazo al principal y que se realizó una sola llamada efectiva.

## Hallazgos nuevos de producto

**D5 🟠 · Una nota posterior invalida una reevaluación vigente.** Confirmé una reevaluación de A con su huella, el SHA correcto del último rechazo y el mismo cuerpo de la aprobación original. El preflight devolvió `[]`. Añadí únicamente `Nota de seguimiento.` entre la huella y la referencia al rechazo. El mismo ID pasó a figurar como «aprobación restaurada anterior al rechazo». En `adevv/revisiones.py:182` se recuperan del informe histórico el veredicto y la huella, pero se pierde la referencia al rechazo que ya había acreditado esa emisión. La corrección debe conservar la acreditación de la reevaluación confirmada a través de esa edición y mantener la precedencia de cualquier rechazo posterior.

**D6 🟠 · Una aprobación escueta de A impide cerrar una revisión nueva de B.** Confirmé una aprobación de A que contenía solo el veredicto y la huella, y después un rechazo de A. Cambié el producto a B y confirmé un informe nuevo con la huella de B y una explicación propia de la corrección. El preflight marcó el ID como «aprobación restaurada anterior al rechazo». En `adevv/revisiones.py:184`, la comparación admite cualquier aprobación histórica con el mismo veredicto. Al eliminar la huella, la aprobación escueta aporta solo las palabras «Veredicto» y «APROBADO», presentes en el informe nuevo. Para resolverlo, la decisión de restauración debe tener en cuenta el producto acreditado y evitar que el vocabulario obligatorio de la cabecera baste para identificar una copia.

## Alcance del seguimiento

H1, H2, H4–H7, D1 y D2 **siguen resueltos en sus casos revisados**. Se conservan el objetivo del intento al relanzar, la recuperación de la huella histórica, las reservas y su consumo, el WIP rastreado, el criterio común de dependencias, el avance por reevaluación y la exclusión del mandato efímero. D5 afecta específicamente a la referencia al rechazo añadida en esta ronda.

Los escenarios de repetición de notas, presupuesto de análisis y aislamiento entre IDs conservan el límite por paso, la transferencia en la recarga y la tanda nueva del arranque manual. H3 afecta a la selección de la reserva. D3, D5 y D6 afectan a la barrera de aprobación vigente que comparten selección, recuperación y preflight. **C1 continúa aprobada, 9,50/10, sin hallazgos de pruebas pendientes.** Los cuatro rojos históricos de C1 reprodujeron defectos de producto. Sus entradas exactas pasan en la verificación actual.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | Se reproducen un cierre indebido, una aprobación citada y dos bloqueos de aprobaciones vigentes. |
| Seguridad | 9/10 | Git recibe argumentos separados y el escaneo de secretos del delta pasó. |
| Conformidad | 5/10 | El cambio conserva las capas y la biblioteca estándar. Las decisiones de cierre y atribución incumplen el contrato en los casos descritos. |
| Calidad | 7/10 | Los consumidores comparten el criterio de cierre. El filtro de declaraciones elimina texto necesario para identificar una restauración. |
| Eficiencia | 8/10 | La lectura del historial ejecuta un `git show` por revisión recorrida y puede llegar al principio de la historia del informe. |
| Documentación | 7/10 | La guía explica el presupuesto y la referencia de reevaluación. Su garantía sobre cambios de espaciado excede el comportamiento observado. |

## Análisis estático y evidencia

Reutilicé el verde de **154 pruebas dirigidas en 265,674 s**, Ruff selectivo, el escaneo de secretos y las dos comprobaciones de diferencias Git. `adevv orquestar --calidad` terminó con código 0 y omitió formato y lint automáticos por ausencia de herramientas. Ruff sí se ejecutó por separado. El proyecto carece de tipado configurado y este delta conserva las dependencias.

Las comprobaciones adicionales se limitaron al lector de dictámenes y al preflight de cierre en tres repositorios temporales eliminados al terminar. Observé directamente los retornos del lector y del preflight. El efecto de H3 sobre la reserva se determinó siguiendo la rama de `agente` que consume el veredicto.
