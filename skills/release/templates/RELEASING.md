# Releasing — {{PROJECT_NAME}}

> Documento humano-legible que describe cómo se cierra una versión de
> este proyecto. La automatización vive en la skill `/release` (montada
> como submódulo en `.agents/skills/release/`); este documento es el
> contrato que esa skill ejecuta.

## 1. Modelo de versionado

Este proyecto sigue el modelo descrito en
[`branch_strategy.md`](./branch_strategy.md):

- **Bloque funcional** (`Y` Minor): rama `release/vX.Y`, abierta con
  `/start-version`, cerrada con `/release` produciendo el tag `vX.Y.0`.
- **Hotfix** (`Z` Patch): rama `hotfix/vX.Y.Z` desde el tag afectado,
  cerrada con `/release` produciendo el tag `vX.Y.Z`.
- El historial de `main` se mantiene limpio mediante **squash merge**
  para releases ordinarias, y **merge commit** para hotfixes.

## 2. Manifiestos a actualizar

La versión "fuente de verdad" es `task_config.yaml::project.version`.
Todos los demás manifiestos deben coincidir (la skill aborta si no lo
hacen).

<!-- BEGIN: manifests-table — generado automáticamente por /release -->
{{MANIFESTS_TABLE}}
<!-- END: manifests-table -->

Ejemplo:

| Fichero | Tipo | Clave |
|---------|------|-------|
| `task_config.yaml` | yaml | `project.version` |
| `package.json` | json | `version` |
| `services/api/pyproject.toml` | toml | `project.version` |

Para sincronizarlos: `/start-version` (al abrir el bloque) o edición
manual seguida de `python .agents/skills/release/scripts/check_manifests_versions.py`.

## 3. Flujo de release ordinario

Tras completar todas las tareas asignadas a `vX.Y` en la rama
`release/vX.Y`:

1. **Pre-flight (local)** — desde la rama `release/vX.Y`:
   - `/review-code` y `/review-test` globales si procede.
   - `python .agents/skills/release/scripts/check_release_completeness.py --version vX.Y.0`
   - `python .agents/skills/release/scripts/check_manifests_versions.py`
   - `actionlint .github/workflows/*.yml` (si el repo tiene workflows)
   - Comandos declarados en `task_config.yaml::release.preflight`
     (lint, type-check, tests, full build con flag `--dir` o equivalente
     para reproducir el path de empaquetado del CI).
2. **CHANGELOG** — confirmar que la sección `[X.Y.Z]` existe y resume
   los cambios. Si no:
   ```
   python .agents/skills/release/scripts/generate_changelog_section.py --version vX.Y.0
   ```
   Pegar la salida en `CHANGELOG.md`, escribir el resumen ejecutivo
   ("Highlights") a mano, commitear.
3. **Tag y merge** — invocar `/release`. La skill:
   - Crea el commit `chore(release): vX.Y.0` en `release/vX.Y`.
   - Pide confirmación explícita antes del paso destructivo.
   - Hace `git checkout main && git merge --squash release/vX.Y`.
   - Crea el tag anotado `vX.Y.0` **sobre `main`**, no sobre la rama
     `release/`.
   - Push con `git push origin main --follow-tags`.
4. **Post-tag verification** — la skill espera al CI:
   - `gh run watch` y validación de assets en `gh release view vX.Y.0`.
   - Health checks declarados en `task_config.yaml::release.deploy_health_checks`.
   - Recordatorio al humano para smoke test del entregable.

## 4. Flujo de hotfix

1. Crear rama desde el tag afectado:
   `git checkout -b hotfix/vX.Y.Z vX.Y.(Z-1)`.
2. Aplicar el fix con `/bug-fix`.
3. Repetir pre-flight resumido (tests + manifest check + actionlint).
4. Invocar `/release`. La skill:
   - Hace **merge commit** (no squash) a `main`.
   - Crea tag `vX.Y.Z` sobre `main`.
   - Hace merge del hotfix también a la rama `release/` activa si
     existe (paso 4b de la skill).

## 5. Rescate del tag (CI falla por errata pequeña)

Si tras `git push --follow-tags` el CI falla **al instante** por una
errata reparable (fichero faltante, sintaxis YAML inválida) **y nadie
ha distribuido el artefacto** (`gh release view vX.Y.Z` muestra 0
descargas):

1. `git checkout -b hotfix/vX.Y.Z-ci-fix main`.
2. Aplicar el fix mínimo y commitear.
3. Fast-forward merge a `main`.
4. Mover el tag: `git tag -fa vX.Y.Z -m "Release vX.Y.Z"`.
5. `git push origin main` (sin `--force`, es un commit normal).
6. `git push origin vX.Y.Z --force` (sólo el tag se mueve).
7. Borrar la rama hotfix.

Si **alguien ya descargó** el artefacto roto, no se mueve el tag: se
hace un `vX.Y.(Z+1)` canónico.

## 6. Distribución y despliegue

<!-- Personalizar por proyecto: artefactos generados, canales de
distribución, despliegues cloud, validaciones post-deploy. -->

{{DISTRIBUTION_SECTION}}

## 7. Code signing (si aplica)

Activado mediante `task_config.yaml::release.code_signing.enabled = true`.
Detalles del proveedor y secretos requeridos en esa misma sección.

Verificación post-release:
- Windows (Authenticode / Trusted Signing): `signtool verify /pa /v <ruta-exe>`.
- macOS: `codesign --verify --deep --strict <ruta-app>`.

## 8. Notas operativas

- **Nunca** se crean tags manualmente fuera de `/release`.
- **Nunca** se commitea directo en `main`.
- Si una tarea no se completa antes de cerrar el bloque, ver la
  política de "Tareas Incompletas entre Versiones" en
  [`branch_strategy.md`](./branch_strategy.md).
- Las notas del Release de GitHub se complementan con el contenido del
  CHANGELOG: `gh release edit vX.Y.Z --notes-file <(extraer-seccion)`.
