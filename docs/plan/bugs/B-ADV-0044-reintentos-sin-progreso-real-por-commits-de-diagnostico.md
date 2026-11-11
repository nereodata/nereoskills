---
id: B-ADV-0044
title: "Los commits que repiten un impedimento técnico reinician la detección de estancamiento"
type: bug
weight: 0
dificultad: dificil
version: "v1.1.3"
status: blocked
depende_de: []
perfil: {artemisa: {harness: codex, model: gpt-6-astra, effort: high}, hades: {harness: codex, model: gpt-6-astra, effort: high}, atenea: {harness: codex, model: gpt-6-astra, effort: high}, estricto: true}
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Incidente de release/v1.2, B-ADV-0031: al menos 28 ejecuciones repitiendo fallo de acceso de Hades"
pendiente_de: especificador
---

# B-ADV-0044 · Repetición indefinida de un impedimento técnico

## Incidente y alcance

El motor 1.1.2 repite bug-fix B-ADV-0031. Hades no puede acceder al disco (registered Core launch requires an installed app). Cada ejecución añade otra nota a la ficha y crea un commit docs(plan), sin dictamen ni arreglo. firma() incluye HEAD, estado Git y huella del árbol. El motor interpreta cada nota como progreso, reinicia sin_progreso y vuelve a lanzar. Ejemplos en release/v1.2: 664a50e, d686fe3, 9300ebc y be73a02. La revisión comenzó a avanzar solo cuando se aportó el material completo como adjuntos.

Analizar el origen histórico antes de llamarlo regresión y registrar el commit que introdujo o dejó expuesta esta conducta. Considerar las distintas vías de progreso y no limitar el diagnóstico a eliminar HEAD de una tupla. Las modificaciones de la ficha también alteran el árbol.

## Criterios de aceptación

- Reproducir con arneses simulados que repiten el mismo impedimento y crean commits o cambian solo la redacción de notas. La repetición debe ser acotada y recuperar o ceder de forma explícita sin consumir indefinidamente.
- Diferenciar avance acreditado (código o pruebas relevantes, especificación o dictamen vigente, resolución de una respuesta) de notas repetidas, timestamps y commits vacíos. Conservar la compatibilidad con tareas antiguas y WIP.
- Los fallos técnicos del revisor no son aprobaciones, ni se atribuyen automáticamente al humano. Respetar perfiles y reservas. Evitar trasladar el bucle infinito a otra rama de recuperación.
- No confundir progreso parcial con tarea completada. Conservar la barrera de cierre revisado de B-ADV-0039, el consumo real y los fallos de cuota.
- Cubrir entradas reales del bucle, alternancia de tareas, cambio de proveedor, reinicio manual y recarga cooperativa según el contrato que determine el análisis. Documentar explícitamente el límite de recuperación y qué estado persiste.
- Verificar mediante un caso de control que una tarea que avanza realmente no se bloquea por falso estancamiento. Revisar también pasos de análisis afectados.
- Hades debe analizar la especificación, las regresiones y la corrección. Usar el modelo potente fijado por el usuario, sin degradación silenciosa. Desde la primera llamada proporcionar instrucciones, criterios, delta exacto completo y evidencias en el mandato para permitir el dictamen sobre adjuntos si falla el acceso a disco. Conservar la independencia y registrar sus limitaciones.

## Entrega urgente

Construir el hotfix sobre v1.1.2, ejecutar las regresiones y la suite completa al cierre, publicar v1.1.3 e instalar. Integrar después la corrección en release/v1.2 conservando la versión 1.2.0 y su trabajo. El usuario autorizó la rama urgente, el modelo potente y la instalación. El bucle original de Adevv tiene solicitada una parada cooperativa.

## Hallazgo de Hades enrutado
- Destino: `especificador`
- Decisión: ejecutar especificar
- Evidencia: Hades rechazó /review-spec (8,25/10) y asignó dos hallazgos altos al especificador. H1: exigir dos salidas normales con commits limpios que solo reformulen el impedimento en la ficha y el resumen de versión, parada técnica tras el segundo y ninguna tercera invocación. H2: contrastar completed con aprobación canónica anterior al delta y revisión actual pendiente frente a aprobación vigente, con el mismo commit parcial y retorno de error. H3 (medio, resolver): vincular código WIP y prueba al comportamiento del bug. Ejecutar especificar. Triaje, escenarios e informe literal en wip/B-ADV-0044, commit 99dd5a1; base_calidad 4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5. Hades dictaminó sobre los adjuntos por fallo de acceso a disco.
