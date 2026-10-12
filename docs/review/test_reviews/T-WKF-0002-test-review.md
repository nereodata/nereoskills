# Test Review: T-WKF-0002 — Gateway de Telegram (Ronda 2)

- **Revisor**: Hades (`/review-test`)
- **Fecha**: 2026-10-12
- **Artefactos**: `tests/test_telegram_gateway.py` frente a `tests/features/telegram_gateway.feature`
- **Ejecución en rojo comprobada**: `python -m unittest tests.test_telegram_gateway -v` → `Ran 11 tests`, `FAILED (failures=13)`. Ahora fallan los 11 tests, y los 13 *failures* incluyen 2 subtests de `/estado`/`/status` y 2 de CA-M-4. Todos fallan por aserción contra el stub. No hay errores de sintaxis, de import ni de fixtures, y `patch.object(gateway, "get_active_version")` resuelve porque el stub expone la función.

## Veredicto: **APROBADO**

La media es 9.0 y no hay hallazgos 🔴 ni 🟠. Los tres hallazgos 🟡 de la ronda 1 están resueltos.

## Puntuaciones

| Criterio | Nota | Motivo |
|---|---|---|
| Cobertura | 9 | Todos los escenarios y ejemplos de la feature tienen prueba, incluida ahora la rama "responde con error" de CA-M-4. Solo quedan los casos límite menores de H-5. |
| Aserciones | 9 | CA-M-1 comprueba ahora "ni modifica" sobre ficheros precargados y añade un control positivo. Ninguna aserción se cumple por construcción. |
| Rojo correcto | 9 | 11 de 11 tests fallan, por aserción y por la funcionalidad. |
| Estabilidad | 9 | Los casos sin versión activa ya no dependen de la rama git. Queda un acoplamiento leve con el punto de *mock* (H-6). |
| **Media** | **9.0** | |

## Hallazgos anteriores

| ID | Estado | Comprobación |
|---|---|---|
| 🟡 H-1 — CA-M-1 pasa en rojo y no comprueba "ni modifica" | **resuelto** | `tests/test_telegram_gateway.py:45-65`. Precarga una tarea y un bug, comprueba que su contenido y el número de ficheros no cambian en cada subtest, y el control positivo con `12345` hace fallar la prueba contra el stub. |
| 🟡 H-2 — "Sin versión activa" depende de la rama | **resuelto** | `:105` y `:147`. Se aplica `patch.object(gateway, "get_active_version", return_value="")`. Ver H-6 sobre el punto de *mock*. |
| 🟡 H-3 — CA-M-4 no cubre "responde con error" | **resuelto** | `:259-265`. Hay un subtest con `MagicMock(return_value=False)` que espera `False` y el WARNING literal. |
| 🔵 H-4 — `/estado` con igualdad exacta | descartar (sin cambios) | — |
| 🔵 H-5 — Casos límite menores (solo espacios, entrega parcial, valores por defecto de `notify`) | descartar (sin cambios) | — |

## Hallazgos nuevos

### 🔵 H-6 — El aislamiento de H-2 depende de que `handle_message` llame a `get_active_version` del módulo · `descartar`
`tests/test_telegram_gateway.py:105, 147`. El *mock* solo surte efecto si la implementación resuelve la versión mediante `gateway.get_active_version`, que es la función definida en el diseño y en el stub. Si la implementación leyera la rama por otra vía, el test volvería a depender del entorno. El riesgo es hipotético mientras se respete la interfaz del diseño, y `/review-code` lo detectaría.

### 🔵 H-7 — La precarga de CA-M-1 no incluye `task_config.yaml` · `descartar`
`tests/test_telegram_gateway.py:45-51`. La corrección sugerida mencionaba `task_config.yaml`, pero esa ruta no está en `docs/plan/`, que es lo que exige el step. Con la tarea y el bug precargados basta para cubrir "ni modifica".
