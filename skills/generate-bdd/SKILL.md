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
- Crear en `<componente>/tests/features/` (integrado en `.feature` existente, no nominal).

### 5. Validar
- Confirmar escenarios con usuario.

