---
name: task-add
description: Añade una nueva tarea al backlog del producto siguiendo estándares de Issue-as-Code v3.0
---

# Skill: Añadir Tarea al Backlog (/task-add)

Este flujo (ahora skill) permite registrar tareas pendientes en el backlog del producto, siguiendo el estándar **Issue-as-Code distribuido v3.0 (Master/Componente)**.

## Qué es una Tarea Padre (Master)

Una **tarea padre representa una única capacidad, mejora o cambio que un usuario percibe como valioso por sí mismo**. Es la **unidad mínima entregable de valor**: lo más pequeño que se puede completar y que un usuario reconocería como *"ahora puedo hacer X"* o *"esto ahora funciona mejor"*.

- Es **atómica desde el punto de vista del usuario**: describe un solo resultado con valor, no un conjunto de resultados.
- Sus **tareas hijas (Componente)** son la descomposición *técnica* de ese mismo objetivo entre los componentes que hay que tocar (HMI, servicio, paquete...). Todas las hijas sirven al **mismo** valor de usuario.
- Un cambio que afecta a 3 componentes pero entrega un único valor de usuario → **una** tarea padre con 3 hijas.
- Dos valores de usuario distintos e independientes → **dos** tareas padre, cada una con sus hijas.

**Prueba rápida:** describe el resultado en una frase desde la perspectiva del usuario. Si necesitas la conjunción "y" para enumerar capacidades distintas (*"permite X y además Y y también Z"*), probablemente son varias tareas padre, no una. Una tarea padre se describe como **una sola cosa útil**.

Una tarea padre **no es** un contenedor temático ni un sitio donde agrupar trabajo afín ("todo lo del login", "mejoras de UI"). Agrupar por afinidad la convierte en una épica difusa y rompe la trazabilidad del valor. Cuando dudes entre agrupar o separar, separa: cada unidad de valor merece su propia tarea padre.

## Estructura del Backlog
El backlog se organiza de forma descentralizada. Así, para un proyecto dado habrá tareas de proyecto (padre), que se descomponen técnicamente en tareas de cada uno de los componentes implicados. Los componentes, a su vez, estarán divididos en:

- **Servicios (Backend)**: Servicios de backend
- **Apps (HMI)**: aplicaciones / interfaces de usuario
- **Paquetes (Soporte)**: paquetes de soporte al resto de elementos

En el archivo `task_config.yaml` se definen el prefijo del proyecto (`[PRJ]`), el prefijo de cada componente (`[COMP]`), las rutas base (`path`) y las subcarpetas de destino (`folders.tasks` y `folders.bugs`).

## Pasos de la Skill

### 1. Clasificación e Identificación de Destino (Task Namer)
- **Determinar el Escenario**:
   - Si la tarea es **Master**:
     - Cargar `task_config.yaml` y usar `levels.master.id_prefix`.
     - Ruta destino: `levels.master.path` + `levels.master.folders.tasks` (ej. `docs/plan/tasks/`).
   - Si la tarea es de **Componente**:
     - Identificar el tipo (app, service, package) en `task_config.yaml` (`levels.components`).
     - Asegurar que la tarea tiene `parent_id` apuntando a su Master correspondiente si aplica.
     - Usar el `id_prefix` del componente, su `path` y su `folders.tasks`. Si la ruta contiene `{name}`, usar el nombre específico del servicio/paquete proporcionado por el usuario.
- **Cálculo de ID Secuencial**:
   - Listar los archivos en el directorio de destino resuelto.
   - Buscar el ID más alto existente (`T-PRE-COMP-XXXX`).
   - Incrementar el número correlativo para el nuevo ID.
- **Formato de Salida**:
   - **ID**: `T-{prefix}-{comp_prefix}-{number}` (si no hay prefijo de componente, omitir el guion central).
   - **Archivo**: `[ID]-descripcion-corta.md` y crearlo en la Ruta Completa calculada.

### 2. Asignación de Metadatos
- Asignar **Peso (Weight)** según prioridad.
- **Estado y Versión por Defecto**:
    - `status: backlog`
    - `version: ""` (vacío)
- **Excepción (Asignación Explícita)**:
    - Si el usuario indica explícitamente una versión, establecer `status: planned` y `version: [versión proporcionada]`.
- **Asignación automática desde rama**:
    - Si la rama activa sigue el patrón `release/vX.Y`, proponer automáticamente `version: "vX.Y.0"` y `status: planned`.
    - El usuario puede rechazar la asignación automática (ej. para tareas que se dejan en backlog para futuras versiones).
- Establecer fechas de creación (`created_at`) y actualización (`updated_at`).

### 3. Creación del Archivo
**Nombre:** `[ID]-descripcion-corta.md`

**Formato para Tarea Maestra (Master):**
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
original_ref: [Legacy ID if any]
---

# [ID]: [Título]

## 🎯 Objetivo de Negocio
[Descripción del valor de negocio y el "qué" se quiere conseguir]

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1:** [Criterio de alto nivel]

## 🛠 Tareas de Componente
- [T-[PRJ]-[COMP]-XXXX: Título]
```

**Formato para Tarea de Componente:**
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
[Descripción técnica del cambio]

## 📋 Criterios de Aceptación (BDD)
- [ ] **CA-1:** Escenario: [Descripción]

## 🧪 Plan de Implementación (TDD)
- [ ] **Test 1:** [Descripción del test unitario]

## 🏗️ Implementación Técnica
[Detalles técnicos, módulos afectados, etc.]
```

### 4. Vinculación Master/Componente (Obligatoria)
- **Componente-> Master**: Es obligatorio incluir el `parent_id` en el frontmatter y un enlace en la sección `## 🔗 Tarea Maestra`.
- **Master -> Componente**: Es obligatorio listar las tareas técnicas en la sección `## 🛠 Tareas de Componente`.
- **Automatización**: Se puede ejecutar un script de sincronización si el repositorio cuenta con uno (ej. `link_tasks.py`).

