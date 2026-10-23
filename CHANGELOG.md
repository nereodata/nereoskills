# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

## [0.4.0] - 2026-10-23

### Añadido

#### General
- **T-ADV-0013** — Comando de métricas (`adevv metrics` / `adevv orquestar --metricas`) con tabla por versión, exportación CSV y coste estimado de API
- **T-ADV-0014** — Mostrar agentes configurados para la tarea actual y estado de cuota en `/estado`
- **T-ADV-0015** — Control remoto del bucle (`/lanzar`, `/parar`) y consulta de `/metricas` desde Telegram
- **T-ADV-0016** — Ejecución en segundo plano de `adevv telegram` (`--fondo`, `--parar`) y auto-arranque desde `orquestar`
- **T-ADV-0017** — Canal limpio de prompts en `--agente` (`--prompt` y limpieza automática de temporales)

### Corregido

#### General
- **B-ADV-0002** — Ajustes menores transversales v0.3: coexistencia de clave `telegram` en `orchestration.json` y marca `sin_cuota` en intento intermedio de paso

## [0.3.0] - 2026-10-23

### Añadido

#### General
- **T-ADV-0010** — Modelos de reserva ante agotamiento de cuota en pasos y subagentes
- **T-ADV-0011** — Subida automática de dificultad de la tarea tras más de 2 reintentos
- **T-ADV-0012** — Conversación libre con continuidad de hilo en el gateway de Telegram

## [0.2.0] - 2026-10-23

### Añadido

#### General
- **T-ADV-0008** — Continuidad de hilo en revisiones de Hades por tarea y reanudación tras espera de cuota
- **T-ADV-0009** — Clasificación de dificultad al crear tareas/bugs y selección de agente/modelo por dificultad

## [0.1.0] - 2026-10-23

### Añadido

#### General
- **T-ADV-0001** — Publicación de versiones sin contenido interno
- **T-ADV-0002** — Instalación y sincronización con los arneses
- **T-ADV-0003** — Adevv desde cualquier proyecto sin rutas
- **T-ADV-0004** — Actualización automática de versiones publicadas
- **T-ADV-0005** — Migración de proyectos con submódulo
- **T-ADV-0006** — Triaje por subfase y alcance sin doble validación en desarrollo y revisión
- **T-ADV-0007** — Detección y espera de cuota agotada en subagentes (--agente)

### Corregido

#### General
- **B-ADV-0001** — Corrección transversal v0.1: resolución de rutas en sync, aislamiento de suite, lista blanca en versions y evaluar_tabla pura
