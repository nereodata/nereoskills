# 🤖 Adevv — AI Agent Workflows & Skills

Este repositorio centraliza los **agentes**, **skills** y **workflows** reutilizables para herramientas de IA (Claude Code, Cursor, Antigravity, etc.) que siguen el estándar **Issue-as-Code distribuido v3.0**.

La arquitectura separa **conocimiento** (skills) de **ejecución**: las skills definen procesos, criterios y playbooks. El **hilo principal** ejecuta las fases productivas **inline** (manteniendo el contexto acumulado), y delega la revisión en contexto aislado a **Hades**.

---

## 🚀 Instalación y sincronización global

Instala Adevv una sola vez por máquina mediante una única orden desde una versión publicada fija en el origen, y sincroniza las carpetas globales de tus arneses (Claude Code, Codex y Antigravity):

```bash
pip install --user git+https://github.com/nereodata/nereoskills.git@v0.1.0 && adevv instalar
```

> Si usas `uv`: `uv tool install git+https://github.com/nereodata/nereoskills.git@v0.1.0 && adevv instalar`.
> Si `adevv` no está en tu PATH, añade el directorio de scripts de usuario de Python (`%APPDATA%\Python\Python312\Scripts` en Windows o `~/.local/bin` en Linux/macOS).

Al ejecutar `adevv instalar`:
1. Comprueba si existe una versión publicada superior en el origen y la actualiza automáticamente.
2. Sincroniza las skills, agentes y workflows en las carpetas globales confirmadas de cada arnés detectado (`~/.claude`, `~/.codex`, `~/.gemini/config`).
3. Registra huellas SHA-256 de los archivos instalados para proteger tus archivos ajenos o editados a mano.

Las actualizaciones, también `adevv actualizar X.Y.Z`, se instalan aunque haya bucles en marcha. Cada versión ocupa su propia carpeta y las versiones existentes se conservan sin sobrescribir. Los motores desde v0.5 toman la versión activa al terminar su paso actual; el gateway la toma entre vueltas de polling. Los motores anteriores requieren reinicio manual, según el aviso de actualización.

Las copias globales de skills y agentes esperan mientras haya bucles, incluso con `adevv instalar --forzar`. La primera orden fuera de pasos y sin bucles reintenta la sincronización. Esta espera no impide instalar ni recargar los motores; reinicia las sesiones abiertas de los arneses cuando las copias estén sincronizadas.

Para comprobar el estado y las versiones sincronizadas en cualquier momento:
```bash
adevv --version
```

---

## 🏗️ Arquitectura: Agentes + Skills

### Agentes — El Equipo

| Agente | Rol | Modelo | Skills que usa | Uso en `task-dev`/`bug-fix` |
|--------|-----|--------|---------------|------------------------------|
| **Atenea** | Analista — Define, diseña la arquitectura, planifica y decide | Opus | ciclo-requisitos, platform-plan, work-plan, generate-bdd | Pasos de análisis de `/orquestar` |
| **Artemisa** | Desarrolladora — Implementa hasta que los tests pasan | Configurable | task-dev, bug-fix | Pasos `task-dev`/`bug-fix` de `/orquestar` |
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
| `revisar-producto` | Al cerrar versión (opcional) o a mano | El producto en uso: utilidad, diseño y usabilidad; propone mejoras con destino y el usuario decide |

Cada 🟡/🔵 lleva un destino: `resolver` (ahora), `registrar` (bug de deuda, fuera de versión) o `descartar`. Cada 🔴/🟠 lleva quién lo resuelve: `desarrollador`, `especificador` o `humano` (solo recursos externos); el orquestador se lo envía y el resto del trabajo sigue.

### Flujo de Desarrollo Canónico (`task-dev` / `bug-fix`)

