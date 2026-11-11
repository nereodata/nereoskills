---
id: B-ADV-0044
title: "Los commits que repiten un impedimento técnico reinician la detección de estancamiento"
type: bug
weight: 0
dificultad: dificil
version: "v1.1.3"
status: planned
depende_de: []
perfil: {artemisa: {harness: codex, model: gpt-6-astra, effort: high}, hades: {harness: codex, model: gpt-6-astra, effort: high}, atenea: {harness: codex, model: gpt-6-astra, effort: high}, estricto: true}
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
- Verificación dirigida: `python -m unittest skills.orquestar.test_progreso skills.orquestar.test_fallos_arnes skills.orquestar.test_recarga skills.orquestar.test_perfil_fijado.BucleTests tests.test_orquestar.RecuperacionAnalisisTests tests.test_orquestar.DificultadTests tests.test_orquestar.OrquestarRegressionTests tests.test_revision_release skills.orquestar.test_acceso_agente`. La reevaluación incorpora los dos consumidores afectados por H1–H4 (preflight de release y salida de Hades). Cubre avance, cierre revisado, cuota, perfiles y recarga. Higiene mediante `git diff --check` y calidad del delta.

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
