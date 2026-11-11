# Diseño Técnico: B-ADV-0032 — Terminación acotada de arneses con JSON

## Cambios

- **[MODIFY]** `skills/orquestar/orquestar.py`: encapsula la captura JSON de `agy` y `claude` en lectura concurrente de ambos streams, detecta la respuesta final y termina el árbol tras una gracia limitada; propaga `timeout_s` desde el perfil y el entorno.
- **[MODIFY]** `tests/test_orquestar.py`: comprueba el cierre forzado tras JSON, el timeout previo al JSON y el `stdin` cerrado de `agy`.

## Mapa de impacto

- Llamantes: `lanzar()` es consumido por `ejecutar()` y `agente()`; ambos reciben las métricas de `timeout` y `cierre_forzado` sin cambiar su contrato de retorno.
- Pruebas: se amplía `SubprocesoColgadoTests`; ninguna prueba previa queda invalidada.
- Decisiones contradichas: ninguna.
- Camino caliente: el sondeo es de 20 ms únicamente mientras el arnés está activo; las pruebas con procesos reales verifican que no queda esperando EOF.

## Testeabilidad

Los procesos Python de prueba emiten JSON y permanecen vivos deliberadamente, permitiendo verificar el corte sin depender de un proveedor externo.

## Reanudación H-01/H-02

Ambos `Popen` de `lanzar()` crean sesión propia en POSIX mediante
`start_new_session=True`. `_terminar_arbol_proceso()` usa `killpg(pid, SIGKILL)`
incluso si el líder ya salió; el grupo corresponde al PID reservado al crear la
sesión. La señal nunca se envía al grupo del orquestador. Se mantiene `p.kill()`
como respaldo y `p.wait(timeout=2)`; Windows conserva `taskkill /F /T`.
Los consumidores de la función de terminación son la captura JSON y el timeout
de captura de líneas de `lanzar()`; ambos requieren el cierre del grupo.

`timeout_de_rol()` valida `math.isfinite` antes de aceptar el número. Sus
consumidores `lanzar()`, `ejecutar()` y `agente()` mantienen configuración inválida
igual a valor por defecto; cero o negativo finito conserva la desactivación
explícita. No se contradice ninguna DEC ni se añade dependencia.

Las regresiones previas se conservan. La nueva regresión POSIX crea un hijo real
con pipes heredados y comprueba que queda ausente o zombi (sin ejecución), tanto
por timeout como por gracia tras JSON; se omite explícitamente en Windows.
