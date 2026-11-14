---
name: orquestar
description: Lleva un producto de la idea a su última tarea sin parar. Invocada por una persona, lanza el bucle desatendido, informa de cómo va o lo para; el bucle deduce la fase del disco y continúa desde donde toque. Invocada por el bucle, ejecuta el paso indicado en modo orquestado.
---

# Skill: Orquestar (/orquestar)

## Uso humano
- **Lanzar en segundo plano:** `adevv orquestar --fondo`
- **Ver estado:** `adevv orquestar --estado`
- **Parar al acabar el paso actual:** `adevv orquestar --parar`
- **Consultar métricas y costes:** `adevv orquestar --metricas [ultima|todas|vX.Y]`
- **Preguntas humanas pendientes:** `adevv orquestar --preguntas` y `adevv orquestar --responder <Q-ID> "<respuesta>"`

## Modo orquestado (cuando te invoca el bucle)
1. **Un solo paso:** ejecuta únicamente el paso recibido y haz `git commit` dejando el árbol limpio.
2. **Autonomía sin ceremonias:** sigue la política activa (`PROJECT.md` o política base). Si un bloqueo externo real impide avanzar sin decisión humana, regístralo con `adevv orquestar --preguntar <ID> "<pregunta concreta>"` y termina.
3. **Verificación focalizada con caché:** usa `adevv orquestar --verificar "<comando>"` (cacheado por huella de producto: editar documentos de plan o revisión no invalida las pruebas).

| Paso | Qué hacer | Hecho cuando |
|---|---|---|
| `ciclo-requisitos` | Ejecuta `/ciclo-requisitos` sobre `<docs>/requirements.md` sin preguntas interactivas | existe `<docs>/req_analysis.md` |
| `platform-plan` | Ejecuta `/platform-plan` | existe `<docs>/platform_plan.md` |
| `work-plan` | Ejecuta `/work-plan` dejando tareas con `version` y `depende_de` | existe `<docs>/work_plan.md` |
| `start-version` | Ejecuta `/start-version` con la versión indicada | rama `release/vX.Y` activa |
| `task-dev` | Ejecuta `/task-dev <ID>` | ficha en `status: completed` y commit limpio |
| `bug-fix` | Ejecuta `/bug-fix <ID>` | ficha en `status: completed` y commit limpio |
| `revisar-producto` | Ejecuta `/revisar-producto` sobre la versión | `vX.Y-producto.md` con `**Decisión:** PENDIENTE` |
| `aplicar-producto` | Ejecuta `/revisar-producto` (`aplicar-producto`) | `**Decisión:** APLICADA` |

*(Las revisiones `revisar-plataforma`, `revisar-tarea` y `revisar-version` las lanza directamente el motor contra Hades sin agente intermediario).*
