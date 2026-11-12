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

  @B-ADV-0029
  Esquema del escenario: La reserva conserva su arnés aunque el principal se elija por CLI
    Dado un rol <rol> de dificultad dificil con principal codex modelo gpt-6.1-sol esfuerzo max
    Y reservas agy modelo gemini-4-argon esfuerzo high y claude modelo claude-opus-5-5 esfuerzo high
    Y un bucle lanzado con --harness codex y una sesión previa codex-principal
    Cuando Codex agota cuota y después agy agota cuota
    Entonces los comandos lanzados usan codex, agy y claude en ese orden con sus respectivos modelos y esfuerzos
    Y agy y claude no reciben la sesión de Codex ni la de otro arnés
    Y las métricas atribuyen cada intento a su arnés, modelo y sesión reales
    Y Claude continúa el paso sin esperar la cuota de Codex
    Ejemplos:
      | rol |
      | development |
      | artemisa |

  @B-ADV-0029
  Escenario: Una reserva del mismo arnés conserva la sesión tras agotar cuota
    Dado un principal codex con --harness codex y una reserva que solo redefine su modelo
    Cuando el principal agota cuota
    Entonces la reserva usa codex con su propio modelo y reanuda la sesión del principal

  @B-ADV-0029
  Escenario: Forzar un principal diferente no traslada su modelo incompatible
    Dado un principal agy modelo gemini-4-argon esfuerzo high y una reserva claude modelo claude-opus-5-5 esfuerzo high
    Cuando el bucle usa --harness codex y Codex agota cuota
    Entonces el principal se lanza con codex sin el modelo ni el esfuerzo de agy
    Y las métricas del principal indican codex y modelo predeterminado
    Y la reserva usa claude modelo claude-opus-5-5 esfuerzo high con sesión nueva

  @T-ADV-0031
  Escenario: Fijar el perfil al crear una tarea desde Telegram
    Cuando envío "/tarea Arreglar login --perfil claude/opus/high --estricto"
    Entonces la tarea se crea sin versión con perfil {harness: claude, model: opus, effort: high, estricto: true}
    Y un perfil inválido se rechaza sin crear la tarea

  @B-ADV-0026 @CA-1 @CA-2 @CA-3 @CA-4
  Escenario: Bloquear localmente una tarea con pregunta humana, conservar su trabajo en wip y continuar con la independiente
    Dado un proyecto en release/v1.1 con Telegram habilitado y usuarios autorizados 111,222
    Y las tareas T-ADV-0101 sin dependencias, T-ADV-0102 independiente y T-ADV-0103 dependiente de T-ADV-0101 en estado planned
    Cuando el paso task-dev de T-ADV-0101 modifica src/modulo_a.py y solicita intervención humana con la pregunta "¿Usar proveedor OAuth interno o externo?" y contexto "Falta decidir proveedor sin valor por defecto seguro"
    Entonces el paso libera el bucle sin esperar entrada interactiva por stdin y mantiene las decisiones autónomas con valor por defecto seguro del modo orquestado
    Y se registra la pregunta Q-ADV-0001 vinculada a T-ADV-0101 con estado pendiente, su contexto y marca de aviso enviado
    Y el trabajo de T-ADV-0101 en src/modulo_a.py queda guardado y aislado en la rama wip/T-ADV-0101
    Y release/v1.1 queda con el árbol limpio, T-ADV-0101 en status blocked y pendiente_de humano y la pregunta anotada en docs/review/versions/v1.1-revision.md
    Y los usuarios 111 y 222 reciben un único aviso del evento respuesta con T-ADV-0101, la referencia Q-ADV-0001, la pregunta y la instrucción "/responder Q-ADV-0001 <respuesta>"
    Y en la siguiente vuelta del bucle se ejecuta T-ADV-0102 con árbol y base_calidad limpios sin incluir src/modulo_a.py, mientras T-ADV-0103 permanece en espera por depender de T-ADV-0101

  @B-ADV-0040
  Esquema del escenario: Continuar la revisión con una reserva tras acceso por suscripción deshabilitado
    Dado que Hades tiene Claude principal y reservas autorizadas agy y Codex en ese orden sin perfil estricto
    Y Claude devuelve código 1 y "Your organization has disabled Claude subscription access for Claude Code."
    Y la disponibilidad de agy es <disponibilidad> y Codex está disponible, autorizado y sin cuota vigente
    Y la reserva que revise emitirá un dictamen APROBADO válido
    Cuando se solicita la revisión pendiente
    Entonces el dictamen real APROBADO de <revisor> llega al paso sin abrir preguntas
    Y los arneses lanzados son exactamente <lanzamientos> en ese orden
    Y el historial identifica el fallo de acceso de Claude y el arnés <revisor> que completó la revisión sin inventar cuota ni veredicto
    Ejemplos:
      | disponibilidad | revisor | lanzamientos |
      | disponible y sin cuota vigente | agy | Claude, agy |
      | cuota vigente | Codex | Claude, Codex |

  @B-ADV-0040
  Escenario: Aplicar el destino de un rechazo auténtico emitido por la reserva
    Dado que Hades tiene Claude principal y agy como reserva autorizada, disponible y sin cuota vigente, sin perfil estricto
    Y Claude devuelve código 1 y "Your organization has disabled Claude subscription access for Claude Code."
    Y agy emite un dictamen RECHAZADO con un hallazgo alto para especificador y destino resolver
    Cuando se solicita la revisión pendiente y el paso recibe el dictamen
    Entonces el registro identifica a agy como revisor y conserva su RECHAZADO y su hallazgo
    Y la tarea queda blocked con pendiente_de especificador y el hallazgo registrado para ejecutar especificar
    Y no se abre una pregunta humana ni se trata el rechazo como indisponibilidad técnica

  @B-ADV-0040
  Escenario: Respetar el perfil fijado estricto aunque exista una reserva operativa
    Dado que la tarea fija explícitamente para Hades el perfil Claude con estricto true
    Y la configuración por dificultad ofrece agy como reserva autorizada, disponible y sin cuota vigente
    Y Claude devuelve código 1 y "Your organization has disabled Claude subscription access for Claude Code."
    Cuando se solicita la revisión pendiente
    Entonces solo se lanza Claude y no se ejecuta agy ni otra reserva
    Y la revisión permanece pendiente sin dictamen con diagnóstico de acceso deshabilitado y restricción del perfil estricto
    Y se conserva el trabajo y no se pregunta por una reserva ni se cambia el perfil fijado

  @B-ADV-0040
  Escenario: Conservar la revisión cuando ningún perfil autorizado puede revisar
    Dado que Hades tiene Claude principal y una reserva Claude de otro modelo autorizada y elegible sin perfil estricto
    Y ambos perfiles devuelven código 1 y "Your organization has disabled Claude subscription access for Claude Code."
    Cuando se solicita dos veces la misma revisión
    Entonces se informa el impedimento técnico y la revisión sigue pendiente sin dictamen
    Y se conservan el trabajo y las preguntas sin duplicarlas ni acreditar progreso de revisión
    Y los errores genéricos de autenticación o red conservan su tratamiento anterior

  @B-ADV-0040
  Escenario: Retomar dos revisiones tras respuestas ya recibidas sin perder WIP ni trabajo ajeno
    Dado una copia aislada de Q-ADV-0001 de B-ADV-0032 y Q-ADV-0002 de B-ADV-0033 con respuestas recibidas y WIP guardado
    Y ambas tareas tienen una reserva autorizada, disponible y sin cuota vigente, sin perfil estricto
    Cuando se incorporan entre pasos y se restauran sus cambios mientras existe trabajo local ajeno
    Y Claude devuelve código 1 y "Your organization has disabled Claude subscription access for Claude Code." y una reserva completa cada revisión
    Entonces ambas revisiones reciben el dictamen real y conservan WIP, historial y respuestas
    Y el trabajo ajeno permanece intacto y no se exige responder otra vez

  @B-ADV-0040
  Esquema del escenario: Conservar el tratamiento de errores genéricos al revisar con Hades
    Dado que Hades tiene Claude principal y Codex como reserva autorizada, disponible y sin cuota vigente, sin perfil estricto
    Y no existe sesión anterior de Hades y todos los ejecutables están disponibles
    Y el lanzador simulado de Claude devuelve código 1 y "<error>" sin diagnóstico de suscripción deshabilitada ni cuota
    Cuando se solicita la revisión pendiente
    Entonces se devuelve código 1 y el diagnóstico conserva "<error>"
    Y solo se lanza Claude una vez y Codex no recibe ninguna petición
    Y la revisión queda pendiente sin dictamen ni progreso de revisión
    Y el intento registra el fallo sin agotamiento de cuota ni ausencia de ejecutable
    Ejemplos:
      | error |
      | authentication failed |
      | network connection failed |

  @B-ADV-0040
  Esquema del escenario: Recuperar una revisión respondida desde una instantánea identificada
    Dado un repositorio temporal independiente por fila con la instantánea sintética <pregunta> de <tarea> sin modificar las preguntas reales
    Y la revisión pendiente es review-test sin dictamen y su historial contiene el rechazo anterior "RT-PREVIO" y el fallo de acceso de Claude
    Y la pregunta conserva ese historial, la referencia a wip/<tarea>, wip_restaurado false y la respuesta literal "Usar la reserva Codex ya configurada; pruebas con mocks"
    Y su estado inicial es <estado_pregunta> con <recepcion> y la tarea está <estado_tarea>
    Y wip/<tarea> contiene el archivo exclusivo borrador.txt con bytes UTF-8 "WIP-<tarea>\n" y su commit se registra como W0
    Y el árbol de destino tiene un cambio ajeno sin confirmar en ajeno.txt con bytes UTF-8 "AJENO\n" cuyo contenido e índice se guardan como A0
    Y Hades tiene Claude principal y Codex como única reserva autorizada, disponible y sin cuota vigente, sin perfil estricto
    Y los lanzadores simulados devuelven código 1 y "Your organization has disabled Claude subscription access for Claude Code." para Claude y código 0 con dictamen APROBADO sin hallazgos para Codex
    Cuando el bucle intenta incorporar la respuesta y preparar la revisión entre pasos con ese cambio ajeno presente
    Entonces conserva A0 sin confirmar, sobrescribir ni apartar el cambio ajeno y no lanza la revisión en ese árbol
    Y conserva W0, el historial y la respuesta sin crear preguntas ni avisar de reanudación efectiva
    Cuando el propietario guarda el cambio ajeno en un commit y el bucle reintenta entre pasos en el árbol limpio
    Entonces la pregunta queda incorporada una sola vez y la tarea queda planned sin pendiente_de antes de iniciar bug-fix
    Y al preparar bug-fix se restaura borrador.txt con los bytes originales y wip_restaurado pasa a true sin modificar el commit W0
    Y ajeno.txt conserva los bytes de A0 y no forma parte del delta restaurado de la tarea
    Cuando el paso solicita la revisión review-test pendiente con la respuesta ya incorporada
    Entonces se lanzan exactamente Claude y Codex en ese orden y el paso recibe APROBADO de Codex sin hallazgos que enrutar
    Y el registro identifica el fallo de Claude y a Codex como revisor final sin inventar cuota
    Y la revisión review-test queda aprobada y permite continuar bug-fix sin acreditar implementación ni cierre de la tarea
    Y se conserva RT-PREVIO y se añade el nuevo dictamen sin borrar el historial ni duplicar la respuesta
    Y otra incorporación no restaura WIP por segunda vez ni exige nueva respuesta ni crea preguntas
    Ejemplos:
      | pregunta | tarea | estado_pregunta | recepcion | estado_tarea |
      | Q-ADV-0001 | B-ADV-0032 | pendiente | una recepción en cola con la respuesta indicada aún no incorporada | blocked con pendiente_de humano |
      | Q-ADV-0002 | B-ADV-0033 | incorporada | respuesta indicada ya incorporada y cola vacía | planned sin pendiente_de |

  @B-ADV-0033 @CA-1 @CA-2 @CA-3 @CA-4 @CA-5
  Esquema del escenario: Enrutar un hallazgo de Hades según su destino sin escalarlo al humano
    Dado una tarea bloqueada con un hallazgo de Hades que declara destino <destino>
    Cuando el orquestador procesa el hallazgo y conserva su decisión en la tarea y en la revisión de versión
    Entonces <resultado>
    Y <preguntas>
    Ejemplos:
      | destino | resultado | preguntas |
      | artemisa | la tarea pasa a planned para retomar desarrollo | no se crea una entrada en orquestar_preguntas.json |
      | especificador | la tarea permanece bloqueada con pendiente_de especificador y se ejecuta el paso especificar | no se crea una entrada en orquestar_preguntas.json |
      | humano | la tarea queda bloqueada con pendiente_de humano | se crea una pregunta humana persistente |

  @B-ADV-0026 @CA-1 @CA-3
  Esquema del escenario: Conservar el bloqueo y diagnosticar sin duplicar avisos cuando el canal de Telegram falla o no está disponible
    Dado un proyecto en release/v1.1 con la tarea T-ADV-0101 que requiere la intervención humana "¿Puerto de escucha de producción?"
    Y configuración de canal <situacion_canal>
    Cuando se registra el bloqueo local de T-ADV-0101 y posteriormente se consulta --estado, /estado y avanza otro paso del bucle
    Entonces la pregunta Q-ADV-0001 permanece en estado pendiente y consultable con diagnóstico <diagnostico>
    Y no se pierde la pregunta ni se reenvían avisos duplicados en pasos o consultas posteriores
    Ejemplos:
      | situacion_canal | diagnostico |
      | sin credenciales de Telegram | canal no disponible |
      | evento respuesta desactivado en orchestration.json | evento desactivado |
      | fallo de envío HTTP al transporte de Telegram | fallo de envío |

  @B-ADV-0026 @CA-4 @CA-6 @CA-7 @CA-8
  Escenario: Incorporar entre pasos una respuesta recibida durante otra tarea y reanudar conservando el trabajo previo
    Dado que T-ADV-0101 está bloqueada con la pregunta Q-ADV-0001 y su trabajo previo src/modulo_a.py aislado en wip/T-ADV-0101
    Y el bucle está en marcha ejecutando la tarea independiente T-ADV-0102 mientras T-ADV-0103 espera a T-ADV-0101
    Cuando el usuario autorizado 111 envía "/responder Q-ADV-0001 Usar proveedor OAuth interno" mientras corre T-ADV-0102
    Entonces el gateway guarda la respuesta de forma duradera sin modificar ni commitear archivos rastreados del repositorio durante T-ADV-0102
    Y confirma al usuario "Respuesta recibida para Q-ADV-0001 (T-ADV-0101); se incorporará al terminar el paso en curso" distinguiéndola de la reanudación efectiva
    Y al terminar T-ADV-0102 el bucle incorpora la respuesta entre pasos, actualiza el contexto de T-ADV-0101 y v1.1-revision.md, pasa T-ADV-0101 a planned sin pendiente_de y marca Q-ADV-0001 como incorporada
    Y notifica que T-ADV-0101 ha sido reanudada efectivamente
    Y al ejecutarse T-ADV-0101 recupera src/modulo_a.py desde wip/T-ADV-0101, recibe la respuesta en su contexto, se completa y desbloquea T-ADV-0103

  @B-ADV-0026 @CA-6
  Escenario: Mantener el bloqueo cuando la respuesta incorporada no resuelve el impedimento
    Dado que T-ADV-0101 está bloqueada con la pregunta Q-ADV-0001 pidiendo "Indica la URL base y el puerto del servicio"
    Cuando el usuario autorizado 111 envía una respuesta insuficiente "PENDIENTE: falta definir URL y puerto" y el bucle procesa la cola entre pasos
    Entonces T-ADV-0101 conserva status blocked y pendiente_de humano y Q-ADV-0001 sigue pendiente explicando qué falta resolver
    Y se informa al usuario de que la respuesta no resuelve el impedimento y T-ADV-0101 permanece bloqueada

  @B-ADV-0026 @CA-4 @CA-7 @CA-8
  Esquema del escenario: Esperar intervención cuando no queda trabajo elegible y reanudar sin segunda orden salvo parada manual
    Dado que T-ADV-0101 está bloqueada con la pregunta pendiente Q-ADV-0001, T-ADV-0102 ya está completed y T-ADV-0103 depende de T-ADV-0101
    Y no quedan tareas elegibles en release/v1.1 y el estado de parada manual es <parada_manual>
    Cuando el bucle alcanza la falta de tareas elegibles y después el usuario autorizado 111 responde "/responder Q-ADV-0001 Usar proveedor OAuth interno"
    Entonces antes de la respuesta el estado distingue el bloqueo de la tarea T-ADV-0101 de un bloqueo global y mantiene el gateway disponible mostrando el motivo
    Y tras la respuesta T-ADV-0101 actualiza su contexto con la decisión y <resultado_reanudacion>
    Ejemplos:
      | parada_manual | resultado_reanudacion |
      | sin parada manual con bucle en espera | el bucle incorpora la respuesta y continúa con T-ADV-0101 y T-ADV-0103 sin segunda orden manual de lanzamiento |
      | sin parada manual con bucle ya detenido por falta de elegibles | el gateway incorpora la respuesta, pasa T-ADV-0101 a planned y relanza el bucle en segundo plano sin exigir /lanzar |
      | con parada manual explícita activa | la respuesta queda registrada pero se respeta la parada manual sin relanzar el bucle |

  @B-ADV-0026 @CA-8
  Escenario: Conservar preguntas, respuestas y estado de incorporación tras reinicios y recargas sin reanudar dos veces
    Dado que Q-ADV-0001 de T-ADV-0101 recibió una respuesta pendiente de incorporar y Q-ADV-0002 de T-ADV-0104 ya fue incorporada
    Cuando el proceso del bucle se recarga o se reinicia antes de ejecutar el siguiente paso
    Entonces el estado de Q-ADV-0001 y Q-ADV-0002 se conserva íntegro en disco
    Y el nuevo ciclo incorpora Q-ADV-0001 exactamente una vez y no vuelve a reanudar ni duplicar Q-ADV-0002

  @B-ADV-0034 @CA-1 @CA-2 @CA-3 @CA-4 @CA-5 @CA-6
  Esquema del escenario: Responder desde CLI sin Telegram y compartir la recepción con el gateway
    Dado que Q-ADV-0001 bloquea T-ADV-0101 en un proyecto sin Telegram configurado
    Y el bucle ejecuta otra tarea independiente
    Cuando el operador consulta "adevv orquestar --preguntas"
    Y ejecuta 'adevv orquestar --responder <referencia> "Usar OAuth interno"'
    Entonces la consulta muestra Q-ADV-0001 y la respuesta confirma recepción durable en cola
    Y la recepción identifica al operador como local sin autorizarlo en Telegram
    Y no cambia ningún archivo rastreado durante el paso activo
    Y la respuesta es un dato que nunca se ejecuta como orden
    Y la misma respuesta enviada por un usuario Telegram autorizado no agrega otra recepción
    Ejemplos:
      | referencia |
      | Q-ADV-0001 |
      | T-ADV-0101 |

  @B-ADV-0034 @CA-3 @CA-7
  Esquema del escenario: Rechazar respuestas CLI inválidas sin mutaciones
    Dado que el proyecto tiene preguntas pendientes y una pregunta cerrada
    Cuando el operador responde desde CLI con <entrada>
    Entonces recibe un diagnóstico de <motivo> sin modificar preguntas ni tareas
    Ejemplos:
      | entrada | motivo |
      | Q-ADV-9999 con texto | referencia inexistente |
      | Q-OTRO-0001 con texto | referencia ajena |
      | T-ADV-0101 con dos preguntas pendientes | ambigüedad |
      | Q-ADV-0002 ya incorporada | pregunta cerrada |
      | Q-ADV-0001 con texto vacío | falta de respuesta |
      | referencia arbitraria con texto | referencia inexistente |

  @B-ADV-0034 @CA-4 @CA-7
  Escenario: Serializar entregas de ambos canales y aislar raíces
    Dado que dos raíces independientes contienen una pregunta Q-ADV-0001
    Y en la primera raíz hay un paso activo
    Cuando CLI y Telegram autorizado entregan concurrentemente el mismo texto en la primera raíz
    Entonces se guarda una sola recepción durable en esa raíz
    Y la segunda raíz conserva su registro intacto
    Y un usuario Telegram no autorizado no puede consultar ni responder preguntas

  @B-ADV-0034 @CA-5 @CA-7
  Esquema del escenario: Incorporar una respuesta CLI entre pasos y mostrar su resultado real
    Dado que Q-ADV-0001 recibió desde CLI una respuesta durable antes de reiniciar
    Cuando se incorpora entre pasos con <condicion>
    Entonces se observa <resultado>
    Y otra incorporación no duplica la decisión ni la reanudación
    Ejemplos:
      | condicion | resultado |
      | respuesta concreta y bucle detenido por falta de elegibles | pregunta incorporada y bucle lanzado una sola vez |
      | parada manual activa | respuesta conservada sin relanzar |
      | respuesta PENDIENTE: falta URL | pregunta pendiente y diagnóstico falta URL |
      | respuesta INSUFICIENTE: falta puerto | pregunta pendiente y diagnóstico falta puerto |
      | otra pregunta pendiente de la misma tarea | respuesta incorporada y tarea bloqueada por esa pregunta |
      | dependencia no completada | respuesta incorporada y tarea en espera de su dependencia sin anunciar elegibilidad ni relanzar por esa tarea |

  @B-ADV-0044
  Esquema del escenario: Acotar la revisión técnica pendiente en desarrollo y análisis
    Dado un paso <paso> con dos intentos permitidos y un trabajo en curso
    Cuando en cada intento Hades termina sin dictamen por falta de acceso tras probar los perfiles autorizados
    Y el arnés registra el impedimento con otra redacción y fecha en la ficha y la revisión de versión
    Y cada invocación confirma únicamente esas dos notas en un commit y termina con código 0 y el árbol limpio
    Entonces el bucle para tras el segundo commit e identifica el paso, el ID y la revisión técnica pendiente
    Y el arnés ha recibido exactamente dos invocaciones y no se inicia una tercera
    Y conserva el trabajo, las métricas de cada ejecución y el perfil estricto sin completar ni abrir una pregunta
    Ejemplos:
      | paso          |
      | bug-fix       |
      | task-dev      |
      | revisar-tarea |

  @B-ADV-0044
  Escenario: Los cambios administrativos no renuevan el presupuesto de análisis
    Dado que work-plan tiene un único perfil con dos intentos y el plan sigue pendiente
    Cuando el primer intento crea un commit vacío y el segundo solo actualiza notas del seguimiento
    Entonces el bucle agota los dos intentos de ese perfil y para informando de work-plan

  @B-ADV-0044
  Esquema del escenario: Reconocer trabajo parcial en una ficha antigua
    Dado un bug sin campos de progreso, en curso con un intento sin avance
    Cuando el siguiente intento aporta <entregable>
    Entonces se registra avance y el bug dispone de nuevo de todos sus intentos de desarrollo
    Y el avance parcial conserva pendiente el cierre revisado
    Ejemplos:
      | entregable                                                              |
      | código WIP sin commit que corrige el comportamiento afectado por el bug |
      | prueba confirmada que reproduce ese comportamiento del bug              |
      | escenario en la especificación de la función                            |
      | primer dictamen formal de la revisión en curso                          |
      | resolución incorporada de una pregunta del ID                           |

  @B-ADV-0044
  Escenario: Aislar intentos técnicos entre IDs y conservarlos al recargar
    Dado que A ha consumido un intento técnico de dos y después B avanza
    Cuando el motor se recarga y otro proveedor autorizado de Hades tampoco emite dictamen para A
    Entonces el segundo intento de A agota su presupuesto y el avance de B queda registrado
    Y un arranque manual posterior conserva el WIP y las métricas y permite una nueva tanda de dos intentos

  @B-ADV-0044
  Esquema del escenario: Distinguir el cierre del trabajo parcial ante un retorno erróneo
    Dado un bug con el mismo cambio parcial de código en un commit nuevo y el árbol limpio
    Cuando el arnés termina con código 1 y el estado en disco es <estado>
    Entonces el bucle <resultado>
    Ejemplos:
      | estado                                                                            | resultado                                                                 |
      | en curso, sin dictamen                                                            | aplica la recuperación acotada del arnés                                  |
      | completed, aprobación canónica anterior al cambio y revisión del cambio pendiente | mantiene pendiente la revisión y aplica la recuperación acotada del arnés |
      | completed, aprobación canónica que cubre el cambio actual                         | continúa sin repetir el paso                                              |

  @B-ADV-0044
  Esquema del escenario: Distinguir la reserva recuperada de una invocación sin cuota
    Dado un intento técnico sin dictamen y una reserva autorizada de la misma invocación
    Cuando la reserva termina con <resultado> y solo hay un commit parcial
    Entonces el bucle <accion>
    Y cada intento conserva su consumo real
    Ejemplos:
      | resultado       | accion                                     |
      | dictamen válido | continúa con ese dictamen                  |
      | cuota agotada   | mantiene la espera de cuota de la revisión |

  @metricas
  Escenario: Una cola parcial no oculta las sesiones ni consume el siguiente evento
    Dado un registro de agente con sesión S seguido de una última fila JSON incompleta sin salto final
    Cuando el motor busca la sesión del agente y comienza a observar eventos nuevos
    Entonces recupera S y la cola pendiente no cuenta como evento
    Cuando termina de escribirse esa fila con una verificación V
    Entonces el motor observa V una sola vez entre los eventos nuevos

  @metricas
  Esquema del escenario: Recuperación explícita de un fragmento entre dos objetos válidos
    Dado un registro con un consumo de 7 tokens y coste de 0,25 USD en línea 1, <fragmento> en línea 2 y una verificación V en línea 3
    Cuando el motor consulta su estado
    Entonces conserva el consumo y V y diagnostica orquestar_metricas.jsonl y la línea 2
    Y el archivo sigue íntegro y la exportación estricta rechaza emitir totales parciales
    Cuando se solicita la recuperación de las métricas
    Entonces queda una copia idéntica byte a byte al original y el registro activo conserva ambas filas válidas en orden
    Y la exportación contabiliza exactamente 7 tokens, 0,25 USD y una verificación V
    Cuando se solicita la recuperación por segunda vez
    Entonces se conservan los mismos dos registros y la exportación sigue contabilizando 7 tokens, 0,25 USD y una verificación V
    Y la copia de evidencia de la primera recuperación sigue disponible e idéntica byte a byte al original

    Ejemplos:
      | fragmento                                |
      | el fragmento JSON inválido `_s": 0}`     |
      | una fila con la secuencia UTF-8 inválida FF |

  @metricas
  Escenario: Procesos concurrentes registran eventos tras una escritura interrumpida
    Dado un registro con una fila válida y un fragmento final de un proceso interrumpido
    Cuando el motor, un agente, una verificación y el gateway registran simultáneamente 100 eventos cada uno con identificadores únicos y contenido Unicode
    Entonces se leen los 400 identificadores con su contenido original una sola vez cada uno, además de la fila original
    Y el fragmento queda identificable con su diagnóstico y disponible para recuperación

  @metricas
  Escenario: El bucle conserva un paso ya completado antes de observar la corrupción
    Dado que el registro está vacío al iniciar el paso A y hay un paso B pendiente que depende de A
    Y A deja su ficha completada en un commit con revisión aprobada
    Y el registro contiene el consumo de A en la línea 1, un fragmento inválido en la línea 2 y la aprobación en la línea 3
    Cuando el bucle recoge el resultado de A antes de recuperar las métricas
    Entonces informa de la corrupción en orquestar_metricas.jsonl, línea 2, sin excepción sin capturar
    Y en esa ejecución se conservan el commit, la ficha completada, el consumo y la aprobación de A
    Cuando se recupera el registro y se relanza el bucle antes de ejecutar B
    Entonces el selector elige B y el número total de ejecuciones de A entre ambos arranques es 1

  @metricas
  Escenario: El observador recibe la siguiente verificación después de acortarse el registro
    Dado un registro con un consumo en la línea 1, un fragmento inválido en la línea 2 y la verificación V1 en la línea 3
    Y un observador de verificaciones nuevas que ya ha recibido V1
    Cuando se recupera el registro y quedan solo las dos filas válidas
    Y se registra la verificación V2 al final
    Entonces la siguiente consulta del mismo observador entrega exactamente V2 una vez
    Y otra consulta sin más escrituras no entrega verificaciones

  @metricas
  Escenario: Una escritura que coincide con la recuperación conserva su evento confirmado
    Dado un registro con los eventos confirmados E1 y E2 separados por una línea cuyos bytes son FF 0A en hexadecimal
    Cuando se solicita la recuperación y, mientras está en curso, otro proceso solicita registrar E3
    Y se completan la recuperación y la confirmación de escritura de E3
    Entonces el registro activo contiene exactamente E1, E2 y E3, una vez cada uno y con su contenido original
    Y la copia de evidencia conserva los bytes FF 0A entre E1 y E2
