# Diseño Técnico: T-ADV-0011 · Subida automática de dificultad de la tarea tras más de 2 reintentos

## 1. Resumen y Contexto
El objetivo de **T-ADV-0011** es permitir que `/orquestar` promueva dinámicamente la dificultad de una tarea o bug (`sencilla` $\to$ `media` $\to$ `dificil`) cuando acumula más de 2 reintentos (ejecuciones de paso sobre ese `ID`, rechazos seguidos de Hades o pasos sin progreso desde la última subida). Esto asegura que el orquestador aplique el perfil de modelo y esfuerzo del nivel inmediato superior configurado en `orchestration.json` (`dificultad.<nivel>`), evitando que el desarrollo quede atascado por un modelo insuficiente.

## 2. Decisiones de Arquitectura y Diseño

- **DEC-D01 (Escalones y actualización de dificultad en frontmatter):**
  - Se define la jerarquía cerrada: `sencilla` $\to$ `media` $\to$ `dificil`.
  - Se implementan `siguiente_dificultad(dif)`, `fichero_de(root, iid)`, `actualizar_dificultad(root, iid, nueva_dif)` y `promover_dificultad(root, iid, motivo='')`.
  - `actualizar_dificultad` localiza el fichero `.md` en los directorios de backlog (`tasks/` o `bugs/`) y actualiza o inserta el campo `dificultad: <nueva>` en su frontmatter YAML preservando el resto de metadatos y cuerpo.
  - `promover_dificultad` ejecuta la actualización, imprime por consola `[orquestar] {iid}: subo dificultad de {actual} a {nueva}{motivo}`, y registra un evento `tipo: promocion` en `orquestar_metricas.jsonl`.

- **DEC-D02 (Detección de reintentos y rechazos desde la última subida):**
  - Se implementa `reintentos_acumulados(root, iid)` y se adapta `rechazos(root, iid)` para resetear contadores en cuanto aparece un evento `tipo: promocion` para ese `iid` en `orquestar_metricas.jsonl`.
  - Se detecta necesidad de promoción si para un `ID` elegible en `task-dev` o `bug-fix` con dificultad `sencilla` o `media`:
    1. Las ejecuciones de paso efectivas (sin cuota) sobre ese `ID` desde la última subida superan 2 (`pasos > 2`), o
    2. Los rechazos seguidos de Hades alcanzan el tope de rechazos (`rech >= tope`).

- **DEC-D03 (Integración con `tope_de_rechazos` y `escalada`):**
  - En `tope_de_rechazos(root, iid)`:
    - Se comprueba si el rol tiene configurados niveles en `dificultad` (`cfg_dev.get('dificultad')`) y la tarea aún puede subir (`dif in ('sencilla', 'media')`).
    - Si puede subir: al alcanzar el tope de rechazos, indica a Artemisa que commitee lo que tenga y termine el paso sin cambiar estados para que el bucle suba la dificultad de la tarea y la relance con el perfil del nuevo nivel.
    - Si la tarea ya está en `dificil` (o el rol no tiene `dificultad` configurada):
      - Si existe `escalada` y no está escalado, ordena commitear y terminar para escalar modelo.
      - Si ya está escalado o no hay `escalada`, ordena aplicar la regla 5 del modo orquestado (bloqueo).
  - En `escalada(root, rol, cfg, iid)`:
    - Si el rol tiene niveles de `dificultad` y la tarea puede subir (`sencilla` o `media`), no escala a la clave `escalada` de rol, permitiendo que la promoción por dificultad tenga prioridad.

- **DEC-D04 (Reintentos sin progreso en `bucle()`):**
  - En `bucle()`, cuando `sin_progreso >= a.reintentos`:
    - Si el paso es `task-dev` o `bug-fix` sobre un `ID` con dificultad `sencilla` o `media`:
      - Antes de parar el bucle, promueve la dificultad del `ID` al nivel superior (`promover_dificultad`).
      - Reinicia `sin_progreso = 0`.
      - Continúa el bucle (`continue`) para reintentar de inmediato con la configuración del nuevo nivel.
    - Si ya está en `dificil` o no es promocionable, procede a detener el bucle como error de falta de avance.

- **DEC-D05 (Documentación en `/orquestar`):**
  - Se actualiza `skills/orquestar/SKILL.md` documentando la promoción automática de dificultad tras reintentos o rechazos seguidos de Hades y su prioridad antes de la escalada o bloqueo.

## 3. Plan de Pruebas Unitarias
En `tests/test_orquestar.py`:
1. `test_promover_dificultad_updates_frontmatter_and_logs_metric`:
   - Verifica actualización de `sencilla` a `media` y de `media` a `dificil` en archivo `.md`.
   - Verifica que `dificil` no promueve (`None`).
   - Verifica emisión de métrica `tipo: promocion`.
2. `test_rechazos_and_reintentos_reset_on_promocion`:
   - Verifica que `rechazos()` y `reintentos_acumulados()` se reinician tras registrar una promoción.
3. `test_tope_de_rechazos_instructs_promotion_when_difficulty_can_increase`:
   - Con rol con `dificultad` y tarea `sencilla`/`media`, mensaje de terminar para subida de dificultad.
   - Con tarea `dificil`, mensaje de escalada o regla 5.
4. `test_escalada_deferred_while_difficulty_can_promote`:
   - Verifica que `escalada()` retorna `False` si la tarea aún puede promocionar en dificultad.
5. `test_bucle_promotes_difficulty_on_sin_progreso_and_retries`:
   - Simulación de bucle con paso sin progreso: promueve de `sencilla` a `media`, reinicia `sin_progreso` y reintenta en lugar de parar.
