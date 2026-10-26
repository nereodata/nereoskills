---
id: T-ADV-0021
title: "Salto de configuraciones con cuota agotada vigente en agente() y exclusión de rebotes sin cuota en hades_llamadas"
type: funcional
weight: 100
dificultad: media
version: "v0.6.0"
status: completed
depende_de: ["B-ADV-0004"]
origen: "Detección en producción (Afinn, Adevv 0.5.0) de rebotes repetidos al titular sin cuota en agente() e inflación de hades_llamadas en metricas.py"
created_at: 2026-10-25
updated_at: 2026-10-25
---

# T-ADV-0021: Salto de configuraciones con cuota agotada vigente en agente() y exclusión de rebotes sin cuota en hades_llamadas

## 🎯 Objetivo de Negocio
Evitar que `agente()` (y `bucle()` cuando existen reservas disponibles) reintente en cada puerta de revisión un modelo titular cuya ventana de agotamiento de cuota sigue vigente en `orquestar_metricas.jsonl`, e impedir que los intentos fallidos por falta de cuota inflen artificialmente el contador `hades_llamadas` en `skills/orquestar/metricas.py`.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Salto de configuraciones con cuota agotada vigente en `agente()`):** En `agente(root, rol, prompt)` (`skills/orquestar/orquestar.py`), antes de iterar sobre `configs_a_probar = [cfg] + reservas`, se consultan las cuotas agotadas vigentes mediante `consumo_cuotas(root, fecha_estado(ahora()))[1]`. Si existen varias configuraciones en `configs_a_probar` y alguna configuración tiene agotamiento vigente en `cuotas` para su clave `(harness, cfg_actual.get('model') or 'predeterminado')`, se salta directamente a la primera configuración sin agotamiento vigente (conservando el último elemento o la lista original si todas estuvieran agotadas, para no dejar `configs_a_probar` vacía).
- [x] **CA-M-2 (Exclusión de rebotes sin cuota en `hades_llamadas` de `metricas.py`):** En `agregar(registros, items, filtro='todas')` (`skills/orquestar/metricas.py`), cuando `grupo == 'hades'`, `fila['hades_llamadas']` solo se incrementa si el registro corresponde a una ejecución efectiva de revisión y no a un rebote por falta de cuota (es decir, cuando no tiene `cuota_espera_s` ni `sin_cuota` activos y, si el registro declara `modelos` como diccionario vacío por fallo temprano sin ejecución, no se contabiliza como llamada efectiva).
- [x] **CA-M-3 (Pruebas unitarias y documentación):** Pruebas unitarias en `tests/test_orquestar.py` y `skills/orquestar/` verifican: (1) que tras registrar un agotamiento de cuota vigente del titular de `hades`, la siguiente invocación a `agente(root, 'hades', ...)` invoca directamente a la reserva sin volver a lanzar el titular agotado; (2) que cuando la ventana de agotamiento ha expirado, `agente()` vuelve a usar el titular; y (3) que `metricas.agregar()` no incrementa `hades_llamadas` con filas de rebote por cuota (`cuota_espera_s` / `sin_cuota` / `modelos: {}`), manteniendo intacto el conteo de llamadas reales y de `hades_rechazos`.

## Triaje de alcance

- **A: Definición [SKIP]**: corrección técnica interna; CA-M-1..3 definen completamente el contrato, sin modificar escenarios funcionales externos.
- **B: Diseño [EXEC]**: selección compartida de configuraciones en `agente()` y `bucle()`, documentada en `docs/design/T-ADV-0021-design.md`.
- **C1: Pruebas [EXEC]**: regresiones aisladas en `skills/orquestar/test_cuota_vigente.py`; conservar y ejecutar `ReservaCuotaTests` de `tests/test_orquestar.py` sin modificarlo, conforme a las rutas autorizadas y DEC-P09.
- **C2: Implementación [EXEC]**: selección por agotamiento vigente y exclusión de rebotes del contador de llamadas.
- **D: QA [EXEC]**: Hades sobre todo el delta de la tarea.
- **E: Documentación [EXEC]**: contrato operativo en `skills/orquestar/SKILL.md` y validación humana en la revisión de versión.
- **F: Cierre [EXEC]**: estado final y commit semántico en `release/v0.6`.

**Verificación al cierre**: `python -m unittest skills/orquestar/test_cuota_vigente.py skills/orquestar/test_metricas.py skills/orquestar/test_estado_agentes.py tests.test_orquestar.ReservaCuotaTests` ejercita selección, caducidad, reservas y contabilidad; `git diff --check` comprueba el delta. Sin dependencias nuevas ni linter/tipado configurados: comprobación sintáctica con `python -m py_compile skills/orquestar/test_cuota_vigente.py skills/orquestar/orquestar.py skills/orquestar/metricas.py`.

**DEC-T21-01**: conservar únicamente la última configuración si todas están agotadas; sin reservas se conserva el titular. El agotamiento solo afecta a la selección, no a la contabilidad de rechazos, tokens o coste.
**DEC-T21-02**: `bucle()` conserva la selección anterior con `--harness` o `--cmd`, que pueden ignorar el modelo configurado; no hay una clave de arnés/modelo fiable para aplicar el filtro.

## Cierre

- Hades review-test: APROBADO (9.5/10), H-01 resuelto; review-code: APROBADO (9.7/10), sin hallazgos pendientes ni deuda.
- Verificacion del triaje: 31 tests OK; sintaxis y git diff --check limpios, con evidencia registrada y reutilizada mediante --verificar.
- Documentacion operativa y revision humana de v0.6 actualizadas.
