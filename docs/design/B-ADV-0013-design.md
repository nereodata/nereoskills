# Diseño técnico · B-ADV-0013

Se conserva la firma de progreso y la recuperación de desarrollo existentes. La
recuperación de análisis se mantiene en memoria por `(paso, argumento)`, serializada
como lista JSON en la transferencia cooperativa. Cada entrada contiene cadena de
perfiles efectivos, posición e intentos sin progreso. Solo el progreso del propio
par elimina su entrada; cambiar de par no reinicia nada.

`cadena_analisis(root, paso, dificultad)` resuelve el rol mediante `rol_de`, los
niveles superiores mediante `ajustes`, la escalada sobre el inicial efectivo y las
reservas mediante `lista_reservas`. Deduplica por harness/model/effort efectivos.
No expande las reservas de niveles ni escalada. Los niveles no alteran el backlog.

El bucle selecciona el perfil pendiente antes de ejecutar el arnés. Sus reservas
operacionales siguen usando el mecanismo existente de cuota/fallo; un éxito sin
progreso consume un intento del perfil de recuperación. Al cambiar de perfil no
se reanuda una sesión anterior. Al agotar la cadena se produce un diagnóstico con
paso, argumento, perfiles e intentos. Los pasos locales reutilizan
`bloquear_sin_progreso` con un detalle opcional, sin cambiar su contrato anterior;
los globales paran sin escrituras al backlog.

## Archivos e impacto

- Modificar `skills/orquestar/orquestar.py`: cadena, estado por par y transferencia.
- Modificar `tests/test_orquestar.py`: simulación determinista del bucle, Git real
  para persistencia y aislamiento local; ningún proveedor ni Telegram real.
- Modificar `skills/orquestar/test_recarga.py`: transferencia ampliada.
- Modificar `skills/orquestar/SKILL.md` y README: contrato operativo.

Llamantes encontrados: `bucle` consume `rol_de`, `escalada` y
`bloquear_sin_progreso`; `registrar_fallo_suite` también usa la recuperación de
desarrollo y conserva su comportamiento. `main` recibe el estado transferido y
`recargar_version` lo transporta sin interpretarlo. No cambia la firma pública de
selección, cuota ni progreso. El argumento opcional del bloqueo lo usa únicamente
la rama de análisis. Tests existentes de bloqueo y cuota mantienen su contrato.
`RecargaTests.test_bucle_transfiere_antes_de_calcular_paso` amplía el estado esperado
con la lista de recuperaciones (vacía para transferencias anteriores).

La regla anterior de parada general tras dos intentos en
`skills/orquestar/SKILL.md` queda sustituida para los siete pasos aprobados en el
bug. No contradice decisiones del plan de plataforma: sigue siendo estado local
en stdlib, sin servicios nuevos. No hay unidades ni zonas horarias nuevas.
La cadena se construye una vez por par; su recorrido es lineal en el número de
perfiles. Las simulaciones cuentan ejecuciones y verifican que no se ejecutan
perfiles posteriores al éxito, evitando trabajo adicional en el camino habitual.

## Verificación

Solo `test_orquestar.py`, `test_recarga.py` y `git diff --check`, mediante
`adevv orquestar --verificar`. Sin linter/tipador configurado en el proyecto ni
cambios de dependencias. La carga de ambos módulos en unittest comprueba sintaxis
e imports. Revisión independiente de pruebas antes del arreglo y de código al final.

## Correcciones de la revisión de código

C-01: la cadena de análisis no consulta rechazos de Hades ni sustituye su inicial
por la escalada de desarrollo. `bucle` aplica ese circuito solo fuera de los siete
pasos de análisis. La regresión existente
`EscaladaTests.test_loop_launches_the_escalated_model_with_its_flag` pasa a
`task-dev`: conserva su intención de verificar la escalada de desarrollo. Su uso
anterior de `revisar-tarea` queda sustituido por el contrato aprobado de este bug;
una regresión nueva con dos rechazos y reservas exclusivas de escalada exige el
orden base, superior, escalada y reserva del inicial, sin marca de escalada por
rechazos en el entorno. No cambian las reglas de `task-dev`/`bug-fix`.

C-02 y C-03: se sincroniza la regla general de la skill con
`docs/orquestacion.md` y se restaura UTF-8 en las adiciones del bug.
