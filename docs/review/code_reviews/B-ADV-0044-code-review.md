**Veredicto:** RECHAZADO · **6,83/10**

# B-ADV-0044 · Revisión independiente de código

Árbol `91f914f09742192e33b51d33c60799bf50e3c67e`. Base `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`.

Las 84 pruebas dirigidas pasan. Dos hallazgos críticos impiden aprobar el cierre revisado. Un arranque posterior puede aceptar una aprobación que el motor ya consideró caducada. Además, una nota añadida al informe antiguo puede acreditar código que Hades nunca revisó.

## Hallazgos

**H1 🔴 CRÍTICO · El relanzamiento pierde la revisión pendiente.** **para: desarrollador**. En `skills/orquestar/orquestar.py`, `cierre_revisado` deniega el cierre si la ficha queda `completed` y el producto cambió después del informe. Si se agota la recuperación y se relanza, `estado → revisada → motivo_revision` solo lee el veredicto formal. El ID queda fuera de `sin_revisar` y el motor puede pasar a `revisar-version`. La comprobación de release en `adevv/revisiones.py::pendientes_cierre` también acepta ese informe. Conservar la revisión pendiente del cambio de ese ID y hacer que selección y cierre consulten la misma acreditación. El caso discriminante es relanzar sobre el disco que dejó el error, con el informe antiguo intacto, y obtener `revisar-tarea` antes de permitir el cierre.

**H2 🔴 CRÍTICO · Una edición administrativa del informe renueva una aprobación antigua.** **para: desarrollador**. En `cierre_revisado`, `git log -1 -- <informe>` identifica la última edición del archivo. Si el commit que modifica el producto también añade al informe «pendiente de revisar el cambio», conservando el veredicto anterior, `revisada` sigue dando verdadero y `revisado == head` acepta el cierre inmediatamente. Una edición posterior del informe también puede satisfacer el diff vacío de producto. Vincular el dictamen formal al contenido que cubre. Contrastar dos casos con el mismo cambio de producto: una nota que conserva la aprobación anterior y un dictamen nuevo que acredita ese cambio.

**H3 🟠 ALTA · Una cita en la salida de Hades puede ocultar un fallo técnico.** **para: desarrollador**. `agente` busca el último patrón de veredicto en cualquier posición de la salida cuando el proceso devuelve 0. Con el texto «El informe anterior decía “Veredicto: APROBADO”. No pude abrir el repositorio», registra una aprobación en las métricas. `revision_sin_dictamen` acepta esa métrica y el intento sale de la recuperación técnica. Reconocer una declaración formal del revisor actual, incluida la entregada para transcripción cuando falla la escritura. La cita del informe anterior debe dejar la revisión pendiente.

**H4 🟠 ALTA · Una salida normal sin dictamen deja sin probar una reserva autorizada.** **para: desarrollador**. Con un principal y una reserva elegibles, si el principal devuelve 0 y «No puedo leer el archivo», `agente` registra la fila y llega a `return codigo` sin visitar la reserva. El siguiente paso puede repetir el principal hasta que `bucle` anuncie la parada técnica. Aplicar la cadena autorizada al fallo sin dictamen dentro de la misma invocación, conservando el consumo y las restricciones del perfil estricto. Una reserva disponible debe poder emitir el dictamen después de ese retorno 0.

**H5 🟠 ALTA · Los reintentos internos pueden cargar el fallo de Hades al desarrollador.** **para: desarrollador**. Si el arnés exterior propaga con código 1 la falta de dictamen, `bucle` ya conoce `revision_pendiente` cuando registra el intento antes de esperar. Omite esa marca tanto en esa fila como en la que precede a una conmutación de arnés. `reintentos_acumulados` cuenta esas filas como pasos ordinarios sin progreso. Tras varios reintentos internos, el siguiente arranque conserva ese consumo para la promoción o el bloqueo por perfil estricto. Registrar el motivo técnico en cada fila y excluir esos intentos del agotamiento ordinario, conservando el consumo real y el límite de recuperación del arnés.

**H6 🟠 ALTA · La firma pierde cambios WIP en archivos rastreados que coinciden con `.gitignore`.** **para: desarrollador**. `indice_de_trabajo` parte de un índice vacío y ejecuta `git add -A .`. Un archivo fuente ya rastreado, por ejemplo uno incorporado con `git add -f`, queda fuera del índice temporal si coincide con una regla de exclusión. Al modificar solo ese archivo, ambas observaciones de `firma` pueden ser idénticas. El motor puede agotar el presupuesto mientras el bug sí avanza. Hacer que la observación de producto incluya los archivos rastreados y el WIP nuevo, preservando el índice del usuario y el contrato de identidad de las evidencias.

**H7 🟡 MEDIA · La recuperación de dependencias exige más que el selector para las fichas antiguas.** **Destino: resolver**. `estado` comprueba la ausencia de `depende_de` en las tareas abiertas con versión. `cierre_tras_error('calcular-dependencias')` exige el campo en todos los maestros abiertos con versión, incluidos los bugs. Si el paso confirma las dependencias de la última tarea pendiente y queda un bug antiguo sin ese campo, aun con `errores_dependencias(items)` vacío, la recuperación puede repetir un paso que el selector ya daría por satisfecho. Compartir el criterio de selección y cierre para ese paso.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 5/10 | El incidente de los dos commits de diagnóstico queda acotado. H1 y H2 permiten cerrar sin una revisión del cambio. |
| Seguridad | 9/10 | El delta usa argumentos estructurados para Git. El escaneo de secretos aportado terminó en verde. |
| Conformidad | 5/10 | Se conservan las capas y el stack del plan de plataforma. Los hallazgos afectan a garantías explícitas de cierre, recuperación y reconocimiento del WIP. |
| Calidad | 7/10 | La correlación por invocación es clara. Selección, recuperación y release aplican criterios distintos al mismo estado en disco. |
| Eficiencia | 8/10 | La recuperación técnica tiene un límite por paso e ID. Las observaciones con rutas materializan el índice de todo el árbol antes de filtrar. |
| Documentación | 7/10 | La guía explica el límite, la recarga y el arranque manual. Sus garantías sobre vigencia y agotamiento de reservas exceden lo que ejecuta el motor. |

## Análisis estático y límites

Se reutilizaron las evidencias del árbol indicado. Pasaron las 84 pruebas dirigidas, `git diff --check`, el escaneo de patrones de secretos y Ruff con `E9,F63,F7,F82`. `--calidad` informó que omitió sus etapas de formato y lint por falta de herramientas. Ruff se ejecutó por separado con la selección indicada. El proyecto carece de comprobador de tipos configurado. El delta no cambia dependencias ni manifiestos.

Los hallazgos se dedujeron por lectura del delta, las funciones completas, el diseño y el plan de plataforma adjuntos. No se repitieron verificaciones. B-ADV-0045 queda fuera de este dictamen.

PowerShell y Node no pudieron iniciar el entorno por `registered Core launch requires an installed app`. También falló la escritura del archivo. Queda pendiente transcribir este informe íntegro en `docs/review/code_reviews/B-ADV-0044-code-review.md`.
