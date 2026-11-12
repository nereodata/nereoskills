# Revisión de especificación · B-ADV-0048

**Veredicto formal: APROBADO. Media: 9,25/10.**

Segunda ronda sobre el esquema y los tres escenarios de `tests/features/uso_sin_rutas.feature`. La primera ronda rechazó la especificación con una media de 7,75/10.

| Obligatoria | Resultado |
| --- | --- |
| No regresión | ✅ El delta añade los casos al final del fichero y conserva los escenarios previos. |
| Coherencia | ✅ Los destinos de desarrollo y el bloqueo sin asignación son compatibles con la ficha. |
| Trazabilidad | ✅ Cada escenario identifica la ficha mediante `@B-ADV-0048`. La ficha numera los criterios sin etiquetas `@CA-*`. |
| Delta real | ✅ La atribución del rechazo de reserva y la recuperación del encargo tras el bloqueo son comportamientos específicos del bug. |

| Dimensión | Nota |
| --- | ---: |
| Claridad | 9 |
| Completitud | 9 |
| Testeabilidad | 9 |
| Estructura | 10 |

## Seguimiento de la primera ronda

- **RS-01 · Resuelto.** El dictamen reproduce el Markdown del incidente. El escenario negativo exige que una cita, un ejemplo o la ausencia de declaración dejen pendiente la revisión.
- **RS-02 · Resuelto.** El esquema parte del rechazo de Codex y alcanza la entrega inmediata o la espera de `bug-fix` hasta recuperar cuota. El caso de recuperación histórica comprueba que el aviso identifica el bug, el paso y el perfil de Artemisa.
- **RS-03 · Resuelto.** El encargo debe aislar el fallo y acreditar la corrección del cierre. El escenario histórico exige conservar la intervención y la condición de salida al relanzar. La devolución del mismo impedimento y un arranque posterior conservan la parada técnica.

## Hallazgos nuevos

- **RS-04 · Resuelto durante la revisión.** La columna `disponibilidad` determina el estado inicial de cada fila. Una fila proporciona a Artemisa un perfil con cuota y la otra agota todos sus perfiles antes de la entrega.
