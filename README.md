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

Las actualizaciones, también `adevv actualizar X.Y.Z`, se instalan aunque haya bucles en marcha. Cada versión ocupa su propia carpeta y las versiones existentes se conservan sin sobrescribir. Los motores desde v0.5 toman la versión activa al terminar su paso actual; el gateway la toma entre vueltas de polling. Desde v1.0.0 solo recargan si el destino es de v0.5.0 o posterior y acepta sus opciones; si no (por ejemplo, al volver atrás a una versión anterior), siguen con su versión, conservan su PID y avisan una vez en su log y por Telegram de que hace falta reiniciarlos. Los motores anteriores requieren reinicio manual, según el aviso de actualización; al volver atrás a una versión anterior a v0.5.0, los de v0.5.0 a v0.6.1 se detienen al terminar su paso.

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
| **Atenea** | Analista — Define, diseña la arquitectura, planifica y decide | Opus / Argon | ciclo-requisitos, platform-plan, work-plan, start-version, revisar-producto | Pasos de análisis de `/orquestar` |
| **Artemisa** | Desarrolladora — Implementa con autonomía hasta dejar cheques y tests en verde | Configurable | task-dev, bug-fix | Pasos `task-dev`/`bug-fix` de `/orquestar` |
| **Hades** | QA — Juez independiente post-verde y de arquitectura | Opus / Argon | review-design, review-code | **Delegado (aislado)** |
| **Cronos** | Gestor de tareas — Controla el ciclo de vida del backlog | Flash / Sonnet | task-add, bug-add | Manual / altas |
| **Clío** | Documentalista — Registra cambios, documentación y commits | Flash / Sonnet | manage-docs, commit | Manual / árbol sucio |

### Quién revisa qué

| Revisión | Cuándo | Mira |
|---|---|---|
| `review-design` | Plan de plataforma y cambios arquitectónicos | Arquitectura y decisiones (`DEC-xx`); nunca código |
| `review-code` | Post-verde en superficies críticas o cierre de versión | Revisión conjunta de código + pruebas, seguridad y conformidad |
| `revisar-producto` | Al cerrar versión (opcional) o a mano | El producto en uso: utilidad, diseño y usabilidad; propone mejoras con destino y el usuario decide |

Cada 🟡/🔵 lleva un destino: `resolver` (ahora), `registrar` (bug de deuda, fuera de versión) o `descartar`. Cada 🔴/🟠 lleva quién lo resuelve: `desarrollador`, `especificador` o `humano` (solo recursos externos); el orquestador se lo envía y el resto del trabajo sigue.

### Flujo de Desarrollo Autónomo (`task-dev` / `bug-fix`)

```
📋 Preparación   → inline:   delta-first, base_calidad, retoma WIP/checkpoint si existe
🟢 Entrega       → inline:   implementación + pruebas directas (unittest) + --verificar + --calidad (ruff)
🔎 review-code   → Hades:    auditoría post-verde proporcional (superficies críticas; N/A verificable fuera)
📄 Docs & Cierre → inline:   manage-docs (si aplica), deuda 🟡/🔵, completed y commit semántico
```

### Orquestador (`/orquestar`)

Si una tarea necesita una decisión sin valor por defecto seguro, `adevv orquestar --preguntar <ID> "<pregunta>" --contexto "<contexto>"` conserva su trabajo y deja continuar las independientes. Consulta `adevv orquestar --preguntas` y responde desde la máquina local con `adevv orquestar --responder <Q-ID> "<respuesta>"`, sin configurar Telegram. También puedes usar `/preguntas` y `/responder <Q-ID> <respuesta>` o `/desbloquear <Q-ID> <respuesta>` en Telegram: el motor incorpora la decisión entre pasos y retoma la tarea; si lo que existe es una espera de cuota o una intervención técnica sin pregunta humana, explica el motivo y conserva su estado. `PENDIENTE: <qué falta>` o `INSUFICIENTE: <qué falta>` conserva el bloqueo; una parada manual impide el relanzamiento automático. La CLI admite un ID de tarea cuando identifica una sola pregunta pendiente y registra al operador como `local:<usuario SO>`, sin credenciales de Telegram ni servidor. Recepción en cola, incorporación y lanzamiento son resultados distintos; las dependencias y otras preguntas siguen limitando la reanudación.

