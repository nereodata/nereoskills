**Veredicto:** RECHAZADO · **8,00/10**

# B-ADV-0044 · Reevaluación independiente de pruebas

Árbol `b0dce90fafcf6d0d435126211f9dd7baf0ca5d40` · Rama `hotfix/v1.1.3` · Base de calidad `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5` · Perfil estricto.

Las regresiones reproducen los fallos de selección, recuperación y reconocimiento del WIP observados en D. Quedan dos carencias de cobertura que impiden aprobar esta ampliación. Una aprobación con una huella caducada podría superar las pruebas. También podría perderse el diagnóstico de suite antes de llegar al consumidor sin que fallara la prueba que declara comprobar su entrega.

## Hallazgos anteriores de C1

| Hallazgo | Estado | Evidencia |
|---|---|---|
| H1 🟠 · Perfiles autorizados de Hades | **resuelto** | Los casos estrictos siguen exigiendo el modelo fijado. La alternancia exige la secuencia `claude/primario`, `codex/autorizado` tanto antes como después de la recarga y comprueba de nuevo los perfiles tras el arranque manual. |
| H2 🟠 · Espera por cuota | **resuelto** | Se conserva la aserción sobre la llamada efectiva a `esperar`, la demora de la reserva y el consumo de ambos intentos. |
| H3 🟡 · Reformulación del impedimento | **resuelto** | Los dos commits mantienen fechas fijas y redacciones distintas en la ficha y en el resumen de versión. |
| H4 🟡 · Informe del ID correcto | **resuelto** | La ruta del informe que se exige ausente sigue construyéndose con el ID del caso, incluida la fila de `task-dev`. |

## Regresiones solicitadas en D

| Hallazgo de D | Evaluación de la prueba |
|---|---|
| H1 · Revisión pendiente al relanzar | **Cubierto.** Tras el retorno erróneo, se consulta el selector sobre el disco que dejó el bucle. Se exige `revisar-tarea` para el ID exacto y que ese ID aparezca entre los pendientes de release. El rojo seleccionó `revisar-version`. |
| H2 · Vigencia de una aprobación editada | **Cobertura parcial.** El rojo muestra que añadir una nota al informe antiguo permitió cerrar. El caso positivo introduce una huella vigente. Falta discriminar una huella formal que pertenece al producto anterior. Véase N1. |
| H3 · Cita confundida con dictamen | **Cubierto.** Se exige que la cita del principal deje su fila sin veredicto y que el `RECHAZADO` formal de la reserva prevalezca sobre una cita posterior de `APROBADO`. El rojo se detuvo antes de esas aserciones al faltar el lanzamiento de la reserva. |
| H4 · Reserva tras una salida normal sin dictamen | **Cubierto.** La prueba exige ambos arneses en la misma invocación. La alternancia aporta un control independiente con una salida de código 0 sin cita ni dictamen. En el rojo faltó la primera reserva, antes de la recarga. |
| H5 · Reintentos técnicos atribuidos al desarrollador | **Cubierto.** Se exigen cuatro lanzamientos concretos, cuatro consumos de 11, la marca `revision_pendiente` en todas las filas y el acumulado ordinario `(0, 0)`. El rojo alcanzó la aserción de la marca después de comprobar perfiles y consumo. |
| H6 · WIP rastreado que coincide con `.gitignore` | **Cubierto para la detección del WIP.** El archivo se confirma antes de añadir la exclusión. Su modificación posterior debe alterar tanto `firma` como `arbol`. En el rojo, `firma` permaneció idéntica. La comprobación del índice tiene la limitación de N3. |
| H7 · Dependencias de una ficha antigua | **Cubierto.** La tarea y el bug empiezan sin `depende_de`. Se completa únicamente la tarea y se exige que coincidan selector y recuperación. En el rojo, el selector abandonó el paso y `cierre_tras_error` lo mantuvo pendiente. |

## Hallazgos nuevos

**N1 🟠 ALTA · Una huella caducada puede satisfacer la cobertura de H2.** **Para:** `desarrollador` (Artemisa). En `test_nota_no_renueva_aprobacion_pero_dictamen_del_producto_si`, el informe que debe rechazarse carece de `Producto revisado`. El único informe que lleva ese campo contiene el valor devuelto por `motor.huella_producto` para el producto vigente. Una implementación que acepte cualquier valor presente en esa línea superaría ambos casos. El rojo aportado acredita el defecto de la nota añadida al informe antiguo, pero no discrimina esa implementación.

