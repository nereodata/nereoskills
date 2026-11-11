**Veredicto:** RECHAZADO
Producto revisado: adc922098f8a94e4cd9da9c2f79ab61bf21dbe7793b38d977f5d37635c70fed5
Rechazo reevaluado: 8449873b6057b2fb94505903739a7233128abcc2

# B-ADV-0044 · Reevaluación independiente de código D

**Calificación: 6,83/10.** Las cuatro reproducciones de C1 pasan en el árbol `6d9aec0cabf4145855a3cd7b45148e9d4d310880`. D5 queda resuelto. Persisten dos defectos de acreditación en D3 y D6. La corrección de H3 resuelve la cita tras texto introductorio, pero introduce D7, que puede ocultar un rechazo propio de Hades.

## Estado de los hallazgos anteriores

| Hallazgo | Estado | Fundamento |
|---|---|---|
| D3 · Restauración de una aprobación revocada | **Persiste.** Resuelto el caso de sangría. | El comparador conserva el párrafo sangrado, pero incorpora el identificador de lenguaje de un bloque de código a las palabras del informe. Retirar ese identificador permite cerrar con la misma aprobación revocada. |
| H3 · Aprobación citada tras texto introductorio | **Resuelto.** | El lector reconoce la apertura de `blockquote` después del texto y mantiene la cita entre líneas. La regresión verde comprueba las llamadas al principal y a la reserva y atribuye el dictamen a esta última. |
| D5 · Referencia desplazada por una nota | **Resuelto.** | La reconstrucción recupera la referencia de la reevaluación confirmada. La regresión comprueba tanto la vigencia después de la nota como la revocación tras un segundo rechazo. |
| D6 · Confusión entre productos A y B | **Persiste.** Resuelto el caso con ambas huellas explícitas e intactas. | Si una edición histórica eliminó la huella de A, la comparación puede atribuir esa aprobación al producto B presente en el commit de la edición. |
| H1, H2, H4, H5, H6, H7, D1, D2 y D4 | **Siguen resueltos en los casos revisados.** | El verde dirigido conserva el objetivo por ID, la recuperación de la huella en la emisión actual, las reservas, el consumo, el WIP rastreado, las dependencias históricas, el avance por reevaluación, el mandato efímero y el rechazo propio tras un encabezado citado. |

## Hallazgos que persisten

**D3 🔴 CRÍTICO · Un cambio de marcado permite cerrar con una aprobación revocada.** Para `desarrollador` (Artemisa). Destino `resolver` en C2.

En `adevv/revisiones.py:164`, `palabras_informe` tokeniza la línea de apertura de un bloque Markdown. Considérese una aprobación de A con el párrafo `Comprobación del doble.` y un bloque abierto con `~~~python` que contiene `assert doble(3) == 6`. Tras confirmar un rechazo del mismo producto, basta restaurar la aprobación en el WIP cambiando `~~~python` por `~~~`. Se conservan el dictamen, la huella, el párrafo y el código del ejemplo. La secuencia histórica contiene la palabra `python` y la restaurada carece de ella. Por tanto, la comparación de `adevv/revisiones.py:199` descarta la restauración y la huella coincidente permite el cierre en la línea 245.

La corrección debe conservar las palabras del contenido sangrado y tratar el identificador de lenguaje como marcado. Para cerrar D3, esa restauración debe mantener el ID en `revisar-tarea` y en los pendientes de release. La reevaluación que acredita el último rechazo debe seguir permitiendo el cierre.

**D6 🟠 ALTA · Una edición histórica puede atribuir a B la aprobación escueta de A.** Para `desarrollador` (Artemisa). Destino `resolver` en C2.

La secuencia afecta también a una revisión nueva que **sí declara la huella correcta de B**. Para el mismo ID, se confirma una aprobación escueta de A con huella. En el commit que introduce B se suprime la línea de huella del informe anterior y queda únicamente el veredicto. Después se confirma un rechazo de B y, finalmente, una aprobación nueva de B con su huella y una explicación propia distinta.

