# language: es
@orquestar @reservas
Característica: Continuidad con arneses ausentes
  Como usuario del bucle desatendido
  Quiero utilizar las reservas disponibles cuando falta un ejecutable
  Para continuar los pasos, las revisiones y la conversación de Telegram

  Esquema del escenario: Saltar configuraciones cuyo arnés no está instalado
    Dado un <flujo> con principal codex modelo principal-a ausente y reserva claude modelo reserva-b disponible
    Cuando solicito ejecutar el trabajo
    Entonces la reserva recibe la petición sin reutilizar la sesión del principal
    Y veo un warning que identifica codex y la conmutación a reserva
    Y las métricas identifican el intento ausente del principal codex modelo principal-a de ese flujo
    Y ese intento registra cero tokens de entrada, caché leída, caché escrita, salida y razonamiento y coste cero
    Y ese intento no registra agotamiento de cuota ni tiempo de recuperación
    Y se solicita el aviso Telegram del evento filtrable "arnes" identificando codex
    Ejemplos:
      | flujo |
      | paso del bucle |
      | agente Hades |
      | conversación del gateway |

  Esquema del escenario: Continuar tras una reserva intermedia ausente
    Dado un <flujo> con estas configuraciones en orden
      | posición | arnés | modelo | ejecutable |
      | principal | codex | principal-a | ausente |
      | primera reserva | claude | reserva-b | ausente |
      | segunda reserva | agy | reserva-c | disponible |
    Cuando solicito ejecutar el trabajo
    Entonces agy modelo reserva-c recibe la petición sin reutilizar sesiones de los otros arneses
    Y no se declara un fallo por falta de arneses ni se espera recuperación de cuota
    Y veo un warning de conmutación por codex y otro por claude
    Y las métricas identifican por separado el principal codex modelo principal-a y la primera reserva claude modelo reserva-b de ese flujo
    Y cada intento ausente registra cero tokens de entrada, caché leída, caché escrita, salida y razonamiento y coste cero
    Y ninguno de los dos intentos ausentes registra agotamiento de cuota ni tiempo de recuperación
    Y se solicita un aviso Telegram del evento filtrable "arnes" por codex y otro por claude
    Ejemplos:
      | flujo |
      | paso del bucle |
      | agente Hades |
      | conversación del gateway |

  Escenario: Ningún ejecutable disponible
    Dado que pruebo por separado paso del bucle, agente Hades y conversación del gateway
    Y faltan los arneses del principal y de todas las reservas
    Cuando solicito ejecutar el trabajo
    Entonces falla con un mensaje que indica que no hay arneses disponibles
    Y cada configuración ausente deja su warning, métrica de consumo cero y aviso arnes identificando su arnés
    Y se solicita un aviso Telegram de error
    Y no espera recuperación de cuota

  Esquema del escenario: Cuota en un arnés disponible y última reserva ausente
    Dado un <flujo> cuyo principal codex modelo principal-a disponible agota cuota con recuperación a las "2026-10-26T18:00:00Z"
    Y la última reserva claude modelo reserva-b tiene el arnés ausente
    Cuando solicito ejecutar el trabajo
    Entonces conserva la señal de agotamiento de cuota del principal codex modelo principal-a
    Y conserva exactamente el instante de recuperación "2026-10-26T18:00:00Z" del principal
    Y las métricas identifican el intento ausente de la última reserva claude modelo reserva-b de ese flujo
    Y ese intento registra cero tokens de entrada, caché leída, caché escrita, salida y razonamiento y coste cero
    Y ese intento no registra agotamiento de cuota ni un nuevo tiempo de recuperación
    Ejemplos:
      | flujo |
      | paso del bucle |
      | agente Hades |

  Escenario: Un error distinto de ausencia no habilita reservas
    Dado que pruebo por separado paso del bucle, agente Hades y conversación del gateway
    Y el principal claude disponible falla por autenticación y tiene reserva codex disponible
    Cuando solicito ejecutar el trabajo
    Entonces se conserva el código de fallo en paso y agente y se informa del error de autenticación en el gateway
    Y codex no recibe ninguna petición y no hay métricas de arnés ausente

  Escenario: Filtrar las notificaciones de ausencia
    Dado que telegram.eventos contiene solo error y el principal ausente tiene una reserva disponible
    Cuando solicito ejecutar el trabajo
    Entonces se ejecuta la reserva y veo el warning de ausencia en consola
    Y no se envía por Telegram el aviso del evento arnes
    Y con la configuración por defecto se solicita el aviso arnes identificando el ejecutable ausente
