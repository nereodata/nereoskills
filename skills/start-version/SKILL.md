---
name: start-version
description: Inicializa un nuevo bloque funcional creando la rama release y actualizando versiones en todos los manifiestos
---

# Skill: Iniciar Versión (/start-version-workflow)

Esta skill formaliza la apertura de un nuevo bloque funcional (release), creando la rama de trabajo y sincronizando la versión target en todos los manifiestos del monorepo.

> **Modo orquestado** (invocada desde `/orquestar`): la versión target es la indicada, sin preguntar. Si no hay releases previas (sin tags), no se exige que `main` esté en un tag.

## Pasos de la Skill

### 1. Validación Previa
- Verificar que la rama activa es `main`.
- Verificar que no hay cambios pendientes (staged, unstaged o untracked relevantes).
- Verificar que `main` está en el tag de la última release (ej. `git describe --tags --exact-match HEAD`).
- Si alguna validación falla, informar al usuario y detenerse.

### 2. Determinación de la Versión Target
- Leer la versión actual de `task_config.yaml` → `project.version`.
- Solicitar al usuario la versión target (ej. `v1.2`). Si no la proporciona, sugerir el incremento Minor automático.
- Validar que el formato es `vX.Y` (sin patch, el patch siempre arranca en `.0`).
- Validar que la versión target es superior a la actual.

### 3. Creación de la Rama
- Crear la rama: `git checkout -b release/vX.Y`.
- Confirmar al usuario que se ha creado la rama.

### 4. Bump de Versión en Manifiestos
Actualizar la versión a `X.Y.0` (o `vX.Y.0` según el formato de cada fichero) en:

| Fichero | Campo | Formato |
|---------|-------|---------|
| `task_config.yaml` | `project.version` | `"vX.Y.0"` |
| `app/package.json` | `version` | `"X.Y.0"` (sin `v`) |
| `services/orchestrator/pyproject.toml` | `[project].version` | `"X.Y.0"` (sin `v`) |
| `services/context/pyproject.toml` | `[project].version` | `"X.Y.0"` (sin `v`) |
| `packages/licensing/pyproject.toml` | `[project].version` | `"X.Y.0"` (sin `v`) |

**Importante**: Antes de editar, verificar que cada fichero existe. Si se detectan manifiestos adicionales con campo `version`, incluirlos.

### 5. Commit Inicial
- Stage de todos los ficheros modificados.
- Commit: `chore(release): start version vX.Y.0`
- **No hacer push**. Informar al usuario de que puede hacerlo cuando quiera.

### 6. Resumen
- Mostrar al usuario:
  - Rama creada: `release/vX.Y`
  - Versión anterior: `vA.B.C`
  - Versión nueva: `vX.Y.0`
  - Ficheros actualizados (lista)
  - Recordatorio: las tareas asignadas a `vX.Y` ya pueden trabajarse en esta rama.
