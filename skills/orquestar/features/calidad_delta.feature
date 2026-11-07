# language: es
@orquestar @calidad @T-ADV-0022
Característica: Formato y lint del delta de una tarea
  Como usuario del desarrollo orquestado
  Quiero que cada tarea compruebe la calidad de sus ficheros antes de completarse
  Para detectar fallos sin esperar a la suite de cierre de versión (Ref: T-ADV-0022)

  Escenario: Expandir los ficheros del delta sin ejecutar sus nombres
    Dado un delta con "src/con espacio.py" y "src/a;eco.py" modificados y "src/borrado.py" eliminado
    Y validation.lint contiene "herramienta {ficheros}"
    Cuando resuelvo el comando de lint de la tarea
    Entonces herramienta recibe exactamente dos argumentos de fichero "src/con espacio.py" y "src/a;eco.py"
    Y no se incluye "src/borrado.py" ni se ejecuta un comando adicional por el punto y coma

  Escenario: El delta incluye cambios confirmados y pendientes de la tarea
    Dado una base Git válida fijada antes de comenzar la tarea
    Y desde esa base se confirmó el cambio de "src/uno.py", hay cambios pendientes en "src/dos.py" y se añadió sin rastrear "src/tres.py"
    Y "src/sin_cambios.py" no ha cambiado desde la base
    Y validation.lint contiene "herramienta {ficheros}"
    Cuando resuelvo el comando de lint de la tarea respecto de esa base
    Entonces herramienta recibe una sola vez uno.py, dos.py y tres.py con sus rutas completas relativas al proyecto
    Y no recibe sin_cambios.py

  Escenario: La configuración explícita prevalece por etapa
    Dado validation.formato igual a "mi-formato --check {ficheros}"
    Y validation.lint igual a "mi-lint {ficheros}"
    Y package.json declara format:check con "prettier --check ." y lint con "eslint ."
    Y el único fichero del delta es "src/a.js"
    Cuando resuelvo formato y lint para la tarea
    Entonces los comandos son "mi-formato --check src/a.js" y "mi-lint src/a.js"
    Y no se ejecutan los scripts de package.json

  Esquema del escenario: Deducir únicamente scripts npm reconocidos y acotarlos al delta
    Dado que no hay configuración explícita de calidad ni configuración ruff
    Y package.json declara únicamente el script <script> con contenido <contenido>
    Y el delta contiene "src/a.js" y hay un fichero ajeno al delta "src/otro.js"
    Cuando resuelvo la calidad de la tarea
    Entonces el comando de <etapa> es <comando>
    Y no se pasan el punto ni src/otro.js como objetivos
    Y la otra etapa queda omitida con motivo visible
    Ejemplos:
      | script       | contenido          | etapa   | comando                   |
      | format:check | prettier --check . | formato | prettier --check src/a.js |
      | lint         | eslint .           | lint    | eslint src/a.js           |

  Escenario: Deducir ruff de su configuración
    Dado que no hay configuración explícita de calidad ni package.json
    Y pyproject.toml contiene una sección tool.ruff
    Y el delta contiene "src/a.py" y "notas.md"
    Cuando resuelvo la calidad de la tarea
    Entonces los comandos de comprobación son "ruff format --check src/a.py" y "ruff check src/a.py"
    Y el comando de escritura disponible es "ruff format src/a.py"
    Y ninguno incluye notas.md

  Escenario: Omitir herramientas no declaradas
    Dado un proyecto sin comandos explícitos, sin scripts npm y sin sección tool.ruff
    Cuando resuelvo la calidad de la tarea
    Entonces formato y lint se omiten sin error con motivo visible de ausencia de herramientas
    Y no se inventa un comando ni se instala una herramienta

  Escenario: Omitir un script no reconocible sin ejecutarlo sobre todo el proyecto
    Dado que no hay configuración explícita ni ruff
    Y package.json solo declara lint con "node scripts/calidad.js"
    Cuando resuelvo la calidad de la tarea
    Entonces lint se omite sin error con motivo visible de script no reconocible
    Y no se ejecuta "node scripts/calidad.js"

  Escenario: Un comando explícito sin marcador conserva su alcance declarado
    Dado validation.lint igual a "mi-lint --proyecto"
    Y el delta tiene ficheros existentes
    Cuando resuelvo el comando de lint
    Entonces se conserva exactamente "mi-lint --proyecto"
    Y se informa de que su alcance es el declarado y no está limitado por ficheros

  Escenario: La configuración explícita inválida no se convierte en omisión
    Dado validation.lint igual al número 123 en lugar de un comando
    Cuando resuelvo la calidad de la tarea
    Entonces se informa de un error identificando validation.lint
    Y no se deduce un comando alternativo ni se acredita calidad satisfactoria

  Escenario: Una base Git inexistente es un error
    Dado una tarea cuya base declarada es una referencia Git inexistente
    Cuando solicito comprobar su calidad
    Entonces se informa de que no se puede calcular el delta por esa base
    Y no se interpreta como delta vacío ni se acredita calidad satisfactoria

  Esquema del escenario: Omitir una etapa sin objetivos compatibles
    Dado una base Git válida y <contexto>
    Y <herramienta>
    Cuando solicito comprobar calidad del delta
    Entonces no se ejecuta ningún comando de calidad
    Y se informa de la omisión sin error por ausencia de objetivos compatibles
    Ejemplos:
      | contexto                                      | herramienta                                      |
      | ningún fichero cambiado                       | validation.lint contiene "mi-lint {ficheros}"     |
      | solo un fichero src/borrado.py eliminado       | pyproject.toml contiene tool.ruff                 |
      | solo el fichero notas.md modificado            | pyproject.toml contiene tool.ruff                 |

  Esquema del escenario: Corregir formato y completar cada flujo en verde
    Dado una ejecución de <flujo> con la implementación y las pruebas del triaje satisfactorias
    Y el delta tiene un fichero con formato incorrecto corregible por el formateador disponible
    Y tras corregirlo las comprobaciones de formato y lint devuelven cero
    Cuando el flujo intenta cerrar la tarea
    Entonces aplica el formateador en escritura sobre el delta antes de comprobar calidad
    Y comprueba formato y lint mediante --verificar sobre el contenido ya corregido
    Y solo después de esas comprobaciones satisfactorias permite status completed
    Ejemplos:
      | flujo     |
      | /task-dev |
      | /bug-fix  |

  Esquema del escenario: Comprobar sin inventar escritura cuando no está disponible
    Dado una ejecución de <flujo> con pruebas de triaje satisfactorias
    Y validation.formato declara un comprobador sin modo de escritura conocido o declarado
    Y formato y lint devuelven cero sobre el delta
    Cuando el flujo intenta cerrar la tarea
    Entonces ejecuta las comprobaciones mediante --verificar sin aplicar escritura
    Y permite status completed tras el resultado satisfactorio
    Ejemplos:
      | flujo     |
      | /task-dev |
      | /bug-fix  |

  Esquema del escenario: Un fallo de calidad impide completar cada flujo
    Dado una ejecución de <flujo> con pruebas del triaje satisfactorias
    Y el formato <formato> después de aplicar escritura si está disponible
    Y el lint <lint>
    Cuando el flujo intenta cerrar la tarea
    Entonces comprueba formato y lint mediante --verificar sobre el delta actual
    Y informa del fallo de <fallo> y mantiene la tarea sin completed
    Ejemplos:
      | flujo     | formato       | lint          | fallo   |
      | /task-dev | devuelve uno  | devuelve cero | formato |
      | /bug-fix  | devuelve uno  | devuelve cero | formato |
      | /task-dev | devuelve cero | devuelve uno  | lint    |
      | /bug-fix  | devuelve cero | devuelve uno  | lint    |

  Escenario: Reutilizar evidencia satisfactoria del mismo árbol y comando
    Dado que --verificar ya registró formato y lint satisfactorios para el árbol actual y los comandos del delta de la tarea
    Y no cambió el contenido del árbol, la base ni los comandos de la comprobación
    Cuando Hades inicia la revisión de código de esa tarea
    Entonces comprueba mediante --verificar formato y lint sin escritura
    Y reutiliza ambos resultados sin volver a ejecutar los comandos

  Esquema del escenario: Un cambio posterior invalida la evidencia anterior
    Dado que --verificar registró formato y lint satisfactorios para el árbol anterior
    Y <cambio> y el árbol resultante aún no tiene evidencia de calidad
    Cuando Hades inicia la revisión de código de la tarea
    Entonces solicita mediante --verificar formato y lint sin escritura sobre el árbol resultante
    Y se ejecutan los comandos y no se acredita el resultado con la evidencia del árbol anterior
    Ejemplos:
      | cambio                                                        |
      | se modifica el contenido de un fichero relevante del delta     |
      | el desarrollador aplica formato en escritura y cambia contenido |

  Esquema del escenario: Hades devuelve al desarrollador un fallo de calidad
    Dado una tarea en revisión con pruebas del triaje satisfactorias y sin evidencia de calidad válida
    Y el comando de <etapa> del delta devuelve uno
    Cuando Hades revisa el código de la tarea
    Entonces comprueba la calidad mediante --verificar sin modificar los ficheros
    Y registra un hallazgo de <etapa> para desarrollador con destino resolver
    Y no aprueba la revisión mientras persista ese fallo
    Ejemplos:
      | etapa   |
      | formato |
      | lint    |

  @T-ADV-0032 @CA-M-1 @CA-M-2
  Escenario: Registrar comprobaciones de calidad y release mostrando el plan explicable sin cobertura ficticia
    Dado un proyecto con task_config.yaml que declara formato "ruff format --check {ficheros}", pruebas "python -m unittest" obligatoria, seguridad obligatoria sin comando y tipado opcional sin comando
    Y package.json declara el script reconocido lint con "eslint ." y el árbol contiene "src/app.py" y "src/ui.js"
    Cuando solicito el plan y la validación de la puerta de release
    Entonces antes de ejecutar se muestra el plan con el alcance, el comando efectivo y el origen de cada comprobación
    Y formato figura con disponibilidad "configurado" y origen "task_config.yaml (validation.formato)"
    Y lint figura con disponibilidad "configurado" y origen "deducido de package.json (scripts.lint)"
    Y tipado figura con disponibilidad "ausente", resultado "sin_acreditar" y motivo "análisis opcional no configurado"
    Y seguridad figura con disponibilidad "ausente", resultado "sin_acreditar" y motivo "análisis obligatorio ausente"
    Y secretos, dependencias y builds figuran con disponibilidad "ausente" y resultado "sin_acreditar" sin inventar comandos ni suponer cobertura por el nombre de la suite
    Y la puerta de release queda en estado "fallido" porque la comprobación obligatoria "seguridad" carece de cobertura acreditada

  @T-ADV-0032 @CA-M-1
  Esquema del escenario: Rechazar configuraciones inválidas de comprobaciones y puertas sin ocultarlas como omisión
    Dado un proyecto cuyo task_config.yaml declara en <ubicacion> el valor inválido <valor>
    Cuando solicito planificar o ejecutar las comprobaciones del proyecto
    Entonces la operación devuelve código de error distinto de cero e identifica <ubicacion> en el mensaje de diagnóstico
    Y no se ejecuta ningún comando ni se acredita ninguna comprobación como aprobada u omitida
    Ejemplos:
      | ubicacion                      | valor               |
      | validation.tipado              | 404                 |
      | validation.seguridad.comando   | ""                  |
      | release.puertas                | "no-es-lista"       |
      | release.restricciones.publicar | "rol-invalido-999"  |

  @T-ADV-0032 @CA-M-2 @CA-M-3
  Escenario: Reutilizar evidencia aprobada entre entradas cuando coinciden las entradas relevantes aunque cambie el commit
    Dado un proyecto con la comprobación de pruebas "python -m unittest" acotada a las entradas relevantes "src/", "tests/" y "pyproject.toml"
    Y una ejecución previa aprobada con código 0 sobre el árbol, las herramientas, la configuración, las dependencias y la plataforma actuales
    Y se crea un nuevo commit que modifica únicamente "docs/notas.md" fuera de las entradas relevantes de pruebas
    Cuando otra entrada solicita la misma comprobación de pruebas desde el gateway, un agente o el cierre de release
    Entonces el plan muestra la acción "reutilizar" con el motivo de coincidencia de identidad de contenido y entorno relevantes
    Y reutiliza la evidencia aprobada con código 0 sin lanzar de nuevo el comando y el contador de ejecuciones reales permanece en 1

  @T-ADV-0032 @CA-M-2 @CA-M-3
  Esquema del escenario: Invalidar la evidencia cuando cambia el contenido, el entorno relevante o una entrada no acreditable
    Dado una evidencia aprobada previa de la comprobación "pruebas" sobre un commit base
    Y en ese mismo commit cambia <factor_modificado>
    Cuando solicito evaluar o reutilizar la comprobación "pruebas"
    Entonces la evidencia anterior no se reutiliza y el plan muestra la acción "ejecutar" explicando el motivo <motivo_esperado>
    Ejemplos:
      | factor_modificado                                          | motivo_esperado                          |
      | un archivo rastreado con cambios pendientes sin confirmar   | cambio en contenido relevante            |
      | un archivo nuevo relevante sin rastrear "src/nuevo.py"      | cambio en contenido relevante            |
      | la versión o huella de la herramienta ejecutable            | cambio en entorno (herramienta)          |
      | el archivo de configuración relevante "pyproject.toml"      | cambio en entorno (configuración)        |
      | el archivo de bloqueo de dependencias "requirements.lock"   | cambio en entorno (dependencias)         |
      | el identificador de plataforma o runtime de Python          | cambio en entorno (plataforma)           |
      | una entrada relevante declarada que no se puede inspeccionar | entrada relevante no acreditable         |

  @T-ADV-0032 @CA-M-3
  Escenario: Impedir acreditar un resultado cuando el árbol o el entorno cambian durante la ejecución
    Dado una comprobación en curso iniciada con una identidad de contenido y entorno A
    Cuando durante la ejecución del comando se modifica un archivo relevante del árbol produciendo la identidad B y el comando termina con código 0
    Entonces el resultado no acredita la identidad B ni deja acreditada como válida la identidad actual
    Y el registro conserva la discrepancia entre la identidad inicial A y la identidad final B con motivo verificable

  @T-ADV-0032 @CA-M-4 @CA-M-8
  Escenario: Compartir un único proceso de cierre y comprobación equivalente entre CLI, gateway, agente y worktrees
    Dado un cierre de versión o comprobación de suite en curso para la misma identidad en el proyecto
    Cuando CLI, gateway y un agente solicitan simultáneamente ese mismo cierre o comprobación, incluso desde un worktree vinculado al mismo repositorio
    Entonces las solicitudes concurrentes se unen a la ejecución en curso sin lanzar un segundo proceso de cierre ni duplicar la suite
    Y mientras dura la ejecución todas las entradas consultan la fase actual, el comando activo, los registros parciales emitidos, las evidencias y la siguiente acción sin inventar un porcentaje de progreso
    Y al terminar con código 0 todas reciben el mismo resultado y el contador de invocaciones reales de la suite es exactamente 1

  @T-ADV-0032 @CA-M-4 @CA-M-8
  Escenario: Aislar solicitudes con distinto contenido o alcance y recuperar interrupciones sin falsos aprobados
    Dado una comprobación en curso con identidad A
    Cuando llega una solicitud con identidad distinta B por cambio de contenido, entorno o alcance
    Entonces la solicitud B no recibe como válido el resultado de A y su consulta de estado muestra el motivo de espera y la siguiente acción "ejecutar con identidad B"
    Y si el proceso que ejecutaba A muere inesperadamente dejando el estado en "ejecutando", al consultar o relanzar se detecta el PID inactivo, se marca la ejecución previa como "interrumpido" sin crear un falso aprobado y se permite iniciar una nueva ejecución limpia

  @T-ADV-0032 @CA-M-5
  Escenario: Prevalecer el último resultado real e invalidar un verde anterior tras un fallo posterior en todas las entradas
    Dado que la comprobación "suite" tiene una ejecución real aprobada con código 0 y después una ejecución real fallida con código 1 para la misma identidad
    Cuando se consulta el estado, se construye el prompt del agente Hades o se solicita reutilizar la evidencia en "--verificar" o en release
    Entonces prevalece el estado "fallido" de la última ejecución real y no se rescata el verde anterior
    Y el prompt del agente no incluye "suite" como verificado en verde sobre este árbol
    Y las consultas y reutilizaciones no añaden una nueva ejecución real ni alteran el último resultado registrado

  @T-ADV-0032 @CA-M-5
  Escenario: Registrar historial de intermitencias sin borrarlo por un verde posterior ni reintentar hasta lograr verde
    Dado que para una misma identidad exacta la comprobación "pruebas" registra resultados alternos código 0, después código 1 y después código 0
    Cuando consulto la evidencia y el estado de la comprobación "pruebas"
    Entonces el último resultado es "aprobado" pero la comprobación conserva la marca "intermitente" con el historial de transiciones y su diagnóstico
    Y ante un fallo el servicio nunca reintenta automáticamente el mismo comando sobre la misma identidad buscando un verde fortuito

  @T-ADV-0032 @CA-M-6 @CA-M-7
  Escenario: Diagnosticar un fallo, conservar en caché las etapas aprobadas independientes y ampliar la validación según impacto
    Dado un proyecto con las etapas aprobadas "formato" (alcance "src/"), "lint" (alcance "src/") y "pruebas" (alcance "src/", "tests/") y una etapa fallida "build" (alcance "packaging/")
    Cuando se diagnostica y repara el fallo modificando únicamente "packaging/build_cfg.json"
    Entonces antes de ejecutar la validación de reparación el plan explica qué etapas se reutilizan y cuáles se invalidan por impacto
    Y las etapas "formato", "lint" y "pruebas" conservan su evidencia "aprobado" en caché y no se reejecutan
    Y se ejecuta primero la etapa afectada "build" y solo se amplía a la suite global si la puerta final o un alcance compartido lo exige con motivo explícito
    Y si la reparación no puede continuar autónomamente tras agotar el ciclo, conserva el diagnóstico, la siguiente acción y el motivo concreto de intervención humana

  @T-ADV-0032 @CA-M-9
  Escenario: Separar validar, cerrar localmente, etiquetar y publicar respetando las restricciones del proyecto y el árbol preparado
    Dado un proyecto que en task_config.yaml permite validar y cerrar localmente pero restringe etiquetar y publicar desde el gateway sin autorización explícita
    Cuando se solicita validar desde cualquier entrada o "/cerrar v1.0 confirmo" desde el gateway
    Entonces la validación acredita únicamente la evidencia de las comprobaciones sin cerrar ni publicar
    Y la solicitud desde el gateway rechaza etiquetar y publicar informando de la restricción configurada, o ejecuta solo el cierre local cuando así se solicita y está permitido
    Y cuando se autoriza publicar, la evidencia de preflight y puertas de release se verifica contra la identidad exacta del worktree de integración preparado tras el merge con main, reutilizando la suite si el árbol integrado coincide y reejecutando si el merge modificó entradas relevantes

  @T-ADV-0032 @CA-M-10
  Escenario: Conservar compatibilidad con configuraciones actuales, tratar evidencia histórica y adoptar el flujo común sin doble suite
    Dado un proyecto con configuración heredada validation.command, validation.formato, validation.lint, release.preflight que invoca de nuevo la misma suite de validación y un lanzador redundante de cierre al estilo de Afinn
    Y un fichero orquestar_evidencias.jsonl que contiene un registro histórico sin huella de entorno completa y otro registro que cumple el contrato completo
    Cuando se ejecuta la migración o adopción al servicio común de chequeos y se solicita el cierre de versión
    Entonces el registro histórico incompleto se conserva como "historial_sin_acreditar" sin falsificar cobertura y el registro completo sí se reutiliza
    Y el flujo común unifica validation.command y release.preflight con el lanzador de cierre, conserva todas las comprobaciones y restricciones de release declaradas y ejecuta la suite de cierre una sola vez para el mismo árbol preparado
    Y si el repositorio externo de Afinn no está accesible dentro del árbol de trabajo autorizado, la herramienta deja comprobada la migración sobre la configuración reproducible y registra explícitamente el bloqueo de la entrega sobre el repositorio externo sin declarar realizada su migración in situ
