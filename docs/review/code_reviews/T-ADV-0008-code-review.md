# Code Review: T-ADV-0008 — Continuidad de hilo en revisiones de Hades por tarea y reanudación tras espera de cuota

**Veredicto:** APROBADO

## Análisis estático y evidencias
- `git diff --check`: limpio (0 errores).
- Verificación en verde reutilizada sobre el árbol (`fa49560156`): `python -m unittest tests/test_orquestar.py`.

## Puntuaciones
| Criterio | Nota | Observaciones |
|---|---|---|
| **Corrección** | 10/10 | Cumple CA-M-1 a CA-M-4: extracción de `sesion` en Claude, Codex y Antigravity; reanudación de hilo en `agente()` y `ejecutar()` con fallback transparente a sesión limpia ante error no asociado a cuota; aislamiento por cambio de `ID`, bloqueo o escalada. |
| **Seguridad** | 10/10 | Los identificadores de sesión se pasan como argumentos posicionales en listas de `subprocess` sin interpolación en shell ni exposición de credenciales. |
| **Conformidad** | 10/10 | Fiel al triaje de `T-ADV-0008` y a la arquitectura del plan de plataforma (solo librería estándar de Python en `skills/orquestar/orquestar.py`). |
| **Calidad** | 9/10 | Código claro, cohesivo y alineado con las convenciones del módulo (`base_comando_agente`, `buscar_sesion_agente`, `buscar_sesion_paso`). |
| **Eficiencia** | 10/10 | Recorrido inverso con corte temprano sobre `orquestar_metricas.jsonl` y ahorro de tokens de entrada al omitir la cabecera estática en reanudaciones de Hades. |
| **Documentación** | 10/10 | Docstrings concisos en las funciones nuevas y modificadas; ningún documento de usuario queda desactualizado tras el delta. |

**Media:** 9.8/10

## Hallazgos
- 🔵 **BAJA** (`destino: descartar`) — En [`buscar_sesion_agente`](../../skills/orquestar/orquestar.py#L849-L856), las comprobaciones explícitas de `paso == 'especificar'` y `e.get('escalado') and not es_escalada` quedan cubiertas por las dos guardas generales inmediatamente posteriores (`bool(e.get('escalado')) != es_escalada` y `e.get('tipo') == 'paso' and not e.get('sin_cuota')`). No afecta al comportamiento y actúa como defensa explícita de dominio.
