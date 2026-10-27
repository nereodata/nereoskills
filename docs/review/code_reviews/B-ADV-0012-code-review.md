# Revisión de código — B-ADV-0012

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Modo orquestado. Ronda única sobre el delta completo.

## Alcance

Código de producción y documentación del delta sin commitear (`git diff HEAD`): `skills/orquestar/orquestar.py` (`bloquear_sin_progreso` y su llamada en `bucle()`), `skills/orquestar/SKILL.md`, `docs/orquestacion.md` y `CHANGELOG.md`, frente al triaje del bug, a `docs/design/B-ADV-0012-design.md` y a la arquitectura existente (motor Python stdlib y backlog Markdown/Git). Las pruebas ya están aprobadas en `docs/review/test_reviews/B-ADV-0012-test-review.md` y no se revisan aquí. Aplicados Hades y `/review-code` de la instalación 0.6.1, ignorando el modelo.

## Análisis estático

`orquestar_evidencias.jsonl` registra en verde para la huella `c04b25f55cbf6466a65a958e15ebf9e87596f9f9`:

| Fecha y hora registradas | Comando | Código |
| --- | --- | --- |
| 2026-10-27T09:00:30 | python -m unittest tests.test_orquestar.BloqueoSinProgresoTests tests.test_orquestar.SuiteRecoveryTests tests.test_orquestar.DificultadTests | 0 |
| 2026-10-27T09:00:32 | python -m py_compile skills/orquestar/orquestar.py tests/test_orquestar.py | 0 |
| 2026-10-27T09:00:33 | git diff --check | 0 |
| 2026-10-27T09:00:44 | escaneo de secretos (script temporal) | 0 |

El intento previo de escaneo con `grep` terminó con 255, un error del propio comando y no un hallazgo; lo sustituye el escaneo en verde posterior. He recalculado la huella con el mismo método que `arbol()` (índice temporal, `add -A`, `write-tree`). Coincide con `c04b25f…` si se excluye `mandato-b12-code.txt`, que es posterior a la evidencia y ajeno al código, así que la evidencia corresponde al delta revisado. No hay lint ni tipado configurados, ni cambios de manifiestos. No relanzo nada ni ejecuto la suite completa.

## Puntuaciones

| Criterio | Nota | Justificación |
| --- | --- | --- |
| Corrección | 9/10 | Solo cambia la rama sin progreso de `task-dev`/`bug-fix` tras intentar la promoción. Los errores del arnés y la cuota salen antes, por su camino de siempre. `salida` siempre está inicializada. La tarea queda `blocked` y fuera de las elegibles, sus dependientes esperan porque `pendientes_de` exige `completed`, y `estado()` acaba en `FIN_VERSION[0]` con la bloqueada. La cola va indentada, así que no rompe el frontmatter ni las secciones, y un rebloqueo sustituye la sección anterior. El commit se limita a la tarea y la revisión. Queda una precondición implícita sobre el formato del fichero (H-C01). |
| Seguridad | 9/10 | Sin credenciales ni entradas externas nuevas. `git` se invoca con lista de argumentos y `--`. La salida del arnés se indenta antes de persistirla y el aviso usa el canal y la firma existentes. |
| Conformidad | 9/10 | Fiel al diseño: helper único, motivo con intentos, dificultad y últimos 2000 caracteres indentados, commit acotado a dos documentos y propagación de errores de Git (DEC-12-D1), y aviso por `respuesta`. No toca `estado()`, `pendientes_de()`, `promover_dificultad()` ni `registrar_fallo_suite()`. Sin desviaciones de arquitectura. |
| Calidad | 9/10 | Sigue el estilo y el precedente de `registrar_fallo_suite`. Nombres claros, sin duplicación ni código muerto. |
| Eficiencia | 10/10 | El camino normal no añade operaciones; las escrituras y el commit solo ocurren al agotar los intentos. |
| Documentación | 9/10 | El docstring describe el helper. `SKILL.md` y `docs/orquestacion.md` reflejan la excepción sin contradecir la regla de suite. Un detalle de formato en el CHANGELOG (H-C02). |

**Media: 9,17/10.** Sin hallazgos 🔴 ni 🟠.

## Hallazgos

### H-C01 — 🔵 BAJA — Partición del frontmatter frágil

- **Responsable:** desarrollador. **Destino:** resolver.
- **Ubicación:** `skills/orquestar/orquestar.py`, `bloquear_sin_progreso`: `fichero.read_text(...).split('\n---\n', 1)`.
- **Evidencia:** si el fichero termina en el `---` de cierre sin salto de línea, o sin cuerpo, el desempaquetado lanza `ValueError`.
- **Impacto:** el bucle se para con un traceback en lugar de bloquear la tarea. No se pierde trabajo, porque el error se propaga como en la parada anterior, pero el caso solo aparece con ficheros editados a mano.
- **Corrección sugerida:** partir con una expresión que acepte el cierre al final del fichero, o añadir `'\n'` al texto antes de partirlo.

### H-C02 — 🔵 BAJA — Línea en blanco en la lista del CHANGELOG

- **Responsable:** desarrollador. **Destino:** resolver.
- **Ubicación:** `CHANGELOG.md`, sección «Corregido».
- **Evidencia:** la entrada de B-ADV-0012 queda separada de las de B-ADV-0009 y B-ADV-0011 por una línea en blanco, y en el render se convierte en una lista suelta distinta.
- **Corrección sugerida:** quitar la línea en blanco tras la entrada nueva.

## Notas sin hallazgo

- El bug de cierre de suite, si su `bug-fix` no avanza en `dificil`, ahora también se bloquea localmente en vez de parar. Su regla propia de recaídas tras un arreglo `completed` no cambia (SuiteRecoveryTests en verde), y la versión termina igualmente en `FIN_VERSION[0]` informando del bloqueo. Es coherente con el contrato del bug.
- Las otras skills añaden contenido a `vX.Y-revision.md` y nunca lo reescriben, y `estado()` no lo usa para decidir la fase. Escribir en ella a mitad de versión no altera el selector.

Solo se escribe este informe en el árbol de trabajo; sin commits, cambios de estado, pruebas, producción ni copia instalada.
