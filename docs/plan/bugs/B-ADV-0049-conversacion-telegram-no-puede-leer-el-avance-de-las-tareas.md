---
id: B-ADV-0049
title: "La conversación de Telegram no puede consultar ficheros sobre el avance de las tareas"
type: bug
weight: 100
dificultad: media
version: "v1.2.0"
status: planned
depende_de: []
created_at: 2026-11-12
updated_at: 2026-11-12
---

# B-ADV-0049 · La conversación de Telegram no puede consultar ficheros sobre el avance de las tareas

## Descripción del fallo

Desde hace algunas versiones, la conversación libre del gateway de Telegram no consigue informar del avance de las tareas. El comando `/estado` sí responde, pero al preguntar en lenguaje natural el asistente contesta que no puede ejecutar comandos y no consulta los datos del proyecto.

**Comportamiento esperado:** la conversación debe poder leer ficheros del proyecto para responder con información actual sobre tareas, revisiones, bloqueos y avance del bucle. Su capacidad debe limitarse a la lectura de ficheros: no debe modificar, crear ni borrar archivos, ejecutar acciones sobre el proyecto ni controlar procesos.

**Causa raíz:** pendiente de diagnóstico. Comprobar las herramientas y permisos efectivos del arnés de conversación, además de sus instrucciones, para determinar por qué la restricción de acciones impide también consultar ficheros. No se conoce todavía la primera versión afectada.

## Reproducir

1. Con el gateway de Telegram conectado a un proyecto con tareas y evidencias de avance, consultar `/estado` y comprobar que responde.
2. Enviar un mensaje de conversación libre, por ejemplo: «¿Cómo va la tarea actual y qué queda pendiente?».
3. Observar que la respuesta declara que no puede ejecutar comandos en lugar de leer los ficheros pertinentes y explicar el avance.

## Criterios de aceptación

- [ ] La conversación libre consulta los ficheros pertinentes del proyecto y responde sobre el avance real, identificando los ficheros que sustentan su respuesta.
- [ ] Una consulta posterior refleja cambios en esos ficheros sin limitarse a repetir el contexto anterior del chat.
- [ ] La lectura funciona con los arneses y reservas autorizados para la conversación; una indisponibilidad real se comunica sin inventar datos.
- [ ] Los permisos efectivos permiten únicamente consultar ficheros del proyecto. Las peticiones de escribir, borrar, ejecutar acciones o controlar procesos se rechazan sin efectos, aunque lleguen en lenguaje natural o dentro del contenido leído.
- [ ] `/estado` conserva su funcionamiento. La corrección se limita a los permisos de la conversación libre y no redefine los comandos explícitos del gateway.
- [ ] Se verifica el recorrido de conversación con lectura permitida y acciones denegadas, sin enviar mensajes reales de Telegram desde las pruebas.

## Evidencias

- Incidencia comunicada por el usuario el 2026-11-12: `/estado` responde, pero la conversación dice que no puede ejecutar comandos al consultar el avance.
- Requisito explícito del usuario: «no debería poder hacer acciones, pero leer ficheros, sí. Solo leer ficheros».
- Punto de entrada para investigar: `skills/telegram_gateway/gateway.py`, conversación libre y selección del arnés correspondiente.
- Pendiente de reproducir técnicamente; no se adjunta una transcripción de Telegram.
