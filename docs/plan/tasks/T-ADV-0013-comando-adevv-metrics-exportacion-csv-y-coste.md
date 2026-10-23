---
id: T-ADV-0013
title: "Comando adevv metrics con tabla por versión, exportación CSV y coste estimado de API"
type: funcional
weight: 100
dificultad: media
version: "v0.4.0"
status: planned
depende_de: []
origen: "Análisis comparativo de consumo, tokens originales/caché y tiempos por dificultad y versión"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0013: Comando adevv metrics con tabla por versión, exportación CSV y coste estimado de API

## 🎯 Objetivo de Negocio
Proporcionar un comando `adevv metrics` (y alias `adevv metricas`) que cruce `orquestar_metricas.jsonl` con el frontmatter del backlog (`docs/plan/tasks/` y `docs/plan/bugs/`) para analizar el rendimiento y el consumo real de cada tarea y versión, distinguiendo dificultad, tiempo estimado vs real, modelos empleados, tokens originales vs caché de desarrollo y de Hades, y coste estimado a precio de API, tanto en salida tabular por terminal como exportado a CSV.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Subcomando `adevv metrics` / `adevv metricas` y filtro `--version`):** `adevv/cli.py` registra los subcomandos `metrics` y `metricas` despachando al generador de métricas. Soporta `--version` (o `-v`) con formatos: `todas` / `all` (por defecto), `ultima` / `last` (la versión más reciente con métricas o en el backlog), `ultimas:N` / `last:N` (las `N` últimas versiones ordenadas por `vkey`), o una lista separada por comas (`v0.1,v0.2,v0.3`, aceptando `v0.3` y `v0.3.0` indistintamente).
- [ ] **CA-M-2 (Desglose de métricas por tarea y versión):** Para cada tarea/bug o paso de versión seleccionado, calcula y expone: `id`, `version`, `tipo` (`funcional`/`bug`/`version`), `dificultad` (`sencilla`/`media`/`dificil`), `tiempo_estimado_min` (referencia por dificultad: p. ej. `sencilla` = 7, `media` = 12, `dificil` = 25), `tiempo_real_min` (duración total de pasos en minutos), `modelos_dev` (modelos usados en el paso principal), `dev_tokens_originales` (`entrada`), `dev_tokens_cache` (`cache_leida`), `dev_tokens_salida` (`salida`), `dev_tokens_razonamiento` (`razonamiento`), `modelos_hades` (modelos usados por Hades), `hades_llamadas`, `hades_rechazos`, `hades_tokens_originales`, `hades_tokens_cache`, `hades_tokens_salida`, `verificaciones_totales`, `verificaciones_reutilizadas`, y `coste_estimado_usd`.
- [ ] **CA-M-3 (Estimación de coste API por modelo):** Cuando la fila de `orquestar_metricas.jsonl` no incluya `coste_usd` (o valga 0, como en `agy` y `codex`), calcula `coste_estimado_usd` aplicando una tabla de tarifas de referencia por millón de tokens (`entrada`, `cache_leida`, `salida`) según la familia del modelo (`claude-opus`, `claude-sonnet`, `claude-haiku`, `gemini-4-argon` / `gemini-pro`, `gemini-3.8-flash` / `gemini-flash`, `gpt` / `codex`, con tarifa por defecto razonable para modelos desconocidos).
- [ ] **CA-M-4 (Salida en tabla y exportación CSV con `--csv`):** Sin `--csv`, imprime un resumen legible en terminal con totales por versión; con `--csv [ruta.csv]` (si se pasa `--csv` sin valor o con `-`, escribe el CSV por `stdout`; si se pasa ruta, escribe el fichero CSV en UTF-8 con cabecera estándar), permitiendo abrirlo directamente en hojas de cálculo. Cubierto con pruebas unitarias.
