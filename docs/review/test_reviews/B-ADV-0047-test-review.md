**Veredicto:** APROBADO

# B-ADV-0047 · Revisión de pruebas

Revisor: Hades. Modo orquestado. Revisión única del delta completo respecto de `ea1ebfc524d471f723fc4e926b12b738717f8998` en `tests/test_control_intervenciones.py`, `tests/test_orquestar.py` (solo `SuiteRecoveryTests`) y `tests/test_revision_release.py`. Referencia: [triaje del bug](../../plan/bugs/B-ADV-0047-suite-roja-al-cerrar-version.md). Los contratos existentes se mantienen; no se revisa especificación, arquitectura ni implementación de producción.

## Puntuaciones

| Criterio | Puntuación | Fundamento |
| --- | --- | --- |
| Cobertura | 9/10 | El delta repara las tres áreas reproducidas: incorporación y bloqueo de respuestas, recuperación de diagnóstico y ausencia de mutaciones al revisar el cierre. Conserva los casos funcionales existentes. |
| Aserciones | 9/10 | Siguen comprobándose estados persistidos, respuestas, lanzamientos únicos, commits, recuperación idempotente y referencias/índice/archivos. Ninguna aserción funcional se elimina ni se satisface mediante un resultado Git prefabricado. |
| Rojo correcto | 9/10 | La evidencia anterior identifica fallos de montaje y observación, no errores de importación o sintaxis. El ajuste restablece los oráculos existentes: no acredita una funcionalidad nueva ni cambia el contrato para obtener verde. |
| Estabilidad | 9/10 | Git opera en el repositorio temporal de cada fixture, las dos salidas modificadas se decodifican como UTF-8 y la instantánea deja de depender de la creación del candado operativo. |

Media: **9/10**. Sin hallazgos críticos ni altos.

## Evaluación del delta

En `ControlIntervencionesTests`, `patch.object(motor, 'git', side_effect=self.git)` delega en un subproceso Git real con `cwd=self.root` y `check=True`. No sustituye el estado del repositorio por valores esperados y se restaura mediante `enterContext`. Las comprobaciones de persistencia, bloqueo, deduplicación y relanzamiento conservan capacidad de detectar regresiones. Los procesos CLI independientes siguen ejecutándose con el repositorio temporal como directorio real.

Los helpers Git de esta clase y de `SuiteRecoveryTests` declaran `encoding='utf-8'`. Conservan ejecución, argumentos, comprobación del código de salida y aserciones, incluidas las que observan el mensaje «aplicar diagnóstico de la suite» después de fallos de add/commit y recuperación. Se corrige la interpretación de los bytes, sin normalizar o reemplazar el contenido esperado.

En `RevisionesReleaseTests.snapshot`, la exclusión nueva coincide únicamente con `.adevv-metricas/registro.lock`. No excluye el directorio de métricas completo ni las copias de recuperación; los archivos restantes siguen comparándose por bytes. Permanecen las observaciones de referencias locales/remotas, rama e índice. La igualdad anterior/posterior sigue detectando mutaciones funcionales.

## Evidencia y límites

Se reutiliza la evidencia local de `orquestar_evidencias.jsonl` (nombre presente en este árbol; la invocación menciona `orquestar_verificaciones.jsonl`). El mismo comando dirigido, ejecutado mediante `adevv orquestar --verificar`, registró:

`python -m unittest tests.test_control_intervenciones tests.test_orquestar.SuiteRecoveryTests tests.test_revision_release`

- Antes: 50 pruebas, 11 fallos, 100.344 s.
- Después: 50 pruebas, OK, 104.989 s; árbol `07cc3ebfcdddde82d5c67b64cff1e4a34db7686c`.
- `git diff --check`: código 0, mismo árbol.

No se repiten las pruebas ni se ejecuta la suite completa. La evidencia verde avala la ejecución dirigida; el juicio sobre la discriminación de las pruebas procede de la lectura del delta y sus fixtures.

Se ejecuta `adevv orquestar --calidad --base ea1ebfc524d471f723fc4e926b12b738717f8998` sin `--aplicar`: código 0. Formato y lint omitidos por ausencia de herramientas, sin configuración aplicable según el triaje; estas omisiones no se presentan como herramientas ejecutadas en verde. No hay tipado configurado ni dependencias modificadas.

## Hallazgos y destino

No se identifican hallazgos en el delta revisado; no procede asignar destinatarios ni destinos.
