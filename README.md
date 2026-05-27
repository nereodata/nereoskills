# Workflows — AI Agent Workflows & Skills

Este repositorio centraliza los **agentes**, **skills** y **workflows** reutilizables para herramientas de IA (Claude Code, Cursor, Antigravity, etc.) que siguen el estándar **Issue-as-Code distribuido v3.0**.

La arquitectura separa **conocimiento** (skills) de **ejecución** (agentes): las skills definen el "qué hacer" de forma agnóstica; los agentes deciden el "cómo", incluyendo aislamiento, paralelización y delegación.

> **Modo de uso previsto:** este repo se integra como un **submódulo Git** en la carpeta `.agents/` de cualquier proyecto consumer. Cada runtime (Claude Code, Cursor, etc.) enlaza a los agentes y skills mediante su propio mecanismo de descubrimiento.

---

## Arquitectura: Agentes + Skills

### Agentes — El Equipo

| Agente | Rol | Skills que usa |
|--------|-----|---------------|
| **Hermes** | Coordinador — recibe tareas/bugs, analiza dependencias, delega a los demás, gestiona HITL | task-dev, bug-fix |
| **Cronos** | Gestor de tareas — crea, actualiza, estima, prioriza y cierra tareas y bugs | task-add, bug-add, task-list |
| **Atenea** | Analista — entiende requisitos, aclara con el usuario, define BDD y evals | generate-bdd, review-test |
| **Artemisa** | Desarrollador — implementa step definitions, tests unitarios y lógica de negocio | (código directo) |
| **Hades** | QA — revisa en contexto aislado, sin historial previo, con bucle de auto-corrección | review-code, review-test, review-fix |
| **Clío** | Documentalista — actualiza docs, changelog y genera commits semánticos | manage-docs, commit |

### Flujo de Desarrollo

```
Usuario
  │
  └─ Hermes (coordinador)
       ├─ Cronos → inicialización (status, esfuerzo, versión)
       ├─ Atenea → especificación (escenarios BDD a nivel feature + evals)
       ├─ [HITL: validación de escenarios]
       ├─ Artemisa → Red (step definitions, evals, unit tests)
       │            → Green (implementación hasta que todo pase)
       ├─ [HITL: validación funcional]
       ├─ Hades → QA aislado (auto-corrección ×3)
       │    └─ Si rechaza → Artemisa corrige → Hades re-evalúa
       ├─ Clío → documentación + commit
       └─ Cronos → cierre (esfuerzo real, status completed)
```

### Principios de diseño

- **Agnóstico de runtime**: las skills no mencionan mecanismos de ninguna herramienta concreta. Los agentes usan vocabulario estándar (`isolation: worktree`) que cada runtime mapea a sus capacidades.
- **Separación de contexto cognitivo**: Hades (QA) opera sin acceso al historial de desarrollo, eliminando sesgo de confirmación.
- **Composabilidad**: los agentes componen skills reutilizables. Añadir un nuevo flujo es crear un agente que reutiliza las mismas piezas.
- **Auto-corrección**: Hades implementa un bucle cerrado de hasta 3 iteraciones. Solo escala al humano si no converge.

### HITL (Human-in-the-Loop)

Hermes gestiona exactamente 2 puntos de parada humana:

| Punto | Propósito |
|-------|-----------|
| **Post-Atenea** (Red Phase) | Validar que los tests capturan correctamente el requisito/fallo |
| **Post-Artemisa** (Green Phase) | Validar integración visual, UX y efectos secundarios no cubiertos por tests |

### Paralelización (Master Mode)

Cuando una tarea o bug afecta a múltiples componentes independientes, Hermes lanza un Artemisa por componente en contextos aislados con copia independiente del código. Si hay dependencias entre componentes, se ejecutan secuencialmente.

---

## Estructura del Repositorio

```
Workflows/
├── agents/                # Agentes (cómo orquestar)
│   ├── hermes.md          # Coordinador
│   ├── atenea.md          # Analista
│   ├── artemisa.md        # Desarrollador
│   ├── cronos.md          # Gestor de tareas
│   ├── hades.md           # QA (contexto aislado)
│   └── clio.md            # Documentalista
├── skills/                # Skills (qué hacer — conocimiento puro)
│   ├── task-dev/          # Proceso de desarrollo de tareas
│   ├── bug-fix/           # Proceso de resolución de bugs
│   ├── generate-bdd/      # Genera feature files Gherkin en español
│   ├── review-code/       # Auditoría de código (8 áreas, puntuación 1-10)
│   ├── review-test/       # Auditoría de suite de tests
│   ├── review-fix/        # Verificación de bug fixes
│   ├── manage-docs/       # Gestión de documentación según docs_config.yaml
│   ├── commit/            # Commit semántico multi-agrupado
│   ├── task-add/          # Registro de tareas (Issue-as-Code)
│   ├── bug-add/           # Registro de anomalías (Issue-as-Code)
│   ├── req-analysis/      # Análisis de requisitos funcionales
│   ├── needs-analysis/    # Análisis técnico y NFRs
│   ├── platform-plan/     # Arquitectura y stack tecnológico
│   ├── work-plan/         # Estrategia de desarrollo y planificación
│   ├── task-list/         # Backlog técnico en formato JSON
│   ├── release/           # Gestión de versiones y tagging
│   ├── start-version/     # Inicialización de bloque funcional
│   └── commit-message-generate/  # Generador de mensajes de commit
├── workflows/             # Proxies para slash commands
│   ├── task-dev.md
│   ├── bug-fix.md
│   └── ...
└── README.md
```

