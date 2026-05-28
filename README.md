# Workflows — AI Agent Workflows & Skills

Este repositorio centraliza los **agentes**, **skills** y **workflows** reutilizables para herramientas de IA (Claude Code, Cursor, Antigravity, etc.) que siguen el estándar **Issue-as-Code distribuido v3.0**.

La arquitectura separa **conocimiento** (skills) de **ejecución** (agentes): las skills definen procesos, criterios y playbooks de orquestación; los agentes son los especialistas que ejecutan cada fase. El hilo principal del runtime actúa como coordinador, leyendo el playbook (skill) y delegando cada paso al agente indicado.

> **Modo de uso previsto:** este repo se integra como un **submódulo Git** en la carpeta `.agents/` de cualquier proyecto consumer. Cada runtime (Claude Code, Cursor, etc.) enlaza a los agentes y skills mediante su propio mecanismo de descubrimiento.

---

## Arquitectura: Agentes + Skills

### Agentes — El Equipo

| Agente | Rol | Skills que usa |
|--------|-----|---------------|
| **Cronos** | Gestor de tareas — crea, actualiza, estima, prioriza y cierra tareas y bugs | task-add, bug-add, task-list |
| **Atenea** | Analista — entiende requisitos, aclara con el usuario, define BDD y evals | generate-bdd, req-analysis |
| **Artemisa** | Desarrollador — implementa step definitions, tests unitarios y lógica de negocio | (código directo) |
| **Hades** | QA — revisa especificación, tests y código en contexto aislado, con bucle de auto-corrección | review-spec, review-test, review-code |
| **Clío** | Documentalista — actualiza docs, changelog y genera commits semánticos | manage-docs, commit |

La **coordinación** la realizan las skills de orquestación (`task-dev`, `bug-fix`) ejecutadas por el hilo principal del runtime, que actúa como director y gestiona los HITL.

### Flujo de Desarrollo

```
Usuario: /task-dev T-APX-XXXX   (tarea padre — foco Product Owner)
  │
  └─ Hilo principal (coordinador, lee skill task-dev/bug-fix)
       ├─ @cronos   → inicializa padre + todas las hijas (status, esfuerzo, versión)
       ├─ @atenea   → especificación de TODOS los componentes (BDD + evals)
       │               → presentación consolidada para revisión ágil
       ├─ @hades    → review-spec (auto-corrección ×3 con @atenea)
       ├─ [HITL: validación de especificación — consolidada, a nivel padre]
       ├─ @artemisa → fase roja (step defs + unit tests, fallan)
       ├─ @hades    → review-test (auto-corrección ×3 con @artemisa)
       ├─ @artemisa → fase verde (implementación, tests pasan)
       ├─ [HITL: validación funcional — todo junto]
       ├─ @hades    → review-code (auto-corrección ×3 con @artemisa)
       ├─ @clio     → documentación + commit
       └─ @cronos   → cierra todas las hijas + la padre
```

> Cada vez que un agente produce un artefacto, Hades lo revisa antes de avanzar: especificación (review-spec), tests (review-test) y código (review-code). La misma lógica aplica a tareas y a bugs — en bugs solo cambia el contexto, y las fases sin cambios se omiten.

### Principios de diseño

- **Agnóstico de runtime**: las skills no mencionan mecanismos de ninguna herramienta concreta. Los agentes usan vocabulario estándar (`isolation: worktree`) que cada runtime mapea a sus capacidades.
- **Separación de contexto cognitivo**: Hades opera sin acceso al historial de desarrollo, eliminando sesgo de confirmación. Nadie revisa su propio trabajo — ni Atenea su especificación, ni Artemisa su código.
- **Composabilidad**: las skills de orquestación componen agentes y skills reutilizables. Añadir un nuevo flujo es crear una skill-playbook que reutiliza los mismos agentes.
- **Auto-corrección**: Hades implementa un bucle cerrado de hasta 3 iteraciones. Solo escala al humano si no converge.
- **Estado del flujo externo**: el coordinador mantiene un checklist explícito de fases (no en memoria de contexto, que se diluye en flujos largos). Lo consulta entre cada paso. Los HITL son ítems del checklist: si se difieren, quedan abiertos hasta realizarse — protege contra el olvido de fases.

### HITL (Human-in-the-Loop)

El hilo principal gestiona exactamente 2 puntos de parada humana:

| Punto | Propósito |
|-------|-----------|
| **Post-especificación** (tras Atenea) | Validar que las BDD y evals consolidadas capturan correctamente el requisito/fallo de toda la tarea padre |
| **Post-implementación** (tras Artemisa) | Validar integración visual, UX y efectos secundarios del conjunto, no cubiertos por tests |

### Trabajo a nivel de tarea padre

El Product Owner trabaja siempre sobre la **tarea/bug padre** (el objetivo atómico con valor para el usuario). El flujo es único aunque la tarea afecte a varios componentes:

- **Atenea** presenta la especificación de todos los componentes de forma **consolidada** — un resumen único de todas las BDD y evals, para revisión ágil en un solo HITL.
- Los HITL son a nivel padre, agrupados (una validación de especificación, una validación funcional).
- **Cronos** traduce padre ↔ hijas: reparte estado, esfuerzo y cierre entre las tareas hijas (una por componente), que son unidades de contabilidad, no flujos separados.
- La implementación de varios componentes puede paralelizarse internamente (independientes) o secuenciarse (dependientes), pero es un detalle de ejecución invisible para el PO.

**Component Mode** (`T-[PRJ]-[COMP]-XXXX`) existe como atajo de desarrollador para trabajar una hija suelta, pero el foco de producto es siempre la padre.

---

## Estructura del Repositorio

```
Workflows/
├── agents/                # Agentes (cómo orquestar)
│   ├── atenea.md          # Analista
│   ├── artemisa.md        # Desarrollador
│   ├── cronos.md          # Gestor de tareas
│   ├── hades.md           # QA (contexto aislado)
│   └── clio.md            # Documentalista
├── skills/                # Skills (qué hacer — conocimiento puro)
│   ├── task-dev/          # Proceso de desarrollo de tareas
│   ├── bug-fix/           # Proceso de resolución de bugs
│   ├── generate-bdd/      # Genera feature files Gherkin en español
│   ├── review-spec/       # Auditoría de la especificación (BDD + evals)
│   ├── review-code/       # Auditoría de código (8 áreas, puntuación 1-10)
│   ├── review-test/       # Auditoría de suite de tests
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
| `review-spec` | Auditoría de la especificación: claridad, completitud y testeabilidad de BDD + evals |
| `review-code` | Auditoría de código: Seguridad, Arquitectura, Eficiencia, Testeabilidad, etc. |
| `review-test` | Auditoría de suite de tests: cobertura BDD, aislamiento, integración |
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
📋 Init          → Cronos:   status, esfuerzo, versión
📝 Especificación → Atenea:   escenarios BDD + evals
🔎 review-spec   → Hades:    audita especificación (aislado, ×3)
                 ↓ [HITL: validación de especificación]
🔴 Red           → Artemisa: step definitions, evals, unit tests (fallan)
🔎 review-test   → Hades:    audita calidad de tests (aislado, ×3)
🟢 Green         → Artemisa: implementación (tests pasan)
                 ↓ [HITL: validación funcional]
🔎 review-code   → Hades:    audita calidad de código (aislado, ×3)
📄 Docs          → Clío:     /manage-docs + /commit
✅ Cierre        → Cronos:   esfuerzo real, cierre de tarea
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
