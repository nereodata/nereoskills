# Alcance del ciclo

## Fase 0 · Arranque (delta frente a lo existente)

- **Ya existe:** motor `skills/orquestar/orquestar.py` (resuelve `AGENTES` y `SKILL` relativos a `__file__`, así que ya funciona desde cualquier carpeta); gateway `skills/telegram_gateway/gateway.py` (carga el motor por ruta relativa `../orquestar/orquestar.py`); backlog propio de Adevv (`task_config.yaml`, `docs/plan/`, commit `91bc9af`); copia congelada manual en `~/.adevv/congelado` con `.agents` como enlace (apaño actual de CE-5).
- **Referencias a `.agents/` en lo que se distribuiría:** `agents/codex/{clio,cronos,hades}.toml`, `skills/orquestar/SKILL.md` (§Roles), `skills/release/templates/RELEASING.md` (4), `skills/seo-audit/SKILL.md`, `workflows/*.md` (`../skills/<x>/SKILL.md`), `README.md §Integración`, `branch_strategy.md §8`.
- **Proyectos consumidores:** de los cinco citados, solo `Afinn` tiene hoy el submódulo (`.gitmodules` → `nereoskills.git`) y adaptadores propios que citan `.agents/` (`AGENTS.md` ×6, `.orchestration/nereoskills-source/…`, una copia congelada propia). `Adayy` cita `.agents/` en documentos históricos (reportes, tareas). El resto no tiene el repo en la ruta indicada.
- **Arneses (comprobado en la web, ver §6 de requirements):** Claude Code lee skills/agentes globales de `~/.claude/skills` y `~/.claude/agents`; Codex documenta `~/.codex/skills` (algunas guías citan `~/.agents/skills`; varía por versión); Antigravity: fuentes no oficiales citan `~/.gemini/antigravity/skills` y workflows por proyecto en `.agent/workflows`. uv instala herramientas desde `git+https://…@<tag>`; `uv tool upgrade` no mueve una etiqueta fijada (hay que reinstalar con la nueva).

## Fase 2 · Ideación (34 ideas)

**Usuario**
- I01 Orden única de instalación documentada en el README.
- I02 `adevv instalar`: sincroniza skills, agentes y workflows en cada arnés detectado.
- I03 `adevv orquestar …` con los mismos argumentos que hoy `orquestar.py`.
- I04 `adevv telegram …` para el gateway.
- I05 `adevv version` / `--version`: versión instalada y destinos sincronizados.
- I06 `adevv actualizar`: fuerza comprobar y aplicar.
- I07 Aviso de una línea cuando se actualiza.
- I08 `adevv migrar`: diagnóstico de un proyecto con submódulo.
- I09 `adevv migrar --aplicar`: quita el submódulo y reescribe referencias automáticamente.
- I10 `adevv init`: crea `task_config.yaml`, `orchestration.json` y `requirements.md` en un proyecto nuevo.
- I11 Autocompletado de órdenes en la shell.
- I12 `adevv desinstalar`: borra lo sincronizado en los arneses.

**Negocio / IA (arneses)**
- I13 Las skills citan las demás skills por nombre (`/nombre`) y la orden `adevv`, no rutas.
- I14 El prompt del bucle cita rutas absolutas de la instalación.
- I15 Adaptadores Codex (`agents/codex/*.toml`) instalados en la carpeta global de agentes de Codex con rutas resueltas.
- I16 Workflows de Antigravity instalados globalmente.
- I17 Plugin de Claude Code como destino adicional.
- I18 Prefijo/espacio de nombres para no chocar con skills propias del usuario.
- I19 Elegir destinos (desactivar un arnés) por configuración.

**Técnico**
- I20 Registro de sincronización (qué archivos escribió Adevv) para borrar los obsoletos y no tocar los ajenos.
- I21 Comprobación como mucho diaria con marca de tiempo.
- I22 Detección de bucles en marcha en todos los proyectos (registro de proyectos + PID vivo).
- I23 Actualización en Windows sin reemplazar el proceso en uso (proceso separado tras salir, o aplicar en la siguiente).
- I24 Paquete que excluye `docs/plan`, `tests`, `docs/` internos; prueba automática que lo verifica.
- I25 Publicación desde `/release` (etiqueta `vX.Y.Z`) como única fuente de actualización.
- I26 Modo desarrollo: ejecutar Adevv desde el árbol de trabajo sin tocar la instalación.
- I27 Retirar la copia congelada `~/.adevv/congelado`.

