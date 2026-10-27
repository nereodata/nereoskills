# B-ADV-0015 — Code Review

**Revisor**: Hades · **Fecha**: 2026-10-27 · **Delta**: `git diff HEAD` (sin commitear) — `skills/orquestar/orquestar.py` (`cambiar_de_rama` y sus dos llamadas en `bucle()`), `skills/orquestar/SKILL.md`; pruebas (`tests/test_orquestar.py`, `skills/orquestar/test_cambio_rama_sucia.py`) fuera del alcance de esta skill.

## Veredicto: ✅ APROBADO

Media 8,8, sin 🔴 ni 🟠.

## Análisis estático
Verificación en verde del árbol (`adevv orquestar --verificar "python -m unittest skills.orquestar.test_cambio_rama_sucia tests.test_orquestar"`); no se relanza. El delta no toca manifiestos ni credenciales; no hay secretos en el diff. Los archivos de estado propios del bucle (`orquestar.log`, `.pid`, `_evidencias.jsonl`…) están ignorados, así que `status --porcelain` y `stash -u` no los tocan.

## Puntuaciones
| Criterio | Nota |
|---|---|
| Corrección | 8 |
| Seguridad | 9 |
| Conformidad | 9 |
| Calidad | 9 |
| Eficiencia | 9 |
| Documentación | 9 |

Conformidad con el bug: los tres comportamientos esperados se cumplen. Clio commitea o descarta; si quedan cambios, se hace `git stash push -u -m "orquestar: <rama> <fecha>"`, se avisa con el nombre del stash y el bucle sigue; solo se para si el stash no deja el árbol limpio, y en ese caso el trabajo sigue en el árbol o en el stash, así que no se pierde. Capturar `SystemExit` de `agente()` es correcto, porque `agente` usa `sys.exit` para los errores de configuración. Las dos llamadas de `bucle()` quedan unificadas. En `SKILL.md`, el nuevo párrafo y la fila del evento `error` coinciden con el código; no queda ningún documento que diga que se para por cambios sin commitear.

## Hallazgos

### 🟡 MEDIA — El checkout no se comprueba · destino: `resolver`
`orquestar.py:1848`: `git('checkout', '-q', rama)` ignora el código de salida, y `cambiar_de_rama` devuelve `True` aunque el checkout falle. En el cierre de versión esto es una regresión: antes se usaba `subprocess.run(..., check=True)`. Si el checkout fallara (rama inexistente o un conflicto con archivos del árbol), el bucle pasaría la suite y, con `registrar_fallo_suite`, commitearía el bug de cierre en la rama equivocada sin avisar. Es poco probable con el árbol ya limpio, y en la ruta de pasos el fallo silencioso ya existía, pero arreglarlo es barato: al final, `return git('branch', '--show-current') == rama`. Con eso, la llamada existente ya para con «no puedo cambiar a <rama>».

### 🔵 BAJA — Trabajo interrumpido en un stash · destino: `descartar`
`task-dev`/`bug-fix` retoman desde los cambios sin commitear de un intento interrumpido (por ejemplo, por cuota). Si el bucle cambia de rama antes de retomarlo y Clio no commitea esos cambios, acaban en el stash y la tarea se rehará desde el último commit. No se pierde trabajo: queda en el stash y se avisa por Telegram. Además, el prompt de Clio ya orienta a commitear «lo que pertenezca al trabajo hecho». Es un riesgo hipotético.
