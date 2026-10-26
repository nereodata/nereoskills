# Diseño técnico · T-ADV-0026

Se conserva la combinación Atenea/telegram y `motor.lista_reservas`. `conversar` consulta `consumo_cuotas` una vez por mensaje y omite todo agotamiento vigente, incluso sin reservas (DEC-ESP-03). No espera. Cada candidato consulta la sesión de su propio usuario y arnés, también las reservas (DEC-ESP-01); guarda solo la sesión que respondió. Cada mensaje reconsidera al titular.

`invocar` conserva su resultado triple. Antes de extraer la respuesta detecta cuota en la salida cruda con `espera_cuota`, registra fecha de detección, arnés, código, modelo_cuota, cuota_espera_s y métricas originales; señala la cuota mediante ModeloIndisponible. Así un result vacío no oculta stderr ni provoca un reintento inútil de sesión. La recuperación se calcula desde esa misma fecha UTC y duración, sin actualizarla por ausencias posteriores.

`invocar` convierte exclusivamente OSError del lanzador en ModeloIndisponible con motivo de arranque; no encubre fallos de E/S de persistencia. `conversar` avanza por ModeloIndisponible (cuota o arranque) y ArnesAusente. Los fallos ordinarios conservan reintento sin sesión y RuntimeError, sin usar reservas. Las ausencias conservan registrar_ausencia; arranques fallidos no generan cuota. La firma identifica al respondedor y añade reserva según posición original. Si no quedan candidatos, lanza GatewayNoDisponible (subclase RuntimeError) con motivos y recuperación por perfil; `responder` convierte exclusivamente esa excepción a diagnóstico firmado.

## Archivos e impacto
- MODIFY `skills/telegram_gateway/gateway.py` y `SKILL.md`; NEW `test_reservas.py`. Sin cambios del motor ni dependencias.
- Llamantes encontrados con rg: `invocar` solo lo consume `conversar`; `conversar` lo consume `responder`. Tests de conversación simulan el triple y conservan el contrato. Llamadas directas siguen recibiendo RuntimeError si todos fallan; responder entrega el diagnóstico al usuario.
- Escenarios aprobados: los seis de `skills/telegram_gateway/features/telegram_gateway.feature`. Ningún test previo se retira ni modifica; los de B-ADV-0005 no tienen una sesión propia de la reserva y siguen iniciando nueva.
- Decisión ampliada: `docs/design/B-ADV-0005-design.md:7` consulta solo al inicio. DEC-ESP-01 autoriza consultar cada arnés sin cruzar sesiones ni modificar pasos/agentes. No se contradicen decisiones arquitectónicas (DEC-P03/P09/P10).
- Referencia temporal: instantes comparables con zona mediante ahora/fecha_estado; espera_cuota recibe ese instante local para interpretar la hora del arnés y el diagnóstico convierte explícitamente a ISO UTC, informe de agentes conserva conversión local del motor. Pruebas fijan reloj y comprueban recuperación exacta y caducidad.
- Camino frecuente: una consulta de métricas por mensaje; pruebas comprueban cantidad y orden de procesos, cero procesos para agotados y ausencia de esperas. Sin red, con directorios temporales y lanzador simulado.
