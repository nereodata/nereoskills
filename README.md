# 🤖 NereoSkills — AI Agent Workflows & Skills

Este repositorio centraliza los **agentes**, **skills** y **workflows** reutilizables para herramientas de IA (Claude Code, Cursor, Antigravity, etc.) que siguen el estándar **Issue-as-Code distribuido v3.0**.

La arquitectura separa **conocimiento** (skills) de **ejecución**: las skills definen procesos, criterios y playbooks. El **hilo principal** ejecuta las fases productivas **inline** (manteniendo el contexto acumulado), y delega la revisión en contexto aislado a **Hades**.

---

## 🏗️ Arquitectura: Agentes + Skills

### Agentes — El Equipo

| Agente | Rol | Modelo | Skills que usa | Uso en `task-dev`/`bug-fix` |
|--------|-----|--------|---------------|------------------------------|
| **Hades** | QA — Juez de calidad objetivo e imparcial | Opus 4.8 | review-spec, review-design, review-test, review-code | **Delegado (aislado)** |
| **Cronos** | Gestor de tareas — Controla el ciclo de vida del backlog | Haiku 4.5 | task-add, bug-add, task-list | Manual (init/cierre van inline) |
| **Clío** | Documentalista — Registra cambios, documentación y commits | Haiku 4.5 | manage-docs, commit | Manual (docs/commit van inline) |

### Flujo de Desarrollo Canónico (`task-dev` / `bug-fix`)

```
📋 Init          → inline:   delta-first, status, esfuerzo, versión
📝 Especificación → inline:   BDD del delta (generate-bdd)
🔎 review-spec   → Hades:    audita especificación (aislado, ×3)
                 ↓ [HITL: validación de especificación]
📐 Diseño        → inline:   arquitectura y diseño de la solución (design)
🔎 review-design → Hades:    audita arquitectura y testeabilidad (aislado, ×3)
                 ↓ [HITL: validación del diseño (opcional)]
🔴 Red           → inline:   step definitions y unit tests que fallan
🔎 review-test   → Hades:    audita calidad de tests (aislado, ×3)
🟢 Green/Fix     → inline:   implementación mínima (suite completa al final)
                 ↓ [HITL: validación funcional]
🔎 review-code   → Hades:    audita calidad de código (aislado, ×3)
📄 Docs          → inline:   manage-docs
💾 Commit        → inline:   commit semántico
✅ Cierre        → inline:   esfuerzo real, cierre de tareas
```

---

## 📁 Estructura del Repositorio

```
├── agents/                # Agentes (Hades, Cronos, Clio)
├── skills/                # Skills (conocimiento puro — qué hacer)
│   ├── task-dev/          # Flujo de desarrollo de tareas
│   ├── bug-fix/           # Flujo de resolución de bugs
│   ├── design/            # Diseño técnico de la solución
│   ├── review-design/     # Auditoría de diseño técnico
│   ├── generate-bdd/      # Generación de BDD en español
│   ├── review-spec/       # Auditoría de BDD + evals
│   ├── review-test/       # Auditoría de calidad de tests
│   ├── review-code/       # Auditoría de calidad de código
│   ├── manage-docs/       # Documentación minimalista y CHANGELOG
│   ├── commit/            # Commits semánticos
│   ├── task-add/          # Registro de tareas en backlog
│   ├── bug-add/           # Registro de bugs en backlog
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
3. **Configurar `task_config.yaml`** en la raíz del proyecto para definir los prefijos y rutas del backlog del proyecto.
