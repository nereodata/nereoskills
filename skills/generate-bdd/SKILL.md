---
name: generate-bdd
description: Generates a new BDD feature file following project standards
---

# Skill: Generar BDD (/generate-bdd)

Crea archivos `.feature` en español, integrados en `.feature` existentes.

## 📋 Pasos

### 1. Identificar
- Funcionalidad a testear.
- Componente afectado.

### 2. Estándares
- **Header**: `# language: es`.
- **Keywords**: Español (Característica, Escenario, Dado, Cuando, Entonces, Y).
- **Tags**: `@ui` (frontend), `@api` (backend), tags funcionales.
- **Estructura**: Característica → User Story (Ref: RF-XXX) → Escenarios.

### 3. Plantilla Base
```gherkin
# language: es
@componente @funcionalidad
Característica: Título (Español)
  Como [rol]
  Quiero [acción]
  Para [beneficio] (Ref: RF-XXX)

  Escenario: Descripción
    Dado que estado inicial
    Cuando realizo acción
    Entonces resultado esperado
```

### 4. Archivo
- Crear en la ruta de features del proyecto (p. ej. `<componente>/tests/features/`), integrado en
  un `.feature` existente, no nominal.
- Organizados por **funcionalidad del sistema**, nunca por tarea, fase o versión.

### 5. Reglas de integridad

- **Nunca elimines ni sustituyas un escenario existente.** Añadir cobertura no puede reducirla.
  Si uno te parece obsoleto o contradictorio, decláralo y detente: retirarlo es una decisión
  aparte, no un efecto colateral del cambio que estás especificando.
- **El escenario debe discriminar.** Un escenario nuevo tiene que **fallar** contra el código
  actual. Si pasa antes de implementar nada, no está verificando el comportamiento que describe:
  reescríbelo hasta que falle por la razón correcta. Ajusta los datos del escenario al
  comportamiento que quieres fijar, no al que hace que pase.
  - Exentos los `@hitl` (validación humana, sin suite que ejecutar): deben declarar qué se
    observa y qué resultado lo daría por inválido.
- **Etiquetas de criterio.** Si etiquetas con un criterio de aceptación (`@CA-*` o equivalente),
  ese criterio debe existir en la tarea o bug de origen. Una etiqueta que no referencia nada
  simula trazabilidad.
- **Conflictos.** Si el comportamiento que especificas contradice una decisión ya documentada
  (nota de diseño, comentario de contrato, test que la fija), no lo resuelvas por tu cuenta:
  señálalo con `archivo:línea` y detente. Elegir entre dos reglas incompatibles es una decisión
  de producto.

### 6. Validar
- Confirmar escenarios con usuario.

