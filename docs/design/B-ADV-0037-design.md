# Diseño B-ADV-0037

## Contrato y componentes

Una única fuente en `adevv/revisiones.py` define identidad operativa de versión
(X,Y,Z con parche cero por omisión), validación del informe canónico
`docs/review/code_reviews/<ID>-code-review.md` y diagnóstico de pendientes.
Acepta el primer veredicto formal APROBADO (con o sin etiqueta Veredicto), o N/A con motivo
explícito de ausencia de código. Un archivo vacío, RECHAZADO o ilegible bloquea.
La existencia de un archivo con prefijo parecido no acredita al ID.
Cada completed requiere informe; cancelados no requieren aprobación.
Los componentes con parent_id usan el informe del maestro, sin exigir informes
independientes que el flujo no produce.

`release_tools.validar_publicacion` exige completitud y revisión antes de consultar
remotos, y también en el worktree integrado previo a etiquetar. El validador CLI
completitud comparte esta regla. No requiere Hades disponible para validar:
informa ID, motivo y reanudación con revisar-tarea. Ningún fallo publica o etiqueta.
El selector delega revisada y vkey en la fuente compartida; las métricas siguen
agrupando por mayor/menor como fija su contrato histórico.

## Mapa mecánico de impacto

Búsqueda: `rg -n 'vkey|revisada' skills/orquestar skills/telegram_gateway`.
Consumidores de vkey: estado (pertenencia y orden), errores_dependencias,
producto_activa, deuda, registrar_fallo_suite, bloquear_sin_progreso, estado_texto,
intervencion._revision y cierre_version.validar/cerrar. Todos quieren aislamiento
operativo por parche. Se preserva parche en rutas de revisión y en start-version;
para parche cero se conserva vX.Y, compatible con las ramas release existentes.
`metricas.clave_version_numerica/version/seleccionar` mantienen agrupación estadística;
no cambian sus consumidores ni tests.
Consumidores de revisada: selector estado; deja de aceptar cualquier archivo vacío.
Fixture RevisionProductoTests debe declarar APROBADO para representar una revisión
válida. SuiteRecoveryTests compara vkey con (X,Y,Z) y se adapta explícitamente.
No se retiran escenarios. B-ADV-0037 cambia el contrato operativo anterior de
agrupación de parches, autorizado por CA4; no contradice capas ni stack del plan.

## Verificación

Regresiones en tests/test_revision_release.py con repos temporales y sin red real:
rechazo del preflight y publicación sin cambios de referencias; informes vacíos,
rechazados, N/A sin motivo y prefijos parecidos; recuperación por informe aprobado;
selector con dos parches, dependencia hacia parche posterior y rutas de revisión.
Se ejecutan también los grupos afectados enumerados en el triaje.
La lectura es lineal sobre el backlog, igual que antes; informe individual O(1),
sin invocaciones de modelos ni esperas en el camino de selección.

## Adaptación a la especificación aprobada

[NEW] adevv/revisiones.py centraliza identidad, informe y pendientes. Lee las
rutas configuradas de maestros (y el valor por defecto docs/plan) y excluye hijos.
[MODIFY] check_release_completeness.py reutiliza ese veto junto a completitud.
[MODIFY] release_tools.py lo exige antes de Git y en el worktree integrado.
[MODIFY] cierre_version.py lo exige antes de publicar, acepta vX.Y.Z y hotfix;
conserva release/vX.Y para parche cero. [MODIFY] orquestar.py e intervencion.py
conservan el parche en selección, creación de versión y rutas de informes.
[MODIFY] README y CHANGELOG documentan diagnóstico y recuperación.

El diagnóstico de una revisión no válida incluye la última ejecución de Hades
para el ID si tuvo falta de cuota, leyendo las métricas ya existentes; no crea
estados de backlog ni equipara recuperar cuota a obtener aprobación. parte()
expone el mismo diagnóstico cuando el próximo paso es revisar-tarea.
La matriz ejecutable cubre ausencia/rechazo × tarea/bug × tres entradas, con
repos Git temporales y referencias locales/remotas observadas. Se provoca cuota
con agente() y transporte del arnés simulado; recuperación emite un informe y
revalida sin publicar. Sin lint/tipado configurado; compilación y diff-check.

No se contradice ninguna decisión arquitectónica del plan de plataforma.
Se sustituye la semántica operativa mayor/menor, autorizada por DEC-ESP-04;
la función de métricas conserva su contrato. Se comprueba coste lineal con los
mismos recorridos existentes, sin arneses ni consultas remotas por informe.


Impacto adicional encontrado mecánicamente: HallazgosHadesRoutingTests usa
v1.1.1 y esperaba el informe v1.1; conserva el parche. DeudaMenorTests
comprobaba identidad entre vkey y la clave estadística: ahora verifica su
separación explícita. Se amplía el triaje solo con esos grupos afectados.
