# Revisión del ciclo

Decisión por hallazgo: **A** = aceptado, **P** = parcial, **R** = rechazado, con su motivo. Regla 4 (complejidad neta cero) aplicada al integrar.

## Ronda 1 · Fase 6 (críticos y simulacro)

Revisores aislados: crítico de alcance/simplicidad/valor (C, nota 6), crítico de privacidad/seguridad/confianza (S, nota 7), ingeniero que solo ve la spec (I, nota 6,5).

| # | Origen | Sev. | Hallazgo | Decisión | Aplicado en |
|---|---|---|---|---|---|
| 1 | S1 | 🔴 | `RF-F02-08` crearía un repositorio git en la carpeta personal, la raíz de una unidad o una subcarpeta de otro proyecto | **A** | `RF-F02-08` (solo con `requirements.md`, fuera de repos, no personal ni raíz; subcarpeta → para), `CA-F02-09` |
| 2 | I-H1 | 🔴 | Aplicar una versión aplazada «sin red» es imposible: instalar descarga | **A** | `§4` fila 5 (fallo de descarga = `SIN_RED`), E12, `CA-F03-03` («con red») |
| 3 | C1, I-H6 | 🔴 | `INCOMPLETO` tenía precedencia sobre `DESFASADO`: un error transitorio no se reintentaba nunca y `RF-F03-09` bloqueaba los bucles para siempre | **A** | `§4` estados (los errores no registran versión → `DESFASADO`; `INCOMPLETO` solo por conflictos), `RF-F01-05`, `RF-F03-09` |
| 4 | I-H5, C1 | 🟠 | Bloquear todos los bucles por un conflicto en un destino es desproporcionado: el bucle cita la instalación, no los destinos | **A** | `RF-F01-13` (aviso y sigue), `CA-F01-04` |
| 5 | C2, I-H2, S11 | 🟠 | «Alcanzable desde `main` y versión del paquete» no se comprueba en 5 s con la lista de etiquetas | **A** | `§4` (publicada = etiqueta anotada `^vX.Y.Z$`; versión comprobada tras instalar → `FALLIDA`), `RF-F03-07`, `CA-F03-07/09` |
| 6 | S5 | 🟠 | Instalar por nombre desde un índice público ejecutaría un paquete ajeno; la etiqueta podría moverse entre consulta e instalación | **A** | `RF-F01-01` (solo origen fijo), `RF-F03-07` (instala el commit consultado) |
| 7 | S3, I-H4, C10 | 🟠 | El repositorio fuente de Adevv nunca llegaría a «Sin pendientes» (su raíz es «copia» y su README documenta `.agents`); «repositorio fuente» no estaba definido | **A** | `§4` (definición), `RF-F04-02/03`, `CA-F04-04`, `RF-F02-09` |
| 8 | S2 | 🟠 | Quitar una junction con `Remove-Item -Recurse` borra su destino (la copia congelada, el submódulo) | **A** | `RF-F04-06` (orden que no sigue el enlace + advertencia), `RF-F04-02` (tipo y destino), `CA-F04-04` |
| 9 | S4 | 🟠 | `RF-F01-11` reescribía destinos con un bucle en marcha leyéndolos | **A** | `RF-F01-11` (solo sin bucles; aviso 1 vez cada 24 h), `CA-F01-11` |
| 10 | C5, I-H12 | 🟠 | El gateway (perpetuo, y con NO-01 arrancará con la sesión) y procesos `otro` aplazarían todas las actualizaciones; la petición previa solo habla de bucles | **A** | `§4` (solo `bucle` aplaza), `RF-F03-06/08`, fila 8 («Reinicia el gateway»), `CA-F03-05`, E11; condición a `/platform-plan` (`§6`) |
| 11 | C4b/c | 🟠 | Vuelta atrás: una aplazada la deshacía; con bucles en marcha no estaba definida | **A** | `RF-F03-11` (con bucles, no instala y lo dice), `CA-F03-13` |
| 12 | S10, C7, I-H8 | 🟡 | «Versión omitida» era estado oculto con contradicciones (fila 6 frente a E11) | **A** (alternativa de S10) | `RF-F03-10/11`: la vuelta atrás desactiva la actualización automática y `adevv actualizar` la reactiva; −1 campo; E11/E12 antiguos eliminados |
| 13 | C7 | 🟡 | `FALLIDA` con ventana de 6 h reinstalaba la misma versión rota; campos de avisos incompletos | **A** | `FALLIDA` cuenta como comprobación y guarda la versión fallida; solo se reintenta con una versión mayor o `adevv actualizar`; −1 ventana; campos de avisos completados en `§4` |
| 14 | C7 | 🟡 | Aviso diario de `DESARROLLO` sobra para un único usuario | **A** | `§4` fila 3: solo en `adevv --version` |
| 15 | C6, I-H7 | 🟠 | «Una orden que instala la última versión» no se puede escribir con uv sin fijar una etiqueta | **A** | `RF-F01-01` (README fija una versión y `adevv instalar` hace comprobación forzada), `CA-F01-01` |
| 16 | C6, S9, C9 | 🟡 | `RF-F01-02` (PATH) lo da el instalador; `RF-F01-08` (solo lectura) duplica `RF-F01-06` y rompe borrado/`--forzar` en Windows | **A** | Retirados; R0 remite al README |
| 17 | C8 | 🟡 | RF que son decisiones técnicas o consecuencias de otros | **P** | Retirados a `§6`: `RF-F01-10`, `RF-F05-02`, `RF-F05-04` (sustituido por `RF-F05-07`, observable). Fusionados: `RF-F02-02`→`01`, `RF-F02-04`→`03`, `RF-F02-08b`→`08`. **Se mantiene** `RF-F03-08`: es la garantía observable de que un proceso en marcha no se rompe |
| 18 | C3 | 🟠 | Eliminar `adevv migrar` (solo dos migraciones reales) | **P** | Se mantiene la orden (verifica CE-2 y la migración del propio Adevv, y apoya los pasos del README); se retiran `RF-F04-04` (bloqueo de un diagnóstico de solo lectura) y `RF-F04-05` (códigos de salida); se añade a `RF-F02-07` la negativa a lanzar con el submódulo presente. Rechazado bajar a 4 maestras: F-04 tiene valor propio (CE-2) y cabe en el presupuesto |
| 19 | I-H11, C | 🔵 | Unidades de recuento de `migrar`; seguir enlaces recorre el submódulo entero | **A** | `RF-F04-01/02`, `CA-F04-01` (9 pendientes, recalculado), `CA-F04-02` |
| 20 | I-H3 | 🟠 | `CA-F02-04` fallaría siempre: el código del paquete debe contener `.agents` y `orquestar.py` (detección); Codex podría usar `~/.agents/skills` | **A** | `RF-F02-05`, `RF-F01-04`: solo archivos de instrucciones y solo rutas relativas que empiezan por `.agents/` |
| 21 | I-H9 | 🟡 | «Elementos locales» sin lista de carpetas | **A** | `RF-F02-07` |
| 22 | I-H10, C12 | 🟡 | `task_config.yaml` mínimo sin `levels.master` (el motor lo lee); repo sin commits rompe el cambio de rama; regla de prefijo con RF propio | **A** | `RF-F02-08` (contenido mínimo, commit inicial, prefijo con `PRJ` de reserva: «Q1» → `PRJ`) |
| 23 | S7 | 🟡 | Escribiría en carpetas de Antigravity/Codex no confirmadas y diría «sincronizado» | **A** | `§4` (`NO_DETECTADO` «sin confirmar»), `RF-F01-03`, `CA-F01-02`, `§6` |
| 24 | S8 | 🟡 | Borrado recursivo de carpetas retiradas; rutas del registro fuera del destino | **A** | `RF-F01-05/07`, `CA-F01-07/08` |
| 25 | C9 | 🟡 | Primera instalación: sin registro, toda copia previa sería conflicto | **A** | `RF-F01-09`, `CA-F01-09` |
| 26 | S6 | 🟠 | El origen es público: hacer de Adevv un proyecto Adevv publica su backlog, nombres de proyectos y rutas personales | **P** | No se decide sin el usuario (visibilidad de su repositorio): `PQ-03` con valor por defecto que no rompe nada; la spec funciona con origen público o privado (`RF-F03-03`, `§6`) |
| 27 | S12 | 🔵 | Los avisos se pierden en Codex/Antigravity | **P** | `RF-F03-13` incluye workflows y adaptadores; `RF-F01-12` muestra el último `APLICADA`/`FALLIDA` |
| 28 | C11 | 🟡 | CE-1 con Antigravity choca con «sin cambios en proyectos» si Antigravity solo lee por proyecto | **P** | CE-1 se conserva literal con una nota de condición (`PQ-01`); no se reescribe un criterio del usuario |
| 29 | C11 | 🔵 | `req_analysis.md` no existía y `alcance.md` citaba IDs antiguos | **A** | `req_analysis.md` creado; `alcance.md` D1-D5 corregidos |
| 30 | I-H8 (esc. 3) | 🔵 | Tras aplicar una aplazada, la siguiente versión espera 24 h más | **R** | Retraso ≤ 24 h aceptable para un único usuario; evita otra regla de tiempo |
| 31 | C4a, I (E7) | 🔵 | E7 no mostraba la fecha del aviso | **A** | Tabla de ejemplos rehecha (E1-E13) con todas las precondiciones |

