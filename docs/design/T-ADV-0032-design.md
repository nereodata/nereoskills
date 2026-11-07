# Diseño Técnico: T-ADV-0032 - Centralizar la planificación, ejecución y reutilización de chequeos de calidad y release

## 🏗️ Arquitectura

Se consolida la planificación, ejecución, acreditación de evidencia, coordinación entre entradas y control de puertas de release en un único módulo de librería estándar `skills/orquestar/chequeos.py`, consumido por:
- `skills/orquestar/orquestar.py` (`verificar`, `construir_prompt_agente`, `resumen`, `parte`, `--verificar`, `--estado`, cierre de versión y recuperación de suite roja).
- `skills/orquestar/calidad.py` (adaptador de formato/lint por delta que delega o se integra en el catálogo común sin romper su interfaz de `T-ADV-0022`).
- `adevv/release_tools.py` y `skills/telegram_gateway/cierre_version.py` (separación de acciones `validar`, `cerrar_local`, `etiquetar`, `publicar`, aplicación de restricciones por entrada y evaluación de `release.preflight` / puertas sobre el worktree preparado reutilizando evidencia vigente a través de `git-common-dir`).
- `adevv/migrate.py` / `skills/orquestar/chequeos.py` (adopción del flujo común para proyectos con lanzadores redundantes de cierre tipo Afinn y transición de evidencia histórica).

Respeta las reglas de capas de `docs/requirements/platform_plan.md §4`: cero dependencias externas (Python ≥ 3.11 stdlib), unicidad de motores (`NO-04`) y persistencia atómica mediante archivo temporal + `os.replace`.

## 🛠️ Cambios

- **[NEW]** `skills/orquestar/chequeos.py`:
  - Catálogo de etapas (`formato`, `lint`, `tipado`, `seguridad`, `secretos`, `dependencias`, `pruebas`, `builds`) y puertas de `release`.
  - Validación estricta de `task_config.yaml` (`validation.*`, `release.puertas`, `release.restricciones`, `release.preflight`).
  - Separación explícita entre `disponibilidad` (`configurado`, `ausente`, `omitido`) y `resultado` (`sin_acreditar`, `pendiente`, `ejecutando`, `aprobado`, `fallido`, `interrumpido`, `historial_sin_acreditar`).
  - Cálculo de identidad compuesta (`calcular_identidad`): comando efectivo + huella de contenido relevante (árbol Git completo o subárbol/archivos de `entradas` declaradas, incluyendo cambios sin confirmar y archivos no rastreados no ignorados) + huella de entorno relevante (`herramienta`, `configuracion`, `dependencias`, `plataforma`).
  - Detección de cambios durante la ejecución (`identidad_inicial != identidad_final`), invalidando la acreditación para ambas identidades.
  - Precedencia del último resultado real por identidad y detección/registro de `intermitente` (`transiciones`, `diagnostico`) sin reintentos automáticos sobre la misma identidad.
  - Coordinación inter-proceso y entre worktrees bajo `<git-common-dir>/adevv-chequeos/`: unión de solicitudes concurrentes con la misma identidad, aislamiento de solicitudes con distinta identidad, captura de salida parcial en vivo y recuperación de procesos interrumpidos (PID inactivo) sin falsos aprobados.
  - Diagnóstico y planificación de reparación (`planificar_reparacion`) con caché por comprobación según alcances de invalidación conservadores.
  - Separación de acciones (`validar`, `cerrar_local`, `etiquetar`, `publicar`) y verificación de restricciones/autorizaciones por canal (`cli`, `gateway`, `agente`).
  - Adopción/migración de lanzadores redundantes (`adoptar_flujo_comun`) y clasificación de evidencia histórica incompleta como `historial_sin_acreditar`.
