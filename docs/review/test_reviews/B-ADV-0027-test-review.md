# Test Review: B-ADV-0027

- **Bug**: B-ADV-0027 — `reintentos_acumulados` sube la dificultad en tareas multiturno con progreso y deshace las bajadas manuales en el Markdown
- **Archivos auditados**:
  - `tests/test_orquestar.py` (`DificultadTests.test_comprobar_promocion_no_promueve_en_multiturno_con_progreso_y_aprobado_hades`, `DificultadTests.test_comprobar_promocion_respeta_bajada_manual_de_dificultad_en_markdown`)
- **Veredicto**: **APROBADO** (media 9.0)

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Cobertura** | 9 / 10 | Cubre los dos casos principales del bug: tareas multiturno con progreso y aprobación de Hades sin promoción indebida, y respeto de la bajada manual de `dificultad` en el frontmatter del Markdown. |
| **Aserciones** | 8 / 10 | Las aserciones principales discriminan el comportamiento esperado, aunque en la prueba de bajada manual la comprobación sobre `rechazos()` se cumple por construcción al no haberse registrado rechazos previos. |
| **Rojo correcto** | 9 / 10 | Ambas pruebas fallan limpiamente por ausencia de la lógica esperada (`(3, 0) != (0, 0)` y `True is not false`), sin fallos de sintaxis, imports ni fixtures. |
| **Estabilidad** | 10 / 10 | Pruebas deterministas, aisladas en `self.root` temporal y sin dependencias de tiempo real, red ni orden de ejecución. |
| **Media** | **9.0 / 10** | **APROBADO** (sin hallazgos 🔴 ni 🟠) |

---

## Hallazgos

- **[H-01] 🟡 MEDIA (`destino: resolver`) — Aserción sobre `motor.rechazos(self.root, 'T1')` cumplida por construcción en `test_comprobar_promocion_respeta_bajada_manual_de_dificultad_en_markdown`** (`tests/test_orquestar.py:964-975`):
  Antes de la bajada manual de dificultad en el Markdown solo se registran 3 eventos `tipo: 'paso'` y ningún evento `tipo: 'agente'` con `veredicto: 'RECHAZADO'`. Por tanto, `motor.rechazos(self.root, 'T1')` ya vale `0` antes del cambio manual y la aserción `self.assertEqual(motor.rechazos(self.root, 'T1'), 0)` no discrimina si la bajada manual realmente reinicia los rechazos acumulados. Conviene registrar también al menos un rechazo de Hades antes de rebajar manualmente `dificultad: sencilla` en el Markdown.

- **[H-02] 🔵 BAJA (`destino: resolver`) — Orden de eventos `agente` y `paso` invertido respecto al flujo real del bucle en `test_comprobar_promocion_no_promueve_en_multiturno_con_progreso_y_aprobado_hades`** (`tests/test_orquestar.py:942-945`):
  En un turno real de `bucle()`, la invocación a Hades (`tipo: 'agente'`, `veredicto: 'APROBADO'`) se registra durante la ejecución del paso y el evento `tipo: 'paso'` se registra al finalizar el turno. En el test se registra primero `paso` y después `agente`. Invertir el orden (`agente` antes de `paso` con `progreso: True`) reflejará fielmente la secuencia real en `orquestar_metricas.jsonl` y garantizará que el evento `paso` con progreso al cierre del turno no deje el contador en `1`.
