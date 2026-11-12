---
id: T-ADV-0035
title: "Pedir intervención humana solo ante una decisión o recurso pendiente del usuario"
type: funcional
weight: 120
dificultad: dificil
version: "v1.2.0"
status: in_progress
base_calidad: 8efac2293421d1190f2fb57724aa6e932d964427
depende_de: ["T-ADV-0039"]
origen: "Propuestas de optimización de v1.2.0 priorizadas el 2026-11-11 tras revisar Adevv y Afinn"
created_at: 2026-11-11
updated_at: 2026-11-12
---

# T-ADV-0035 · Pedir intervención humana solo ante una decisión o recurso pendiente del usuario

## Objetivo

Aplicar el mismo criterio a preguntas originadas por un agente, un dictamen o el motor de recuperación. Integrar las correcciones de v1.1.2 (B-ADV-0033, B-ADV-0036, B-ADV-0039 y B-ADV-0040) en un comportamiento comprobable desde el paso hasta la cola de preguntas.

## Criterios de aceptación

- [ ] **CA-M-1.** Un hallazgo con responsable de desarrollo o especificación vuelve a ese rol. Un destino ambiguo se aclara dentro del flujo. Un fallo de proveedor usa las reservas autorizadas y, si se agotan temporalmente, deja una espera técnica recuperable.
- [ ] **CA-M-2.** Una pregunta humana explica la decisión o el recurso concreto que únicamente puede aportar el usuario. Ante el mismo impedimento se conserva una sola pregunta y su respuesta incluso después de una reanudación.
- [ ] **CA-M-3.** Repetir la misma indisponibilidad o reescribir su diagnóstico no acredita avance. Al recuperar el recurso se retoma el paso pendiente y las tareas independientes siguen siendo elegibles.
- [ ] **CA-M-4.** Cubrir con proveedores simulados un fallo técnico, un conflicto resoluble por el especificador y una decisión genuinamente humana. Verificar estado, cola y destino a través de los canales existentes.
- [ ] **CA-M-5.** Aplicar en un único punto la decisión técnica del LLM y el resultado de llamada de T-ADV-0039. Confirmar una acción cuando hay agente autorizado, mandato y condición de salida. Si hay duda sobre el destino, solicitar aclaración dentro del flujo. Una pausa justificada conserva el impedimento y la condición verificable para levantarla.
- [ ] **CA-M-6.** Con un ítem en espera o pausado, despachar otro independiente que tenga capacidad disponible. Comprobar por separado falta de cuota del rol, falta de un recurso externo y ausencia acreditada de una vía ejecutable.

## Triaje

- A [EXEC] Escenarios de decisión por ítem, continuidad de preguntas y despacho durante una espera en la feature de orquestación.
- B [EXEC] Aplicación común de la decisión, identidad del impedimento, persistencia y selección del siguiente ítem.
- C1 [EXEC] Recorridos con proveedores simulados desde el motor y las entradas de intervención. Reutilizar las regresiones existentes de llamadas y canales.
- C2 [EXEC] Integrar el resultado de llamada en la transición del ítem y en la selección de trabajo independiente.
- D [EXEC] Hades revisa el delta de producción respecto a la base de calidad.
- E [EXEC] Documentar espera, pausa, pregunta y reanudación en la guía de orquestación.
- F [EXEC] Verificación final, revisión de versión y commit.

Verificación dirigida con `adevv orquestar --verificar "python -m unittest tests.test_decision_item tests.test_llamadas tests.test_control_intervenciones skills.orquestar.test_intervencion_humana skills.orquestar.test_acceso_agente"`. El módulo `tests.test_decision_item` corresponde a C1. Las regresiones existentes de llamadas, recepción por CLI y Telegram, persistencia y acceso se pueden ejecutar ya en A.

## Retoma de desarrollo · C1

Diseño en `docs/design/T-ADV-0035-design.md` y siete recorridos nuevos en `tests/test_decision_item.py`. La verificación del triaje ejecutó 59 pruebas sobre el árbol `351bd4dd12e5d41edcbf1839b35cb41590e61c4b`. Pasaron las 52 regresiones previas. Fallaron los siete casos nuevos de aclaración, decisión humana y despacho durante una espera.

Queda pendiente el dictamen de Hades sobre C1, objetivo `test`, entradas `d1dd9b2883454864834789f465aa4d310bf2327b55cf2965cf5bdfebc5d8e1c3`, invocación `3de02e970fc3416eaa5fcd8cfabc394b`. Claude devolvió acceso por suscripción deshabilitado. La reserva Codex no pudo leer las instrucciones instaladas y terminó sin dictamen. El orquestador conserva la espera de cuota de la reserva agy. Al reanudar, presentar el mismo objetivo y entradas a Hades, con las instrucciones de revisión accesibles para el revisor. La implementación C2 espera el dictamen de C1.

## Decisiones de especificación

- **S1.** Se usan las consultas existentes `--estado` y `/estado` para observar el destino de A y `--preguntas` y `/preguntas` para comprobar la cola antes y después de la decisión. Observar solo el registro interno permitiría que un canal siguiera pidiendo intervención humana por una espera técnica. La recepción y el transporte de la respuesta reutilizan las regresiones de `tests.test_control_intervenciones` y `skills.orquestar.test_intervencion_humana`.
- **S2.** Se simula la denegación de suscripción de Claude en el principal y su única reserva autorizada. Este caso acredita que A sigue esperando revisión mientras el motor despacha B. Los escenarios de B-ADV-0040 fijan por separado el perfil estricto, la reserva que sí puede revisar y el fallo genérico de autenticación o red que devuelve el error sin conmutar.

## Hallazgo de Hades enrutado
- Destino: `especificador`
- Decisión: ejecutar especificar
- Evidencia: Hades /review-spec RECHAZADO. S1 alta (CA-M-4): comprobar por CLI y Telegram el estado, la cola y el destino en los tres recorridos (conflicto de especificación, espera técnica y decisión humana); observar la pregunta concreta antes de responder y su respuesta tras reiniciar. S2 media, resolver: precisar el acceso por suscripción deshabilitada y las reservas autorizadas, conservando el contrato de autenticación/red. Ejecutar especificar sobre la subfase A. Triaje, escenarios y dictamen íntegro en wip/T-ADV-0035, commit 6923ca6, docs/review/spec_reviews/T-ADV-0035-spec-review.md. Las 27 regresiones previas de control de intervenciones y acceso pasaron con --verificar.
