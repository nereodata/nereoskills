---
name: telegram-gateway
description: Gateway de Telegram de Adevv. Atiende a los usuarios autorizados mientras el bucle trabaja: /estado resume el bucle y el backlog; /tarea y /bug registran entradas sin versión; /nuevo reinicia el hilo. Cualquier otro mensaje mantiene conversación interactiva en texto libre con el asistente del proyecto conservando el hilo de sesión. Los avisos de eventos del bucle (fin de versión, cuota, paradas) los envía orquestar.py con la misma configuración.
---

# Skill: Telegram Gateway (/telegram-gateway)

Canal de entrada por Telegram para un proyecto que corre con `/orquestar`. Los avisos de salida (fin de versión, falta de cuota, paradas que necesitan respuesta, errores) no son del gateway: los envía el bucle (ver «Avisos por Telegram» en `/orquestar`).

## 🔐 Configuración (fichero `.env` en la raíz o variables de entorno)
- Fichero `.env` en la raíz (recomendado para aislar el bot de cada proyecto; excluido de git por defecto).
- `TELEGRAM_BOT_TOKEN`: token del bot (de `@BotFather`). Nunca commitear en git.
- `TELEGRAM_ALLOWED_USER_IDS`: IDs numéricos de Telegram autorizados, separados por comas. Solo ellos reciben respuesta, y son también los destinatarios de los avisos del bucle. Los mensajes de cualquier otro usuario se ignoran sin tocar nada.
- Modelo conversacional: configurable en `orchestration.json` bajo la clave `"telegram"` (`harness`, `model`, `effort`). Si no se define, hereda por defecto la configuración de `"atenea"`.

## 📋 Comandos y Conversación Libre
- `/estado` o `/status`: si el bucle está en marcha, parado o esperando cuota; la fase según el disco; la versión abierta (cerradas, en curso, bloqueadas); el backlog sin versión; las altas por registrar y el último paso.
- `/tarea <título>` (o `/task`) y `/bug <título>`: nueva tarea o bug maestro **sin versión** (`status: backlog`, como la deuda registrada). El bucle no lo trabaja hasta que le pones versión (o, si es un bug, hasta que `revisar-deuda` lo incluya). Las tareas van sin `depende_de`: se calculan cuando entran en una versión.
- `/nuevo` o `/reset`: elimina la sesión guardada del usuario emisor y reinicia el hilo de conversación.
- `/ayuda` (o `/help`, `/start`): lista de comandos disponibles.
- **Conversación libre**: cualquier mensaje enviado por un usuario autorizado que no comience por un comando fijo mantiene una conversación interactiva en texto libre con el asistente del proyecto. El hilo de la conversación se persiste automáticamente en `orquestar_telegram.json` (excluido de git) por usuario y arnés. Si la reanudación de una sesión previa falla, conmuta automáticamente a una sesión nueva sin interrumpir la experiencia.
- **Contexto seguro con el bucle en marcha**: si existe `orquestar.pid`, el asistente es instruido para no modificar ni commitear archivos rastreados del repositorio, limitándose a responder consultas, analizar el proyecto o sugerir registrar tareas o bugs mediante el buzón.

**Nunca escribe en el backlog con el bucle en marcha.** Deja la petición en el buzón (`orquestar_buzon.jsonl`, excluido de git) y el bucle la registra entre pasos, con un commit que solo lleva esos ficheros, y te avisa del ID. Sin bucle, la registra y la commitea en el momento, en la rama actual.

## 🛠️ Uso
Desde la raíz del proyecto, en una terminal aparte del bucle:
```bash
adevv telegram            # escucha (long polling) hasta Ctrl+C
adevv telegram --estado   # imprime lo que respondería /estado
```