```
📋 Init          → inline:   delta-first, status, versión
📝 Especificación → inline:   BDD del delta (generate-bdd)
🔎 review-spec   → Hades:    audita lo añadido o modificado (aislado)
                 ↓ [HITL: validación de especificación]
📐 Diseño        → inline:   diseño de la solución (design), sin revisión
🔴 Red           → inline:   tests que fallan + lint/tipado limpios
🔎 review-test   → Hades:    audita calidad de tests (aislado)
🟢 Green/Fix     → inline:   implementación mínima + verificación del triaje + lint/tipado
                 ↓ [HITL: validación funcional]
🔎 review-code   → Hades:    audita código y conformidad (aislado)
📄 Docs          → inline:   manage-docs
✅ Cierre        → inline:   deuda (resolver/registrar/descartar), cierre de tareas
💾 Commit        → inline:   commit semántico
```

### Orquestador (`/orquestar`)

Las cuotas con hora de recuperación se respetan; las respuestas sin hora y los errores de créditos permiten comprobar el trabajo pendiente al relanzar y cada 300 segundos (`cuota_reintento_s` en `orchestration.json`). `adevv orquestar --cuota-reset [arnés[/modelo]]` recupera las marcas seleccionadas, o todas sin selector, conservando el histórico. Un bucle esperando cuota lo detecta en un máximo de 30 segundos. `--estado` y `--agentes` muestran si la marca es real o supuesta y su origen; los créditos generan un aviso específico una vez por episodio.

Lleva un producto de la idea a su última versión sin parar: requisitos → plataforma → plan → por versión, revisión de deuda, `task-dev`/`bug-fix`, revisión de versión y, si se activa, revisión de producto. El humano solo interviene al cerrar cada versión: ajusta la tabla de propuestas y el bucle crea las tareas. Desde cualquier arnés, `/orquestar` lanza el bucle desatendido (`orquestar.py --fondo`), informa de cómo va (`estado`) o lo para (`parar`); el bucle deduce la fase del disco y continúa desde donde toque. Detalle en [`skills/orquestar/SKILL.md`](skills/orquestar/SKILL.md); diagramas en [`docs/orquestacion.md`](docs/orquestacion.md). Las dependencias entre tareas (`depende_de`) las resuelve el script; los roles (arnés, modelo y esfuerzo de Atenea, Artemisa, Hades, Clío y Cronos) se configuran en `orchestration.json`. Por Telegram, el bucle avisa de fin de versión, falta de cuota y paradas que necesitan respuesta, y el gateway ([`skills/telegram_gateway`](skills/telegram_gateway/SKILL.md)) responde a `/estado` y registra tareas y bugs sin versión.

---

## 📁 Estructura del Repositorio

```
├── agents/                # Agentes (Atenea, Artemisa, Hades, Cronos, Clio)
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
│   ├── telegram_gateway/  # Telegram: /estado, /tarea y /bug mientras el bucle trabaja
│   ├── revisar-producto/  # Revisión funcional de una versión y propuestas de mejora
│   └── ...
├── workflows/             # Proxies para slash commands (/task-dev, /bug-fix, etc.)
└── README.md
```

---

## 🛠️ Integración en proyectos consumer

1. **Instalar Adevv**:
   ```bash
   pip install --user git+https://github.com/nereodata/nereoskills.git@v0.1.0
   ```
2. **Sincronizar arneses**:
   ```bash
   adevv instalar
   ```
   Instala y sincroniza automáticamente las skills y agentes en los arneses de IA detectados (`.claude`, `.codex`, etc.) a nivel de usuario sin requerir submódulos ni enlaces en cada repositorio.
3. **Configurar `task_config.yaml`** en la raíz del proyecto para definir los prefijos y rutas del backlog del proyecto.
4. **Lanzar el bucle**:
   ```bash
   adevv orquestar
   ```

---

## 🔄 Guía de migración desde submódulo `.agents`

Para migrar proyectos consumidores que todavía utilizan el antiguo submódulo `.agents/` hacia la instalación desacoplada de Adevv, sigue estrictamente estos pasos en el orden indicado:

1. **Parar el bucle**:
   Ejecuta `/orquestar parar` o `adevv orquestar --parar` y espera a que el proceso termine y ya no exista el archivo `orquestar.pid`.
2. **Diagnosticar estado actual**:
   Ejecuta `adevv migrar` en la raíz del proyecto para auditar de forma segura y de solo lectura qué elementos quedan por migrar.
