# B-ADV-0037 — Revisión de especificación

- **Revisor:** Hades.
- **Fecha:** 2026-11-11.
- **Modo:** orquestado, revisión estática del delta.
- **Veredicto: RECHAZADO.**
- **Responsable de corrección:** especificador (Artemisa).

## Alcance y evidencia

Se revisan exclusivamente los tres escenarios añadidos con `@B-ADV-0037` en `tests/features/publicacion.feature`, frente a los criterios y al triaje operativo de `docs/plan/bugs/B-ADV-0037-cierre-con-revisiones-hades-pendientes.md`.

La revisión utiliza los materiales completos aportados en la solicitud. El acceso local falla con `registered Core launch requires an installed app`; no se acredita una comparación independiente con el árbol o la base Git. No se revisan producción, diseño, implementación de pruebas ni escenarios anteriores. No se ejecutan pruebas ni commits.

CA3 se considera acreditado por los informes formales RECHAZADO de B-ADV-0032 y B-ADV-0033, trazados y con correcciones enrutadas a Artemisa en esos IDs. No se exige aprobación ficticia, repetir sus revisiones ni trasladar sus correcciones a B-ADV-0037. La identidad operativa completa de versión se distingue de la agrupación histórica de métricas, que se conserva.

## Obligatorias

| Regla | Resultado | Motivo |
|---|---|---|
| No regresión | ✅ | El delta suministrado es aditivo; no modifica los cinco escenarios anteriores. Evaluación limitada al material aportado. |
| Coherencia | ✅ | Bloquear ante revisión ausente o rechazada es coherente con el cierre sujeto a revisión. Aislar parches y equiparar v1.1 con v1.1.0 respeta la decisión operativa documentada y no exige cambiar métricas. |
| Trazabilidad | ✅ | Los escenarios se vinculan al bug mediante `@B-ADV-0037`. No añaden etiquetas `@CA-*` inexistentes. Cubren parcialmente CA1, CA2, CA4 y CA5; CA3 queda acreditado por el saneamiento declarado. |
| Delta real | ✅ | Introducen bloqueo por revisión formal, recuperación y aislamiento operativo de parches, comportamientos no descritos por los escenarios anteriores suministrados. |

## Puntuaciones

| Dimensión | Puntuación | Motivo |
|---|---:|---|
| Claridad | 7/10 | Las alternativas del primer escenario y la condición N/A no identifican casos concretos. |
| Completitud | 6/10 | Falta describir la generación del estado pendiente por indisponibilidad y concretar las variantes de bloqueo. |
| Testeabilidad | 7/10 | Hay resultados observables, pero varias alternativas pueden quedar sin ejercitar manteniendo los escenarios satisfechos. |
| Estructura | 9/10 | Los escenarios están en el feature funcional de publicación y mantienen el lenguaje de comportamiento. |
| **Media** | **7,25/10** | No supera 8 y existen hallazgos de severidad alta. |

## Hallazgos

### H1 — 🟠 ALTA: el bloqueo agrupa alternativas sin concretar su cobertura

- **Ubicación:** «Cierre bloqueado por revisión formal ausente o rechazada».
- **Criterios afectados:** CA1 y CA5.
- **Evidencia:** el título menciona ausencia y rechazo, pero el único estado inicial es «sin informe formal aprobado». La acción también agrupa «validar, cerrar o publicar» y solo se utiliza un bug.
- **Problema:** el escenario no determina qué estado de informe ni qué acción se ejercita. Puede satisfacerse cubriendo únicamente un bug sin informe al validar, dejando sin especificación discriminante el informe RECHAZADO, las tareas completadas o el intento directo de cierre/publicación. La obligatoriedad de comprobar cada tarea o bug queda incompleta.
- **Para:** `especificador` (Artemisa).
- **Corrección requerida:** separar los casos o utilizar ejemplos explícitos para ausencia y RECHAZADO, tareas y bugs completados y los puntos de entrada aplicables. Incluir una versión con varios IDs completados para exigir que se identifiquen todos los que carecen de revisión válida. Mantener como resultados observables el bloqueo, la identificación de pendientes y la ausencia de cierre declarado, etiqueta y publicación.

### H2 — 🟠 ALTA: se presupone el estado pendiente sin especificar cómo se produce

- **Ubicación:** «Recuperación tras indisponibilidad de Hades».
- **Criterios afectados:** CA2 y CA5.
- **Evidencia:** el `Dado` parte de una revisión que ya quedó pendiente por falta de Hades; el `Cuando` solo describe su recuperación y aprobación.
- **Problema:** no hay un caso que haga indisponible a Hades e intente obtener la revisión o continuar el cierre. Por ello no se exige observar que esa indisponibilidad deja un estado pendiente con ID, motivo concreto y vía de reanudación, sin sustituirlo por la suite verde. El primer escenario exige un motivo genérico de revisión pendiente, pero tampoco provoca la indisponibilidad.
- **Para:** `especificador` (Artemisa).
- **Corrección requerida:** añadir un caso con Hades indisponible y pruebas verdes que desencadene el flujo y compruebe el estado pendiente, ID, motivo de indisponibilidad, instrucción de reanudación y bloqueo del cierre. Conservar el caso de recuperación y hacer explícita la revalidación tras recibir el informe APROBADO.

### H3 — 🟡 MEDIA: la excepción N/A queda como condición sin ejercicio propio

- **Ubicación:** última cláusula de «Recuperación tras indisponibilidad de Hades».
- **Evidencia:** después de recibir un informe APROBADO se afirma que «un informe N/A solo permite continuar si declara por qué no hay código que revisar».
- **Problema:** el informe N/A no forma parte de los antecedentes ni de la acción. Esa cláusula no exige ejercitar un N/A válido ni uno sin justificación.
- **Para:** `especificador` (Artemisa).
- **Destino:** `resolver`.
- **Corrección requerida:** expresar la excepción en casos propios con informe N/A justificado y sin justificación, indicando respectivamente si la revisión deja de bloquear o permanece pendiente.

## Resolución

Devolver el delta al especificador (Artemisa) para resolver H1, H2 y H3. Reevaluar los escenarios corregidos y su delta. Este veredicto se limita a la especificación de B-ADV-0037 y no cambia los veredictos ni los responsables de B-ADV-0032 y B-ADV-0033.
