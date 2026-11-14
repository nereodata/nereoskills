**Veredicto:** APROBADO
Producto revisado: 5e8a70446f3e2d164fcef7fdc9e72a59776ec138de9f94955ed55e645492fc10

# Code Review · T-ADV-0038

## Resumen de verificación

- **Calidad determinista (`adevv orquestar --calidad --base 9b7b255`)**: comprobada en verde sin `--aplicar`, reutilizando las evidencias vigentes sobre el árbol `a5ec5dba02` sin relanzar pruebas ya acreditadas.
- **CA-M-1 (Gateway de Telegram e idempotencia)**:
  - `skills/telegram_gateway/gateway.py` expone `/desbloquear <Q-ID> <respuesta>` (y alias `/unblock`) en `AYUDA`, en el recordatorio de comandos de `construir_prompt()` y en `responder()`, delegando en `motor.responder_pregunta(...)`.
  - Se reutiliza íntegramente el contrato serializado de `skills/orquestar/intervencion.py` (`adevv-respuesta.lock` y `adevv-intervencion.lock`): control de remitentes autorizados, rechazo de referencias inexistentes o de otro proyecto, detección de ambigüedad, encolado seguro con bucle vivo sin mutar Git, deduplicación cruzada con `/responder` y rechazo de entregas repetidas tras el cierre sin duplicar commits ni relanzamientos.
- **CA-M-2 (Recuperación del planificador y diagnóstico sin mutación)**:
  - Tras incorporar la decisión humana, la tarea vuelve a `status: planned`, respeta `orquestar.parar` sin arrancar en segundo plano, aguarda dependencias abiertas (`depende_de`) o esperas locales vigentes (`decision_item.bloqueada_condicion`), restaura su `wip/<ID>` al retomarse y activa `motor.en_fondo` cuando el bucle estaba detenido por bloqueo humano o espera local (`"Bloqueo de tarea;"` o `"Espera en "`).
  - Ante ausencia de pregunta humana pendiente (tanto por `<T-ID|B-ID>` como sin referencia), `_motivos_item_sin_pregunta()` y `_diagnostico_proyecto_sin_pregunta()` explican esperas de cuota (`leer_espera`, `marcas_cuota` y `decision_item`) e intervenciones técnicas (`especificador`, `intervencion_tecnica`, `decision_item`, revisión pendiente y `pausa_tecnica` en `contexto_ejecucion`) de forma estrictamente consultiva, conservando intactos el árbol Git y los registros de estado.
- **Pruebas y documentación (`PROJECT.md`)**: `tests/test_desbloquear_telegram.py` ejercita de extremo a extremo `CA-M-1` y `CA-M-2` sobre repositorios Git reales con transporte y procesos en segundo plano aislados (cero tráfico real a Telegram), alineado con `skills/telegram_gateway/SKILL.md`, `README.md` y `CHANGELOG.md`.

Sin hallazgos abiertos.
