# B-ADV-0011 — Revisión de código (reevaluación)

**Veredicto: APROBADO**

Modo orquestado, tras releer la skill instalada `review-code`. Misma base: `95b3d0bd2f8daace92f9688a366fe04dab06f59b`. Alcance: delta de producción de `skills/orquestar/orquestar.py`, skill distribuida, README, guía de orquestación, CHANGELOG, diseño, triaje y apunte documental de la versión. Reevaluados H-01/H-02 y las consecuencias de sus correcciones. Este informe sustituye el rechazo anterior.

Se mantienen las aprobaciones de especificación y pruebas, sin rehacer esas revisiones. No se han modificado producción, diseño, pruebas o estados, ni realizado commits o ejecutado suite completa.

## Análisis estático y evidencia

- `orquestar_evidencias.jsonl` confirma código 0 para `git diff --check`, compilación de producción/pruebas y calidad local desde la base indicada en el árbol `079dbc60e88ef8d02241908519f13e6c4051a315`. Se reutiliza la evidencia sin repetirla.
- La calidad local no ejecuta herramientas inexistentes: no hay linter/tipador configurados ni dependencias nuevas. Se mantiene la distinción entre omisión justificada y análisis efectivo.
- Se reutilizan las 14 pruebas dirigidas verdes del árbol `9b5427249edb47e7125e8f86e5865c0b6a8e31e6` y la aprobación renovada de `/review-test`. No se atribuye a los cuatro casos nuevos un RED distinto del documentado: el resumen disponible acredita tres fallos iniciales de la ampliación.
- Las regresiones de ausencia, cuota vigente, recarga y motor (9/8/11/70) constan verdes en `f5a6758e1a…`, anterior al último cambio de producción. Su renovación no llegó a ejecutarse: `adevv orquestar --verificar` falló al calcular el árbol con `git add -A .` (128), y el intento de usar almacenamiento temporal de objetos fue rechazado por la política de ejecución antes de arrancar. Véase H-03; no se declaran 112 pruebas verificadas sobre la última producción.
- Seguridad revisada sobre el delta: no se detectan secretos o credenciales incrustados, nuevos comandos interpolados o cambios de destinatarios y permisos. La ampliación usa configuraciones originales y no crea perfiles desde la salida del arnés.

## Puntuaciones

| Criterio | Nota | Motivo |
| --- | --- | --- |
| Corrección | 9/10 | La selección recupera los omitidos disponibles y compara las esperas restantes; la ampliación de perfiles es finita. |
| Seguridad | 9/10 | Continúa la validación CLI y no se añaden secretos, dependencias ni nuevas rutas de ejecución de comandos. |
| Conformidad | 9/10 | Los ajustes están documentados en el diseño; se preservan arquitectura, capas y alcance limitado a pasos. |
| Calidad | 9/10 | Se conservan modelos de consumo y se añade identidad explícita del perfil; el auxiliar mantiene compatibilidad por defecto. |
| Eficiencia | 9/10 | Los reintentos siguen acotados y los plazos monotónicos descuentan el tiempo transcurrido. |
| Documentación | 9/10 | Guía, skill, README y CHANGELOG describen el comportamiento; el diseño recoge las correcciones. La procedencia temporal de la evidencia se precisa en este informe. |

**Media: 9,0/10.** Sin hallazgos críticos ni altos pendientes. Queda una limitación media de renovación de evidencia.

## Reevaluación de hallazgos anteriores

### H-01 — Cuota omitida y recuperación durante reintentos — Resuelto

- **para:** desarrollador.
- **destino:** resolver; cerrado en código.
- `cuota_descartada(..., incluir_recuperadas=False)` conserva el contrato anterior de sus llamantes. Solo la recuperación operacional solicita incluir recuperadas.
- Al agotar la selección por error operacional, un perfil original omitido y ya disponible se añade a `configs_a_probar`. Al quedar incluido deja de ser omitido; la lista solo puede crecer hasta los perfiles originales y cada perfil conserva su presupuesto de intentos. No se reinician perfiles agotados indefinidamente.
- Las cuotas observadas durante el paso guardan plazos monotónicos y se convierten a segundos restantes al decidir. Se comparan con la cuota omitida pendiente, manteniendo la configuración asociada a la menor espera.
- Los dos casos anteriores —120 segundos frente a una recuperación más larga y omitido que recupera durante las esperas— ya no siguen las rutas de parada prematura señaladas. La evidencia dirigida entregada los ejercita, junto con la recuperación persistentemente fallida y acotada.

### H-02 — Modelo ausente en métricas sin consumo — Resuelto

- **para:** desarrollador.
- **destino:** resolver; cerrado.
- Las escrituras de intentos intermedios, conmutación y registro final incluyen `modelo`, obtenido de la configuración o `predeterminado`.
- Se conserva `modelos` de las métricas reales sin reconstruir consumo a partir del modelo configurado. Las ausencias mantienen su registro específico de consumo cero. La regresión dirigida entregada distingue dos modelos del mismo arnés sin consumo.

## Hallazgos nuevos

### H-03 — 🟡 MEDIA — Falta renovar parte de la evidencia del triaje tras el último cambio de producción

- **para:** desarrollador.
- **destino:** resolver.
- **Evidencia:** las cuatro regresiones de 9/8/11/70 pruebas están registradas antes de cambiar `cuota_descartada` y la recuperación del bucle. Los 14 casos nuevos y el estático sí tienen evidencia posterior. La ejecución intentada en esta revisión falló antes de lanzar la primera regresión; el segundo intento fue bloqueado por política.
- **Impacto:** la lectura confirma compatibilidad del argumento opcional por defecto, pero falta renovar la comprobación dirigida de agentes, ausencias, cuota vigente, recarga y CLI del motor con la última producción.
- **Corrección y cierre:** ejecutar únicamente las cuatro regresiones del triaje mediante `adevv orquestar --verificar` en un entorno que permita calcular la huella Git y registrar sus resultados. No repetir los 14 casos ni el estático si mantienen evidencia aplicable; no se solicita suite completa. Actualizar la atribución de los 112 resultados en el bug con la evidencia correspondiente.

## Resto del delta

Se mantienen limpieza de sesión tras fallo operacional, omisión de ejecutables ausentes, parada cooperativa antes de intentos y durante esperas, y comprobación de progreso commiteado antes de repetir. El diagnóstico continúa limitado a los últimos 2000 caracteres del último intento ejecutado. No se amplía la recuperación operacional de agente/gateway ni se alteran capas o dependencias del plan de plataforma.

## Instantánea revisada

SHA-256:

- `skills/orquestar/orquestar.py`: `1C591AA1CC6B54CFF66E6406AC3390749765FD2652AC5FDF63AF64277187537D`.
- `docs/design/B-ADV-0011-design.md`: `B5330252F9A9E9352285AE73D1E864C7211E01C56F22B24D622BA49540992B03`.
