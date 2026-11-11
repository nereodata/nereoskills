---
id: B-ADV-0045
title: "El ejecutor de Codex no inicia las herramientas de lectura y escritura de Hades"
type: bug
weight: 1
dificultad: dificil
version: "v1.1.3"
status: planned
depende_de: []
perfil: {artemisa: {harness: codex, model: gpt-6-astra, effort: high}, hades: {harness: codex, model: gpt-6-astra, effort: high}, atenea: {harness: codex, model: gpt-6-astra, effort: high}, estricto: true}
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Petición expresa del usuario; incidente B-ADV-0031 en release/v1.2 y revisiones de v1.1.2"
---

# B-ADV-0045 · Fallo de herramientas en el ejecutor de Hades

## Hechos observados

En sesiones Codex lanzadas como Hades por Adevv, la herramienta de ejecución de comandos y la alternativa Node fallan con registered Core launch requires an installed app. El revisor no logra leer sus instrucciones, la skill de revisión ni las fuentes del repositorio y tampoco puede escribir el informe canónico. Una salida del proceso con código cero puede carecer de dictamen. Aportar todo el material en el mandato permitió dictámenes independientes, pero deja sin resolver el fallo de las herramientas.

Evidencia accesible en el worktree principal C:/Users/Iván Moreno/SW/Adevv, rama release/v1.2, en la ficha y el informe de especificación de B-ADV-0031, orquestar.log y métricas. Las sesiones de Hades de v1.1.2 también documentan el mismo error. El lanzador de roles Codex usa exec o exec resume, approval_policy never y sandbox workspace-write. Estas opciones son contexto para diagnosticar, no una causa raíz confirmada.

## Alcance urgente y criterios de aceptación

- Reproducir el fallo mediante la entrada normal de Hades y recoger el comando efectivo, ejecutable resuelto, versión de CLI, directorio, entorno pertinente y error. Excluir credenciales y datos privados del registro.
- Determinar si el origen está en Adevv, la resolución de ejecutables, la configuración heredada o el runtime externo. Contrastar sesión nueva y reanudada e identificar el cambio histórico cuando sea posible. No afirmar una regresión sin evidencia.
- Corregir la causa identificada y demostrar que una sesión real de Hades puede leer el contenido exacto de un archivo del checkout y escribir su informe canónico por sus herramientas normales, con veredicto independiente sobre el alcance solicitado.
- Conservar el aislamiento y los permisos previstos del revisor. Cambiar a ejecución sin sandbox o desactivar herramientas no satisface este arreglo. Cualquier ajuste de entorno debe ser mínimo y compatible con otros proyectos, arneses y sesiones reanudadas.
- Añadir regresiones deterministas del defecto de lanzamiento o configuración y una comprobación real en este equipo. El uso de adjuntos por sí solo no acredita el arreglo del ejecutor.
- Si la causa requiere actualizar o reparar un componente externo, registrar la acción y verificar el recorrido real después. Mantener el bug abierto mientras no se pueda demostrar el arreglo.
- Verificar conjuntamente con B-ADV-0044 que un fallo operacional no produce una aprobación falsa ni una repetición ilimitada.

## Condición de publicación e instalación

El usuario exige resolver B-ADV-0044 y B-ADV-0045 en v1.1.3 antes de instalarla. Ambos deben estar completados con sus dictámenes y evidencias. Mantener la versión instalada 1.1.2 mientras quede cualquiera pendiente.
