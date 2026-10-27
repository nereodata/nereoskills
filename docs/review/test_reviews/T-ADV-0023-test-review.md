# Revisión de pruebas — T-ADV-0023

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Skill aplicada: `/review-test` de Adevv 0.6.0. Segunda revisión.

## Alcance y evidencia

Reevaluación de los hallazgos de la primera revisión, que rechazó la versión del árbol `b814a0b23e`, frente al delta de `skills/telegram_gateway/test_cierre_version.py` en el árbol `db89977871`. Se contrasta con los escenarios `@T-ADV-0023` aprobados, que no se revisan de nuevo. El delta se limita a la prueba de cierre correcto y a la tabla de rechazos, así que no ha hecho falta ampliar la revisión al resto del archivo. No se ha inspeccionado el código de producción.

La evidencia de `orquestar_evidencias.jsonl` sobre `db89977871` está completa: compilación en verde y `python -m unittest skills.telegram_gateway.test_cierre_version` en rojo (código 1). No se han repetido. La producción del cierre aún no existe y `conversar` está simulado, así que el rojo sigue debiéndose a la funcionalidad ausente. Los módulos usan solo la biblioteca estándar y no tienen linter ni tipado configurados.

## Puntuaciones

| Criterio | Nota | Evaluación |
| --- | ---: | --- |
| Cobertura | 9/10 | Las cuatro combinaciones del esquema de cierre (completed/cancelled × continuación/FIN) son pruebas independientes con una fixture limpia. Las 18 filas de rechazo, los tres fallos de publicación, el relanzamiento fallido y el resumen con el aviso siguen cubiertos. Queda la inversión de datos de H-05, que se descartó. |
| Aserciones | 9/10 | `assert_publication` compara el remoto por referencia exacta: `refs/heads/main` y el objeto pelado de `refs/tags/v1.0.0` deben ser el merge, y `refs/tags/v1.0.0` debe ser el mismo objeto de etiqueta anotada que el local. Si falta la etiqueta remota, la prueba falla (`KeyError`). Los motivos planned, in_progress y bloqueo son explícitos. |
| Rojo correcto | 9/10 | La respuesta simulada no contiene ninguno de los fragmentos esperados y las API que se usan existen. `test_unauthorized_is_silent` sigue pasando en rojo como control de regresión. |
| Estabilidad | 8/10 | No ha cambiado: Git real y temporal, sin configuración global ni del sistema, remoto bare local y restauración en `finally`. Cada ejemplo de cierre parte de su propio `setUp`. |

**Media: 8,75/10.** Supera 8 y no quedan hallazgos críticos ni altos.

## Reevaluación de hallazgos anteriores

### H-01 — 🟠 ALTA — Resuelto

La aserción con `assertIn` sobre la salida conjunta de `ls-remote` se sustituye por un diccionario de referencias remotas con tres igualdades separadas: `refs/heads/main`, `refs/tags/v1.0.0^{}` y `refs/tags/v1.0.0`. Si `main` se publica sin la etiqueta, la prueba ya no pasa.

### H-02 — 🟠 ALTA — Resuelto

`test_finish_without_process` se sustituye por `test_completed_and_finish` y `test_cancelled_and_finish`. Ambas usan `assert_publication` y exigen merge, etiqueta anotada local y remota, borrado de `release/v1.0`, árbol limpio en `main`, `FIN` y que no se lance nada.

### H-03 — 🟡 MEDIA — Resuelto

Los cuatro ejemplos del esquema son pruebas propias. La continuación exige `segundo plano` y una única llamada a `en_fondo(root, argumentos=[])`.

### H-04 — 🟡 MEDIA — Resuelto

Los fragmentos son ahora `planned`, `in_progress` y `bloqueo`, cada uno distinto del identificador de la tarea.

### H-05 — 🔵 BAJA — Descartado

Se mantiene el destino de la primera revisión.

### H-06 — 🔵 BAJA — Resuelto en lo que se marcó `resolver`

La asignación muerta de `release` ha desaparecido. La sensibilidad de los fragmentos a la redacción sigue descartada.

## Hallazgos nuevos

### H-07 — 🔵 BAJA — Carácter corrupto en un docstring

El docstring de `assert_publication` (línea 103) contiene un `?` literal en lugar de `Í` («Comprueba ?ntegro…»), probablemente por un problema de codificación al editar. No afecta a la ejecución.

- **Destino:** resolver (desarrollador). Hay que sustituirlo por «Comprueba íntegro cada ejemplo…».

## Destinatarios

- **Desarrollador (Artemisa):** H-07, que se corrige ahora en el hilo principal. Después puede pasarse a la implementación (C2).
- **Especificador / humano:** nada.
