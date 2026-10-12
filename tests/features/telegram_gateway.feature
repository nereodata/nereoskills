# language: es
@telegram @gateway
Característica: Gateway de Telegram para nereoskills
  Como desarrollador u operador del sistema
  Quiero interactuar con nereoskills mediante Telegram
  Para registrar tareas o bugs, consultar el estado del backlog y recibir alertas de orquestación de forma remota

  @CA-M-1
  Esquema del escenario: Rechazar comandos de usuarios no autorizados sin modificar el sistema
    Dado que el gateway está configurado con usuarios autorizados "12345,67890"
    Cuando se recibe el mensaje "<mensaje>" del usuario no autorizado con ID "99999"
    Entonces el gateway ignora la petición sin enviar ninguna respuesta
    Y no se crea ni modifica ningún archivo en "docs/plan/"

    Ejemplos:
      | mensaje                                |
      | /estado                                |
      | /status                                |
      | /tarea Intento de escritura maliciosa  |
      | /bug Falso reporte no autorizado       |

  @CA-M-2
  Escenario: Registro de nueva tarea con versión activa
    Dado que el usuario autorizado "12345" envía el mensaje "/tarea Implementar vista resumen"
    Y la versión activa en el proyecto es "v0.2.0"
    Y el último ID de tarea existente es "T-WKF-0002"
    Cuando el gateway procesa el comando de tarea
    Entonces se crea el archivo "docs/plan/tasks/T-WKF-0003-implementar-vista-resumen.md"
    Y la tarea tiene estado "planned" y versión "v0.2.0"
    Y el gateway responde con el mensaje "Tarea registrada: T-WKF-0003 - Implementar vista resumen"

  @CA-M-2
  Escenario: Registro de nueva tarea sin versión activa
    Dado que el usuario autorizado "12345" envía el mensaje "/tarea Refactorizar utilidades"
    Y no hay ninguna versión activa en el proyecto
    Y el último ID de tarea existente es "T-WKF-0002"
    Cuando el gateway procesa el comando de tarea
    Entonces se crea el archivo "docs/plan/tasks/T-WKF-0003-refactorizar-utilidades.md"
    Y la tarea tiene estado "backlog" y versión ""
    Y el gateway responde con el mensaje "Tarea registrada: T-WKF-0003 - Refactorizar utilidades"

  @CA-M-2
  Escenario: Registro de nuevo bug con versión activa
    Dado que el usuario autorizado "12345" envía el mensaje "/bug Error 500 al listar métricas"
    Y la versión activa en el proyecto es "v0.2.0"
    Y el último ID de bug existente es "B-WKF-0001"
    Cuando el gateway procesa el comando de bug
    Entonces se crea el archivo "docs/plan/bugs/B-WKF-0002-error-500-al-listar-metricas.md"
    Y el bug tiene estado "planned" y versión "v0.2.0"
    Y el gateway responde con el mensaje "Bug registrado: B-WKF-0002 - Error 500 al listar métricas"

  @CA-M-2
  Escenario: Registro de nuevo bug sin versión activa
    Dado que el usuario autorizado "12345" envía el mensaje "/bug Fallo tipográfico en menú"
    Y no hay ninguna versión activa en el proyecto
    Y el último ID de bug existente es "B-WKF-0001"
    Cuando el gateway procesa el comando de bug
    Entonces se crea el archivo "docs/plan/bugs/B-WKF-0002-fallo-tipografico-en-menu.md"
    Y el bug tiene estado "backlog" y versión ""
    Y el gateway responde con el mensaje "Bug registrado: B-WKF-0002 - Fallo tipográfico en menú"

  @CA-M-2
  Esquema del escenario: Validación de argumentos vacíos en comandos de ingesta
    Dado que el usuario autorizado "12345" envía el mensaje "<comando>"
    Cuando el gateway procesa el mensaje
    Entonces el gateway no crea ningún archivo en "docs/plan/"
    Y responde con el mensaje de uso "<respuesta_uso>"

    Ejemplos:
      | comando | respuesta_uso                                  |
      | /tarea  | Uso: /tarea <título descriptivo de la tarea>  |
      | /bug    | Uso: /bug <descripción del error detectado>    |

  @CA-M-3
  Esquema del escenario: Consulta de estado con tarea en curso mediante /estado y su alias /status
    Dado que la versión activa del proyecto es "v0.2.0"
    Y la tarea "T-WKF-0001" con título "Estrategia de ramas" tiene estado "completed"
    Y la tarea "T-WKF-0002" con título "Gateway Telegram" tiene estado "in_progress"
    Y la tarea "T-WKF-0003" con título "Botones interactivos" tiene estado "backlog"
    Cuando el usuario autorizado "12345" envía el comando "<comando>"
    Entonces el gateway responde con un mensaje en Markdown que contiene:
      """
      *Versión activa:* `v0.2.0`
      *En curso:* `T-WKF-0002` - Gateway Telegram
      *Pendientes (1):*
      - `T-WKF-0003`: Botones interactivos
      """

    Ejemplos:
      | comando |
      | /estado |
      | /status |

  @CA-M-3
  Escenario: Consulta de estado cuando no hay tarea en curso
    Dado que la versión activa del proyecto es "v0.2.0"
    Y la tarea "T-WKF-0001" con título "Estrategia de ramas" tiene estado "completed"
    Y no hay ninguna tarea con estado "in_progress"
    Y la tarea "T-WKF-0002" con título "Gateway Telegram" tiene estado "planned"
    Cuando el usuario autorizado "12345" envía el comando "/estado"
    Entonces el gateway responde con un mensaje en Markdown que contiene:
      """
      *Versión activa:* `v0.2.0`
      *En curso:* Ninguna
      *Pendientes (1):*
      - `T-WKF-0002`: Gateway Telegram
      """

  @CA-M-4
  Escenario: Notificación saliente exitosa a chats autorizados
    Dado que el gateway tiene configurados los chats autorizados "12345,67890"
    Cuando el orquestador emite la notificación "Hito v0.2 completado con éxito"
    Entonces la función de notificación devuelve verdadero
    Y se despacha un mensaje con texto "📢 Hito v0.2 completado con éxito" a los chats "12345" y "67890"

  @CA-M-4
  Escenario: Resiliencia ante fallos de conexión en notificaciones salientes
    Dado que el gateway tiene configurados los chats autorizados "12345,67890"
    Y el servicio de la API de Telegram no se encuentra accesible o responde con error
    Cuando el orquestador emite la notificación "Alerta de sistema"
    Entonces la función de notificación devuelve falso sin lanzar ninguna excepción
    Y se registra un aviso de nivel WARNING con el mensaje "Fallo al enviar notificación a Telegram: Alerta de sistema"
