# Revisión de especificación: B-ADV-0005 (segunda ronda)

- **Artefacto**: `skills/orquestar/features/orquestacion.feature` (7 escenarios/esquemas)
- **Origen**: `docs/plan/bugs/B-ADV-0005-arnes-no-encontrado-conmuta-a-reserva.md` (comportamiento esperado 1-4, DEC del triaje, H-01, H-02, DEC-ESP-01 y DEC-ESP-02)
- **Revisor**: Hades (reevaluación aislada, sin diseño, código ni pruebas)
- **Fecha**: 2026-10-26 · **Modo**: orquestado

## Veredicto: APROBADO

Media 8,75 y sin hallazgos 🔴 ni 🟠.

## Hallazgos de la ronda anterior

- **H-01 (🟡). «Filtrable» no estaba especificado: resuelto.** El nuevo escenario «Filtrar las notificaciones de ausencia» lo concreta así: con `telegram.eventos` igual a solo `error`, se ejecuta la reserva y el warning sale por consola, pero no se envía el aviso `arnes`; con la configuración por defecto, sí se solicita y en él se identifica el ejecutable ausente.
- **H-02 (🟡). «Ningún ejecutable disponible» no decía el flujo ni los avisos: resuelto.** El escenario se aplica ahora por separado a paso, agente Hades y conversación del gateway. Además, exige que cada configuración ausente deje su warning, su métrica con consumo cero y su aviso `arnes` identificando el arnés, antes del aviso de error y sin espera de cuota. Es coherente con H-01 del especificador.
- **H-03 (🟡). El error distinto de ausencia era vago: resuelto.** Ahora la configuración es concreta: principal claude disponible que falla por autenticación, con reserva codex disponible. El resultado es observable en cada flujo: se conserva el código de fallo en paso y agente, el gateway informa del error de autenticación, codex no recibe ninguna petición y no hay métricas de arnés ausente.
- **H-04 y H-05 (🔵, `descartar`):** siguen igual, por decisión de la ronda anterior.

## Obligatorias

- ✅ **No regresión**: los tres esquemas originales y el escenario de cuota no cambian. Los dos escenarios que se tocan, «Ningún ejecutable disponible» y «Un error distinto de ausencia», son del propio delta, que todavía no se había aprobado. Se amplían conservando y reforzando su sentido: no se sustituyen ni pierden ninguna exigencia. No se tocan escenarios de `tests/features/`.
- ✅ **Coherencia**: el escenario de autenticación cumple el contrato de `/orquestar` («cualquier otro fallo del arnés para el bucle»). El filtro usa el mecanismo `telegram.eventos` con todos los eventos por defecto. Se mantiene que la ausencia no equivale a cuota, y se cumple DEC-ESP-02: un aviso por cada configuración ausente y consumo nulo sin imponer nombres de campos.
- ✅ **Trazabilidad**: no hay etiquetas `@CA-*`. Cada escenario corresponde a un punto del bug: el filtro al punto 2, «Ningún ejecutable disponible» al punto 4 y a H-01, y el error de autenticación a la frontera del alcance.
- ✅ **Delta real**: el nuevo escenario de filtro no duplica ningún otro, y las ampliaciones no se solapan con los esquemas existentes.

## Puntuaciones

| Criterio | Nota |
|---|---|
| Claridad | 9 |
| Completitud | 9 |
| Testeabilidad | 9 |
| Estructura | 8 |
| **Media** | **8,75** |

## Hallazgos nuevos

- 🔵 **H-06 · Estructura: hay varios casos dentro de un mismo escenario** (`descartar`).
  - «Ningún ejecutable disponible» y «Un error distinto de ausencia» enumeran los flujos en el `Dado` («pruebo por separado…») en lugar de usar un `Esquema del escenario` con `Ejemplos`, como hacen los demás. Esa redacción, además, habla de la prueba y no del usuario.
  - «Filtrar las notificaciones de ausencia» mezcla en un solo `Entonces` el caso filtrado y el caso por defecto.
  - Se entiende y se puede probar, pero dos ejemplos lo harían más homogéneo.
- 🔵 **H-07 · Completitud: el escenario de autenticación no excluye de forma explícita el warning ni el aviso `arnes`** (`descartar`). Ya lo implica que no haya métricas de arnés ausente y que codex no reciba ninguna petición.
