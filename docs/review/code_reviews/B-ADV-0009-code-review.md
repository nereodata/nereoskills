# Revisión de código — B-ADV-0009

**Veredicto: APROBADO. Media: 9/10.** H1 resuelto; sin hallazgos nuevos ni pendientes.

## Alcance y método

Reevaluación única e integrada del delta completo respecto a HEAD de:

- `adevv/updater.py`, `adevv/sync.py` y `adevv/cli.py`.
- `README.md` y `CHANGELOG.md`.
- `docs/requirements/platform_plan.md` y `docs/design/B-ADV-0009-design.md`.

Fecha: 2026-10-27. Modo orquestado, aplicando Hades y `/review-code` leídos de `C:/Users/Iván Moreno/.adevv/versions/0.6.1/` e ignorando el modelo del frontmatter. Referencias: triaje del bug, diseño actual, DEC-P13 y especificación corregida aprobada 9/10. Se consultó la nueva aprobación de pruebas 9/10, sin reabrir su revisión ni leerlas como objeto de review-code.

Se revisa el conjunto de instalación, activación, copias, limpieza y avisos, junto a su documentación; no son aprobaciones por archivo ni una revisión limitada a H1. Se coteja además la corrección desde el árbol de la revisión anterior `e5e2c159952ff996c80322b826b18a844eba19c7`: la producción incorpora la restauración del puntero en la reutilización local y el diseño la documenta. El diseño nuevo se leyó directamente como archivo del árbol de trabajo, incluido su contenido no versionado todavía.

Se excluyen los cambios concurrentes ajenos del buzón/configuración y cualquier cambio de estados. No se ejecutaron pruebas ni comprobaciones estáticas, ni se modificó producción, pruebas o estados. La única modificación de esta actuación es este informe; no se crea commit.

## Evidencia renovada y análisis estático

Se reutiliza `orquestar_evidencias.jsonl`, árbol `ead77297bc18ca97239eee6730d0384d3a85dfa4`. Las diez entradas de 06:36:05 a 06:36:56 tienen código 0 y constan mediante `adevv orquestar --verificar`:

| Comando registrado | Resultado |
| --- | --- |
| `python -m unittest tests.test_updater.TestUpdaterIntegrationAndCli.test_instalar_reutiliza_version_sin_puntero_y_no_la_limpia` | Verde; regresión dirigida de H1 |
| `python -m unittest discover -s tests -p test_updater.py` | Verde; 31 pruebas según evidencia entregada |
| `python -m unittest discover -s tests -p test_sync.py` | Verde; 15 pruebas |
| `python -m unittest discover -s tests -p test_cli_commands.py` | Verde; 10 pruebas |
| `python -m unittest discover -s tests -p test_install_and_release.py` | Verde; 8 pruebas |
| `python -m unittest discover -s skills/orquestar -p test_recarga.py` | Verde; 11 pruebas |
| `python -m unittest discover -s skills/telegram_gateway -p test_recarga_gateway.py` | Verde; 7 pruebas |
| `python -m py_compile adevv/updater.py adevv/sync.py adevv/cli.py tests/test_updater.py tests/test_sync.py` | Verde |
| `git diff --check` | Verde |
| `python .git/B-ADV-0009-check-secrets.py` | Verde |

Los seis comandos exactos del triaje suman 82 pruebas según los recuentos recibidos; la ejecución dirigida de H1 es adicional. No se presenta como suite completa. No hay linter ni tipado configurados ni cambios de dependencias según el contexto entregado; no se exige auditoría de dependencias sin cambios.

Se cotejaron los siete artefactos actuales con sus blobs en el árbol de evidencia mediante `git ls-tree` y `git hash-object`: todos coinciden. En particular, updater coincide con `5929f7fcc94c80145153800e0ce0052f783766de` y el diseño con `a74e855bf3f0f13297e7890620349d970f004a48`. Las verificaciones estáticas, de secretos y funcionales se reutilizan sin repetirlas. Esa evidencia es anterior a este informe actualizado y no verifica su escritura.

## Puntuaciones

