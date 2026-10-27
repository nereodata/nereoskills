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
    Dado que pruebo por separado agente Hades y conversación del gateway
    Y el principal claude disponible falla por autenticación y tiene reserva codex disponible
    Cuando solicito ejecutar el trabajo
    Entonces se conserva el código de fallo en agente y se informa del error de autenticación en el gateway
    Y codex no recibe ninguna petición y no hay métricas de arnés ausente

  Escenario: Filtrar las notificaciones de ausencia
    Dado que telegram.eventos contiene solo error y el principal ausente tiene una reserva disponible
    Cuando solicito ejecutar el trabajo
    Entonces se ejecuta la reserva y veo el warning de ausencia en consola
    Y no se envía por Telegram el aviso del evento arnes
    Y con la configuración por defecto se solicita el aviso arnes identificando el ejecutable ausente

  @T-ADV-0030 @CA-M-1 @CA-M-4
  Esquema del escenario: Resolver por separado el token y los destinatarios de Telegram
    Dado un proyecto temporal ProyectoDemo sin variables TELEGRAM_* heredadas y con restauración del entorno al terminar incluso ante fallos
    Y credenciales exclusivamente ficticias, transporte sin red y observadores de escucha y procesos sin efectos reales
    Y token local <local>, IDs locales <ids_locales>, token ambiental <ambiental> e IDs ambientales <ids_ambientales>
    Y que AUSENTE significa variable no definida y VACIO significa cadena vacía
    Cuando resuelvo las credenciales del proyecto
    Entonces el token efectivo es <token>, los IDs efectivos son <ids> y el origen del token es <origen>
    Ejemplos:
      | local | ids_locales | ambiental | ids_ambientales | token | ids | origen |
      | token-local-ficticio | 111 | AUSENTE | AUSENTE | token-local-ficticio | 111 | proyecto |
      | AUSENTE | AUSENTE | token-entorno-ficticio | 222 | token-entorno-ficticio | 222 | entorno |
      | token-local-ficticio | 111 | token-entorno-ficticio | 222 | token-local-ficticio | 111 | proyecto |
      | token-local-ficticio | AUSENTE | token-entorno-ficticio | 222 | token-local-ficticio | 222 | proyecto |
      | AUSENTE | 111 | token-entorno-ficticio | 222 | token-entorno-ficticio | 111 | entorno |
      | VACIO | 111 | token-entorno-ficticio | 222 | token-entorno-ficticio | 111 | entorno |
      | token-local-ficticio | VACIO | token-entorno-ficticio | 222 | token-local-ficticio | 222 | proyecto |
      | VACIO | 111 | AUSENTE | 222 | VACIO | 111 | ninguno |
      | AUSENTE | AUSENTE | AUSENTE | AUSENTE | VACIO | lista vacía | ninguno |

  @T-ADV-0030 @CA-M-2 @CA-M-4
  Esquema del escenario: Identificar el proyecto al principio de cada aviso con cualquier fuente válida
    Dado un proyecto temporal ProyectoDemo sin variables TELEGRAM_* heredadas y con restauración del entorno al terminar incluso ante fallos
    Y credenciales exclusivamente ficticias, transporte sin red y observadores de escucha y procesos sin efectos reales
    Y token local <local>, IDs locales <ids_locales>, token ambiental <ambiental> e IDs ambientales <ids_ambientales>
    Y que AUSENTE significa variable no definida y los avisos Telegram están habilitados sin filtro de eventos
    Cuando solicito un aviso de evento version y texto "Versión terminada"
    Entonces observo exactamente un envío con token <token> al destinatario <destinatario>
    Y el mensaje comienza exactamente por "[ProyectoDemo] Versión terminada" y conserva la firma de versión de Adevv
    Y no hay envíos a otros destinatarios ni escucha ni creación de procesos
    Ejemplos:
      | local | ids_locales | ambiental | ids_ambientales | token | destinatario |
      | token-local-ficticio | 111 | AUSENTE | AUSENTE | token-local-ficticio | 111 |
      | AUSENTE | AUSENTE | token-entorno-ficticio | 222 | token-entorno-ficticio | 222 |
      | token-local-ficticio | 111 | token-entorno-ficticio | 222 | token-local-ficticio | 111 |
      | token-local-ficticio | AUSENTE | token-entorno-ficticio | 222 | token-local-ficticio | 222 |
      | AUSENTE | 111 | token-entorno-ficticio | 222 | token-entorno-ficticio | 111 |

  @T-ADV-0030 @CA-M-3 @CA-M-4
  Escenario: Informar una vez por bucle sin arrancar el gateway con el respaldo
    Dado un proyecto temporal ProyectoDemo con todas las variables TELEGRAM_* heredadas excluidas y restauración al terminar incluso ante fallos
    Y únicamente token ambiental token-entorno-ficticio e IDs ambientales 222, todos ficticios
    Y Telegram habilitado, transporte sin red, sin gateway activo y observadores de escucha, procesos y PID sin efectos reales
    Cuando solicito tres veces el autoarranque en una misma ejecución del bucle
    Entonces no se solicita escucha ni creación de procesos ni reserva de PID
    Y aparece exactamente una nota con el motivo "token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto"
    Cuando inicio otra ejecución del bucle y solicito tres veces el autoarranque
    Entonces tampoco se solicita escucha ni creación de procesos ni reserva de PID
    Y la salida de la nueva ejecución contiene exactamente una nota con el mismo motivo

  @T-ADV-0030 @CA-M-3 @CA-M-4
  Esquema del escenario: Conservar el autoarranque con token del proyecto
    Dado un proyecto temporal ProyectoDemo sin variables TELEGRAM_* heredadas y con restauración del entorno al terminar incluso ante fallos
    Y credenciales exclusivamente ficticias, transporte sin red y observadores de escucha y procesos sin efectos reales
    Y token local token-local-ficticio, IDs locales <ids_locales>, token ambiental <ambiental> e IDs ambientales <ids_ambientales>
    Y que AUSENTE significa variable no definida, Telegram está habilitado y no existe gateway ni PID activo
    Cuando solicito una vez el autoarranque con el lanzador disponible y exitoso
    Entonces se solicita exactamente un arranque del gateway del proyecto en segundo plano
    Y las credenciales destinadas a la escucha tienen token token-local-ficticio y usuario <usuario>
    Y no aparece el diagnóstico de token del entorno solo para avisos
    Ejemplos:
      | ids_locales | ambiental | ids_ambientales | usuario |
      | 111 | AUSENTE | AUSENTE | 111 |
      | 111 | token-entorno-ficticio | 222 | 111 |
      | AUSENTE | token-entorno-ficticio | 222 | 222 |

  @B-ADV-0011
  Escenario: Recuperar un fallo transitorio del paso
    Dado un paso cuyo arnés falla dos veces por red y después responde correctamente
    Y el límite de reintentos del arnés es 3
    Cuando ejecuto el paso
    Entonces espero 60 y 300 segundos antes de repetir el mismo perfil
    Y completo el paso sin usar reservas ni consumir otros pasos del bucle
    Y aunque el contador de falta de progreso esté a un intento de su límite, los reintentos no lo incrementan
    Y cada intento deja su consumo en métricas sin señalar cuota

  @B-ADV-0011
  Escenario: Agotar perfiles ante un fallo persistente
    Dado un principal y una reserva que fallan siempre con error de autenticación
    Y el límite de reintentos del arnés es 1
    Cuando ejecuto el paso
    Entonces cada perfil recibe un intento inicial y un reintento tras 60 segundos
    Y solo después se detiene el bucle
    Y el aviso incluye la cola de salida del último arnés ejecutado

  @B-ADV-0011
  Escenario: La reserva recupera un fallo persistente del principal
    Dado un principal que falla persistentemente por red y una reserva que responde
    Y el límite de reintentos del arnés es 0
    Cuando ejecuto el paso
    Entonces la reserva recibe el paso sin sesión heredada del principal
    Y el bucle continúa sin esperar ni señalar cuota

  @B-ADV-0011
  Escenario: Detener durante la espera de recuperación
    Dado un arnés que falla por red
    Cuando solicito parar durante la espera de reintento
    Entonces termina el bucle sin ejecutar nuevos intentos ni reservas

  @B-ADV-0011
  Escenario: No repetir un paso ya completado en disco
    Dado un arnés que devuelve un error después de completar y commitear el paso
    Cuando el bucle comprueba el resultado
    Entonces continúa sin reintentos ni reservas

  @B-ADV-0011
  Escenario: Conservar la espera de cuota
    Dado un principal que agota cuota y una reserva que falla persistentemente por red
    Cuando ambos perfiles se agotan
    Entonces conserva la espera de recuperación de cuota del principal
    Y no atribuye cuota al error de red

  @B-ADV-0011
  Escenario: Aplicar el límite por defecto y saturar la espera
    Dado que no configuro el límite de reintentos del arnés
    Y el principal falla persistentemente
    Cuando ejecuto el paso
    Entonces hace 4 intentos separados por esperas de 60, 300 y 900 segundos
    Y si configuro 4 reintentos la cuarta espera también es de 900 segundos
    Y un límite negativo o no entero se rechaza antes de arrancar el bucle
    Y si la salida es un prefijo de 3000 letras A seguido de 1997 letras B y FIN, el fragmento del aviso contiene exactamente las 1997 letras B y FIN del último arnés ejecutado
