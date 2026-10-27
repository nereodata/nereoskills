# Revisión de especificación B-ADV-0020

**Veredicto: RECHAZADO**

Fecha: 2026-10-27. Modo: orquestado. Revisor: Hades. Ronda: 2.

## Alcance y método

Reevaluación de H1–H3 del informe anterior y del delta de escenarios `@B-ADV-0020` en `skills/orquestar/features/orquestacion.feature`, frente al contrato del bug `docs/plan/bugs/B-ADV-0020-marca-de-agotado-a-ciegas-impide-usar-modelo-con-cuota.md`, incluido triaje y decisiones. Se aplicó la skill instalada de la versión 0.6.1. No se revisaron código, diseño ni pruebas; no se ejecutaron pruebas ni suite completa.

Las correcciones añaden recuperación del registro histórico de 1800 segundos, ejemplos de intervalo configurado y conservación de marcas ajenas al selector. El cambio autorizado de espera supuesta de 1800 a 300 segundos no constituye un hallazgo. Los escenarios no afectados por las correcciones no se someten a una nueva revisión de fondo.

## Obligatorias

| Criterio | Resultado | Evidencia |
| --- | --- | --- |
| No regresión | ✅ | El diff frente a la base conserva los escenarios anteriores al bug; las correcciones amplían los escenarios de B-ADV-0020. |
| Coherencia | ✅ | La recuperación histórica de 1800 segundos y el intervalo configurable siguen el triaje. No se observa contradicción expresa con el contrato; quedan las omisiones y la ambigüedad señaladas abajo. |
| Trazabilidad | ✅ | El delta lleva `@B-ADV-0020` y corresponde a decisiones del bug; no incorpora etiquetas `@CA-*` sin criterio de origen. |
| Delta real | ✅ | Los casos añadidos distinguen registros históricos y valores configurados; la aserción del reset pretende proteger pares ajenos. |

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Claridad | 8/10 | El nuevo paso del reset deja ambiguo el referente de «esos perfiles». |
| Completitud | 7/10 | Se cubre el incidente histórico principal, pero falta la otra rama de compatibilidad y la opción de intervalo omitida. |
| Testeabilidad | 9/10 | Los nuevos casos aportan valores y resultados observables. |
| Estructura | 9/10 | El delta permanece en el feature de orquestación. |

**Media: 8,25/10.** H1 mantiene severidad alta e impide aprobar.

## Reevaluación de hallazgos anteriores

### H1 — 🟠 ALTA — PERSISTE parcialmente: compatibilidad de los demás registros históricos

- **Resuelto:** las líneas 262–265 parten de un registro sin clasificación de 1800 segundos y antigüedad de 60 segundos; exigen comprobar al titular y registrar recuperación sin reescribir el registro antiguo. Cubren la marca que originó el fallo.
- **Persiste:** no hay un caso de registro histórico sin clasificación con duración distinta de 1800 segundos que conserve su recuperación registrada, como exige expresamente el triaje y pedía H1. El escenario de recuperación confirmada parte de una marca confirmada, sin establecer que proceda de ese formato histórico.
- **Impacto:** interpretar todos los registros históricos sin clasificación como sospechas seguiría satisfaciendo los escenarios, pero permitiría probar antes de tiempo perfiles cuya recuperación anterior debe respetarse.
- **para:** especificador.
- **destino:** resolver.
- **Corrección requerida:** añadir un registro histórico sin clasificación de duración distinta de 1800 segundos, aún vigente, y exigir que al relanzar conserve su recuperación y no se pruebe el titular antes de ella. Por ejemplo, duración de 3600 segundos y antigüedad de 60 segundos, con reserva disponible.

### H2 — 🟡 MEDIA — PERSISTE parcialmente: intervalo por defecto cuando se omite la opción

- **Resuelto:** las líneas 268–278 incluyen 120 segundos y resultados concretos para cero, un negativo, texto y null. El comportamiento ante valores no positivos ya tiene resultado observable: recurrir a 300 segundos.
- **Persiste:** ningún ejemplo omite `cuota_reintento_s`. Una propiedad presente con null no establece inequívocamente el comportamiento de una propiedad ausente. El triaje fija 300 segundos por defecto.
- **Impacto:** los ejemplos no discriminan una configuración antigua sin esa propiedad de una configuración con valor explícito.
- **para:** especificador.
- **destino:** resolver.
- **Corrección requerida:** añadir un caso con la propiedad ausente que establezca 300 segundos como intervalo efectivo.

### H3 — 🟡 MEDIA — PERSISTE parcialmente: elegibilidad ambigua tras conservar pares ajenos

- **Resuelto:** la línea 226 exige expresamente que los pares ajenos al selector conserven sus marcas.
- **Persiste:** inmediatamente después se afirma «Y esos perfiles vuelven a ser elegibles» y «estado y agentes dejan de mostrarlos agotados». Tras insertar la frase sobre los pares ajenos, el referente puede ser tanto los seleccionados como los ajenos. Tampoco se explicita que los ajenos con marca confirmada vigente sigan restringidos hasta su recuperación, solicitado en H3.
- **Impacto:** la corrección permite lecturas incompatibles sobre qué perfiles recuperan elegibilidad y dejan de aparecer agotados.
- **para:** especificador.
- **destino:** resolver.
- **Corrección requerida:** nombrar explícitamente los pares seleccionados en las aserciones de elegibilidad y visualización; para los ajenos, establecer marcas confirmadas vigentes y que conserven su restricción hasta la recuperación correspondiente.

## Hallazgos nuevos

Ninguno independiente de H1–H3. La ambigüedad introducida por la corrección del reset se trata dentro de H3.

## Salida para el bucle

**RECHAZADO. para: especificador. destino: resolver.** Completar H1 y las correcciones concretas de H2–H3; reevaluar esos hallazgos y el siguiente delta sin ampliar a código, diseño o pruebas.
