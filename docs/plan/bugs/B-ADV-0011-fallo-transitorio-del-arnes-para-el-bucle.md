---
id: B-ADV-0011
title: "Un fallo del arnés que no es de cuota para el bucle sin reintentar ni usar reservas"
type: bug
weight: 15
dificultad: media
version: "v1.0.0"
status: planned
depende_de: []
origen: "Revisión humana de los puntos de parada de orquestar.py (2026-10-27): para sin necesitar al humano"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0011: Un fallo del arnés que no es de cuota para el bucle sin reintentar ni usar reservas

## 🎯 Descripción del Fallo

**Causa raíz**: en `bucle()` (`skills/orquestar/orquestar.py`, hacia la línea 2447), si el arnés termina con código distinto de 0 y no se detecta falta de cuota, el bucle para con «el arnés terminó con código N (¿autenticación, red?)». Las reservas solo se prueban si falta cuota (`espera_cuota()`) o si no se encuentra el arnés (`ArnesAusente`).

**Comportamiento observado**: un corte de red, un error 5xx de la API o un cuelgue del arnés paran el bucle desatendido entero, a menudo de noche.

**Comportamiento esperado**:
1. Reintenta el mismo perfil con espera creciente (por ejemplo, 1, 5 y 15 min), con un tope configurable.
2. Si sigue fallando, pasa a la siguiente reserva de `lista_reservas()`, igual que cuando falta cuota.
3. Solo para si fallan todas las configuraciones tras los reintentos. El aviso incluye la cola de la salida del arnés para distinguir un problema de autenticación (que sí requiere a una persona) de uno de red.
4. Se mantiene el caso actual de «paso completado en disco a pesar del retorno».
5. Pruebas con un arnés simulado que falla de forma transitoria y otro que falla de forma persistente.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario ha pedido este cambio expresamente: el bucle solo debe pararse cuando haga falta una decisión humana. Si hay que cambiar requisitos o escenarios del bucle (orquestar), forma parte del alcance de este bug. Se puede tocar cualquier ruta necesaria.
