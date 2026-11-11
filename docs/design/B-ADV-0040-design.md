# Diseño técnico: B-ADV-0040

`agente()` reconocerá exclusivamente el diagnóstico de Claude `Your organization has disabled Claude subscription access for Claude Code` cuando el proceso falle. La clasificación se hará antes del reintento de una sesión antigua y antes de interpretar cuotas. No es un dictamen ni una cuota: se registra `acceso_denegado`, modelo, diagnóstico y código real, sin `veredicto` ni espera inventada. Se continúa por la lista ya filtrada por cuotas; `aplicar_perfil()` ya elimina reservas para perfiles estrictos. No se cambian perfiles ni se reintenta una sesión bloqueada por suscripción.

Si no queda perfil operativo, el resultado es fallo técnico con instrucción de conservar la revisión pendiente y terminar sin completar ni abrir preguntas para elegir perfiles. El mandato del paso y la skill explicitan esta regla. Los errores genéricos de autenticación/red y los rechazos reales conservan su comportamiento. El caso mixto acceso/cuota conserva la espera real existente. El éxito sigue registrando el arnés y veredicto reales.

## Impacto

- [MODIFY] `skills/orquestar/orquestar.py`: clasificador puro, rama de recuperación en `agente()` y mandato del paso.
- [MODIFY] `skills/orquestar/SKILL.md`: operación ante acceso denegado.
- [NEW] `skills/orquestar/test_acceso_agente.py`: lanzadores simulados y repositorio temporal con copias estructurales de Q-ADV-0001/0002, respuestas, historial y ramas WIP.
- Consumidores de `agente()`: CLI `main()` (`--agente`); conserva entero de salida y añade recuperación para el diagnóstico acotado. Los tests de reservas por cuota/ausencia y perfil estricto deben conservar resultados.
- Consumidores de `construir_prompt_paso()`: bucle y pruebas de mandato; reciben aclaración operativa sin cambiar firma. La decisión del agente de desarrollo es no determinista: se verifica la instrucción entregada y la ausencia de mutaciones por el lanzador, sin fingir ejecución de un modelo en tests.
- Ninguna decisión documentada contradicha: `test_errores_operacionales_no_prueban_reservas` fija autenticación genérica; este diseño no la reclasifica.
- Sin cambio arquitectónico ni dependencias. Clasificación constante de una cadena de error sobre una salida ya capturada; no añade E/S al camino exitoso ni sondeos.

## Recuperación

No se migran preguntas de otros bugs en este paso. Las regresiones usan la incorporación durable y restauración existentes: conservan respuestas en cola si hay trabajo ajeno, incorporan tras conservar ese trabajo y restauran WIP sobre archivos independientes. Solo se simulan los lanzadores de revisión; Git, preguntas y respuestas son reales en el repositorio temporal. La evidencia de Hades y la revisión de versión deben explicar esta frontera.

## Impedimento detectado al reanudar

La prueba de recuperación usa archivos LF y Git real: `intervencion.git()` envía el parche como texto y Windows convierte LF a CRLF antes de `git apply`, que rechaza su contexto. No se simula ni se sortea esa ruta: se propone enviar entradas Git como bytes UTF-8 para preservar el parche exacto; las llamadas sin entrada conservan su comportamiento. Consumidor con entrada encontrado: `restaurar()`, usado por el bucle antes del paso y por la regresión de ambas preguntas. El alcance de C2 incluye ese transporte, sin modificar preguntas reales ni ampliar contratos de bloqueo. La prueba dirigida existente captura el fallo en Windows. Sin cambios de firma ni arquitectura.

## Precisión H1/H2 al retomar

Los fallos genéricos conservarán el diagnóstico en la métrica, sin conmutación ni veredicto. `restaurar()` comprobará el destino limpio antes de aplicar un WIP aún pendiente, también con pregunta ya incorporada. Devolverá False si debe esperar; el bucle no lanzará el paso ni notificará reanudación en ese caso. Sin WIP pendiente mantiene la continuación. El parche viaja en bytes tanto al capturarlo como al aplicarlo para conservar LF, CRLF y contenido binario.

Impacto mecánico adicional: `intervencion.git` es helper privado de bloqueo, preguntas, incorporación, enrutado y restauración, todos conservan salida texto por defecto; solo restauración pide salida bytes. `restaurar` lo consume el bucle antes del lanzamiento y las pruebas de intervenciones; todos requieren preservar cambios independientes. La prueba anterior de dos tareas guarda el cambio ajeno y el WIP retomado antes de preparar la siguiente. Se añade test H2 por fila con recepción pendiente e incorporada; el guardado pertenece al propietario simulado, nunca al motor. No hay decisiones arquitectónicas contradichas.

## RC-01 de QA

La restauración no debe heredar la tolerancia de `asegurar_destino` a escrituras propias preparadas: una pregunta incorporada ya concluyó esa transacción. Se antepone una barrera estricta con `git status --porcelain` antes de llamar al helper. Cualquier cambio de índice, worktree o archivo sin seguimiento impide restaurar; incluye índice AJENO y worktree vuelto a HEAD que se cancelan en diff HEAD. Se conserva la recuperación previa de incorporación sin modificar ese helper ni su contrato. El caso adicional del triaje vive en test_acceso_agente.py, con Git real y la instantánea incorporada, y debe fallar antes de la corrección. Sin nueva arquitectura ni dependencias.

## Reapertura: diagnóstico sin punto final

Se reconoce la frase específica completa hasta `Claude Code`, independientemente del punto o del sufijo explicativo. Solo en Claude y con código distinto de cero. No se amplía a autenticación/red genéricas ni al código 403 por sí solo. [MODIFY] clasificador y pruebas de acceso existentes; sin nuevas capas ni firmas.

Mapa de impacto: los dos consumidores en `agente()` (exclusión del reintento de sesión y clasificación previa a cuotas) necesitan reconocer esta variante. La búsqueda del helper no encuentra otros consumidores de producción. Los tests previos no se modifican ni invalidan; se añaden reserva con sesión previa, estricto con sesión previa y exclusión de otro proveedor. La primera descripción de este documento exigía un punto literal y se precisa aquí conforme al diagnóstico real, sin contradecir decisiones arquitectónicas. El clasificador conserva una sola búsqueda de subcadena sobre la salida capturada, sin nueva E/S; las pruebas dirigidas validan la secuencia de lanzamientos.
