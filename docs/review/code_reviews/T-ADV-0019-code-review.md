# Revisión de Código: T-ADV-0019

- **Ronda**: 2 — reevaluación tras subsanar H1.
- **Tarea**: `docs/plan/tasks/T-ADV-0019-firma-version-en-telegram-y-modelos-siempre-en-estado.md`.
- **Diseño**: `docs/design/T-ADV-0019-design.md`.
- **Arquitectura**: `docs/requirements/platform_plan.md` (`DEC-P09`, `DEC-P10`).
- **Archivos de producción del delta**: `skills/orquestar/orquestar.py`, `skills/telegram_gateway/gateway.py`, `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md`.
- **Veredicto**: **APROBADO**.
- **Puntuación media**: **9.00 / 10**. Sin hallazgos críticos ni altos pendientes.

## Análisis estático y evidencia

- **Compilación**: se acepta la evidencia aportada de `python -m py_compile` limpio sobre todos los módulos modificados.
- **Formato**: se acepta la evidencia aportada de `git diff --check` limpio.
- **Seguridad y dependencias**: evidencia aportada sin secretos ni credenciales en el delta; uso de stdlib sin dependencias externas ni cambios de manifiestos. La corrección no introduce nuevas entradas externas, ejecución de comandos ni cambios de autorización.
- **Linter / tipado**: N/A; no se aporta un chequeo específico adicional aplicable.
- **Verificación funcional aportada**: `adevv orquestar --verificar "python -m unittest skills/orquestar/test_firma_telegram.py skills/telegram_gateway/test_firma_gateway.py"`, 13 tests en verde sobre el árbol identificado por el invocante como `0570712106`. Se acepta también la evidencia comunicada del caso con `detalle_estado` devolviendo una lista representativa y comprobación de texto legible y firma final `— Adevv v0.5.0`. No se relanzan pruebas ni comprobaciones acreditadas y no se auditan las pruebas en esta revisión.

## Puntuaciones de Ronda 2 (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| Corrección | 9 | La conversión explícita de las líneas de `/agentes` y `/agents` produce texto con saltos de línea antes de pasar por la firma común; elimina el fallo de integración de H1. |
| Seguridad | 10 | Sin nuevos secretos, dependencias, ejecución de shell ni cambios en el control de usuarios autorizados. |
| Conformidad | 9 | La corrección satisface el contrato de respuesta textual firmada de la sección 3 del diseño y CA-M-1 para ambas variantes del comando. Mantiene las capas y rutas de DEC-P09/DEC-P10. |
| Calidad | 9 | Adaptación local y explícita del contrato de retorno; conserva la utilidad compartida y los consumidores existentes de `detalle_estado`. |
| Eficiencia | 9 | Unión lineal de las líneas ya disponibles, sin nuevas consultas de red, procesos ni cálculo del estado adicional. |
| Documentación | 8 | Las dos skills mantienen documentada la firma al pie y el gateway describe la idempotencia y el arnés/modelo. La garantía documental afectada por H1 queda satisfecha. |

## Seguimiento de hallazgos anteriores

### H1 — 🟠 ALTA: `/agentes` devuelve una lista y elude la firma — RESUELTO

- **Ronda 1**: hallazgo asignado a `desarrollador`, destino `resolver`. La rama asignaba directamente a `resp` la lista devuelta por `motor.detalle_estado(...)`; `firmar` conservaba los valores no textuales y el transporte recibía una representación de lista sin firma.
- **Ubicación de la subsanación**: `skills/telegram_gateway/gateway.py:235-237`; retorno común firmado en `:272`.
- **Evidencia de resolución**: ambas variantes (`/agentes`, `/agents`) comparten la rama que obtiene `det` y aplica `'\n'.join(det) if isinstance(det, (list, tuple)) else str(det or '')`. El contrato real de `detalle_estado` construye líneas de texto y devuelve una lista. La unión produce una cadena legible, que llega a `firmar(resp)` y recibe la firma al pie. El tratamiento alternativo conserva los retornos textuales y normaliza valores ausentes.
- **Impacto de la corrección**: no altera `detalle_estado` ni sus otros consumidores; tampoco cambia el transporte o la idempotencia. El recorrido de tipos que causó H1 queda corregido sin extender el alcance a otras interfaces.
- **Resultado**: `resuelto`; sin acciones pendientes para H1.

## Hallazgos nuevos en Ronda 2

Ninguno. La corrección no presenta regresiones identificables por lectura en el recorrido revisado.

## Alcance y método

Reevaluación por lectura del informe anterior y de la subsanación de H1, contrastada con el delta de producción, el contrato de `detalle_estado`, la tarea, el diseño y DEC-P09/DEC-P10. Se mantiene el alcance de la segunda ronda en el hallazgo y sus efectos: no se reabre la revisión completa de componentes que la corrección no afecta. No se auditan pruebas ni se modifica código, diseño o documentación de usuario. No se ejecutan experimentos ni verificaciones adicionales; se acepta la evidencia en verde aportada para el árbol revisado.

## Historial de veredictos

- **Ronda 1**: RECHAZADO, media **8.00 / 10**; H1 alto pendiente (corrección 6, seguridad 10, conformidad 7, calidad 8, eficiencia 9, documentación 8).
- **Ronda 2**: APROBADO, media **9.00 / 10**; H1 resuelto, sin hallazgos nuevos ni críticos o altos pendientes.
