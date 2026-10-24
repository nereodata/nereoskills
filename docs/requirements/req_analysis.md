**Estado:** ASUNCIONES_REALIZADAS

# Análisis de requisitos · Adevv: instalación, actualización y distribución

Producido por `/ciclo-requisitos` en modo orquestado (sin ronda de preguntas de la fase 0). Especificación en [`requirements.md`](requirements.md); trabajo del ciclo en [`ciclo/`](ciclo/).

## Preguntas

| ID | Pregunta | Impacto | Valor por defecto adoptado |
|---|---|---|---|
| PQ-01 | ¿Qué carpetas globales leen de verdad Codex (`~/.codex/skills` o `~/.agents/skills`, y sus agentes) y Antigravity (skills y workflows)? Solo Claude Code está documentado sin ambigüedad. | Alto para CE-1 con Antigravity | `/platform-plan` las confirma con la versión instalada de cada arnés; lo no confirmado no se escribe (destino «sin confirmar», `RF-F01-03`). Si Antigravity no lee ninguna carpeta global, CE-1 para Antigravity queda pendiente de la revisión de versión |
| PQ-02 | ¿El origen de publicación es `github.com/nereodata/nereoskills` (remoto actual) o se renombra a `adevv` (como cita el README)? | Medio: cambia la orden de instalación y el origen fijo | `nereodata/nereoskills`, el remoto real; si se renombra, GitHub redirige y basta con publicar una versión con el origen nuevo |
| PQ-03 | El repositorio de origen es hoy público. Al hacer de Adevv un proyecto Adevv, su backlog y sus documentos de requisitos y revisiones (con nombres de proyectos y rutas personales) quedan publicados. ¿Debe pasar a privado? | Alto en privacidad; nulo en funcionamiento | Sin cambio de visibilidad por parte del bucle (es una acción del dueño del repositorio, y el bucle solo hace commits locales: no empuja). Hecho comprobado: el commit `91bc9af` (encuadre en `docs/requirements/requirements.md`) ya está en `origin/main`, así que ese texto ya es público; lo que añada este ciclo y los siguientes solo se publica cuando el autor empuje. La spec funciona igual con origen privado: consulta e instalación usan las credenciales ya guardadas en Git sin preguntar (`RF-F03-03`). Se recomienda decidirlo en la revisión de la v0.1 |
| PQ-04 | ¿Debe `/orquestar` en un proyecto nuevo crear git y un `task_config.yaml` mínimo (`RF-F02-08`), o basta con documentar qué preparar? | Bajo | Crearlos, con las protecciones de `RF-F02-08` (solo con `requirements.md`, nunca en la carpeta personal, la raíz de una unidad ni dentro de otro repositorio), porque CE-1 pide que un proyecto nuevo pueda lanzar `/orquestar` |

## Asunciones

| ID | Asunción | Motivo | Solución adoptada |
|---|---|---|---|
| SUP-01 | Solo Afinn usa hoy el submódulo; Adayy tiene citas históricas; Adataxx, Adoxx y Aprexx no están en la ruta indicada | Comprobado en disco en el arranque | F-04 se valida con Afinn y con el propio Adevv; los demás se diagnostican con `adevv migrar` cuando aparezcan |
| SUP-02 | La copia `~/.adevv/congelado` con la junction `.agents` es un apaño manual para CE-5, no parte del producto | Comprobado en disco; ninguna skill la crea | Se documenta su retirada segura (`RF-F04-06`) |
| SUP-03 | Los roles lanzados con `--agente` siguen admitiendo solo `claude` o `codex` | NO-04: no rediseñar el bucle | CE-1 con Antigravity se refiere a los pasos del bucle, no a Hades |
| SUP-04 | Los avisos de Adevv van a la salida de errores y los reenvía la skill que lanzó la orden | La salida estándar la consumen el arnés y los scripts | `RF-F03-13` |
| SUP-05 | El proceso del bucle lanzado por `adevv orquestar --fondo` no repite la comprobación de actualización | Ya la hizo la orden que lo lanzó | Detalle de implementación para `/platform-plan` (p. ej. marcar el entorno del hijo) |
| SUP-06 | Comprobación como mucho una vez cada 24 h desde la última contada (no «por día natural») | La petición dice «como mucho una comprobación al día»; 24 h es verificable sin zonas horarias | `§4` fila 4 |
| SUP-07 | Tiempos: 5 s para consultar, 180 s para instalar, 1 h para reintentar sin red, 7 días para avisar de que no se puede comprobar | Proporcionados a un único usuario con red doméstica; ninguno lo fijó el usuario | `§4`, `RF-F03-03/07` |
| SUP-08 | La skill `/orquestar` en modo persona y los workflows se reescriben para usar `adevv …` sin cambiar su comportamiento | NO-04 | `RF-F02-05` |

