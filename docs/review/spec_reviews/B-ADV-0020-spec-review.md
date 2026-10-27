# Revisión de especificación B-ADV-0020

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Modo: orquestado. Ronda: 4, nuevo intento de desarrollo; ratifica la ronda 3.

## Alcance y método

Revisión de TODO el bloque @B-ADV-0020 de skills/orquestar/features/orquestacion.feature (líneas 202–294) frente al bug docs/plan/bugs/B-ADV-0020-marca-de-agotado-a-ciegas-impide-usar-modelo-con-cuota.md y sus decisiones de contrato. Se aplican Hades y review-spec instalados en C:/Users/Iván Moreno/.adevv/versions/0.6.1, ignorando el modelo del frontmatter.

La lectura comprende los once escenarios/esquemas: relanzamiento de sospechas, recuperación real, intervalo de comprobación, reset selectivo/global, despertar, créditos, origen real, histórico de 1800 segundos, configuración, histórico de 3600 segundos y propiedad ausente. No se reabre ningún otro alcance. No se revisan diseño, implementación ni tests para este veredicto.

El diff del feature contra HEAD/base estable 3f53a3c7ecd707733e58cecf5041bf3d25def4b9 está vacío: la especificación aprobada en ronda 3 no ha cambiado. Frente a f7ac5bd solo se añade el bloque del bug; no se modifican los escenarios anteriores. La revisión completa solicitada ratifica el contrato aprobado, sin exigir cambios nuevos a ese contrato.

## Obligatorias

| Criterio | Resultado | Motivo |
| --- | --- | --- |
| No regresión | ✅ | El bloque aprobado permanece intacto; el diff frente a f7ac5bd solo añade el bloque B-ADV-0020. |
| Coherencia | ✅ | Distingue sospecha y recuperación confirmada; respeta las decisiones de compatibilidad histórica, intervalo y reset, incluido el cambio autorizado del antiguo supuesto de 1800 segundos. |
| Trazabilidad | ✅ | Los once escenarios/esquemas llevan @B-ADV-0020 y corresponden al comportamiento esperado o a las decisiones explícitas del bug. No hay etiquetas @CA-* que exijan criterios adicionales. |
| Delta real | ✅ | Describe recuperación, selección, avisos, configuración y visibilidad nuevos o modificados. Los casos de propiedad ausente y registros históricos son ramas distintas. |

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Claridad | 9/10 | Identifica titular, reserva, marcas reales/supuestas y pares seleccionados/ajenos al reset. |
| Completitud | 9/10 | Cubre los seis puntos del comportamiento esperado y las tres precisiones de la ronda anterior. |
| Testeabilidad | 9/10 | Fija 300/120 segundos, histórico de 1800/3600, 3540 restantes, máximo de 30 segundos y mensajes observables. |
| Estructura | 9/10 | El bloque permanece en el feature de orquestación. |

**Media: 9/10.** Sin hallazgos críticos ni altos.

## Seguimiento de hallazgos anteriores

| Hallazgo | Estado | Evidencia y enrutado |
| --- | --- | --- |
| H1 — ALTA: histórico sin clasificación distinto de 1800 | Resuelto; se mantiene | El caso de 3600 segundos y antigüedad de 60 exige reserva, restricción de 3540 segundos y conservación del histórico. para: especificador; destino: resolver, completado. |
| H2 — MEDIA: propiedad ausente | Resuelto; se mantiene | Escenario propio sin cuota_reintento_s: no reintentar antes de 300 segundos y priorizar titular al alcanzarlos. para: especificador; destino: resolver, completado. |
| H3 — MEDIA: pares ajenos al reset | Resuelto; se mantiene | El esquema exige conservar sus marcas confirmadas, restricciones y visualización, diferenciándolos de los seleccionados. para: especificador; destino: resolver, completado. |

## Evidencia reutilizada

No se ejecutaron pruebas, compilación ni suite completa. El registro de orquestar_evidencias.jsonl acredita compilación verde del test el 2026-10-27T09:51:52, árbol e74e5a0dc07a660506f93e72cf3dde3ba91ff1cf; se acepta la evidencia suministrada sin atribuirle validación semántica de este BDD. El rojo funcional registrado pertenece al desarrollo y no invalida la especificación.

## Salida para el bucle

**APROBADO.** H1–H3 siguen resueltos. Sin hallazgos nuevos ni acciones de especificación pendientes. Este informe actualiza la revisión para el intento actual y no declara corregido el bug.
