**Veredicto:** APROBADO

# B-ADV-0040 · Regresión de RC-01 · 2026-11-11

Hades mantiene APROBADO, 9/10 en cobertura, aserciones, rojo y estabilidad; sin hallazgos nuevos. Dictamen independiente transcrito de --agente sobre adjuntos exactos por fallo de disco, sin ejecutar pruebas.

El nuevo test reproduce índice AJENO y worktree=HEAD en una instantánea incorporada con WIP pendiente. Exige conservación de HEAD, índice, diff local, estado, stashes y bytes sin restaurar. El rojo aportado (11 tests, un fallo) discrimina restauración indebida sin error de fixture. El propietario guarda después ambos planos explícitamente antes de reintentar. El parámetro opcional conserva las dos filas previas. RT-01/02 siguen resueltos; esta aprobación no resuelve RC-01 de producción.

---

## Antecedentes

**Veredicto:** APROBADO

# B-ADV-0040 · Reevaluación limitada de fixtures · 2026-11-11

Hades mantiene APROBADO, media 9/10 (cobertura, aserciones, rojo correcto y estabilidad: 9 cada una), RT-01/02 resueltos y sin hallazgos nuevos. Dictamen independiente sobre adjuntos exactos mediante --agente; sin contraste con disco ni ejecución de pruebas por el revisor. Se transcribe por el fallo de acceso del arnés.

El parser real `perfil_fijado_de(...)[1]` conserva la comprobación efectiva del perfil estricto. Popen simula únicamente Codex y delega Git a POPEN_REAL. Ninguna expectativa funcional se rebaja. La valoración previa del rojo queda matizada: había dos defectos latentes de fixture que solo se alcanzaron al superar los fallos iniciales; están corregidos y cubiertos por el verde de diez tests. Las consecuencias del dictamen y la preservación de A0 siguen aprobadas.

---

## Antecedentes

**Veredicto:** APROBADO

# B-ADV-0040 · Reevaluación de pruebas · 2026-11-11

Hades vía `adevv orquestar --agente hades --prompt-file orquestar_prompt.txt`. Dictamen independiente transcrito sobre adjuntos exactos; no pudo acceder al disco ni guardar informe. No ejecutó pruebas ni contrastó los adjuntos contra disco.

Cobertura 9, aserciones 9, rojo correcto 9, estabilidad 9; media 9/10. Diez tests en rojo, trece fallos contando subTests y sin errores; compilación y diff-check aportados en verde. Sin linter/tipador configurados.

- RT-01 resuelto: lanzar real transmite el rechazo observado, del que se derivan destinatario y contexto al enrutador real. Las instantáneas consumen la salida real procesada de Codex y conservan historial al añadir APROBADO manteniendo planned. Es la frontera determinista scriptada de un paso/agente, no ejecución de un modelo.
- RT-02 resuelto: conservación de HEAD, índice en bytes, estado, diff binario y stash antes del commit del propietario. Se mantiene W0 y restauración idempotente.
- Test adicional del bucle: restaurar=False debe impedir ejecución y aviso de reanudación. El revisor lo considera cobertura complementaria de propagación de espera.
- Sin hallazgos nuevos. APROBADO para pruebas previas a producción; no acredita implementación.

---

## Antecedente

**Veredicto:** RECHAZADO

Revisión independiente de Hades vía --agente, 2026-11-11. Transcripción del dictamen sobre adjuntos exactos; acceso a disco falló (registered Core launch requires an installed app), sin pruebas ejecutadas por el revisor.

Cobertura 7, aserciones 7, rojo 9, estabilidad 9; media 8/10.

- RT-01 · ALTA · para: desarrollador · destino: resolver. El enrutado reconstruye destino y contexto como literales independientes; la aprobación en métricas no demuestra consumo. Conectar consecuencias con la salida observable real del agente simulado, conservando el hallazgo y acreditando la revisión pendiente sin cerrar la tarea.
- RT-02 · ALTA · para: desarrollador · destino: resolver. Capturar HEAD, índice exacto, diff local y evidencia de no apartar A0. Los bytes del archivo y un índice vacío no impiden que se haya confirmado automáticamente. Comprobarlo antes del commit del propietario.

No pide cambios de especificación ni suite completa. Rojo funcional válido; no identifica defectos de fixture.
