**Veredicto:** APROBADO

# Revisión de Pruebas — T-ADV-0012

## Puntuaciones

| Criterio | Puntuación | Notas |
| :--- | :---: | :--- |
| **Cobertura** | 9/10 | Cubre todos los escenarios del `.feature` (`@CA-M-1`, `@CA-M-2`, `@CA-M-3`), además de autorización en mensajes libres y actualización de `/ayuda`. |
| **Aserciones** | 9/10 | Comprueban estado persistido, argumentos de invocación al modelo, aislamiento entre usuarios al reiniciar sesión y texto de respuesta. |
| **Rojo correcto** | 10/10 | Los 6 tests nuevos fallan limpiamente por ausencia de la funcionalidad (`invocar`, `guardar_sesion`, `construir_prompt` y texto en `AYUDA`). |
| **Estabilidad** | 10/10 | Totalmente deterministas: usan `TemporaryDirectory` aislado y mocks para las llamadas al modelo. |
| **Media** | **9.5/10** | |

## Hallazgos

- 🔵 **BAJA** (`destino: descartar`): En `test_conversation_reuses_existing_session`, el mock devuelve el mismo ID de sesión (`sess-existente`) en lugar de uno distinto para ejercitar explícitamente la cláusula *"Y actualiza el ID de sesión si cambia"* del escenario BDD (aunque el guardado del ID devuelto ya queda cubierto en los otros dos tests de conversación).
- 🔵 **BAJA** (`destino: resolver`): `test_prompt_includes_safety_notice_when_loop_is_running` invoca directamente `gateway.construir_prompt(...)`; comprobar también que `responder()` pasa dicho prompt a `gateway.invocar` cerraría el vínculo extremo a extremo del escenario `@CA-M-3`.
