**Veredicto:** APROBADO · **9,50/10**

# B-ADV-0044 · Reevaluación independiente de pruebas C1

## Hallazgos anteriores de pruebas

**N9 · resuelto.** En `test_aprobacion_historica_de_b_tras_rechazar_b`, el historial Git comienza con una aprobación de A que contiene el veredicto y su huella, sin explicación. La prueba confirma el cambio de `producto.py`, comprueba que B tiene otra huella y confirma un rechazo con la huella de B. En el siguiente commit aprueba B con el cuerpo propio «El doble es correcto.» y sin línea de huella. Exige que el selector avance a `revisar-version` y que el preflight devuelva `pendientes_cierre(...) == []`.

El nuevo caso falló en el selector, que devolvió `revisar-tarea`. La aserción del preflight se comprobó por lectura porque sigue a ese primer fallo. El valor predeterminado de `rechazar_b` conserva los dos recorridos anteriores con rechazo de A. La aprobación histórica de B sigue dando rojo en ese recorrido y la aprobación con huella explícita pasa las dos aserciones.

H1–H4 y N1–N8 de pruebas siguen **resueltos** en el alcance de sus rondas. El delta solo añade el caso de N9 y adapta su auxiliar.

## Hallazgos nuevos de pruebas

Ninguno.

## Hallazgos de producto reproducidos

| Hallazgo | Estado | Resultado observado y control |
|---|---|---|
| D3 · 🔴 | **persiste** | Al restaurar la aprobación revocada quitando el cerco exterior, el selector adelantó la revisión de versión. La prueba exige revisión del ID. El control de restauración con huella del mismo producto pasó, incluida la liberación posterior por una reevaluación propia. |
| D6 · 🟠 | **persiste** | Los dos historiales con aprobación propia de B sin huella mantienen pendiente la tarea, tanto con rechazo previo de A como con rechazo previo de B. La variante con aprobación explícita de B libera selector y preflight. |
| D8 · 🟠 | **persiste** | La respuesta quedó incorporada durante la espera. Hubo dos llamadas a A en total y se esperaban tres, una antes y dos después de responder. La comprobación posterior que conserva el intento consumido de B se verificó por lectura. |

Los tres corresponden a Artemisa (`desarrollador`), con destino `resolver` en C2. D7 sigue **resuelto** según la revisión de código anterior.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | El nuevo historial reproduce la secuencia que faltaba en D6 y conserva las variantes previas y los controles de D3 y D8. |
| Aserciones | 9/10 | Se distinguen las huellas de A y B y se exige el resultado observable de los dos consumidores del dictamen. |
| Rojo correcto | 10/10 | Los cuatro fallos son de comportamiento. Los dos historiales de D6 alcanzan el selector, D3 detecta un cierre prematuro y D8 detecta el intento perdido. |
| Estabilidad | 9/10 | Cada historial usa su propio repositorio Git temporal. El orden lo fijan los commits y la respuesta de D8 se entrega en una espera simulada. |

**Evidencia.** Árbol `75c275c26dde5c829247867f03f2f3681640bba4`, rama `hotfix/v1.1.3`. El archivo local de pruebas corresponde al blob `2b94974` del delta aportado. Se reutilizó la ejecución dirigida de seis pruebas en 11,357 s, con cuatro fallos de aserción y dos controles verdes, y el resultado verde de Ruff selectivo. El proyecto carece de tipado configurado.
