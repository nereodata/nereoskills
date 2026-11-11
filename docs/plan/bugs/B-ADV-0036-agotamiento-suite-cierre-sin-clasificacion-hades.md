---
id: B-ADV-0036
title: "El agotamiento de reintentos de la suite de cierre bloquea al humano sin diagnóstico de Hades"
type: bug
weight: 20
dificultad: dificil
version: "v1.1.2"
status: planned
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "Caso observado en Afinn release/v0.7, B-AFN-0185, con Adevv 1.1.1"
---

# B-ADV-0036: El agotamiento de reintentos de la suite de cierre bloquea al humano sin diagnóstico de Hades

## 🎯 Descripción del fallo

**Causa raíz:** al registrar una suite roja, `registrar_suite_roja()` usa el
contador `suite_intentos` como decisión de enrutado. Al llegar a tres intentos
en dificultad `dificil`, actualiza directamente el bug de cierre a
`status: blocked` y `pendiente_de: humano`, sin solicitar una revisión de
diagnóstico a Hades ni distinguir si el último fallo pertenece al mismo grupo
causal que los anteriores.

**Comportamiento observado:** en Afinn, `release/v0.7`, `B-AFN-0185`, después
de tres recaídas de la suite en dificultad `dificil`, el bucle se detuvo,
notificó por Telegram y dejó el bug pendiente del humano. Quedaban siete
fallos técnicos de integración, sin una decisión, permiso o recurso pendiente
del usuario. Las recaídas agrupaban fallos de causas distintas que aparecían
al ir avanzando la suite bajo un único bug de cierre.

**Comportamiento esperado:** al agotar los reintentos se pide una revisión
finita a Hades con los fallos vigentes, los arreglos intentados y la evidencia
de cada intento. Hades clasifica el impedimento y el bucle aplica su destino:

- `desarrollador`: continúa con un diagnóstico y una estrategia de corrección
  revisada.
- `especificador`: resuelve contradicciones o ambigüedades del contrato por el
  flujo de especificación.
- `humano`: bloquea solo si falta una decisión, permiso o recurso humano
  concreto; persiste la pregunta y su justificación.

Si no es posible avanzar técnicamente tras la revisión, Hades debe cerrar el
diagnóstico con los intentos y evidencias realizados e indicar la intervención
concreta requerida. No se reinicia el ciclo de forma ilimitada.

## 📋 Reproducir

1. Crear o reutilizar un bug de cierre de suite con dificultad `dificil`.
2. Registrar tres recaídas de la suite roja con evidencia de fallos técnicos de
   integración y sin una solicitud humana concreta.
3. Comprobar que, en la tercera recaída, el estado pasa directamente a
   `blocked` con `pendiente_de: humano` y se avisa por Telegram.
4. Repetir con grupos de fallos distintos que emergen secuencialmente de la
   suite y comprobar que el contador actual los trata como tres recaídas del
   mismo impedimento.

## ✅ Criterios de aceptación

1. Al alcanzar el umbral de reintentos en `dificil`, el contador por sí solo
   no asigna `pendiente_de: humano` ni emite una pregunta o aviso humano.
2. El orquestador solicita una única revisión diagnóstica finita de Hades con
   los fallos actuales, su evidencia y el historial de arreglos e intentos.
3. Un diagnóstico con destino `desarrollador` mantiene el bug elegible y
   aporta una estrategia de corrección revisada; el bucle continúa el trabajo.
4. Un diagnóstico con destino `especificador` conserva la trazabilidad y
   enruta automáticamente al flujo de especificación, sin pregunta humana.
5. Solo un diagnóstico con destino `humano` bloquea el bug con
   `pendiente_de: humano`, y exige una pregunta que identifique la decisión,
   permiso o recurso solicitado y su justificación.
6. El diagnóstico identifica y diferencia los grupos causales de fallos de
   suite. Los nuevos grupos que aparecen tras resolver otros no consumen como
   recaídas del mismo problema el presupuesto de éste.
7. Cuando Hades determine imposibilidad técnica de continuar, su salida es
   terminal, enumera intentos y evidencias y pide una intervención concreta;
   el orquestador no reabre diagnósticos indefinidamente.
8. Existen regresiones deterministas que cubren los destinos `desarrollador`,
   `especificador` y `humano`, y demuestran que llegar al contador no basta
   para bloquear al humano.

## 📋 Evidencias

- Caso comunicado: Afinn `release/v0.7`, `B-AFN-0185`, Adevv `1.1.1`.
- Tras tres recaídas en `dificil`, se observaron `status: blocked` y
  `pendiente_de: humano` sin clasificación de Hades.
- El caso conservaba siete fallos técnicos de integración y no requería
  decisión, permiso ni recurso humano.
- La implementación actual concentra la escalada directa en
  `skills/orquestar/orquestar.py`, en el registro de suite roja; las
  regresiones actuales comprueban precisamente la asignación humana al agotarse
  el contador.

## Triaje de alcance

- Subfase A: Definición — `[EXEC]`; especificar el contrato de diagnóstico
  terminal, destinos de Hades y agrupación causal de recaídas.
- Subfase B: Diseño — `[EXEC]`; definir el artefacto de diagnóstico, su
  identidad de grupo de fallo, los límites finitos y el enrutado.
- Subfase C1: Pruebas — `[EXEC]`; regresiones deterministas de los tres
  destinos, del umbral sin bloqueo humano y de grupos sucesivos de fallos.
- Subfase C2: Corrección — `[EXEC]`; sustituir la escalada directa por el
  diagnóstico de Hades y aplicar su salida de forma trazable.
- Subfase D: QA — `[PENDIENTE]`; revisión de código y del contrato de parada
  finita.
- Subfase E: Documentación — `[EXEC]`; actualizar la guía de recuperación de
  suites rojas y la semántica del contador.
- Subfase F: Cierre — `[PENDIENTE]`; tras la calidad y verificación completas.
- Verificación al cierre: pruebas de registro de suite roja y de enrutado de
  Hades en `tests/test_orquestar.py`, porque acreditan que el umbral no asigna
  el humano y que los tres destinos se procesan correctamente.

## Fuera de alcance

- No modificar Afinn, su rama `release/v0.7` ni sus requisitos como parte de
  esta corrección. El caso se conserva exclusivamente como evidencia de
  reproducción.
