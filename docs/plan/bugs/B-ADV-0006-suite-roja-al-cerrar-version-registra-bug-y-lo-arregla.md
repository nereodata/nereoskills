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
2. Continuar con el `bug-fix` de ese bug (lo elegirá `estado()` como cualquier bug planificado de la versión) y volver a ejecutar la suite al llegar de nuevo al cierre.
3. Parar solo si el **mismo fallo persiste** tras el intento de arreglo (p. ej. misma firma de etapa/ficheros/errores, o el bug autogenerado ya existe cerrado o en curso para ese fallo), para no entrar en un bucle infinito. En ese caso el mensaje de parada y el aviso por Telegram referencian el bug.

## 📋 Reproducir
1. En un producto orquestado, dejar la versión abierta sin tareas elegibles y con la suite rota (p. ej. ficheros sin formatear que hagan fallar el paso de Prettier).
2. Lanzar `/orquestar`.
3. Observado: `PARAR: la versión no tiene más tareas elegibles pero la suite falla (...)`, sin bug registrado.
4. Esperado: se registra `B-XXX-NNNN` con la salida del fallo, se ejecuta su `bug-fix`, se repite la suite y, si pasa, se sigue con `revisar-version`.

## 📋 Evidencias
- `skills/orquestar/orquestar.py:2056-2057` — parada al cerrar versión con suite en rojo (igual en `~/.adevv/versions/0.6.0`).
- `skills/orquestar/orquestar.py:1517` — `verificar()` no captura la salida de la suite.
- Caso observado: cinco ficheros con formato de Prettier pendiente.
