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
