---
id: T-ADV-0004
title: "Actualización automática de versiones publicadas"
type: funcional
weight: 140
version: "v0.1.0"
status: completed
depende_de: [T-ADV-0001, T-ADV-0002]
origen: "F-03 (docs/requirements/funcionalidades/F-03_actualizacion_automatica.md)"
created_at: 2026-10-22
updated_at: 2026-10-22
---

# T-ADV-0004: Actualización automática de versiones publicadas

## 🎯 Objetivo de Negocio
Garantizar que cualquier nueva versión publicada de Adevv se detecte y se instale automáticamente al ejecutar la siguiente orden `adevv` sin intervención manual, sin bloquear ni romper bucles o gateways en marcha en Windows, sin esperar a la red más de 5 segundos y permitiendo volver a una versión anterior con `adevv actualizar X.Y.Z`.

### Hueco real (Delta sobre el código actual)
- **Ya existe:** El almacén `~/.adevv/` y el sincronizador de destinos (`T-ADV-0002`), junto con el formato de paquete y etiquetas anotadas (`T-ADV-0001`).
- **Falta implementar:** `adevv/processes.py` (enumeración de procesos vivos en Windows y POSIX y clasificación en `bucle | gateway | otro`, incluyendo procesos anteriores a la migración que invocan `orquestar.py` o `gateway.py` e ignorando PIDs reutilizados) y `adevv/updater.py` (evaluación de la tabla de 9 resultados y ejemplos `E1`–`E13`, consulta de etiquetas anotadas `vX.Y.Z^{}` con `git ls-remote --tags` en ≤ 5 s sin ventanas de credenciales, descarga e instalación lado a lado en `~/.adevv/versions/<V>/` en ≤ 180 s, conmutación atómica de `active.json`, resincronización con el `sync.py` de la nueva versión, limpieza de versiones antiguas sin procesos en uso, órdenes `adevv actualizar` y `adevv actualizar X.Y.Z`, y emisión de avisos en una línea por `stderr`).

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (`@CA-F03-01`, `@CA-F03-11`, `@CA-F03-15`, `@RF-F03-01`, `@RF-F03-04`, `@RF-F03-05`):** Al arrancar cualquier orden `adevv`, el sistema evalúa antes de la acción la tabla de 9 resultados (`DESACTIVADA`, `DENTRO_DE_ORQUESTACION`, `DESARROLLO`, `ESPERA`, `SIN_RED`, `AL_DIA`, `APLAZADA`, `APLICADA`, `FALLIDA`), cumple todos los casos de la ventana temporal (`E1`–`E13`: 24 h entre comprobaciones contadas, 1 h tras `SIN_RED`, 7 días para aviso de fallo de red prolongado, aplicación inmediata de versión aplazada al quedar sin bucles), no consulta la red dentro de un paso del bucle (`ORQUESTAR_PASO` o `ADEVV_BOOTSTRAPPED`) ni con la actualización automática desactivada, y guarda atómicamente el estado en `update_state.json`.
- [x] **CA-M-2 (`@CA-F03-06`, `@CA-F03-07`, `@RF-F03-02`, `@RF-F03-03`):** La consulta de versiones se realiza únicamente contra el origen fijo en ≤ 5 segundos sin abrir ventanas ni pedir credenciales (`GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`), ignorando etiquetas ligeras, ramas o pre-releases (`v0.2.0-rc1`) y comparando versiones numéricamente (`0.10.0 > 0.9.3`).
- [x] **CA-M-3 (`@CA-F03-03`, `@CA-F03-04`, `@CA-F03-05`, `@RF-F03-06`, `@RF-F03-08`):** Con cualquier bucle en marcha (incluidos los lanzados antes de la migración con `python .agents/skills/orquestar/orquestar.py`), el sistema no instala nada, guarda la versión como aplazada y avisa nombrando los bucles; en cambio, los procesos `gateway` u `otro` no aplazan la actualización, siguen ejecutándose sin fallos sobre su carpeta inmutable `~/.adevv/versions/<anterior>/` y el aviso de actualización añade `Reinicia el gateway en <carpeta>.`.
- [x] **CA-M-4 (`@CA-F03-02`, `@CA-F03-08`, `@CA-F03-09`, `@CA-F03-10`, `@CA-F03-16`, `@RF-F03-07`, `@RF-F03-09`, `@RF-F03-13`):** Al aplicar una versión nueva `A.B.C`, el sistema instala en `~/.adevv/versions/A.B.C/` el commit exacto de la etiqueta consultada en ≤ 180 s, comprueba que la versión del paquete sea `A.B.C`, conmuta `active.json`, sincroniza los destinos con el `sync.py` de `A.B.C`, limpia las versiones antiguas que no use ningún proceso vivo y ejecuta la acción de la orden ya con la `A.B.C` emitiendo el aviso solo por `stderr`; si la instalación falla o la versión del paquete no coincide, la acción se ejecuta íntegra con la versión anterior intacta y se registra `A.B.C` como `FALLIDA`; si solo falla la sincronización de un arnés, queda activa la `A.B.C` con ese destino `DESFASADO` y el aviso añade `Arneses sin sincronizar: <arnés>: <causa>.`.
- [x] **CA-M-5 (`@CA-F03-12`, `@CA-F03-13`, `@CA-F03-14`, `@RF-F03-10`, `@RF-F03-11`, `@RF-F03-12`):** `adevv actualizar` fuerza la comprobación, olvida la versión fallida, reactiva la actualización automática si estaba desactivada e instala la mayor publicada; `adevv actualizar X.Y.Z` valida `X.Y.Z` en el origen (si no existe, muestra `X.Y.Z no es una versión publicada. Publicadas: <las 5 mayores>.`), rechaza instalar si hay bucles en marcha (`No se puede instalar X.Y.Z con bucles en marcha: <lista>.`), instala `X.Y.Z` cuando procede y, si es menor que la última publicada, desactiva la actualización automática informando `Actualización automática desactivada; \`adevv actualizar\` la reactiva.`.

## 📋 Triaje de Alcance (/task-dev)
- [x] **Subfase A: Definición** → `[EXEC]` (trasladar escenarios BDD de F-03 a `tests/features/actualizacion_automatica.feature`)
- [x] **Subfase B: Diseño** → `[EXEC]` (diseño técnico en `docs/design/T-ADV-0004-design.md`)
- [x] **Subfase C: Desarrollo** → `[EXEC]` (implementación de `adevv/updater.py`, integración en `adevv/processes.py`, `adevv/cli.py` y tests unitarios/integración)
- [x] **Subfase D: QA** → `[EXEC]` (revisión de pruebas y código con Hades `/review-test` y `/review-code`)
- [x] **Subfase E: Documentación** → `[EXEC]` (actualización minimalista y registro en revisión de versión)
- [x] **Subfase F: Cierre** → `[EXEC]` (commit y cierre de tarea)

**Verificación al cierre:**
`python skills/orquestar/orquestar.py --verificar "python -m unittest tests/test_updater.py tests/test_processes.py"`
(Ejercita la tabla de 9 resultados, ventana temporal E1–E13, detección y no rotura de procesos bucle y gateway, descarga/instalación lado a lado y órdenes `adevv actualizar`).
