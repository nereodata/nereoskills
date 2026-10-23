# Test Review: T-ADV-0005 (Migración de proyectos con submódulo) — Ronda 2

- **Veredicto**: APROBADO
- **Media**: 9.5 / 10

## Puntuaciones

| Criterio | Nota | Comentario |
|---|---|---|
| **Cobertura** | 9.5/10 | Cubre fielmente los 5 escenarios de `migracion.feature`, ocultación local (`RF-F02-07` / `RF-F04-02`) y despacho CLI `adevv migrar`. |
| **Aserciones** | 9.5/10 | Comprueban comportamiento real: enlaces/junctions reales sin recorrer su interior, acotación exacta a 20 pendientes, inmutabilidad de archivos y exclusión de `README.md` en el repo fuente. |
| **Rojo correcto** | 9.5/10 | Las 7 pruebas fallan limpiamente por `NotImplementedError` en `adevv.migrate` y subcomando `migrar` pendiente en `adevv.cli`. |
| **Estabilidad** | 9.5/10 | Uso aislado de `TemporaryDirectory`, sin dependencias de reloj, red ni orden de ejecución. |

## Estado de hallazgos de la Ronda 1

- **H-01 (🟠 ALTA)** — `tests/test_migrate.py:98-149` (`test_deteccion_adaptadores_enlaces_y_copias_sin_recorrer`): **`resuelto`**. `scripts/orchestrate.py` cita literalmente `.agents/skills/orquestar/orquestar.py` y `.claude/skills` se crea como junction/enlace real hacia `.agents/skills` (con un `SKILL.md` interno que cita `.agents/`), comprobando sin mocks internos que su contenido no se recorre ni aparece en la salida.
- **H-02 (🟡 MEDIA)** — `tests/test_migrate.py:215-234` (`test_salida_acotada_20_pendientes`): **`resuelto`**. Verifica que la línea 20 se muestra y la línea 21 no aparece en la salida.
- **H-03 (🟡 MEDIA)** — `tests/test_migrate.py:165-214` (`test_migracion_repositorio_fuente_adevv_junction`): **`resuelto`**. `README.md` incluye una cita explícita a `.agents/` además de `git submodule deinit -f .agents`, discriminando su exclusión en el repositorio fuente de Adevv.

## Hallazgos nuevos

Sin hallazgos nuevos.
