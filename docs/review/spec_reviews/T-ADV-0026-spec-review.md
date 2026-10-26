# Revisión de especificación: T-ADV-0026

- **Revisor:** Hades · **Fecha:** 2026-10-26 · **Modo:** orquestado.
- **Artefacto:** únicamente los cuatro escenarios añadidos con `@T-ADV-0026` en `tests/features/telegram_gateway.feature:227-255`.
- **Referencia:** `docs/plan/tasks/T-ADV-0026-reservas-en-la-conversacion-de-telegram.md`, CA-M-1 a CA-M-6 y triaje de subfase A.
- **Límite:** sin revisión de código, diseño ni pruebas automatizadas; sin ejecutar suite ni crear commits. Los contratos aprobados de B-ADV-0005 y T-ADV-0021 se consultan solo como contexto. La herencia y el ejecutable ausente ya cubiertos por B-ADV-0005 no se vuelven a auditar ni se pide reimplementar el motor.

## Veredicto: RECHAZADO

Media **7,75/10**, con un hallazgo de severidad alta. Debe concretarse la conservación de sesiones al conmutar y regresar al titular antes de aprobar la especificación.

## Obligatorias

- ✅ **No regresión:** el diff del feature solo añade los cuatro escenarios; no elimina ni modifica escenarios existentes.
- ✅ **Coherencia:** la conmutación por cuota o fallo de arranque y el tratamiento separado de errores ordinarios son compatibles con la tarea y B-ADV-0005. No lanzar el único modelo agotado es una exigencia expresa de CA-M-2 de esta tarea; no modifica el contrato del motor de T-ADV-0021.
- ✅ **Trazabilidad:** todas las etiquetas `@CA-M-*` añadidas existen en la tarea y corresponden al comportamiento declarado. CA-M-6 se materializa en las subfases de pruebas y documentación; no exige aquí un escenario que compruebe la existencia de archivos.
- ✅ **Delta real:** se especifican conmutación por cuota en conversación, salto y retorno, diagnóstico combinado y frontera con errores ordinarios. Las referencias a herencia y ausencia se entienden como contexto de contratos previos, conforme al triaje, sin reabrir su aprobación.

## Puntuaciones

| Criterio | Nota | Motivo |
|---|---:|---|
| Claridad | 8 | Los recorridos se entienden; algunos resultados introducen condiciones alternativas sin prepararlas. |
| Completitud | 7 | Falta una comprobación discriminante de conservación y separación de sesiones por usuario y arnés. |
| Testeabilidad | 7 | Horas y modelos concretos, pero sesiones sin identificadores previos y registro de cuota sin recuperación esperada concreta. |
| Estructura | 9 | Escenarios en el feature funcional del gateway y etiquetados por tarea y criterio. |
| **Media** | **7,75** | |

## Hallazgos

### H-01 · 🟠 ALTA · El retorno no demuestra que se conservan las sesiones por usuario y arnés

- **Referencia:** `tests/features/telegram_gateway.feature:235-242`; CA-M-3.
- **Evidencia:** el escenario prepara solo un agotamiento y una reserva disponible. Después exige guardar la sesión de agy «por usuario» y volver a codex «con su propia sesión», sin haber establecido ninguna sesión previa ni sus identificadores. Tampoco comprueba que un mensaje posterior a agy reanude la sesión que este arnés guardó.
- **Impacto:** no queda definido qué sesión concreta debe reanudarse al regresar. El escenario no discrimina de forma fiable una conservación por usuario y arnés frente a perder la sesión anterior al sobrescribir una única sesión del usuario. Es una parte central del comportamiento exigido al introducir reservas.
- **Para:** `especificador`.
- **Destino:** `resolver`.
- **Corrección necesaria:** preparar para el mismo usuario sesiones distintas, por ejemplo `codex-s1` y `agy-s1`; exigir que la reserva reanude únicamente `agy-s1`, que su nuevo identificador se conserve sin reemplazar `codex-s1`, y que al vencer la cuota codex reanude exactamente `codex-s1`. Concretar también que otro usuario no recibe esas sesiones. Puede hacerse mediante un esquema o escenarios breves, sin imponer almacenamiento interno.

### H-02 · 🟡 MEDIA · El agotamiento compartido carece de un resultado temporal verificable

- **Referencia:** `tests/features/telegram_gateway.feature:228-232`; CA-M-5.
- **Evidencia:** se provoca cuota durante 1800 segundos, pero el resultado solo exige un registro «consultable por el bucle y /agentes». El escenario posterior parte de un agotamiento ya preparado, sin vincularlo al generado por la conversación.
- **Impacto:** la especificación no discrimina claramente un registro visible con recuperación incorrecta de uno que permite al bucle saltar el modelo durante los 1800 segundos detectados.
- **Para:** `especificador`.
- **Destino:** `resolver`.
- **Corrección necesaria:** fijar la hora del fallo y exigir que el agotamiento compartido identifique codex/m1 y su recuperación exacta, por ejemplo fallo a las 12:00 y recuperación a las 12:30; concretar que /agentes refleja esa vigencia y que la consulta del bucle la reconoce. No requiere nombres internos de campos ni pruebas del motor heredado.

### H-03 · 🟡 MEDIA · El caso de un único modelo agotado aparece como resultado de otra configuración

- **Referencia:** `tests/features/telegram_gateway.feature:245-249`; CA-M-2 y CA-M-4.
- **Evidencia:** el `Dado` configura tres candidatos, mientras que el último resultado añade «aunque sea el único configurado». No hay una ejecución preparada con un único candidato ni una hora que establezca la vigencia de ese agotamiento.
- **Impacto:** ese límite nuevo puede quedar como una afirmación sin ejercicio propio; es especialmente relevante porque T-ADV-0021 conserva el titular cuando no hay reservas, mientras esta tarea exige saltarlo si su cuota sigue vigente.
- **Para:** `especificador`.
- **Destino:** `resolver`.
- **Corrección necesaria:** separar o parametrizar el caso de un único modelo con cuota vigente y sin reservas; exigir cero lanzamientos y un diagnóstico que identifique el modelo y la cuota. Mantener aparte el diagnóstico de las tres configuraciones indisponibles.

No se requieren recursos externos ni intervención humana. La corrección corresponde a la especificación de la subfase A; este informe no modifica los escenarios.