Al retroceder más allá del rechazo, `adevv/revisiones.py:194` encuentra la edición sin huella y usa el producto de ese commit, que ya es B. El informe editado aporta cero palabras de cuerpo. En la línea 199, `all(...)` sobre esa secuencia vacía clasifica la aprobación nueva como restaurada. El selector y el preflight mantienen pendiente el ID. El diseño exige recuperar el producto de la emisión original, que en este historial es A.

Para cerrar D6, la comparación histórica debe atribuir esa edición a la emisión de A. Deben conservarse tanto la aceptación de la revisión propia de B como el bloqueo de una copia revocada del mismo producto.

## Hallazgo nuevo

**D7 🟠 ALTA · Una cita en la línea del veredicto oculta un rechazo propio.** Para `desarrollador` (Artemisa). Destino `resolver` en C2.

Una respuesta válida de una línea permite ver el defecto por lectura:

```text
**Veredicto:** RECHAZADO. El informe anterior decía <blockquote>APROBADO</blockquote>.
```

En `adevv/revisiones.py:61`, `contiene_cita` encuentra la etiqueta tras el rechazo y devuelve `True` para toda la línea, incluso cuando la cita se cierra en ella. En la línea 93, `lineas_del_informe` descarta también el prefijo que contenía la declaración propia. Con retorno 0, `agente` clasifica la respuesta como revisión sin dictamen y puede invocar una reserva después del rechazo del principal.

La corrección debe conservar la declaración que precede a la apertura y excluir el contenido citado. Para cerrar D7, esa entrada debe registrar el rechazo del principal con una sola llamada. La entrada técnica de H3, cuyo único veredicto está dentro de la cita, debe seguir activando la reserva.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | D3 permite un cierre indebido, D6 bloquea una aprobación vigente y D7 pierde un rechazo propio. |
| Seguridad | 9/10 | El delta usa argumentos separados para Git y el escaneo de secretos pasó. |
| Conformidad | 5/10 | Se conservan la biblioteca estándar, las capas y las carpetas maestras configurables. D3 y D6 incumplen las reglas del diseño para cambios de marcado y atribución histórica. |
| Calidad | 7/10 | Los consumidores comparten la decisión de cierre. El lector HTML descarta una línea completa cuando solo parte de ella es una cita. |
| Eficiencia | 8/10 | La reconstrucción recorre el historial de la ruta canónica y puede consultar el árbol de producto por cada candidato sin huella. |
| Documentación | 7/10 | La guía describe correctamente la referencia al último rechazo y su desplazamiento. La garantía de conservar la acreditación original excede el comportamiento del caso D6. |

## Evidencia y límites

Comprobé directamente en Git la rama `hotfix/v1.1.3`, el rechazo canónico `8449873b6057b2fb94505903739a7233128abcc2` y el delta desde el árbol anterior `8923fe8e39557265a1ca358caa8cc80d6fd785b3`. El blob revisado de `adevv/revisiones.py` es `10c3de8d63bd94eba572bf49e69fd3046299f1a2`. Los tres recorridos descritos en los hallazgos se deducen de las condiciones y retornos del código. No se ejecutaron como reproducciones adicionales.

Reutilicé la evidencia del triaje. Las cuatro regresiones fallaron inicialmente por aserción en `41e0939b33`. En el árbol revisado pasaron **158 pruebas dirigidas en 411,355 s**, incluidas esas cuatro. Ruff selectivo, ambas comprobaciones `git diff --check` y el escaneo de secretos terminaron con código 0. `--calidad` terminó con código 0 y comunicó que omitió formato y lint por ausencia de herramientas. Ruff se ejecutó por separado. El proyecto carece de comprobador de tipos configurado y el delta conserva las dependencias. **C1 mantiene su aprobación de 9,50/10.**
