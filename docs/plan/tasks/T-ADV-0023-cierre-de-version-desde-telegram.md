---
id: T-ADV-0023
title: "Cerrar la versión y relanzar el bucle desde Telegram"
type: funcional
weight: 100
dificultad: media
version: "v1.0.0"
status: blocked
pendiente_de: especificador
depende_de: []
origen: "La única intervención humana por versión obliga a volver a la máquina para lanzar /release y relanzar"
created_at: 2026-10-26
updated_at: 2026-10-27
---

# T-ADV-0023: Cerrar la versión y relanzar el bucle desde Telegram

## 🎯 Objetivo de Negocio
Cuando el bucle para con «Versión vX.Y terminada», el humano revisa y cierra con `/release`. Hoy eso exige estar en la máquina. Esta tarea permite hacer esa única intervención desde Telegram: ver el resumen de la revisión, cerrar la versión y relanzar el bucle con la siguiente.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Aviso de cierre útil):** el aviso de fin de versión por Telegram incluye un resumen de `docs/review/versions/vX.Y-revision.md` (tareas, bloqueos, validaciones funcionales pendientes) y las órdenes disponibles para cerrarla.
- [ ] **CA-M-2 (Orden `/cerrar vX.Y`):** solo para usuarios autorizados y solo si el bucle está parado en la revisión de esa versión (sin bloqueos ni decisiones de producto pendientes). Ejecuta el cierre de versión de `/release` (merge a `main`, etiqueta anotada, push) en modo no interactivo y responde con el resultado. Pide confirmación explícita (p. ej. `/cerrar v1.0 confirmo`) antes de actuar.
- [ ] **CA-M-3 (Relanzar):** tras un cierre correcto, relanza el bucle en segundo plano (como `/lanzar`) para que abra la siguiente versión pendiente; si no hay más, informa de `FIN`.
- [ ] **CA-M-4 (Errores):** cualquier fallo (árbol sucio, conflicto de merge, push rechazado, validación de versión) no deja el repositorio a medias: se informa por Telegram con el motivo y el bucle sigue parado.
- [ ] **CA-M-5 (Pruebas y documentación):** pruebas con repositorio git temporal y remoto `bare` local, sin red; documentación en `skills/telegram_gateway/SKILL.md` y `skills/orquestar/SKILL.md` («Revisión de versión»).
