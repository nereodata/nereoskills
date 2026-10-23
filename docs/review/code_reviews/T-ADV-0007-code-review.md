# Revisión de Código (`review-code`): T-ADV-0007

- **Tarea**: T-ADV-0007 — Detección y espera de cuota agotada en subagentes (--agente)
- **Archivos auditados**:
  - `skills/orquestar/orquestar.py`
  - `tests/test_orquestar.py`
- **Veredicto**: **APROBADO**

## Análisis Estático y Evidencias

- **`git diff --check`**: Limpio, sin errores de formato.
- **Pruebas unitarias (`tests/test_orquestar.py`)**: En verde incluyendo `test_subagent_out_of_credits_triggers_quota_wait_in_loop` y `test_quota_wait_and_quota_stop_notify`.

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Corrección** | 9.5 / 10 | Propaga la falta de cuota desde `agente()` hasta `bucle()` mediante `orquestar_metricas.jsonl` sin bloquear el subproceso del arnés padre y sin contabilizar `sin_progreso` cuando el paso termina con código `0` sin cambios en el árbol. |
| **Seguridad** | 9.5 / 10 | Sin ejecución adicional de subprocesos ni exposición de credenciales. |
| **Conformidad** | 9.5 / 10 | Cumple los tres criterios de aceptación (`CA-M-1`, `CA-M-2`, `CA-M-3`) de `T-ADV-0007`. |
| **Calidad** | 9.5 / 10 | Cambio mínimo y localizado en `CUOTA`, `agente` y `bucle`. |
| **Eficiencia** | 9.5 / 10 | Lectura acotada únicamente a las líneas nuevas de `orquestar_metricas.jsonl` generadas durante el paso. |
| **Documentación** | 9.5 / 10 | Mensajes claros por consola y en avisos de cuota. |
| **Media** | **9.50 / 10** | **APROBADO** (media > 8, sin hallazgos 🔴 ni 🟠) |

## Hallazgos

Sin hallazgos 🔴, 🟠, 🟡 ni 🔵.

Veredicto: APROBADO
