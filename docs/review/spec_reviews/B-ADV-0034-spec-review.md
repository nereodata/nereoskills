# Revisión de especificación — B-ADV-0034

- **Fecha:** 2026-11-11.
- **Modalidad:** reevaluación aislada de H-01, limitada a definición, previa a escenarios.
- **Fuentes:** agente Hades, skill `/review-spec`, informe anterior, ficha revisada del bug y restricción de plataforma suministrados como adjuntos.
- **Limitación:** sin acceso al disco; no se ha contrastado el árbol ni obtenido un diff independiente.
- **Alcance:** coherencia de los CA revisados y cierre de las cuatro preguntas de H-01.
- **Exclusiones:** aprobación de BDD, diseño, implementación y ejecución de pruebas.

## Veredicto

**APROBADO — exclusivamente la resolución de H-01 en la definición.**

**H-01: resuelto.** Los criterios revisados y DEC-ESP-0034-01 establecen un único alcance obligatorio: consulta y respuesta mediante CLI local, con dominio compartido con Telegram y sin endpoint ni servicio de escucha.

La definición permite continuar a escenarios sin delegar al desarrollador la elección del alcance, transporte o autorización. Esta aprobación no acredita escenarios, diseño, código ni cumplimiento funcional.

## Antecedente histórico

La revisión anterior, de 2026-11-11, emitió **NO APROBADO** y registró:

**H-01 — 🟠 ALTA — Alcance obligatorio contradictorio y compatibilidad arquitectónica sin resolver.**
**para: especificador**

La definición anterior exigía un endpoint autenticado y versionado en CA-2, incluía ese endpoint en CA-4 y CA-7 y, simultáneamente, permitía aplazarlo mediante la alternativa de CLI suficiente. La restricción de plataforma descartaba servidores propios. El informe exigió decidir y reconciliar alcance, significado del endpoint, modalidad CLI y contrato/autenticación/verificación.

Ese rechazo se conserva como antecedente de la definición anterior. Su escala orientativa de 0 a 5 y su declaración de instrucciones inaccesibles pertenecen a aquella revisión; no constituyen la rúbrica de esta reevaluación.

## Reevaluación de H-01

| Pregunta pendiente | Resolución documental | Resultado |
|---|---|---|
| 1. ¿Es obligatorio el endpoint o queda aplazado? | CA-2 y DEC-ESP-0034-01 lo excluyen expresamente de esta entrega. No es opcional ni condición de cierre. Una ampliación futura requeriría una decisión separada. | **Cerrada** |
| 2. Si es obligatorio, ¿qué significa y cómo respeta la arquitectura? | La condición deja de aplicar: no se entrega endpoint. CA-2 excluye HTTP, socket, pipe y proceso de escucha; la decisión no introduce excepciones a la prohibición de servidores propios. | **Cerrada por exclusión expresa** |
| 3. ¿Qué CLI funciona sin HTTP y cómo se relaciona con el endpoint? | CA-3 conserva `adevv orquestar --preguntas` y añade `adevv orquestar --responder <Q-ID> "<respuesta>"`. Funciona localmente sin HTTP ni Telegram; no depende de un endpoint. | **Cerrada** |
| 4. ¿Qué contrato, autenticación y verificación se exigen? | El contrato es la sintaxis de CA-3 y los resultados observables de CA-5. La autoridad local procede de permisos del sistema operativo; Telegram conserva su autorización independiente. CA-7 delimita la verificación posterior. No se exige contrato de red versionado ni token de API. | **Cerrada** |

### Coherencia del delta

- **CA-1 a CA-3:** la consulta existente y la nueva respuesta CLI satisfacen el acceso independiente de Telegram. “Punto de control propio” no obliga a interpretar una interfaz de red: la decisión lo concreta como CLI.
- **CA-4:** los dos adaptadores exigidos son CLI y Telegram. Compartir operación de dominio resulta compatible con mantener identidades y autorizaciones distintas.
- **CA-5:** recepción durable, incorporación y reanudación efectiva se distinguen expresamente. Incorporar una respuesta no promete arrancar si persisten preguntas, dependencias o parada manual.
- **CA-6:** se conserva el compromiso de compatibilidad de Telegram.
- **CA-7:** la verificación corresponde al alcance CLI y al dominio compartido; ya no exige un endpoint excluido. Los escenarios y pruebas quedan explícitamente para la siguiente subfase.
- **Decisión y alternativa:** DEC-ESP-0034-01 elimina la alternativa contradictoria como opción de esta entrega. El texto del triaje que describe el conflicto anterior queda contextualizado como antecedente y señala su resolución.

## Comprobaciones obligatorias

| Obligatoria | Resultado | Fundamento |
|---|---|---|
| No regresión | ✅ En el alcance documental recibido | La ficha declara que no existen escenarios aprobados de este bug que retirar o modificar; conserva consulta existente y compatibilidad Telegram. No se certifica el árbol inaccesible. |
| Coherencia | ✅ | CA-2/CA-3/CA-4/CA-7 y la decisión convergen en CLI local sin servidor, compatible con la restricción adjunta. |
| Trazabilidad | No aplica todavía a etiquetas BDD | Los CA-1 a CA-7 están identificados en la ficha; no se han recibido escenarios ni etiquetas `@CA-*` para aprobar. |
| Delta real | ✅ | Se identifica como novedad el acceso de respuesta CLI. La consulta y persistencia existentes se conservan; no se presentan como funcionalidad nueva. |

## Puntuaciones

Rúbrica de 1 a 10 aplicada a la definición recibida, sin atribuir puntuación a BDD inexistente.

| Dimensión | Puntuación | Justificación |
|---|---:|---|
| Claridad | 9/10 | Alcance, exclusiones, sintaxis y autoridad local explícitos. |
| Completitud | 9/10 | Las cuatro decisiones pendientes están cerradas y reconciliadas con los CA afectados. |
| Testeabilidad | 9/10 | Se identifican entradas, rechazos, estados observables y casos de verificación suficientes para elaborar escenarios. |
| Estructura del `.feature` | No evaluable | Los escenarios aún no se han elaborado. |

**Media de dimensiones aplicables: 9/10.** No hay hallazgos críticos ni altos abiertos dentro del alcance revisado.

## Hallazgos

### Anteriores

**H-01 — 🟠 ALTA — resuelto.**
**para: especificador**

CA-2 y DEC-ESP-0034-01 fijan el alcance CLI y excluyen el endpoint. CA-3, CA-4 y CA-7 quedan alineados; contrato y autorización están definidos sin excepciones arquitectónicas implícitas.

### Nuevos

Ninguno en el delta de definición revisado.

## Disposición

- **Para especificador:** H-01 cerrado; puede continuar la elaboración de escenarios.
- **Para desarrollador:** ningún hallazgo asignado en esta reevaluación.
- **Para humano:** ninguno; no falta un recurso externo.
- **BDD:** sin aprobación emitida; deberá revisarse cuando exista.
- **Diseño e implementación:** no auditados.
- **Pruebas ejecutadas:** ninguna.
- **Estado del bug:** esta revisión no acredita su resolución funcional ni autoriza marcarlo como completado.
