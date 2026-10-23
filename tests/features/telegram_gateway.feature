# language: es
@telegram @gateway
Característica: Gateway de Telegram de Adevv
  Como persona que lleva un producto con el orquestador
  Quiero consultar el estado y apuntar tareas o bugs desde Telegram
  Para seguir el trabajo sin estar delante y sin interferir con el bucle

  Antecedentes:
    Dado que los usuarios autorizados son "12345,67890"
    Y que el prefijo del proyecto es "ADV" y la última tarea es "T-ADV-0002"

  Esquema del escenario: Ignorar a usuarios no autorizados sin tocar nada
    Cuando el usuario "99999" envía "<mensaje>"
    Entonces no recibe respuesta
    Y no cambia nada en "docs/plan/" ni en el buzón

    Ejemplos:
      | mensaje         |
      | /estado         |
      | /tarea Intento  |
      | /bug Falso      |

  Escenario: Registrar una tarea sin el bucle en marcha
    Dado que el bucle no está en marcha
    Cuando el usuario "12345" envía "/tarea Exportar informe"
    Entonces se crea "docs/plan/tasks/T-ADV-0003-exportar-informe.md" con estado "backlog" y sin versión
    Y la tarea no declara "depende_de"
    Y se commitea solo ese fichero
    Y recibe "Registrada T-ADV-0003: Exportar informe (backlog, sin versión)."

  Escenario: Apuntar una tarea con el bucle en marcha
    Dado que el bucle está en marcha
    Cuando el usuario "12345" envía "/tarea Exportar informe"
    Entonces no cambia nada en "docs/plan/"
    Y la petición queda en el buzón
    Y recibe que se registrará al terminar el paso en curso

  Escenario: El bucle registra el buzón entre pasos
    Dado que el buzón tiene una tarea y un bug
    Cuando el bucle empieza el siguiente paso
    Entonces crea la tarea y el bug sin versión con los IDs siguientes
    Y los commitea en un commit que no incluye otros cambios del árbol
    Y avisa a los usuarios autorizados de cada ID registrado

  Escenario: Una tarea sin versión no altera la versión en curso
    Dado que hay una tarea en "backlog" sin versión y sin "depende_de"
    Cuando el bucle calcula el siguiente paso
    Entonces no lanza "calcular-dependencias" ni la trabaja
    Pero en cuanto tiene versión, lanza "calcular-dependencias"

  Escenario: Consultar el estado
    Dado que el bucle está en marcha y "T-ADV-0002" de "v0.1.0" está en curso
    Cuando el usuario "12345" envía "/estado"
    Entonces recibe que el bucle está en marcha, la fase, "0/1 cerradas · en curso T-ADV-0002" y las altas por registrar

  Escenario: Un mensaje que falla no detiene la escucha
    Dado que procesar un mensaje lanza un error
    Cuando llegan ese mensaje y otro válido
    Entonces el primero recibe que no se pudo procesar
    Y el segundo recibe su respuesta

  @CA-M-1
  Escenario: Conversación libre con el modelo del proyecto
    Dado que el usuario "12345" envía un mensaje sin comando "Hola, ¿de qué trata este proyecto?"
    Cuando el gateway procesa el mensaje
    Entonces invoca al modelo configurado para el gateway
    Y guarda el identificador de sesión asociado a "12345"
    Y el usuario recibe la respuesta textual del asistente

  @CA-M-1
  Escenario: Continuidad de hilo entre mensajes del mismo usuario
    Dado que el usuario "12345" tiene una sesión previa "sess-prev-001"
    Cuando el usuario envía "Y qué tareas están abiertas?"
    Entonces el gateway reanuda la sesión "sess-prev-001"
    Y actualiza el ID de sesión si cambia

  @CA-M-1
  Escenario: Fallback a sesión nueva si la reanudación falla
    Dado que el usuario "12345" tiene una sesión previa inválida "sess-invalida"
    Cuando el usuario envía "Explícame el flujo"
    Y la reanudación con "sess-invalida" devuelve error
    Entonces el gateway reintenta automáticamente iniciando una sesión nueva
    Y guarda el nuevo identificador de sesión

  @CA-M-2
  Escenario: Reiniciar el hilo de conversación con /nuevo o /reset
    Dado que el usuario "12345" tiene una sesión guardada
    Cuando el usuario "12345" envía "/nuevo"
    Entonces se elimina la sesión guardada de "12345"
    Y recibe confirmación de que el hilo de conversación se ha reiniciado

  @CA-M-3
  Escenario: Contexto seguro cuando el bucle está en marcha
    Dado que el bucle está en marcha con "orquestar.pid"
    Cuando el usuario "12345" envía una consulta libre
    Entonces el prompt enviado al modelo advierte de no modificar ni commitear ficheros rastreados
    Y sugiere usar apuntar tareas o bugs si se desea registrar trabajo

  @T-ADV-0014 @CA-M-1
  Escenario: Agentes efectivos compartidos entre CLI y Telegram
    Dado un paso task-dev de dificultad dificil con ajustes por paso y reservas heredadas
    Y dos rechazos que activan la escalada de Artemisa
    Cuando consulto --estado o /estado
    Entonces veo la dificultad, Artemisa en escalada y Hades con su arnés, modelo, esfuerzo y reservas efectivos
    Y para un paso de planificación veo Atenea en lugar de Artemisa

  @T-ADV-0014 @CA-M-2
  Escenario: Consumo reciente y cuota con vencimiento conocido
    Dado que son las 12:00 y el modelo codex/m1 consumió 100 tokens de entrada, 20 de caché y 30 de salida a las 08:00
    Y consumió 900 tokens a las 06:59 que quedan fuera de las últimas 5 horas
    Y a las 11:50 agotó cuota durante 1800 segundos antes de conmutar a reserva
    Cuando consulto --estado o /estado
    Entonces veo codex/m1 con 150 tokens en 5 h y agotado hasta las 12:20 con 20 min restantes
    Y no sumo de nuevo los tokens de razonamiento incluidos en salida

  @T-ADV-0014 @CA-M-2
  Escenario: Ausencia de evidencia y esperas globales
    Dado que una cuota ya venció y hay modelos configurados sin métricas
    Y existe una espera global hasta las 12:15 cuando son las 12:00
    Cuando consulto --estado o /estado
    Entonces veo la espera global y 15 min restantes sin atribuirla a un modelo desconocido
    Y los modelos sin evidencia indican sin agotamiento registrado y cero tokens
    Y un estado sin paso ni métricas sigue siendo consultable

  @T-ADV-0015 @CA-M-1
  Esquema del escenario: Solicitar la parada del bucle
    Dado que existe la marca de bucle en marcha
    Cuando el usuario autorizado envía "<comando>"
    Entonces se solicita la parada y se confirma que terminará al acabar el paso en curso
    Y el bucle conserva su marca de ejecución y sus datos
    Ejemplos:
      | comando |
      | /parar  |
      | /stop   |

  @T-ADV-0015 @CA-M-1
  Escenario: Parar un bucle ya parado
    Dado que no hay marca de ejecución
    Cuando el usuario autorizado envía "/parar"
    Entonces recibe que el bucle ya está parado sin crear una solicitud de parada

  @T-ADV-0015 @CA-M-2
  Esquema del escenario: Lanzar el bucle desde Telegram
    Dado que no hay marca de ejecución y el siguiente paso previsto es task-dev para T-ADV-0015
    Cuando el usuario autorizado envía "<comando>"
    Entonces se lanza el bucle en segundo plano para este proyecto
    Y recibe confirmación del lanzamiento y el siguiente paso previsto
    Ejemplos:
      | comando        |
      | /lanzar        |
      | /run@AdevvBot   |

  @T-ADV-0015 @CA-M-2
  Escenario: Evitar otro lanzamiento si el bucle está en marcha
    Dado que existe la marca de bucle en marcha
    Cuando el usuario autorizado envía "/run"
    Entonces recibe que ya está en marcha y no se lanza otro proceso

  @T-ADV-0015 @CA-M-3
  Escenario: Consultar métricas de la última versión por defecto
    Dado que hay tareas y métricas en v0.3 y v0.4
    Cuando el usuario autorizado envía "/metricas"
    Entonces recibe solo v0.4 con tiempo real, tokens de desarrollo y Hades y coste estimado USD por tarea
    Y no cambia el estado del bucle ni las métricas

  @T-ADV-0015 @CA-M-3
  Escenario: Seleccionar versiones y tratar errores de consulta
    Cuando el usuario autorizado envía "/metrics v0.3,v0.4"
    Entonces recibe las dos versiones con el mismo cálculo de la consulta CLI
    Pero si el filtro es inválido recibe una explicación del filtro
    Y si el registro está corrupto recibe el error con número de línea sin resultados parciales
    Y si no hay tareas ni registros recibe que no hay métricas

  @T-ADV-0015 @CA-M-4
  Escenario: Ayuda del control remoto
    Cuando el usuario autorizado envía "/ayuda"
    Entonces ve /lanzar y /run, /parar y /stop, /metricas y /metrics con filtro opcional por defecto ultima

  @T-ADV-0015
  Escenario: Proteger el control y las métricas
    Cuando un usuario no autorizado envía /lanzar, /parar o /metricas
    Entonces no obtiene respuesta, no se ejecuta ningún comando ni se lee o escribe el proyecto
