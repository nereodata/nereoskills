# Estrategia de Ramas y Ciclo de Desarrollo

Esta documentación establece el marco de trabajo para el flujo de código, asegurando un ciclo de despliegue estable mediante entregas incrementales semánticas (x.y.z) adaptadas a un desarrollador/fase Post-MVP.

## 1. Nomenclatura y Gestión de Releases (SemVer Adaptado)

El ciclo de desarrollo está regido por el versionado semántico estricto de lanzamientos (formato `vX.Y.Z`), mediante el cual se determina el ritmo de los Bloques Funcionales y se clasifica la naturaleza de los cambios implementados:

*   **`X` (Major / Paradigma):** Cambios fundamentales en la arquitectura, grandes rediseños completos del sistema UI o restructuraciones del core que marcan un salto evolutivo en el producto.
*   **`Y` (Minor / Bloque Funcional):** Representa la entrega de un Bloque Funcional completo. Agrupa orgánicamente una o varias tareas terminadas (nuevas funcionalidades, mejoras y correcciones no urgentes) que se empujan a producción empacadas en una misma iteración.
*   **`Z` (Patch / Hotfix):** Soluciones a anomalías (bugs) urgentes que ocurren sobre código ya productivo. Conservan exactamente la misma funcionalidad, pero proporcionan estabilización urgente o correcciones técnicas.

## 2. El Modelo de Ramas (Version-Based Branching)

Se emplea un modelo de Trunk-Based Development adaptado donde las ramas se alinean directamente con las versiones planificadas, manteniendo una correspondencia 1:1 entre la rama de trabajo y la agrupación de tareas en el gestor de tareas.

*   **`main`**: Rama principal y permanente. Siempre debe ser estable, compilable y desplegable. Refleja la versión actual en producción. **Nunca se hace commit directamente aquí.**
*   **`release/vX.Y` (Bloque Funcional — avanza la `Y` Minor o `X` Major):**
    *   *Ejemplo:* `release/v1.2`, `release/v2.0`
    *   Representa el bloque funcional de la próxima versión. Se abre partiendo de `main` mediante la skill `/start-version`.
    *   Aquí se integran **todas** las tareas planificadas para esa versión: funcionalidades nuevas, mejoras y bugs no urgentes que pueden esperar al lanzamiento del bloque completo.
    *   Cada tarea en el gestor de tareas se asigna a una versión, lo que indica en qué rama `release/` se trabaja. Sin ambigüedad.
    *   Una vez verificado y probado el bloque completo, se hace merge hacia `main` y se etiqueta la Release (ej. `v1.2.0`) mediante la skill `/release`.
*   **`hotfix/vX.Y.Z` (Corrección urgente — avanza la `Z` Patch):**
    *   *Ejemplo:* `hotfix/v1.1.1`
    *   Se emplean para corregir bugs críticos detectados en una versión ya distribuida en producción que no pueden esperar al siguiente bloque funcional.
    *   **Nacen desde el *tag* de la versión afectada**, *no* desde `main` (especialmente crítico si `main` ya contiene tareas del próximo bloque funcional).
    *   Ejemplo de creación: `git checkout -b hotfix/v1.1.1 v1.1.0`
    *   Al terminar: Se hace la release del parche (`v1.1.1`), y **obligatoriamente** se realiza:
        1.  Merge del `hotfix` hacia `main`.
        2.  Merge del `hotfix` hacia la rama `release/` activa para asegurar que el parche convive en futuras iteraciones.

## 3. Estrategia de Merge

Al integrar una rama hacia `main`, se utiliza **squash merge**:

```bash
git checkout main
git merge --squash release/v1.2
git commit -m "chore(release): v1.2.0"
git tag -a v1.2.0 -m "Release v1.2.0"
```

**Justificación:**
*   `main` mantiene un historial limpio: un commit = una release.
*   El historial granular (commits individuales de cada tarea) se conserva en la rama `release/` y queda accesible vía `git log release/v1.2`.
*   Facilita revertir una release completa con un solo `git revert`.

**Excepción — Hotfixes:** Los hotfixes se integran con **merge commit** (no squash), ya que suelen ser un único commit y es importante preservar la trazabilidad directa del parche.

```bash
git checkout main
git merge hotfix/v1.1.1
```

## 4. Protección de `main`

La regla "nunca commit directo en main" se refuerza a dos niveles:

1.  **Nivel Git (GitHub/GitLab):** Configurar branch protection en el repositorio remoto:
    *   Require pull request / merge request antes de merge.
    *   No permitir push directo (ni siquiera para admins en entorno productivo).
2.  **Nivel Skill:** La skill `/commit` valida la rama activa antes de ejecutar. Si detecta `main`, advierte al usuario y requiere confirmación explícita para continuar.

