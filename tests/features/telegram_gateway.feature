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
