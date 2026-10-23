---
id: T-ADV-0012
title: "Conversación libre con continuidad de hilo en el gateway de Telegram"
type: funcional
weight: 100
dificultad: media
version: "v0.3.0"
status: planned
depende_de: []
origen: "Conversación interactiva con el modelo del proyecto desde Telegram"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0012: Conversación libre con continuidad de hilo en el gateway de Telegram

## 🎯 Objetivo de Negocio
Permitir que desde Telegram no solo se puedan lanzar comandos fijos (`/estado`, `/tarea`, `/bug`), sino también mantener una conversación en texto libre con el modelo configurado para el proyecto, conservando el hilo de sesión entre mensajes de cada usuario autorizado y pudiendo reiniciarlo cuando se desee, sin interferir con el árbol de trabajo si el bucle de `/orquestar` está en marcha.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Conversación en texto libre y persistencia de hilo por usuario):** Cuando un usuario autorizado envía un mensaje que no empieza por `/` (o que no corresponde a los comandos fijos), `responder(root, usuario, texto, autorizados)` en `skills/telegram_gateway/gateway.py` invoca al modelo configurado en `orchestration.json` (usando `harness`/`model`/`effort` de `"telegram"` si están definidos, o la configuración de `"atenea"` por defecto), reanudando la sesión previa asociada a ese `(usuario, harness)` (persistida en un fichero local excluido de git en `PROPIOS`, p. ej. `orquestar_telegram.json`) y devolviendo al usuario la respuesta textual del modelo. Si la reanudación de una sesión previa falla, reintenta automáticamente iniciando sesión nueva y actualiza el ID de sesión guardado.
- [ ] **CA-M-2 (Comando `/nuevo` / `/reset` para reiniciar el hilo):** Los comandos `/nuevo` y `/reset` eliminan la sesión guardada del usuario que los envía y responden confirmando que el hilo de conversación se ha reiniciado; `/ayuda` (y `/help`, `/start`) documenta `/nuevo` y que cualquier mensaje sin comando conversa con el asistente del proyecto.
- [ ] **CA-M-3 (Contexto seguro frente al bucle en marcha):** El prompt enviado al modelo indica que responde por Telegram sobre el proyecto en `root` y advierte que no debe modificar ni commitear ficheros rastreados del repositorio mientras exista `orquestar.pid` (bucle en marcha), limitándose a consultar/analizar o usar `apuntar` si el usuario pide registrar tareas/bugs.
- [ ] **CA-M-4 (Pruebas y documentación):** `tests/test_telegram_gateway.py` verifica la conversación en texto libre, la reutilización de sesión entre mensajes del mismo usuario, el reinicio con `/nuevo` y el fallback a sesión nueva si falla el resume; `skills/telegram_gateway/SKILL.md` documenta la conversación libre y `/nuevo`.