3. **Quitar el submódulo Git**:
   ```bash
   git submodule deinit -f .agents
   git rm -f .agents
   rm -rf .git/modules/.agents
   ```
   (en Windows PowerShell: `Remove-Item -Recurse -Force .git/modules/.agents`).
4. **Quitar enlaces y elementos locales**:
   Retira los enlaces simbólicos o junctions creados previamente en `.claude/skills`, `.codex/agents`, etc., así como elementos locales que oculten los distribuidos.
   > **⚠️ ADVERTENCIA CRÍTICA DE SEGURIDAD EN WINDOWS:**
   > Para retirar un enlace simbólico o junction **sin seguirlo ni borrar su contenido de destino**, utiliza siempre:
   > ```cmd
   > cmd /c rmdir <ruta_del_enlace_o_junction>
   > ```
   > **NUNCA utilices `Remove-Item -Recurse` (PowerShell) ni `rm -rf` (Bash) sobre un enlace o junction**, ya que en Windows seguirán el enlace y **borrarán recursivamente los archivos reales del destino** (como tu copia congelada o repositorio de agentes).
5. **Quitar o corregir `instructions` en `orchestration.json`**:
   Elimina o ajusta cualquier clave `instructions` que apunte a rutas `.agents/` para que los agentes utilicen las versiones instaladas globalmente.
6. **Actualizar adaptadores propios**:
   Si dispones de scripts personalizados en `scripts/` u otras carpetas que importaban directamente desde `.agents/`, adáptalos para invocar las herramientas globales mediante el CLI `adevv` (ej. `adevv orquestar`, `adevv release`, etc.).
7. **Borrar copias locales de Adevv**:
   Elimina cualquier carpeta clonada o congelada de Adevv que resida dentro del árbol del proyecto (carpetas distintas de la raíz que contengan `skills/orquestar/SKILL.md`).
8. **Diagnosticar hasta «Sin pendientes»**:
   Ejecuta nuevamente `adevv migrar` y repite los ajustes necesarios hasta que la salida concluya con `Sin pendientes` (o `Sin pendientes (N citas históricas).`).
9. **Registrar commit de migración**:
   ```bash
   git commit -m "chore: migración de submódulo .agents a adevv"
   ```
10. **Relanzar el bucle**:
    Ejecuta `/orquestar` o `adevv orquestar` para continuar con el desarrollo de forma desacoplada.

### Migración del propio repositorio de desarrollo de Adevv

Para migrar el propio repositorio fuente de Adevv (que utiliza una junction `.agents` hacia la copia congelada en `~/.adevv/congelado` durante la transición):
1. Parar cualquier bucle en marcha que esté corriendo desde la copia congelada (`adevv orquestar --parar`).
2. Instalar la versión publicada de Adevv (`adevv instalar`).
3. Quitar la junction `.agents` sin seguirla:
   ```cmd
   cmd /c rmdir .agents
   ```
4. Relanzar el bucle con `adevv orquestar`.
5. La copia congelada en `~/.adevv/congelado` solo debe borrarse cuando se confirme que ningún proceso ni arnés en el sistema la está utilizando.

### Calidad por tarea

El triaje conserva una base Git estable. Las skills task-dev y bug-fix aplican el formato disponible y comprueban formato y lint del delta antes de cerrar; Hades comprueba sin escritura. Configuración, deducción conservadora y omisiones justificadas: [calidad del delta](skills/orquestar/SKILL.md#calidad-del-delta-en-cada-tarea). La suite completa sigue correspondiendo al cierre de versión.


Los pasos del bucle recuperan errores de red o autenticación mediante `adevv orquestar --reintentos-arnes 3`: reintentos por perfil y después reservas, con diagnóstico si se agotan. Consulta las esperas y la parada cooperativa en [Orquestación](docs/orquestacion.md).


Los pasos de análisis recuperan la falta de progreso por `(paso, argumento)`:
prueban niveles superiores, escalada y reservas con el límite `--reintentos` por
perfil. La recarga conserva sus intentos. Si se agotan, `especificar` y
`revisar-tarea` bloquean solo la tarea y permiten continuar las independientes;
los análisis globales paran indicando los perfiles probados. Véase
[recuperación de análisis](skills/orquestar/SKILL.md#recuperación-de-análisis-sin-progreso).
