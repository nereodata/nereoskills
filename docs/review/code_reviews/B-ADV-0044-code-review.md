**Veredicto:** RECHAZADO

Producto revisado: e57996a4abd91de45eb490878b78e07e6df5c5708f94b9055e2b973bb5a7daac

# B-ADV-0044 · Reevaluación D de código

Rama `hotfix/v1.1.3`. Árbol `5f9b5ac7f3f63b8beb0717dc32dc8ced1c681141`. Ronda anterior `91f914f09742192e33b51d33c60799bf50e3c67e`. Base de calidad `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`. **Media 7,00/10.**

El bucle ya acota el incidente de los dos commits de diagnóstico. H4–H7 quedan resueltos. Persisten dos vías de cierre con una aprobación antigua y una vía que registra una cita como dictamen. La corrección también puede bloquear para el humano un ID cuya reevaluación acaba de aprobarse.

## Hallazgos de la ronda anterior

| Hallazgo | Estado | Para | Destino | Evidencia y acción pendiente |
|---|---|---|---|---|
| H1 🔴 · Revisión perdida al relanzar | **persiste** | artemisa | resolver | `cierre_revisado` comprueba el producto de `HEAD`. Al relanzar, `motivo_revision` toma el commit que cambió la ficha a `completed` o el de una emisión posterior. Si el mismo `bug-fix` confirma primero el cierre con la aprobación de A y después una corrección B del mismo ID, termina con árbol limpio y código 1, la recuperación rechaza B. Al agotar los intentos, selección y preflight vuelven a A y aceptan el informe intacto. El caso verde confirma B y `completed` en un mismo commit. Conservar el objetivo pendiente del intento fallido al relanzar. El control positivo es un cambio posterior de **otro** ID, que debe conservar la aprobación de A. |
| H2 🔴 · Una nota renueva la aprobación | **persiste** | artemisa | resolver | Una nota ordinaria ya conserva la emisión histórica. Pero `declaracion` busca la línea de huella en todo el informe. En un informe histórico aprobado sin huella, basta añadir una copia del mandato pendiente en un bloque de código que contenga `Producto revisado: <huella de B>`. Comprobé que el lector devuelve la aprobación antigua emparejada con la huella citada. Si se confirma esa nota junto al producto B y al cierre del ID, la igualdad de `motivo_revision` acredita B. Leer la huella de la declaración del revisor y conservar la acreditación histórica al añadir ejemplos o mandatos citados. |
| H3 🟠 · Una cita se registra como dictamen actual | **persiste** | artemisa | resolver | El transporte ya aísla la respuesta y la cita en mitad de una frase se descarta. Probé `declaracion` con «No pude revisar. Transcribo el dictamen anterior.» seguido de un bloque Markdown cercado con `~~~markdown` que contenía la línea del veredicto anterior. Devolvió `('APROBADO', None)`. Con código 0, `agente` registra esa aprobación y omite la reserva. Reconocer la declaración propia fuera del material citado. Conservar el caso de un informe actual entregado para transcripción. |
| H4 🟠 · Reserva tras salida normal sin dictamen | **resuelto** | artemisa | resolver · completado | Cuando el principal devuelve 0 sin declaración reconocida, `agente` registra el consumo y continúa con la siguiente configuración elegible dentro de la misma invocación. El perfil estricto y la espera por cuota conservan sus vías. H3 identifica el error previo a esta decisión. |
| H5 🟠 · Reintentos técnicos cargados al desarrollador | **resuelto** | artemisa | resolver · completado | `bucle` incorpora `revision_pendiente` a las métricas antes de registrar la espera, la conmutación y el intento final. `reintentos_acumulados` excluye esas filas sin avance. La evidencia dirigida conserva los cuatro consumos y el acumulado ordinario a cero. |
| H6 🟠 · WIP rastreado e ignorado | **resuelto** | artemisa | resolver · completado | `indice_de_trabajo` importa las entradas del índice real en el temporal antes de aplicar el WIP. Así `firma` y `arbol` observan el archivo rastreado que coincide con una exclusión. El índice preparado del usuario conserva su contenido. |
| H7 🟡 · Dependencias de fichas antiguas | **resuelto** | artemisa | resolver · completado | `estado` y `cierre_tras_error` llaman a `faltan_dependencias`. Un bug antiguo sin el campo permite recuperar el paso cuando la última tarea pendiente declara sus dependencias y el grafo es válido. |

