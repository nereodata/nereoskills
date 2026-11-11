# Revisión de especificación — B-ADV-0034

- **Fecha:** 2026-11-11
- **Modalidad:** orquestada; revisión aislada única del alcance completo de definición, antes de escenarios.
- **Fuentes:** ficha completa y restricción de plataforma adjuntas.
- **Límite:** sin auditoría de implementación, corrección de requisitos ni ejecución de suite.
- **Limitación operativa:** no se ha podido acceder al disco ni leer las instrucciones instaladas de Hades y `/review-spec`. Este informe no acredita conformidad con su plantilla o rúbrica.

## Veredicto

**NO APROBADO — requiere resolución del especificador.**

No existe en la definición suministrada un valor por defecto seguro y justificable que permita continuar desarrollo cumpliendo **todos** los criterios y la restricción de arquitectura.

Implementar únicamente la CLI resolvería el desbloqueo fuera de Telegram y seguiría la alternativa propuesta, pero incumpliría CA-2, la participación del endpoint exigida por CA-4 y su verificación en CA-7.

Implementar un servidor HTTP local autenticado atendería una interpretación de CA-2, pero contravendría la restricción de plataforma que descarta servidores propios. Restringirlo a una interfaz local no elimina esa incompatibilidad.

Elegir un socket o pipe tampoco constituye una resolución autorizada: CA-2 no fija ese transporte y la alternativa presenta ese endpoint como una ampliación posterior condicionada. Además, debe aclararse si un servicio de escucha local queda permitido por la restricción arquitectónica. La ausencia de HTTP no demuestra por sí misma compatibilidad con una arquitectura sin servidores propios.

Corresponde al **especificador** decidir y reconciliar el alcance obligatorio. No procede trasladar esta decisión al desarrollador ni solicitar intervención humana por un recurso externo: no se necesita ninguno.

## Comprobaciones obligatorias

Estas comprobaciones corresponden al alcance solicitado; no se presentan como reproducción de la skill inaccesible.

| Comprobación | Resultado | Fundamento |
|---|---|---|
| Coherencia entre criterios y alternativa | **NO CUMPLE** | CA-2 exige publicar un endpoint; la alternativa permite omitirlo. |
| Compatibilidad con la restricción arquitectónica | **NO DEMOSTRADA** | Se descartan servidores propios y no se define una excepción ni un mecanismo compatible para el endpoint. |
| Existencia de un valor por defecto que cumpla todos los criterios | **NO CUMPLE** | CLI sola incumple criterios; HTTP introduce el conflicto arquitectónico; socket/pipe requiere una decisión pendiente. |
| Alcance suficientemente decidido para elaborar escenarios aprobables | **NO CUMPLE** | No está determinado si el endpoint pertenece a esta entrega ni qué contrato deberá verificarse. |
| Conservación de garantías funcionales | **DEFINIDAS A NIVEL DE CRITERIO** | CA-4 a CA-6 recogen dominio común, persistencia, idempotencia, estados observables y compatibilidad. No se valida aquí su implementación. |
| Necesidad de recurso externo inaccesible | **NO APLICA** | La decisión pendiente es de especificación. |
| Aprobación previa de escenarios | **NO EMITIDA** | Esta revisión precede a su elaboración. |

## Hallazgos

### H-01 — ALTA — Alcance obligatorio contradictorio y compatibilidad arquitectónica sin resolver

**para: especificador**

**Evidencia**

- CA-2 exige un endpoint local autenticado y un contrato versionado.
- CA-3 exige disponibilidad del desbloqueo en instalaciones sin servidor HTTP ni Telegram.
- CA-4 incluye endpoint, CLI y Telegram como adaptadores de una misma operación.
- CA-7 exige pruebas del endpoint y la CLI.
- La alternativa considera suficiente la CLI y permite posponer el endpoint si no existe un consumidor que lo justifique.
- La restricción de plataforma adjunta descarta servidores propios.
- El triaje declara que no existe una decisión sobre transporte, autenticación o consumidor.

**Problema**

La definición admite dos alcances incompatibles: endpoint obligatorio en esta entrega y CLI suficiente con endpoint aplazable. La obligación de admitir instalaciones sin HTTP no determina si el endpoint debe existir mediante otro transporte, ser opcional o quedar fuera de esta entrega.

La restricción arquitectónica impide asumir un servidor HTTP como solución por defecto. Tampoco autoriza automáticamente un servicio mediante socket o pipe.

**Impacto**

Desarrollo tendría que elegir qué obligación incumplir o introducir una decisión arquitectónica no acordada. Los escenarios podrían consolidar una interpretación arbitraria y aparentar una aprobación inexistente.

**Resolución obligatoria**

El especificador debe dejar una única definición coherente que determine:

1. Si el endpoint es obligatorio para esta entrega o queda aplazado.
2. Si es obligatorio, qué significa “endpoint” y cómo resulta compatible con la prohibición de servidores propios.
3. Qué modalidad de CLI debe funcionar en instalaciones sin HTTP y cómo se relaciona con ese endpoint.
4. Qué alcance de contrato versionado, autenticación y verificación resulta exigible según la decisión.

Debe reconciliar los criterios afectados y la alternativa. Este informe no elige la solución ni modifica los requisitos.

**Condición de cierre**

La definición revisada permite derivar escenarios sin excepciones implícitas, sin contradecir la arquitectura y sin delegar la decisión de alcance al desarrollador.

## Puntuaciones

Escala orientativa propia de **0 a 5**: 0 significa ausente o incompatible; 5, suficientemente definido para esta fase. No sustituye la rúbrica de la skill inaccesible.

| Dimensión | Puntuación | Justificación |
|---|---:|---|
| Claridad del problema y resultado funcional | 5/5 | El bloqueo fuera de Telegram y el resultado esperado están claramente descritos. |
| Coherencia interna | 1/5 | Conviven endpoint obligatorio y endpoint aplazable. |
| Compatibilidad arquitectónica | 1/5 | Falta una interpretación acordada compatible con la restricción adjunta. |
| Verificabilidad de la definición | 3/5 | Se enumeran garantías y casos relevantes, pero el control que debe probarse sigue indeterminado. |
| Preparación para continuar a escenarios y desarrollo | 1/5 | La decisión pendiente altera alcance, contrato y pruebas. |

**La puntuación no compensa el incumplimiento obligatorio de coherencia.**

## Disposición

- **Obligatorias:** resolver H-01 mediante el especificador antes de continuar con escenarios aprobables, diseño o implementación del control.
- **Para desarrollador:** ningún hallazgo ALTA/CRÍTICO asignado; no debe resolver esta contradicción mediante una elección implícita.
- **Para humano:** ninguno.
- **Pruebas ejecutadas:** ninguna; revisión exclusivamente documental.
- **Auditoría de implementación:** no realizada.
- **Cambios de requisitos o producción:** ninguno.
- **Aprobación:** no concedida.
