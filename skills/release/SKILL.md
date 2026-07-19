---
name: release
description: Gestión de lanzamientos y etiquetado de versiones (Release Management)
---

# Skill: Gestión de Lanzamientos (/release)

Formaliza el cierre de una versión del proyecto y su etiquetado.

## 📋 Pasos de la Skill

### 1. Pre-Release (Validación)
- **Rama**: `release/vX.Y` o `hotfix/vX.Y.Z` → coincide con `task_config.yaml::project.version`.
- **Backlog**: Tareas cerradas (ver scripts en `skills/release/scripts/` si necesario).
- **Manifiestos**: Versiones alineadas.
- **Changelog**: Sección de versión presente; generar si falta.
- **CI Preflight**: Ejecutar comandos en `task_config.yaml::release.preflight`.

### 2. Ejecución del Bump
- Confirmar versión con el usuario.
- Crear commit `chore(release): vX.Y.Z` con los archivos actualizados.
- Cerrar la tarea de release en el backlog.

### 3. Merge y Etiquetado (Requiere confirmación)
- **Para Release normal (`release/vX.Y`)**:
  ```bash
  git checkout main
  git pull --ff-only
  git merge --no-ff release/vX.Y -m "chore(release): vX.Y.Z"
  git tag -a vX.Y.Z -m "Release vX.Y.Z"
  git push origin main --follow-tags
  git branch -d release/vX.Y
  ```
- **Para Hotfix (`hotfix/vX.Y.Z`)**:
  ```bash
  git checkout main
  git pull --ff-only
  git merge --no-ff hotfix/vX.Y.Z -m "chore(release): vX.Y.Z"
  git tag -a vX.Y.Z -m "Release vX.Y.Z"
  git push origin main --follow-tags
  # Si hay rama release activa, integrar el fix:
  git checkout release/vA.B && git merge hotfix/vX.Y.Z && git push
  ```

### 4. Verificación Post-Tag
- Vigilar compilación/CI: `gh run watch` u observar panel.
- Comprobar publicación: `gh release view vX.Y.Z` y comprobar assets.
- Ejecutar smoke tests manuales del producto.

### 5. Rescate (En caso de error menor antes de distribuir)
**Condición crítica:** Solo mover un tag si nadie ha descargado el artefacto. Verificar con:
```bash
gh release view vX.Y.Z --json downloadCount -q '.downloadCount'
```
Si `downloadCount > 0`, **NO mover el tag**: lanzar una versión canónica `vX.Y.(Z+1)` en su lugar.

Si `downloadCount == 0` y falla el CI al instante:
1. `git checkout -b hotfix/vX.Y.Z-ci-fix main`
2. Aplicar fix, commitear y mergear a `main`.
3. Mover tag: `git tag -fa vX.Y.Z -m "Release vX.Y.Z"`
4. Push: `git push origin main && git push origin vX.Y.Z --force`
