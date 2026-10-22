# Test Review: T-ADV-0003 (Ronda 2)

- **Tarea:** T-ADV-0003 — Adevv desde cualquier proyecto sin rutas
- **Archivos revisados:** `tests/test_instructions_cleanliness.py`, `tests/test_cli_commands.py`
- **Referencia BDD:** `tests/features/uso_sin_rutas.feature`
- **Veredicto:** **APROBADO**

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Cobertura** | 9.5 / 10 | Cubre todos los escenarios `@CA-F02-01` a `@CA-F02-10` y sus ejemplos (unidades distintas `C:` y `D:`, prefijos `MIA`/`PRJ`/`NAN`, ocultación local, `.agents`/`.gitmodules`, carpetas prohibidas y subcomandos CLI incluidos `release` y `telegram`). |
| **Aserciones** | 9.5 / 10 | Aserciones discriminantes que comparan código y salida contra los scripts subyacentes, verifican rutas absolutas entrecomilladas de la instalación activa, comprueban el PID activo y el contenido del commit inicial, y auditan los patrones prohibidos con expresiones regulares completas. |
| **Rojo correcto** | 9.0 / 10 | Las pruebas fallan limpiamente por ausencia de la funcionalidad a implementar y por las coincidencias reales pendientes de sanear en las instrucciones distribuibles. |
| **Estabilidad** | 9.0 / 10 | Limpieza explícita del árbol de procesos y de `orquestar.pid` en `finally` durante la prueba en segundo plano y aislamiento en directorios temporales. |
| **Media** | **9.25 / 10** | **APROBADO** (media > 8, sin hallazgos 🔴 ni 🟠). |

---

## Reevaluación de Hallazgos de la Ronda 1

1. **[🔴 CRÍTICO] `test_ca_f02_02_adevv_orquestar_fondo` no verifica `orquestar.pid`, no comprueba que el proceso siga vivo y deja procesos huérfanos** — `resuelto`
   - Se utiliza un comando controlado, se espera los 5 segundos de `@CA-F02-02`, se comprueba la existencia de `orquestar.pid` y que el proceso sigue vivo (`_pid_is_alive`), se valida `orquestar.log` y se termina el árbol de procesos en `finally` (`_kill_pid_tree`).
2. **[🔴 CRÍTICO] Expresiones regulares incompletas en `test_instructions_cleanliness.py` no detectan nombres con guiones ni placeholders** — `resuelto`
   - Las expresiones regulares incluyen `-`, `<` y `>` (`r"python\s+[\w\-\./\\<>]+\.py"` y `r"skills/[\w\-<>]+/scripts"`), detectando las 49 coincidencias pendientes en el árbol.
3. **[🟠 ALTA] `@CA-F02-03` y `@CA-F02-10` no comprueban que el prompt cite las rutas absolutas de la versión instalada ni prueban distinta unidad (`D:\`)** — `resuelto`
   - `test_ca_f02_03_and_10_prompt_construction` simula una instalación activa y verifica las rutas absolutas entrecomilladas tanto en `C:` como en `D:/proyectos/Nuevo`, el prompt con `--agente` y la ejecución sobre el repositorio fuente de Adevv.
4. **[🟠 ALTA] Cobertura incompleta en `@CA-F02-09` y en `@CA-F02-07`** — `resuelto`
   - Se añadieron los casos de carpeta personal simulada, raíz de unidad simulada, `.codex/agents/hades.toml` y `.gitmodules`.
5. **[🟠 ALTA] Aserciones no discriminantes en `test_ca_f02_05_adevv_release_subcommands` y ausencia de prueba para `adevv telegram`** — `resuelto`
   - Se comparan código de salida y `stdout` contra la ejecución directa de cada script original y se incluye `adevv telegram --estado`.
6. **[🟠 ALTA] Acoplamiento inválido en `test_ca_f02_08_new_project_auto_initialization` y falta de aserción sobre el mensaje emitido** — `resuelto`
   - Se invoca `["orquestar", "--max-pasos", "0"]`, se comprueba la línea informativa con el prefijo derivado y se verifica que el commit inicial contiene únicamente `.gitignore` y `task_config.yaml`.
7. **[🟡 MEDIA] Inconsistencia en cómo se verifican las paradas por error en `main_cli`** — `resuelto`
   - `_ejecutar_cli` normaliza la captura de código de retorno y salida (`out`/`err`) tanto si `main_cli` devuelve un entero como si lanza `SystemExit`.

---

## Hallazgos Nuevos

Ninguno.
