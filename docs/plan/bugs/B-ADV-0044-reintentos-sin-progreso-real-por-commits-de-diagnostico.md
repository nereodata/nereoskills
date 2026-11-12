---
id: B-ADV-0044
title: "Los commits que repiten un impedimento técnico reinician la detección de estancamiento"
type: bug
weight: 1
dificultad: dificil
version: "v1.1.3"
status: planned
depende_de: []
perfil: {artemisa: {harness: codex, model: gpt-6-astra, effort: high}, hades: {harness: codex, model: gpt-6-astra, effort: high}, atenea: {harness: codex, model: gpt-6-astra, effort: high}}
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Incidente de release/v1.2, B-ADV-0031: al menos 28 ejecuciones repitiendo fallo de acceso de Hades"
---

# B-ADV-0044 · Repetición indefinida de un impedimento técnico

## Incidente y alcance

El motor 1.1.2 repite bug-fix B-ADV-0031. Hades no puede acceder al disco (registered Core launch requires an installed app). Cada ejecución añade otra nota a la ficha y crea un commit docs(plan), sin dictamen ni arreglo. firma() incluye HEAD, estado Git y huella del árbol. El motor interpreta cada nota como progreso, reinicia sin_progreso y vuelve a lanzar. Ejemplos en release/v1.2: 664a50e, d686fe3, 9300ebc y be73a02. La revisión comenzó a avanzar solo cuando se aportó el material completo como adjuntos.

Analizar el origen histórico antes de llamarlo regresión y registrar el commit que introdujo o dejó expuesta esta conducta. Considerar las distintas vías de progreso y no limitar el diagnóstico a eliminar HEAD de una tupla. Las modificaciones de la ficha también alteran el árbol.

## Criterios de aceptación

- Reproducir con arneses simulados que repiten el mismo impedimento y crean commits o cambian solo la redacción de notas. La repetición debe ser acotada y recuperar o ceder de forma explícita sin consumir indefinidamente.
- Diferenciar avance acreditado (código o pruebas relevantes, especificación o dictamen vigente, resolución de una respuesta) de notas repetidas, timestamps y commits vacíos. Conservar la compatibilidad con tareas antiguas y WIP.
- Los fallos técnicos del revisor no son aprobaciones, ni se atribuyen automáticamente al humano. Respetar perfiles y reservas. Evitar trasladar el bucle infinito a otra rama de recuperación.
- No confundir progreso parcial con tarea completada. Conservar la barrera de cierre revisado de B-ADV-0039, el consumo real y los fallos de cuota.
- Cubrir entradas reales del bucle, alternancia de tareas, cambio de proveedor, reinicio manual y recarga cooperativa según el contrato que determine el análisis. Documentar explícitamente el límite de recuperación y qué estado persiste.
- Verificar mediante un caso de control que una tarea que avanza realmente no se bloquea por falso estancamiento. Revisar también pasos de análisis afectados.
- Hades debe analizar la especificación, las regresiones y la corrección. Usar el modelo potente fijado por el usuario, sin degradación silenciosa. Desde la primera llamada proporcionar instrucciones, criterios, delta exacto completo y evidencias en el mandato para permitir el dictamen sobre adjuntos si falla el acceso a disco. Conservar la independencia y registrar sus limitaciones.

## Entrega urgente

Construir el hotfix sobre v1.1.2, ejecutar las regresiones y la suite completa al cierre, publicar v1.1.3 e instalar. Integrar después la corrección en release/v1.2 conservando la versión 1.2.0 y su trabajo. El usuario autorizó la rama urgente, el modelo potente y la instalación. El bucle original de Adevv tiene solicitada una parada cooperativa.

## Hallazgo de Hades enrutado
- Destino: `especificador`
- Decisión: ejecutar especificar
- Evidencia: Hades rechazó /review-spec (8,25/10) y asignó dos hallazgos altos al especificador. H1: exigir dos salidas normales con commits limpios que solo reformulen el impedimento en la ficha y el resumen de versión, parada técnica tras el segundo y ninguna tercera invocación. H2: contrastar completed con aprobación canónica anterior al delta y revisión actual pendiente frente a aprobación vigente, con el mismo commit parcial y retorno de error. H3 (medio, resolver): vincular código WIP y prueba al comportamiento del bug. Ejecutar especificar. Triaje, escenarios e informe literal en wip/B-ADV-0044, commit 99dd5a1; base_calidad 4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5. Hades dictaminó sobre los adjuntos por fallo de acceso a disco.

