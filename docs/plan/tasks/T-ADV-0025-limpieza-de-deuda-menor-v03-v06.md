---
id: T-ADV-0025
title: "Limpieza de deuda menor descartada en las revisiones de v0.3 a v0.6"
type: funcional
weight: 300
dificultad: sencilla
version: "v1.0.0"
status: planned
depende_de: []
origen: "Hallazgos 🔵 con destino descartar en docs/review/versions/v0.4-arquitectura.md, v0.5-arquitectura.md y v0.6-arquitectura.md"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0025: Limpieza de deuda menor descartada en las revisiones de v0.3 a v0.6

## 🎯 Objetivo de Negocio
Antes de etiquetar la v1.0, eliminar los detalles de mantenimiento que Hades fue descartando por ser menores, empezando por uno que es un fallo latente.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Versión de respaldo):** `version_adevv()` (`skills/orquestar/orquestar.py:68`) no devuelve un literal fijo (`'0.5.0'` hoy, con la versión ya en 0.6.0). Usa como respaldo la versión de los manifiestos (`pyproject.toml` / `task_config.yaml`) o un valor explícito de «desconocida», y una prueba impide que vuelva a quedar desfasado.
- [ ] **CA-M-2 (Propiedad de PID):** la comprobación de propiedad de PID repetida en `orquestar.py` reutiliza un único helper compartido con `gateway.py` (`es_propietario_pid`), y la verificación de PID vivo es simétrica entre `telegram.pid` y `orquestar.pid` (v0.4 y v0.6).
- [ ] **CA-M-3 (Ruta de versiones):** la resolución de `ADEVV_HOME/versions/<ver>` se hace en un único sitio, usado por `version_adevv` y `version_activa_distinta` (v0.5).
- [ ] **CA-M-4 (Restos de compatibilidad):** se retira `detalle_estado(root, e)` si solo la usan pruebas antiguas, adaptándolas (v0.5); se unifican las utilidades duplicadas entre `orquestar.leer_metricas`/`vkey` y `metricas.py` (v0.4).
- [ ] **CA-M-5 (Sin cambio de comportamiento):** la suite completa sigue en verde y no cambia ninguna salida visible salvo la del CA-M-1.
