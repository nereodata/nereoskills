# Revisión de especificación — B-ADV-0005

**Veredicto: RECHAZADO**  
**Enrutado para: especificador**  
**Fecha:** 2026-10-26  
**Modo:** orquestado, sin preguntas.

## Alcance y criterio

Revisión exclusiva de `skills/orquestar/features/orquestacion.feature` frente al contrato de `docs/plan/bugs/B-ADV-0005-arnes-no-encontrado-conmuta-a-reserva.md`, siguiendo Hades y `/review-spec` de la versión 0.6.0. No se han revisado código, pruebas ni diseño, ni ejecutado suites. Las referencias técnicas del contrato no se han utilizado para inferir comportamiento de la implementación.

El feature figura como archivo nuevo sin seguimiento; se revisa completo como delta. No se ha recibido un informe anterior para reevaluación.

## Obligatorias

| Regla | Resultado | Motivo |
|---|---|---|
| No regresión | ✅ | El archivo es nuevo y no presenta eliminación o alteración de escenarios preexistentes en el delta examinado. |
| Coherencia | ✅ | Los resultados descritos son compatibles con el contrato: ausencia recuperable, sesión separada al cambiar de arnés, aviso `arnes`, ausencia sin cuota y conservación de una cuota previa. Las lagunas de cobertura se detallan abajo. |
| Trazabilidad | ✅ | No hay etiquetas `@CA-*` que remitan a criterios inexistentes. Los escenarios corresponden al comportamiento esperado y a la decisión de cuota documentada en el bug. |
| Delta real | ✅ | Describe el cambio ante ejecutables ausentes y límites relevantes; no se observan escenarios duplicados en el artefacto. |

## Puntuaciones

| Criterio | Puntuación | Justificación |
|---|---:|---|
| Claridad | 8/10 | Flujos y efectos comprensibles; algunas comprobaciones carecen de datos concretos. |
| Completitud | 6/10 | Falta la continuidad a través de una reserva ausente cuando otra posterior está disponible. |
| Testeabilidad | 7/10 | Los efectos son observables, pero las métricas y el tiempo de recuperación no tienen valores de referencia. |
| Estructura | 10/10 | Feature ubicado en la funcionalidad de orquestación, sin organización por tarea, fase o versión. |

**Media: 7,75/10.** No alcanza el umbral superior a 8 y existe un hallazgo de severidad alta.

## Hallazgos

### H-01 — 🟠 ALTA: no se especifica saltar una reserva ausente y alcanzar otra posterior

- **Evidencia:** el esquema «Saltar configuraciones cuyo arnés no está instalado» parte únicamente de un principal ausente y una reserva disponible. «Ningún ejecutable disponible» solo cubre el agotamiento total. Ninguno exige continuar después de encontrar una reserva ausente.
- **Contrato:** la descripción incluye expresamente el perfil principal o reserva; el comportamiento esperado exige pasar a la siguiente reserva y permite el fallo por ausencia únicamente cuando ninguna configuración dispone de arnés.
- **Consecuencia:** la especificación permite que pase desapercibido un comportamiento que conmuta desde el principal pero se detiene ante una reserva ausente, dejando sin intentar otra posterior disponible. Es una variante directa del fallo que se pretende resolver.
- **Para:** especificador.
- **Destino:** resolver en la especificación de B-ADV-0005 antes de aprobarla.
- **Corrección necesaria:** añadir cobertura con una cadena ordenada y concreta —principal ausente, primera reserva ausente, segunda reserva disponible— para los tres consumidores del esquema. Exigir que la última reciba la petición y que cada intento ausente produzca los efectos de warning, métrica sin cuota y evento `arnes` ya comprometidos. El resultado debe distinguir la continuación correcta de un fallo prematuro por ausencia.

### H-02 — 🟡 MEDIA: faltan referencias concretas para métricas y recuperación de cuota

- **Evidencia:** «queda una métrica del intento ausente sin consumo ni señal de cuota» no fija cómo identificar ese intento; «conserva la señal y el tiempo de recuperación de cuota del principal» no aporta un tiempo inicial contrastable.
- **Consecuencia:** las comprobaciones pueden limitarse a constatar la existencia de cualquier métrica o cualquier tiempo de recuperación, sin discriminar una atribución equivocada o un tiempo sustituido.
- **Para:** especificador.
- **Destino:** resolver en el mismo feature.
- **Corrección necesaria:** identificar el arnés/configuración ausente en la salida observable de métricas, concretar el consumo nulo y la ausencia de señal de cuota, y proporcionar un instante de recuperación inicial que deba permanecer idéntico tras la reserva ausente. No requiere prescribir nombres internos de campos ni mecanismos de implementación.

## Salida de la revisión

Devolver al especificador para resolver H-01 y H-02 y solicitar una nueva revisión del delta. No se derivan hallazgos a código o diseño ni se propone deuda fuera de B-ADV-0005. Esta revisión solo crea este informe; no corrige los artefactos ni realiza commits.
