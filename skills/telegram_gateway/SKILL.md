---
name: telegram-gateway
description: Gateway de Telegram para nereoskills (ingesta de tareas/bugs, consulta de estado y alertas)
---

# Skill: Telegram Gateway (/telegram-gateway)

Integración bidireccional entre la API de Telegram y el entorno de tareas de nereoskills.

## 🔐 Configuración (Variables de Entorno)
- `TELEGRAM_BOT_TOKEN`: Token API del bot proporcionado por `@BotFather`.
- `TELEGRAM_ALLOWED_USER_IDS`: Lista separada por comas de identificadores numéricos de usuarios de Telegram con permiso de interacción (ej. `"12345678,98765432"`).

## 📋 Capacidades y Comandos
1. **Seguridad:** Filtrado estricto por lista blanca. Cualquier mensaje de un usuario no listado es ignorado silenciosamente sin modificar archivos locales.
2. **Ingesta remota (Issue-as-Code v3.0):**
   - `/tarea <título>` o `/task <título>`: Registra la tarea en `docs/plan/tasks/` con estado `planned` si hay versión activa o `backlog` si no la hay.
   - `/bug <título>`: Registra la anomalía en `docs/plan/bugs/` con peso normal (100) y plantilla oficial de reproducción.
3. **Consulta de estado:**
   - `/estado` o `/status`: Devuelve el resumen estructurado en Markdown con la versión activa, la tarea en curso y los pendientes.
4. **Notificaciones salientes:**
   - Función `notify(text)`: Despacha alertas a los chats autorizados sin propagar excepciones al flujo del orquestador.

## 🛠️ Modos de Ejecución
- **Modo Polling (Daemon):**
  ```bash
  python -m skills.telegram_gateway.gateway --poll
  ```
- **Modo Notificación Saliente (CLI):**
  ```bash
  python -m skills.telegram_gateway.gateway --notify "Hito completado"
  ```
- **Modo Consulta de Estado (CLI):**
  ```bash
  python -m skills.telegram_gateway.gateway --status
  ```
