# language: es
@telegram @gateway @reservas
Característica: Continuidad de la conversación de Telegram con reservas
  Como usuario autorizado del gateway
  Quiero seguir conversando con una reserva cuando el titular no está disponible
  Para conservar mis conversaciones y conocer qué modelo responde

  @T-ADV-0023 @CA-M-1 @CA-M-2
  Escenario: Revisar y confirmar el cierre desde Telegram
    Dado una versión v1.0 en revisión final, con tarea T-DEMO-0001 completada y validación funcional "Abrir la pantalla"
    Cuando se envía el aviso de fin de versión y el usuario autorizado solicita /cerrar v1.0
    Entonces ambos mensajes incluyen la tarea, los bloqueos y las validaciones de la revisión
    Y muestran /cerrar v1.0 confirmo como confirmación necesaria
    Y no se modifican ramas ni etiquetas ni se relanza el bucle

  @T-ADV-0023 @CA-M-2 @CA-M-3 @CA-M-5
  Esquema del escenario: Cerrar una versión confirmada y continuar
    Dado un repositorio temporal limpio con main, release/v1.0 y remoto bare local sin red
    Y la rama activa es release/v1.0, no existe PID del bucle y el estado es PARAR por revisión final de v1.0
    Y todos los ítems de v1.0.0 están completed salvo la tarea T-DEMO-0002 con estado <estado_permitido>
    Y existen las revisiones de versión y arquitectura, no hay informe de producto y versiones y manifiestos están alineados en 1.0.0
    Y el changelog de 1.0.0 está presente, el preflight es satisfactorio y no existe etiqueta v1.0.0 local ni remota
    Y <pendientes>
    Cuando el usuario autorizado envía /cerrar v1.0 confirmo
    Entonces main local y remoto contienen el merge de release/v1.0 y la etiqueta anotada v1.0.0 apunta al merge
    Y desaparece la rama local release/v1.0 y el repositorio queda limpio en main
    Y la respuesta confirma el cierre y <continuacion>
    Ejemplos:
      | estado_permitido | pendientes | continuacion |
      | completed | una tarea planned en v1.1.0 | solicita una vez el relanzamiento en segundo plano |
      | cancelled | una tarea planned en v1.1.0 | solicita una vez el relanzamiento en segundo plano |
      | completed | ninguna tarea pendiente con versión | informa FIN sin lanzar procesos |
      | cancelled | ninguna tarea pendiente con versión | informa FIN sin lanzar procesos |

  @T-ADV-0023 @CA-M-2 @CA-M-4
  Esquema del escenario: Rechazar cierres no elegibles sin alterar el repositorio
    Dado un repositorio temporal limpio en release/v1.0 con main y remoto bare local sin red
    Y no existe PID del bucle y su estado es PARAR por revisión final de v1.0
    Y todos los ítems de v1.0.0 están completed, existen las revisiones de versión y arquitectura y no hay informe de producto
    Y versiones y manifiestos están alineados en 1.0.0, el changelog está presente y el preflight es satisfactorio
    Y no existe etiqueta v1.0.0 local ni remota y el cierre sería elegible para un remitente autorizado
    Y se introduce únicamente <impedimento>, manteniendo las demás precondiciones
    Cuando el remitente <remitente> envía /cerrar v1.0 confirmo
    Entonces <respuesta>
    Y ramas locales y remotas, etiquetas, índice y archivos conservan el estado anterior sin relanzar el bucle
    Ejemplos:
      | remitente | impedimento | respuesta |
      | no autorizado | remitente ajeno a TELEGRAM_ALLOWED_USER_IDS | no se responde al remitente |
      | autorizado | PID del bucle existente | se informa que existe un PID del bucle |
      | autorizado | rama activa main | se informa que la rama activa no es release/v1.0 |
      | autorizado | revisión final correspondiente a v0.9 en vez de v1.0 | se informa que la versión solicitada no coincide con la revisión final |
      | autorizado | tarea T-DEMO-0001 de v1.0.0 en estado planned | se informa del trabajo pendiente T-DEMO-0001 con estado planned |
      | autorizado | tarea T-DEMO-0001 de v1.0.0 en estado in_progress | se informa del trabajo pendiente T-DEMO-0001 con estado in_progress |
      | autorizado | tarea T-DEMO-0001 de v1.0.0 en estado blocked | se informa del bloqueo de T-DEMO-0001 |
      | autorizado | parada por petición manual en lugar de revisión final, sin PID | se informa que la parada no corresponde a revisión final |
      | autorizado | revisión de arquitectura ausente | se informa que falta la revisión de arquitectura |
      | autorizado | informe de producto con decisión PENDIENTE | se informa que quedan decisiones de producto pendientes |
      | autorizado | informe de producto con decisión APLICAR | se informa que falta aplicar las decisiones de producto |
      | autorizado | modificación sin confirmar de un archivo rastreado | se informa que el árbol está sucio |
      | autorizado | archivo nuevo no rastreado y no ignorado | se informa que el árbol está sucio |
      | autorizado | manifiesto con versión 0.9.0 | se informa de la versión desalineada del manifiesto |
      | autorizado | sección 1.0.0 ausente del changelog | se informa que falta el changelog de la versión |
      | autorizado | comando preflight que termina con código 1 | se informa del fallo de preflight |
      | autorizado | etiqueta local v1.0.0 existente | se informa que la etiqueta local ya existe |
      | autorizado | etiqueta remota v1.0.0 existente | se informa que la etiqueta remota ya existe |

  @T-ADV-0023 @CA-M-4 @CA-M-5
  Esquema del escenario: Recuperar fallos de publicación sin cierre parcial
    Dado un repositorio temporal limpio en release/v1.0 con main y remoto bare local sin red
    Y no existe PID del bucle, el estado es PARAR por revisión final de v1.0 y todos sus ítems están completed
    Y existen las revisiones de versión y arquitectura, no hay informe de producto y los manifiestos están alineados en 1.0.0
    Y el changelog está presente, el preflight es satisfactorio y no existe etiqueta v1.0.0 local ni remota
    Y se introduce únicamente <fallo>, manteniendo las demás precondiciones de cierre
    Cuando el usuario autorizado envía /cerrar v1.0 confirmo
    Entonces se informa del motivo y no se relanza el bucle
    Y main y release locales, rama activa, índice y archivos vuelven al estado anterior sin merge pendiente ni etiqueta nueva
    Y main y etiquetas remotas permanecen sin cambios
    Ejemplos:
      | fallo |
      | conflicto al integrar release sobre main actualizado |
      | rechazo del push por un hook del remoto |
      | remoto sin soporte de push atómico |

  @T-ADV-0023 @CA-M-3 @CA-M-4
  Escenario: Informar de un relanzamiento fallido después de cerrar
    Dado una publicación correcta de v1.0.0 y una tarea pendiente en v1.1.0
    Cuando el arranque en segundo plano falla
    Entonces la respuesta confirma que v1.0.0 quedó publicada e indica el motivo y /lanzar para reintentar
    Y no deshace ni repite el merge, etiqueta o push

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

  @T-ADV-0030 @CA-M-3 @CA-M-4
  Esquema del escenario: Rechazar cada entrada de escucha con token ambiental antes de cualquier efecto
    Dado un proyecto temporal ProyectoDemo sin variables TELEGRAM_* heredadas y con restauración del entorno al terminar incluso ante fallos
    Y credenciales exclusivamente ficticias, transporte sin red y observadores de escucha, procesos y PID sin efectos reales
    Y token local <local>, IDs locales <ids_locales>, token ambiental token-entorno-ficticio e IDs ambientales 222
    Y que AUSENTE significa variable no definida y VACIO significa cadena vacía
    Y Telegram habilitado sin gateway ni PID activo
    Cuando ejecuto <comando> para el proyecto temporal
    Entonces la entrada termina con código distinto de cero
    Y muestra el mismo motivo del bucle "token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto"
    Y no solicita escucha, creación de procesos ni reserva de PID
    Ejemplos:
      | comando | local | ids_locales |
      | adevv telegram | AUSENTE | AUSENTE |
      | adevv telegram | AUSENTE | 111 |
      | adevv telegram | VACIO | 111 |
      | adevv telegram --fondo | AUSENTE | AUSENTE |
      | adevv telegram --fondo | AUSENTE | 111 |
      | adevv telegram --fondo | VACIO | 111 |
      | adevv telegram --gestionado | AUSENTE | AUSENTE |
      | adevv telegram --gestionado | AUSENTE | 111 |
      | adevv telegram --gestionado | VACIO | 111 |

  @T-ADV-0030 @CA-M-3 @CA-M-4
  Esquema del escenario: Permitir cada entrada de escucha con token local y destinatario efectivo
    Dado un proyecto temporal ProyectoDemo sin variables TELEGRAM_* heredadas y con restauración del entorno al terminar incluso ante fallos
    Y credenciales exclusivamente ficticias, transporte sin red y observadores de escucha, procesos y PID sin efectos reales
    Y token local token-local-ficticio, IDs locales <ids_locales>, token ambiental <ambiental> e IDs ambientales <ids_ambientales>
    Y que AUSENTE significa variable no definida y Telegram está habilitado sin gateway ni PID activo
    Cuando ejecuto <comando> para el proyecto temporal con lanzador disponible y exitoso
    Entonces se permite el arranque y se alcanza la escucha simulada con token token-local-ficticio y usuario <usuario>
    Y no aparece el diagnóstico de token del entorno solo para avisos
    Ejemplos:
      | comando | ids_locales | ambiental | ids_ambientales | usuario |
      | adevv telegram | 111 | AUSENTE | AUSENTE | 111 |
      | adevv telegram | 111 | token-entorno-ficticio | 222 | 111 |
      | adevv telegram | AUSENTE | token-entorno-ficticio | 222 | 222 |
      | adevv telegram --fondo | 111 | AUSENTE | AUSENTE | 111 |
      | adevv telegram --fondo | 111 | token-entorno-ficticio | 222 | 111 |
      | adevv telegram --fondo | AUSENTE | token-entorno-ficticio | 222 | 222 |
      | adevv telegram --gestionado | 111 | AUSENTE | AUSENTE | 111 |
      | adevv telegram --gestionado | 111 | token-entorno-ficticio | 222 | 111 |
      | adevv telegram --gestionado | AUSENTE | token-entorno-ficticio | 222 | 222 |

  @T-ADV-0030 @CA-M-1 @CA-M-3 @CA-M-4
  Esquema del escenario: No avisar ni escuchar con credenciales incompletas
    Dado un proyecto temporal ProyectoDemo sin variables TELEGRAM_* heredadas y con restauración del entorno al terminar incluso ante fallos
    Y credenciales exclusivamente ficticias, transporte sin red y observadores de escucha, procesos y PID sin efectos reales
    Y token local <local>, IDs locales <ids_locales>, token ambiental AUSENTE e IDs ambientales AUSENTE
    Y que AUSENTE significa variable no definida y VACIO significa cadena vacía, con Telegram habilitado
    Cuando solicito un aviso version y un autoarranque y ejecuto <comando> para el proyecto temporal
    Entonces no se envían avisos ni se solicita escucha, creación de procesos o reserva de PID
    Y la entrada termina con código distinto de cero y diagnóstico de credenciales incompletas
    Ejemplos:
      | comando | local | ids_locales |
      | adevv telegram | VACIO | 111 |
      | adevv telegram | token-local-ficticio | AUSENTE |
      | adevv telegram --fondo | VACIO | 111 |
      | adevv telegram --fondo | token-local-ficticio | AUSENTE |
      | adevv telegram --gestionado | VACIO | 111 |
      | adevv telegram --gestionado | token-local-ficticio | AUSENTE |

  @T-ADV-0024 @CA-M-1 @CA-M-2 @CA-M-3
  Escenario: Registrar una única entrada de Inicio por proyecto con la orden pública
    Dado Windows con usuario sin privilegios de administrador y carpeta Inicio de usuario simulada vacía
    Y dos proyectos temporales distintos Proyecto Uno y Proyecto Dos, ambos con Telegram habilitado
    Y cada proyecto tiene token ficticio en su .env e ID permitido 111 y no tiene gateway activo
    Y entorno TELEGRAM_* aislado y restaurado al terminar, transporte sin red y lanzador simulado
    Cuando ejecuto adevv telegram --autoarranque on dos veces desde la raíz de Proyecto Uno y una desde Proyecto Dos
    Entonces las tres órdenes terminan con código cero e informan autoarranque registrado para su proyecto
    Y hay exactamente dos entradas distintas, una por proyecto, sin requerir elevación
    Y cada entrada solicita adevv telegram --fondo desde la raíz de su proyecto sin ventana visible
    Y ninguna entrada contiene rutas al almacén de versiones de Adevv

  @T-ADV-0024 @CA-M-1
  Escenario: Consultar y quitar la entrada propia conservando la ajena
    Dado Windows con carpeta Inicio simulada y entradas registradas para Proyecto Uno y Proyecto Dos
    Y los proyectos son temporales, los procesos están simulados y no se usa el Inicio real
    Cuando ejecuto adevv telegram --autoarranque estado desde la raíz de Proyecto Uno
    Entonces termina con código cero e informa autoarranque registrado para Proyecto Uno sin modificar entradas
    Cuando ejecuto adevv telegram --autoarranque off desde la raíz de Proyecto Uno
    Entonces termina con código cero e informa autoarranque no registrado para Proyecto Uno
    Y la entrada de Proyecto Uno ha desaparecido y la de Proyecto Dos conserva exactamente su contenido
    Cuando ejecuto adevv telegram --autoarranque estado desde la raíz de Proyecto Uno
    Entonces termina con código cero e informa autoarranque no registrado para Proyecto Uno sin modificar entradas
    Cuando ejecuto adevv telegram --autoarranque off otra vez desde la raíz de Proyecto Uno
    Entonces termina con código cero, sigue informando autoarranque no registrado y conserva intacta la entrada de Proyecto Dos

  @T-ADV-0024 @CA-M-1 @CA-M-2
  Esquema del escenario: Iniciar el gateway con la sesión del usuario sin administrador
    Dado Windows con usuario sin privilegios de administrador y carpeta Inicio de usuario simulada vacía
    Y proyecto temporal Proyecto Uno con Telegram habilitado, sin gateway activo y token local token-local-ficticio
    Y IDs locales <ids_locales>, IDs ambientales <ids_ambientales> y ningún token ambiental
    Y AUSENTE significa clave no definida, entorno TELEGRAM_* aislado y restaurado incluso ante fallos
    Y transporte sin red y lanzador estable adevv simulado disponible y exitoso
    Cuando ejecuto adevv telegram --autoarranque on desde la raíz de Proyecto Uno
    Y simulo un inicio de sesión ejecutando su entrada de Inicio
    Entonces se solicita exactamente una vez adevv telegram --fondo desde la raíz absoluta de Proyecto Uno
    Y el lanzamiento es sin ventana visible y no requiere elevación ni rutas al almacén de versiones
    Y la entrada termina con código cero sin programar reintentos
    Ejemplos:
      | ids_locales | ids_ambientales |
      | 111 | AUSENTE |
      | AUSENTE | 222 |

  @T-ADV-0024 @CA-M-3
  Esquema del escenario: Terminar un arranque inválido con diagnóstico de su causa
    Dado Windows y una entrada previamente registrada para el proyecto temporal Proyecto Uno en una carpeta Inicio simulada
    Y proyecto <proyecto>, token local <local>, token ambiental <ambiental>, IDs locales <ids_locales> e IDs ambientales <ids_ambientales>
    Y AUSENTE significa clave no definida y el entorno TELEGRAM_* está aislado y se restaura incluso ante fallos
    Y Telegram está habilitado, sin gateway activo, con procesos simulados y transporte sin red
    Cuando simulo un inicio de sesión ejecutando su entrada de Inicio una vez
    Entonces el intento termina con código distinto de cero y deja un diagnóstico observable que identifica <motivo>
    Y no inicia escucha ni un proceso de gateway ni reserva PID ni programa reintentos
    Ejemplos:
      | proyecto | local | ambiental | ids_locales | ids_ambientales | motivo |
      | eliminado tras registrar | AUSENTE | AUSENTE | AUSENTE | AUSENTE | proyecto inexistente |
      | existente | AUSENTE | AUSENTE | 111 | AUSENTE | credenciales incompletas |
      | existente | AUSENTE | token-entorno-ficticio | AUSENTE | 222 | token del entorno solo para avisos; se requiere token en el .env del proyecto |
      | existente | token-local-ficticio | AUSENTE | AUSENTE | AUSENTE | credenciales incompletas |

  @T-ADV-0024 @CA-M-4
  Escenario: Rechazar la activación fuera de Windows sin modificar el sistema
    Dado un sistema no Windows con proyecto temporal y carpeta de arranque simulada con una entrada ajena
    Y procesos simulados y transporte sin red
    Cuando ejecuto adevv telegram --autoarranque on desde la raíz del proyecto
    Entonces termina con código distinto de cero e informa que el autoarranque no está soportado en este sistema
    Y la carpeta conserva exactamente sus entradas y contenidos y no se solicita ningún proceso ni registro de autoarranque
