# Revisión de pruebas T-ADV-0039

**Veredicto: APROBADO**

Alcance: únicamente `tests/test_llamadas.py` y los escenarios `@T-ADV-0039` de `tests/features/uso_sin_rutas.feature`. No se ha examinado código de producción ni los fixtures importados. Revisión estática de la versión final ampliada. El invocante acredita el rojo previo de Afinn (`len(self.llamadas): 1 != 2`), pertinente al bloqueo persistente. Evidencia final recibida del invocante: `tests.test_llamadas.LlamadasTests`, 11 pruebas OK en 21,245 s; sintaxis AST y `git diff --check` correctos. Formato y lint omitidos explícitamente por falta de herramientas; no se acredita tipado estático.

| Criterio | Puntuación | Motivo |
| --- | ---: | --- |
| Cobertura | 8/10 | Afinn, aislamiento básico, historial entre procesos, retoma de las tres entradas, aclaración y perfil estricto cubren los riesgos principales. |
| Aserciones | 9/10 | Comprueban estados, fuentes, encargo, preservación de ficha, perfiles, persistencia de invocación y consumo no duplicado. |
| Rojo correcto | 8/10 | El rojo acreditado reproduce el bloqueo de Afinn; las nuevas aserciones son discriminantes por comportamiento, aunque no se ha recibido su rojo individual. |
| Estabilidad | 9/10 | Proveedores simulados, directorios temporales y recuperación explícita; las pruebas no esperan al reloj real. |

**Media: 8,5/10. Sin hallazgos críticos ni altos pendientes.**

## Rectificación y cambios revisados

Se retira el hallazgo inicial sobre `configuraciones_con_cuota`: la aserción negativa acredita que el perfil agotado no está disponible. No demuestra borrado de cuota ni contradice el escenario. La interpretación inicial del revisor era incorrecta.

Afinn enruta mediante `enrutar_hallazgo` y comprueba estado planned y encargo. El historial se lee desde otro proceso. El paso principal agota ambos perfiles y vuelve a ejecutar tras recuperación conservando la ficha. La contradicción atraviesa cuota y concordancia sin perder las fuentes originales. Un rol estricto no ejecuta su reserva.

La matriz ejercita rol y diagnóstico, incluyendo cuota seguida de recuperación y entrega válida. El diagnóstico recoge la salida emitida durante la ejecución del doble del proveedor. El rol comprueba que la espera desaparece y que la invocación original sigue persistida. Cada intento devuelve siete tokens y el total registrado debe ser siete por llamada efectiva: la aserción detecta pérdida o duplicación del consumo incluso cuando existen registros de resumen sin coste propio. Estas ampliaciones resuelven los hallazgos altos de las revisiones anteriores.

## Hallazgos no bloqueantes

### 🟡 MEDIA — Precisar correlación y aislamiento negativo

La matriz comprueba que el padre existe, pero no su relación exacta con el padre esperado. El aislamiento contrasta spec/test para una sola tarea y entradas idénticas. Conviene añadir casos de otra tarea y otras entradas y comprobar el padre concreto para detectar correlaciones excesivamente amplias.

### 🟡 MEDIA — Reforzar el cierre de espera de diagnóstico y la lectura histórica

Tras recuperar diagnóstico se comprueba un dictamen válido, mientras que la eliminación de la espera original solo se comprueba explícitamente en el rol. Una aserción equivalente sobre el historial de diagnóstico reforzaría ese cierre. La prueba de canal junto con legado verifica la indicación explícita de correlación desconocida. Falta un coste histórico no nulo en la prueba de identidad incompleta; la matriz sí cubre consumo no nulo de intentos nuevos.


## Evidencia adicional revisada

Las nuevas regresiones comprueban que una espera antigua registrada tarde no revoca una ratificación más reciente, que un canal vigente no oculta una llamada de legado pendiente y que un fallo de Hades conserva la revisión pendiente aunque el padre termine con código cero. El paso principal también afirma el consumo total esperado tras sus tres intentos. No aparecen nuevos hallazgos altos; se mantiene APROBADO.
