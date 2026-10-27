# Revisión de pruebas — B-ADV-0013

**Veredicto: APROBADO. Media: 9/10.** Sin hallazgos pendientes.

Fecha: 2026-10-27. Revisor: Hades. Modo orquestado. Agente y skill `/review-test` de la instalación 0.6.1; modelo del frontmatter ignorado. Tercera ronda: se mantiene la aprobación de las pruebas, incluida la regresión añadida tras C-01 de código.

## Alcance

Revisión aislada por lectura de todo el delta respecto a HEAD de `tests/test_orquestar.py` y `skills/orquestar/test_recarga.py`, incluidos los fixtures usados, la clase `RecuperacionAnalisisTests` completa y el cambio de paso en `EscaladaTests.test_loop_launches_the_escalated_model_with_its_flag`. Contraste con el contrato aprobado de `docs/plan/bugs/B-ADV-0013-pasos-de-analisis-sin-escalada.md` y los escenarios `@B-ADV-0013` de `tests/features/uso_sin_rutas.feature`, sin cambios de contrato. Se comprueba la conservación de H-01 a H-04 y el nuevo caso solicitado por C-01, sin revisar producción. Del diseño solo se consulta la declaración del impacto en la prueba antigua, sin auditar su solución.

## Puntuaciones

| Criterio | Nota | Motivo |
| --- | --- | --- |
| Cobertura | 9/10 | Los siete pasos tienen éxito por escalada y reserva y agotamiento local/global. Incluye argumentos vacíos, deduplicación, herencia, alternativas ausentes, aislamiento, progreso, recarga y rechazos previos sin adelantar escalada. |
| Aserciones | 9/10 | Secuencias exactas, sesiones, continuación y reinicio, persistencia y diagnósticos; la regresión distingue reservas del inicial y de escalada y comprueba el indicador del entorno. |
| Rojo correcto | 9/10 | La regresión nueva falla por una secuencia de perfiles incorrecta, según la evidencia entregada; no por sintaxis, imports o preparación. El resto dispone de verde anterior identificado como tal. |
| Estabilidad | 9/10 | Git temporal, perfiles ficticios, selector y firma controlados, arneses y avisos simulados, gateway aislado; sin dependencia de proveedores ni esperas reales en las pruebas nuevas. |

**Media: 9/10 (> 8), sin hallazgos críticos ni altos.**

## Reevaluación de hallazgos

### H-01 — ALTA — Resuelto

**Para:** desarrollador. **Destino:** resolver. **Estado vigente:** resuelto, sin acción pendiente.

En `simular`, la selección de `start-version` depende ahora del progreso producido por el arnés. El caso de éxito comprueba que ese paso se ejecuta y que después reaparece el par original con perfil base. La secuencia exacta diferencia el éxito en escalada y en reserva y no permite continuar en el perfil agotado o probar posteriores antes del siguiente paso. Se elimina la aserción sobre el estado `completed` heredado del fixture. Ya no basta con consumir una lista que termina justo en la ejecución ganadora.

### H-02 — ALTA — Resuelto

**Para:** desarrollador. **Destino:** resolver. **Estado vigente:** resuelto, sin acción pendiente.

Éxito y agotamiento pasan `None` para `work-plan` y `calcular-dependencias`; los otros globales conservan `v0.1`. Se observa también el argumento vacío normalizado al reaparecer el par y su identificación en el diagnóstico global. Quedan ejercitados los dos casos sin argumento del contrato.

### H-03 — MEDIA — Resuelto

**Para:** desarrollador. **Destino:** resolver. **Estado vigente:** resuelto, sin acción pendiente.

`comprobar_diagnostico` exige el orden de los cuatro perfiles y busca «2 intentos» en el segmento de cada uno, delimitado por el siguiente perfil. Se aplica al diagnóstico global y a tarea, revisión de versión y avisos locales capturados. Paso y argumento siguen comprobándose. Una mención genérica anterior a todos los perfiles ya no satisface la comprobación.

### H-04 — MEDIA — Resuelto

**Para:** desarrollador. **Destino:** resolver. **Estado vigente:** resuelto, sin acción pendiente.

`test_transfiere_argumentos_raiz_estado_y_pid` transporta dos recuperaciones no vacías, con índices distintos y contadores parciales. Comprueba igualdad del estado serializado en `ADEVV_RECARGA` y del recibido por `recibir_recarga`, usando el transporte real con lanzamiento de proceso simulado. Complementa el caso del bucle que captura dos pares, reentra con el estado transferido y exige continuar los intentos parciales sin reiniciar perfiles agotados.

