---
id: T-ADV-0024
title: "Arranque del gateway de Telegram con la sesión de Windows"
type: funcional
weight: 110
dificultad: sencilla
version: "v1.0.0"
status: blocked
depende_de: []
pendiente_de: especificador
origen: "NO-01 de docs/requirements/requirements.md, aplazado a una versión posterior"
created_at: 2026-10-26
updated_at: 2026-10-27
---

# T-ADV-0024: Arranque del gateway de Telegram con la sesión de Windows

## 🎯 Objetivo de Negocio
Que los gateways de Telegram de los proyectos configurados estén siempre escuchando tras iniciar sesión, sin abrir una terminal, para poder consultar el estado, recibir avisos y cerrar versiones (T-ADV-0023) desde el móvil.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Orden):** `adevv telegram --autoarranque on|off|estado` en la raíz de un proyecto registra, quita o muestra el arranque de su gateway con la sesión del usuario. Usa la orden `adevv` (nunca rutas al almacén de versiones), de modo que sobrevive a las actualizaciones.
- [ ] **CA-M-2 (Mecanismo en Windows):** una entrada por proyecto en el arranque de usuario (carpeta Inicio o Programador de tareas, sin privilegios de administrador) que ejecuta `adevv telegram --fondo` en ese proyecto, sin ventana visible.
- [ ] **CA-M-3 (Robustez):** si el proyecto ya no existe o no tiene credenciales, el arranque no falla en bucle: registra el motivo y termina. Activarlo dos veces no duplica la entrada.
- [ ] **CA-M-4 (Otros SO):** en sistemas no Windows, `on` informa de que no está soportado sin cambiar nada.
- [ ] **CA-M-5 (Pruebas y documentación):** pruebas con la carpeta de arranque y el lanzador simulados; documentación en `skills/telegram_gateway/SKILL.md`.
