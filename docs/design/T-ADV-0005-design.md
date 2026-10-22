# Diseño Técnico: T-ADV-0005 · Migración de proyectos con submódulo

## 1. Resumen y Contexto
El objetivo de **T-ADV-0005** es proporcionar una herramienta de diagnóstico de solo lectura (`adevv migrar`) junto con la documentación completa de migración en `README.md` y `branch_strategy.md §8`. Esto permite migrar proyectos consumidores y el propio repositorio de desarrollo de Adevv desde el modelo de submódulo `.agents/`, enlaces simbólicos, junctions y copias locales hacia el uso desacoplado del CLI `adevv` sin alterar ningún archivo ni correr riesgos de pérdida de datos por eliminación recursiva de junctions.

## 2. Decisiones de Arquitectura y Diseño
- **DEC-D01 (Diagnóstico estricto de solo lectura):** `adevv migrar` no altera el sistema de archivos ni ejecuta comandos de modificación (`DEC-04`, `RF-F04-01`). La orden se limita a inspeccionar el estado del proyecto y reportar los pendientes restantes para que el desarrollador ejecute los pasos documentados de forma segura e informada.
- **DEC-D02 (Inspección no recursiva de enlaces y submódulos):** Para evitar recorrer árboles externos o el contenido congelado, el escáner no entra dentro de directorios que sean enlaces simbólicos o junctions de Windows (`RF-F04-02`), ni recorre el interior de `.agents/` ni copias completas de Adevv detectadas.
- **DEC-D03 (Detección y clasificación precisa de pendientes):**
  - Entrada `.agents` en `.gitmodules`.
  - Carpeta, enlace o junction `.agents` en la raíz (formato `.agents → <destino> (<tipo>)`).
  - Directorio `.git/modules/.agents`.
  - Enlaces en `.claude/`, `.codex/` y `.agent/` apuntando a `.agents` (formato `<ruta> → <destino> (<tipo>)`).
  - Claves `instructions` en `orchestration.json` que citen `.agents/`.
  - Elementos locales que ocultan los distribuidos según `RF-F02-07`.
  - Copias de Adevv en el proyecto (directorios distintos de la raíz que contengan `skills/orquestar/SKILL.md`).
  - Líneas en archivos en uso que contengan referencias relativas a `.agents/`.
  Cada pendiente cuenta exactamente una sola vez (`RF-F04-01`).
- **DEC-D04 (Distinción entre archivos en uso y citas históricas):**
  - Son archivos en uso: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `orchestration.json`, `task_config.yaml` en la raíz, y archivos de texto bajo `scripts/`, `.claude/`, `.codex/`, `.agent/`, `.github/` (`RF-F04-03`).
  - En el repositorio fuente de Adevv, `README.md` documenta la migración y se excluye de pendientes y de citas históricas (`RF-F04-03`, `CA-F04-04`). En proyectos consumidores, `README.md` es archivo en uso.
  - Citas en cualquier otro archivo (`docs/**`, `tests/**`, evidencias) se contabilizan exclusivamente como citas históricas (`Sin pendientes (N citas históricas).`).
- **DEC-D05 (Formateo agrupado y acotado a 20 elementos):** Los pendientes se listan agrupados por archivo, mostrando hasta 20 pendientes. Si hay más de 20, se emite `… y M más (total T).` y concluye con `T pendientes.` o `Sin pendientes (N citas históricas).` o `Sin pendientes` (`RF-F04-01`, `CA-F04-05`).
- **DEC-D06 (Documentación y salvaguardas de eliminación en Windows):** `README.md` documenta la secuencia obligatoria de 10 pasos para proyectos consumidores y los pasos específicos para Adevv fuente. Advierte explícitamente contra `Remove-Item -Recurse` y `rm -rf` en junctions/enlaces, indicando la orden nativa segura `cmd /c rmdir <ruta>`. `branch_strategy.md §8` se sustituye por un enlace a esta sección del `README.md` (`RF-F04-06`).

## 3. Modificaciones y Componentes

### 3.1. `[NEW] adevv/migrate.py`
- Función `diagnosticar_migracion(root: Path) -> ResultadoDiagnostico` con toda la lógica de detección de pendientes, clasificación de enlaces/junctions y recuento de citas históricas.
- Detección de enlaces (`info_enlace`) con descarte del prefijo de dispositivo Windows `\\?\`.
- Formateo de salida `imprimir_diagnostico` con límite de 20 pendientes, agrupación por archivo y mensajes finales estandarizados.
- Función `ejecutar_migrar(root: Path, out: TextIO, err: TextIO) -> int`.

### 3.2. `[MODIFY] adevv/cli.py`
- Registrar subcomando `migrar` en el parser de `adevv`.
- Despachar `adevv migrar` llamando a `adevv.migrate.ejecutar_migrar`.

### 3.3. `[NEW] tests/test_migrate.py`
- Pruebas unitarias para todos los criterios de aceptación:
  - `test_diagnostico_submodulo_y_adaptadores` (`CA-F04-01`).
  - `test_deteccion_adaptadores_enlaces_y_copias_sin_recorrer` (`CA-F04-02`).
  - `test_proyecto_migrado_con_citas_historicas` (`CA-F04-03`).
  - `test_migracion_repositorio_fuente_adevv_junction` (`CA-F04-04`).
  - `test_salida_acotada_20_pendientes` (`CA-F04-05`).

### 3.4. `[MODIFY] README.md`
- Actualizar sección de integración para proyectos consumidores reemplazando la creación de submódulos y symlinks por el uso de `adevv instalar` y el nuevo playbook de migración en 10 pasos con advertencias de junctions y migración del repositorio de desarrollo.

### 3.5. `[MODIFY] branch_strategy.md`
- Reemplazar el contenido de la sección 8 (`Gestión de Submódulos`) por un enlace canónico a la guía de migración del `README.md`.

## 4. Análisis de Principios
- **SOLID / Single Responsibility:** El módulo `adevv.migrate` encapsula exclusivamente la regla de negocio de auditoría de migración.
- **KISS / DRY:** Reutilización de `es_repositorio_fuente_adevv` y de la lista de elementos locales de `RF-F02-07`.
- **Seguridad:** Cero mutaciones de disco en `adevv migrar`; protección contra borrado accidental de directorios de destino en documentación.

## 5. Criterios de Aceptación Verificados
- `CA-M-1`, `CA-M-2` y `CA-M-3` cubiertos exhaustivamente mediante pruebas automáticas y actualización documental.