**Riesgos**
- I28 Actualizar a mitad de un bucle cambia skills que un paso está leyendo → prohibido (petición previa).
- I29 Un paso del bucle invoca `adevv` → no debe disparar la comprobación.
- I30 Sin red o GitHub caído → seguir sin esperar más de unos segundos.
- I31 Actualización fallida a medias → la versión anterior sigue usable.
- I32 Choque de nombre con una skill del usuario → no sobrescribir, avisar.
- I33 Referencias residuales a `.agents/` en lo que se instala → prueba que las detecta.
- I34 PID reutilizado por otro proceso → falso «bucle en marcha» (aplaza de más; seguro).

## Fase 3 · Ronda aditiva

Tres ideadores aislados (gobierno/integridad/seguridad · núcleo e integración con arneses · usuario y operación diaria). Notas: 6 · 6 · 6. Coincidencias entre los tres marcadas con ×3.

### Defectos en lo ya escrito (van a la ola A, regla 5)

| D | Origen | Defecto | Resolución |
|---|---|---|---|
| D1 | ×3 | Resultado `APLICADA` contradice la restricción de Windows: la orden que lanza el bucle (`adevv orquestar --fondo`) no puede sustituir su propio entorno, y si lo hace al salir, el bucle recién lanzado ya lo usa | `RF-F03-07/08`: los procesos en marcha nunca ven cambiar sus archivos; la acción de la orden se ejecuta entera con la versión nueva o entera con la anterior. Mecanismo (versiones lado a lado o actualizador desacoplado) a `/platform-plan` |
| D2 | ×3 | «Bucle en marcha» solo por registro de proyectos: no ve el gateway, ni los bucles lanzados desde el submódulo o la copia congelada (hay uno vivo ahora en Adevv) | Se sustituye por «proceso de Adevv en marcha» (código instalado o línea de órdenes con `orquestar.py`/`gateway.py`); se elimina la entidad Registro de proyectos |
| D3 | ×2 | Tabla de resultados: «4-8 cuentan» y «FALLIDA/APLAZADA no consumen el día» se contradicen; `SIN_RED` consumía el día (hasta ~24 h de retraso) y `APLAZADA` consultaba la red en cada orden | `APLAZADA` guarda la versión y cuenta; `SIN_RED` reintenta ≥ 1 h; `FALLIDA` cuenta y no se reintenta la misma versión (revisión, fase 6); recalculado en `F-03` |
| D4 | ×1 (núcleo) | El motor cita `python <relpath>/orquestar.py` en los prompts (Python sin dependencias, `relpath` falla entre unidades) y `en_fondo()` relanza con `sys.argv` | `RF-F02-01/03` |
| D5 | ×2 | Paquete instalado ≠ sincronizado en los arneses (vuelta atrás manual o sincronización fallida) sin que nada lo diga | `RF-F01-11` resincroniza; `RF-F01-12` muestra versiones |
| D6 | ×2 | Versión del paquete ≠ etiqueta → reinstalación diaria; etiquetas movidas o no deliberadas se instalarían | `F-05` (versión = etiqueta, etiqueta no se mueve) y `RF-F03-02` (qué cuenta como publicada) |

### Candidatas nuevas

