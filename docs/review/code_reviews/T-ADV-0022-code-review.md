# Code Review: T-ADV-0022

- **Delta**: `0da8307..árbol actual` (commit `7696358` + README, CHANGELOG y tarea pendientes). Producción: `skills/orquestar/calidad.py`, `skills/orquestar/orquestar.py` (`main()`), `skills/orquestar/SKILL.md`, `skills/task-dev/SKILL.md`, `skills/bug-fix/SKILL.md`, `skills/review-code/SKILL.md`, `README.md`, `CHANGELOG.md`.
- **Contrato**: triaje de la tarea, `docs/design/T-ADV-0022-design.md`, `skills/orquestar/features/calidad_delta.feature`, `docs/requirements/platform_plan.md`.
- **Veredicto vigente**: **APROBADO** (media 9,2, sin 🔴 ni 🟠). Detalle en «Reevaluación (2.ª ronda)»; la primera ronda se conserva más abajo como historial.

## Primera ronda

### Análisis estático

Todo vía `adevv orquestar --verificar` sobre el árbol actual:
- `python -m unittest discover -s skills/orquestar -p test_calidad.py`: 19 OK.
- `python -m unittest tests.test_orquestar tests.test_package_and_instructions tests.test_instructions_cleanliness`: 74 OK.
- `python -m py_compile` de `calidad.py`, `orquestar.py` y `test_calidad.py`, y `git diff --check`: en verde.
- `python skills/orquestar/orquestar.py --calidad --base 0da8307`, sin escritura: código 0. Formato y lint **omitidos con motivo** («ausencia de herramientas»), porque el repositorio no configura herramientas reconocidas. No cuenta como formato ni lint ejecutados en verde.
- No hay lint ni tipado configurados. El delta no añade dependencias ni manifiestos, y no expone secretos.

### Puntuaciones

| Criterio | Nota |
|---|---|
| Corrección | 7 |
| Seguridad | 9 |
| Conformidad | 9 |
| Calidad | 8 |
| Eficiencia | 9 |
| Documentación | 8 |
| **Media** | **8,3** |

### Hallazgos

#### 🟠 ALTA — H-01: en Windows, la evidencia de calidad falla con deltas medianos por el límite de la línea de órdenes de cmd.exe
- **Dónde**: `skills/orquestar/calidad.py:187-195` (`_comando_verificable`) y la llamada `verificar(...)` en `ejecutar`.
- **Problema**: el comando que se entrega a `verificar` incluye en base64 la lista completa de `ficheros` y, otra vez, los objetivos dentro de `comando`. `verificar` lo ejecuta con `shell=True`, que en Windows pasa por `cmd.exe`, y cmd.exe no admite líneas de más de 8191 caracteres. Lo he medido en esta máquina:
  - Un comando de 9114 caracteres falla con «La línea de comandos es demasiado larga» (código 1).
  - Con rutas de unos 45 caracteres, `_comando_verificable` produce 7955 caracteres con 60 ficheros y 9207 con 70.
- **Impacto**: el plan de plataforma fija Windows 11 como máquina principal. Cualquier tarea que toque más de unos 60 ficheros (andamiaje, migraciones, reformateos) da rojo de calidad aunque formato y lint estén limpios. Ese rojo impide `completed` en task-dev/bug-fix, Hades lo devuelve al desarrollador y el desarrollador no tiene forma de corregirlo. Las pruebas actuales usan deltas pequeños y no lo detectan.
- **para: desarrollador**. Saca la carga útil de la línea de órdenes sin perder la identidad de la evidencia. Por ejemplo:
  1. Guarda el JSON en un fichero direccionado por su hash, fuera del árbol que se hashea (p. ej. bajo `git rev-parse --git-path`).
  2. Pon en el comando solo ese sha256. La clave de evidencia sigue dependiendo de la base, los objetivos y el comando.
  3. Añade una prueba con un delta de más de 8191 caracteres que pase en Windows.

#### 🟡 MEDIA — H-02: la documentación no explica el rechazo de lanzadores `.cmd`/`.bat` en Windows · destino: `resolver`
- **Dónde**: `skills/orquestar/SKILL.md`, sección «Calidad del delta en cada tarea». Comportamiento en `calidad.py:177-180`.
- **Problema**: en Windows, los comandos con `{ficheros}` cuyo ejecutable es un `.cmd`/`.bat` siempre dan rojo. Es el caso de `npx`, del `prettier`/`eslint` globales y de los paquetes npm sin `node_modules` local. El rechazo es correcto: evita la inyección de argumentos a través de cmd. Pero la documentación solo dice que «un ejecutable resuelto ausente o que falla produce rojo», y quien configure `validation.lint: "npx eslint {ficheros}"` no sabrá por qué falla siempre. Hay que añadir una frase con la restricción y la alternativa: `node node_modules/... {ficheros}` o un comando sin marcador.