Las cuotas con hora de recuperación se respetan; las respuestas sin hora y los errores de créditos permiten comprobar el trabajo pendiente al relanzar y cada 300 segundos (`cuota_reintento_s` en `orchestration.json`). `adevv orquestar --cuota-reset [arnés[/modelo]]` recupera las marcas seleccionadas, o todas sin selector, conservando el histórico. Un bucle esperando cuota lo detecta en un máximo de 30 segundos. `--estado` y `--agentes` muestran si la marca es real o supuesta y su origen; los créditos generan un aviso específico una vez por episodio.

Lleva un producto de la idea a su última versión sin parar: requisitos → plataforma → plan → por versión, revisión de deuda, `task-dev`/`bug-fix`, revisión de versión y, si se activa, revisión de producto. El humano solo interviene al cerrar cada versión: ajusta la tabla de propuestas y el bucle crea las tareas. Desde cualquier arnés, `/orquestar` lanza el bucle desatendido (`orquestar.py --fondo`), informa de cómo va (`estado`) o lo para (`parar`); el bucle deduce la fase del disco y continúa desde donde toque. Detalle en [`skills/orquestar/SKILL.md`](skills/orquestar/SKILL.md); diagramas en [`docs/orquestacion.md`](docs/orquestacion.md). Las dependencias entre tareas (`depende_de`) las resuelve el script; los roles (arnés, modelo y esfuerzo de Atenea, Artemisa, Hades, Clío y Cronos) se configuran en `orchestration.json`. Por Telegram, el bucle avisa de fin de versión, falta de cuota y paradas que necesitan respuesta, y el gateway ([`skills/telegram_gateway`](skills/telegram_gateway/SKILL.md)) responde a `/estado` y registra tareas y bugs sin versión.

---

## 📁 Estructura del Repositorio

```
├── agents/                # Agentes (Atenea, Artemisa, Hades, Cronos, Clio)
├── skills/                # Skills ligeras orientadas a guardarraíles
│   ├── task-dev/          # Ejecución autónoma de tareas
│   ├── bug-fix/           # Resolución autónoma de bugs
│   ├── review-design/     # Auditoría de arquitectura
│   ├── review-code/       # Auditoría conjunta post-verde (código + pruebas)
│   ├── manage-docs/       # Documentación minimalista y CHANGELOG
│   ├── commit/            # Commits semánticos
│   ├── task-add/          # Registro de tareas en backlog
│   ├── bug-add/           # Registro de bugs en backlog
│   ├── orquestar/         # Bucle autónomo de la idea al producto
│   ├── telegram_gateway/  # Telegram: /estado, /tarea, /bug, /responder, /desbloquear, /cerrar
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


El cierre local, `/cerrar` por Telegram y la API de publicación exigen un informe
formal `docs/review/code_reviews/<ID>-code-review.md` para cada tarea o bug maestro
completado de la versión. Debe estar APROBADO, o N/A con motivo explícito de ausencia
de código. Un informe ausente, vacío o RECHAZADO mantiene pendiente el cierre aunque
las pruebas pasen. El diagnóstico enumera los IDs y pide reanudar `revisar-tarea`
y volver a validar; si Hades agotó cuota, hay que recuperar su disponibilidad y
obtener el informe. Recuperar cuota o emitir el informe no publica por sí solo.
El selector y el cierre distinguen parches (`v1.1.1` y `v1.1.2`); `v1.1` equivale
a `v1.1.0`. `/cerrar v1.1.2 confirmo` admite la rama hotfix o release correspondiente.
Las métricas conservan su agrupación histórica por mayor y menor.

Si el bucle diagnostica una línea dañada en `orquestar_metricas.jsonl`, ejecuta `adevv orquestar --recuperar-metricas` en la raíz del proyecto. El comando indica dónde guardó el original y recupera los registros válidos en su orden. [Consulta y exportación de métricas](skills/orquestar/SKILL.md#consulta-y-exportación-de-métricas)
