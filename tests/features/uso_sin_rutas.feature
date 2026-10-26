# language: es
Característica: F-02 · Adevv desde cualquier proyecto sin rutas
  Como desarrollador u operador de proyectos con agentes de IA
  Quiero invocar el bucle, Hades, la verificación, el gateway y los scripts mediante la orden global adevv
  Para prescindir de rutas al submódulo .agents/ y trabajar de forma consistente y aislada en cualquier proyecto

  @CA-F02-01 @RF-F02-01
  Escenario: La orden adevv sustituye a los scripts del submódulo
    Dado Adevv instalado y un proyecto sin submódulo
    Cuando ejecuto "adevv orquestar --estado" en la raíz del proyecto
    Entonces obtengo la misma salida y el mismo código que daba "orquestar.py --estado" para ese proyecto

  @CA-F02-02 @RF-F02-01
  Escenario: Lanzar el bucle en segundo plano
    Dado un proyecto con requisitos y Adevv instalado
    Cuando ejecuto "adevv orquestar --fondo --harness claude"
    Entonces a los 5 segundos existe "orquestar.pid" con un proceso vivo
    Y "orquestar.log" no contiene errores de argumentos

  @CA-F02-03 @RF-F02-03
  Esquema del escenario: El prompt de un paso cita la instalación
    Dado Adevv instalado en la unidad C:
    Y un proyecto en "<carpeta>"
    Cuando el bucle construye el prompt del paso "ciclo-requisitos"
    Entonces cita la skill "orquestar" y el agente "atenea" por su ruta absoluta en la instalación
    Y la verificación y Hades aparecen como "adevv orquestar --verificar" y "adevv orquestar --agente hades"
    Y no aparece "orquestar.py"

    Ejemplos:
      | carpeta            |
      | C:\SW\Afinn        |
      | D:\proyectos\Nuevo |

  @CA-F02-04 @RF-F02-05
  Escenario: Ninguna instrucción distribuible cita rutas del submódulo o scripts por ruta
    Dado los archivos de instrucciones del contenido distribuible
    Cuando busco rutas relativas que empiezan por ".agents/", "python " seguido de una ruta a ".py" y "skills/<nombre>/scripts"
    Entonces no hay ninguna coincidencia

  @CA-F02-05 @RF-F02-01 @RF-F02-05
  Escenario: /release en un proyecto consumidor sin submódulo
    Dado un proyecto sin submódulo con una versión lista para publicar
    Cuando la skill de release comprueba los manifiestos
    Entonces lo hace con "adevv release manifiestos"
    Y el resultado es el mismo que daba el script del submódulo

  @CA-F02-06 @RF-F02-06
  Escenario: instructions que apunta a un archivo inexistente
    Dado un "orchestration.json" cuyo rol "hades" tiene "instructions" igual a ".agents/agents/hades.md"
    Y que ese archivo no existe
    Cuando lanzo el bucle
    Entonces para sin lanzar ningún arnés con "orchestration.json: hades.instructions apunta a .agents/agents/hades.md, que no existe."

  @CA-F02-07 @RF-F02-07
  Esquema del escenario: Elementos locales o submódulo que impiden lanzar
    Dado un proyecto con "<elemento>"
    Cuando lanzo el bucle
    Entonces no se lanza y el mensaje cita "<elemento>"
    Cuando ejecuto "adevv orquestar --estado"
    Entonces responde con el estado del proyecto

    Ejemplos:
      | elemento                  |
      | .claude/skills/orquestar  |
      | .codex/agents/hades.toml  |
      | .agents                   |

  @CA-F02-08 @RF-F02-08
  Esquema del escenario: Proyecto nuevo sin git ni task_config.yaml
    Dado una carpeta "<carpeta>" con "docs/requirements/requirements.md", fuera de cualquier repositorio git y sin "task_config.yaml"
    Cuando lanzo el bucle
    Entonces existe un repositorio git con un commit inicial que solo lleva "task_config.yaml" y ".gitignore"
    Y "task_config.yaml" tiene "project.prefix" e "id_prefix" iguales a "<prefijo>"
    Y se ha mostrado una línea que lo dice

    Ejemplos:
      | carpeta | prefijo |
      | Mi app  | MIA     |
      | Q1      | PRJ     |
      | Ñandú   | NAN     |

  @CA-F02-09 @RF-F02-08
  Esquema del escenario: Carpetas donde no se crea nada
    Dado la carpeta "<carpeta>", que <requisitos> "docs/requirements/requirements.md"
    Cuando lanzo el bucle en ella
    Entonces no se crea ningún repositorio ni "task_config.yaml"
    Y el resultado es "<resultado>"

    Ejemplos:
      | carpeta             | requisitos  | resultado                                                               |
      | la carpeta personal | contiene    | el bucle para por falta de configuración, como hoy                      |
      | C:\                 | contiene    | el bucle para por falta de configuración, como hoy                      |
      | C:\SW\Afinn\docs    | contiene    | Estás en una subcarpeta de C:\SW\Afinn: lanza /orquestar desde la raíz. |
      | C:\SW\Nueva         | no contiene | el bucle para por falta de configuración, como hoy                      |

  @CA-F02-10 @RF-F02-09
  Escenario: El bucle sobre el repositorio de Adevv no ve el árbol de trabajo
    Dado Adevv 0.1.0 instalado
    Y un bucle en marcha sobre el repositorio fuente de Adevv
    Cuando un paso modifica "skills/orquestar/SKILL.md" del árbol de trabajo
    Entonces el paso siguiente del bucle recibe la ruta de la skill "orquestar" de la 0.1.0 instalada
    Y su prompt indica que los cambios se hacen en el árbol de trabajo, en cualquier ruta, y nunca en la copia instalada
