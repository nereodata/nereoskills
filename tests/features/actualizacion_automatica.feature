# language: es
Característica: F-03 · Actualización automática de versiones publicadas
  Como desarrollador u operador de proyectos con agentes de IA
  Quiero que una versión publicada se instale automáticamente en la siguiente orden adevv
  Para mantener el sistema al día sin romper bucles ni gateways en marcha y sin demoras en la red

  @CA-F03-01 @RF-F03-01 @RF-F03-04 @RF-F03-06 @RF-F03-07
  Esquema del escenario: Ventana de comprobación
    Dado Adevv 0.1.0 instalado y publicadas "<publicadas>"
    Y el estado de actualización "<estado>"
    Y en marcha "<en marcha>"
    Cuando a las "<ahora>" ejecuto "adevv orquestar --estado" fuera de un bucle y con red
    Entonces el resultado de la comprobación es "<resultado>"

    Ejemplos:
      | publicadas  | estado                                              | ahora     | en marcha | resultado |
      | 0.2.0       | última contada lun 09:00                            | mar 08:59 | nada      | ESPERA    |
      | 0.2.0       | última contada lun 09:00                            | mar 09:00 | nada      | APLICADA  |
      | 0.2.0       | último SIN_RED lun 10:00, última contada dom 09:00  | lun 10:59 | nada      | ESPERA    |
      | 0.2.0       | último SIN_RED lun 10:00, última contada dom 09:00  | lun 11:00 | nada      | APLICADA  |
      | 0.2.0       | fallida 0.2.0, última contada lun 10:00             | lun 15:59 | nada      | ESPERA    |
      | 0.2.0       | fallida 0.2.0, última contada lun 10:00             | mar 10:00 | nada      | AL_DIA    |
      | 0.2.0 0.2.1 | fallida 0.2.0, última contada lun 10:00             | mar 10:00 | nada      | APLICADA  |
      | 0.2.0       | aplazada 0.2.0, aviso lun 09:00                     | lun 12:00 | bucle     | APLAZADA  |
      | 0.2.0       | aplazada 0.2.0, aviso lun 09:00                     | lun 12:00 | nada      | APLICADA  |
      | 0.2.0       | aplazada 0.2.0, aviso lun 09:00                     | lun 12:00 | gateway   | APLICADA  |

  @CA-F03-02 @RF-F03-07
  Escenario: Actualización aplicada al lanzar
    Dado Adevv 0.1.0 instalado, la 0.2.0 publicada, sin bucles en marcha y sin comprobación en 24 h
    Cuando ejecuto "adevv orquestar --estado"
    Entonces la salida de errores muestra "Adevv actualizado de 0.1.0 a 0.2.0. Reinicia las sesiones abiertas de los arneses para usar las skills nuevas."
    Y el estado lo calcula la 0.2.0
    Y "adevv --version" informa 0.2.0 con los destinos sincronizados con la 0.2.0

  @CA-F03-03 @RF-F03-06
  Escenario: Aplazada con un bucle en marcha en otro proyecto
    Dado Adevv 0.1.0 instalado, la 0.2.0 publicada, sin comprobación en 24 h y un bucle en marcha en "C:\SW\Afinn"
    Cuando ejecuto "adevv orquestar --estado" en otro proyecto
    Entonces no se instala nada
    Y la salida de errores muestra "Adevv 0.2.0 disponible; se aplicará cuando no haya bucles en marcha: bucle en C:\SW\Afinn."
    Cuando el bucle de Afinn termina y ejecuto otra orden "adevv" con red
    Entonces se aplica la 0.2.0 sin esperar 24 horas

  @CA-F03-04 @RF-F03-06
  Escenario: Un bucle anterior a la migración también bloquea
    Dado un bucle en marcha lanzado con "python .agents/skills/orquestar/orquestar.py" en un proyecto
    Y la 0.2.0 publicada
    Cuando ejecuto "adevv actualizar"
    Entonces no se instala nada y el mensaje nombra ese bucle

  @CA-F03-05 @RF-F03-08
  Escenario: Un gateway abierto no impide actualizar ni se rompe
    Dado Adevv 0.1.0 instalado, la 0.2.0 publicada y un gateway en marcha en "C:\SW\Adevv"
    Cuando ejecuto "adevv actualizar"
    Entonces queda instalada la 0.2.0
    Y el gateway sigue respondiendo con la 0.1.0
    Y el mensaje incluye "Reinicia el gateway en C:\SW\Adevv."

  @CA-F03-06 @RF-F03-02 @RF-F03-03
  Escenario: Sin red o sin credenciales
    Dado que el origen no responde en 5 segundos
    Cuando ejecuto "adevv orquestar --estado"
    Entonces la orden sigue con la versión instalada tras esperar como mucho 5 segundos a la red
    Y no aparece ninguna petición de credenciales

  @CA-F03-07 @RF-F03-02
  Escenario: Solo cuentan las versiones publicadas
    Dado Adevv 0.1.0 instalado
    Y en el origen las etiquetas "v0.2.0-rc1", "v0.3.0" ligera y "v0.2.1" anotada
    Cuando ejecuto "adevv actualizar"
    Entonces se instala la 0.2.1

  @CA-F03-08 @RF-F03-07
  Escenario: Fallo de instalación
    Dado Adevv 0.1.0 instalado y la 0.2.0 publicada pero imposible de instalar
    Cuando ejecuto "adevv orquestar --fondo"
    Entonces la salida de errores muestra "No se pudo actualizar a 0.2.0: <causa>. Sigues con la 0.1.0. Reintenta con `adevv actualizar`."
    Y el bucle se lanza con la 0.1.0 después del intento
    Y "adevv --version" informa 0.1.0 con los destinos sincronizados

  @CA-F03-09 @RF-F03-07
  Escenario: La etiqueta no coincide con la versión del paquete
    Dado Adevv 0.1.0 instalado y la etiqueta anotada "v0.3.0" cuyo paquete declara 0.2.9
    Cuando ejecuto "adevv actualizar"
    Entonces el resultado es "FALLIDA" con la causa "la versión instalada no es 0.3.0"
    Y sigue instalada la 0.1.0

  @CA-F03-10 @RF-F03-09
  Escenario: Instalada pero un arnés sin sincronizar
    Dado que al aplicar la 0.2.0 Codex tiene bloqueado un archivo de su destino
    Cuando termina la actualización
    Entonces la versión instalada es 0.2.0 y Codex queda "DESFASADO"
    Y el mensaje añade "Arneses sin sincronizar: Codex: <causa>."

  @CA-F03-11 @RF-F03-05
  Escenario: Actualización desactivada
    Dado la actualización automática desactivada en la configuración de usuario
    Cuando ejecuto cualquier orden "adevv" que no sea "adevv actualizar"
    Entonces no se consulta la red

  @CA-F03-12 @RF-F03-11 @RF-F03-10
  Escenario: Volver atrás y reactivar
    Dado Adevv 0.3.0 instalado, sin bucles en marcha y publicadas la 0.2.1 y la 0.3.0
    Cuando ejecuto "adevv actualizar 0.2.1"
    Entonces queda instalada la 0.2.1
    Y el mensaje dice "Actualización automática desactivada; `adevv actualizar` la reactiva."
    Y 24 horas después una orden "adevv" no consulta la red
    Cuando se publica la 0.3.1 y ejecuto "adevv actualizar"
    Entonces se instala la 0.3.1 y la actualización automática queda activa

  @CA-F03-13 @RF-F03-11
  Escenario: Volver atrás con un bucle en marcha
    Dado Adevv 0.3.0 instalado, publicadas la 0.2.1 y la 0.3.0, y un bucle en marcha en "C:\SW\Afinn"
    Cuando ejecuto "adevv actualizar 0.2.1"
    Entonces nada cambia y el mensaje es "No se puede instalar 0.2.1 con bucles en marcha: bucle en C:\SW\Afinn."

  @CA-F03-14 @RF-F03-12
  Escenario: Versión inexistente
    Dado Adevv 0.1.0 instalado y las versiones publicadas 0.1.0 y 0.2.0
    Cuando ejecuto "adevv actualizar 0.9.0"
    Entonces nada cambia y el mensaje es "0.9.0 no es una versión publicada. Publicadas: 0.2.0, 0.1.0."

  @CA-F03-15 @RF-F03-01
  Escenario: Dentro de un paso del bucle no se comprueba
    Dado un paso de un bucle en marcha
    Cuando ese paso ejecuta "adevv orquestar --verificar"
    Entonces no se consulta la red ni se instala nada

  @CA-F03-16 @RF-F03-13
  Escenario: Los avisos no alteran la salida de la orden
    Dado que una orden "adevv orquestar --estado" aplica una actualización
    Entonces el aviso aparece solo en la salida de errores
    Y la salida estándar es la del estado
