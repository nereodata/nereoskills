---
id: T-ADV-0002
title: "Instalación y sincronización con los arneses"
type: funcional
weight: 120
version: "v0.1.0"
status: completed
depende_de: [T-ADV-0001]
origen: "F-01 (docs/requirements/funcionalidades/F-01_instalacion_y_sincronizacion.md)"
created_at: 2026-10-22
updated_at: 2026-10-22
---

# T-ADV-0002: Instalación y sincronización con los arneses

## 🎯 Objetivo de Negocio
Permitir instalar Adevv una sola vez por máquina y sincronizar sus skills (sin código), agentes, adaptadores y workflows en las carpetas globales confirmadas de Claude Code, Codex y Antigravity mediante `adevv instalar`, protegiendo archivos ajenos o editados a mano mediante un registro de huellas SHA-256 y mostrando el estado completo con `adevv --version`.

### Hueco real (Delta sobre el código actual)
- **Ya existe:** El contenido fuente en `skills/`, `agents/` (incluidos `agents/codex/*.toml`) y `workflows/*.md`, más el empaquetado base de `T-ADV-0001`.
- **Falta implementar:** `adevv/store.py` (almacén `~/.adevv/` / `$ADEVV_HOME` con escritura atómica `tempfile` + `os.replace` para `active.json`, `config.json`, `update_state.json` y `sync/<destino>.json`), `adevv/sync.py` (mapa `DESTINOS` confirmado para `claude`, `codex` y `agy`, resolución de rutas absolutas instaladas, cálculo de estados `NO_DETECTADO` / `DESACTIVADO` / `DESFASADO` / `INCOMPLETO` / `SINCRONIZADO`, adopción sin registro, gestión de conflictos y `--forzar`, limpieza no recursiva y resincronización de destinos `DESFASADO`), órdenes `adevv instalar [--forzar]` y `adevv --version` en `adevv/cli.py`, y documentación de la orden única de primera instalación en `README.md`.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (`@CA-F01-01`, `@CA-F01-13`, `@RF-F01-01`, `@RF-F01-03`):** El `README.md` documenta una sola orden de instalación desde versión publicada fija en el origen seguido de `adevv instalar`; `adevv instalar` ejecuta la comprobación de actualización sin la fila `ESPERA` (cuando la actualización automática está activa y sin bucles) y sincroniza las carpetas confirmadas de cada destino detectado informando qué escribió por arnés (o `sin cambios` si se ejecuta dos veces seguidas).
- [x] **CA-M-2 (`@CA-F01-02`, `@RF-F01-03`):** Si no existe la carpeta base de un arnés o la versión instalada no declara carpetas confirmadas para él, el destino queda en `NO_DETECTADO`, no se crea ninguna carpeta y `adevv --version` muestra `<Arnés>: no detectado` o `<Arnés>: sin confirmar`.
- [x] **CA-M-3 (`@CA-F01-03`, `@RF-F01-04`):** Al sincronizar los destinos, las rutas de adaptadores (`agents/codex/*.toml`) y workflows (`workflows/*.md`) se resuelven a rutas absolutas de la versión instalada, de modo que ningún archivo registrado en los destinos contiene rutas relativas que empiecen por `.agents/` ni `../`.
- [x] **CA-M-4 (`@CA-F01-04`, `@CA-F01-05`, `@CA-F01-09`, `@RF-F01-05`, `@RF-F01-06`, `@RF-F01-09`, `@RF-F01-13`):** El sincronizador guarda atómicamente la huella SHA-256 de cada archivo escrito; si el registro no existe o es ilegible adopta las copias idénticas sin borrar nada; si un archivo existe fuera del registro o su huella fue editada a mano no lo toca, marca el destino `INCOMPLETO` y lista los conflictos (máx. 20 líneas más total); con `adevv instalar --forzar` sobrescribe solo los archivos del registro editados a mano (nunca los ajenos); y al lanzar un bucle cuando un destino usado por el proyecto está `INCOMPLETO` o `DESFASADO` emite el aviso en una línea por `stderr` y continúa.
- [x] **CA-M-5 (`@CA-F01-06`, `@CA-F01-07`, `@CA-F01-08`, `@RF-F01-05`, `@RF-F01-07`):** El sincronizador nunca toca carpetas ajenas ni entradas ocultas (`.` como `.system`), nunca sigue enlaces, ignora e informa cualquier ruta del registro que resuelva fuera del destino, y al retirar una skill en una versión nueva borra solo los archivos registrados cuya huella coincida, conservando las carpetas que aún contengan archivos del usuario.
- [x] **CA-M-6 (`@CA-F01-10`, `@CA-F01-11`, `@CA-F01-12`, `@RF-F01-11`, `@RF-F01-12`):** Cualquier orden `adevv` fuera de un paso de bucle resincroniza antes de su acción los destinos `DESFASADO` si no hay bucles en marcha (mostrando `<Arnés> sincronizado con la X.Y.Z.`), o los deja sin tocar si hay bucles en marcha avisando como mucho una vez cada 24 h (`<Arnés> sigue con la A.B.C; se sincronizará cuando no haya bucles en marcha: <lista>.`); y `adevv --version` muestra versión instalada y origen, estado de cada destino, si la actualización automática está activa, última comprobación y último resultado `APLICADA`/`FALLIDA` con fecha.

## 📋 Triaje de Alcance (/task-dev)
- [x] **Subfase A: Definición** → `[EXEC]` (trasladar escenarios BDD de F-01 a `tests/features/instalacion_y_sincronizacion.feature`)
- [x] **Subfase B: Diseño** → `[EXEC]` (diseño técnico de almacén, sincronización y CLI en `docs/design/T-ADV-0002-design.md`)
- [x] **Subfase C: Desarrollo** → `[EXEC]` (implementación de `adevv/store.py`, `adevv/sync.py`, `adevv/cli.py` y pruebas unitarias/integración)
- [x] **Subfase D: QA** → `[EXEC]` (revisión de código con Hades `/review-code`)
- [x] **Subfase E: Documentación** → `[EXEC]` (orden única de instalación en `README.md`)
- [x] **Subfase F: Cierre** → `[EXEC]` (commit y cierre de tarea)

**Verificación al cierre:**
`python skills/orquestar/orquestar.py --verificar "python -m unittest tests/test_sync.py tests/test_install_and_release.py"`
(Ejercita el almacén atómico, la sincronización de destinos con registros SHA-256, resolución de rutas y comandos CLI).
