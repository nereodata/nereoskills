# Diseño Técnico: T-ADV-0002 - Instalación y sincronización con los arneses

## 🏗️ Arquitectura
- **Componentes creados/modificados:**
  - `adevv/store.py`: Gestión del almacén de usuario `$ADEVV_HOME` (`~/.adevv/`), persistencia JSON atómica (`tempfile` + `os.replace`), puntero activo `active.json`, configuración `config.json`, estado de actualización `update_state.json`, registros de sincronización `sync/<destino>.json` y directorios de versiones `versions/<id>/`.
  - `adevv/processes.py`: Detección no invasiva de procesos vivos de Adevv (`bucle`, `gateway`, `otro`) y carpetas de trabajo asociadas sin dependencias externas pesadas (`Win32_Process` en Windows, `ps`/`/proc` en POSIX).
  - `adevv/sync.py`: Mapa `DESTINOS` confirmado para `claude`, `codex` y `agy`, resolución de rutas absolutas para adaptadores (`agents/codex/*.toml`) y workflows (`workflows/*.md`), motor de sincronización idempotente con registro de huellas SHA-256, adopción sin registro, detección de conflictos (alien / editado a mano), soporte `--forzar`, borrado seguro no recursivo y protección estricta contra entradas ocultas (`.`), rutas ajenas y directory traversal.
  - `adevv/cli.py`: Entrada de línea de comandos `adevv`, gestión de órdenes `adevv instalar [--forzar]`, `adevv --version`, resincronización transparente de destinos `DESFASADO` al arrancar sin bucles en marcha, y avisos de 24 h por `stderr`.
  - `README.md`: Documentación de la orden única de primera instalación (`pip install --user git+https://... && adevv instalar`).
  - `tests/test_sync.py`: Suite de pruebas unitarias y de integración para toda la lógica de sincronización, registros, huellas, conflictos, traversal, adopción y borrado no recursivo.
  - `tests/test_install_and_release.py`: Pruebas de integración de primera instalación (`CA-F01-01`), destinos y CLI.

## 🛠️ Cambios
- **[NEW]** `adevv/store.py`: Funciones de acceso y persistencia atómica para `$ADEVV_HOME`.
- **[NEW]** `adevv/processes.py`: Detección y clasificación de procesos vivos de Adevv.
- **[NEW]** `adevv/sync.py`: Mapa de destinos, resolución de rutas y motor de sincronización de arneses.
- **[NEW]** `adevv/cli.py`: Punto de entrada CLI con `instalar` y `--version`.
- **[NEW]** `tests/test_sync.py`: Pruebas exhaustivas de sincronización y arneses.
- **[MODIFY]** `tests/test_install_and_release.py`: Añadir pruebas de integración de instalación y verificación CLI.
- **[MODIFY]** `README.md`: Añadir sección de instalación única con `adevv instalar`.

## 🎯 Mapa de impacto
- **Llamantes:**
  - Usuarios y arneses invocando el comando `adevv` en consola.
  - Subórdenes `adevv instalar` y `adevv --version`.
  - Futuras tareas: `T-ADV-0003` (CLI completo y orquestación sin rutas) y `T-ADV-0004` (autoactualizador con tabla de 9 resultados).
- **Escenarios/tests afectados:**
  - Cobertura completa de los 13 escenarios `@CA-F01-01` a `@CA-F01-13` de `tests/features/instalacion_y_sincronizacion.feature`.
  - Pruebas existentes en `tests/test_package_and_instructions.py` y `tests/test_install_and_release.py` se mantienen en verde.
- **Decisiones arquitectónicas observadas:**
  - `DEC-P01`: Almacén de versiones lado a lado en `~/.adevv/versions/<id>/` y conmutación atómica de `active.json`.
  - `DEC-P03`: Exclusivamente librería estándar de Python ≥ 3.11 sin dependencias de terceros.
  - `DEC-P04`: Carpetas globales confirmadas para Claude (`~/.claude`), Codex (`~/.codex`) y Antigravity (`~/.gemini/config`). Destinos con carpetas vacías reportan `NO_DETECTADO` / «sin confirmar».
  - `DEC-P05`: Mantener nombres de carpeta originales de cada skill en el destino (`skills/<nombre>/`).
  - `DEC-P07`: Detección de procesos del SO sin `psutil`, filtrando bucles frente a gateways y otros.

## 🧩 Patrones y Algoritmos

### 1. Escritura Atómica en Almacén (`adevv/store.py`)
- Toda escritura de JSON (`active.json`, `config.json`, `update_state.json`, `sync/<destino>.json`) se realiza creando un archivo temporal (`tempfile.NamedTemporaryFile`) en el mismo directorio padre y cerrándolo antes de invocar `os.replace`.
- Se asegura la creación de directorios padre (`~/.adevv/sync`, `~/.adevv/versions`).
- Lectura tolerante: si un archivo de estado no existe o está corrupto, se retorna valor por defecto seguro sin propagar excepciones no controladas.

### 2. Destinos Confirmados y Contenido
- `claude`:
  - `skills/`: todas las carpetas en `skills/` (excluyendo subcarpetas `scripts/`, `__pycache__/` y archivos `*.py`, `*.pyc`).
  - `agents/`: `agents/<rol>.md`.
