---
id: B-ADV-0006
title: "Con la suite en rojo al cerrar la versión, el bucle se para en vez de registrar un bug y arreglarlo"
type: bug
weight: 40
dificultad: media
version: "v0.7.0"
status: planned
depende_de: []
created_at: 2026-10-26
updated_at: 2026-10-26
---

# B-ADV-0006: Con la suite en rojo al cerrar la versión, el bucle se para en vez de registrar un bug y arreglarlo

## 🎯 Descripción del Fallo

**Causa raíz**: en `bucle()` (`skills/orquestar/orquestar.py:2056`), cuando la versión abierta ya no tiene tareas elegibles (`cierre_de_version(e)`) se ejecuta la suite completa con `verificar()`. Si falla, el bucle termina con `parar(root, 'version', 'la versión no tiene más tareas elegibles pero la suite falla (...)')` (`:2057`). No se registra ningún bug ni se prepara un paso de `bug-fix`: solo se avisa al humano.

Además, `verificar()` (`:1517`) ejecuta la suite sin capturar su salida, así que tampoco hay material con el que describir el fallo.

**Comportamiento observado**: el bucle desatendido se detiene aunque el arreglo sea trivial (caso real: cinco ficheros sin formato de Prettier). Contradice el principio de `/orquestar` de que el humano solo intervenga al cerrar cada versión.

**Comportamiento esperado**: se mantiene el criterio de no cerrar una versión con la suite rota, pero el bucle sale de ahí por sí mismo:
1. Al cerrar la versión con la suite en rojo, registrar un bug **en esa versión** (`status: planned`, `version` de la rama release) con la salida del fallo: etapa que falla, ficheros afectados y errores, igual que haría `/bug-add`. Para ello `verificar()` debe guardar la salida (o al menos su cola) del comando.
2. A partir de ahí el bug es una tarea normal del ciclo: `estado()` lo elige como cualquier bug planificado de la versión, pasa por `bug-fix` y por Hades, y la suite se vuelve a ejecutar al llegar de nuevo al cierre.
3. Escalado por dificultad, con el mecanismo que ya existe (`comprobar_promocion()` / `promover_dificultad()`, `skills/orquestar/orquestar.py:956` y `:561`): si Hades rechaza varias veces **o la suite sigue fallando** tras el `bug-fix`, se sube la dificultad del bug para que lo resuelva un modelo más potente. Un nuevo fallo de la suite en el cierre cuenta como un intento fallido de ese bug; no se registra un bug nuevo por el mismo fallo.
4. Si el bug ya está en la dificultad máxima (`dificil`) y sigue sin resolverse tras **3 intentos**, el bucle para e informa (consola y Telegram) citando el bug y la última salida de la suite.
5. No cambia lo de siempre: en cada paso se sigue revisando si hace falta información del usuario, un cambio de requisitos, etc., y en ese caso se para como en cualquier otra tarea.

## 📋 Reproducir
1. En un producto orquestado, dejar la versión abierta sin tareas elegibles y con la suite rota (p. ej. ficheros sin formatear que hagan fallar el paso de Prettier).
2. Lanzar `/orquestar`.
3. Observado: `PARAR: la versión no tiene más tareas elegibles pero la suite falla (...)`, sin bug registrado.
4. Esperado: se registra `B-XXX-NNNN` con la salida del fallo, se ejecuta su `bug-fix`, se repite la suite y, si pasa, se sigue con `revisar-version`. Si vuelve a fallar, el bug sube de dificultad. En `dificil`, tras 3 intentos sin éxito, el bucle para e informa.

## 📋 Evidencias
- `skills/orquestar/orquestar.py:2056-2057` — parada al cerrar versión con suite en rojo (igual en `~/.adevv/versions/0.6.0`).
- `skills/orquestar/orquestar.py:1517` — `verificar()` no captura la salida de la suite.
- Caso observado: cinco ficheros con formato de Prettier pendiente.