---

## Skills

Las skills son conocimiento puro — definen procesos, criterios y estándares. No contienen lógica de orquestación ni mecanismos de runtime.

| Skill | Responsabilidad |
|-------|-----------------|
| `task-dev` | Proceso y fases para desarrollo de tareas (Master/Componente) |
| `bug-fix` | Proceso y fases para resolución de anomalías |
| `generate-bdd` | Genera feature files Gherkin en español |
| `review-code` | Auditoría de código: Seguridad, Arquitectura, Eficiencia, Testeabilidad, etc. |
| `review-test` | Auditoría de suite de tests: cobertura BDD, aislamiento, integración |
| `review-fix` | Verificación de correcciones de bugs |
| `manage-docs` | Gestión de documentación según `docs_config.yaml` |
| `commit` | Generación de commits semánticos con trazabilidad |
| `task-add` | Registro de tareas (Issue-as-Code v3.0) |
| `bug-add` | Registro de anomalías (Issue-as-Code v3.0) |
| `req-analysis` | Análisis de ambigüedades y conflictos en requisitos |
| `needs-analysis` | Cuantificación de NFRs, compliance y viabilidad |
| `platform-plan` | Definición de arquitectura e infraestructura |
| `work-plan` | Estrategia de desarrollo y creación de tareas |
| `task-list` | Backlog técnico en formato JSON |
| `release` | Gestión de versiones, bumping y tagging |
| `start-version` | Inicialización de bloque funcional (rama release) |

---

## Workflows

Proxies que mapean slash commands a skills. El nombre del archivo determina el comando: `task-dev.md` → `/task-dev`.

---

## Estándares

### Issue-as-Code Distribuido v3.0

Cada componente es dueño de su propio backlog. Las tareas maestras en `docs/plan/` dan visibilidad global; las de componente viven junto al código.

### Estructura de IDs

```
T-[PRJ]-XXXX             # Tarea Maestra
T-[PRJ]-[COMP]-XXXX       # Tarea de Componente
B-[PRJ]-XXXX             # Bug Maestro
B-[PRJ]-[COMP]-XXXX       # Bug de Componente
```

### BDD — Regla de Idioma

```gherkin
# language: es
Característica: Título en español
  Escenario: Descripción en español
    Dado que ...
    Cuando ...
    Entonces ...
```

### Flujo de Desarrollo Estándar

```
📋 Init Phase  → Cronos: status, esfuerzo, versión
🔴 Red Phase   → Atenea: escenarios BDD + evals (especificación)
              ↓  /review-test (mínimo 8/10)
              ↓  [HITL: validación de escenarios]
              → Artemisa: step definitions, evals, unit tests (código)
🟢 Green Phase → Artemisa: implementación
              ↓  [HITL: validación funcional]
🔵 QA Phase    → Hades: revisión aislada (auto-corrección ×3)
              ↓
📄 Sync Phase  → Clío: /manage-docs + /commit
              ↓
✅ Close Phase → Cronos: esfuerzo real, cierre de tarea
```

### Política de Versionado y Estrategia de Ramas

Definidas en [branch_strategy.md](./branch_strategy.md).

---

## Integración en proyectos consumer

### 1. Añadir el submódulo

```bash
git submodule add https://github.com/imoremu/Wokflows.git .agents
```

### 2. Enlazar para Claude Code

```bash
ln -s ../.agents/skills .claude/skills
ln -s ../.agents/agents .claude/agents
```

### 3. Estructura resultante

```
mi-proyecto/
├── .agents/                         ← submódulo (este repo)
│   ├── agents/                      ← agentes (orquestación)
│   ├── skills/                      ← skills (conocimiento)
│   └── workflows/                   ← proxies slash commands
├── .claude/
│   ├── skills -> ../.agents/skills  ← symlink
│   └── agents -> ../.agents/agents  ← symlink
├── task_config.yaml                 ← configuración específica del proyecto
├── src/
└── docs/
```

### 4. Actualizar a la última versión

```bash
git submodule update --remote .agents
git add .agents
git commit -m "chore(agent): update workflows to latest"
```

### 5. Configurar `task_config.yaml`

```yaml
project:
  prefix: PRJ
  name: Mi Proyecto

levels:
  master:
    id_prefix: ""
    path: docs/plan/
    folders:
      tasks: tasks/
      bugs: bugs/
  components:
    - type: service
      id_prefix: SRV
      path: services/{name}/docs/backlog/
      folders:
        tasks: tasks/
        bugs: bugs/
```

> `task_config.yaml` es propio de cada proyecto y no forma parte de este repositorio.