## Resto del delta y hallazgos nuevos

Sin hallazgos nuevos. El intercalado comprueba ahora también la primera ejecución escalada tras consumir el segundo intento superior, tanto al distinguir argumentos como pasos. El caso de progreso mantiene la recuperación del otro par. El agotamiento local usa selector y persistencia reales, observa la finalización de la independiente y deja la dependiente pendiente, preservando contenido previo y dificultad. El global exige ocho ejecuciones y conserva el backlog. La prueba de cadena contrasta herencia, sobreescrituras, reservas no recursivas y configuraciones sin niveles.

### Regresión incorporada tras C-01 de código

`test_rechazos_previos_no_adelantan_escalada_ni_sustituyen_reservas` prepara la configuración común, añade una reserva exclusiva de escalada y simula dos rechazos mediante `patch` de `rechazos`. No sustituye la selección del perfil ni la construcción de su cadena. Ejecuta `revisar-tarea` con firma estable hasta el séptimo lanzamiento y compara los siete perfiles: base ×2 → superior ×2 → escalada ×2 → reserva del inicial ×1. Esa igualdad detecta tanto omitir el inicial como reemplazar sus reservas o insertar la reserva exclusiva de escalada. La captura del entorno permite exigir ausencia de `ORQUESTAR_ESCALADA` en todos los lanzamientos, separando esta recuperación del circuito por rechazos de desarrollo.

El incremento simulado de progreso en la séptima ejecución permite terminar el caso; la discriminación de C-01 procede de la secuencia exacta, no de ese incremento. La continuidad tras éxito y el reinicio posterior del par siguen cubiertos por el caso aprobado de éxito. Ampliar la tupla capturada con el indicador no altera los índices de par, perfil y sesión usados por las demás pruebas.

La prueba antigua de escalada cambia únicamente el paso seleccionado de `revisar-tarea` a `task-dev`, como declara el diseño. Conserva la preparación de dos veredictos reales simulados de Hades y las aserciones sobre el modelo escalado y `ORQUESTAR_ESCALADA=1`. Su configuración no declara niveles de dificultad; el cambio conserva una comprobación de desarrollo y evita exigir a análisis el comportamiento contrario al contrato nuevo. La regresión añadida cubre explícitamente la separación que antes no se observaba.

Los textos restaurados a UTF-8 no cambian las condiciones de los fixtures ni las expectativas funcionales. El delta de recarga conserva dos pares con contadores parciales en la transferencia y recepción comprobadas por igualdad.

## Evidencia y límites

Se reutilizan los registros de `orquestar_evidencias.jsonl`:

- Árbol `6c731a8607627b70d2b9364c86428f47681eb59d`, 09:34:51: `python -m unittest tests.test_orquestar.RecuperacionAnalisisTests.test_rechazos_previos_no_adelantan_escalada_ni_sustituyen_reservas`, código 1. Según el resultado entregado, un fallo de secuencia: comienza escalado, vuelve a superior y consume la reserva exclusiva de escalada. Solo se han modificado documentos desde ese rojo, según la invocación.
- Árbol actual `c2f5bceb0c315aef63601a43e0c1651acccd21fc`, 09:35:29: `git diff --check`, código 0.
- Antecedente verde del resto: árbol `449bda72bb6dee63cde7ed2f23df157972f0ab3b`, `python -m unittest discover -s tests -p test_orquestar.py` (79 pruebas, 09:31:08) y `python -m unittest discover -s skills/orquestar -p test_recarga.py` (11 pruebas, 09:29:42), código 0 en ambos. No se atribuyen esos verdes al árbol actual ni se afirma haber ejecutado el caso antiguo con su paso cambiado.

La aprobación corresponde a la calidad de las pruebas, incluida la nueva regresión en rojo; no acredita la resolución de C-01 en producción ni la ejecución satisfactoria de aserciones posteriores al primer fallo. Sin linter ni tipador configurados, sin dependencias nuevas y sin errores de carga reportados. El cambio del caso antiguo se evalúa por lectura de su fixture y aserciones.

No se repiten verificaciones ni se usan antecedentes WIP como evidencia. No se ejecutan suite completa ni proveedores reales.

## Enrutado

H-01 a H-04 continúan resueltos; **sin hallazgos de pruebas ni destino correctivo pendiente** para desarrollador, especificador o humano. C-01 dispone de una regresión discriminante; su corrección y cierre corresponden a desarrollo y revisión de código, fuera de este veredicto. Se actualiza únicamente este informe, sin implementar, cambiar estados ni crear commits.