**Corrección requerida.** Obtener la huella del producto A, cambiar el mismo archivo para producir B y conservar en el informe del ID la aprobación con la huella de A. Una edición administrativa de ese informe debe dejar el ID pendiente tanto para el cierre como para release. Sobre el mismo producto B, por la misma vía de cierre, sustituir la acreditación antigua por la de B y exigir que el ID quede liberado. Las dos huellas pueden obtenerse mediante la API existente.

**N2 🟠 ALTA · La prueba de diagnóstico estructurado no observa la entrega al consumidor.** **Para:** `desarrollador` (Artemisa). `test_diagnostico_estructurado_de_suite_se_entrega_al_consumidor` introduce un JSON con cinco campos y comprueba el código de salida, la ausencia de reserva y el resultado de `revision_sin_dictamen`. Ninguna aserción recupera el diagnóstico emitido. Si el agente reconociera el modo `diagnostico-suite`, marcara la invocación como atendida y descartara el JSON, las tres comprobaciones podrían seguir pasando. El rojo aportado demuestra el error de clasificación en las métricas.

**Corrección requerida.** Hacer pasar la salida del agente simulado por el punto de entrada que consume el diagnóstico, o capturar la salida que ese consumidor recibe y procesarla con su lector real. Comprobar que se recuperan la causa, la decisión, el destino, el responsable y la intervención del ejemplo. Conservar las aserciones actuales sobre reserva y revisión pendiente. La prueba debe fallar si el agente devuelve 0 y pierde el contenido.

**N3 🟡 MEDIA · La preservación del índice se comprueba con el índice igual a `HEAD`.** **Destino:** `resolver`. **Responsable:** `desarrollador` (Artemisa). En `test_wip_rastreado_aunque_ignorado`, la instantánea de `ls-files --stage` se toma inmediatamente después del commit. Una restauración indebida del índice a `HEAD` dejaría esa misma instantánea y podría borrar cambios preparados por el usuario en un repositorio real. Preparar una versión del archivo en el índice, dejar otra en el directorio de trabajo y conservar la comparación del índice antes y después de `firma` y `arbol`.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 7/10 | Las regresiones recorren los siete hallazgos de D. Quedan sin discriminar la huella caducada y la pérdida del diagnóstico en la entrega. |
| Aserciones | 7/10 | Se observan decisiones del selector, perfiles, esperas, métricas y estado Git. Los controles de N1 y N2 admiten los falsos positivos descritos. |
| Rojo correcto | 9/10 | Las dos ejecuciones contra `e797552` suman ocho fallos de aserción, sin errores de importación, sintaxis ni preparación. Las aserciones posteriores al primer fallo de cada caso se evaluaron por lectura. |
| Estabilidad | 9/10 | Las pruebas usan repositorios temporales, identidad Git local y configuración aislada. Los proveedores y las esperas están simulados. |

## Evidencia, alcance y destino

Se contrastaron los escenarios, el delta desde la ronda aprobada, el informe de D y los dos rojos adjuntos. Para `b0dce90fafcf6d0d435126211f9dd7baf0ca5d40` se aceptaron las tres verificaciones acreditadas en verde: `git diff --check`, el escaneo de patrones de secretos y Ruff con `E9,F63,F7,F82`. No se repitieron. El proyecto declara Python mínimo 3.11 y carece de comprobador de tipos configurado. La ejecución dirigida de 84 pruebas corresponde a una ronda anterior. La suite completa queda para el cierre de versión.

PowerShell falló con `registered Core launch requires an installed app` y el proceso de Node terminó antes de devolver los archivos. El dictamen se emitió sobre el mandato de Hades, la skill `/review-test` y los artefactos adjuntos. Se evaluó la suficiencia de las pruebas. La corrección del código de producción corresponde a `/review-code`.

**Destino del dictamen:** devolver a `desarrollador` (Artemisa) para completar N1 y N2 y resolver N3. **Ruta de transcripción literal:** `docs/review/test_reviews/B-ADV-0044-test-review.md`. El informe se entrega íntegro en esta respuesta. No se escribió ni modificó ningún archivo.
