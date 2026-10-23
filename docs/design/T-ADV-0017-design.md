# Diseño técnico: T-ADV-0017

Se amplía el soporte de invocación de subagentes en `skills/orquestar/orquestar.py` para admitir `--prompt <texto>` directo, incluir `orquestar_prompt.txt` en `PROPIOS` (excluido de git) y garantizar la auto-limpieza atómica en un bloque `finally` de ficheros temporales pasados mediante `--prompt-file <ruta>` cuando se encuentren en la raíz del proyecto y no estén rastreados por git.

## Reglas y Decisiones Técnicas

1. **Prioridad y captura del mandato:**
   - Para `--agente <rol>`, el texto del prompt se resuelve en este orden:
     1. `--prompt <texto>` si se proporciona.
     2. `--prompt-file <ruta>` si se especifica: lee en UTF-8.
     3. `sys.stdin.read()` si ninguno de los anteriores se pasa.
   - Si tras resolver el prompt el contenido está vacío o en blanco, `sys.exit('Falta el mandato: --prompt, --prompt-file o entrada estándar.')`.

2. **Inclusión en PROPIOS:**
   - Se añade la constante `PROMPT_FILE_DEFAULT = 'orquestar_prompt.txt'` a la tupla `PROPIOS`.
   - La función `excluir(root)` añade automáticamente `orquestar_prompt.txt` al `.git/info/exclude` del repositorio, impidiendo que ensucie el estado de git si se utiliza como fichero intermedio.

3. **Detección de seguimiento y auto-limpieza en la raíz:**
   - Helper `es_fichero_rastreado_git(root, ruta)`: ejecuta `git ls-files --error-unmatch <rel_path>` en `root`. Si el comando termina con código 0, el fichero está rastreado por git; si falla (código distinto de 0), no está rastreado.
   - Si se pasa `--prompt-file <ruta>`, se resuelve la ruta absoluta (`(root / a.prompt_file).resolve()`).
   - Se marca `borrar_prompt_file = True` únicamente si:
     - `ruta_prompt_file.parent == root.resolve()` (está en la raíz del proyecto, no en subdirectorios ni fuera del proyecto).
     - `not es_fichero_rastreado_git(root, ruta_prompt_file)` (no está bajo control de versiones).
   - La invocación `agente(root, a.agente, prompt)` se ejecuta dentro de un bloque `try ... finally`.
   - En el bloque `finally`: si `borrar_prompt_file` es verdadero y el archivo existe, se elimina de forma segura con `unlink(missing_ok=True)` capturando posibles `OSError`.
   - Esto asegura que ante errores, cuotas agotadas (`sys.exit`), excepciones o finalización normal, el fichero temporal no rastreado en la raíz desaparece sin dejar rastro en `git status`.

4. **Preservación e inocuidad:**
   - Ficheros rastreados en la raíz nunca se borran.
   - Ficheros ubicados en subcarpetas (por ejemplo `tests/`, `docs/`, `tmp/`) no se borran automáticamente.
   - No se altera la interfaz de `agente(root, rol, prompt)`.

## Impacto y Pruebas

- **Ficheros modificados:** `skills/orquestar/orquestar.py`, `skills/orquestar/SKILL.md`.
- **Ficheros nuevos:** `skills/orquestar/test_agente_prompt.py`.
- **Tests unitarios:** Validarán `--prompt`, `--prompt-file` con borrado de temporales no rastreados en raíz, no borrado de rastreados, no borrado de ficheros en subcarpetas, borrado garantizado incluso tras excepción o fallo del agente, y presencia de `orquestar_prompt.txt` en `PROPIOS`.
