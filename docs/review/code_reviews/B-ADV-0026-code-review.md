**Veredicto:** APROBADO

# Revisión de código: B-ADV-0026 · tercera ronda

- **Revisor:** Hades · **Fecha:** 2026-11-07 · **Skill:** `/review-code` (tercera ronda).
- **Base:** `cd1b3bdd452f4454bf5a28c620e3c38a52f918a1`.
- **Alcance:** delta de producción y documentación de `B-ADV-0026` (`skills/orquestar/intervencion.py`, `skills/orquestar/orquestar.py`, `skills/telegram_gateway/gateway.py`, `skills/orquestar/SKILL.md`, `skills/telegram_gateway/SKILL.md`, `README.md`, `CHANGELOG.md`) y reevaluación de los hallazgos pendientes de la segunda ronda (`RC-03` parcial y `RC-04`) frente a `docs/design/B-ADV-0026-design.md`.
- **Aislamiento:** no se reauditan las pruebas (`docs/review/test_reviews/B-ADV-0026-test-review.md` ya APROBADO 9.00/10 en quinta ronda). No se relanzan las pruebas ya acreditadas en verde sobre el árbol actual ni se modifican archivos de producción.

Media **9.00/10**. Los cuatro hallazgos históricos (`RC-01`..`RC-04`) quedan resueltos y no se detectan hallazgos nuevos.

## Análisis estático y evidencias

Evidencias en verde reutilizadas de `orquestar_evidencias.jsonl` sobre el árbol actual (`1935d9c7482dfd70b6a4e0f4caab058eba852a5a`):

- `git diff --check`: código 0 (sin errores de espacios ni marcadores de conflicto).
- `adevv orquestar --calidad --base cd1b3bdd452f4454bf5a28c620e3c38a52f918a1`: código 0 (**formato omitido y lint omitido por ausencia de herramientas**; omisión justificada, no se presenta como herramienta ejecutada en verde).
- `python -m unittest skills.orquestar.test_intervencion_humana`: **13 tests OK** (incluye la prueba 13 `test_bloqueo_incompleto_con_trabajo_ajeno_no_ejecuta_tarea`).
- Verificación completa del triaje (`python -m unittest skills.orquestar.test_intervencion_humana tests.test_orquestar.BloqueoSinProgresoTests tests.test_orquestar.RecuperacionAnalisisTests tests.test_orquestar.AvisosTelegramTests tests.test_telegram_gateway skills.telegram_gateway.test_gateway_control skills.telegram_gateway.test_cierre_version tests.test_instructions_cleanliness tests.test_package_and_instructions`): **79 tests OK** (código 0).
- Sin tipador ni escáner de seguridad configurados en el proyecto, sin dependencias nuevas ni cambios en el manejo de credenciales.

## Puntuaciones

| Criterio | Nota | Justificación |
|---|---:|---|
| Corrección | 9 | Reconciliación por fases completa (`bloqueo_aplicado`, `aviso_intentado` y `diagnostico_aviso == 'envío iniciado'`), bloqueo global de persistencia en `estado()` si una pregunta pendiente no pudo persistir su bloqueo en Git por trabajo ajeno, selección unívoca por tarea entre preguntas pendientes y mantenimiento del bloqueo cuando quedan otras preguntas abiertas. |
| Seguridad | 9 | Autorización por `TELEGRAM_ALLOWED_USER_IDS`, aislamiento por proyecto, cierre de `stdin` (`DEVNULL`), argumentos pasados a Git sin shell y protección del árbol rastreado durante la ejecución del bucle o ante cambios locales ajenos. |
| Conformidad | 9 | Totalmente alineado con el triaje de `B-ADV-0026`, con `docs/design/B-ADV-0026-design.md` (incluida la sección `Ajustes de implementacion (2026-11-07)`) y con la arquitectura del proyecto (stdlib, reemplazo atómico con `os.fsync` + `os.replace`, bloqueo de fichero en `.git`). |
| Calidad | 9 | Código conciso y legible en `skills/orquestar/intervencion.py`, responsabilidades bien delimitadas y sin código muerto ni duplicación. |
| Eficiencia | 9 | Operaciones locales $O(1)$ sobre JSON pequeño, sin llamadas HTTP en consultas y sin invocar arneses adicionales para encolar o incorporar respuestas. |
| Documentación | 9 | Docstrings claros en las funciones de API y actualización coherente de `skills/orquestar/SKILL.md`, `skills/telegram_gateway/SKILL.md`, `README.md` y `CHANGELOG.md`, incluyendo el bloqueo global de persistencia y la reconciliación de envíos interrumpidos. |
| **Media** | **9.00** | Superior a 8 y sin hallazgos 🔴 ni 🟠. |

## Reevaluación de hallazgos anteriores

| Hallazgo | Severidad original | Estado | Verificación |
|---|---|---|---|
| **RC-01** · Selección por tarea y múltiples preguntas pendientes | 🟠 ALTA | **Resuelto** (ronda 2) | `responder()` filtra por preguntas pendientes de la tarea, rechaza ambigüedad con varias candidatas y `incorporar()` conserva `status: blocked` mientras queden otras preguntas pendientes para la misma tarea. |
| **RC-02** · Incorporación sobre rama distinta o con cambios ajenos | 🟠 ALTA | **Resuelto** (ronda 2) | `asegurar_destino()` valida rama `release/` o `hotfix/`, exige árbol limpio (salvo escrituras preparadas propias exactas) antes de cambiar de rama y conserva la respuesta en cola con diagnóstico si hay cambios ajenos. |
| **RC-03** · Persistencia/reconciliación del bloqueo interrumpido e impedimento de ejecución | 🟠 ALTA | **Resuelto** (ronda 3) | En `skills/orquestar/orquestar.py:1211-1215`, `estado()` comprueba `incompletas = [q for q in listar_preguntas(root, True) if not q.get('bloqueo_aplicado')]` antes de evaluar tareas elegibles y devuelve `('PARAR', 'Bloqueo global: intervención humana pendiente de persistir con seguridad; ...')`. En `bucle()`, `incorporar_respuestas(root)` intenta reconciliar primero; si persiste trabajo ajeno, `estado()` detiene el bucle sin ejecutar la tarea todavía `planned` ni tocar ni descartar los cambios ajenos. |
| **RC-04** · Reconciliación automática del diagnóstico `envío iniciado` tras corte | 🟡 MEDIA | **Resuelto** (ronda 3) | En `skills/orquestar/intervencion.py:280-282`, la condición inicial de `incorporar()` incluye `or q.get('diagnostico_aviso') == 'envío iniciado'`, invocando `completar_solicitud()` para transformar el estado en `envío interrumpido; consultar pregunta, sin reenvío automático` sin reenviar el aviso. |

## Hallazgos nuevos

Sin hallazgos nuevos.
