# Diseño Técnico: T-ADV-0009 · Clasificación de dificultad y selección de agente/modelo

## 1. Resumen y Contexto
El objetivo de **T-ADV-0009** es optimizar el consumo de recursos y la asignación de modelos en `/orquestar` permitiendo que cada tarea o bug declare su dificultad (`sencilla`, `media`, `dificil`) en el momento de su creación (en `/work-plan`, `/task-add` o `/bug-add`), sin incurrir en llamadas adicionales ni pasos previos. Con base en esta dificultad, el motor de orquestación adapta automáticamente la configuración del rol asignado (modelo, esfuerzo, arnés) tanto en el paso principal (`rol_de` / `ejecutar`) como en las invocaciones a subagentes (`agente`), conservando la escalada automática como red de seguridad superior ante rechazos reiterados.

## 2. Decisiones de Arquitectura y Diseño

- **DEC-D01 (Normalización y valor por defecto de `dificultad`):**
  - El campo `dificultad` en el frontmatter de tareas y bugs admite: `sencilla`, `media` y `dificil` (tolerando tildes y mayúsculas, e.g. `difícil` -> `dificil`).
  - Si una tarea no declara `dificultad`, o el valor es inválido o no reconocido, se normaliza por defecto a `media`.
  - `backlog(root)` incluye en cada elemento retornado `'dificultad': dif`.
  - Se define la función auxiliar `dificultad_de(root, iid)` para resolver de forma rápida y desacoplada la dificultad de cualquier tarea o bug a partir de su ID.

- **DEC-D02 (Jerarquía y precedencia de configuración en `ajustes`):**
  - La firma de `ajustes` se extiende a `ajustes(cfg, paso='', dificultad=None)`.
  - La configuración base del rol se obtiene filtrando las claves de metamodelado: `{k: v for k, v in cfg.items() if k not in ('pasos', 'dificultad')}`.
  - Se aplican primero los overrides de dificultad: `cfg.get('dificultad', {}).get(dificultad, {})`.
  - Se aplican a continuación los overrides de paso: `cfg.get('pasos', {}).get(paso, {})`.
  - El resultado es `{**base, **ov_dificultad, **ov_paso}`. De este modo, un ajuste específico para un paso concreto puede afinar o prevalecer sobre el ajuste general por dificultad.

- **DEC-D03 (Prevalencia estricta de `escalada`):**
  - La escalada se evalúa después de resolver los ajustes de paso y dificultad: `cfg_rol, escalado = escalada(root, rol, cfg_rol, arg)`.
  - Cuando los rechazos seguidos de Hades alcanzan el límite configurado (`escalada.rechazos`), los campos definidos en `escalada` (por ejemplo `model` o `effort`) sobrescriben los valores de `cfg_rol`. Esto garantiza que la escalada a un modelo superior siempre se impone, independientemente de que la tarea haya sido catalogada como `sencilla` o `media`.

- **DEC-D04 (Resolución contextual en `agente` y `ejecutar`):**
  - En `agente(root, rol, prompt)`: lee `iid = os.environ.get('ORQUESTAR_ID', '')` y `paso = os.environ.get('ORQUESTAR_PASO', '')`. Resuelve `dif = dificultad_de(root, iid) if iid else None` y calcula `cfg = ajustes(config(root).get(rol, {}), paso, dificultad=dif)`.
  - En `rol_de(root, paso, dificultad=None)`: acepta opcionalmente `dificultad` y lo traslada a `ajustes`.
  - En `ejecutar`: si `rol is None`, resuelve la configuración del rol por defecto considerando la dificultad derivada de `env['ORQUESTAR_ID']`.
  - En el bucle principal de `orquestar.py`: resuelve la dificultad de la tarea/bug antes de llamar a `rol_de` y `escalada`.

- **DEC-D05 (Plantillas y directrices en skills):**
  - `skills/task-add/SKILL.md`: incorpora `dificultad: sencilla | media | dificil` en metadatos y en las plantillas de tarea maestra e hija, con los criterios concisos de asignación.
  - `skills/bug-add/SKILL.md`: incorpora `dificultad: sencilla | media | dificil` en metadatos y en la plantilla de bug.
  - `skills/work-plan/SKILL.md`: documenta la asignación de dificultad al desglosar el backlog en la Fase 2 sin pasos extra.
  - `skills/task-dev/SKILL.md` y `skills/bug-fix/SKILL.md`: en la Inicialización confirman que si la tarea carece de dificultad se asume `media`.
  - `skills/orquestar/SKILL.md`: documenta la clave opcional `dificultad` dentro de la sección de roles en `orchestration.json`.

## 3. Plan de Pruebas Unitarias
1. `test_backlog_reads_dificultad`: Tareas sin campo dificultad retornan `'media'`; tareas con `sencilla` o `dificil` (incluyendo variantes con acento o espacios) retornan el valor normalizado.
2. `test_ajustes_applies_dificultad_overrides`: Comprobar que `ajustes(cfg, paso, dificultad)` aplica correctamente los valores de `dificultad[dif]`.
3. `test_ajustes_paso_and_dificultad_precedence`: Comprobar que `pasos.<paso>` prevalece sobre `dificultad.<dif>` si ambos redefinen la misma clave.
4. `test_escalada_takes_precedence_over_dificultad`: Comprobar que `escalada()` eleva el modelo aun cuando la dificultad haya seleccionado un modelo inferior.
5. `test_agente_applies_dificultad_from_active_orquestar_id`: Comprobar que `agente()` consulta `ORQUESTAR_ID` y aplica la configuración de dificultad del rol correspondiente (ej. Hades).