## Triaje

- base_calidad: `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`.
- Origen histórico: `31d7acd` ya reiniciaba el contador ante otro HEAD. `ab08fc54` incluyó el contenido WIP para detectar trabajo sin commit. `c52ef29` permitió continuar tras un error del arnés con cambio en disco y árbol limpio. El incidente `664a50e` cambió tanto la ficha como el resumen de versión. La conducta estaba presente desde el primer bucle.
- A [EXEC] Especificar el avance y la parada técnica observable en la feature de orquestación. Revisión independiente de especificación.
- B [EXEC] Diseñar las señales por paso y la interacción con cuota, errores, alternancia y recarga.
- C1 [EXEC] Regresiones del bucle con Git real y arnés simulado, incluidas las vías de salida y el control de avance. Revisión independiente de las pruebas en rojo.
- C2 [EXEC] Corregir detección y recuperación en el motor. Conservar las evidencias exactas del verificador.
- D [EXEC] Revisión independiente de código sobre todo el delta.
- E [EXEC] Documentar el límite y la persistencia en la guía del orquestador.
- F [EXEC] Registrar validación de versión y cerrar mediante commit cuando las revisiones estén aprobadas.
- Verificación dirigida: `python -m unittest skills.orquestar.test_progreso skills.orquestar.test_fallos_arnes skills.orquestar.test_recarga skills.orquestar.test_perfil_fijado.BucleTests tests.test_orquestar.RecuperacionAnalisisTests tests.test_orquestar.DificultadTests tests.test_orquestar.OrquestarRegressionTests tests.test_revision_release skills.orquestar.test_acceso_agente skills.orquestar.test_agente_prompt`. La reevaluación incorpora los dos consumidores afectados por H1–H4 (preflight de release y salida de Hades). Cubre avance, cierre revisado, cuota, perfiles y recarga. La corrección de D2 incorpora test_agente_prompt para verificar la firma de llamada y la limpieza del archivo temporal de la CLI. Higiene mediante `git diff --check` y calidad del delta.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 /review-test RECHAZADO (7,50/10), para desarrollo. H1 exige observar los perfiles de Hades autorizados antes y después de la recarga. H2 exige comprobar la espera efectiva por cuota. H3 y H4 piden reformular las dos notas con fechas fijas y comprobar el informe del ID correcto. Artemisa ha corregido las cuatro observaciones en skills/orquestar/test_progreso.py. Verificación dirigida del árbol 4260a399190751a42391073489643364dcc282c8: 84 pruebas, 12 fallos de comportamiento esperados antes de C2, sin errores de preparación. Reevaluar C1 con Hades adjuntando el informe literal docs/review/test_reviews/B-ADV-0044-test-review.md, el delta desde 68247f62b598e7f1ec3fd6c5e63eaed4208fff89, los escenarios y la última evidencia. La especificación sigue aprobada. Tras el aprobado de pruebas, implementar C2 según docs/design/B-ADV-0044-design.md y completar las fases pendientes del triaje.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades rechazó el árbol 91f914f09742192e33b51d33c60799bf50e3c67e (6,83/10). H1-H2: conservar para selección y release la revisión pendiente y vincular el dictamen al producto. H3-H5: descartar citas, probar reservas permitidas tras salida normal sin dictamen y excluir los intentos técnicos internos de la promoción. H6: observar fuentes rastreadas ignoradas. H7: compartir el criterio de dependencias con el selector. Artemisa retoma el desarrollo. Informe literal en docs/review/code_reviews/B-ADV-0044-code-review.md.

