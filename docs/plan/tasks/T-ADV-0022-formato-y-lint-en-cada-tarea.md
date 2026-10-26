---
id: T-ADV-0022
title: "Formato y lint del proyecto sobre los ficheros tocados en cada tarea, no solo al cerrar la versión"
type: funcional
weight: 60
dificultad: media
version: "v1.0.0"
status: planned
depende_de: []
origen: "B-ADV-0006: la suite llega en rojo al cierre por formato (Prettier) acumulado tarea a tarea"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0022: Formato y lint del proyecto sobre los ficheros tocados en cada tarea, no solo al cerrar la versión

## 🎯 Objetivo de Negocio
Cada tarea verifica solo las pruebas de su triaje, así que los fallos de formato y lint (p. ej. Prettier, ESLint, ruff) se acumulan y solo aparecen al pasar la suite completa al cerrar la versión. B-ADV-0006 hace que el bucle se recupere de ese rojo; esta tarea evita que llegue a producirse, comprobando formato y lint en cada `task-dev` / `bug-fix` y en la revisión de Hades.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Detección de las etapas de formato y lint):** el proyecto puede declarar en `task_config.yaml` (p. ej. `validation.formato` y `validation.lint`) los comandos de formato y lint, aceptando un marcador de ficheros (`{ficheros}`) para limitarlos al delta. Sin declaración, se deducen de forma conservadora de los manifiestos habituales (`package.json` scripts `format:check`/`lint`, `pyproject.toml` con `ruff`, etc.) o se omiten sin error.
- [ ] **CA-M-2 (Uso en cada tarea):** `/task-dev` y `/bug-fix` ejecutan esas etapas sobre los ficheros que tocan antes de cerrar (aplicando el formateador si existe modo de escritura), y la tarea no pasa a `completed` con formato o lint en rojo en su delta.
- [ ] **CA-M-3 (Hades):** la revisión de código de Hades comprueba (vía `--verificar`, reutilizando evidencia del mismo árbol) que formato y lint pasan sobre el delta; un fallo es un hallazgo para el `desarrollador`.
- [ ] **CA-M-4 (Pruebas y documentación):** pruebas unitarias de la resolución de comandos y del marcador `{ficheros}`; documentación en las skills afectadas y en `skills/orquestar/SKILL.md`.

## 📋 Notas
- La suite completa al cerrar versión se mantiene como red de seguridad (B-ADV-0006).

## Especificación revisada (2026-10-26)

Los hallazgos H-01/H-02/H-03 se resuelven en [calidad_delta.feature](../../../skills/orquestar/features/calidad_delta.feature). La especificación rechazada solo existe en WIP; no hay escenarios aprobados de calidad que retirar. Se conserva íntegra la característica de reservas existente. No se incorpora código, diseño ni pruebas del WIP.

### Decisiones sin preguntar
- **DEC-ESP-01 — Delta estable:** base Git registrada antes de comenzar la tarea; incluir cambios confirmados desde ella, preparados, pendientes y nuevos sin rastrear no ignorados; excluir eliminados y duplicados. Alternativa descartada: solo diff pendiente, porque pierde los cambios ya confirmados de la tarea. Base inexistente es error, no omisión.
- **DEC-ESP-02 — Contrato explícito:** `validation.formato` y `validation.lint` son cadenas no vacías; opcionalmente `validation.formato_escritura` declara la escritura. `{ficheros}` produce argumentos independientes preservando nombres y sin ejecutar su contenido. Sin marcador se conserva el alcance explícito y se avisa. Alternativa descartada: modificar silenciosamente comandos del usuario o adivinar escritura por sustitución de texto. Valor no válido es error, sin deducción alternativa.
- **DEC-ESP-03 — Deducción mínima por etapa:** lo explícito prevalece; después scripts npm simples `format:check: prettier --check .` y `lint: eslint .`; sin script reconocido para esa etapa, configuración `[tool.ruff]` permite `ruff format --check` y `ruff check`. Prettier ofrece escritura con `prettier --write`; ruff con `ruff format`. Sustituir el objetivo global por ficheros del delta; scripts compuestos, wrappers y herramientas desconocidas se omiten con motivo. Alternativa descartada: ejecutar scripts arbitrarios sobre todo el proyecto. No se instalan herramientas; si un comando resuelto falla (incluida ausencia de ejecutable), es fallo de calidad.
- **DEC-ESP-04 — Compatibilidad:** ruff solo `.py` y `.pyi`; ESLint `.js`, `.jsx`, `.mjs`, `.cjs`, `.ts`, `.tsx`; Prettier extensiones habituales `.js`, `.jsx`, `.mjs`, `.cjs`, `.ts`, `.tsx`, `.json`, `.css`, `.scss`, `.html`, `.md`, `.yaml`, `.yml`. Comandos explícitos reciben todos los ficheros existentes del delta; el usuario controla su compatibilidad. Sin objetivos se omite con motivo, incluso con comando explícito sin marcador. Alternativa descartada: invocar una herramienta sin objetivos y permitir su alcance global por defecto.
- **DEC-ESP-05 — Cierre y evidencia:** ambos flujos deben aplicar escritura disponible y comprobar ambas etapas antes de completed. Hades solo comprueba y devuelve fallos al desarrollador. La evidencia satisfactoria exige mismo árbol exacto y comando (incluidos base y objetivos de la tarea); cualquier cambio de contenido posterior exige evidencia nueva. Alternativa descartada: aceptar el verde anterior al formateo. No se cambia el mecanismo de invalidación existente de --verificar ni se exige una suite completa por tarea.

## Triaje del paso especificar
- Alcance: resolver H-01/H-02/H-03 mediante requisito, DEC y escenarios; sin implementación ni tests nuevos, que corresponden a Artemisa.
- Verificación de este paso: `adevv orquestar --verificar "git diff --check"`. No hay ejecutor BDD configurado; los escenarios son contrato pendiente de automatizar. Hades /review-spec valida el delta de especificación, sin revisión de código ni de pruebas.
- Triaje de desarrollo conservado del WIP para el siguiente paso: `python -m unittest discover -s skills/orquestar -p test_calidad.py` (archivo aún ausente en release) y `python -m unittest tests.test_orquestar tests.test_package_and_instructions tests.test_instructions_cleanliness`. No ejecutarlos para fingir funcionalidad implementada en este paso; Artemisa ajustará el triaje si cambia el alcance. No suite completa.
- Base del siguiente desarrollo: el commit de cierre de esta especificación; la base histórica del intento WIP fue `981b18dc23a2fc292aeda6d38c80fff1206b748c`.

## Cierre del paso especificar

Hades /review-spec APROBADO (9,25/10), ratificado mediante el lanzador con veredicto final inequívoco. H-01/H-02/H-03 resueltos, sin hallazgos pendientes. El siguiente paso corresponde al desarrollo; no se declara completada la funcionalidad.
