# Diseño Técnico: T-ADV-0004 · Actualización automática de versiones publicadas

## 1. Resumen y Contexto
El objetivo de **T-ADV-0004** es implementar el ciclo de actualización automática de Adevv según los requisitos de `F-03` y `requirements.md §4`.
Cualquier orden `adevv` evalúa la actualización antes de su acción, asegurando:
- Cero demoras perceptibles o cuelgues (timeout de red ≤ 5 s sin credenciales interactivas).
- Inmunidad total para bucles en marcha (se aplazan indicando los bucles vivos).
- Compatibilidad lado a lado en Windows (los gateways u otros procesos siguen ejecutando su versión sin verse afectados).
- Conmutación atómica de versión activa y resincronización de arneses.
- Órdenes manuales `adevv actualizar` y `adevv actualizar X.Y.Z` (con desactivación/reactivación y vuelta atrás).

## 2. Decisiones de Arquitectura y Diseño
- **DEC-D01 (Módulo desacoplado `adevv/updater.py`):** Encapsula la lógica de la tabla de 9 resultados, la evaluación de la ventana temporal (`E1`–`E13`), la consulta a Git (`ls-remote`), la descarga por lista blanca a `~/.adevv/versions/<V>/` y la gestión del estado en `update_state.json`.
- **DEC-D02 (Filtrado estricto de etiquetas anotadas `refs/tags/vX.Y.Z^{}`):** La consulta mediante `git ls-remote --tags` busca exclusivamente referencias terminadas en `^{}` que encajen con `v\d+\.\d+\.\d+`. Esto descarta de forma natural etiquetas ligeras, ramas y versiones pre-release (`v0.2.0-rc1`), y obtiene directamente el commit exacto para la extracción (`DEC-P06`, `RF-F03-02`).
- **DEC-D03 (Ejecución de red sin prompts de credenciales ni bloqueos):** Todas las consultas e invocaciones a Git establecen variables de entorno `GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`, `GIT_ASKPASS=echo` y timeout de 5 segundos. Cualquier error de red o autenticación se captura como `SIN_RED` con causa clara (`RF-F03-03`).
- **DEC-D04 (Instalación lado a lado y conmutación atómica en Windows):** La nueva versión se extrae en `~/.adevv/versions/<A.B.C>/`. Se valida que la versión declarada en el paquete sea idéntica a `A.B.C`. Tras la validación, se actualiza atómicamente `active.json`, se invocan las rutinas de sincronización de `sync.py` de la versión entrante y se limpian las versiones antiguas no utilizadas por ningún proceso (`DEC-P01`, `DEC-P02`).
- **DEC-D05 (Preservación de procesos `gateway` y no interferencia):** Los procesos `gateway` o de inspección no aplazan la actualización (`RF-F03-08`). Continúan su ejecución contra su carpeta de versión inmutable. El mensaje de actualización completada incluye avisos para reiniciar los gateways vivos con su ruta de trabajo.
- **DEC-D06 (Emisión de avisos exclusivamente por `stderr`):** Todos los avisos de actualización automática se escriben en `sys.stderr` en una sola línea, manteniendo `stdout` inalterado para herramientas y scripts consumidores (`RF-F03-13`).
- **DEC-D07 (Soporte completo de `adevv actualizar [X.Y.Z]`):** 
  - `adevv actualizar`: forzada, olvida versión fallida, reactiva la actualización automática si estaba desactivada e instala la mayor versión publicada.
  - `adevv actualizar X.Y.Z`: valida `X.Y.Z` en el origen remoto; si no existe, muestra las 5 mayores; si hay bucles, rechaza; si es menor que la última publicada, instala y desactiva la actualización automática (`RF-F03-11`, `RF-F03-12`).

## 3. Componentes y Modificaciones

### 3.1. `[NEW] adevv/updater.py`
- Definición de estados y resultados: `DESACTIVADA`, `DENTRO_DE_ORQUESTACION`, `DESARROLLO`, `ESPERA`, `SIN_RED`, `AL_DIA`, `APLAZADA`, `APLICADA`, `FALLIDA`.
- `consultar_versiones_publicadas(origin_url, timeout=5)`: consulta `git ls-remote --tags` filtrando `refs/tags/vX.Y.Z^{}`.
- `evaluar_comprobacion_actualizacion(...)`: implementa la tabla de precedencia y las reglas de ventana temporal `E1`–`E13`.
- `instalar_version(...)`: descarga el commit exacto, valida la versión del paquete, conmuta `active.json`, sincroniza arneses y limpia versiones obsoletas no activas y sin procesos en uso.
- `limpiar_versiones_antiguas()`: borra versiones de `~/.adevv/versions/` que no sean la activa ni estén en el `cmdline` de procesos vivos.

### 3.2. `[MODIFY] adevv/processes.py`
- Refinar `_clasificar_linea_comandos` para reconocer con precisión:
  - Bucles antiguos: `orquestar.py` fuera de subcomandos como `--estado`, `--verificar`, etc.
  - Gateways: `gateway.py` o `adevv telegram`.
  - Extracción robusta de carpetas de trabajo de los procesos para la UI (`bucle en <cwd>`, `gateway en <cwd>`).

### 3.3. `[MODIFY] adevv/cli.py`
- Integrar la comprobación automática al inicio de `main_cli` (antes de la acción, emitiendo avisos a `err_stream`).
- Añadir el subcomando `actualizar [target_version]`.
- En caso de actualización aplicada en el arranque, refrescar el contexto activo para que el subcomando inmediato corra sobre la versión recién instalada.

### 3.4. `[NEW] tests/test_updater.py`
- Pruebas exhaustivas de la ventana temporal (`E1` a `E13`), precedencia de resultados y persistencia en `update_state.json`.
- Pruebas de consulta con timeout, ausencia de red y descarte de etiquetas ligeras o pre-releases.
- Pruebas de instalación exitosa, fallo de versión de paquete, sincronización incompleta y reversión a versión anterior.
- Pruebas de `adevv actualizar` y `adevv actualizar X.Y.Z`.

### 3.5. `[NEW] tests/test_processes.py`
- Pruebas de detección y clasificación de procesos (`bucle`, `gateway`, `otro`).
- Verificación de no rotura ni bloqueo de gateways durante la conmutación de versiones.

## 4. Análisis de Principios
- **SOLID:** `updater.py` asume la responsabilidad exclusiva de actualización y versionado remoto; `processes.py` se encarga únicamente de la introspección del sistema operativo; `cli.py` orquesta la invocación.
- **KISS / YAGNI:** Uso de Git estándar mediante llamadas no interactivas con timeout; sin dependencias externas pesadas.
- **Delta-First:** Reutiliza el almacén existente en `store.py` y las rutinas de sincronización en `sync.py`.

## 5. Trazabilidad con Requisitos
- `CA-M-1` (`RF-F03-01`, `RF-F03-04`, `RF-F03-05`) -> Tabla de 9 resultados y casos `E1`–`E13`.
- `CA-M-2` (`RF-F03-02`, `RF-F03-03`) -> `git ls-remote --tags`, sin ventanas, solo `vX.Y.Z^{}`.
- `CA-M-3` (`RF-F03-06`, `RF-F03-08`) -> Clasificación de bucles vs gateways y mensajes UI.
- `CA-M-4` (`RF-F03-07`, `RF-F03-09`, `RF-F03-13`) -> Instalación en `versions/`, conmutación atómica, limpieza y avisos por `stderr`.
- `CA-M-5` (`RF-F03-10`, `RF-F03-11`, `RF-F03-12`) -> Subcomando `adevv actualizar [X.Y.Z]`.
