# Diseño Técnico: T-ADV-0003 · Adevv desde cualquier proyecto sin rutas

## 1. Resumen y Contexto
El objetivo de **T-ADV-0003** es permitir que el bucle de `/orquestar`, las revisiones de Hades, la verificación, el gateway de Telegram y las herramientas de `/release` se invoquen desde cualquier proyecto mediante la orden unificada `adevv` sin depender del submódulo `.agents/`. Asimismo, asegura la inicialización automática de proyectos nuevos y la ejecución aislada y protegida del bucle sobre el propio repositorio de desarrollo de Adevv.

## 2. Decisiones de Arquitectura y Diseño
- **DEC-D01 (Despacho transparente en CLI `adevv`):** El CLI `adevv` (`adevv/cli.py`) añade soporte para los subcomandos `orquestar`, `telegram` y `release`. El despacho a los scripts subyacentes (`orquestar.py`, `gateway.py`, scripts de release) se realiza localizando la versión activa instalada (`get_active_version_dir()`) o el propio paquete, preservando argumentos, códigos de salida y streams `stdout`/`stderr`. Con `adevv orquestar --fondo`, el proceso desacoplado recibe exactamente los argumentos de usuario sin alterar los argumentos del script subyacente.
- **DEC-D02 (Fallback YAML stdlib en el motor):** En `skills/orquestar/orquestar.py`, todas las lecturas de manifiestos YAML (`task_config.yaml`) intentan importar `yaml` (`PyYAML`) y en caso de `ImportError` utilizan `adevv.yaml_lite.load_yaml`, garantizando cero dependencias externas obligatorias según `DEC-P03`.
- **DEC-D03 (Prompts desacoplados con rutas absolutas):** Los prompts construidos por `orquestar.py` tanto en el bucle principal como en `--agente` citan siempre las rutas absolutas entrecomilladas a las skills y agentes en la versión instalada (`get_active_version_dir()`). Las instrucciones citan órdenes `adevv orquestar --verificar` y `adevv orquestar --agente hades` sin mencionar `orquestar.py`.
- **DEC-D04 (Aislamiento en repositorio fuente de Adevv):** Al detectar que el proyecto actual es el repositorio de desarrollo de Adevv (`es_repositorio_fuente_adevv(root)`), el prompt del bucle aclara que las herramientas corresponden a la versión instalada y que los cambios deben realizarse en `skills/`, `agents/` y `workflows/` del árbol de trabajo (`RF-F02-09`).
- **DEC-D05 (Validaciones previas al lanzar el bucle):** Antes de iniciar cualquier arnés, `orquestar.py` valida:
  1. Que `<rol>.instructions` definido en `orchestration.json` exista en disco (`RF-F02-06`).
  2. Que el proyecto no contenga el submódulo `.agents` ni su entrada en `.gitmodules` (`RF-F02-07`).
  3. Que no existan elementos locales en `.claude/`, `.codex/`, `.agents/` o `.agent/` que oculten elementos distribuidos de Adevv (`RF-F02-07`).
  Estas validaciones se omiten en órdenes informativas como `--estado`.
- **DEC-D06 (Inicialización automática de proyectos nuevos):** Si se lanza el bucle en una carpeta con `docs/requirements/requirements.md` fuera de cualquier repositorio git (y no es raíz de unidad ni home del usuario), se inicializa git (`git init`), se genera un `task_config.yaml` mínimo con prefijo de 3 letras normalizado (`unicodedata`) y `.gitignore`, y se realiza un commit inicial informando en una línea (`RF-F02-08`). Si se ejecuta en una subcarpeta de otro repositorio git, aborta indicando la raíz.
- **DEC-D07 (Saneamiento integral de instrucciones distribuibles):** Ningún archivo de instrucciones distribuible (`skills/**` salvo `.py`, `agents/**`, `workflows/**`, `skills/release/templates/RELEASING.md`) debe contener `.agents/`, invocaciones `python .../*.py`, `skills/<nombre>/scripts` ni rutas relativas `../`. Se sustituyen por órdenes `adevv ...` o nombres canónicos `/nombre` (`RF-F02-05`).

