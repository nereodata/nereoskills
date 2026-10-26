---
id: T-ADV-0026
title: "Reservas en la conversación de Telegram cuando el modelo configurado no tiene cuota o no está disponible"
type: funcional
weight: 70
dificultad: media
version: "v1.0.0"
status: completed
depende_de: ["B-ADV-0005"]
origen: "Petición del usuario: el chat de Telegram usa el modelo definido, pero debe conmutar a reserva si no tiene cuota o no está disponible"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0026: Reservas en la conversación de Telegram cuando el modelo configurado no tiene cuota o no está disponible

## 🎯 Objetivo de Negocio
La conversación libre de Telegram (`conversar()`, `skills/telegram_gateway/gateway.py:182`) usa solo el modelo de la clave `telegram` (o el de `atenea`). Si ese modelo está sin cuota o su arnés no está disponible, el mensaje falla. Debe seguir respondiendo con el siguiente arnés o modelo de reserva, igual que hacen los pasos del bucle.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Configuración):** la clave `telegram` de `orchestration.json` admite `reserva` (objeto o lista ordenada) con la misma semántica que en los roles: hereda los campos no redefinidos. Sin `reserva` propia, se usan las de `atenea` cuando `telegram` las hereda.
- [x] **CA-M-2 (Conmutación):** se prueba primero el modelo definido. Se pasa a la siguiente configuración si (a) tiene un agotamiento de cuota vigente registrado (se salta sin lanzarlo, como en T-ADV-0021), (b) su ejecución falla por falta de cuota, o (c) su arnés no se encuentra o no arranca (en coherencia con B-ADV-0005, sin `RuntimeError` que corte la conversación).
- [x] **CA-M-3 (Sesiones):** al cambiar de arnés no se intenta reanudar la sesión de otro arnés; la sesión se guarda por usuario y arnés, como hoy. Al volver a estar disponible el titular, los mensajes siguientes vuelven a él.
- [x] **CA-M-4 (Transparencia):** la firma de la respuesta indica el `harness/model` que respondió; si se usó una reserva, se indica brevemente. Si ninguna configuración está disponible, responde con un mensaje claro (motivo de cada una) en vez de un error genérico.
- [x] **CA-M-5 (Métricas):** los agotamientos detectados en la conversación se registran igual que en el bucle, para que `/agentes` y el bucle los tengan en cuenta.
- [x] **CA-M-6 (Pruebas y documentación):** pruebas con lanzadores simulados (cuota agotada, arnés ausente, todos caídos, vuelta al titular); documentación en `skills/telegram_gateway/SKILL.md`.

## Triaje para la reanudación
- Subfase A: [EXEC] Contratos de cuota, sesiones, diagnóstico y retorno en `skills/telegram_gateway/features/telegram_gateway.feature`.
- Subfase B: [EXEC] Adaptar el borrador de diseño WIP a DEC-ESP-01; reutilizar motor y herencia existentes.
- Subfase C1: [EXEC] Pruebas simuladas del gateway y regresiones de conversación/arnés ausente.
- Subfase C2: [EXEC] Solo `skills/telegram_gateway/gateway.py`; mantener la herencia existente.
- Subfase D: [EXEC] Hades sobre el delta de producción.
- Subfase E: [EXEC] Skill del gateway y changelog.
- Subfase F: [EXEC] Cierre y commit.
- Verificación: `python -m unittest discover -s skills/telegram_gateway -p test_*.py`, `python -m unittest discover -s tests -p test_telegram_gateway.py` y `python -m unittest discover -s skills/orquestar -p test_arnes_ausente.py`, mediante `adevv orquestar --verificar`. Estático: compilación de Python modificados y `git diff --check`. Sin suite completa en este paso.
- B-ADV-0005 ya cubre herencia (incluida reserva objeto/lista) y ejecutable ausente: no se reimplementan ni se vuelven a especificar.

