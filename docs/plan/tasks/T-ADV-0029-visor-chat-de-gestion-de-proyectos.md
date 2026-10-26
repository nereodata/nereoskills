---
id: T-ADV-0029
title: "Visor gráfico: chat para gestionar los proyectos sin pasar por los arneses"
type: funcional
weight: 120
dificultad: dificil
version: "v1.1.0"
status: planned
depende_de: ["T-ADV-0027", "T-ADV-0026"]
origen: "Petición del usuario: chat en el visor desde el que gestionar los proyectos sin hablar desde Claude, Codex o Gemini (v1.1)"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0029: Visor gráfico: chat para gestionar los proyectos sin pasar por los arneses

## 🎯 Objetivo de Negocio
Gestionar los proyectos desde el visor con un chat propio, sin abrir la interfaz de Claude Code, Codex o Antigravity: preguntar cómo va algo, registrar tareas o bugs, lanzar o parar bucles y cerrar versiones, con el mismo modelo y reservas que la conversación de Telegram.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Un solo motor de conversación):** el chat del visor y el de Telegram comparten la misma lógica de conversación (selección de modelo con reservas de T-ADV-0026, sesiones por usuario y arnés, construcción del prompt con el contexto del proyecto). Se extrae de `gateway.py` a un módulo común sin cambiar el comportamiento de Telegram.
- [ ] **CA-M-2 (Contexto de proyecto):** el chat trabaja sobre el proyecto seleccionado en el visor (o uno general para preguntas entre proyectos), con una sesión por proyecto que se conserva entre aperturas del visor.
- [ ] **CA-M-3 (Órdenes):** admite las mismas órdenes que Telegram (`/estado`, `/tarea`, `/bug`, `/lanzar`, `/parar`, `/metricas`, `/agentes` y `/cerrar` de T-ADV-0023, con su confirmación), además de texto libre. Las acciones con efectos piden confirmación en la propia interfaz.
- [ ] **CA-M-4 (Experiencia):** historial visible, indicador de «pensando», firma `harness/model` en cada respuesta (indicando si respondió una reserva) y errores claros si ningún modelo está disponible.
- [ ] **CA-M-5 (Seguridad):** el servidor del visor solo escucha en `127.0.0.1` y exige un token local generado al arrancar (incluido en la URL que abre `adevv visor`), para que otra página del navegador no pueda lanzar órdenes.
- [ ] **CA-M-6 (Pruebas y documentación):** pruebas del motor común (regresión de Telegram incluida) y de la API del chat con lanzadores simulados; documentación en la del visor y en `skills/telegram_gateway/SKILL.md`.
