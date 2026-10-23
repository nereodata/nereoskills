**Veredicto:** APROBADO

# Code Review: T-ADV-0011 · Subida automática de dificultad de la tarea tras más de 2 reintentos

## Análisis estático y evidencias
- `git diff --check`: limpio (0 errores).
- `python -m unittest tests/test_orquestar.py`: verificado en verde sobre el árbol `3a9231eba6` (`--verificar`).

## Puntuaciones
| Criterio | Nota | Comentario |
|---|---|---|
| **Corrección** | 9/10 | La transición `sencilla` → `media` → `dificil`, el reinicio de contadores tras un evento `promocion` en `orquestar_metricas.jsonl` y la integración con `tope_de_rechazos` y `bucle()` son correctos. |
| **Seguridad** | 10/10 | Sin superficie de inyección ni manejo inseguro de credenciales o rutas. |
| **Conformidad** | 9/10 | Conforme con los criterios `CA-M-1` a `CA-M-4` de la tarea y con las decisiones `DEC-D01` a `DEC-D05` de `docs/design/T-ADV-0011-design.md`. |
| **Calidad** | 9/10 | Funciones cohesivas, nombres consistentes con el resto de `skills/orquestar/orquestar.py` y sin duplicación innecesaria. |
| **Eficiencia** | 10/10 | Coste despreciable en lectura de frontmatter y recorrido lineal de `orquestar_metricas.jsonl`. |
| **Documentación** | 9/10 | Docstrings concisos en las nuevas funciones y comportamiento documentado en `skills/orquestar/SKILL.md`. |

**Media:** 9.3 / 10

## Hallazgos

- 🔵 **BAJA** · `skills/orquestar/orquestar.py` (líneas 1567-1574) · `destino: descartar`
  `antes = firma(root, a.docs)` se calcula inmediatamente antes de `promover_dificultad(root, arg, motivo=motivo)`. Cuando la promoción ocurre al inicio del paso, la escritura de `dificultad:` en el frontmatter cambia la firma del árbol respecto a `antes` en esa iteración. No compromete la parada del bucle porque en la iteración siguiente `comprobar_promocion` ya devuelve `False` y `sin_progreso` contabiliza con normalidad.
