# Reevaluación de pruebas — B-ADV-0037

**Veredicto: APROBADO**

**Destino canónico:** `docs/review/test_reviews/B-ADV-0037-test-review.md`

Revisión Hades `/review-test` limitada al delta de pruebas aportado desde `4a3c3dc`, relativo a RC-01 y RC-02. Se conserva la aprobación previa del resto de las pruebas. Esta aprobación no resuelve los hallazgos de producción.

## Evidencia y alcance

Se revisaron los dos tests añadidos en `tests/test_orquestar.py`, incluidos sus estados, dobles y aserciones visibles en el diff.

Se acepta la evidencia aportada de `adevv orquestar --verificar`: dos tests, dos fallos y un error esperado:

- Checkout de `release/v1.1.2` inexistente: reproduce la causa exacta de RC-01.
- Selección de la rama release cuando existen ambas ramas: reproduce la segunda manifestación de RC-01.
- Ausencia de llamada al resumen para `v1.1.2`: reproduce RC-02.

Según la evidencia aportada, no existen errores de fixtures, imports ni sintaxis. No hay lint ni tipado configurados. No se ejecutó la suite completa ni se repitió la verificación.

El acceso local falló antes de poder contrastar el árbol, leer los archivos instalados o guardar este informe. La evaluación se basa en el perfil, la skill, el informe de código, el diff y la evidencia incluidos en la solicitud.

## Puntuaciones

| Dimensión | Nota | Motivo |
|---|---:|---|
| Cobertura | 9/10 | Cubre las dos manifestaciones de RC-01 y la versión con parche de RC-02, conservando el caso histórico sin parche. |
| Aserciones | 10/10 | Comprueba la rama realmente observada durante la verificación, el estado final, la parada y el contenido enviado. |
| Rojo correcto | 9/10 | La evidencia aportada corresponde a los defectos concretos; el error de checkout forma parte de la regresión buscada. |
| Estabilidad | 9/10 | Usa estados Git locales explícitos y dobles para verificación y avisos, sin depender de red ni tiempo real. |

**Media: 9,25/10. Sin hallazgos 🔴 ni 🟠.**

## Reevaluación de la cobertura solicitada

### RC-01 — Resuelto en las pruebas

`test_hotfix_final_stop_checks_selected_branch` prepara una hotfix con parche y revisión de arquitectura presente, y comprueba que el selector alcanza el cierre `PARAR`.

Sus dos subcasos discriminan entre:

- Ausencia de `release/v1.1.2`, que descubre la reconstrucción incorrecta mediante el error de checkout.
- Existencia simultánea de release y hotfix, que exige verificar específicamente `hotfix/v1.1.2`.

La rama se observa dentro del doble de `verificar`, por lo que la aserción comprueba dónde se realiza la validación. También se exige conservar esa rama al terminar, no ejecutar pasos adicionales y emitir el aviso de cierre correspondiente.

### RC-02 — Resuelto en las pruebas

`test_version_summary_preserves_optional_patch` exige que `resumen` reciba la versión completa y que su resultado aparezca en los mensajes enviados.

El caso `v1.1.2` detecta la pérdida del parche. El caso `v0.1` conserva el comportamiento histórico. El doble se crea de nuevo para cada subcaso, evitando acumulación de llamadas.

## Hallazgos nuevos

Ninguno.

## Resolución

**APROBADO el delta de pruebas relativo a RC-01 y RC-02.** Se mantiene la aprobación previa del resto.

No se modificaron producción, pruebas ni backlog. El informe queda entregado íntegramente en esta salida por el fallo de acceso local.