En esta misma revisión se reprodujo H3: la primera línea del dictamen literal es RECHAZADO, pero el motor 1.1.2 registró APROBADO al encontrar la cita de H3 más adelante. Para reevaluar, usar el informe literal y el delta desde el árbol 91f914f09742192e33b51d33c60799bf50e3c67e. La última ejecución dirigida de ese árbol pasó las 84 pruebas en 70,832 s.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Reevaluación de pruebas del árbol b0dce90fafcf6d0d435126211f9dd7baf0ca5d40, RECHAZADO (8,00/10). N1 exige rechazar la huella del producto A frente al producto B y liberar B solo con la huella vigente. N2 exige recuperar los cinco campos de diagnóstico por el consumidor real. N3 exige observar el índice preparado distinto de HEAD y del WIP. Artemisa reanuda desarrollo y someterá estos cambios a Hades. Informe literal en docs/review/test_reviews/B-ADV-0044-test-review.md.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 APROBADO, 9,25/10. N1–N3 resueltos. N4 (baja, resolver, desarrollador): conservar la pareja de comprobaciones por bug-fix y recuperar la comprobación positiva de revisar-tarea con la misma aprobación vigente. Artemisa incorpora esta aserción y continúa hacia la reevaluación de código.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades D, árbol 5f9b5ac7f3f63b8beb0717dc32dc8ced1c681141, RECHAZADO (7,00/10). H4–H7 resueltos. Artemisa reanuda el desarrollo para conservar el objetivo del intento al relanzar (H1), reconocer solo la huella y el veredicto propios del revisor (H2–H3), detectar la reevaluación vigente como avance (D1), omitir el mandato efímero de su huella (D2) y acreditar los informes históricos restaurados en WIP (D3). Informe en docs/review/code_reviews/B-ADV-0044-code-review.md.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 RECHAZADO por Hades (8,50/10, árbol d541cedb12000f740bd29d3f9ff9bd405c579e06). N5: comprobar que dos contenidos diferentes del mismo mandato rastreado producen huellas diferentes en el mandato del proveedor y mantener el control temporal. N6: ejecutar el paso de un segundo ID identificable y verificar que conserva la aprobación del primero en selector y preflight. Reanudar desarrollo por estos dos controles y reevaluar C1 antes de corregir H1–H3 y D1–D3. Seis regresiones en rojo por aserción (8,820 s) y Ruff selectivo en verde. Tras el segundo rechazo consecutivo el motor ordenó guardar el trabajo y terminar este paso. Informe literal en docs/review/test_reviews/B-ADV-0044-test-review.md.

## Bloqueo sin progreso
- B-ADV-0044 bloqueada para el humano: 2 rechazos seguidos de Hades con el perfil fijado estricto, que impide subir de dificultad o escalar a otro modelo; fecha: 2026-11-11T20:04:22
- Cola de la última salida:

    (el arnés no produjo salida)

## Reanudación del trabajo técnico autorizado

