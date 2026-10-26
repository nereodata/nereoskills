# Revisión de código: B-ADV-0007

**Veredicto: RECHAZADO**

**Fecha:** 2026-10-26 · **Revisor:** Hades · **Modo:** orquestado

## Alcance y estado recibido

Rama `release/v1.0`, HEAD `f990cc066cbc7e171e07999e5cafe282b0e6c51f`. Antes de esta revisión, el único cambio sin commit es el artefacto maestro `docs/plan/bugs/B-ADV-0007-tests-cli-arrancan-gateway-real-con-token-del-entorno.md`: pasa de `planned` a `in_progress` y añade el triaje. No hay cambios en el índice ni delta de implementación o pruebas. No existe código de producción revisable para este bug; el rechazo evalúa el impedimento y la imposibilidad de dar la corrección por terminada, no defectos introducidos por un delta inexistente.

Se han contrastado el triaje, el código actual de `tests/test_cli_commands.py`, el despacho de `adevv/cli.py`, las credenciales y el autoarranque en `skills/orquestar/orquestar.py`, el antecedente B-ADV-0003 y las decisiones aplicables del plan de plataforma. A y B están omitidas justificadamente: el contrato de aislamiento ya consta en el bug y no requiere un diseño adicional. No se exige crear esos artefactos para desbloquearlo.

## Análisis estático y verificación

**N/A para producción:** no hay delta que compilar, tipar, analizar con lint o auditar por dependencias o secretos añadidos. No se han ejecutado pruebas: la lectura basta para confirmar el impedimento y ejecutar la reproducción sin aislamiento podría arrancar un gateway real. No se han leído ni utilizado credenciales reales.

Las evidencias históricas de `orquestar_evidencias.jsonl` que incluyen `test_cli_commands.py` pertenecen a árboles anteriores; no acreditan la corrección de B-ADV-0007 ni el aislamiento con variables Telegram presentes. No se declara ninguna verificación nueva en verde.

## Puntuaciones

Corrección, seguridad, conformidad, calidad, eficiencia y documentación: **N/A**; no hay implementación nueva que puntuar. **Media: N/A**. No procede inventar notas ni aprobar por ausencia de delta.

## Hallazgos

### HC-01 — 🟠 ALTA: el alcance autorizado excluye el archivo necesario para corregir el bug

**para: especificador**

- **Evidencia:** C1 y C2 del triaje exigen aislar las credenciales heredadas en `tests/test_cli_commands.py`. El mandato limita los cambios de implementación a `skills/`, `agents/` y `workflows/`; `tests/test_cli_commands.py` queda fuera. Su `setUp` (líneas 65-79) no aísla `TELEGRAM_BOT_TOKEN` ni `TELEGRAM_ALLOWED_USER_IDS`. El despacho CLI ejecuta el motor mediante `subprocess.run` sin un entorno aislado (`adevv/cli.py:301-309`). `credenciales` toma ambas variables del entorno (`skills/orquestar/orquestar.py:1482-1489`) y `iniciar_gateway` lanza el gateway cuando están configuradas (líneas 1935-1944), tanto desde `en_fondo` como desde `bucle` (líneas 1957 y 2094).
- **Consecuencia:** el fallo sigue sin corregir. Las pruebas pueden arrancar procesos reales con las credenciales heredadas, competir con el gateway legítimo y fallar al limpiar temporales. El triaje reconoce correctamente un impedimento real; no es una justificación suficiente para aprobar o cerrar el bug.
- **Resolución requerida:** conciliar el contrato de alcance con la corrección localizada exigida en `tests/test_cli_commands.py`, dejando explícita la incompatibilidad con el mandato vigente. El especificador no puede ampliar por su cuenta una restricción de la persona: mientras siga vigente, el bug permanece bloqueado. No procede sustituir el aislamiento por cambios en el motor, desactivar Telegram en producción, mover las pruebas ni inventar otra corrección dentro de las rutas permitidas.
- **Enrutamiento:** corresponde al especificador por un contrato de ejecución incompatible con la solución requerida. No se asigna al desarrollador mientras ese archivo esté excluido. Tampoco corresponde `para: humano` según la definición de Hades: no faltan cuentas, credenciales, hardware, pagos ni otro recurso externo.
- **Criterio de resolución:** alcance conciliado y aislamiento implementado en el archivo afectado; después, verificar los casos CLI con y sin ambas variables presentes, sin usar credenciales reales ni acceder a Telegram. La ejecución en verde del comando del triaje por sí sola, con las variables ausentes, no demuestra esa independencia.

## Salida para el paso invocador

**La restricción de alcance debe bloquear B-ADV-0007.** Aplicar la regla 5 del modo orquestado: conservar los cambios de la tarea en `wip/B-ADV-0007`, devolver `release/v1.0` al estado previo a la tarea, registrar el maestro con `status: blocked` y `pendiente_de: especificador`, y anotar HC-01 en la revisión de versión. Las tareas dependientes se dejan en espera sin modificarlas.

Esta revisión entrega el veredicto y su enrutamiento. No modifica código, el estado del bug, ramas ni otros artefactos; esas operaciones corresponden al paso invocador. La única escritura de Hades es este reporte, solicitado expresamente con el ID maestro. No se aprueba la corrección ni se cierra el bug.
