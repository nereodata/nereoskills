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

  @B-ADV-0020
  Escenario: Comprobar una sospecha al relanzar y borrar la marca al responder
    Dado un titular con una marca supuesta de hace 60 segundos y una reserva disponible
    Cuando relanzo el bucle y el titular responde al paso pendiente
    Entonces utilizo el titular y registro su recuperación sin borrar el histórico

  @B-ADV-0020
  Escenario: Respetar la recuperación confirmada
    Dado un titular con reinicio confirmado dentro de 3600 segundos y una reserva disponible
    Cuando relanzo el bucle
    Entonces utilizo la reserva y no pruebo el titular antes del reinicio

  @B-ADV-0020
  Escenario: Limitar comprobaciones de una sospecha
    Dado un intervalo cuota_reintento_s de 300 segundos y una marca sin hora confirmada
    Cuando el titular sigue sin cuota
    Entonces no lo vuelvo a probar en este proceso antes de 300 segundos
    Y al alcanzar los 300 segundos lo pruebo antes de usar la reserva

  @B-ADV-0020
  Esquema del escenario: Recuperar marcas por orden explícita
    Dado marcas confirmadas vigentes de codex/m1, codex/m2 y claude/m1 con recuperación dentro de 3600 segundos
    Cuando ejecuto adevv orquestar --cuota-reset <selector>
    Entonces registro recuperación para <pares> sin reescribir el histórico
    Y los pares seleccionados <pares> vuelven a ser elegibles
    Y estado y agentes dejan de mostrar agotados los pares seleccionados <pares>
    Y los pares ajenos al selector conservan sus marcas confirmadas y siguen restringidos hasta su recuperación registrada
    Y estado y agentes siguen mostrando agotados los pares ajenos al selector hasta esa recuperación
    Ejemplos:
      | selector | pares |
      | codex/m1 | codex/m1 |
      | codex | codex/m1 y codex/m2 |
      | | codex/m1 y codex/m2 y claude/m1 |

  @B-ADV-0020
  Escenario: Despertar una espera después de un reset
    Dado un bucle esperando 3600 segundos por cuota real de codex/m1
    Cuando otra orden ejecuta --cuota-reset codex/m1
    Entonces el bucle continúa en su siguiente comprobación de como máximo 30 segundos
    Y no necesita relanzarse

  @B-ADV-0020
  Esquema del escenario: Avisar de créditos una vez por episodio
    Dado Telegram habilitado y un titular cuya respuesta contiene <error>
    Cuando falla por créditos y vuelve a fallar en la siguiente comprobación
    Entonces envío una sola vez el aviso "Sin créditos en codex: recarga y el bucle lo reintentará"
    Y conservo una marca supuesta que permite reintentar cada 300 segundos
    Y agentes y estado indican "supuesto" y el origen "sin créditos"
    Ejemplos:
      | error |
      | out of credits |
      | credit balance |
      | billing_hard_limit |

  @B-ADV-0020
  Escenario: Identificar el origen de una marca real
    Dado un titular que responde "usage limit resets in 1 hour"
    Cuando consulto estado o agentes
    Entonces veo la hora de recuperación y "real" y "hora en la respuesta"

  @B-ADV-0020
  Escenario: Recuperar la marca histórica que originó el fallo
    Dado un registro histórico sin clasificación de cuota con espera 1800 segundos de hace 60 segundos
    Cuando relanzo el bucle y el titular responde
    Entonces compruebo el titular y registro recuperación sin reescribir el registro antiguo

  @B-ADV-0020
  Esquema del escenario: Configurar el intervalo de sondeo
    Dado cuota_reintento_s con valor <valor> en orchestration.json
    Cuando el titular responde sin cuota y sin hora de reinicio
    Entonces el siguiente sondeo del mismo proceso se permite tras <segundos> segundos
    Ejemplos:
      | valor | segundos |
      | 120 | 120 |
      | 0 | 300 |
      | -5 | 300 |
      | texto | 300 |
      | null | 300 |

  @B-ADV-0020
  Escenario: Conservar la recuperación de una marca histórica distinta del antiguo valor por defecto
    Dado un titular codex/m1 con un registro histórico sin clasificación de cuota con espera 3600 segundos de hace 60 segundos
    Y una reserva claude/m2 disponible
    Cuando relanzo el bucle
    Entonces utilizo la reserva y no pruebo codex/m1 durante los 3540 segundos restantes hasta su recuperación registrada
    Y conservo el registro histórico sin reescribirlo

  @B-ADV-0020
  Escenario: Usar el intervalo por defecto en una configuración sin la opción de sondeo
    Dado un orchestration.json que no contiene la propiedad cuota_reintento_s
    Cuando el titular responde sin cuota y sin hora de reinicio
    Entonces no vuelvo a probarlo en este proceso antes de 300 segundos
    Y al alcanzar los 300 segundos lo pruebo antes de usar la reserva disponible

  @T-ADV-0031
  Escenario: Sin perfil fijado nada cambia
    Dado una tarea sin el campo perfil y con dificultad dificil
    Cuando el bucle resuelve el perfil del paso task-dev
    Entonces se usa exactamente el perfil que corresponde a la dificultad

  @T-ADV-0031
  Esquema del escenario: Fijar el perfil de una tarea
    Dado una tarea con <perfil> y un perfil por dificultad con model sonnet y effort medium
    Cuando el bucle resuelve el perfil del paso <paso>
    Entonces el rol <rol> usa model <modelo> y effort <esfuerzo>
    Y los campos que el perfil no declara se toman del perfil por dificultad
    Y las métricas y --agentes lo muestran como fijado por la tarea
    Ejemplos:
      | perfil | paso | rol | modelo | esfuerzo |
      | perfil único {model: opus} | task-dev | artemisa | opus | medium |
      | perfil único {model: opus, effort: high} | bug-fix | artemisa | opus | high |
      | perfil único {model: opus} | especificar | atenea | sonnet | medium |
      | perfil por rol {atenea: {effort: max}} | especificar | atenea | sonnet | max |
      | perfil por rol {hades: {model: haiku}} | task-dev | artemisa | sonnet | medium |

  @T-ADV-0031
  Escenario: Reserva con aviso cuando el perfil fijado no está disponible
    Dado una tarea con perfil fijado claude/opus y una reserva en el perfil por dificultad
    Cuando el perfil fijado no tiene cuota o su arnés no existe
    Entonces el paso se ejecuta con la reserva del perfil por dificultad
    Y se avisa una sola vez "T-XXX: perfil fijado claude/opus sin cuota; uso la reserva claude/haiku"

  @T-ADV-0031
  Esquema del escenario: Perfil estricto
    Dado una tarea con perfil fijado claude/opus y estricto true
    Cuando <situación>
    Entonces <resultado>
    Y no se usa ninguna reserva ni otro modelo
    Ejemplos:
      | situación | resultado |
      | el perfil fijado no tiene cuota | el bucle espera la cuota |
      | el arnés del perfil fijado no existe | la tarea se bloquea para la persona con el motivo |
      | los rechazos de Hades alcanzan el tope de escalada o promoción | la tarea se bloquea en lugar de escalar o subir de dificultad |

  @T-ADV-0031
  Esquema del escenario: Rechazar un perfil inválido
    Dado una tarea pendiente con <perfil>
    Cuando el bucle lee el backlog
    Entonces para con el error del backlog que cita el ID y <motivo>
    Y no lanza ningún paso
    Ejemplos:
      | perfil | motivo |
      | harness nube | arnés no soportado |
      | effort enorme | esfuerzo no válido |
      | un rol artemis | rol desconocido |

  @T-ADV-0031
  Escenario: Solo una persona fija el perfil
    Dado una tarea con perfil fijado
    Cuando el bucle promueve su dificultad
    Entonces el campo perfil queda intacto

  @T-ADV-0031
  Escenario: Fijar el perfil al crear una tarea desde Telegram
    Cuando envío "/tarea Arreglar login --perfil claude/opus/high --estricto"
    Entonces la tarea se crea sin versión con perfil {harness: claude, model: opus, effort: high, estricto: true}
    Y un perfil inválido se rechaza sin crear la tarea
