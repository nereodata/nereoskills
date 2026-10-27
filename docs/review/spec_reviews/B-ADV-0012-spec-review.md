# Revisión de especificación — B-ADV-0012

**Veredicto: RECHAZADO**

Fecha: 2026-10-27. Revisor: Hades.

## Alcance

Se revisan exclusivamente los tres escenarios añadidos en `tests/features/uso_sin_rutas.feature:153-179`, contra el contrato de `docs/plan/bugs/B-ADV-0012-tarea-atascada-en-dificil-para-todo-el-bucle.md`. El diff se usa para comprobar que los escenarios previos permanecen intactos; no se reevalúan. Se aplican el agente Hades y la skill `review-spec` de la instalación 0.6.1, ignorando el modelo del frontmatter.

La decisión humana del contrato autoriza cambiar la parada global por bloqueo local y continuidad con otras tareas elegibles. No se considera ese cambio una contradicción. No se revisan código ni diseño, ni se ejecutan pruebas de implementación.

## Comprobaciones obligatorias

| Comprobación | Resultado | Evidencia |
| --- | --- | --- |
| No regresión | ✅ | El delta solo añade escenarios; no elimina ni modifica los anteriores. |
| Coherencia | ✅ | El bloqueo local, la espera de dependientes, Telegram y la revisión humana corresponden al contrato. La excepción de cierre de suite está expresamente conservada en su punto 4. |
| Trazabilidad | ✅ | Los escenarios se vinculan al bug existente mediante `@B-ADV-0012`. No introducen etiquetas `@CA-*` sin criterio de origen. |
| Delta real | ❌ | El último escenario repite el caso de parada tras tres arreglos fallidos en dificultad máxima ya especificado por B-ADV-0006; véase H-01. |

## Puntuaciones

| Criterio | Nota | Justificación |
| --- | --- | --- |
| Claridad | 8/10 | Se distingue el bloqueo de la tarea de la continuidad del bucle; falta declarar la configuración del umbral de intentos. |
| Completitud | 9/10 | Cubre task-dev y bug-fix, dependencias, tarea independiente, motivo persistido, aviso, fin de elegibles y promoción disponible. |
| Testeabilidad | 8/10 | Hay estados y efectos observables, con dos intentos y una cola de 2000 caracteres; el umbral necesita una precondición explícita. |
| Estructura | 9/10 | Los escenarios amplían el archivo funcional existente del uso de Adevv y su bucle, sin crear un archivo por bug o versión. |

**Media: 8,5/10.** El fallo de una comprobación obligatoria impide aprobar aunque la media supere 8.

## Hallazgos

### H-01 — 🔴 CRÍTICO — Escenario añadido sin delta de comportamiento

**Ubicación:** `tests/features/uso_sin_rutas.feature:175-179`.

**Para:** especificador.

El escenario «El cierre de suite conserva su regla de tres arreglos fallidos» reproduce el caso ya cubierto por el esquema de B-ADV-0006 «Recaídas del mismo cierre reutilizan el bug y suben la dificultad»: su fila `dificil | 2` exige el tercer fallo, el bloqueo y la parada con aviso, ID y última salida. El nuevo escenario no introduce una condición que distinga el comportamiento y ofrece menos detalle que el existente.

Esto incumple la obligación de delta real sin duplicados. Conservar una regla anterior en el contrato del bug es correcto, pero no requiere volver a añadir su escenario aprobado.

**Corrección requerida:** retirar únicamente este escenario nuevo y conservar intacto el esquema previo de B-ADV-0006. Si se pretende especificar una interacción nueva entre el bloqueo local y el cierre de suite, explicitar esa condición diferencial y su resultado observable.

### H-02 — 🟡 MEDIA — Umbral de dos intentos sin configuración declarada

**Ubicación:** `tests/features/uso_sin_rutas.feature:155-157` y `:171-173`.

**Destino:** resolver. **Responsable:** especificador.

El contrato describe el agotamiento de `--reintentos`, mientras los dos escenarios nuevos fijan dos intentos sin declarar el valor configurado. Así no queda inequívoco si dos es una configuración del ejemplo o un umbral fijo que sustituye al configurable.

**Corrección propuesta:** añadir a ambos escenarios la precondición de que el límite de intentos sin progreso está configurado en 2. No hace falta modificar el contrato ni pedir una decisión humana adicional.

## Condición de aprobación

Resolver H-01 y aclarar H-02; reevaluar el delta resultante. No se solicitan cambios de código ni diseño, ni un cambio adicional de alcance.