- `codex`:
  - `skills/`: todas las carpetas en `skills/` (sin código).
  - `agents/`: `agents/codex/*.toml`, reescribiendo rutas relativas a agentes y skills por rutas absolutas a la versión activa instalada.
- `agy`:
  - `skills/`: todas las carpetas en `skills/` (sin código).
  - `workflows/`: `workflows/*.md`, reescribiendo referencias a `SKILL.md` o skills por rutas absolutas a la versión activa instalada.

### 3. Resolución de Rutas Absolutas (`adevv/sync.py`)
- Se localiza la raíz de la versión instalada (`get_active_version_dir()`).
- En `agents/codex/*.toml`:
  - `.agents/agents/<rol>.md` -> `{installed_root}/agents/<rol>.md`
  - `.agents/skills/<nombre>/SKILL.md` -> `{installed_root}/skills/<nombre>/SKILL.md`
- En `workflows/*.md`:
  - `../skills/<nombre>/SKILL.md` o `.agents/skills/<nombre>/SKILL.md` -> `{installed_root}/skills/<nombre>/SKILL.md`
- Se normalizan las barras a `/` para consistencia y portabilidad en archivos de configuración.

### 4. Ciclo de Sincronización y Registro SHA-256
1. Comprobar existencia de carpeta base y carpetas confirmadas:
   - Si no existe carpeta base -> `NO_DETECTADO` (`<Arnés>: no detectado`).
   - Si existe base pero `carpetas == {}` -> `NO_DETECTADO` (`<Arnés>: sin confirmar`).
   - Si destino está en `config["disabled_targets"]` -> `DESACTIVADO` (`<Arnés>: desactivado`).
2. Lectura de registro `sync/<destino>.json`:
   - Si no existe o está corrupto: no se borra ningún archivo; se adoptan archivos existentes en disco cuya huella coincida con el contenido fuente (`RF-F01-09`).
3. Detección de Conflictos:
   - Archivo existente en disco que no figura en el registro -> Conflicto (alien). No se toca nunca, ni con `--forzar`.
   - Archivo existente en el registro pero editado a mano (`hash_disco != hash_registro`):
     - Si `--forzar` está activo: se sobrescribe y actualiza huella.
     - Si `--forzar` no está activo: Conflicto (editado). No se toca.
4. Borrado de archivos obsoletos (`RF-F01-07`):
   - Archivo en registro que ya no existe en el contenido nuevo:
     - Si su huella en disco coincide con la huella registrada: se borra el archivo.
     - Si la carpeta queda vacía, se borra (sin recursión destructiva).
     - Si su huella fue editada a mano, no se borra.
5. Guardas de Seguridad (`RF-F01-05`, `CA-F01-06`, `CA-F01-07`):
   - Nunca tocar archivos ni carpetas que empiecen por `.` (ej. `.system`, `.git`).
   - Nunca seguir enlaces simbólicos ni reparse points NTFS (`os.lstat` / `0x0400`).
   - Ignorar e informar rutas en el registro que resuelvan fuera del directorio destino.
6. Guardado de Registro:
   - Si no hay conflictos: estado `SINCRONIZADO`, se guarda registro con la versión instalada y huellas.
   - Si hay conflictos: estado `INCOMPLETO`, se guardan las huellas de los archivos escritos/adoptados y se reportan los conflictos.

### 5. Resincronización al Arrancar (`adevv/cli.py`)
- Al invocar cualquier orden `adevv`:
  - Si no estamos dentro de un paso de bucle (`ORQUESTAR_PASO` no definido):
    - Comprobar si algún destino está `DESFASADO`.
    - Si hay destinos desfasados:
      - Si hay bucles en marcha (`processes.hay_bucles_en_marcha()`): no tocar el destino; si pasaron ≥ 24 h desde el último aviso, emitir aviso por `stderr`.
      - Si no hay bucles en marcha: resincronizar el destino y emitir `<Arnés> sincronizado con la X.Y.Z.`.

## 🧪 Testeabilidad
- `tests/test_sync.py`:
  - Pruebas unitarias de `store.py` (escritura atómica, corrupción, concurrencia simulada).
  - Pruebas de resolución de rutas en adaptadores Codex y workflows Antigravity (`CA-F01-03`).
  - Pruebas de conflicto alien (`CA-F01-04`), conflicto editado a mano y `--forzar` (`CA-F01-05`).
  - Pruebas de respeto a carpetas ajenas y ocultas (`CA-F01-06`).
  - Pruebas de traversal y escape de destino (`CA-F01-07`).
  - Pruebas de borrado no recursivo de skills retiradas (`CA-F01-08`).
  - Pruebas de adopción sin registro o registro corrupto (`CA-F01-09`).
  - Pruebas de estados de destino (`NO_DETECTADO`, `DESACTIVADO`, `DESFASADO`, `INCOMPLETO`, `SINCRONIZADO`).
- `tests/test_install_and_release.py`:
  - Prueba de primera instalación y actualización en cadena (`CA-F01-01`).
  - Prueba de `adevv --version` con desglose exacto (`CA-F01-12`).
  - Prueba de sincronización repetida "sin cambios" (`CA-F01-13`).
  - Prueba de resincronización bloqueada por bucle vivo (`CA-F01-11`) y desbloqueada sin bucles (`CA-F01-10`).
