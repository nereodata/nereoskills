**Veredicto:** APROBADO

# Revisión de especificación — T-ADV-0022

- **Veredicto actual: APROBADO**.
- Fecha: 2026-10-26. Revisor: Hades, mediante `/review-spec`, en modo orquestado.
- Referencia: HEAD `7414be56fdab34520c8902e481a001caf9ff7836`.
- Alcance: nueva especificación `skills/orquestar/features/calidad_delta.feature`, criterios y DEC-ESP-01/02/03/04/05 de la tarea; resolución de H-01/H-02/H-03 y no regresión de `skills/orquestar/features/orquestacion.feature`.
- Método: lectura de especificación, criterios, DEC e informe anterior, y comparación frente a HEAD. Sin leer diseño, código ni tests; sin suite completa ni pruebas funcionales.

## Comprobaciones obligatorias actuales

| Comprobación | Resultado | Motivo |
| --- | --- | --- |
| No regresión | ✅ | El diff de `orquestacion.feature` respecto a HEAD está vacío. La característica nueva se añade en otro archivo y conserva íntegros los escenarios aprobados de reservas. |
| Coherencia | ✅ | Las DEC delimitan base, objetivos, precedencia por etapa, compatibilidad, escritura y evidencia. El comando explícito sin marcador conserva su alcance declarado y avisa; los deducidos se limitan al delta. Se distingue escritura del desarrollador de comprobación sin escritura de Hades. |
| Trazabilidad | ✅ | No hay etiquetas `@CA-*` inexistentes. `@T-ADV-0022` identifica la tarea. Resolución, argumentos, errores y omisiones (líneas 8–97) corresponden a CA-M-1; cierre de ambos flujos (99–137), a CA-M-2; evidencia y revisión de Hades (138–166), a CA-M-3. CA-M-4 sigue siendo obligación posterior de pruebas y documentación, no un resultado validado en este paso. |
| Delta real | ✅ | Añade calidad del delta sin duplicar reservas ni retirar escenarios aprobados. |

## Puntuaciones actuales

| Criterio | Puntuación | Motivo |
| --- | --- | --- |
| Claridad | 9/10 | Contextos separados y desencadenantes, actores y resultados explícitos. |
| Completitud | 9/10 | Resolución explícita y deducida, errores, omisiones, nombres de fichero, cierre en verde y rojo y vigencia de evidencia. |
| Testeabilidad | 9/10 | Comandos y argumentos concretos, códigos cero/uno, bloqueo de completed y reutilización frente a nueva ejecución observables. |
| Estructura | 10/10 | Característica propia nombrada por funcionalidad, sin alterar la de reservas. |
| **Media** | **9,25/10** | Supera 8; sin hallazgos críticos ni altos pendientes. |

## Resolución de los hallazgos anteriores

| Hallazgo | Severidad anterior | para | destino | Estado y evidencia actual |
| --- | --- | --- | --- | --- |
| H-01 | 🟠 ALTA | especificador | resolver | **Resuelto.** Líneas 99–137: el intento de cierre en ambos flujos dispara escritura disponible y comprobaciones; verde permite completed y rojo lo impide. Líneas 156–166: Hades comprueba sin escritura y devuelve el fallo al desarrollador. DEC-ESP-05 fija el contrato. |
| H-02 | 🟠 ALTA | especificador | resolver | **Resuelto.** Líneas 24–97 separan precedencia, deducción npm/ruff, herramientas ausentes, script desconocido, configuración inválida, base inexistente y ausencia de objetivos. Líneas 99–137 distinguen formato corregible, falta de escritura y fallos independientes de formato/lint. Líneas 138–155 distinguen reutilización del mismo árbol y comando de invalidación tras cambio o formateo. |
| H-03 | 🟡 MEDIA | especificador | resolver | **Resuelto.** `calidad_delta.feature:3–6` declara la funcionalidad propia y `orquestacion.feature` permanece sin cambios respecto a HEAD. |

