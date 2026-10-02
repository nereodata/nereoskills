# 🤖 NereoSkills — AI Agent Workflows & Skills

Este repositorio centraliza los **agentes**, **skills** y **workflows** reutilizables para herramientas de IA (Claude Code, Cursor, Antigravity, etc.) que siguen el estándar **Issue-as-Code distribuido v3.0**.

La arquitectura separa **conocimiento** (skills) de **ejecución**: las skills definen procesos, criterios y playbooks. El **hilo principal** ejecuta las fases productivas **inline** (manteniendo el contexto acumulado), y delega la revisión en contexto aislado a **Hades**.

---

## 🏗️ Arquitectura: Agentes + Skills

### Agentes — El Equipo

| Agente | Rol | Modelo | Skills que usa | Uso en `task-dev`/`bug-fix` |
|--------|-----|--------|---------------|------------------------------|
| **Hades** | QA — Juez de calidad objetivo e imparcial | Opus | review-spec, review-design, review-test, review-code | **Delegado (aislado)** |
| **Cronos** | Gestor de tareas — Controla el ciclo de vida del backlog | Sonnet | task-add, bug-add, task-list | Manual (init/cierre van inline) |
| **Clío** | Documentalista — Registra cambios, documentación y commits | Sonnet | manage-docs, commit | Manual (docs/commit van inline) |

### Quién revisa qué

| Revisión | Cuándo | Mira |
|---|---|---|
| `review-spec` | Cada tarea | Escenarios y evals que la tarea añade o modifica |
| `review-design` | Plan de plataforma y revisión de versión | Arquitectura y sus decisiones; nunca código |
| `review-test` | Cada tarea, tras el rojo | Cobertura, aserciones, rojo correcto y estabilidad |
| `review-code` | Cada tarea, tras el verde | Corrección, seguridad, calidad y conformidad con el diseño y la arquitectura |

Cada 🟡/🔵 lleva un destino: `resolver` (ahora), `registrar` (bug de deuda, fuera de versión) o `descartar`.

### Flujo de Desarrollo Canónico (`task-dev` / `bug-fix`)

```
📋 Init          → inline:   delta-first, status, versión
📝 Especificación → inline:   BDD del delta (generate-bdd)
🔎 review-spec   → Hades:    audita lo añadido o modificado (aislado, ×3)
                 ↓ [HITL: validación de especificación]
📐 Diseño        → inline:   diseño de la solución (design), sin revisión
🔴 Red           → inline:   tests que fallan + lint/tipado limpios
🔎 review-test   → Hades:    audita calidad de tests (aislado, ×3)
🟢 Green/Fix     → inline:   implementación mínima + suite completa + lint/tipado
                 ↓ [HITL: validación funcional]
🔎 review-code   → Hades:    audita código y conformidad (aislado, ×3)
📄 Docs          → inline:   manage-docs
✅ Cierre        → inline:   deuda (resolver/registrar/descartar), cierre de tareas
💾 Commit        → inline:   commit semántico
```

### Orquestador (`/orquestar`)

Lleva un producto de la idea a su última versión sin parar: requisitos → plataforma → plan → por versión, revisión de deuda, `task-dev`/`bug-fix` y revisión de versión. El humano solo interviene al cerrar cada versión. Detalle en [`skills/orquestar/SKILL.md`](skills/orquestar/SKILL.md).

---

## 📁 Estructura del Repositorio

```
├── agents/                # Agentes (Hades, Cronos, Clio)
├── skills/                # Skills (conocimiento puro — qué hacer)
│   ├── task-dev/          # Flujo de desarrollo de tareas
│   ├── bug-fix/           # Flujo de resolución de bugs
│   ├── design/            # Diseño técnico de la solución
│   ├── review-design/     # Auditoría de arquitectura
│   ├── generate-bdd/      # Generación de BDD en español
│   ├── review-spec/       # Auditoría de BDD + evals
│   ├── review-test/       # Auditoría de calidad de tests
│   ├── review-code/       # Auditoría de calidad de código
│   ├── manage-docs/       # Documentación minimalista y CHANGELOG
│   ├── commit/            # Commits semánticos
│   ├── task-add/          # Registro de tareas en backlog
│   ├── bug-add/           # Registro de bugs en backlog
│   ├── orquestar/         # Bucle de la idea al producto
│   └── ...
├── workflows/             # Proxies para slash commands (/task-dev, /bug-fix, etc.)
└── README.md
```

---

## 🛠️ Integración en proyectos consumer

1. **Añadir como submódulo**:
   ```bash
   git submodule add https://github.com/imoremu/Wokflows.git .agents
   ```
2. **Symlink para runtime** (ej. Claude Code):
   ```bash
   ln -s ../.agents/skills .claude/skills
   ln -s ../.agents/agents .claude/agents
   ```
   Para Codex, los agentes con modelo propio (`clio` y `cronos` en luna, esfuerzo bajo) están en `agents/codex/`:
   ```bash
   ln -s ../.agents/agents/codex .codex/agents
   ```
3. **Configurar `task_config.yaml`** en la raíz del proyecto para definir los prefijos y rutas del backlog del proyecto.