#### 🔵 BAJA — H-03: `validation:` vacío se trata como error · destino: `resolver`
- **Dónde**: `calidad.py:160`.
- **Problema**: `cfg.get('validation', {})` devuelve `None` cuando la clave existe pero está vacía, y `resolver` lo rechaza con «validation debe ser un mapa». El motor (`orquestar.py:1573`) usa `cfg.get('validation') or {}`. Basta con alinear ambos.

#### 🔵 BAJA — H-04: rutas del delta si `root` no es la raíz del repositorio · destino: `descartar`
- **Dónde**: `calidad.py:42-44`.
- **Problema**: `git diff --name-only` devuelve rutas relativas a la raíz Git, mientras que `ls-files --others` y `root / nombre` son relativas al directorio de trabajo. Solo importa si un proyecto Adevv vive en un subdirectorio de su repositorio, cosa que hoy no ocurre.

#### 🔵 BAJA — H-05: `formato_escritura` se ignora en silencio sin etapa de formato · destino: `descartar`
- **Problema**: si se declara `formato_escritura` sin `formato` explícito ni deducido, la escritura no se aplica y no hay aviso. Es inocuo, porque no se acredita nada.

### Conformidad

- El diseño se sigue fielmente: módulo stdlib cargado por ruta, `verificar` como callback, ejecución sin shell para el marcador, deducción limitada a DEC-ESP-03/04, base resuelta a SHA, comprobación de ambas etapas aunque una falle y escritura previa solo con `--aplicar`.
- Las instrucciones de task-dev, bug-fix y review-code cubren los escenarios de flujo y de Hades.
- No hay desviaciones de la arquitectura (DEC-P03, DEC-P09/P10).
- README y CHANGELOG reflejan el comportamiento real.

## Reevaluación (2.ª ronda)

**Alcance**: corrección de H-01, H-02 y H-03 desde `7696358`, en `skills/orquestar/calidad.py`, la sección «Calidad del delta en cada tarea» de `skills/orquestar/SKILL.md` y `docs/design/T-ADV-0022-design.md`. No se reabre el resto del delta.

### Análisis estático y verificación

Todo vía `adevv orquestar --verificar` sobre el árbol actual:
- `test_calidad.py`: 21 OK.
- Regresiones del triaje: 74 OK.
- `py_compile` del delta y `git diff --check`: en verde.
- `python skills/orquestar/orquestar.py --calidad --base 0da8307`, sin escritura: código 0. Formato y lint **omitidos con motivo** («ausencia de herramientas»), porque el repositorio no configura herramientas reconocidas. No cuenta como formato ni lint ejecutados en verde.
- El delta no añade dependencias nuevas ni secretos.

### Estado de los hallazgos

**H-01 · resuelto.** `_comando_verificable` hace ahora lo siguiente:
- Guarda el JSON (base SHA, ficheros, etapa, comando y herramienta) en `<git-dir absoluto>/adevv-calidad/<sha256>.json`. Escribe en un temporal del mismo directorio y lo sustituye con `os.replace`; el directorio viene de `--absolute-git-dir`, así que funciona en worktrees y queda fuera del árbol que se hashea.
- La orden solo lleva el hash de 64 hexadecimales, así que su longitud ya no depende del delta.
- La identidad de la evidencia se mantiene: el hash cubre base, objetivos y comando.
- El ejecutor rechaza identidades mal formadas, comprueba el SHA-256 del contenido antes de lanzar y sigue ejecutando sin shell.
- Si falta la carga útil o falla Git, la ejecución termina con código distinto de cero, es decir, en rojo y nunca en verde falso.
- La regresión de 100 ficheros cubre la longitud, la conservación de argumentos y la reutilización.

**H-02 · resuelto.** `SKILL.md` documenta el rechazo de `.cmd`/`.bat` con marcador en Windows. Da tres alternativas: `node node_modules/eslint/bin/eslint.js {ficheros}`, el paquete local deducible o un comando sin marcador.

**H-03 · resuelto.** Solo `validation: null` pasa a `{}`. Cualquier otro tipo inválido sigue dando error en `resolver`.

**H-04 y H-05 · descartados.** No requieren acción.

**R-01 (informe de pruebas) · resuelto.** Con `validation:` vacío y `[tool.ruff]`, la prueba exige exactamente `ruff format --check uno.py` y `ruff check uno.py`. Ahora distingue «vacío equivale a ausencia» de «se omite todo».

### Hallazgos nuevos

#### 🔵 BAJA — H-06: las cargas útiles se acumulan en `.git/adevv-calidad/` · destino: `descartar`

Cada combinación distinta de delta y comando deja un JSON pequeño que nunca se borra. Ocupa poco y no afecta a la corrección.

#### 🔵 BAJA — H-07: frase redundante en el diseño · destino: `descartar`

`T-ADV-0022-design.md` encadena dos frases que empiezan por «Así…». Es solo cosmético.

### Puntuaciones

| Criterio | Nota |
|---|---|
| Corrección | 9 |
| Seguridad | 10 |
| Conformidad | 9 |
| Calidad | 9 |
| Eficiencia | 9 |
| Documentación | 9 |
| **Media** | **9,2** |

**Veredicto vigente: APROBADO.**
