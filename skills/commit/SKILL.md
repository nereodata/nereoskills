---
name: commit
description: Genera y ejecuta un commit semántico a partir de los cambios detectados
inputs:
  - msg: (Opcional) Mensaje personalizado
outputs:
  - commit_sha: SHA del commit generado
---

# Skill: Commit Inteligente (/commit)

Agrupa y registra cambios de forma funcional y estructurada.

## 📋 Pasos

### 1. Validar
- Rama: `release/vX.Y` o `hotfix/vX.Y.Z` (advertir si es `main`).

### 2. Agrupar y Proponer
- Cambios por funcionalidad/componente.
- **Mensaje**: `<type>(<scope>): [ID] - <subject>`
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `perf`.
  - Scope: `plan`, `config`, `api`, `ui`, `backend`, paquete.
  - ID: Tarea/bug (ej. T-APX-0001).
  - Body: Descripción técnica + refs (ej. Ref: T-APX-0001, RF-204).

### 3. Ejecutar
- Presentar propuesta → aprobación → `git add` + `git commit` → limpiar temporales.