**Recalculado tras integrar:** tabla E1-E13 y `CA-F03-01` (10 filas) contra `§4`; prefijos `MIA`, `PRJ`, `NAN` contra `RF-F02-08`; `CA-F04-01` = `.gitmodules` + `.agents` + 6 líneas de `AGENTS.md` + `orchestration.json` (una vez) = 9; `CA-F04-05` 35 → 20 + 15. Trazabilidad: 39 RF, 38 con CA; `RF-F04-06` por inspección y validación funcional.

**Complejidad neta de la ronda:** −8 RF (47 → 39), −1 campo (versión omitida), −1 ventana de tiempo (6 h), −2 tipos de proceso que bloquean; +1 RF (`RF-F01-13`, sustituye un bloqueo), +2 definiciones (repositorio fuente, instalación de desarrollo).

## Juez (Hades)

### Iteración 1 · RECHAZADO (media 7,17)

Coherencia 6 · Completitud 8 · Simplicidad 7 · Verificabilidad 7 · Privacidad por defecto 7 · Implementabilidad 8. Confirma aplicados los 31 hallazgos de la ronda 1 y correctos todos los ejemplos recalculados (E1-E13, `CA-F03-01`, prefijos, recuentos de F-04).

| # | Sev. | Hallazgo | Decisión | Aplicado en |
|---|---|---|---|---|
| J1 | 🟠 | El respaldo de CE-1 para Antigravity («sigue con los workflows del proyecto») choca con `RF-F02-07`/`RF-F04-02`, que los tratan como elementos que ocultan | **A** | CE-1 (nota): «queda pendiente de la revisión de versión (`PQ-01`)»; `PQ-01` |
| J2 | 🟠 | `adevv instalar` con «comprobación forzada» consultaba la red con la actualización desactivada y deshacía la vuelta atrás | **A** | `RF-F01-01` (comprobación de `§4` sin la fila 4, que respeta la desactivada); `§4` |
| J3 | 🟠 | No estaba definido si `adevv actualizar X.Y.Z` pasa por la comprobación; `CA-F03-14` no era determinista | **A** | `RF-F03-11` (no la hace; solo valida X.Y.Z), `§4`, `CA-F03-14` (instalada 0.1.0) |
| J4 | 🟡 | La versión aplazada no se borraba tras aplicarse | **A** | `§4` (nota bajo la tabla) |
| J5 | 🟡 | `CA-F01-10` no determinista (aplicaría antes una actualización) | **A** | `CA-F01-10` (actualización automática desactivada) |
| J6 | 🟡 | Aviso de resincronización aplazada sin fecha propia | **A** | `§4` Estado de actualización |
| J7 | 🟡 | Faltaba el bloque Entorno del original | **A** | `§6` Entorno (literal); `§1` corregido |
| J8 | 🟡 | R0 «con o sin git y `task_config.yaml`» no cubría «git sin `task_config.yaml`» | **A** | R0 |
| J9 | 🟡 | Privacidad del origen público (para el humano) | **Registrar** | `PQ-03` con el hecho comprobado: `91bc9af` ya está en `origin/main` |
| J10 | 🔵 | Formato del enlace en `CA-F04-02` | **A** | `CA-F04-02` |
| J11 | 🔵 | «5 más recientes» ambiguo | **A** | `RF-F03-12` («5 mayores») |
| J12 | 🔵 | `CA-F02-09` no probaba la protección de la carpeta personal ni la raíz de unidad | **A** | `CA-F02-09` |
| J13 | 🔵 | «Aviso de una línea» frente a líneas añadidas | **Descartar** (lo propone el juez) | — |