> En fase de desarrollo individual, el nivel Skill puede ser suficiente. La protección a nivel Git se recomienda activar cuando haya más de un contribuidor o cuando el proyecto tenga usuarios en producción.

## 5. Etiquetado y Mecanismo de Release

Las etiquetas (tags) se crean **exclusivamente** a través de la skill `/release`, que es el mecanismo oficial para:

*   Validar que la rama y la versión son coherentes.
*   Ejecutar revisiones de código y tests pre-release.
*   Actualizar el CHANGELOG.
*   Crear el tag anotado (`git tag -a vX.Y.Z`).
*   Guiar el merge hacia `main` y la limpieza de la rama.

**No se crean tags manualmente.** Esto garantiza que toda release pasa por el mismo proceso de validación.

## 6. Tareas Incompletas entre Versiones

Si una tarea asignada a `release/vX.Y` no se completa antes de querer cerrar el bloque, se aplica la siguiente política (en orden de preferencia):

1.  **Revertir la tarea incompleta** de la rama release (`git revert` de sus commits) y reasignarla a la siguiente versión. Es la opción preferida si los commits de la tarea son identificables y aislados.
2.  **Mover la tarea a la siguiente versión** sin revertir, si el código incompleto no afecta a la estabilidad ni introduce funcionalidad visible al usuario (ej. refactors internos parciales, código muerto aún no conectado).
3.  **No cerrar el bloque** hasta completar o descartar la tarea. Aceptable si la tarea está próxima a terminarse y el retraso es menor.

> **Nunca** se usa la estrategia de feature flags para aislar trabajo incompleto en este modelo. Los feature flags añaden complejidad de runtime que no se justifica en equipos pequeños. Si el código no está listo, no viaja a `main`.

Para prevenir esta situación:
*   Planificar bloques funcionales con tareas atómicas e independientes.
*   Revisar el alcance del bloque antes de iniciar si se detecta riesgo de no completar alguna tarea.
*   **Subramas para tareas largas o complejas:** Si una tarea se prevé extensa o con riesgo de no completarse dentro del bloque, se puede trabajar en una subrama nacida desde la release (ej. `release/v1.2/T-[PRJ]-XXXX`). De este modo, la rama `release/` se mantiene limpia y la tarea solo se integra (merge a `release/`) cuando está terminada. Si no se completa a tiempo, la subrama simplemente no se mergea y se reasigna a la siguiente versión.

## 7. Staging y Validación Pre-Producción

Este modelo **no incluye rama de staging** de forma intencional. La validación se realiza directamente en la rama `release/vX.Y` antes del merge a `main`:

*   Las skills `/review-code` y `/review-test` se ejecutan como parte del proceso de `/release`.
*   La rama `release/` actúa como entorno de integración y validación.

**Cuándo reevaluar esta decisión:**
*   Cuando haya usuarios finales en producción con SLA de disponibilidad.
*   Cuando haya más de un contribuidor concurrente.
*   Cuando se requiera validación por parte de terceros (QA externo, cliente) antes del pase a producción.

En ese momento, considerar añadir una rama `staging` o un entorno de preview desplegado automáticamente desde `release/`.

## 8. Gestión de Submódulos (Carpeta `.agents`)

El uso del submódulo `.agents/` ha quedado obsoleto y reemplazado por la instalación global desacoplada de Adevv (`adevv instalar` y `adevv orquestar`).

Para migrar proyectos existentes que todavía utilizan el submódulo o retirar junctions locales de forma segura, consulta la [Guía de migración desde submódulo .agents en el README](README.md#--guía-de-migración-desde-submódulo-agents).

## 9. Resumen Visual del Flujo de Trabajo

```text
main (v1.1.0) ── tag: v1.1.0
  │
  ├─> /start-version v1.2
  │    Crea: release/v1.2 + bump manifiestos
  │      │
  │      ├─ T-[PRJ]-XXXX (feature A)
  │      ├─ T-[PRJ]-XXXX (feature B)
  │      ├─ B-[PRJ]-XXXX (bug no urgente, va con el bloque)
  │      └─ T-[PRJ]-XXXX (feature C)
  │
  │   (mientras tanto, bug urgente en prod)
  ├─> hotfix/v1.1.1 (desde tag v1.1.0)
  │     └─ B-[PRJ]-XXXX (fix crítico)
  │     /release → merge commit → main (tag v1.1.1)
  │     merge → release/v1.2 (incorporar el fix)
  │
  │   (bloque completo y validado)
  │   /release → squash merge → main (tag v1.2.0)
  │
main (v1.2.0) ─────────> ¡Lanzamiento Oficial v1.2.0!
  │
  ├─> /start-version v1.3
  │     └─ ...
```