- **[MODIFY]** `skills/orquestar/orquestar.py`:
  - `verificar(root, cmd)`: registra la identidad completa (`entorno`, `identidad`, `contrato: "v2"`, `intermitente`, `cambio_en_vuelo`), coordina ejecuciones concurrentes equivalentes y evalúa la reutilización según el **último resultado real aplicable** (un fallo posterior invalida cualquier verde anterior).
  - `construir_prompt_agente(root, rol, prompt, reanudacion=False)`: incluye en `Verificado en verde sobre este árbol` únicamente los comandos cuyo **último resultado real aplicable** sobre el árbol/identidad actual es `codigo == 0` (excluyendo los que tienen un fallo posterior o cambio en vuelo).
  - `resumen(root)` y `parte(root)`: exponen el estado de comprobación/cierre activo si hay uno en ejecución o interrumpido.
- **[MODIFY]** `adevv/release_tools.py` y `skills/telegram_gateway/cierre_version.py`:
  - Soportan restricciones declaradas en `task_config.yaml::release.restricciones` (distinguiendo `validar`, `cerrar_local`, `etiquetar`, `publicar` y canal de origen).
  - En `publicar_version`, evalúan `release.preflight` y puertas de release sobre el worktree integrado tras el merge con `main` a través del verificador compartido (vinculado al repositorio principal mediante `git-common-dir`), evitando repetir suites ya acreditadas sobre el mismo árbol integrado y reejecutando si el merge modificó entradas relevantes.
- **[NEW]** `skills/orquestar/test_chequeos.py`:
  - Suite de pruebas unitarias, de concurrencia e integración para `CA-M-1` a `CA-M-10`.
- **[MODIFY]** `skills/orquestar/SKILL.md`, `skills/release/SKILL.md`, `skills/telegram_gateway/SKILL.md`, `CHANGELOG.md`:
  - Documentación de configuración de etapas, puertas, restricciones de release, coordinación y transición de evidencia.

## 🎯 Mapa de impacto

- **Llamantes de elementos modificados:**
  1. `orquestar.verificar(root, cmd)`:
     - Llamado por `orquestar.main()` (`--verificar`), `orquestar.bucle()` (suite de cierre), `calidad.ejecutar()` (formato y lint del delta) y pruebas en `tests/test_orquestar.py` y `skills/orquestar/test_calidad.py`.
     - **Comportamiento requerido:** todos los llamantes quieren el nuevo comportamiento (el último resultado real prevalece; un fallo posterior invalida un verde anterior; no se duplica una ejecución equivalente en curso; Reutilizar no escribe una nueva línea en `orquestar_evidencias.jsonl`).
     - **Preservación de contrato existente:** `arbol(root)` sigue ejecutándose al inicio de `verificar(root, cmd)` para mantener intacto el contrato de fallo temprano verificado por `test_failed_capture_neither_reads_nor_writes_validation_evidence`.
  2. `orquestar.construir_prompt_agente(root, rol, prompt, reanudacion=False)`:
     - Llamado por `orquestar.agente()` y probado en `tests/test_orquestar.py::test_agent_prompt_lists_verified_commands_for_current_tree`.
     - **Comportamiento requerido:** quiere que un comando cuyo último resultado en `orquestar_evidencias.jsonl` para el árbol actual es `codigo == 0` aparezca en `Verificado en verde sobre este árbol`, pero que deje de aparecer si un registro posterior para ese mismo comando y árbol falló (`codigo != 0`). Los registros sintéticos de pruebas existentes con un único verde (`codigo == 0`) siguen apareciendo sin romper ningún test existente.
  3. `release_tools.publicar_version(repo_dir, target_tag, origin_url=None, *, rama=None, cfg=None, canal='cli', accion='publicar')`:
     - Llamado por `cierre_version.publicar()` (con `canal='gateway'`) y `tests/test_publicacion_compartida.py`, `tests/test_install_and_release.py` y `skills/telegram_gateway/test_cierre_version.py`.
     - **Comportamiento requerido:** mantiene su firma posicional y por palabra clave compatible hacia atrás; añade verificación de restricciones por acción/canal y reutilización de evidencia vigente en `preflight` sobre el árbol del worktree preparado.
- **Escenarios y tests existentes afectados:**
  - Ningún escenario BDD ni test existente en `tests/test_orquestar.py`, `skills/orquestar/test_calidad.py`, `tests/test_publicacion_compartida.py` o `skills/telegram_gateway/test_cierre_version.py` queda invalidado ni requiere modificarse para pasar.