## 3. Modificaciones y Componentes

### 3.1. `[MODIFY] adevv/cli.py`
- Añadir despacho de subcomandos `orquestar`, `telegram` y `release`.
- Subcomando `release` admite `manifiestos`, `completitud` y `changelog` pasando argumentos al script correspondiente en `skills/release/scripts/`.
- Conectar con `get_active_version_dir()` para resolver las rutas a los scripts ejecutables.

### 3.2. `[MODIFY] skills/orquestar/orquestar.py`
- Reemplazar importación directa de `yaml` por fallback a `adevv.yaml_lite`.
- Implementar validaciones previas de lanzamiento:
  - `validar_instrucciones_roles(root, cfg)`
  - `validar_ausencia_submodulo(root)`
  - `validar_no_ocultamiento_local(root, version_dir)`
  - `comprobar_e_inicializar_proyecto_nuevo(root)`
- Ajustar construcción de prompts en `ejecutar()` y `agente()`:
  - Rutas absolutas entrecomilladas a la versión activa instalada.
  - Órdenes `adevv orquestar --verificar` y `adevv orquestar --agente hades`.
  - Nota de trabajo en árbol si es repositorio fuente de Adevv.

### 3.3. `[MODIFY]` Contenido distribuible (Saneamiento de instrucciones)
- `skills/orquestar/SKILL.md`: corregir `.agents/agents/<rol>.md` a `agents/<rol>.md`.
- `skills/release/SKILL.md`: cambiar referencia a `skills/release/scripts/` por `adevv release ...`.
- `skills/release/templates/RELEASING.md`: cambiar `python .agents/skills/release/scripts/...` por `adevv release ...` y eliminar `.agents/`.
- `skills/seo-audit/SKILL.md`: eliminar `.agents/`.
- `skills/task-add/SKILL.md`: eliminar `../../../docs/plan/tasks/`.
- `agents/codex/*.toml`: eliminar `.agents/` en `developer_instructions`.
- `workflows/*.md`: reemplazar referencias relativas `../skills/<n>/SKILL.md` por `skills/<n>/SKILL.md` o `/n`.

### 3.4. `[NEW] tests/test_cli_commands.py`
- Pruebas unitarias y de integración para `adevv orquestar`, `adevv telegram` y `adevv release`.
- Pruebas de `--fondo` preservando argumentos y PID.
- Pruebas de inicialización automática de proyectos nuevos (`Mi app` -> `MIA`, `Q1` -> `PRJ`, `Ñandú` -> `NAN`), subcarpetas de repositorios ajenos y carpetas prohibidas (home / raíz de unidad).
- Pruebas de validaciones previas (submódulo `.agents`, elementos locales que ocultan, `instructions` inexistentes).

### 3.5. `[NEW] tests/test_instructions_cleanliness.py`
- Auditoría exhaustiva automatizada sobre todo el contenido distribuible verificando la ausencia total de `.agents/`, `python .../*.py`, `skills/<n>/scripts` y `../`.

## 4. Análisis de Principios
- **SOLID / Single Responsibility:** El CLI delega la ejecución de dominios a sus respectivos scripts y módulos especializados; las validaciones previas están modularizadas en funciones puras y verificables.
- **KISS / YAGNI:** Reutilización de scripts existentes sin reescribir la lógica de orquestación ni de release.
- **Delta-First:** Modificación quirúrgica de los puntos de integración sin alterar contratos existentes.

## 5. Criterios de Aceptación Verificados
- `CA-M-1` a `CA-M-5` cubiertos al 100% con pruebas automatizadas en `tests/test_cli_commands.py`, `tests/test_instructions_cleanliness.py` y `tests/test_orquestar.py`.
