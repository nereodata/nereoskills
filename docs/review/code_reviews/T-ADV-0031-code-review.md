# Code Review: T-ADV-0031 — Perfil de arnés, modelo y esfuerzo fijado por tarea o bug

- **Veredicto**: APROBADO
- **Ronda**: 2 (reevaluación del delta sin commitear completo, incluido `skills/orquestar/test_perfil_fijado.py`)

## Análisis estático
- `git diff --check` limpio; sin manifiestos cambiados ni secretos en el delta.
- Batería del triaje (`skills.orquestar.test_perfil_fijado` más reservas, cuotas, fallos de arnés, agentes, métricas, calidad, gateway y limpieza de instrucciones) en verde con `adevv orquestar --verificar`: 179 pruebas OK.

## Criterios de aceptación
| CA | Resultado |
|---|---|
| CA-M-1 (campo opcional, único o por rol, completado por dificultad) | ✓ `perfil_crudo`, `normalizar_perfil`, `aplicar_perfil`; flujo y bloque, con comentarios finales |
| CA-M-2 (precedencia, subagentes, `--agentes`, métricas) | ✓ `rol_de`, `agente`, `informe_agentes`; `perfil_fijado` explícito desde `cfg.get('fijado')` |
| CA-M-3 (reservas con aviso, estricto, escalada y promoción) | ✓ aviso al ejecutar la reserva usada; estricto sin reservas, espera la cuota, bloquea si falta el arnés o cuando el flujo normal promovería o escalaría |
| CA-M-4 (validación, solo una persona fija el perfil) | ✓ `errores_perfil` → PARAR; plantillas de `task-add`/`bug-add` con la línea comentada |
| CA-M-5 (task-add, bug-add, Telegram) | ✓ `extraer_perfil`, `alta`, buzón y `gateway.py` |
| CA-M-6 (pruebas y documentación) | ✓ las pruebas ejercitan `bucle()` real con frontmatter real (solo se simulan lanzamiento, git y firma); `docs/orquestacion.md` y `skills/orquestar/SKILL.md` actualizados |

## Hallazgos de la ronda anterior
- 🟠 1 Comentario YAML final rompe el `perfil` y la plantilla lo induce — **resuelto** (`sin_comentario`, plantilla comentada, `test_comentario_final_en_el_perfil`, pista de entrecomillar en el error).
- 🟡 2 `agotado_estricto` bloqueaba en `dificil` sin cambio de modelo — **resuelto** (reutiliza `comprobar_promocion` y `rechazos`/`escalada`; el estricto tampoco promueve por falta de progreso; `test_estricto_en_dificil_no_bloquea_por_ejecuciones`).
- 🟡 3 `registrar` marcaba de más y leía el backlog — **resuelto** (`marca_fijado(cfg_actual)`; las reservas y la escalada no llevan `fijado`).
- 🔵 4 El aviso nombraba una reserva que podía no usarse — **resuelto** (se emite al ejecutar la reserva real).

## Puntuaciones
| Criterio | Nota |
|---|---|
| Corrección | 9 |
| Seguridad | 9 |
| Conformidad | 9 |
| Calidad | 8 |
| Eficiencia | 8 |
| Documentación | 9 |
| **Media** | **8,7** |

## Hallazgos nuevos
- 🔵 **Dos ramas del estricto sin prueba propia** — `para: desarrollador`, destino `resolver`. El bloqueo por escalada en `dificil` (`agotado_estricto` vía `rechazos() >= escalada.rechazos`) y la rama sin progreso en `sencilla`/`media` que, con estricto, bloquea en vez de promover (`and not estricto`) no tienen prueba que las ejercite; `test_estricto_bloquea_en_lugar_de_escalar` entra por `comprobar_promocion`. Añadir un caso para cada una en `BucleTests`.
- 🔵 **`perfil_de` relee el backlog completo en cada `rol_de`/`aplicar_perfil`** — `para: desarrollador`, destino `descartar`. Coste lineal con el número de tareas, varias veces por paso; despreciable con backlogs del tamaño actual.