## Hallazgos nuevos

Ninguno pendiente en los artefactos finalmente leídos. Al principio se observó una cabecera literal `Caracter?stica`; durante la revisión los artefactos se actualizaron y una nueva lectura confirmó `Característica` y los acentos restaurados. No se considera defecto vigente. Hades no modificó esos archivos.

## Evidencia y límites

Se consultó `orquestar_evidencias.jsonl`. Sus verdes no se atribuyen automáticamente al árbol revisado: no se pudo confirmar su identidad mediante el mecanismo autorizado. Tampoco se utilizan resultados funcionales de otros árboles como prueba de esta especificación.

Único intento de verificación: `adevv orquestar --verificar "git diff --check"`. Terminó con código 1 antes de ejecutar la comprobación, al fallar `git add -A .` con código 128 durante la preparación del índice temporal. No se acredita un nuevo verde de integridad. Es una limitación de verificación, no un defecto demostrado del contrato. No se inspeccionó ni modificó el mecanismo ni se ejecutaron alternativas o pruebas adicionales.

La aprobación se limita a especificación; no acredita implementación, automatización BDD ni cumplimiento material de CA-M-4. Solo se actualiza este informe, sin modificar escenarios ni tarea y sin commit.

## Histórico conservado — rechazo anterior

Resumen: **RECHAZADO**, media **6,25/10**; H-01/H-02 altos y H-03 medio, todos para `especificador`, destino `resolver`. El texto anterior se conserva a continuación; su veredicto queda sustituido por la reevaluación actual.

- **Veredicto: RECHAZADO**
- Fecha: 2026-10-26.
- Revisor: Hades, mediante `/review-spec`.
- Alcance: únicamente los cuatro escenarios nuevos `@T-ADV-0022` de `skills/orquestar/features/orquestacion.feature:80–112`, contrastados con `docs/plan/tasks/T-ADV-0022-formato-y-lint-en-cada-tarea.md` y su sección Triaje.
- Evidencia: lectura de la especificación y del diff del archivo de escenarios. No se examinaron diseño ni implementación, ni se ejecutaron pruebas. No había un informe anterior de esta tarea en la ruta de destino.

## Comprobaciones obligatorias

| Comprobación | Resultado | Motivo |
| --- | --- | --- |
| No regresión | ✅ | El diff solo añade los cuatro escenarios; conserva los anteriores. |
| Coherencia | ✅ | El comportamiento descrito es compatible con los criterios y el triaje; las carencias de cobertura se detallan abajo. |
| Trazabilidad | ✅ | No se introducen etiquetas `@CA-*` inexistentes. Los escenarios llevan `@T-ADV-0022` y corresponden a detección y resolución (CA-M-1), ejecución (CA-M-2) y revisión (CA-M-3). CA-M-4 requiere pruebas y documentación posteriores, ajenas a esta revisión. |
| Delta real | ✅ | Añade comprobaciones de calidad sobre el delta, sin duplicar los escenarios previos de reservas de arneses. |

## Puntuaciones

| Criterio | Puntuación | Motivo |
| --- | --- | --- |
| Claridad | 6/10 | Se entiende la intención, pero varias ramas y actores comparten una sola ejecución. |
| Completitud | 6/10 | Falta exigir la activación al cierre de cada uno de los dos flujos y concretar la reutilización e invalidación de evidencia. |
| Testeabilidad | 6/10 | Faltan precondiciones diferenciadas para observar precedencia, errores, omisiones y rechazo de calidad de forma independiente. |
| Estructura | 7/10 | Se usa el archivo solicitado, pero su característica está dedicada exclusivamente a la ausencia de arneses. |
| **Media** | **6,25/10** | No supera 8 y existen hallazgos de severidad alta. |

## Hallazgos

### H-01 — 🟠 ALTA: no se especifica la activación obligatoria en ambos flujos de cierre

