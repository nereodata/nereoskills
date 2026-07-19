---
name: task-add
description: Añade una nueva tarea al backlog del producto siguiendo estándares de Issue-as-Code v3.0
inputs:
  - title: Título de la tarea
  - parent_id: (Opcional) ID de la tarea maestra si es de componente
outputs:
  - task_id: ID de la tarea generada
---

# Skill: Añadir Tarea al Backlog (/task-add)

Crea y registra una nueva tarea de backlog siguiendo el formato Issue-as-Code v3.0.

## 🎯 Qué es una Tarea Padre

Una **tarea padre representa una única capacidad, mejora o cambio que un usuario percibe como valioso por sí mismo** — la unidad mínima entregable. **Prueba rápida:** si describes el resultado con "permite X **y además** Y", probablemente sean varias tareas padre, no una. Agrupar por afinidad ("todo el login") es una épica difusa; cuando dudes, separa.

**Tareas hijas** (Componente) son la descomposición técnica entre componentes. Un cambio de 3 componentes, un solo valor de usuario → una padre + 3 hijas.

## 📋 Pasos de la Skill

### 1. Clasificación e Identificación de Destino
- **Master**: Si representa una capacidad o valor del usuario final.
  - Ruta: `docs/plan/tasks/` (según `task_config.yaml`).
  - ID: `T-[PRJ]-XXXX` (autoincremental).
- **Componente**: Descomposición técnica del cambio para un componente.
  - Ruta: Definida en `task_config.yaml` para el componente (service, app o package).
  - ID: `T-[PRJ]-[COMP]-XXXX` (autoincremental). Debe vincularse a su Master (`parent_id`).

### 2. Inicialización de Metadatos
- `status: backlog` (por defecto) o `planned` (si se especifica versión).
- `version`: Vacío por defecto, o detectado automáticamente de la rama `release/vX.Y` (ej: `"vX.Y.0"`).
- Establecer fechas `created_at` y `updated_at`.

### 3. Plantillas de Archivos
Crear un archivo markdown `[ID]-descripcion-corta.md` en la ruta correspondiente:

**Para Tarea Maestra (Master):**
```markdown
---
id: T-[PRJ]-XXXX
title: "Título descriptivo"
type: funcional | despliegue | diseño | tools | infra
weight: [integer]
version: ""
status: backlog
effort_unit: h
estimated_effort: 0
remaining_effort: 0
actual_effort: 0
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
---

# [ID]: [Título]

## 🎯 Objetivo de Negocio
[Descripción del valor de negocio]

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1:** [Criterio]

## 🛠 Tareas de Componente
- [T-[PRJ]-[COMP]-XXXX: Título]
```

**Para Tarea de Componente:**
```markdown
---
id: T-[PRJ]-[COMP]-XXXX
title: "Título técnico"
type: feature | enhancement | refactor | technical-debt
parent_id: T-[PRJ]-XXXX
weight: [integer]
version: ""
status: backlog
effort_unit: h
estimated_effort: 0
remaining_effort: 0
actual_effort: 0
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
---

# [ID]: [Título]

## 🔗 Tarea Maestra
- [T-[PRJ]-XXXX: Título Maestros](../../../docs/plan/tasks/T-[PRJ]-XXXX.md)

## 🎯 Objetivo Técnico
[Descripción técnica]

## 📋 Criterios de Aceptación (BDD)
- [ ] **CA-1:** Escenario: [Descripción]
```