- **Decisiones documentadas contradichas:**
  - **Ninguna.** Extiende `T-ADV-0006`, `T-ADV-0022`, `T-ADV-0023` y `B-ADV-0025` dentro de la arquitectura de `docs/requirements/platform_plan.md`.
- **Sistema de referencia:**
  - Marcas temporales en formato ISO-8601 local con segundo (`datetime.now().isoformat(timespec='seconds')`), idéntico a `orquestar.ahora()`. Huellas de contenido y entorno en SHA-256 hexadecimal (y SHA-1/SHA-256 de `git write-tree` para el árbol completo).
- **Camino caliente:**
  - `verificar` y `construir_prompt_agente` se invocan en cada tarea y revisión. La identidad por defecto usa `git write-tree` con índice temporal (igual que hoy) más lectura `stat`/SHA-256 únicamente de los manifiestos de configuración/dependencias declarados o presentes en la raíz (`task_config.yaml`, `pyproject.toml`, `package.json` y lockfiles directos), sin recorrer recursivamente `node_modules` ni `.git`. Se comprueba en tests que la reutilización de evidencia no invoca el subproceso del comando y resuelve en milisegundos.

## 🧩 Patrones y firmas principales (`skills/orquestar/chequeos.py`)

- `ETAPAS = ('formato', 'lint', 'tipado', 'seguridad', 'secretos', 'dependencias', 'pruebas', 'builds')`
- `ACCIONES_RELEASE = ('validar', 'cerrar_local', 'etiquetar', 'publicar')`
- `validar_configuracion(root, cfg=None) -> dict`: valida `validation` y `release`, lanzando `ValueError` descriptivo ante configuraciones inválidas.
- `resolver_catalogo(root, cfg=None, ficheros_delta=None) -> dict`: devuelve el mapa de etapas con `disponibilidad`, `comando`, `obligatorio`, `entradas`, `origen` y `motivo`.
- `calcular_identidad(root, etapa, comando, entradas=None, entorno_override=None) -> dict`: devuelve `{'identidad': sha256, 'contenido': hash_contenido, 'entorno': {...}, 'acreditable': bool, 'motivo_no_acreditable': str}`.
- `planificar(root, etapas=None, puerta=None, cambios_reparacion=None, entorno_override=None) -> dict`: genera el plan explicable antes de ejecutar y calcula qué etapas se reutilizan, ejecutan, omiten, esperan o bloquean.
- `ejecutar_comprobacion(root, etapa, ..., ejecutor=None, entorno_override=None) -> dict`: coordina bloqueo por identidad en `<git-common-dir>/adevv-chequeos/`, une clientes concurrentes de la misma identidad, escribe estado y salida parcial en vivo, verifica que la identidad no haya cambiado durante la ejecución y persiste en `orquestar_evidencias.jsonl`.
- `evaluar_puerta(root, puerta='release', ejecutar=True, ejecutor=None, entorno_override=None) -> dict`: evalúa todas las comprobaciones de una puerta respetando obligatoriedad, caché por etapa y precedencia del último resultado.
- `verificar_accion_release(root, accion, canal='cli', autorizado=False, cfg=None) -> dict`: aplica la separación entre `validar`, `cerrar_local`, `etiquetar` y `publicar`.
- `adoptar_flujo_comun(root, ruta_externa_afinn=None) -> dict`: migra configuraciones y lanzadores redundantes al flujo compartido, clasifica evidencia histórica y registra explícitamente el bloqueo si el repositorio externo `Afinn` está fuera del árbol de trabajo autorizado.

## 🧪 Testeabilidad

- `ejecutor` inyectable en `ejecutar_comprobacion` y `evaluar_puerta` para simular comandos lentos, fallos, cambios de ficheros a mitad de ejecución y concurrencia entre hilos/procesos sin ejecutar suites de una hora.
- `entorno_override` inyectable para variar determinísticamente versión de herramienta, configuración, lockfile de dependencias o plataforma sobre un mismo commit Git.
- Repositorios Git temporales con worktrees reales (`git worktree add`) y remotos `bare` locales para verificar coordinación entre worktrees y reutilización de evidencia en `publicar_version` tras el merge con `main`.
