# Code Review: B-ADV-0014 — Las dependencias inválidas ya no paran el bucle

- **Fecha**: 2026-10-27 (segunda ronda)
- **Revisor**: Hades
- **Delta**: preparado en el índice sobre `be21713` — `skills/orquestar/orquestar.py`, `skills/orquestar/SKILL.md` (las pruebas de `tests/test_orquestar.py` quedan para `/review-test`)

## Veredicto: APROBADO

## Análisis estático
`adevv orquestar --verificar "python -m unittest tests.test_orquestar"` en verde sobre el árbol revisado (`orquestar_evidencias.jsonl`, 10:32:53). El delta no añade dependencias ni secretos. No relanzo nada.

## Puntuaciones
| Criterio | Nota |
|---|---|
| Corrección | 9 |
| Seguridad | 10 |
| Conformidad | 9 |
| Calidad | 9 |
| Eficiencia | 9 |
| Documentación | 8 |
| **Media** | **9,0** |

## Hallazgos de la ronda anterior

- 🟠 **El contador cortaba la recuperación de análisis** — **resuelto**. El contador ahora está en la rama `else` del final del bucle (`orquestar.py:2823-2831`), que solo se alcanza si la firma cambió. Las ejecuciones sin progreso las sigue llevando la cadena de recuperación (escala de perfil y, si se agota, para con el diagnóstico), así que la sección «Recuperación de análisis sin progreso» de SKILL.md vuelve a ser cierta. La parada llega tras `--reintentos` ejecuciones con cambios y los mismos errores (`>=`), y el contador se vacía en cuanto el backlog queda sin errores. La nueva prueba de `bucle()` cubre la parada con evento `respuesta`, con los errores tanto en el prompt como en el aviso.
- 🟡 **`intentos_dependencias` no pasaba por la recarga** — **resuelto**. Se serializa como lista de `{errores, n}` y se reconstruye con claves tupla (`orquestar.py:2504`, `2513-2515`).
- 🔵 **Se calculan dos veces los errores por paso** — persiste, sigue en `descartar`.

## Hallazgos nuevos

### 🔵 BAJA — La fila de la tabla de estados no dice qué cuenta como intento (resolver)
`SKILL.md:91`. «si tras `--reintentos` siguen los mismos» no aclara que solo cuentan las ejecuciones que cambian el disco; las que no cambian nada siguen la recuperación de análisis. Basta con media frase, por ejemplo: «tras `--reintentos` ejecuciones con cambios que dejan los mismos errores».

### 🔵 BAJA — Las salidas tempranas por «paso completado» no cuentan (descartar)
Las ramas `paso_completado` y «completado en disco a pesar del retorno» (`orquestar.py:2748`, `2774`) hacen `continue` antes de la rama `else`. Un arnés que siempre devolviera error pero tocara el disco sin quitar los errores no sumaría intentos y solo pararía al llegar a `--max-pasos`. Es un caso hipotético y el límite lo acota.

### 🔵 BAJA — Errores que cambian en cada intento no paran por este contador (descartar)
Si Cronos alterna entre conjuntos distintos de errores, ninguna tupla llega a `--reintentos` y solo para al llegar a `--max-pasos`. Es lo que pide el bug («los mismos errores»).
