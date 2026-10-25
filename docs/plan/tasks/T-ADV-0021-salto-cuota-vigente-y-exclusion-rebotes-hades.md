---
id: T-ADV-0021
title: "Salto de configuraciones con cuota agotada vigente en agente() y exclusión de rebotes sin cuota en hades_llamadas"
type: funcional
weight: 100
dificultad: media
version: "v0.6.0"
status: backlog
depende_de: ["B-ADV-0004"]
origen: "Detección en producción (Afinn, Adevv 0.5.0) de rebotes repetidos al titular sin cuota en agente() e inflación de hades_llamadas en metricas.py"
created_at: 2026-10-25
updated_at: 2026-10-25
---

# T-ADV-0021: Salto de configuraciones con cuota agotada vigente en agente() y exclusión de rebotes sin cuota en hades_llamadas

## 🎯 Objetivo de Negocio
Evitar que `agente()` (y `bucle()` cuando existen reservas disponibles) reintente en cada puerta de revisión un modelo titular cuya ventana de agotamiento de cuota sigue vigente en `orquestar_metricas.jsonl`, e impedir que los intentos fallidos por falta de cuota inflen artificialmente el contador `hades_llamadas` en `skills/orquestar/metricas.py`.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Salto de configuraciones con cuota agotada vigente en `agente()`):** En `agente(root, rol, prompt)` (`skills/orquestar/orquestar.py`), antes de iterar sobre `configs_a_probar = [cfg] + reservas`, se consultan las cuotas agotadas vigentes mediante `consumo_cuotas(root, fecha_estado(ahora()))[1]`. Si existen varias configuraciones en `configs_a_probar` y alguna configuración tiene agotamiento vigente en `cuotas` para su clave `(harness, cfg_actual.get('model') or 'predeterminado')`, se salta directamente a la primera configuración sin agotamiento vigente (conservando el último elemento o la lista original si todas estuvieran agotadas, para no dejar `configs_a_probar` vacía).
- [ ] **CA-M-2 (Exclusión de rebotes sin cuota en `hades_llamadas` de `metricas.py`):** En `agregar(registros, items, filtro='todas')` (`skills/orquestar/metricas.py`), cuando `grupo == 'hades'`, `fila['hades_llamadas']` solo se incrementa si el registro corresponde a una ejecución efectiva de revisión y no a un rebote por falta de cuota (es decir, cuando no tiene `cuota_espera_s` ni `sin_cuota` activos y, si el registro declara `modelos` como diccionario vacío por fallo temprano sin ejecución, no se contabiliza como llamada efectiva).
- [ ] **CA-M-3 (Pruebas unitarias y documentación):** Pruebas unitarias en `tests/test_orquestar.py` y `skills/orquestar/` verifican: (1) que tras registrar un agotamiento de cuota vigente del titular de `hades`, la siguiente invocación a `agente(root, 'hades', ...)` invoca directamente a la reserva sin volver a lanzar el titular agotado; (2) que cuando la ventana de agotamiento ha expirado, `agente()` vuelve a usar el titular; y (3) que `metricas.agregar()` no incrementa `hades_llamadas` con filas de rebote por cuota (`cuota_espera_s` / `sin_cuota` / `modelos: {}`), manteniendo intacto el conteo de llamadas reales y de `hades_rechazos`.
