---
id: T-ADV-0039
title: "Retomar cada llamada al LLM según su propio resultado y su cuota"
type: funcional
weight: 110
dificultad: dificil
version: "v1.2.0"
status: planned
depende_de: ["B-ADV-0048"]
created_at: 2026-11-12
updated_at: 2026-11-12
---

# T-ADV-0039 · Retomar cada llamada al LLM según su propio resultado y su cuota

## Objetivo

Aplicar un solo contrato de ejecución al paso principal, a una llamada interna y al diagnóstico de suite. El llamador recibe el resultado directamente. Las métricas registran lo ocurrido y permiten consultar el histórico. B-ADV-0048 aporta el primer recorrido de integración que debe conservarse al extraer esta responsabilidad de `bucle()` y `agente()`.

## Criterios de aceptación

- [ ] **CA-M-1.** En cada entrada, identificar trabajo, invocación, llamada padre cuando proceda, rol y perfil efectivo. Una reserva con entrega válida termina la llamada aunque el principal siga sin cuota. Un rechazo formal válido termina la revisión y devuelve el trabajo al responsable de decidir.
- [ ] **CA-M-2.** Con todos los perfiles autorizados sin cuota, registrar qué llamada espera y hasta cuándo se conoce su recuperación. Al exceder la espera del proceso se guarda la acción pendiente. Tras relanzar, reanudarla respetando perfiles estrictos, reservas y trabajo acreditado.
- [ ] **CA-M-3.** Distinguir entrega válida, entrega ambigua o contradictoria, fallo de ejecución y cuota. Si procede aclaración, conservar la entrega y aplicar a la aclaración sus propios perfiles y cuota. Una incidencia de recepción identifica la revisión afectada.
- [ ] **CA-M-4.** Ejecutar la misma matriz con proveedores simulados por las tres entradas. Comprobar el resultado del llamador, los eventos de consumo y la recuperación tras interrupción, incluidas métricas históricas con información parcial. La decisión de espera o reserva debe tener una sola implementación.