## Decisiones

| ID | Decisión | Alternativa descartada | Motivo |
|---|---|---|---|
| DEC-01 | Una sola versión de Adevv activa por máquina; todos los proyectos usan la instalada | Fijar versión por proyecto | El objetivo es «recibir versiones nuevas sin tocar cada proyecto»; fijar por proyecto reintroduce el problema del submódulo (NO-05) |
| DEC-02 | «Proceso de Adevv en marcha» se calcula por lo que ejecutan los procesos vivos, sin registro de proyectos | Registro de proyectos + `orquestar.pid` | El registro no ve bucles anteriores a la migración ni gateways (hay uno vivo hoy en Adevv desde la copia congelada) y falla con PID reutilizados; −1 entidad |
| DEC-03 | Solo los bucles aplazan la actualización; gateways y otros procesos siguen con su versión durante la instalación y la operación en curso (y hasta reiniciarse en versiones anteriores a `v0.5.0`, o hasta su auto-recarga cooperativa entre ciclos desde `v0.5.0`, `DEC-P10`) | Aplazar con cualquier proceso | El gateway es perpetuo y con NO-01 arrancará con la sesión: nunca se actualizaría. La petición previa solo prohíbe actualizar con bucles en marcha. Impone a `/platform-plan` un mecanismo que no toque archivos en uso (`RF-F03-08`) |
| DEC-04 | `adevv migrar` solo diagnostica; los cambios los hace el autor siguiendo el README | `adevv migrar --aplicar` | Quitar submódulos y enlaces es difícil de deshacer (una junction mal borrada vacía su destino) y hay dos migraciones reales (NO-09) |
| DEC-05 | Fuera de la v0.1: `init`, `desinstalar`, autocompletado, plugin de Claude Code como destino, prefijos de nombre en las skills | Incluirlas | No las pide ningún recorrido; los choques de nombre los resuelve el registro con huellas (NO-08) |
| DEC-06 | Vuelta atrás con `adevv actualizar X.Y.Z`, que desactiva la actualización automática; `adevv actualizar` la reactiva | «Versión omitida» guardada | Estado visible en `adevv --version` en lugar de un campo oculto; −1 campo |
| DEC-07 | Una versión `FALLIDA` cuenta como comprobación y no se reintenta hasta que haya otra mayor o se ejecute `adevv actualizar` | Reintentar cada 6 h | Evita reinstalar una versión rota varias veces al día; un fallo de red no es `FALLIDA` sino `SIN_RED` (reintento en 1 h) |
| DEC-08 | Mecanismo de actualización en Windows (versiones lado a lado o actualizador desacoplado) lo decide `/platform-plan` con las condiciones de `RF-F03-07/08` | Fijarlo en requisitos | Regla 8: los requisitos son funcionales |
| DEC-09 | Sin ronda de preguntas de la fase 0 (modo orquestado); las tensiones se registran como PQ con valor por defecto | Parar a preguntar | Reglas del modo orquestado; ninguna PQ carece de valor por defecto seguro |
| DEC-10 | Cinco funcionalidades (tareas maestras), todas de la ola A | Fusionar F-04 en F-02 (4 maestras) | F-04 tiene valor propio (CE-2) y cabe en el presupuesto de 3-5 |
