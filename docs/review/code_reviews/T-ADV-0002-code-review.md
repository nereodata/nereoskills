# Revisión de Código (`review-code`): T-ADV-0002

- **Tarea**: T-ADV-0002 — Instalación y sincronización con los arneses
- **Diseño de referencia**: `docs/design/T-ADV-0002-design.md`
- **Plan de plataforma**: `docs/requirements/platform_plan.md` (`DEC-P01`, `DEC-P03`, `DEC-P04`, `DEC-P05`, `DEC-P07`)
- **Archivos auditados**:
  - `adevv/store.py`
  - `adevv/sync.py`
  - `adevv/processes.py`
  - `adevv/cli.py`
  - `README.md`
  - `docs/plan/tasks/T-ADV-0002-instalacion-y-sincronizacion-arneses.md`
- **Veredicto**: **APROBADO**

## Análisis Estático y Evidencias

- **`git diff --check`**: Limpio, sin errores de formato ni espacios en blanco.
- **`py_compile`**: Limpio sobre todos los módulos Python del delta (`adevv/store.py`, `adevv/sync.py`, `adevv/processes.py`, `adevv/cli.py`).
- **Auditoría de dependencias**: Uso exclusivo de la librería estándar de Python ≥ 3.11, cumpliendo estrictamente `DEC-P03` y `DEC-P07`.
- **Evidencia de pruebas (`orquestar_evidencias.jsonl`)**: Verificación en verde registrada mediante `orquestar.py --verificar` (`python -m unittest tests/test_sync.py tests/test_install_and_release.py`, código `0`).

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Corrección** | 9.0 / 10 | Sincronización idempotente con registro SHA-256, adopción sin registro, gestión de conflictos (alien vs. editado a mano con `--forzar`), borrado no recursivo de obsoletos y precedencia de estados conformes con `F-01`. |
| **Seguridad** | 9.5 / 10 | Validación estricta contra directory traversal (`ruta_segura_dentro_de`), exclusión de entradas ocultas (`.`), detección de symlinks y reparse points NTFS (`os.lstat` y `0x0400`) sin seguir enlaces, y ejecución de subprocesos sin `shell=True`. |
| **Conformidad** | 9.5 / 10 | Fiel a `docs/design/T-ADV-0002-design.md` y a las decisiones `DEC-P01`, `DEC-P03`, `DEC-P04`, `DEC-P05` y `DEC-P07`, respetando la separación entre planificación pura (`planificar_sincronizacion`) y escritura en disco (`sincronizar_destinos`) así como las reglas de capas. |
| **Calidad** | 9.0 / 10 | Código modular, tipado, legible y bien estructurado, con responsabilidades claras entre `store.py`, `processes.py`, `sync.py` y `cli.py`. |
| **Eficiencia** | 9.5 / 10 | Operaciones en memoria y escrituras atómicas acotadas a los archivos modificados; enumeración de procesos con `timeout=10`. |
| **Documentación** | 9.5 / 10 | Docstrings claros en módulos y funciones públicas; `README.md` actualizado con la orden única de primera instalación (`RF-F01-01`). |
| **Media** | **9.33 / 10** | **APROBADO** (media > 8, sin hallazgos 🔴 ni 🟠) |

---

## Hallazgos

### 🔵 BAJA

- **H-01 [BAJA]** (`adevv/cli.py`, líneas 111-125) — `destino: descartar`
  - **Descripción**: En `_resincronizar_desfasados_al_arrancar`, cuando no hay bucles vivos, se invoca `sincronizar_destinos()` dentro del bucle `for target_key in DESTINOS.keys():`. Dado que `sincronizar_destinos()` actualiza todos los destinos detectados en una sola pasada, si hubiera más de un destino `DESFASADO` simultáneamente, el segundo ya aparecería como `SINCRONIZADO` en su iteración del bucle y no imprimiría su línea `<Arnés> sincronizado con la X.Y.Z.`. Impacto cosmético en un caso extremo multiproveedor.

- **H-02 [BAJA]** (`adevv/cli.py`, líneas 118-121) — `destino: descartar`
  - **Descripción**: El aviso por `stderr` cuando hay un destino `DESFASADO` y bucles en marcha se emite en cada invocación sin persistir aún la marca temporal de 24 h en `update_state.json`. La gestión completa de ventanas de tiempo en `update_state.json` corresponde a `T-ADV-0004` (`F-03`).
