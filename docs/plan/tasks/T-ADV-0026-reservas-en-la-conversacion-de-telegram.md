---
id: T-ADV-0026
title: "Reservas en la conversación de Telegram cuando el modelo configurado no tiene cuota o no está disponible"
type: funcional
weight: 70
dificultad: media
version: "v1.0.0"
status: blocked
pendiente_de: especificador
depende_de: ["B-ADV-0005"]
origen: "Petición del usuario: el chat de Telegram usa el modelo definido, pero debe conmutar a reserva si no tiene cuota o no está disponible"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0026: Reservas en la conversación de Telegram cuando el modelo configurado no tiene cuota o no está disponible

## 🎯 Objetivo de Negocio
La conversación libre de Telegram (`conversar()`, `skills/telegram_gateway/gateway.py:182`) usa solo el modelo de la clave `telegram` (o el de `atenea`). Si ese modelo está sin cuota o su arnés no está disponible, el mensaje falla. Debe seguir respondiendo con el siguiente arnés o modelo de reserva, igual que hacen los pasos del bucle.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Configuración):** la clave `telegram` de `orchestration.json` admite `reserva` (objeto o lista ordenada) con la misma semántica que en los roles: hereda los campos no redefinidos. Sin `reserva` propia, se usan las de `atenea` cuando `telegram` las hereda.
- [ ] **CA-M-2 (Conmutación):** se prueba primero el modelo definido. Se pasa a la siguiente configuración si (a) tiene un agotamiento de cuota vigente registrado (se salta sin lanzarlo, como en T-ADV-0021), (b) su ejecución falla por falta de cuota, o (c) su arnés no se encuentra o no arranca (en coherencia con B-ADV-0005, sin `RuntimeError` que corte la conversación).
- [ ] **CA-M-3 (Sesiones):** al cambiar de arnés no se intenta reanudar la sesión de otro arnés; la sesión se guarda por usuario y arnés, como hoy. Al volver a estar disponible el titular, los mensajes siguientes vuelven a él.
- [ ] **CA-M-4 (Transparencia):** la firma de la respuesta indica el `harness/model` que respondió; si se usó una reserva, se indica brevemente. Si ninguna configuración está disponible, responde con un mensaje claro (motivo de cada una) en vez de un error genérico.
- [ ] **CA-M-5 (Métricas):** los agotamientos detectados en la conversación se registran igual que en el bucle, para que `/agentes` y el bucle los tengan en cuenta.
- [ ] **CA-M-6 (Pruebas y documentación):** pruebas con lanzadores simulados (cuota agotada, arnés ausente, todos caídos, vuelta al titular); documentación en `skills/telegram_gateway/SKILL.md`.

## Bloqueo de especificacion
Hades /review-spec RECHAZADO: H-01 (alta), H-02 y H-03 (medias), todos para especificador. Ver docs/review/spec_reviews/T-ADV-0026-spec-review.md y docs/review/versions/v1.0-revision.md. Avance conservado en wip/T-ADV-0026, commit f247889. Sin cambios de produccion en release ni tareas dependientes alteradas.
