---
id: T-ADV-0019
title: "Firma de versión de Adevv al pie de los mensajes de Telegram y modelos configurados siempre visibles en /estado"
type: funcional
weight: 200
dificultad: sencilla
version: "v0.5.0"
status: planned
depende_de: ["T-ADV-0018"]
origen: "Identificar en cada mensaje de Telegram la versión de Adevv que responde y ver los modelos/cuota aunque el bucle esté parado"
created_at: 2026-10-24
updated_at: 2026-10-24
---

# T-ADV-0019: Firma de versión de Adevv al pie de los mensajes de Telegram y modelos configurados siempre visibles en /estado

## 🎯 Objetivo de Negocio
Permitir ver en cada mensaje de Telegram con qué versión de Adevv se ha generado (para detectar de inmediato si algún proyecto no ha actualizado aún) y asegurar que `/estado` y `adevv orquestar --estado` muestren siempre los modelos configurados del proyecto y su estado de cuota incluso cuando el bucle está parado (`FIN` o `PARAR`) o lleva más de 5 horas sin actividad.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Firma con la versión de Adevv al pie de los mensajes de Telegram):** Todos los mensajes enviados por Telegram —tanto las respuestas de `responder()` en `skills/telegram_gateway/gateway.py` (comandos y conversación libre) como los avisos enviados por `avisar()` en `skills/orquestar/orquestar.py`— incluyen al final una línea de pie con la versión en ejecución de Adevv (p. ej. `v0.5.0`, obtenida de la carpeta de versión o de `adevv.__version__` / `pyproject.toml`), con formato legible como `— Adevv vX.Y.Z` (y en conversación libre incluyendo además el `harness/model` que respondió, p. ej. `— Adevv vX.Y.Z · agy/gemini-4-argon-medium`).
- [ ] **CA-M-2 (Modelos configurados y estado de cuota siempre visibles en `/estado` y `--estado`):** En `detalle_estado(root, e)` de `skills/orquestar/orquestar.py`, incluso cuando `e[0]` no es `'PASO'` (es decir, cuando el bucle está en `PARAR` o `FIN`) y aunque no haya ejecuciones en las últimas 5 horas, se muestran los modelos configurados en `orchestration.json` para el proyecto (`artemisa`, `hades`, `atenea` y sus reservas) junto con su estado de cuota (`sin agotamiento registrado` / `0 tokens (5 h)` o la espera restante si hay cuota agotada vigente).
- [ ] **CA-M-3 (Pruebas unitarias y documentación):** Pruebas unitarias en `skills/orquestar/` y `skills/telegram_gateway/` validan la firma de versión al pie de respuestas y avisos de Telegram y la presencia de los modelos configurados y su estado de cuota en `parte()` y `resumen()` cuando el estado es `FIN` o `PARAR` sin actividad reciente.
