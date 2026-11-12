---
id: B-ADV-0048
title: "Continuar la intervención de cierre tras un rechazo válido de Hades en reserva"
type: bug
weight: 0
dificultad: media
version: "v1.1.4"
status: in_progress
depende_de: []
origen: "Afinn, release/v0.7, B-AFN-0185, solicitud 0c9187dc, commit fdf53457"
created_at: 2026-11-12
updated_at: 2026-11-12
---

# B-ADV-0048 · Continuar la intervención de cierre tras un rechazo válido de Hades en reserva

## Reproducción en 1.1.3

1. Usar una solicitud de cierre con tres recaídas contabilizadas, estrategia aplicada y un único bug abierto. La intervención prevista consiste en identificar la operación pendiente del arnés E2E. El candidato focal queda en 70/71.
2. Con Gemini Argon sin cuota, Hades en Codex sale con código 0. Su respuesta final propia empieza por `**Veredicto formal: RECHAZADO. Media: 7,75/10.**`. El informe rechaza C1, asigna RT-CIERRE-01 a Artemisa y describe la intervención sin pedir un recurso externo.
3. La misma invocación queda primero sin veredicto reconocido y después con la cuota de Gemini. Artemisa enruta el hallazgo, aplica la conclusión técnica y confirma `blocked / intervencion_tecnica`. El proceso para por cuota. Al relanzar, el selector devuelve diagnóstico terminal.

Evidencia en el repositorio consumidor Afinn, commit `fdf53457`. Véanse `docs/review/evidence/B-AFN-0185/cleanup-test-review.json`, la ficha y el JSON hermano en `docs/plan/bugs`. En las métricas locales, contrastar las dos filas de las 07:16 con la del paso de las 07:21 del 12 de noviembre. Las pruebas de Adevv usarán datos sintéticos equivalentes y proveedores simulados.

## Orden de implementación y aceptación

- [ ] **1. Recibir el rechazo.** Reconocer la declaración anterior en la respuesta final por la vía existente. Registrar un rechazo para esa invocación. La marca del principal sigue disponible para seleccionar perfil en futuras llamadas. Una cita, un ejemplo o una entrega sin dictamen siguen sin acreditar una revisión.
- [ ] **2. Entregar la intervención.** Si persiste el fallo y Hades ha asignado una investigación concreta y distinta al rol autorizado de desarrollo, usar el enrutado existente a Artemisa. El siguiente `bug-fix` recibe la intervención, su condición de salida y la misma solicitud. La suite continúa roja y C1 rechazado. Un nombre libre de mantenedor, por sí solo, no acredita asignación. Una intervención realmente externa conserva su destino y motivo.
- [ ] **3. Retomar desde disco.** Con una ficha ya bloqueada como la de Afinn, recuperar una sola vez la intervención inequívocamente pendiente del hallazgo vigente. Preservar WIP, historial, contador y rechazo. Un segundo arranque o la devolución del mismo resultado sin evidencia nueva no vuelve a emitir el encargo ni reinicia la estrategia agotada. Si la evidencia histórica es insuficiente, el estado explica qué asignación falta.
- [ ] **4. Comprobar el recorrido completo.** Desde el bucle normal, la reserva devuelve el rechazo y el siguiente paso entrega la intervención a Artemisa. En el caso vecino todos los perfiles autorizados de Artemisa carecen de cuota. La espera, el aviso y la retoma corresponden a esa llamada y conservan el encargo. Ninguno de los dos recorridos abre una pregunta humana ni permite cerrar el bug en rojo.

El parche reutiliza el lector formal, el enrutado de hallazgos, el selector de bugs y la gestión de reservas de `bug-fix`. El contrato general para otros roles, la reorganización del bucle y la traza común se planifican en 1.2.

## Triaje

Base de calidad (`base_calidad`) = `04d602db81ade77b5e91c2f6436ada86f1a364ab`. A [EXEC] entrega y cuota en uso_sin_rutas. B [EXEC] identidad de la intervención y reanudación. C1 [EXEC] regresión por el bucle con proveedores simulados. C2 [EXEC] recepción formal, asignación y cuota real del paso. D [EXEC] revisión independiente. E [EXEC] guía del operador y changelog. F [EXEC] verificación y commit. Ejecutar las regresiones de orquestación, cuota y revisiones afectadas y repetir el recorrido con los artefactos reales de Afinn en un repositorio temporal.
