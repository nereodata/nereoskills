---
name: task-list
description: Generar el backlog técnico asignable a equipos/agentes en formato JSON.
---

# Skill: Generación de Lista de Tareas (/task-list)

Este flujo se encarga de transformar el plan de trabajo y la arquitectura en un backlog técnico estructurado para procesamiento automatizado.

**Objetivo:** Generar el backlog técnico asignable a equipos/agentes.

**Documentación necesaria:**
- `requirements.md`
- `req_analysis.md`
- `needs_analysis.md`
- `platform_plan.md`
- `work_plan.md`

## Proceso

Basándote en Plan de Trabajo + Arquitectura:

1. Generar JSON: tareas técnicas finales (accionables para agentes).
2. **Cada tarea**: `id_tarea`, `descripcion`, `equipo_asignado` (tech stack, no "dev/tester/reviewer").
3. **Devolución**: JSON puro sin markdown ni explicaciones.

```json
{
  "lista_de_tareas": [
    {
      "id_tarea": 1,
      "descripcion": "...",
      "equipo_asignado": "Tech stack"
    }
  ]
}
```

