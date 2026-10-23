# Test Review: T-ADV-0013

- **Veredicto**: APROBADO
- **Media**: 9.5 / 10

## Puntuaciones
- **Cobertura**: 9.5 / 10 — Cubre de extremo a extremo `CA-M-1`..`CA-M-4`: alias CLI (`--metricas`, `--metrics`, `--version-filtro`, `--csv` a `stdout`, `-` y ruta de fichero), formatos de filtro (`todas`/`all`, `ultima`/`last`, `ultimas:N`/`last:N`, lista de versiones y normalización `v0.X`/`v0.X.0`), las 20 columnas del esquema, separación de consumos/llamadas entre paso principal y Hades sin duplicar tiempos de espera ni de subagente, tarifas por familia de modelo con fallback y prioridad de `coste_usd` reportado, salida tabular con totales y manejo de entradas inválidas o JSONL corrupto.
- **Aserciones**: 9.5 / 10 — Verifican valores exactos de negocio, cabeceras, ausencia de efectos colaterales sobre `orquestar.pid` y `orquestar_evidencias.jsonl`, y códigos de retorno / `stderr` ante errores.
- **Rojo correcto**: 9.5 / 10 — Falla limpiamente en fase roja (`Ran 10 tests, FAILED (failures=19)`, código 2 de `argparse` por opciones `--metricas`/`--metrics`/`--csv` aún no implementadas) sin errores de sintaxis, imports ni fixtures.
- **Estabilidad**: 9.5 / 10 — Pruebas herméticas sobre `tempfile.TemporaryDirectory`, codificación UTF-8 explícita y fixtures deterministas sin dependencia de reloj, red ni estado externo.

## Hallazgos
Sin hallazgos.
