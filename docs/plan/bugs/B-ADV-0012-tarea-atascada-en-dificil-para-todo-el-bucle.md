---
id: B-ADV-0012
title: "Una tarea que no avanza en dificultad máxima para todo el bucle en vez de bloquearse sola"
type: bug
weight: 20
dificultad: media
version: "v1.0.0"
status: planned
depende_de: []
origen: "Revisión humana de los puntos de parada de orquestar.py (2026-10-27): para sin necesitar al humano"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0012: Una tarea que no avanza en dificultad máxima para todo el bucle en vez de bloquearse sola

## 🎯 Descripción del Fallo

**Causa raíz**: en `bucle()` (`orquestar.py`, hacia la línea 2462), cuando un `task-dev` o `bug-fix` en `dificil` llega a `--reintentos` sin progreso, se llama a `parar(...)` y se detiene todo el bucle.

**Comportamiento observado**: una sola tarea atascada impide avanzar con el resto de tareas independientes de la versión hasta que una persona relanza.

**Comportamiento esperado**:
1. La tarea pasa a `status: blocked` con `pendiente_de: humano` y una sección con el motivo: intentos, dificultad y la cola del último error o rechazo.
2. Se avisa por Telegram, pero el bucle sigue con las demás tareas elegibles. Las que dependen de ella quedan en espera, como ya ocurre con `pendientes_de()`.
3. Al cerrar la versión, `estado()` ya informa de las bloqueadas en `FIN_VERSION[0]` y en `{v}-revision.md`, que es donde decide la persona.
4. El bug de cierre de suite de B-ADV-0006 sigue con su regla propia: a los 3 intentos en `dificil` para e informa. La razón es que ninguna otra tarea puede cerrar la versión mientras la suite siga en rojo.
5. Pruebas: con dos tareas independientes y una que no avanza, la otra se completa y la atascada acaba en `blocked`.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario ha pedido este cambio expresamente: el bucle solo debe pararse cuando haga falta una decisión humana. Si hay que cambiar requisitos o escenarios del bucle (orquestar), forma parte del alcance de este bug. Se puede tocar cualquier ruta necesaria.
