# language: es
@telegram @gateway @reservas
Característica: Continuidad de la conversación de Telegram con reservas
  Como usuario autorizado del gateway
  Quiero seguir conversando con una reserva cuando el titular no está disponible
  Para conservar mis conversaciones y conocer qué modelo responde

  @T-ADV-0026 @CA-M-1 @CA-M-2 @CA-M-4 @CA-M-5
  Escenario: Conmutar por cuota y compartir su recuperación exacta
    Dado telegram con titular codex/m1 y reservas ordenadas agy/m2 y claude/m3 que heredan effort high
    Y que todos los instantes del escenario están en UTC el 26 de octubre de 2026
    Cuando a las 12:00:00 codex/m1 falla por cuota durante 1800 segundos y agy no arranca
    Entonces claude/m3 responde con firma que identifica claude/m3 e indica reserva
    Y el agotamiento compartido identifica codex/m1 con recuperación exacta a las 12:30:00
    Y a las 12:15:00 /agentes muestra codex/m1 agotado hasta las 12:30:00
    Y a las 12:15:00 la consulta de cuotas del bucle reconoce codex/m1 como agotado hasta las 12:30:00
    Y a las 12:30:00 esas consultas dejan de considerar vigente ese agotamiento
    Y el fallo de arranque de agy/m2 no cambia la recuperación de codex/m1 ni atribuye cuota a agy/m2

  @T-ADV-0026 @CA-M-2 @CA-M-3
  Escenario: Conservar las sesiones de cada arnés al usar reservas y regresar al titular
    Dado el usuario autorizado 12345 con sesiones codex-s1 para codex y agy-s1 para agy
    Y telegram con titular codex/m1 agotado hasta las 12:30:00 UTC y reserva agy/m2 disponible
    Cuando el usuario 12345 envía un mensaje a las 12:00:00 UTC
    Entonces solo se invoca agy/m2 reanudando exactamente agy-s1
    Y agy devuelve agy-s2 que queda disponible para ese usuario sin reemplazar codex-s1
    Cuando el mismo usuario envía otro mensaje a las 12:01:00 UTC
    Entonces solo se invoca agy/m2 reanudando exactamente agy-s2
    Y agy devuelve agy-s3 que queda disponible sin reemplazar codex-s1
    Cuando el mismo usuario envía otro mensaje a las 12:31:00 UTC
    Entonces se invoca primero codex/m1 reanudando exactamente codex-s1 y responde sin usar reservas
    Y agy-s3 sigue disponible para ese usuario

  @T-ADV-0026 @CA-M-2 @CA-M-3
  Escenario: Aislar las sesiones de otro usuario durante la conmutación
    Dado el usuario autorizado 12345 con sesiones codex-s1 para codex y agy-s3 para agy
    Y el usuario autorizado 67890 sin sesiones previas
    Y telegram con titular codex/m1 agotado hasta las 12:30:00 UTC y reserva agy/m2 disponible
    Cuando el usuario 67890 envía un mensaje a las 12:10:00 UTC
    Entonces solo se invoca agy/m2 sin reanudar ninguna sesión
    Y su respuesta devuelve agy-u2 que se conserva únicamente para 67890
    Y las sesiones codex-s1 y agy-s3 de 12345 se conservan sin cambios
    Cuando 67890 envía otro mensaje a las 12:31:00 UTC
    Entonces codex/m1 responde sin reanudar ninguna sesión ni invocar reservas
    Y ninguna petición de 67890 recibe codex-s1 ni agy-s3

  @T-ADV-0026 @CA-M-2 @CA-M-4
  Escenario: Diagnosticar todas las configuraciones indisponibles
    Dado telegram con titular codex/m1 agotado hasta las 12:30:00 UTC, reserva agy/m2 ausente y reserva claude/m3 que no arranca
    Cuando un usuario autorizado envía un mensaje a las 12:00:00 UTC
    Entonces no se lanza codex/m1 y se intenta agy/m2 antes de claude/m3
    Y el usuario recibe un diagnóstico que identifica codex/m1 por cuota hasta las 12:30:00 UTC, agy/m2 por arnés ausente y claude/m3 por fallo de arranque
    Y no recibe un error genérico ni queda esperando la recuperación de cuota

  @T-ADV-0026 @CA-M-2 @CA-M-4
  Escenario: No lanzar el único modelo cuando su cuota sigue vigente
    Dado telegram con codex/m1 como único modelo efectivo y sin reservas propias ni heredadas
    Y codex/m1 agotado hasta las 12:30:00 UTC
    Cuando un usuario autorizado envía un mensaje a las 12:00:00 UTC
    Entonces no se lanza ningún arnés
    Y el usuario recibe un diagnóstico que identifica codex/m1 por cuota hasta las 12:30:00 UTC
    Y la respuesta no espera a que se recupere la cuota

  @T-ADV-0026 @CA-M-2
  Escenario: No ocultar un fallo ordinario como indisponibilidad
    Dado un titular con sesión previa y una reserva disponible
    Cuando la reanudación falla y el reintento sin sesión también falla sin cuota ni error de arranque
    Entonces se conserva el tratamiento de error ordinario sin invocar reservas