- **Referencia:** `skills/orquestar/features/orquestacion.feature:98–105`; CA-M-2 y CA-M-3.
- **para:** `especificador`.
- **destino:** `resolver`.
- **Problema:** el desencadenante es «el desarrollador solicita aplicar formato y comprobar calidad». No aparece el cierre de `/task-dev` ni el de `/bug-fix` como desencadenante obligatorio. La frase «impide completed» tampoco sitúa la transición en cada uno de esos flujos. Una comprobación invocada manualmente podría satisfacer el escenario aunque cualquiera de las dos skills cerrase tareas sin ejecutarla. Hades se menciona como otra consecuencia del mismo escenario, sin una revisión de código como acción propia.
- **Corrección requerida:** expresar casos para `/task-dev` y `/bug-fix`, por ejemplo mediante un esquema con ambos flujos. Al intentar cerrar, deben ejecutar formato en escritura cuando esté disponible, comprobar formato y lint sobre el delta, permitir completar tras pasar y bloquear la transición ante un fallo de cualquiera de las etapas. Añadir un caso de revisión de código de Hades que compruebe mediante `--verificar`, sin escritura, y asigne el fallo al desarrollador.

### H-02 — 🟠 ALTA: ramas y resultados sin precondiciones verificables independientes

- **Referencia:** `skills/orquestar/features/orquestacion.feature:88–112`; CA-M-1, CA-M-2 y CA-M-3.
- **para:** `especificador`.
- **destino:** `resolver`.
- **Problema:** «Detección conservadora» parte de scripts npm sin configuración explícita, pero exige después precedencia de un comando explícito, un proyecto que solo contiene ruff, ausencia de herramientas y un script desconocido. No define qué datos cambian ni una nueva resolución para cada caso. «Configuración errónea y delta vacío» mezcla un error de configuración/base con una omisión válida. «Formatear y comprobar» no prepara por separado un formato corregible, un fallo persistente de formato y un fallo de lint. Además, «usa la evidencia del mismo árbol exacto» no distingue reutilizar un resultado válido de rechazar evidencia anterior a un cambio, especialmente tras aplicar escritura.
- **Impacto:** no queda determinado qué ejecución produce cada resultado; es posible cubrir solo una alternativa o aceptar evidencia anterior sin que los escenarios discriminen el defecto.
- **Corrección requerida:** separar los contextos en escenarios o filas de ejemplos con entrada, acción y resultado propios. Concretar comandos esperados para la deducción y precedencia, y distinguir error de configuración, base inexistente y omisión por delta sin ficheros compatibles. Fijar resultados separados para formato corregido, formato aún en rojo y lint en rojo. Para Hades, indicar que evidencia satisfactoria del mismo árbol se reutiliza y que, al cambiar un fichero relevante o aplicar formato, la evidencia anterior deja de acreditar la calidad del árbol resultante.

### H-03 — 🟡 MEDIA: los escenarios de calidad quedan bajo una característica de ausencia de arneses

- **Referencia:** `skills/orquestar/features/orquestacion.feature:3–6` y nuevas líneas 80–112.
- **para:** `especificador`.
- **destino:** `resolver`.
- **Problema:** el título y la narrativa de la característica son «Continuidad con arneses ausentes» y describen reservas de ejecutables. Los nuevos escenarios de calidad no pertenecen a ese comportamiento, aunque compartan el componente orquestador.
- **Corrección requerida:** ubicarlos en una característica de comprobación de calidad del delta, en un archivo nombrado por esa funcionalidad, conservando íntegros los escenarios existentes. Si se mantiene el archivo solicitado, hacer que la estructura y narrativa de características abarquen expresamente esta funcionalidad sin alterar los contratos anteriores. No crear un archivo nombrado por tarea o versión.

## Resolución

Corresponde al especificador corregir los escenarios. La siguiente revisión debe comprobar los tres hallazgos y el delta de su corrección. Este informe no prescribe una implementación ni modifica los artefactos revisados.