| C | Origen | Idea | V | C | R | Prio (2V−C−R) | Clase |
|---|---|---|---|---|---|---|---|
| C01 | I1-P4, I2-P5 | Registro de sincronización con hash; no tocar lo ajeno; destino `INCOMPLETO` | 5 | 2 | 1 | 7 | Must |
| C02 | I2-P3/P4 | Prompts con `adevv …` y rutas absolutas; scripts de skills como subórdenes; prueba sin `.agents/` ni `.py` | 5 | 2 | 1 | 7 | Must |
| C03 | I1-P9, I3-P7 | Negarse a lanzar si hay skills locales del proyecto que tapan las instaladas | 4 | 1 | 1 | 6 | Must |
| C04 | I1-P5 | Lista blanca del paquete y prueba del paquete construido | 4 | 1 | 1 | 6 | Must |
| C05 | I1-P6 | Red no interactiva con tiempos máximos (5 s / 180 s) | 4 | 1 | 1 | 6 | Must |
| C06 | I3-P3, I2-P8 | `migrar` se niega con bucle en marcha; solo cuenta archivos en uso; detecta enlaces, `instructions`, copias congeladas; históricos sin bloquear | 5 | 2 | 1 | 7 | Must |
| C07 | I3-P8, I2-H7 | Migración del propio Adevv y retirada segura de `~/.adevv/congelado` | 4 | 1 | 2 | 5 | Must |
| C08 | I1-P7 | `adevv actualizar X.Y.Z` con versión omitida (vuelta atrás que no se deshace sola) | 3 | 1 | 1 | 4 | Should |
| C09 | I1-H11 | Instalación de desarrollo (no publicada) no se autoactualiza | 3 | 1 | 1 | 4 | Should |
| C10 | I2-P7 | `adevv orquestar` crea git y `task_config.yaml` mínimo en un proyecto nuevo (CE-1) | 4 | 1 | 1 | 6 | Must |
| C11 | I3-P9 | Avisos por stderr y recordatorio de reiniciar sesiones | 2 | 1 | 1 | 2 | Should |
| C12 | I2-H7 | Archivos sincronizados de solo lectura; en el repo de Adevv el prompt dice que los cambios van al árbol (CE-5) | 4 | 1 | 1 | 6 | Must |
| C13 | I3-H7 | Aviso si no se puede comprobar en ≥ 7 días (origen inaccesible silencioso) | 3 | 1 | 1 | 4 | Should |
| C14 | I2-P9 | Prueba de humo automática por arnés tras instalar | 3 | 2 | 2 | 2 | Won't (validación manual en la revisión de versión) |
| C15 | I1-P1 | Versiones lado a lado con lanzador estable | — | — | — | — | Mecanismo: pasa a `/platform-plan` como opción para D1 |

## Fase 4 · Convergencia

**Ideas de la fase 2:** Must: I01-I08, I13-I16, I19-I25, I27-I33. Won't: I09 (`migrar --aplicar`, irreversible y un solo proyecto con submódulo), I10 (`init`; sustituida por C10, sin orden nueva), I11 (autocompletado), I12 (`desinstalar`), I17 (plugin de Claude Code; la petición previa lo permite como destino más, no aporta frente a `~/.claude/skills`), I18 (prefijo; los choques se resuelven con C01), I26 (modo desarrollo; sustituido por C09), I34 (resuelto por D2).

**Funcionalidades (5, todas ola A, Must; presupuesto 3-5 maestras):**

| F | Agrupa | Recorridos |
|---|---|---|
| F-01 Instalación y sincronización con los arneses | I01, I02, I05, I15, I16, I19, I20, I32, C01, D5 | R0, R2 |
| F-02 Adevv desde cualquier proyecto sin rutas | I03, I04, I13, I14, I33, C02, C03, C10, C12, D4 | R0, R1, R4 |
| F-03 Actualización automática | I06, I07, I21-I23, I25, I28-I31, C05, C08, C09, C11, C13, D1-D3 | R2 |
| F-04 Migración de proyectos con submódulo | I08, I27, C06, C07 | R3, R4 |
| F-05 Publicación de versiones sin contenido interno | I24, I25, C04, D6 | R4 |

**Cobertura de recorridos:** R0 → F-01, F-02 · R1 → F-02 · R2 → F-01, F-03 · R3 → F-04 · R4 → F-02, F-04, F-05. Todos cubiertos.

**Peticiones explícitas:** 1 (empaquetado y despliegue) → F-05, F-01 · 2 (Adevv como proyecto Adevv, backlog fuera) → F-05 (lista blanca), F-02 (`RF-F02-09`, CE-5), F-04 (migración del propio Adevv) · 3 (buscar actualizaciones y actualizarse) → F-03. Ninguna eliminada ni condicionada.

**Complejidad:** se elimina la entidad Registro de proyectos (D2) y se añaden dos campos (versión omitida, origen de la instalación); los Won't quitan 6 órdenes posibles. Neto: las 5 funcionalidades encajan en el presupuesto.
