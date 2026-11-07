---
id: T-ADV-0033
title: "Delimitar la autonomía del arnés para preservar el ciclo de revisión de Adevv"
type: funcional
weight: 100
dificultad: media
version: ""
status: backlog
depende_de: []
origen: "Petición del usuario (2026-11-05): mantener la iniciativa y la paralelización del arnés evitando revisiones paralelas al ciclo controlado por Adevv"
created_at: 2026-11-05
updated_at: 2026-11-05
---

# T-ADV-0033: Delimitar la autonomía del arnés para preservar el ciclo de revisión de Adevv

## 🎯 Objetivo de Negocio

Conservar la capacidad del arnés para organizar y paralelizar el trabajo del paso que ejecuta, manteniendo en Adevv la autoridad sobre las revisiones formales. Evitar que el arnés lance por iniciativa propia un circuito adicional de revisión, con coste duplicado o sin el perfil, aislamiento y trazabilidad configurados.

## Enfoque propuesto

Establecer un contrato breve por responsabilidad: el arnés decide cómo ejecutar su encargo y puede delegar exploración, implementación, pruebas o diagnóstico dentro de ese alcance. Las revisiones formales previstas por el flujo se solicitan mediante el canal de Adevv; no se sustituyen ni se duplican con revisores nativos del arnés, aunque se les dé otro nombre.

La comprobación ordinaria del trabajo, la lectura crítica y el diagnóstico siguen permitidos. Encargar a otro agente un veredicto independiente de aceptación sobre especificación, pruebas, código o arquitectura constituye una revisión formal y sigue el circuito de Adevv. El criterio es la responsabilidad delegada, no el nombre del agente ni la herramienta utilizada.

Hades puede repartir el análisis de una revisión si lo considera útil, conservando su alcance y aislamiento, y emitiendo un único informe y veredicto bajo la revisión solicitada. Esa descomposición no abre otro ciclo de revisión del revisor.

## Base existente y delta

- `skills/orquestar/orquestar.py`: `construir_prompt_paso` ya indica el lanzamiento de Hades mediante `adevv orquestar --agente hades --prompt-file <mandato>`; `construir_prompt_agente` prepara el contexto de los roles.
- `agents/artemisa.md`, `agents/hades.md` y las skills de desarrollo y revisión establecen responsabilidades, aislamiento y puntos de revisión.
- El delta consiste en explicitar y transmitir la frontera entre delegación operativa y revisión formal, reconciliando instrucciones que puedan inducir ciclos duplicados. No requiere crear un segundo orquestador ni un planificador de subagentes.

## 📋 Criterios de Aceptación (Nivel Máster)

- [ ] **CA-M-1 — Autonomía dentro del encargo:** las instrucciones permiten al arnés decidir si divide y paraleliza el trabajo del paso actual sin imponer un número fijo de agentes ni solicitar autorización adicional para esa organización.
- [ ] **CA-M-2 — Canal único de revisión formal:** las revisiones requeridas por el flujo se solicitan mediante Adevv y respetan su configuración efectiva, perfiles, aislamiento, continuidad y registro. Se prohíbe sustituirlas o añadir revisiones formales paralelas por iniciativa del arnés mediante mecanismos nativos o lanzamientos directos de otros arneses.
- [ ] **CA-M-3 — Distinción por responsabilidad:** las instrucciones distinguen comprobación y diagnóstico de revisión formal mediante ejemplos concretos. Ejecutar pruebas, investigar un fallo o comprobar una implementación está permitido; delegar un veredicto independiente sobre su aceptación corresponde al circuito de revisión.
- [ ] **CA-M-4 — Delegación con el mismo límite:** el mandato de los colaboradores conserva el alcance del encargo y la reserva de las revisiones formales a Adevv. La delegación anidada no sirve para eludir esa frontera. Hades puede distribuir análisis dentro de la revisión recibida, manteniendo el aislamiento y un único informe y veredicto, sin revisiones recursivas de su propio trabajo.
- [ ] **CA-M-5 — Aplicación coherente:** el contrato se transmite por las entradas pertinentes, tanto en pasos como en invocaciones de roles y sus reanudaciones. Skills, agentes y workflows distribuidos no contienen instrucciones contradictorias que pidan un revisor nativo adicional. Si Hades está desactivado, se respeta esa configuración sin inventar un sustituto.
- [ ] **CA-M-6 — Verificación y límites honestos:** las pruebas comprueban la presencia y coherencia del contrato en los mandatos aplicables y que el circuito existente de Hades conserva su comportamiento. Se documenta que una instrucción orienta al modelo pero no impide técnicamente cualquier incumplimiento; no se promete interceptar herramientas internas que Adevv no controle.

## Alcance y límites

Registrar esta capacidad como una única tarea, sin versión asignada. El diseño decidirá la ubicación común del contrato y cómo evitar duplicaciones, aprovechando la construcción de prompts y las instrucciones existentes. Mantener el texto breve y centrado en responsabilidades; no introducir restricciones generales a subagentes, interceptores específicos por arnés, ni nuevas puertas de aprobación.
