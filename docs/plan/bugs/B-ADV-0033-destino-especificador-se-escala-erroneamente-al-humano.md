---
id: B-ADV-0033
title: "El orquestador escala al humano hallazgos de Hades destinados al especificador"
type: bug
weight: 20
dificultad: media
version: "v1.1.1"
status: planned
created_at: 2026-11-09
updated_at: 2026-11-10
---

# B-ADV-0033: El orquestador escala al humano hallazgos de Hades destinados al especificador

## 🎯 Descripción del Fallo

**Causa raíz:** el enrutado posterior al informe de Hades pierde o ignora el destino `especificador`. En consecuencia, trata esos hallazgos como si requiriesen una decisión humana, crea una entrada en `orquestar_preguntas.json` y bloquea la tarea, en vez de ejecutar automáticamente el flujo `especificar`, incorporar la decisión y reanudarla.

**Comportamiento observado:** en Afinn v0.7, Hades asignó correctamente `T-AFN-0139`, hallazgo `H-02`, y `T-AFN-0140`, hallazgo `C-1`, a `especificador`. El orquestador creó, no obstante, las preguntas humanas `Q-AFN-0001` y `Q-AFN-0002` y bloqueó ambas tareas. El fallo no está en el juicio de Hades, sino en el enrutado posterior.

**Comportamiento esperado:**
1. Un destino `artemisa` devuelve el hallazgo a desarrollo.
2. Un destino `especificador` ejecuta automáticamente el flujo de especificación, conserva la trazabilidad entre hallazgo y decisión incorporada, y reanuda la tarea sin intervención humana.
3. Solo un destino `humano` crea una pregunta o bloqueo en `orquestar_preguntas.json`.
4. La existencia de WIP, commits intercalados o una tarea bloqueada no convierte por sí misma un destino `especificador` en un bloqueo humano.

## 📋 Reproducir

1. Procesar un informe de Hades que incluya un hallazgo con destino `especificador` para una tarea en curso.
2. Observar que el orquestador crea una entrada en `orquestar_preguntas.json` y bloquea la tarea, en lugar de invocar `especificar`.
3. Procesar un hallazgo equivalente con destino `humano` y verificar que sí crea una pregunta humana.

## ✅ Criterios de aceptación

1. Un hallazgo de Hades con destino `especificador` nunca crea una entrada humana en `orquestar_preguntas.json`.
2. El orquestador ejecuta el especificador y conserva trazabilidad del hallazgo y de la decisión incorporada.
3. Tras incorporar el cambio, la tarea vuelve al flujo normal sin intervención humana.
4. Un hallazgo con destino real `humano` continúa creando su pregunta; por ejemplo, cuando falta una capacidad o herramienta de navegador para obtener evidencia visual.
5. Existe una prueba de regresión que cubre los tres destinos: `artemisa`, `especificador` y `humano`.

## 📋 Evidencias

- Afinn v0.7: `T-AFN-0139` / `H-02` y `T-AFN-0140` / `C-1`, asignados por Hades a `especificador`.
- Preguntas creadas erróneamente: `Q-AFN-0001` y `Q-AFN-0002`.
- Caso de contraste válido para `humano`: `T-AFN-0141`, por falta de una capacidad o herramienta de navegador para evidencia visual.

## Triaje de alcance

- Subfase A: Definición — `[EXEC]`; escenario BDD con los tres destinos.
- Subfase B: Diseño — `[EXEC]`; añade el contrato explícito de enrutado y su trazabilidad.
- Subfase C1: Pruebas — `[EXEC]`; regresión que comprueba `artemisa`, `especificador` y `humano`.
- Subfase C2: Corrección — `[EXEC]`; el motor preserva destinos de Hades, y la CLI permite declararlos sin degradarlos a pregunta humana.
- Subfase D: QA — `[PENDIENTE]`; revisión del delta completo al finalizar ambas correcciones del hotfix.
- Subfase E: Documentación — `[EXEC]`; escenario de orquestación y changelog.
- Subfase F: Cierre — `[PENDIENTE]`; tras calidad y revisión.
- Verificación al cierre: `python -m unittest tests.test_orquestar.HallazgosHadesRoutingTests`, porque acredita los tres destinos y la ausencia de preguntas para el especificador.

## Resolución

- Se añade `--enrutar-hallazgo <ID> <artemisa|especificador|humano>` y el mandato de los pasos obliga a usarlo para los destinos asignados por Hades.
- `especificador` conserva la tarea en `blocked` con `pendiente_de: especificador`, registra la evidencia y deja que el bucle ejecute `especificar`; `artemisa` la devuelve a `planned`; solo `humano` crea una pregunta persistente.
- El detector de bloqueos conserva como salvaguarda el destino explícito presente en el contexto o salida del paso.
- El selector del bucle reconoce también ramas `hotfix/v*`, de modo que el flujo automático funciona en `hotfix/v1.1.1`.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades RECHAZADO (docs/review/code_reviews/B-ADV-0033-code-review.md). H-01 ALTA para desarrollador/Artemisa: detectar_bloqueo recorta a 4000 caracteres antes de extraer destino y puede perder especificador, creando pregunta humana; extraer antes del recorte y definir precedencia. H-02 ALTA para desarrollador/Artemisa: destino_hallazgo no reconoce etiquetas Markdown resaltadas o entre backticks; soportarlas sin degradar a humano. Decisión: reanudar desarrollo, corregir ambos y ampliar únicamente HallazgosHadesRoutingTests con los casos indicados antes de reevaluar.
