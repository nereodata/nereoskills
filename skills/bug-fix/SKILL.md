---
name: bug-fix
description: Proceso y criterios para la resolución completa de anomalías (bugs)
---

# Skill: Resolución de Anomalías

Conocimiento de proceso para la resolución de bugs, siguiendo la jerarquía **Master/Componente v3.0**.

## Modos de Ejecución

1.  **Modo Maestro (Master Fix)**:
    - Entrada: `B-[PRJ]-XXXX`
    - Analizar todos los componentes afectados por el bug maestro y evaluar sus dependencias.
    - Componentes independientes pueden ejecutarse en paralelo.
    - Componentes con dependencias: ejecutar secuencialmente en orden de dependencia.
2.  **Modo Componente (Componente Fix)**:
    - Entrada: `B-[PRJ]-[COMP]-XXXX`
    - Foco exclusivo en la corrección técnica de un componente.

## Fases de la Resolución

### 0. Clasificación de Urgencia y Rama de Trabajo
- Determinar: **¿hotfix (urgente, producción) o release (bloque funcional actual)?**
- **Si hotfix**:
  - Identificar la versión de producción afectada (último tag en `main`).
  - Calcular la versión patch: si el último tag es `vX.Y.Z`, la rama será `hotfix/vX.Y.(Z+1)`.
  - Crear la rama desde el tag correspondiente.
  - Actualizar la versión en los manifiestos al patch correspondiente.
  - Commit inicial: `chore(hotfix): start hotfix vX.Y.Z`
- **Si release**:
  - Verificar que la rama activa es `release/vX.Y`.
  - Si no lo es, advertir al usuario y sugerir cambiar a la rama release activa.
- En ambos casos, actualizar el campo `version` del bug con la versión de la rama de trabajo.

### 1. Reproducción y Análisis
- Cargar metadatos del bug y la versión actual de `task_config.yaml` (`project.version`).
- Cambiar `status` a `in_progress`.
- Establecer `actual_effort` y actualizar `remaining_effort`.
- Crear/actualizar BDD y Unit Test que capturen el fallo.
    - Integrar el escenario en un `.feature` de sistema existente. No crear archivos `.feature` nominales al bug o ID de tarea: los feature son de sistema, no de proceso.
- Validar calidad de tests (puntuación mínima 8/10).
- **HITL — Validación de reproducción**: verificar que los tests capturan correctamente el fallo antes de implementar la corrección.

### 2. Corrección (Fix Phase)
- Implementar la corrección siguiendo estándares (Docstrings obligatorios, no comentarios inline).
- Verificar que los tests pasan.
- **HITL — Validación funcional**: el usuario valida que la corrección funciona correctamente en contexto (integración visual, UX, efectos secundarios) — lo que los tests BDD/unitarios no cubren.

### 3. Revisión de Calidad (QA Phase)
- Ejecutar suite de pruebas completa para descartar regresiones.
- Revisión de código (8 áreas, puntuación mínima 8/10).
- Incluir en la evaluación: descripción del bug original y criterios de aceptación.
- Esta fase debe ejecutarse con evaluación objetiva, sin influencia de las decisiones tomadas durante la corrección.

### 4. Documentación y Cierre
- Documentar la solución y actualizar métricas de esfuerzo en el archivo de backlog.
- Marcar `status: completed` y asegurar que `version` coincide con la actual de `task_config.yaml`.
- Actualizar documentación del proyecto.
- Si es **Master Fix**, verificar si otros componentes requieren correcciones para el mismo problema.
- Generar commit con el prefijo `fix([ID])`.
