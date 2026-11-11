# B-ADV-0036 · Revisión de especificación

**Veredicto de Hades: APROBADO (9,00/10).**

## Revisión de las decisiones y del delta BDD

Hades revisó DEC-36-1/2/3, los ocho criterios y el delta exacto de la característica. Emitió el dictamen mediante la reserva autorizada tras el fallo de acceso de Claude. El revisor trabajó sobre los adjuntos porque su entorno rechazó la lectura local. Recibió íntegra la skill de revisión. Reutilizó la evidencia dirigida de la base (árbol `c0c1338aca`, 16 pruebas en 33,677 s, OK).

| Comprobación | Dictamen |
|---|---|
| No regresión | Conforme. La decisión sustituye expresamente el bloqueo automático. El esquema conserva sus seis filas bajo las precondiciones de igual causa y dictamen humano justificado. |
| Coherencia | Conforme. Se conservan el ID por versión y comando, la promoción desde media, los bloqueos y cancelaciones previos y el cierre solo en verde. |
| Trazabilidad | Conforme. Los ejemplos de los tres destinos y sus etiquetas corresponden a los criterios del bug. |
| Delta real | Conforme. Los cambios especifican el diagnóstico en el umbral, el destino, el presupuesto causal y el resultado terminal. |

Claridad 9, completitud 8, testeabilidad 9 y estructura 10. Hades dio por resueltos F-01 (sustitución del contrato), F-02 (identidad causal y finitud) y F-03 (CA 8 y delta BDD). No encontró hallazgos críticos ni altos. La implementación y sus regresiones corresponden al desarrollo posterior.

**F-04 · Media, para el especificador, no bloqueante.** Faltaba un ejemplo de imposibilidad técnica acreditada desde el primer dictamen, con una intervención concreta y sin otro arreglo ni diagnóstico al retomar. Enrutado mediante `--enrutar-hallazgo`.

## Reevaluación de F-04

**APROBADO. F-04 resuelto, sin hallazgos nuevos ni acción pendiente.** Hades evaluó únicamente el escenario añadido sobre la revocación irreversible de un certificado. El primer dictamen cita la evidencia y pide al titular un reemplazo. Al retomar sin ese recurso se conservan tres intentos, una pregunta y un diagnóstico. Las cuatro comprobaciones obligatorias son conformes. Claridad 9, completitud 9, testeabilidad 10 y estructura 10 (9,50/10 para este delta). Se mantiene la aprobación previa del resto.

El revisor recibió el rol, la skill y el escenario íntegros como adjuntos por la reserva autorizada. Aceptó la evidencia de `SuiteRecoveryTests` del árbol `071a094c3c` (16 pruebas en 35,151 s, código 0). La revisión cubre la especificación. Las regresiones ejecutables del comportamiento nuevo corresponden a Artemisa.
