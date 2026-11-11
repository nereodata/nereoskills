**Veredicto:** APROBADO · **9,00/10**

# B-ADV-0044 · Reevaluación independiente de pruebas (C1)

Árbol acreditado `74fc0f7591274353c86a8cf59020aed328f864a9`. Ronda anterior `68247f62b598e7f1ec3fd6c5e63eaed4208fff89`. Los cuatro hallazgos anteriores quedan resueltos.

## Hallazgos anteriores

| Hallazgo | Estado | Evidencia en las pruebas corregidas |
|---|---|---|
| H1 🟠 · Perfiles de Hades | **resuelto** | `revisar` invoca `motor.agente` y captura el arnés y el modelo que recibe el lanzador simulado. Los tres casos con perfil estricto exigen exactamente dos lanzamientos de `claude/critico`. En la alternancia, la prueba exige `claude/primario` antes de la recarga y, después, `claude/primario` seguido de la reserva declarada `codex/autorizado`. Un perfil ajeno o un intento adicional de A incumpliría las secuencias esperadas. |
| H2 🟠 · Espera por cuota | **resuelto** | La prueba permite esperar dos horas ante una cuota que se restablece en una. Exige una llamada a `esperar` con la raíz y la demora registrada para la reserva agotada, de al menos 3600 segundos. El doble devuelve una parada cooperativa. La variante con dictamen exige cero esperas. Ambas comprueban los consumos 7 y 9 de la misma invocación y el consumo 11 del paso. |
| H3 🟡 · Reformulación del impedimento | **resuelto** | En la ficha y en el resumen de versión, los intentos del 10 y el 11 de noviembre describen con palabras distintas la misma falta de acceso. Cada intento confirma las notas, comprueba que el árbol queda limpio y devuelve código 0. La prueba exige la parada tras el segundo commit. |
| H4 🟡 · Informe del ID correcto | **resuelto** | `repeticion` construye la ruta canónica con el `iid` del caso. Una aprobación espuria escrita para `T-DEMO-0001` haría fallar la fila de `task-dev`. |

## Hallazgos nuevos

Ninguno.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 9/10 | Los seis escenarios tienen casos que ejercen el bucle. Cubren los diagnósticos repetidos, `work-plan`, los cinco tipos de avance de una ficha antigua, la alternancia con recarga y arranque manual, la vigencia de la aprobación y las dos salidas de la reserva. |
| Aserciones | 9/10 | Las pruebas observan lanzamientos, esperas, métricas y artefactos del ID. Con el mismo cambio de producto, estado `completed` y retorno 1, una aprobación anterior exige reintentar el bug y una vigente permite pasar a revisar la versión. |
| Rojo correcto | 9/10 | La ejecución dirigida aportada registró 84 pruebas y 12 fallos de aserción, sin errores de carga ni preparación. Los tres casos de diagnóstico recibieron cinco llamadas donde se esperaban dos. La aprobación antigua permitió pasar prematuramente a revisar la versión. En los cuatro controles de entregable, el avance se registró y el fallo fue un intento posterior de más. |
| Estabilidad | 9/10 | Cada prueba crea un repositorio temporal, fija la identidad Git, aísla la configuración global y de sistema y limpia las variables heredadas de Git y del orquestador. Las fechas del diagnóstico son fijas. Los lanzamientos de proveedores y las esperas están simulados. |

## Evidencia y límites

El dictamen se basa en el perfil de Hades, la skill `/review-test`, los escenarios, los deltas de pruebas y la evidencia adjuntos. Se reutilizaron el rojo dirigido y el `git diff --check` en verde del árbol indicado, sin repetir verificaciones. La evidencia declara que se omitieron formato y lint por falta de herramientas y que el proyecto carece de comprobador de tipos configurado.

En los casos de repetición y alternancia, el rojo se detuvo en el recuento de llamadas antes de alcanzar las aserciones posteriores sobre perfiles. Esas aserciones se evaluaron por lectura. Las dos variantes de reserva pasaron en la ejecución aportada. La aprobación corresponde a las pruebas de C1. La implementación de C2 queda fuera del dictamen.

La lectura local mediante PowerShell y Node falló con `registered Core launch requires an installed app`. También falló la escritura del informe. Queda pendiente transcribir este dictamen íntegro en `docs/review/test_reviews/B-ADV-0044-test-review.md`.
