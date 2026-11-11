# language: es
Característica: F-05 Publicación de versiones sin contenido interno

  @CA-F05-01 @RF-F05-01 @RF-F05-03
  Escenario: El paquete no lleva contenido interno
    Dado el repositorio de Adevv con "docs/plan/", "tests/", "task_config.yaml", "orchestration.json", "orquestar.log" y la junction ".agents" en el árbol
    Cuando se construye el paquete de la versión
    Entonces su contenido solo tiene archivos de "skills/", "agents/", "workflows/" y el código del paquete
    Y la prueba de contenido del paquete pasa

  @CA-F05-02 @RF-F05-03
  Escenario: La prueba detecta contenido prohibido
    Dado un archivo "skills/orquestar/__pycache__/orquestar.cpython-312.pyc" versionado
    Cuando ejecuto la suite de Adevv
    Entonces la prueba de contenido del paquete falla nombrando ese archivo

  @CA-F05-03 @RF-F05-05
  Escenario: Versión del paquete distinta de la etiqueta
    Dado el repositorio de Adevv con la versión del paquete 0.1.0
    Cuando intento publicar "v0.2.0"
    Entonces la publicación falla con "La versión del paquete (0.1.0) no coincide con v0.2.0."
    Y no se crea ninguna etiqueta

  @CA-F05-04 @RF-F05-05
  Escenario: Una etiqueta publicada no se mueve
    Dado "v0.1.0" ya publicada en el origen
    Cuando intento publicar "v0.1.0" de nuevo
    Entonces la publicación falla con "v0.1.0 ya está publicada: publica v0.1.1."

  @CA-F05-05 @RF-F05-06 @RF-F05-07
  Escenario: Publicación correcta
    Dado el repositorio de Adevv en "release/v0.1" abierta con "/start-version v0.1"
    Cuando se publica la versión con "/release" sin editar a mano la versión del paquete
    Entonces la versión del paquete y "project.version" son 0.1.0
    Y existe la etiqueta anotada "v0.1.0" en un commit de "main" del origen
    Y una máquina con Adevv instalado la considera versión publicada

  # B-ADV-0037: CA1 y CA5. Cada fila se ejecuta con el resto del cierre válido.
  @B-ADV-0037
  Esquema del escenario: Revisión formal obligatoria en cada entrada de cierre
    Dado un <tipo> maestro completado con ID "<id>" en v1.1.2
    Y su informe formal de Hades está <informe>
    Y las pruebas están verdes y los demás requisitos de cierre están satisfechos
    Cuando intento <entrada> v1.1.2
    Entonces la operación se rechaza e identifica "<id>" y el motivo "<motivo>"
    Y indica obtener la revisión mediante "revisar-tarea" y volver a validar
    Y no declara cerrada la versión ni crea etiquetas ni publica main

    Ejemplos:
      | tipo  | id         | informe   | entrada                           | motivo             |
      | tarea | T-ADV-0100 | ausente   | validar el preflight local        | informe ausente    |
      | tarea | T-ADV-0100 | RECHAZADO | validar el preflight local        | informe rechazado  |
      | bug   | B-ADV-0100 | ausente   | validar el preflight local        | informe ausente    |
      | bug   | B-ADV-0100 | RECHAZADO | validar el preflight local        | informe rechazado  |
      | tarea | T-ADV-0100 | ausente   | cerrar por Telegram               | informe ausente    |
      | tarea | T-ADV-0100 | RECHAZADO | cerrar por Telegram               | informe rechazado  |
      | bug   | B-ADV-0100 | ausente   | cerrar por Telegram               | informe ausente    |
      | bug   | B-ADV-0100 | RECHAZADO | cerrar por Telegram               | informe rechazado  |
      | tarea | T-ADV-0100 | ausente   | publicar mediante la API de release | informe ausente  |
      | tarea | T-ADV-0100 | RECHAZADO | publicar mediante la API de release | informe rechazado |
      | bug   | B-ADV-0100 | ausente   | publicar mediante la API de release | informe ausente  |
      | bug   | B-ADV-0100 | RECHAZADO | publicar mediante la API de release | informe rechazado |

  @B-ADV-0037
  Escenario: El diagnóstico enumera todos los IDs con revisión pendiente
    Dado T-ADV-0100 completada en v1.1.2 sin informe formal
    Y B-ADV-0100 completado en v1.1.2 con informe RECHAZADO
    Y B-ADV-0101 completado en v1.1.2 con informe APROBADO
    Cuando valido el preflight local de v1.1.2
    Entonces rechaza el cierre e identifica T-ADV-0100 por informe ausente y B-ADV-0100 por informe rechazado
    Y no incluye B-ADV-0101 entre los pendientes
    Y no declara cerrada la versión ni crea etiquetas ni publica main

  # B-ADV-0037: CA2 y CA5. Indisponibilidad y recuperación son acciones observadas.
  @B-ADV-0037
  Escenario: Hades indisponible deja una revisión pendiente aunque las pruebas pasen
    Dado B-ADV-0100 completado en v1.1.2 sin informe formal y con pruebas verdes
    Y el perfil de Hades no se puede ejecutar por falta de cuota
    Cuando el orquestador intenta obtener su revisión formal con "revisar-tarea"
    Y consulto el estado e intento validar el cierre de v1.1.2
    Entonces el estado y el diagnóstico de cierre identifican B-ADV-0100 como revisión pendiente por Hades sin cuota
    Y indican recuperar la disponibilidad de Hades, reanudar "revisar-tarea" y volver a validar el cierre
    Y no dan la revisión por aprobada por las pruebas verdes
    Y no declaran cerrada la versión ni crean etiquetas ni publican main

  @B-ADV-0037
  Escenario: Recuperar Hades exige obtener el informe y revalidar
    Dado B-ADV-0100 completado en v1.1.2 pendiente de revisión por Hades sin cuota
    Y los demás requisitos de cierre están satisfechos y las pruebas están verdes
    Cuando Hades recupera cuota y reanudo "revisar-tarea" para B-ADV-0100
    Y Hades emite el informe formal APROBADO para B-ADV-0100
    Y vuelvo a ejecutar el preflight local de v1.1.2
    Entonces el preflight permite continuar el cierre sin revisión pendiente para B-ADV-0100
    Y obtener el informe por sí solo no ha creado etiquetas ni publicado main ni declarado cerrada la versión

  # B-ADV-0037: excepción de revisión sin cambios de código.
  @B-ADV-0037
  Esquema del escenario: N/A requiere justificación de ausencia de código
    Dado B-ADV-0100 completado en v1.1.2 con informe formal N/A de Hades
    Y el informe contiene "<justificacion>"
    Y los demás requisitos de cierre están satisfechos y las pruebas están verdes
    Cuando valido el preflight local de v1.1.2
    Entonces la revisión de B-ADV-0100 <resultado>
    Y no se crean etiquetas ni se publica main ni se declara cerrada la versión al validar

    Ejemplos:
      | justificacion                                           | resultado                                           |
      | Motivo: sin cambios de código; solo documentación.       | deja de bloquear el cierre                          |
      |                                                         | bloquea el cierre por N/A sin justificación          |

  # B-ADV-0037: CA4 y CA5; las métricas conservan su agrupación histórica.
  @B-ADV-0037
  Escenario: Dos parches mantienen sus tareas y revisiones separadas
    Dado B-ADV-0032 completado en v1.1.1 con revisión rechazada
    Y B-ADV-0100 planificado en v1.1.2 y solo la rama hotfix/v1.1.2 abierta
    Cuando el orquestador selecciona el siguiente paso
    Entonces selecciona B-ADV-0100 sin recuperar la revisión de B-ADV-0032
    Y al validar v1.1.2 el informe rechazado de B-ADV-0032 no figura como impedimento de ese parche

  @B-ADV-0037
  Escenario: La versión sin parche equivale al parche cero
    Dado T-ADV-0100 completada en v1.1 sin informe formal
    Cuando valido el preflight local de v1.1.0 con los demás requisitos satisfechos
    Entonces el cierre se rechaza identificando T-ADV-0100 por informe ausente
