---
name: bug-add
description: Registro de una nueva anomalía (bug) siguiendo el estándar Issue-as-Code
inputs:
  - title: Título del bug
  - parent_id: (Opcional) ID del bug maestro si es de componente
outputs:
  - bug_id: ID del bug generado
---

# Skill: Registro de Anomalía (/bug-add)

Registra un nuevo bug en el backlog siguiendo el estándar Issue-as-Code v3.0.

## 📋 Pasos

### 1. Clasificar
- **Master** (múltiples componentes o producción): `docs/plan/bugs/` → `B-[PRJ]-XXXX`.
- **Componente** (bug localizado): Path en `task_config.yaml` → `B-[PRJ]-[COMP]-XXXX`.

### 2. Metadatos
- `status: backlog` o `planned` (si rama release/hotfix).
- `version`: Auto-detectado de rama o vacío.
- `weight`: 0-10 crítico, 10-100 prioritario, 100-1000 normal.
- Fechas: `created_at`, `updated_at`.

### 3. Archivo [`[ID]-descripcion-corta.md`]
```markdown
---
id: B-[PRJ]-[COMP]-XXXX
title: "Título"
type: bug
weight: [int]
version: ""
status: backlog
estimated_effort: 0
created_at: YYYY-MM-DD
parent_id: [Master ID si aplica]
---

# [ID]: [Título]

## 🎯 Descripción del Fallo
Causa raíz, comportamiento observado vs esperado

## 📋 Reproducir
1. Paso 1
2. Paso 2

## 📋 Evidencias
- Imágenes en `assets/`
```
