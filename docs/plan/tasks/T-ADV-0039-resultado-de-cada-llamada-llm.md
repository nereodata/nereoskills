---
id: T-ADV-0039
title: "Retomar cada llamada al LLM según su propio resultado y su cuota"
type: funcional
weight: 110
dificultad: dificil
version: "v1.2.0"
status: completed
depende_de: ["B-ADV-0048"]
created_at: 2026-11-12
updated_at: 2026-11-12
---

# T-ADV-0039 · Retomar cada llamada al LLM según su propio resultado y su cuota

## Objetivo

Aplicar un solo contrato de ejecución al paso principal, a una llamada interna y al diagnóstico de suite. El llamador recibe el resultado directamente. Las métricas registran lo ocurrido y permiten consultar el histórico. B-ADV-0048 aporta el primer recorrido de integración que debe conservarse al extraer esta responsabilidad de `bucle()` y `agente()`.

## Criterios de aceptación

- [x] **CA-M-1.** En cada entrada, identificar trabajo, invocación, llamada padre cuando proceda, rol y perfil efectivo. Una reserva con entrega válida termina la llamada aunque el principal siga sin cuota. Un rechazo formal válido termina la revisión y devuelve el trabajo al responsable de decidir.
- [x] **CA-M-2.** Con todos los perfiles autorizados sin cuota, registrar qué llamada espera y hasta cuándo se conoce su recuperación. Al exceder la espera del proceso se guarda la acción pendiente. Tras relanzar, reanudarla respetando perfiles estrictos, reservas y trabajo acreditado.
- [x] **CA-M-3.** Distinguir entrega válida, entrega ambigua o contradictoria, fallo de ejecución y cuota. Si procede aclaración, conservar la entrega y aplicar a la aclaración sus propios perfiles y cuota. Una incidencia de recepción identifica la revisión afectada.
- [x] **CA-M-4.** Ejecutar la misma matriz con proveedores simulados por las tres entradas. Comprobar el resultado del llamador, los eventos de consumo y la recuperación tras interrupción, incluidas métricas históricas con información parcial. La decisión de espera o reserva debe tener una sola implementación.

## Triaje · 12 de noviembre

Base de calidad (`base_calidad`) = `09b10c001aca10bc5426b986d087030680691a05`. A [EXEC] estados de llamada y correlación de revisión, con el episodio T-AFN-0147 de Afinn. B [EXEC] identidad lógica, recepción y política de recuperación común. C1 [EXEC] regresiones de las tres entradas y aislamiento entre revisiones. C2 [EXEC] contrato de llamada y adaptación del motor. D [EXEC] Hades sobre el delta. E [EXEC] guía de roles y changelog. F [EXEC] verificación dirigida y commit. La verificación comprende los tests de llamadas, progreso, cuota, reservas, perfiles y diagnóstico/cierre afectados.

El caso de aceptación exige conservar la espera de la revisión de especificación de las 18:00 hasta su ratificación de las 18:01, y permitir que el rechazo de código de las 18:38 vuelva a Artemisa. Una revisión de pruebas válida no cancela una especificación aún pendiente. La evidencia insuficiente del historial se comunica como desconocida.

## Evidencia de ejecución

La regresión de T-AFN-0147 utiliza proveedores simulados y un repositorio Git temporal. Antes de la implementación, el bucle ejecutaba una sola vez Artemisa y paraba por la cuota antigua. Con el contrato de llamadas, recibe la ratificación de especificación, registra el rechazo de código, enruta el hallazgo por la entrada existente y vuelve a ejecutar Artemisa con el encargo y la tarea en `planned`. La cuota de Gemini sigue excluyendo ese perfil para próximas llamadas.

La matriz de 12 pruebas verifica roles, diagnóstico, paso principal y CLI en otro proceso. Comprueba agotamiento y retoma, identidad, perfil estricto, fuentes contradictorias con aclaración, conservación de costes, métricas incompletas, compatibilidad de canal con llamadas antiguas y precedencia concurrente. Las revisiones independientes de especificación, pruebas y código están aprobadas. Formato y lint se declaran omitidos por ausencia de herramientas configuradas; sintaxis Python y diff comprobados.

Verificación final registrada mediante `--verificar`: 220 pruebas dirigidas, todas correctas, en 345,208 s. El conjunto cubre progreso, cuotas, reservas, perfiles, acceso, recuperación de suite, revisiones de cierre, B-ADV-0048 y las 12 pruebas de T-ADV-0039.
