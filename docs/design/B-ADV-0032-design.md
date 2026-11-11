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

## Reanudación H-01/H-03/H-04

La captura JSON supervisa proceso y lectores hasta su cierre conjunto. Si el padre
sale con pipes heredados abiertos, conserva la gracia JSON y el timeout, y aplica
una gracia de cierre desde su salida incluso sin JSON ni timeout configurado.
La captura por líneas mantiene el temporizador durante p.wait(), también tras EOF
o excepción; solo lo cancela después de esa espera.

Un sentinel privado distingue el timeout omitido en lanzar() de None explícito
(desactivado). ejecutar() y agente() propagan siempre el valor resuelto; los
llamantes directos sin argumento siguen consultando el entorno. No cambian los
consumidores enumerados ni se invalida ninguna prueba; ninguna DEC contradicha.
Los plazos siguen en segundos monotónicos y el sondeo en 20 ms. Se añaden
regresiones dentro de SubprocesoColgadoTests, incluida la salida inmediata del
padre en POSIX (skip explícito en Windows) y supervisión con streams controlados.

## Reanudación H-05: grupo Windows duradero

Ambos lanzamientos reales se centralizan en un helper: Windows crea un Job Object
con KILL_ON_JOB_CLOSE y el arnés suspendido, lo asigna al job antes de reanudarlo.
Así ningún hijo puede escapar durante el arranque. El handle permanece en el
invocador y sobrevive al padre. La terminación utiliza TerminateJobObject, seguida
de espera acotada; el cierre normal libera el handle y termina cualquier residual.
Los fallos de creación/asignación/reanudación abortan y limpian el proceso
suspendido; no se degrada silenciosamente a taskkill. POSIX conserva su sesión.

Consumidores: _ejecutar_captura_json y lanzar por líneas usan el helper de creación
y liberan el job; _terminar_arbol_proceso usa el job si existe y mantiene respaldo
para procesos sin job. ejecutar/agente conservan contratos y métricas. Las pruebas
previas no cambian de contrato; los dobles de Popen evitan APIs nativas. El nuevo
caso Windows verifica ambos caminos y la ausencia del hijo al retornar. Ninguna
DEC contradicha, sin dependencias nuevas. No hay sondeo adicional en el camino
caliente; se comprueba con las regresiones locales del triaje.

La reanudación usa APIs Win32 documentadas: snapshot de hilos del proceso recién
creado suspendido, OpenThread y ResumeThread. El snapshot y el handle del hilo se
cierran siempre. No se usan APIs NT privadas. _proceso_agrupado centraliza ambos
Popen y el cierre del job; los errores nativos se propagan, nunca como éxito.
