# Code Review: T-WKF-0002 - Integración de Gateway de Telegram (Ronda 3)

- **Revisor**: Hades (`/review-code`)
- **Fecha**: 2026-10-12
- **Alcance**: `skills/telegram_gateway/gateway.py` (delta en `_default_http_post`, `get_updates` y `run_polling`), `skills/telegram_gateway/SKILL.md`
- **Referencias**: `docs/plan/tasks/T-WKF-0002-telegram-gateway-integration.md`, `docs/design/T-WKF-0002-design.md`, reporte de la Ronda 2

## ⚖️ Veredicto: **APROBADO**

Media 8.7 (> 8), sin hallazgos 🔴 ni 🟠 abiertos. H-10 y H-11 están resueltos.

## 🔍 Análisis estático

- **Evidencia aportada (no repetida):** 23/23 tests en verde (17 de gateway y 6 de orquestador) y `git diff --check` limpio. No hay `orquestar_evidencias.jsonl` para este árbol.
- **`py_compile`:** limpio. `urllib.error` está importado.
- **Secretos y dependencias:** sin cambios respecto a la Ronda 2.
- **Comprobación propia de H-10, con un script desechable que simula `urlopen`:**
  - `/tarea arreglar test_orquestar` con `sendMessage` respondiendo 400 cuando lleva `parse_mode`: se hace un primer envío con Markdown y un segundo en texto plano. La tarea se crea una sola vez y `run_polling` termina con normalidad.
  - `handle_message` lanzando `OSError` durante 2 iteraciones: se registra el error con `logger.error` y el bucle continúa.

## 📊 Puntuaciones

| Criterio | Nota |
|---|---|
| Corrección | 9 |
| Seguridad | 8 |
| Conformidad | 9 |
| Calidad | 8 |
| Eficiencia | 9 |
| Documentación | 9 |
| **Media** | **8.7** |

## ✅ Estado de los hallazgos anteriores

| Hallazgo | Estado | Comprobación |
|---|---|---|
| 🟠 H-1, H-2 · 🟡 H-3 a H-6 · 🔵 H-7 | **resuelto** | Resueltos en la Ronda 2. El delta no los toca. |
| 🟠 H-10 Caída del daemon y duplicados al reiniciar | **resuelto** | `_default_http_post` (`gateway.py:298-313`) reintenta en texto plano si recibe un 400 con `parse_mode` y convierte cualquier otro fallo de red en `False` con un warning. `run_polling` (`gateway.py:376-393`) avanza el `offset` antes de procesar y aísla cada update en `try/except Exception`. Un mensaje fallido ya no detiene el proceso, y el `offset` se confirma en el siguiente `getUpdates`, así que no se duplican tareas. Verificado (ver arriba). Se conserva el formato Markdown en el caso normal, como pide el diseño. |
| 🔵 H-11 Errores de `getUpdates` invisibles | **resuelto** | `get_updates` registra el fallo con `logger.warning` (`gateway.py:357-358`). El bucle espera 1 s antes de reintentar, así que el ritmo de logs está acotado. |
| 🔵 H-8, H-9, H-12 | descartados | Sin cambios. |

## 🐞 Hallazgos nuevos

Ninguno 🔴, 🟠 ni 🟡.

### 🔵 H-13: Con un fallo persistente de `getUpdates` se registra un warning cada segundo — destino: `descartar`
`gateway.py:357-358`, `gateway.py:395-396`. Con un token inválido el log crece a razón de un warning por segundo. Es aceptable para un daemon supervisado. Si molesta, se puede registrar solo el primer fallo de cada racha o aplicar un backoff.
