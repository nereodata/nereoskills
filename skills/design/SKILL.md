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

### 3. Mapa de impacto

Obligatorio cuando el cambio altera la **firma**, la **semántica** o el **conjunto de resultados**
de una función compartida, un esquema de datos o un contrato de API. Es enumeración mecánica, no
juicio: se resuelve buscando, no recordando.

- **Llamantes.** Enumera los consumidores de cada elemento que cambia y di, para cada uno, si
  quiere el comportamiento nuevo o el anterior. Presta atención especial a los que **escriben con
  lo que leen**: ensanchar el resultado de una consulta que alimenta una operación de escritura
  cambia lo que esa operación modifica, y eso es corrupción de datos, no un cambio de lectura.
- **Escenarios afectados.** Enumera los escenarios y tests existentes que cambian de
  comportamiento o quedan invalidados. **Si un test que hoy pasa tendrá que modificarse, eso es un
  cambio de contrato**: nómbralo aquí y di qué se hace con él. No es un paso de la implementación.
- **Decisiones contradichas.** Declara toda decisión ya documentada que este diseño contradiga,
  con `archivo:línea`. Si no hay ninguna, dilo explícitamente.
- **Sistema de referencia.** Si el comportamiento depende de una unidad o referencia (zona
  horaria, moneda, locale, unidad de medida), indica cuál se usa y en qué frontera se convierte.
- **Camino caliente.** Si el cambio toca una consulta o una ruta de ejecución frecuente, indica
  **cómo se comprobará** que no degrada (plan de consulta, medición). Por intuición no cuenta.

Una regla nueva vive en **un solo sitio**. Si aparece replicada en varias capas o lenguajes,
extráela; tres copias divergen y ningún test falla cuando se olvida una.

### 4. Documento [`docs/design/[ID]-design.md`]
```markdown
# Diseño Técnico: [ID] - [Título]

## 🏗️ Arquitectura
- Componentes modificados/creados.

## 🛠️ Cambios
- **[NEW]** `ruta` (objetivo).
- **[MODIFY]** `ruta` (cambios).
- **[DELETE]** `ruta` (si aplica).

## 🎯 Mapa de impacto
- Llamantes de lo que cambia y qué versión quiere cada uno.
- Escenarios/tests afectados o invalidados (y qué se hace con ellos).
- Decisiones documentadas que se contradicen (`archivo:línea`), o "ninguna".
- Sistema de referencia y frontera de conversión (si aplica).
- Cómo se comprobará que no degrada el camino caliente (si aplica).

## 🧩 Patrones
- SOLID, DRY, etc. + firmas críticas.

## 🧪 Testeabilidad
- Cómo aislar lógica (mocks, fixtures).
```
