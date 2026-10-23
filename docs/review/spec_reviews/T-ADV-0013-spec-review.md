# Reporte de Revisión de Especificación: T-ADV-0013

- **ID Maestro**: T-ADV-0013
- **Artefacto revisado**: [`docs/plan/tasks/T-ADV-0013-comando-adevv-metrics-exportacion-csv-y-coste.md`](../../plan/tasks/T-ADV-0013-comando-adevv-metrics-exportacion-csv-y-coste.md) (impedimento de especificación/alcance y triaje)
- **Veredicto**: **RECHAZADO**

## Comprobaciones Obligatorias

- **No regresión**: ✅ No se eliminan ni alteran escenarios existentes.
- **Coherencia**: ❌ **Fallo crítico**. `CA-M-1` exige literalmente que `adevv/cli.py` registre los subcomandos `metrics` y `metricas` (y `CA-M-4` exige cubrirlo con pruebas unitarias), lo cual contradice la restricción de alcance del mandato de ejecución («Los cambios se hacen en `skills/`, `agents/` y `workflows/` del árbol de trabajo»). Verificado `adevv/cli.py`, la tabla de subcomandos de `argparse` (`instalar`, `actualizar`, `orquestar`, `telegram`, `release`, `migrar`) es cerrada y estática: no existe ningún mecanismo de descubrimiento ni punto de extensión que permita registrar nuevos subcomandos de primer nivel (`adevv metrics` / `adevv metricas`) desde `skills/`, `agents/` o `workflows/`.
- **Trazabilidad**: ❌ **Fallo crítico**. No existen escenarios BDD (`.feature`) que tracen `@CA-M-1`..`@CA-M-4` debido al bloqueo en Subfase A por el impedimento de alcance.
- **Delta real**: ❌ **Fallo crítico**. La tarea está detenida en el triaje sin especificación ejecutable (`.feature`) debido a la contradicción entre el contrato exigido en `CA-M-1` y las rutas autorizadas.

## Puntuaciones

- **Claridad**: 7/10 (los criterios `CA-M-1`..`CA-M-4` son claros funcionalmente, pero el alcance permitido para satisfacer `CA-M-1` es contradictorio con el contrato).
- **Completitud**: 2/10 (sin escenarios BDD generados por bloqueo previo de alcance).
- **Testeabilidad**: 4/10 (`CA-M-1` no es verificable dentro de las rutas autorizadas sin editar `adevv/cli.py`).
- **Estructura**: 5/10 (el triaje e impedimento están documentados en la tarea, pero falta el delta en `.feature`).
- **Media**: **4.5/10**

## Hallazgos

### 1. 🔴 CRÍTICO — Contradicción inviable entre `CA-M-1` (`adevv/cli.py`) y las rutas autorizadas del mandato
- **para:** `especificador`
- **Descripción**: [`CA-M-1`](../../plan/tasks/T-ADV-0013-comando-adevv-metrics-exportacion-csv-y-coste.md#L21) exige que [`adevv/cli.py`](../../../adevv/cli.py#L328-L390) registre los subcomandos `metrics` y `metricas` despachando al generador de métricas y soportando `--version` / `-v`. Sin embargo, el mandato de ejecución restringe los cambios exclusivamente a `skills/`, `agents/` y `workflows/`. Al inspeccionar [`adevv/cli.py`](../../../adevv/cli.py#L325-L390), se confirma que:
  1. `subparsers` define una lista cerrada de subcomandos (`instalar`, `actualizar`, `orquestar`, `telegram`, `release`, `migrar`) sin carga dinámica desde `skills/`, `agents/` ni `workflows/`.
  2. Además, el parser raíz captura `-v` / `--version` (`action="store_true"`) antes de despachar cualquier subcomando ([`adevv/cli.py`](../../../adevv/cli.py#L326-L349)), por lo que incluso si se invocara mediante un subcomando existente, `--version` / `-v` requeriría modificar `adevv/cli.py` si el punto de entrada es `adevv metrics`.
  Por tanto, el impedimento declarado en el triaje es legítimo y **no es solucionable por el desarrollador** respetando simultáneamente `CA-M-1` y las rutas permitidas.
- **Qué necesita el especificador para resolverlo**:
  Resolver la contradicción de alcance eligiendo una de estas dos opciones de contrato antes de reanudar `task-dev`:
  1. **Ajustar el contrato (`CA-M-1` / `CA-M-4`) a las rutas autorizadas**: especificar la invocación dentro de `skills/` (por ejemplo, como script o flag bajo una skill existente despachada como `skills/orquestar/orquestar.py` o `skills/metrics/...`) sin exigir el registro en `adevv/cli.py` ni tests fuera de las rutas permitidas; **o bien**
  2. **Ampliar el alcance de rutas autorizadas de la tarea/proyecto**: autorizar explícitamente la edición de `adevv/` (en particular `adevv/cli.py`) y `tests/` para poder registrar los subcomandos `metrics` y `metricas` y sus pruebas unitarias conforme a `CA-M-1` y `CA-M-4`.
