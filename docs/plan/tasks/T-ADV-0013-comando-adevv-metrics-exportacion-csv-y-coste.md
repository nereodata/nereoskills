---
id: T-ADV-0013
title: "Comando de métricas en orquestar (--metricas / --metrics) con tabla por versión, exportación CSV y coste estimado de API"
type: funcional
weight: 100
dificultad: media
version: "v0.4.0"
status: completed
depende_de: []
origen: "Análisis comparativo de consumo, tokens originales/caché y tiempos por dificultad y versión"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0013: Comando de métricas en orquestar (--metricas / --metrics) con tabla por versión, exportación CSV y coste estimado de API

## 🎯 Objetivo de Negocio
Proporcionar en `skills/orquestar/orquestar.py` (despachado por `adevv orquestar --metricas` y `adevv orquestar --metrics`) un generador de métricas que cruce `orquestar_metricas.jsonl` con el frontmatter del backlog (`docs/plan/tasks/` y `docs/plan/bugs/`) para analizar el rendimiento y el consumo real de cada tarea y versión, distinguiendo dificultad, tiempo estimado vs real, modelos empleados, tokens originales vs caché de desarrollo y de Hades, y coste estimado a precio de API, tanto en salida tabular por terminal como exportado a CSV.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Opciones `--metricas` / `--metrics` y filtro de versión en `skills/orquestar/orquestar.py`):** `skills/orquestar/orquestar.py` (ya despachado por `adevv orquestar`, sin necesidad de modificar `adevv/cli.py`, conforme a `DEC-P09`) registra `--metricas [FILTRO]` y `--metrics [FILTRO]` (`nargs='?'`, `const='todas'`, soportando también `--version-filtro <FILTRO>`). Soporta los formatos de filtro: `todas` / `all` (por defecto), `ultima` / `last` (la versión más reciente con métricas o en el backlog), `ultimas:N` / `last:N` (las `N` últimas versiones ordenadas por `vkey`), o una lista separada por comas (`v0.1,v0.2,v0.3`, aceptando `v0.3` y `v0.3.0` indistintamente).
- [x] **CA-M-2 (Desglose de métricas por tarea y versión):** Para cada tarea/bug o paso de versión seleccionado, calcula y expone (en `skills/orquestar/orquestar.py` o módulo auxiliar `skills/orquestar/metricas.py`): `id`, `version`, `tipo` (`funcional`/`bug`/`version`), `dificultad` (`sencilla`/`media`/`dificil`), `tiempo_estimado_min` (referencia por dificultad: p. ej. `sencilla` = 7, `media` = 12, `dificil` = 25), `tiempo_real_min` (duración total de pasos en minutos), `modelos_dev` (modelos usados en el paso principal), `dev_tokens_originales` (`entrada`), `dev_tokens_cache` (`cache_leida`), `dev_tokens_salida` (`salida`), `dev_tokens_razonamiento` (`razonamiento`), `modelos_hades` (modelos usados por Hades), `hades_llamadas`, `hades_rechazos`, `hades_tokens_originales`, `hades_tokens_cache`, `hades_tokens_salida`, `verificaciones_totales`, `verificaciones_reutilizadas`, y `coste_estimado_usd`.
- [x] **CA-M-3 (Estimación de coste API por modelo):** Cuando la fila de `orquestar_metricas.jsonl` no incluya `coste_usd` (o valga 0, como en `agy` y `codex`), calcula `coste_estimado_usd` aplicando una tabla de tarifas de referencia por millón de tokens (`entrada`, `cache_leida`, `salida`) según la familia del modelo (`claude-opus`, `claude-sonnet`, `claude-haiku`, `gemini-4-argon` / `gemini-pro`, `gemini-3.8-flash` / `gemini-flash`, `gpt` / `codex`, con tarifa por defecto razonable para modelos desconocidos).
- [x] **CA-M-4 (Salida en tabla, exportación CSV con `--csv` y pruebas unitarias en `skills/`):** Sin `--csv`, imprime un resumen legible en terminal con totales por versión; con `--csv [ruta.csv]` (`nargs='?'`, `const='-'`; si se pasa `--csv` sin valor o con `-`, escribe el CSV por `stdout`; si se pasa ruta, escribe el fichero CSV en UTF-8 con cabecera estándar), permitiendo abrirlo directamente en hojas de cálculo. Se documenta en `skills/orquestar/SKILL.md` y se cubre con pruebas unitarias en `skills/orquestar/test_metricas.py` (ejecutables con `adevv orquestar --verificar "python -m unittest skills/orquestar/test_metricas.py"`), dentro de las rutas autorizadas `skills/`.

## 🔬 Triaje de Alcance
- **Subfase A: Definición** → `[SKIP]` Opciones CLI y lógica interna de agregación en `skills/orquestar/orquestar.py` con contrato completo en `CA-M-1`..`CA-M-4` (`DEC-P09`); se verifica mediante pruebas unitarias en `skills/orquestar/test_metricas.py`.
- **Subfase B: Diseño** → `[EXEC]` Documento `docs/design/T-ADV-0013-design.md` con el diseño de agregación de registros, tarifas de referencia por modelo y exportación CSV.
- **Subfase C1: Pruebas (Red Phase)** → `[EXEC]` Pruebas unitarias en `skills/orquestar/test_metricas.py` para filtrado de versiones, agregación de tokens/tiempos/llamadas de desarrollo y Hades, estimación de coste por familia de modelo y salida tabular/CSV.
- **Subfase C2: Implementación (Green Phase)** → `[EXEC]` Implementación en `skills/orquestar/orquestar.py` (y/o `skills/orquestar/metricas.py`).
- **Subfase D: QA** → `[EXEC]` Revisión de Hades (`/review-code`) sobre el delta con `adevv orquestar --agente hades`.
- **Subfase E: Documentación** → `[EXEC]` Documentación de `--metricas` / `--metrics` y `--csv` en `skills/orquestar/SKILL.md`.
- **Subfase F: Cierre** → `[EXEC]` Cierre de tarea y commit semántico.
- **Verificación al cierre:** `python -m unittest skills/orquestar/test_metricas.py`. Estático del delta: `python -m py_compile skills/orquestar/metricas.py skills/orquestar/orquestar.py skills/orquestar/test_metricas.py` y `git diff --check`; sin linter/tipado configurados ni dependencias nuevas.
