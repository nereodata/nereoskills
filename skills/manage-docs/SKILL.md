---
name: manage-docs
description: Gestión y actualización minimalista de la documentación del proyecto.
inputs:
  - task_id: ID de la tarea/bug
---

# Skill: Gestión de Documentación (/manage-docs)

Actualiza los documentos de proyecto configurados de forma concisa y directa.

## 📋 Pasos de la Skill

### 1. Cargar Configuración
- `docs_config.yaml` (o `README.md` por defecto).

### 2. Identificar e Integrar
- Documentos afectados por cambio.
- Integración minimalista, coherente, legible.

### 3. CHANGELOG (si existe)
```markdown
## [vX.Y.Z] - YYYY-MM-DD
### Added | Changed | Fixed
- [ID] - Resumen (Scope)
```
- MINOR: features | PATCH: fixes
