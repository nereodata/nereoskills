---
id: T-ADV-0030
title: "El token de Telegram del entorno sirve de respaldo solo para avisos, sin arrancar gateway"
type: funcional
weight: 80
dificultad: sencilla
version: "v1.0.0"
status: blocked
pendiente_de: especificador
depende_de: ["B-ADV-0007"]
origen: "Petición del usuario: poner el token del bot de Adevv en las variables de sistema para que los proyectos que olviden su .env le avisen allí"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0030: El token de Telegram del entorno sirve de respaldo solo para avisos, sin arrancar gateway

## 🎯 Objetivo de Negocio
El usuario quiere definir el token del bot de Adevv (y sus usuarios) en las variables de sistema como respaldo: un proyecto que olvide su `.env` debe seguir avisando, a ese bot. Hoy `credenciales()` (`skills/orquestar/orquestar.py:1482`) toma el `.env` del proyecto y, si falta, el entorno, y trata igual ambos orígenes: con el token de respaldo, cada proyecto sin `.env` arrancaría además su gateway (`iniciar_gateway()`, `:1935`) escuchando el bot de Adevv. Telegram solo admite un lector por bot, así que chocaría (409) con el gateway real de Adevv y uno de los dos dejaría de escuchar.

Los avisos ya llevan el nombre del proyecto delante (`avisar()`, `:1531`), así que en el bot compartido se distingue el origen.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Origen de las credenciales):** `credenciales()` informa de si el token viene del `.env` del proyecto o del entorno de ejecución, sin cambiar la precedencia actual (`.env` primero).
- [ ] **CA-M-2 (Avisos con el respaldo):** con credenciales del entorno, `avisar()` sigue enviando los avisos del proyecto con su nombre delante, como hoy.
- [ ] **CA-M-3 (Sin gateway con el respaldo):** con credenciales del entorno, `iniciar_gateway()` no arranca el gateway del proyecto y lo dice una vez en la salida del bucle (p. ej. «[orquestar] token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto»). `adevv telegram` / `--fondo` lanzado a mano en un proyecto así se niega con el mismo motivo, salvo que el `.env` del proyecto defina el token (incluido el propio repositorio del bot, que lo tendrá en su `.env`).
- [ ] **CA-M-4 (Pruebas y documentación):** pruebas de los dos orígenes (solo `.env`, solo entorno, ambos) para avisos, autoarranque y arranque manual, sin red y sin heredar las variables `TELEGRAM_*` reales (B-ADV-0007); documentación en `skills/telegram_gateway/SKILL.md` y `skills/orquestar/SKILL.md` (credenciales y su respaldo).
