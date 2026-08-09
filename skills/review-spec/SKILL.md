---
name: review-spec
description: Evaluación de la calidad de la especificación (escenarios BDD + evals) antes de implementar
inputs:
  - spec_file: Ruta de la especificación a revisar
outputs:
  - verdict: APROBADO o RECHAZADO
---

# Skill: Specification Review (/review-spec)

Audita la especificación (escenarios BDD a nivel feature y evals de IA) antes de escribir código.

## 📋 Pasos de la Skill

### 1. Comprobaciones obligatorias

Se verifican por búsqueda o por diff, no por criterio. **Si alguna falla, el veredicto es
RECHAZADO con independencia de la puntuación.** Cada una se reporta con su evidencia.

- **No regresión de cobertura**: revisa el diff de los `.feature`. Ningún escenario preexistente
  puede eliminarse ni sustituirse. Si uno te parece obsoleto, señálalo y detente — retirarlo es
  una decisión del propietario de la especificación, no un efecto colateral del cambio en curso.
- **Conflicto con decisiones vigentes**: enumera toda decisión ya documentada —nota de diseño,
  comentario de contrato, test que la fija— que esta especificación contradiga, con
  `archivo:línea`. Si no hay ninguna, decláralo explícitamente. Una especificación que contradice
  una decisión vigente sin derogarla delega la decisión de producto en quien implemente, y quien
  implementa resolverá el empate inventando una regla intermedia.
- **Trazabilidad de etiquetas**: toda etiqueta de criterio (`@CA-*` o equivalente) debe
  referenciar un criterio que exista en la tarea o bug de origen. Compruébalo por búsqueda. Una
  etiqueta que no apunta a nada simula trazabilidad sin tenerla.
- **El escenario discrimina**: cada escenario nuevo ejecutable debe **fallar** contra el código
  anterior al cambio. Uno que pasa antes y después no verifica nada, por bien redactado que esté.
  Los `@hitl` quedan exentos por no tener suite que ejecutar, pero deben declarar qué se observa
  y qué resultado lo daría por inválido.

### 2. Evalúa (1-10 por pilar)

- **Claridad**: Escenarios sin ambigüedades, `Dado/Cuando/Entonces` concretos.
- **Completitud**: Camino feliz, casos límite, errores. Enumera el espacio de casos antes de
  puntuar (fronteras e igualdades exactas, vacíos y nulos, unidades y husos, orden y
  concurrencia) y señala los que la especificación no cubre.
- **Testeabilidad**: Resultados observables y objetivos. El escenario asevera el **contenido** del
  resultado, no solo su presencia.
- **Estructura**: Integrados en `.feature` existentes (no nominales), organizados por
  funcionalidad y nunca por tarea, fase o versión.
- **Alcance colateral**: Declara qué funcionalidades vecinas **no** deben verse afectadas, de modo
  que existan como aserción y no como suposición.

### 3. Reporte [`docs/review/spec_reviews/[ID]-spec-review.md`]

- **Veredicto**: APROBADO (>8 **y** sin comprobación obligatoria fallida) / RECHAZADO
- **Comprobaciones obligatorias**: resultado de cada una con su evidencia (`archivo:línea`,
  salida de la búsqueda, líneas eliminadas del diff).
- **Por Pilar**: Puntuación + nota breve.
- **Mejoras**: 🔴 CRÍTICO | 🟠 ALTA | 🟡 MEDIA | 🔵 BAJA
