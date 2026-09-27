---
name: platform-plan
description: Decidir la arquitectura y el stack mínimos que cumplen los requisitos, en proporción al tamaño del producto.
---

# Skill: Plan de Plataforma (/platform-plan)

**Objetivo:** Decidir la arquitectura y el stack mínimos que cumplen los requisitos, para que `/work-plan` pueda crear las tareas.

**Documentación necesaria:**
- `requirements.md` (incluye el tamaño del producto y las entradas técnicas detectadas).
- `req_analysis.md`.

## Proceso

1. **Necesidades que condicionan**: solo las que cambian una decisión (volumen, datos, disponibilidad, datos personales y cumplimiento normativo, dependencias externas). Verifica en la web los límites, costes y términos de las dependencias externas. Cifras con base; si no la hay, supuesto declarado.
2. **Opciones**: las 2-3 arquitecturas más lógicas para este producto concreto. Decide una, di por qué y qué te haría cambiar de opinión. Si eliges algo propietario, el lock-in forma parte del porqué.
3. **Stack**: ningún componente sin una necesidad que lo justifique. Por defecto, lo más simple que funcione para el tamaño declarado.

## Salida: `platform_plan.md`

En el mismo directorio que los ficheros de entrada:
- **Necesidades**: tabla breve (necesidad | valor | por qué condiciona).
- **Opciones y decisión**.
- **Stack**: tabla (capa | elección | necesidad que cubre).
- **Estructura del código y reglas de capas** (si aplica).
- **Estrategia de pruebas**: niveles y herramientas.
- **Pasos manuales** que requieren a una persona.
- **Decisiones** (`DEC-xx`).

Lo justo para que `/work-plan` cree las tareas y `/design` diseñe: sin tutoriales, sin versiones de paquetes (salvo incompatibilidad conocida) y sin comparar tipos genéricos de arquitectura.