El bloqueo por dos rechazos corresponde al límite del perfil estricto introducido al preparar este hotfix. No hay una decisión ni un recurso del humano pendiente. Se conserva GPT-6 Astra con esfuerzo alto para Artemisa, Hades y Atenea, la dificultad difícil y todos los dictámenes. Se retira el modo estricto añadido durante la preparación y se devuelve la ficha a planned para corregir N5 y N6, completar las regresiones y corregir H1-H3 y D1-D3. No se considera aprobado ningún hallazgo por esta reanudación.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades D rechazó el árbol c311964fe4ef788c496c2f459de194ebbab85075 (7,00/10). H1, H4-H7, D1 y D2 resueltos. Artemisa reanuda H2, H3 y D3 para conservar la huella cuando una nota la desplace o suprima, distinguir citas con continuación Markdown o bloque HTML de un dictamen propio y conservar la precedencia del rechazo ante la restauración WIP de una aprobación del mismo producto. Las 144 pruebas dirigidas pasaron. Véase el informe canónico de código.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 aprobado por Hades (9,25/10). Cinco regresiones rojas reproducen H2, H3 y D3 y el control de informe íntegro pasa. Artemisa continúa C2, comprueba el selector, el preflight y las reservas y somete el delta a revisión de código.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades D, árbol 45f708880b084d9ebddbf88a5a092b9a06c41c98, RECHAZADO 7,00/10. H2 resuelto. D3 exige mantener pendiente una aprobación revocada incluso con cambios de presentación o seguimiento. H3 exige respetar la apertura HTML de blockquote multilínea. D4 exige reconocer el rechazo propio inmediatamente después de un encabezado Markdown citado. Reanudar desarrollo con esas tres reproducciones y reevaluar C1/D. Las 149 pruebas del triaje pasaron en 170,668 s. Detalles en docs/review/code_reviews/B-ADV-0044-code-review.md.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 APROBADO 9,25/10, árbol ce8f66c2a349515fe8bd836a48a9133bbd2a261b. Cuatro rojos reproducen D3, H3 y D4 y tres controles pasan. Artemisa añade la comprobación de llamada efectiva N7 y corrige los tres defectos de producto antes de la revisión D.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 rechazado por N8 (9,00/10): distinguir una referencia a R1 de otra a R2, dos rechazos reales del mismo producto, manteniendo el caso del SHA de aprobación y un HEAD administrativo posterior. N7 resuelto. Reanudar desarrollo y reevaluar las pruebas antes de D.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: D RECHAZADO 6,83/10, árbol 8923fe8e39557265a1ca358caa8cc80d6fd785b3. D4 resuelto. Reanudar C2 con cuatro reproducciones de Hades: D3 conserva el cuerpo histórico con sangría al identificar restauraciones; H3 reconoce la apertura HTML multilínea de blockquote tras texto introductorio; D5 conserva la referencia al último rechazo de la emisión aprobada cuando una nota la desplaza; D6 distingue el producto A del B en la restauración histórica de aprobaciones escuetas. C1 aprobada 9,50/10 sin pendientes. Las 154 pruebas del triaje pasaron en 265,674 s. Ver informe canónico de código para entradas y resultados.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 aprobado por Hades (9,50/10) en el árbol 41e0939b3365d0f3cadf5a2117dda0ad64ba640a. Los cuatro rojos reproducen D3, H3, D5 y D6. El informe de pruebas atribuye a Artemisa la corrección de esos cuatro defectos en C2. Reanudar desarrollo y reevaluar D.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: D RECHAZADO 6,83/10 sobre 6d9aec0cabf4145855a3cd7b45148e9d4d310880, con 158 pruebas verdes. H3 y D5 resueltos. Artemisa debe corregir D3 (quitar el identificador de lenguaje de un bloque permite restaurar una aprobación revocada), D6 (una edición histórica sin huella atribuye al producto B la aprobación escueta de A) y D7 (una cita HTML a continuación del veredicto propio oculta el rechazo del principal). El informe canónico contiene los recorridos de código y los resultados exigidos para selector, preflight y reservas. C1 aprobada 9,50/10.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 APROBADO (9,50/10) sobre e453d91f77. Los tres fallos de aserción reproducen D3 (lenguaje del bloque), D6 (emisión histórica de A sin huella durante B) y D7 (rechazo propio seguido por una cita). Artemisa reanuda C2 para corregir los tres recorridos y solicitar la reevaluación D.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: D RECHAZADO (7,00/10) en cff52f5481280368df0943abe889928d6e0e88fe, 161 pruebas dirigidas verdes. D7 resuelto. Hades reprodujo D3 (retirar el cerco Markdown exterior permite cerrar con una aprobación revocada), D6 (se bloquea una aprobación histórica propia de B sin huella por la anterior de A) y D8 (una respuesta incorporada durante la espera deja un solo intento de los dos permitidos). Reanudar C2 con los tres recorridos reproducibles y sus controles en el informe canónico. C1 aprobada 9,50/10.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 RECHAZADO (8,50/10) en el árbol 566d0a3ea27e1ea6f94cbce4fb0d276fe4364aa1. Hades aceptó la cobertura de D3 y D8. N9 exige conservar los controles existentes y reproducir el rechazo de B tras la aprobación escueta de A, seguido de una aprobación propia de B sin huella. Deben avanzar el selector y el preflight. Reanudar C1, reevaluar con Hades y abordar D3, D6 y D8 en C2. Tres regresiones en rojo por aserción y Ruff selectivo en verde. El motor ordenó guardar el trabajo y terminar este paso tras el segundo rechazo consecutivo.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 aprobada 9,50/10 sobre 75c275c26dde5c829247867f03f2f3681640bba4. N9 resuelto. Hades verificó cuatro rojos de comportamiento y dos controles verdes. Artemisa retoma C2 para corregir D3 (cerco exterior), D6 (producto de la emisión histórica confirmada) y D8 (renovación por ID durante la espera) y solicitar revisión de código.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: D RECHAZADO por Hades (7,33/10) en el árbol 0c523fc036bc554e0ade546389e173c3819c0e2b. D3, D6 y D8 resueltos en los casos de C1. D9 crítico, para Artemisa en C2: tras rechazar B, confirmar solo la copia literal del informe histórico sin huella de A permite cerrar B. Conservar la procedencia de esa copia también tras el commit y el control positivo de una aprobación histórica propia de B. Reproducir en selector, preflight y cierre_revisado y someter la corrección a Hades. Las 165 pruebas del triaje pasaron en 209,582 s. Reproducción independiente e informe en docs/review/code_reviews/B-ADV-0044-code-review.md.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 aprobada por Hades con 9,75/10. D9 para Artemisa en C2. La regresión reproduce las tres decisiones de cierre indebidas tras confirmar el informe de A y la aprobación propia de B pasa como control. Corregir la procedencia histórica y reevaluar el código.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: D9 resuelto en los tres consumidores. Hades rechazó el árbol e40be2b764ee04736af04642d760d44a5c0b056d (7,33/10). D10 crítico: confirmar la copia escueta de A y añadir en otro commit una nota de archivo libera B. D11 alto: un veredicto de ejemplo en HTML pre/code se interpreta como propio y omite la reserva de Hades. Ambos para Artemisa en C2; añadir las reproducciones y conservar los controles positivos antes de reevaluar el código. Las 166 pruebas dirigidas pasaron. Informe canónico en docs/review/code_reviews/B-ADV-0044-code-review.md.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 aprobada por Hades (9,50/10) sobre 51f8328d7e41b1b45975db7554557807dd3fe4af. N10 medio, resolver en C2: guardar el ejemplo HTML pre/code en el informe canónico y comprobar que el preflight mantiene pendiente el ID. Corregir D10 (procedencia de una aprobación escueta copiada tras añadir una nota posterior) y D11 (ejemplo HTML interpretado como dictamen propio), conservar el control de aprobación legítima de B y solicitar revisión D. Las cuatro pruebas focalizadas produjeron cinco fallos de aserción y el control positivo pasó.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades D rechazó el árbol cba87a86f9fd1ded147ddf0a341e648f521b9710 (7,67/10). D10 y N10 resueltos. Reanudar C2: D11, una apertura pre/code sangrada dentro de details expone el dictamen del ejemplo; D12, ocultar code en línea interrumpe una cita Markdown y expone su aprobación. Conservar el rechazo propio posterior y la reserva si falta dictamen. Reproducciones e impacto en proveedor e informe canónico en docs/review/code_reviews/B-ADV-0044-code-review.md. Las 170 pruebas del triaje pasaron en 211,847 s.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 APROBADO por Hades (9,75/10). N10 resuelto. Las seis pruebas rojas del árbol 309d88d17a8364db18f1309b92cc72d9bb90cd09 reproducen D11 y D12 en la reserva, el rechazo propio y el preflight. Reanudar C2 para corregir los dos casos y reevaluar el código.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Reevaluación D rechazada (7,67/10), árbol 959e9a5d3aaa87b07058d2218288c40baf1527c7. D12 resuelto. D11 persiste: una aprobación en code sangrado dentro de un párrafo HTML se toma como propia incluso ante un rechazo posterior. D13 nuevo: una etiqueta pre literal en un bloque de código Markdown sangrado dentro de details oculta el rechazo posterior al cierre de details. Reanudar desarrollo en C2 con las dos reproducciones y controles del informe canónico docs/review/code_reviews/B-ADV-0044-code-review.md. C1 aprobado (9,75/10) y 176 pruebas del triaje verdes en 344,486 s.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Reevaluación D rechazada por Hades (7,67/10) en el árbol a26fcef1631e03e6e5f108b7f79f3b24c3a5e1dc. D11 y D13 resueltos en los cinco recorridos aprobados por C1. Reanudar C2 por D14 y D15, ambos altos para Artemisa. D14: el marcador de lista antes de <div> expone la aprobación citada en el código sangrado, incluso con rechazo propio posterior. D15: un <pre> literal en el atributo multilínea de un div oculta el rechazo propio posterior. Preservar las decisiones del proveedor y del preflight según las reproducciones del informe canónico docs/review/code_reviews/B-ADV-0044-code-review.md. Pasaron las 181 pruebas del triaje en 351,869 s.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 aprobado por Hades (9,75/10). Las cinco pruebas rojas del árbol 0f1f6df4aba12d31e3d82318f697891ff46a85c6 reproducen D14 y D15 en proveedor y preflight. Reanudar C2 para conservar el contexto de lista Markdown y de atributo HTML multilínea y presentar el arreglo a revisión D.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Reevaluación D rechazada por Hades (7,50/10) sobre el árbol 68283b0ddb726545ee42b47eddf300451dbef6bb. D14 y D15 resueltos; 186 pruebas del triaje verdes. Reanudar C2 con D16 (una continuación sin sangría de una cita dentro de una lista acredita la aprobación citada), D17 (la comparación x<y deja sin reconocer el rechazo propio) y D18 (un guion dentro del bloque HTML interrumpe el ejemplo de código y acredita su aprobación). Los tres son de prioridad alta, para Artemisa. Reproducciones y decisiones esperadas del proveedor y del preflight en docs/review/code_reviews/B-ADV-0044-code-review.md.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 aprobada (9,75/10) sobre f9bf920b045f95ceb484762bf77b511e5d2ff7de. Ocho fallos de aserción reproducen D16, D17 y D18 en proveedor y preflight. Artemisa reanuda C2 para conservar la continuación citada, reconocer el rechazo tras x<y y mantener literal el guion dentro de HTML. Reevaluar D.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Reevaluación D rechazada por Hades (7,67/10) sobre el árbol 1a134d9bcb834658906fcf5b7ec08d49efeb65c1. D16, D17 y D18 resueltos. D19 alto, para Artemisa en C2: en un div, el atributo @click de pre hace que el lector acredite la aprobación del ejemplo y permita cerrar pese al rechazo exterior. Recuperar el rechazo del principal en una sola llamada y mantener la ficha pendiente por informe rechazado. Conservar el control con title, D17 y D15. Las ocho regresiones y las 194 pruebas del triaje pasaron. Reproducción en proveedor y preflight e informe literal en docs/review/code_reviews/B-ADV-0044-code-review.md.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: D19 resuelto en el proveedor y el preflight. Hades rechazó el árbol e5146fc231ecc69c2fa3bb74f3443708624d2d11 (7,67/10). D20 alto, para Artemisa en C2: si la etiqueta de apertura de pre con @click se presenta entre acentos graves repartida en dos líneas, el lector pierde el rechazo propio posterior, invoca la reserva y registra su aprobación. El preflight indica informe sin veredicto formal. Conservar el rechazo en una sola llamada y el motivo informe rechazado, con el ejemplo en una línea como control. Reanudar desarrollo desde el informe canónico de código. Las 198 pruebas del triaje pasaron en 224,274 s y C1 fue aprobada con 9,75/10.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 aprobada por Hades (9,75/10) para D20. Los dos fallos muestran la aprobación indebida de la reserva y el motivo de preflight equivocado. Pasaron cuatro controles de una línea y de HTML efectivo. Artemisa corrige D20 en C2 y presenta el delta a revisión D.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades da por resuelto D20. Reevaluación D rechazada (7,00/10), árbol e0adec49b5a340d171503744fa1362fa09c4f37a, con 202 pruebas dirigidas verdes. Reanudar C2 para resolver D21 (un cierre literal de code en un segundo ejemplo expone una aprobación citada), D22 (el acento grave de un encabezado oculta el rechazo del párrafo siguiente) y D23 (lectura cuadrática del párrafo). Reproducciones, controles y destinos en docs/review/code_reviews/B-ADV-0044-code-review.md.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades aprueba C1 con 9,75/10. Cuatro fallos de aserción y cuatro controles verdes en el árbol 7449b14424d6198eabcc5aa09396c8389a96a5de. Artemisa retoma C2 para preservar el rechazo propio ante los dos ejemplos HTML de D21 y el encabezado de D22, y comparar con el lector anterior el coste de 300, 600 y 1200 líneas para D23. Reevaluar el código con Hades.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades rechazó la reevaluación D (7,50/10) del árbol cdcee1cb4fbd493365a05c9bd46aa630ffb27472. D21, D22 y D23 resueltos. Reanudar C2 por D24 y D25: una línea que empieza por 2. o una continuación sin sangría dentro de una viñeta exponen una aprobación de ejemplo y permiten cerrar pese al rechazo propio. D26: marcar un nombre de archivo como código antes del ejemplo pre oculta su cierre efectivo y el rechazo posterior, e invoca la reserva. Los tres son altos, para Artemisa, destino resolver. Reproducciones y controles en docs/review/code_reviews/B-ADV-0044-code-review.md. Pasaron las 210 pruebas del triaje en 233,099 s. La salida y el informe literal de Hades dicen RECHAZADO; el motor instalado 1.1.2 registró APROBADO en la métrica de esa invocación. Prevalece el informe canónico.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: C1 aprobada por Hades (9,75/10). D24, D25 y D26 reproducidos en proveedor y preflight, con tres controles verdes. Artemisa reanuda C2 para corregir la delimitación del párrafo y el tratamiento de pre antes de reevaluar el código.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Reevaluación D rechazada por Hades (7,50/10) sobre el árbol 4a9b1d2fb5d9ece9edeb5aeee0e61cedb5c4b92d. D24–D26 resueltos. Reanudar desarrollo en C2 por tres hallazgos altos de análisis estático: D27 pierde el límite entre dos elementos numerados tras una continuación sin sangría y oculta el rechazo; D28 interpreta la cadena <pre> de un script como HTML efectivo y permite cerrar con una aprobación citada; D29 une un encabezado Setext subrayado con un guion y espacio con el rechazo del párrafo siguiente y habilita la reserva. Reproducciones y controles en docs/review/code_reviews/B-ADV-0044-code-review.md. Las 216 pruebas del triaje pasaron en 240,004 s. Los tres casos nuevos quedan pendientes de reproducción y corrección.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades aprobó C1 con 9,75/10. D27 se reproduce con cero y dos espacios, D28 acredita una aprobación citada y D29 oculta el rechazo. Ocho fallos de aserción, tres controles verdes. Artemisa reanuda C2 para corregir la lectura de listas, texto de script y subrayados Setext y someter el producto a Hades.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades rechazó la reevaluación D del árbol 870a23e384ede126aca575b4441b0b45d377c7f8 (7,67/10). D27–D29 resueltos en proveedor y preflight. D30 alto, para Artemisa en C2: un script multilínea con JSON en la continuación de una cita Markdown puede exponer su aprobación y permitir cerrar pese al rechazo propio. Reproducir la entrada y su control en una línea del informe canónico docs/review/code_reviews/B-ADV-0044-code-review.md, conservar la cita al ocultar el script y reevaluar. D30 procede de análisis estático. Pasaron las siete pruebas focalizadas y las 223 del triaje en 249,717 s.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades aprueba C1 de D30 (9,75/10). El script multilínea acredita la aprobación citada y deja cerrar la ficha rechazada. El control de una línea conserva el rechazo en ambos consumidores. Artemisa reanuda C2 para preservar el párrafo citado y presentar la corrección a revisión D.
