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
- `dificultad`: `sencilla | media | dificil` (por defecto `media`). Criterio conciso de asignación:
  - `sencilla`: contenido declarativo, documentación, configuración o cambio mecánico localizado.
  - `media`: funcionalidad o corrección estándar en uno o pocos módulos.
  - `dificil`: algoritmos complejos, concurrencia, seguridad crítica o cambio transversal multi-componente.
  Si un bug preexistente no declara `dificultad`, se trata por defecto como `media`.
- `perfil`: (Opcional, solo lo fija una persona) arnés, modelo y esfuerzo con que se ejecuta este bug, en lugar del perfil por dificultad. Perfil único, para el rol que ejecuta el paso (Artemisa en `task-dev` y `bug-fix`): `perfil: {harness: claude, model: claude-opus-5-5, effort: high}`. Por rol, para fijar también la revisión, la especificación o la documentación de este bug: `perfil: {artemisa: {...}, hades: {...}, atenea: {...}}`. Lo que falte se toma del perfil por dificultad. Con `estricto: true` no se cambia de modelo: se espera la cuota y, si el arnés no existe o no avanza, se bloquea. Sin el campo manda `orchestration.json`. Un `perfil` inválido (arnés, esfuerzo o rol desconocidos) para el bucle con el error.

**Deuda registrada** (hallazgo de Hades con destino `registrar`): es un bug, porque es algo que la tarea de origen debía resolver y no resolvió. Va **sin versión** aunque se registre en una rama `release/`, con `status: backlog`, `weight` > 1000 y `origen` con el ID y el reporte. Queda fuera de la versión en curso hasta que una revisión de deuda la incluya.

### 3. Archivo [`[ID]-descripcion-corta.md`]
```markdown
---
id: B-[PRJ]-XXXX
title: "Título"
type: bug
weight: [int]
dificultad: sencilla | media | dificil
# perfil: {harness: claude, model: claude-opus-5-5, effort: high}  (opcional, solo una persona)
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
