---
name: bug-add
description: Registro de una nueva anomalía (bug) siguiendo el estándar Issue-as-Code
inputs:
  - title: Título del bug
  - parent_id: (Opcional) ID del bug maestro si es de componente
  - origen: (Opcional) ID de la tarea o bug y reporte de Hades, si es deuda registrada
outputs:
  - bug_id: ID del bug generado
---

# Skill: Registro de Anomalía (/bug-add)

Registra un nuevo bug en el backlog siguiendo el estándar Issue-as-Code v3.0.

## 📋 Pasos

### 1. Clasificar
- **Master**: `docs/plan/bugs/` → `B-[PRJ]-XXXX`.
- **Componente**: solo si el bug necesita descomponerse en bloques que conviene tratar por separado (ver hijas en `/task-add`). Path en `task_config.yaml` → `B-[PRJ]-[COMP]-XXXX`.

### 2. Metadatos
- `status: backlog` o `planned` (si rama release/hotfix).
- `version`: Auto-detectado de rama o vacío.
- `weight`: 0-10 crítico, 10-100 prioritario, 100-1000 normal, > 1000 mejora (deuda registrada).
- Fechas: `created_at`, `updated_at`.

**Deuda registrada** (hallazgo de Hades con destino `registrar`): es un bug, porque es algo que la tarea de origen debía resolver y no resolvió. Va **sin versión** aunque se registre en una rama `release/`, con `status: backlog`, `weight` > 1000 y `origen` con el ID y el reporte. Queda fuera de la versión en curso hasta que una revisión de deuda la incluya.

### 3. Archivo [`[ID]-descripcion-corta.md`]
```markdown
---
id: B-[PRJ]-XXXX
title: "Título"
type: bug
weight: [int]
version: ""
status: backlog
created_at: YYYY-MM-DD
parent_id: [Master ID si es de componente]
origen: [ID y reporte, si es deuda registrada]
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