## Resolución del especificador (2026-10-26)
- H-01: sesiones concretas codex-s1 y agy-s1 para 12345; la reserva reanuda agy-s1, conserva agy-s2 y luego reanuda agy-s2, sin reemplazar codex-s1. Al vencer la cuota se reanuda codex-s1. El usuario 67890 no recibe ninguna sesión de 12345.
- H-02: cuota detectada el 2026-10-26 a las 12:00:00 UTC por 1800 segundos; recuperación compartida exacta a las 12:30:00 UTC, reconocida por /agentes y la consulta del bucle, sin atribuir cuota a ausencias.
- H-03: caso separado con único modelo efectivo y sin reservas propias ni heredadas, cuota vigente y cero lanzamientos, con diagnóstico del modelo y recuperación.
- **DEC-ESP-01 (sesiones):** CA-M-3 exige conservar y reanudar la sesión del mismo usuario y arnés también en una reserva. Se descarta forzar siempre una sesión nueva en toda reserva: perdería continuidad aunque exista una sesión propia válida. Nunca se transfiere la sesión del arnés anterior; sin sesión propia se inicia nueva. El contrato aprobado de B-ADV-0005 (`skills/orquestar/features/orquestacion.feature`) prohíbe reutilizar sesiones de otros arneses; se conserva íntegro. La restricción del diseño anterior (`docs/design/B-ADV-0005-design.md`: sesión consultada solo al inicio) y el borrador WIP de T-ADV-0026 (sesión nueva en toda conmutación) deben adaptarse para esta ampliación de CA-M-3. No cambia el contrato de sesiones de pasos ni agentes.
- **DEC-ESP-02 (alcance):** recuperar únicamente la intención BDD del WIP y corregirla en `skills/telegram_gateway/features/telegram_gateway.feature`, sin modificar `tests/features/`, producción ni tests automatizados. Se descarta fusionar `wip/T-ADV-0026` (`f247889`): conserva pruebas y diseño que Artemisa debe adaptar a esta especificación. No se elimina ni altera ningún escenario previo. El rojo WIP es evidencia histórica, no verde del árbol actual.
- **DEC-ESP-03 (disponibilidad):** a diferencia del motor sin reservas, la conversación no lanza siquiera el único modelo con cuota vigente; responde inmediatamente con diagnóstico. Se mantiene el tratamiento de errores ordinarios y su reintento sin sesión, sin conmutar por autenticación u otros fallos ajenos a cuota/arranque.
- No se necesitan recursos externos ni intervención humana. Los criterios permanecen pendientes de implementación; este paso solo resuelve la especificación.
- Hades /review-spec: **APROBADO (9,25/10)**, H-01/H-02/H-03 resueltos y sin hallazgos nuevos. Reporte: `docs/review/spec_reviews/T-ADV-0026-spec-review.md`. Estado planned, sin pendiente_de, para retomar task-dev.

## Ejecución de Artemisa (2026-10-26)
- Subfase A: especificación aprobada reutilizada sin alterar los seis escenarios; no se repite review-spec porque no hay delta respecto al origen aprobado.
- Subfase B: diseño adaptado a DEC-ESP-01 en `docs/design/T-ADV-0026-design.md`; no se fusiona el WIP.
- Subfase C1: siete pruebas simuladas nuevas; rojo de funcionalidad actual en `docs/review/test_reviews/T-ADV-0026-red.txt` (3 fallos, 4 errores). Compilación de pruebas verde mediante --verificar; Hades review-test APROBADO (8,75/10), H-01 medio resuelto verificando modelos m1/m2/m3 y esfuerzo heredado.
- Subfase C2: implementación mínima en gateway, siete pruebas nuevas verdes y 78 pruebas del triaje verdes (45 + 24 + 9); compilación de los dos Python modificados y git diff --check verdes mediante --verificar. Sin suite completa.
- Subfase E: SKILL del gateway y changelog actualizados; validación humana pendiente al cierre de versión, sin detener este paso.
- Subfase D: Hades review-code APROBADO (9,17/10), sin hallazgos; reutiliza evidencia del mismo árbol. Reporte `docs/review/code_reviews/T-ADV-0026-code-review.md`. Sin deuda que registrar.
- Subfase F: cierre orquestado autorizado; se trasladan los HITL a `docs/review/versions/v1.0-revision.md` y se conserva el WIP histórico sin fusionar.
