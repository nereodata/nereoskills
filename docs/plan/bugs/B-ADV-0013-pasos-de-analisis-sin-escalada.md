---
id: B-ADV-0013
title: "Los pasos de análisis paran tras 2 intentos sin escalar de modelo ni probar reservas"
type: bug
weight: 25
dificultad: media
version: "v1.0.0"
status: blocked
pendiente_de: especificador
depende_de: []
origen: "Revisión humana de los puntos de parada de orquestar.py (2026-10-27): para sin necesitar al humano"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0013: Los pasos de análisis paran tras 2 intentos sin escalar de modelo ni probar reservas

## 🎯 Descripción del Fallo

**Causa raíz**: la promoción de dificultad cuando no hay progreso (`promover_dificultad()`, `comprobar_promocion()`) solo se aplica a `task-dev` y `bug-fix`. `especificar`, `revisar-tarea`, `revisar-version`, `calcular-dependencias`, `work-plan`, `revisar-deuda` y `aplicar-producto` paran con «"<paso>" no avanza tras 2 intentos».

**Comportamiento observado**: en v1.0, «"especificar" no avanza tras 2 intentos» (B-ADV-0007) detuvo el bucle sin probar un modelo más fuerte.

**Comportamiento esperado**:
1. Antes de parar, un paso de análisis sin progreso se repite con el perfil escalado del rol (`escalada()` / el siguiente nivel configurado) y después con las reservas.
2. Si sigue sin avanzar y el paso afecta a una tarea concreta (`especificar`, `revisar-tarea`), esa tarea se bloquea con `pendiente_de: humano` y el bucle continúa, como en B-ADV-0012. Si el paso es de toda la versión o de todo el producto, entonces para.
3. El aviso dice qué perfiles se probaron.
4. Pruebas con un paso de análisis simulado que solo avanza con el perfil escalado.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario ha pedido este cambio expresamente: el bucle solo debe pararse cuando haga falta una decisión humana. Si hay que cambiar requisitos o escenarios del bucle (orquestar), forma parte del alcance de este bug. Se puede tocar cualquier ruta necesaria.

## Bloqueo de especificaci?n (2026-10-27)
Hades /review-spec RECHAZADO (7,5/10), con H-01/H-02 altos y H-03 medio asignados al especificador. Resolver la secuencia observable de perfiles, ?xito con reserva, aislamiento por paso/argumento, reinicio por progreso y conservaci?n en recarga; parametrizar pasos locales, tarea independiente y l?mite de intentos.

Intento conservado en `wip/B-ADV-0013` (6b43e5c). Informe: `docs/review/spec_reviews/B-ADV-0013-spec-review.md`. Detalle de enrutado en `docs/review/versions/v1.0-revision.md`. Sin cambios de producci?n en release.
