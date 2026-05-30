# Workflows — AI Agent Workflows & Skills

Este repositorio centraliza los **agentes**, **skills** y **workflows** reutilizables para herramientas de IA (Claude Code, Cursor, Antigravity, etc.) que siguen el estándar **Issue-as-Code distribuido v3.0**.

La arquitectura separa **conocimiento** (skills) de **ejecución**: las skills definen procesos, criterios y playbooks. El **hilo principal** ejecuta las fases productivas **inline** (manteniendo el contexto acumulado), y delega **únicamente la revisión** al agente aislado **Hades** — el único punto donde el aislamiento de contexto aporta valor (revisión sin sesgo de confirmación).

> **Por defecto: inline + Hades.** Los flujos `task-dev` y `bug-fix` NO delegan cada fase a un subagente. La separación de roles es de *fase*, no de *contexto*: fragmentar el trabajo en subagentes amnésicos cuesta arranques en frío y pérdida de contexto sin beneficio en tareas atómicas. Los demás agentes quedan disponibles para **invocación manual** del Product Owner cuando una tarea grande o multi-componente lo justifique (p. ej. paralelizar componentes independientes).

> **Modo de uso previsto:** este repo se integra como un **submódulo Git** en la carpeta `.agents/` de cualquier proyecto consumer. Cada runtime (Claude Code, Cursor, etc.) enlaza a los agentes y skills mediante su propio mecanismo de descubrimiento.

---

## Arquitectura: Agentes + Skills

### Agentes — El Equipo

| Agente | Rol | Skills que usa | Uso en `task-dev`/`bug-fix` |
|--------|-----|---------------|------------------------------|
| **Hades** | QA — revisa especificación, tests y código en contexto aislado, con bucle de auto-corrección | review-spec, review-test, review-code | **Delegado (aislado)** |
| **Cronos** | Gestor de tareas — crea, actualiza, estima, prioriza y cierra tareas y bugs | task-add, bug-add, task-list | Manual (init/cierre van inline) |
| **Atenea** | Analista — entiende requisitos, aclara con el usuario, define BDD | generate-bdd | Manual (spec va inline) |
| **Artemisa** | Desarrollador — implementa step definitions, tests unitarios y lógica de negocio | (código directo) | Manual (dev va inline) |
| **Clío** | Documentalista — actualiza docs, changelog y genera commits semánticos | manage-docs, commit | Manual (docs/commit van inline) |

La **coordinación y las fases productivas** las ejecuta el hilo principal inline (usando las skills `generate-bdd`, `manage-docs`, `commit`); solo **Hades** se delega, en contexto aislado. Los agentes marcados como "Manual" se invocan a mano cuando el Product Owner lo decide.

### Flujo de Desarrollo

```
Usuario: /task-dev T-APX-XXXX   (tarea padre — foco Product Owner)
  │
  └─ Hilo principal (ejecuta inline, mantiene el contexto)
       ├─ init        → carga padre+hijas, DELTA-FIRST (¿ya existe?), status, esfuerzo
       ├─ especif.    → BDD del delta (skill generate-bdd); preguntar solo si hay ambigüedad real
       ├─ @hades      → review-spec (aislado; auto-corrección ×3, corrige el hilo)
       ├─ [HITL: validación de especificación — consolidada, a nivel padre]
       ├─ fase roja   → step defs + unit tests del cambio (fallan); corre solo tests relevantes
       ├─ @hades      → review-test (aislado; ×3)
       ├─ fase verde  → implementación mínima; suite completa una vez al final
       ├─ [HITL: validación funcional — todo junto]
       ├─ @hades      → review-code (aislado; ×3)
       ├─ docs+commit → skills manage-docs + commit
       └─ cierre      → esfuerzo real, cierra hijas + padre
```

> Las fases productivas van inline en el hilo (un solo contexto continuo). Solo **Hades** se delega a un contexto aislado, en los tres puntos de revisión (spec, tests, código) — así nadie revisa su propio trabajo. Tanto en tareas como en bugs, un **paso de triaje** tras el init decide qué fases producen cambios reales (BDD, evals, dev, tests, docs); las que no aportan se omiten junto con su revisión. Así el proceso se ajusta a la tarea en vez de ejecutar siempre el flujo máximo.

### Principios de diseño

- **Inline por defecto, delegar solo donde paga**: las fases productivas van en el hilo principal (contexto continuo = rápido y barato). Se delega únicamente la revisión a Hades, porque solo ahí el aislamiento de contexto aporta valor. La separación de roles es de *fase*, no de *contexto*.
- **Separación de contexto cognitivo (solo Hades)**: Hades opera sin acceso al historial de desarrollo, eliminando sesgo de confirmación. Nadie revisa su propio trabajo.
- **Delta-first, no greenfield**: cada fase parte de "¿qué hay ya y qué falta?". Se comprueba el estado del código antes de especificar o construir, para no reimplementar funcionalidad existente.
- **Economía**: implementar lo mínimo que satisface lo especificado; sin ampliar alcance ni tests fuera de él. Durante el bucle de desarrollo se corren solo los tests relevantes; la suite completa, una vez al final.
- **Agnóstico de runtime**: las skills no mencionan mecanismos de ninguna herramienta concreta (`isolation: worktree` se mapea por cada runtime).
- **Auto-corrección**: Hades implementa un bucle cerrado de hasta 3 iteraciones; el hilo principal corrige entre iteraciones. Solo escala al humano si no converge.
- **Estado del flujo externo**: el hilo mantiene un checklist explícito de fases (no en memoria de contexto, que se diluye en flujos largos). Los HITL son ítems del checklist: si se difieren, quedan abiertos hasta realizarse.

### HITL (Human-in-the-Loop)

El hilo principal gestiona exactamente 2 puntos de parada humana:

| Punto | Propósito |
|-------|-----------|
| **Post-especificación** | Validar que las BDD y evals consolidadas capturan correctamente el requisito/fallo de toda la tarea padre |
| **Post-implementación** | Validar integración visual, UX y efectos secundarios del conjunto, no cubiertos por tests |

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
📋 Init          → inline:   delta-first (¿ya existe?), status, esfuerzo, versión
📝 Especificación → inline:   BDD del delta (skill generate-bdd)
🔎 review-spec   → Hades:    audita especificación (aislado, ×3)
                 ↓ [HITL: validación de especificación]
🔴 Red           → inline:   step definitions, unit tests del cambio (fallan)
🔎 review-test   → Hades:    audita calidad de tests (aislado, ×3)
🟢 Green         → inline:   implementación mínima (suite completa al final)
                 ↓ [HITL: validación funcional]
🔎 review-code   → Hades:    audita calidad de código (aislado, ×3)
📄 Docs          → inline:   /manage-docs + /commit
✅ Cierre        → inline:   esfuerzo real, cierre de tarea
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
