# Diseno tecnico: B-ADV-0005

La ausencia del ejecutable se propaga como `ArnesAusente`, recuperable unicamente por los consumidores de reservas. `--cmd` conserva su aborto. Una funcion comun registra cada ausencia (flujo, posicion base cero, arnes, modelo, contadores y coste cero), imprime el warning y emite el evento filtrable `arnes`. No genera cuota.

## Cambios y mapa de impacto
- MODIFY skills/orquestar/orquestar.py: comando -> ejecutar -> bucle; agente construye su comando directamente. Ambos consumidores saltan la configuracion ausente, conservan la ultima ejecucion real y su cuota, sin atribuirla al intento ausente. Sin ejecuciones disponibles retornan fallo claro con aviso error.
- MODIFY skills/telegram_gateway/gateway.py: invocar -> conversar; la excepcion comun permite recorrer las reservas heredadas de Atenea/Telegram. Conserva el contrato de invocar (codigo, sesion, respuesta). La sesion solo se consulta al inicio y no cruza arneses. No se amplian las reglas de cuota del gateway, reservadas a T-ADV-0026.
- NEW skills/orquestar/test_arnes_ausente.py: pruebas aisladas de los tres consumidores con procesos, disco temporal y avisos simulados.
- MODIFY skills/orquestar/SKILL.md y skills/telegram_gateway/SKILL.md: evento y reservas por ausencia.

Busqueda mecanica: comando solo se consume en ejecutar (incluido reintento fresco); ejecutar en bucle. base_comando_agente se consume en agente e invocar. invocar solo en conversar (incluido reintento fresco). Los tests directos de comandos conservan su contrato en exito; ningun test existente requiere modificacion. Se mantienen errores de autenticacion y reintentos frescos existentes sin saltar reservas.

Ninguna decision arquitectonica contradicha (DEC-P03/P09/P10). Se preserva la recuperacion UTC del principal mediante su registro original, sin recalcular fecha al encontrar reservas ausentes. La ruta no lanza procesos ni consultas adicionales salvo por cada ausencia; las pruebas comprueban un solo lanzamiento real para cadenas de dos ausencias y ninguna espera de cuota.

Si tras una ejecución con cuota solo quedan ausencias, se añade una señal agregada de espera sin repetir consumo ni atribuir cuota al arnés ausente. Los registros originales conservan el modelo y la recuperación; la señal agregada usa `modelos: {}`. El paso conserva la configuración de la última ejecución real. En el agente la señal agregada conserva también la fecha de esa ejecución.

HC-01: si el filtro ya omitió perfiles con cuota vigente y todas las configuraciones evaluadas faltan, `cuota_descartada` consulta la recuperación original y comprueba que el ejecutable de un perfil omitido siga disponible. Calcula solo los segundos restantes hasta la recuperación más temprana. Agente y paso emiten una señal de espera sin modelo de cuota ni consumo; no modifican la ventana original. La posición de las ausencias sigue el orden original de configuraciones, aun con perfiles omitidos. HC-02: el agente informa su error sin anunciar una parada del bucle. HC-03: ambas señales agregadas conservan `escalado` cuando corresponde.
