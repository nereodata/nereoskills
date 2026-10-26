# Revisión de código — B-ADV-0004

**Veredicto: APROBADO**

Fecha: 2026-10-25. Revisor: Hades. Skill aplicada: `/review-code` de Adevv 0.5.0.

## Alcance

Revisión estática del delta de producción en `skills/orquestar/orquestar.py`, contrastado con el triaje de `docs/plan/bugs/B-ADV-0004-codex-resume-sandbox-y-doble-conteo-tokens-cache.md` y con `docs/requirements/platform_plan.md`. Se ha leído el contexto de construcción y ejecución de comandos, agregación de uso y consumo de métricas. No se modifica código de producción ni se reevalúa la calidad de las pruebas.

El triaje omite expresamente definición, diseño y documentación de usuario para este arreglo interno; no se exige un diseño de tarea adicional.

## Análisis estático y evidencia

`orquestar_evidencias.jsonl` registra código de salida 0 sobre el árbol `21ba286e8a7280fbcedec2d949d04e273cc801ed` para:

- `python -m unittest skills/orquestar/test_codex_resume_usage.py skills/orquestar/test_agente_prompt.py` (25 tests OK según la evidencia aportada).
- `git diff --check`.
- `python -m py_compile skills/orquestar/orquestar.py skills/orquestar/test_codex_resume_usage.py`.

Se acepta esa verificación y no se repiten las comprobaciones. La inspección del delta concuerda con la declaración de ausencia de secretos y credenciales. No cambian dependencias; no procede una auditoría de dependencias. No se aporta un resultado adicional de linter o tipado. No se ha ejecutado una reanudación real contra el servicio de Codex; la revisión contrasta la construcción del comando con el contrato técnico del bug.

## Puntuaciones

| Criterio | Nota | Evaluación |
| --- | ---: | --- |
| Corrección | 9/10 | En `base_comando_agente`, la reanudación sustituye el flag rechazado por el par `-c`, `sandbox_mode="workspace-write"`, conservando sesión, JSON, política de aprobación y entrada por stdin. En `lanzar`, la entrada neta resta la caché acumulada, admite claves ausentes o nulas y limita el resultado a cero. Se conservan las métricas de caché, salida y razonamiento. |
| Seguridad | 9/10 | Mantiene `workspace-write` y `approval_policy="never"`. Los argumentos siguen separados en una lista para `Popen`, sin introducir shell, interpolación ejecutable ni credenciales. |
| Conformidad | 10/10 | Implementa exactamente las dos correcciones del triaje. Respeta la ubicación del motor y las reglas de capas del plan de plataforma, incluida DEC-P09, sin nuevas dependencias ni desviaciones arquitectónicas que requieran una DEC. |
| Calidad | 9/10 | Cambio localizado y legible, sin duplicación ni código muerto. La reasignación local de `entrada` ocurre después de su último uso como prompt y no altera el envío a stdin. |
| Eficiencia | 10/10 | Añade una resta y un límite de coste constante; no añade procesos, lecturas ni almacenamiento. |
| Documentación | 9/10 | Conserva contratos y firmas públicos. El docstring de `lanzar` sigue siendo válido y no cambia la interfaz de usuario; la omisión de documentación adicional coincide con el triaje. |

**Media: 9,33/10.** Supera 8 y no se identifican hallazgos críticos ni altos.

## Fundamento del veredicto

La agregación de eventos `turn.completed` precede a la normalización: para contadores válidos, restar los totales acumulados produce la entrada no cacheada total. El consumidor `metricas.py` tarifica `entrada` y `cache_leida` por separado y `consumo_cuotas` suma ambas categorías; la normalización evita contabilizar dos veces la caché en los registros nuevos. El delta no migra registros históricos, algo que el triaje no solicita.

Las ramas de Claude y agy devuelven antes de este cálculo y no cambian su contabilidad. La construcción de sesiones nuevas conserva su comando anterior. La corrección de reanudación mantiene el contrato que utiliza `agente`, incluido el añadido de modelo mediante `con_modelo`.

No se identifican hallazgos en el código de producción del delta.