## Hallazgos nuevos de D

**D1 🟠 · Una reevaluación válida puede bloquear el ID para el humano.** Estado **abierto**. Para `artemisa`. Destino `resolver`. En `orquestar.py:1404`, la firma de `revisar-tarea` guarda el resultado de `motivo_informe`. Una aprobación de A caducada y la nueva aprobación vigente de B producen el mismo valor vacío. Con la ficha ya completada, un único perfil, `--reintentos 1` y retorno 0, el bucle registra falta de progreso y llama a `bloquear_sin_progreso` antes de volver al selector. Este escribe `status: blocked` y `pendiente_de: humano`. La comprobación positiva de N4 cubre `cierre_revisado`; esta ruta de éxito ordinario decide mediante `firma`. Observar la transición de revisión pendiente a vigente y comprobar que, en ese mismo límite, el ID sigue completado.

**D2 🟠 · El mandato temporal forma parte de la huella de producto.** Estado **abierto**. Para `artemisa`. Destino `resolver`. La CLI admite `--prompt-file mandato_temporal.txt` en la raíz y mantiene ese archivo hasta el `finally` de `main`. Si es nuevo y no está ignorado, `construir_prompt_agente` calcula la huella con él presente mediante `arbol` y `git add -A` sobre el índice temporal. Después de que Hades emita la aprobación, la CLI elimina el mandato. El producto confirmado tiene otra huella aunque el único cambio sea esa limpieza. El caso está en la entrada documentada con nombre libre; el nombre predeterminado sí está excluido. Excluir de la huella de revisión el mandato que la propia llamada retirará, preservando los mandatos rastreados y la identidad exacta de las evidencias.

**D3 🔴 · Un informe histórico restaurado en el WIP puede liberar un rechazo.** Estado **abierto**. Para `artemisa`. Destino `resolver`. En `revisiones.py:111`, cuando faltan tanto huella como emisión acreditada, `vigente = not confirmar` da verdadero para el selector y el preflight. Basta que la versión confirmada del informe rechace B y que en el WIP se restaure el antiguo informe aprobado de A sin huella. La búsqueda histórica se detiene al leer el rechazo de B, deja `emision` vacía y ambas consultas dan por revisado el ID. Acreditar la procedencia del informe recuperado frente al producto objetivo. Mantener un control positivo para el informe histórico cuya emisión sí cubre el cierre.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | El incidente original queda acotado. Persisten aprobaciones falsas y un bloqueo humano después de una revisión válida. |
| Seguridad | 9/10 | Las llamadas a Git usan argumentos estructurados. El escaneo dirigido de credenciales pasó. |
| Conformidad | 5/10 | Se conservan el stack y las capas. La barrera de cierre, el reconocimiento del avance y la distinción entre fallo técnico y dictamen tienen las excepciones descritas. |
| Calidad | 8/10 | El criterio de dependencias y la consulta de vigencia se comparten entre consumidores. La firma de avance aún interpreta el informe con un criterio distinto. |
| Eficiencia | 8/10 | La recuperación por paso e ID tiene límite. Reconstruir la emisión de cada informe exige consultar el historial y leer sus versiones. |
| Documentación | 7/10 | La guía describe el límite, la cuota, la recarga y el arranque manual. Las garantías sobre la vigencia al relanzar exceden el comportamiento observado. |

## Evidencias y alcance

Leí en el checkout el agente, la skill, el informe anterior y las rutas de producción afectadas. Contrasté el árbol de trabajo con el árbol Git indicado y calculé sobre este la huella que figura en la cabecera. Los casos de H2 y H3 se comprobaron directamente con el lector de declaraciones, sin escribir en el árbol. Los demás recorridos se determinaron por lectura del código y de sus consumidores. El diagnóstico de suite conserva su validador JSON y su canal de métricas diferenciado. Se toma C1 como aprobado, con N4 incorporado. B-ADV-0045 conserva su dictamen independiente.

Se reutilizaron las evidencias de este árbol. Las **119 pruebas dirigidas** pasaron en **179,763 s**. Pasaron Ruff selectivo (`E9,F63,F7,F82`), `git diff --check` y el escaneo de patrones de secretos contra la base del triaje. `--calidad` terminó con código 0 y omitió formato y lint automáticos por ausencia de herramientas configuradas. El proyecto carece de verificador de tipos configurado. La auditoría de dependencias no aplica a este delta. La suite completa corresponde al cierre de versión.