### Iteración 2 · APROBADO (media 8,25)

Coherencia 8 · Completitud 9 · Simplicidad 8 · Verificabilidad 8 · Privacidad por defecto 8 · Implementabilidad 8,5. Confirma J1-J12 aplicados sin contradicciones nuevas y todos los ejemplos recalculados correctos (E1-E13, `CA-F03-01`, prefijos, recuentos de F-04, `CA-F03-14`, `CA-F04-04` contra el repositorio real). Sin 🔴 ni 🟠; los 🟡/🔵 se aplican sin relanzar al juez:

| # | Sev. | Hallazgo | Decisión | Aplicado en |
|---|---|---|---|---|
| K1 | 🟡 | Sin `requirements.md` ni `task_config.yaml` el motor para hoy por configuración, no por idea | **A** | `RF-F02-08`, `CA-F02-09` |
| K2 | 🟡 | `prefijo()` del motor lee `project.prefix`, no `id_prefix` | **A** | `RF-F02-08` (`project.prefix`), `CA-F02-08` |
| K3 | 🟡 | `CA-F03-03` sin precondición de ventana | **A** | `CA-F03-03` |
| K4 | 🟡 | `CA-F03-10` dependía de Antigravity (`PQ-01`) | **A** | `CA-F03-10` con Codex |
| K5 | 🟡 | Aplazada frente a `adevv actualizar` con una publicada mayor | **A** | `§4` (nota) |
| K6 | 🟡 | Mensajes sin red en `adevv instalar` y `adevv actualizar X.Y.Z` | **A** | `§4` fila 5, `RF-F03-11` |
| K7 | 🟡 | `README.md` sin ruta podía contar el del submódulo | **A** | `RF-F04-03` (raíz; `.agents` no se recorre) |
| K8 | 🔵 | `CA-F03-13` sin la 0.2.1 publicada | **A** | `CA-F03-13` |
| K9 | 🔵 | Aviso de `APLAZADA` 1 vez cada 24 h sin verificación | **A** | F-03 «Otras verificaciones» (E8, E10) |
| K10 | 🔵 | §1 «literal» con anotaciones del ciclo | **A** | Anotaciones marcadas _(ciclo)_ |
| K11 | 🔵 | `adevv actualizar X.Y.Z` con la instalada | **A** | `RF-F03-11` |
