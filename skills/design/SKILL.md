---
name: design
description: Diseña la solución técnica a implementar a partir de la especificación BDD y el código existente.
inputs:
  - id: ID de la tarea/bug (ej. T-PRJ-XXXX, B-PRJ-XXXX)
  - component: Componente afectado
outputs:
  - design_file: Ruta del documento de diseño técnico generado
---

# Skill: Diseño Técnico (/design)

Define el diseño técnico detallado de los cambios antes de comenzar la implementación. Garantiza que la solución sea limpia, testeable y alineada con la arquitectura del proyecto.

## 📋 Pasos

### 1. Analizar
- Escenarios BDD (`.feature`) + especificación aprobada.
- Código actual: clases/funciones existentes (evitar duplicación).

### 2. Diseñar
- Archivos: `[NEW]`, `[MODIFY]`, `[DELETE]`.
- Estructura: SOLID, DRY, KISS, YAGNI, cohesión alta, acoplamiento bajo.
- **Testeabilidad**: Inyección de dependencias, mocks.

### 3. Documento [`docs/design/[ID]-design.md`]
```markdown
# Diseño Técnico: [ID] - [Título]

## 🏗️ Arquitectura
- Componentes modificados/creados.

## 🛠️ Cambios
- **[NEW]** `ruta` (objetivo).
- **[MODIFY]** `ruta` (cambios).
- **[DELETE]** `ruta` (si aplica).

## 🧩 Patrones
- SOLID, DRY, etc. + firmas críticas.

## 🧪 Testeabilidad
- Cómo aislar lógica (mocks, fixtures).
```