| Dimensión | Nota | Valoración |
| --- | --- | --- |
| Corrección | 9/10 | Instalación con procesos vivos, consumo heredado y copias diferidas coherentes. La reutilización local restaura ahora el puntero antes de la limpieza, conservando la carpeta. |
| Seguridad | 9/10 | Sin shell, credenciales ni dependencias nuevas. Se conservan filtrado de instalación y planificación segura de destinos. Escaneo de secretos acreditado en verde. |
| Conformidad | 9/10 | Sigue el triaje, diseño y DEC-P13: instalación versionada separada de copias, ancestros protegidos por ORQUESTAR_PASO y recarga existente sin reimplementación. |
| Calidad | 9/10 | Guarda compartida y activación/mensaje publicados centralizados. Las dos rutas locales, nueva y reutilizada, conservan efectos de activación coherentes para el llamante. |
| Eficiencia | 9/10 | Reutiliza carpetas válidas sin descargar ni rematerializar y no añade polling. Conserva ventanas y consulta heredada sin volver a listar versiones. |
| Documentación | 9/10 | README, changelog, diseño y plan explican instalación inmediata, conservación de versiones, copias pendientes y adopción cooperativa o manual. El diseño incorpora expresamente la recuperación del puntero. |

**Media: (9 + 9 + 9 + 9 + 9 + 9) / 6 = 9/10**, superior a 8 y sin hallazgos críticos ni altos pendientes.

## Reevaluación de H1 y enrutado

| Hallazgo anterior | Gravedad anterior | Estado | Para | Destino |
| --- | --- | --- | --- | --- |
| H1 — Reutilizar una versión local no restaura el puntero y la limpieza puede borrarla | 🟠 ALTA | **Resuelto** | `desarrollador` | `resolver`: corrección satisfecha, sin acción pendiente |

En `materializar_version_local`, la rama de carpeta existente valida primero su versión. Después escribe el puntero mediante `set_active_info`, con versión/id y origen local publicado coherentes con la rama de materialización nueva, y retorna sin sobrescribir el contenido de la carpeta.

Por tanto, cuando `comando_instalar` continúa hacia `limpiar_versiones_antiguas`, el puntero ya identifica esa versión como activa y la limpieza la excluye. Se resuelve tanto la ausencia de activación como su consecuencia destructiva. La escritura del puntero precede al retorno; no se elude la validación de carpeta ni se introduce rematerialización por `--forzar`.

La regresión CLI real sin puntero consta ahora en verde sobre el mismo árbol; su revisión aislada de pruebas permanece aprobada. Esto aporta evidencia adicional al seguimiento del flujo de código, sin convertir las pruebas en objeto de esta revisión.

## Valoración del conjunto

El evaluador automático instala con bucles y consume los aplazamientos heredados sin esperar a que finalicen. APLAZADA permanece como señal interna de entrada; no se generan nuevos estados terminales de instalación aplazada. Se preservan los caminos de error, SIN_RED y actualización de estado.

La instalación publicada valida y reutiliza carpetas existentes; una carpeta de versión incorrecta falla sin reemplazarla. Las carpetas nuevas se preparan en staging y se publican por renombrado antes de activar el puntero. La activación está separada de las copias globales, por lo que el cambio de versión no queda bloqueado por los bucles.

La guarda común de sincronización considera tanto bucles enumerados como ORQUESTAR_PASO, protegiendo el motor ancestro excluido por el detector. Con la guarda activa no se escriben ni borran archivos globales ni registros, tampoco con `--forzar`; se comunican las copias pendientes. El instalador evita cargar un sincronizador entrante antiguo cuando las copias no son seguras. La limpieza de versiones también se aplaza con bucles o pasos.

La CLI dirigida permite instalar y retroceder con bucles; conserva el tratamiento de versiones inexistentes y la desactivación de autoactualización al elegir una anterior a la última publicada. Los avisos nuevos se envían a stderr y distinguen recarga cooperativa, reinicio manual y copias sin sincronizar. `--forzar` sigue afectando a las copias permitidas, no a la elección o rematerialización de la versión activa.

La recarga existente del bucle y gateway no cambia. El comportamiento y los mensajes son compatibles con DEC-P13 y con la primera orden elegible sin bucles/pasos que reintenta las copias. Los cambios de README, changelog y plan reflejan ese contrato; no se observa otra divergencia material del diseño o de la especificación aprobada.

## Hallazgos nuevos y salida orquestada

Ninguno. No quedan acciones para `desarrollador`, `especificador` o `humano`, ni hallazgos con destino `registrar` o `descartar`. El delta completo recibido queda aprobado en review-code. Esta actuación no cierra el bug ni cambia su estado o crea commit.
