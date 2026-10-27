# Revisión de pruebas — B-ADV-0012

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Modo orquestado. Segunda ronda (reevaluación).

## Alcance

Reevaluación de la clase `BloqueoSinProgresoTests` de `tests/test_orquestar.py`, incluidos sus datos y preparación, frente a los dos escenarios `@B-ADV-0012` de `tests/features/uso_sin_rutas.feature` y al informe de la primera ronda. Aplicados Hades y `/review-test` de la instalación 0.6.1, ignorando el modelo. Sin lectura de producción ni diseño y sin revisión de otras clases de pruebas. La corrección no toca nada fuera de lo señalado, así que no se amplía el alcance.

## Puntuaciones

| Criterio | Nota | Justificación |
| --- | --- | --- |
| Cobertura | 9/10 | Tres subcasos cubren task-dev y bug-fix en dificil y la promoción desde media con `reintentos=2`. Comprueban continuidad de la independiente, espera de la dependiente, persistencia, motivo completo en la revisión humana, aviso y bloqueo final de versión. |
| Aserciones | 8/10 | La cola esperada son ahora exactamente los últimos 2000 caracteres de la salida y se exige en tarea, revisión y aviso, junto con el descarte del prefijo. La revisión exige intentos y dificultad. Queda una comprobación de dificultad en la tarea que se cumple por construcción (H-T03). |
| Rojo correcto | 9/10 | Rojo repetido sobre el árbol corregido: tres subtests fallan por in_progress != blocked, coherente con el defecto original y no con imports, sintaxis o preparación. |
| Estabilidad | 9/10 | Git y backlog temporales; arnés, gateway, avisos y recarga aislados. Pasos e intentos acotados, sin esperas configuradas ni servicios externos reales. |

**Media: 8,75/10.** Sin hallazgos 🔴 ni 🟠 abiertos.

## Hallazgos anteriores

### H-T01 — 🟠 ALTA — La cola esperada excede el límite contractual — **resuelto**

`cola = 'Z' * 1989 + 'FIN RECHAZO'` mide 2000 caracteres y la salida es `'DESCARTAR' * 500 + cola`, de modo que sus últimos 2000 caracteres son exactamente la cola. Las tres comprobaciones (tarea, revisión y aviso) usan esa expectativa y se mantiene `assertNotIn('DESCARTAR', texto)`, que discrimina una cola más larga que 2000. No se amplió el límite del producto.

### H-T02 — 🟡 MEDIA — El motivo de la revisión humana se comprueba parcialmente — **resuelto**

La revisión exige ahora `Contenido previo.`, el ID, la cola, `2 intentos` y `dificil`. Ninguno de los dos nuevos fragmentos está en el contenido inicial de la revisión, así que solo se cumplen si el bucle escribe el motivo completo.

## Hallazgos nuevos

### H-T03 — 🔵 BAJA — La dificultad del motivo en la tarea se cumple por construcción

- **Responsable:** desarrollador. **Destino:** resolver.
- **Ubicación:** `tests/test_orquestar.py`, bucle `for fragmento in ('Trabajo previo.', '2 intentos', 'dificil', cola)` sobre el texto completo de la tarea.
- **Evidencia:** el fichero de la tarea lleva `dificultad: dificil` en el frontmatter desde la preparación (subcasos dificil) o tras la promoción (subcaso media), y la aserción busca en todo el fichero.
- **Impacto:** un motivo de bloqueo en la tarea que omita la dificultad pasaría. El riesgo es bajo porque la revisión humana ya exige `dificil` de forma no trivial.
- **Corrección sugerida:** buscar los fragmentos del motivo solo en el cuerpo, tras el frontmatter (por ejemplo, `texto.split('---', 2)[2]`).

## Evidencia reutilizada y límites

`orquestar_evidencias.jsonl` registra para la huella `e50a43c9a2a1b6dfbf4c7cea7e90d355adffa9f8`:

| Fecha y hora registradas | Comando | Código |
| --- | --- | --- |
| 2026-10-27T08:55:16 | python -m unittest tests.test_orquestar.BloqueoSinProgresoTests | 1 |
| 2026-10-27T08:55:17 | python -m py_compile tests/test_orquestar.py | 0 |
| 2026-10-27T08:55:19 | git diff --check | 0 |

El JSONL conserva comando, huella y resultado, no el traceback. El detalle de los tres subtests que fallan por in_progress != blocked procede de la evidencia entregada por el invocador y es coherente con la primera aserción de estado de la clase. No hay lint ni tipado configurados.

Se reutiliza esa evidencia sin relanzar comandos de verificación ni la suite completa. Solo se modifica este informe en el árbol de trabajo; sin cambios en pruebas, producción, estados, copia instalada ni commits.
