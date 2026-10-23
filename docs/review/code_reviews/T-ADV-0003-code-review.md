# Revisión de Código (`review-code`): T-ADV-0003

- **Tarea**: T-ADV-0003 — Adevv desde cualquier proyecto sin rutas
- **Diseño de referencia**: `docs/design/T-ADV-0003-design.md`
- **Plan de plataforma**: `docs/requirements/platform_plan.md` (`DEC-P01`, `DEC-P03`, `DEC-P04`, `DEC-P05`, `DEC-P07`)
- **Archivos auditados**:
  - `adevv/cli.py`
  - `skills/orquestar/orquestar.py`
  - `skills/orquestar/SKILL.md`
  - `skills/release/SKILL.md`
  - `skills/seo-audit/SKILL.md`
  - `skills/task-add/SKILL.md`
  - `skills/telegram_gateway/SKILL.md`
  - `skills/release/templates/RELEASING.md`
  - `agents/codex/clio.toml`, `agents/codex/cronos.toml`, `agents/codex/hades.toml`
  - `workflows/*.md`
- **Veredicto**: **APROBADO**

## Análisis Estático y Evidencias

- **`git diff --check`**: Limpio, sin errores de formato ni espacios en blanco.
- **`py_compile`**: Limpio y compilado sin errores sintácticos en todos los módulos modificados (`adevv/cli.py`, `skills/orquestar/orquestar.py`).
- **Auditoría de instrucciones (`tests/test_instructions_cleanliness.py`)**: Limpio; 0 ocurrencias de los patrones prohibidos (`.agents/`, `python .../*.py`, `skills/<nombre>/scripts`, `../`) en el contenido distribuible.
- **Auditoría de dependencias**: Uso exclusivo de la librería estándar de Python ≥ 3.11 con fallback de `PyYAML` a `adevv.yaml_lite`, cumpliendo `DEC-P03`.
- **Evidencia de pruebas (`orquestar_evidencias.jsonl`)**: Verificación en verde registrada mediante `orquestar.py --verificar` (`python -m unittest tests/test_orquestar.py tests/test_cli_commands.py tests/test_instructions_cleanliness.py`, árbol `54742790a9`, código `0`).

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Corrección** | 9.5 / 10 | Despacho transparente de `orquestar`, `telegram` y `release` (`manifiestos`, `completitud`, `changelog`) preservando argumentos, códigos de retorno y `stdout`/`stderr`; fallback YAML a `adevv.yaml_lite`; inicialización automática de proyectos nuevos con prefijo normalizado (`NFD` / `PRJ`); validaciones previas al bucle (`instructions`, submódulo `.agents`, ocultamiento local y subcarpeta Git) y construcción de prompts con rutas absolutas entrecomilladas y aislamiento en el repositorio fuente de Adevv. |
| **Seguridad** | 9.5 / 10 | Invocación de subprocesos mediante listas de argumentos sin `shell=True`, guardas explícitas frente a la inicialización de Git en la carpeta personal del usuario (`es_carpeta_personal`) o en la raíz de una unidad (`es_raiz_de_unidad`), y entrecomillado de rutas absolutas con espacios o caracteres no ASCII. |
| **Conformidad** | 9.5 / 10 | Fiel a `docs/design/T-ADV-0003-design.md` (`DEC-D01` a `DEC-D07`) y a `docs/requirements/platform_plan.md` (`DEC-P01`, `DEC-P03`, `DEC-P04`, `DEC-P05`, `DEC-P07`, unicidad de motores `NO-04` y limpieza de rutas en el contenido distribuible). |
| **Calidad** | 9.0 / 10 | Código claro, modular y cohesivo tanto en `adevv/cli.py` como en `skills/orquestar/orquestar.py`. Solo se observan detalles cosméticos menores documentados abajo como `🔵 BAJA`. |
| **Eficiencia** | 9.5 / 10 | Despacho ligero y validaciones previas al arranque ejecutadas con comprobaciones locales en disco y una única consulta `git rev-parse --show-toplevel`, omitidas en comandos informativos como `--estado`. |
| **Documentación** | 9.5 / 10 | Docstrings precisos en las funciones públicas e internas nuevas; skills, plantillas de release, workflows y adaptadores de Codex actualizados con las órdenes canónicas `adevv orquestar`, `adevv telegram` y `adevv release`. |
| **Media** | **9.42 / 10** | **APROBADO** (media > 8, sin hallazgos 🔴 ni 🟠) |

---

## Hallazgos

### 🔵 BAJA

- **H-01 [BAJA]** (`skills/telegram_gateway/SKILL.md`, líneas 13-14) — `destino: descartar`
  - **Descripción**: La viñeta descriptiva de `TELEGRAM_ALLOWED_USER_IDS` aparece duplicada en dos líneas consecutivas dentro de la sección de configuración de la skill. Efecto puramente cosmético.

- **H-02 [BAJA]** (`skills/orquestar/orquestar.py`, líneas 37-38 y 53-55) — `destino: descartar`
  - **Descripción**: Las constantes globales `SKILL`, `AGENTES` y `PROMPT` han dejado de referenciarse internamente tras extraerse la construcción dinámica a `construir_prompt_paso()` y `construir_prompt_agente()`. Mantenerlas no afecta al comportamiento y preserva compatibilidad ante posibles importaciones externas.

- **H-03 [BAJA]** (`skills/orquestar/orquestar.py`, líneas 239-248) — `destino: descartar`
  - **Descripción**: En `validar_lanzamiento_bucle()`, el conjunto `nombres_distribuidos` recopila los nombres de carpeta de `skills/` (`telegram_gateway`) y de archivos en `agents/` (`agents/*.md`), sin añadir el alias con guion del frontmatter (`telegram-gateway`, `DEC-P05`) ni escanear `agents/codex/*.toml` (cuyos stems ya coinciden 1:1 con `agents/*.md`). Riesgo hipotético mínimo.
