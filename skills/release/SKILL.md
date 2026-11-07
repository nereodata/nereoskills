---
name: release
description: Gestión de lanzamientos y etiquetado de versiones (Release Management)
---

# Skill: Gestión de Lanzamientos (/release)

Formaliza el cierre de una versión del proyecto y su etiquetado.

## 📋 Pasos de la Skill

### 1. Pre-Release (Validación)
- **Rama**: `release/vX.Y` o `hotfix/vX.Y.Z` → coincide con `task_config.yaml::project.version`.
- **Backlog**: Tareas cerradas (ver `adevv release completitud` si necesario).
- **Manifiestos**: Versiones alineadas (`adevv release manifiestos`).
- **Changelog**: Sección de versión presente; generar si falta (`adevv release changelog`).
- **CI Preflight**: Ejecutar comandos en `task_config.yaml::release.preflight`.

### 2. Ejecución del Bump
- Confirmar versión con el usuario.
- Crear commit `chore(release): vX.Y.Z` con los archivos actualizados.
- Cerrar la tarea de release en el backlog.

### 3. Merge y Etiquetado (Requiere confirmación)
- Desde la rama `release/vX.Y` o `hotfix/vX.Y.Z`, usar la misma implementación que `/cerrar`:
  ```bash
  python -c "from pathlib import Path; from adevv.release_tools import publicar_version; publicar_version(Path.cwd(), 'vX.Y.Z')"
  ```
- La función valida manifiestos, changelog y etiquetas; prepara el merge en un worktree aislado y evalúa `release.preflight` reutilizando la evidencia acreditada del proyecto si el árbol integrado coincide exactamente con el árbol ya verificado (o reejecutándolo si el merge con `main` introduce cambios). Publica `main` y la etiqueta anotada mediante un único push atómico. Un fallo anterior al push conserva la rama y el árbol originales. Respeta además las políticas de `task_config.yaml::release.restricciones` para `validar`, `cerrar_local`, `etiquetar` y `publicar`.
- Tras éxito queda en `main`. Eliminar la rama release cerrada con `git branch -d release/vX.Y`.
- Para hotfix, si hay una release abierta, integrar después el fix en ella y publicar esa rama como antes.

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
