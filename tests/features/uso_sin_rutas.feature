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

  @B-ADV-0006
  Escenario: Suite roja al cerrar una versión se convierte en un bug elegible
    Dado una release sin tareas elegibles cuya suite escribe errores en stdout y stderr
    Cuando falla la suite al cerrar la versión
    Entonces se conserva su salida y se registra un bug planned en esa versión con el comando y los errores
    Y el contador de arreglos fallidos es 0
    Y el siguiente paso es bug-fix sobre ese bug con las revisiones habituales
    Y la revisión de versión solo continúa cuando la suite pasa

  @B-ADV-0006
  Esquema del escenario: Recaídas del mismo cierre reutilizan el bug y suben la dificultad
    Dado un bug de cierre de dificultad <nivel> con <previas> recaídas desde su última promoción
    Y las recaídas corresponden a la misma causa que el arreglo intenta corregir
    Y Hades, si se le solicita diagnóstico, asignará al humano la renovación de un certificado que solo su titular puede renovar
    Y bug-fix acaba de marcarlo completed
    Cuando la suite de la misma versión y comando falla con una salida distinta a la anterior
    Entonces se conserva el ID y se actualiza la salida del bug
    Y su estado es <estado> y su dificultad es <resultado> con contador <contador>
    Y el bucle <accion>

    Ejemplos:
      | nivel   | previas | estado  | resultado | contador | accion                                                     |
      | media   | 0       | planned | media     | 1        | continúa con bug-fix                                        |
      | media   | 1       | planned | media     | 2        | continúa con bug-fix                                        |
      | media   | 2       | planned | dificil   | 0        | continúa con bug-fix con el perfil de dificultad dificil     |
      | dificil | 0       | planned | dificil   | 1        | continúa con bug-fix                                        |
      | dificil | 1       | planned | dificil   | 2        | continúa con bug-fix                                        |
      | dificil | 2       | blocked | dificil   | 3        | para y avisa en consola y Telegram con ID y la última salida |

  @B-ADV-0006
  Esquema del escenario: Bloqueos y cancelaciones del bug conservan la intervención habitual
    Dado un bug de cierre en estado <estado>
    Cuando la suite de la misma versión y comando sigue roja en el cierre
    Entonces el bug permanece <estado> y el bucle informa del impedimento sin reabrirlo

    Ejemplos:
      | estado    |
      | blocked   |
      | cancelled |

  @B-ADV-0006
  Esquema del escenario: Un cierre diferente obtiene su propio bug
    Dado un bug de cierre para la versión v0.1 y el comando suite-a
    Cuando falla el cierre de la versión <version> con el comando <comando>
    Entonces se registra otro ID sin modificar el bug anterior

    Ejemplos:
      | version | comando |
      | v0.1    | suite-b |
      | v0.2    | suite-a |

  @B-ADV-0036 @CA-1 @CA-2 @CA-6
  Escenario: La tercera recaída del grupo abre un único diagnóstico con el historial
    Dado que dos arreglos en dificil dejaron roja la comprobación de pedidos porque falta la columna «moneda»
    Cuando tras el tercer arreglo vuelve a faltar «moneda» aunque cambia la ruta temporal del informe
    Entonces Hades recibe una solicitud con el ID del bug, el fallo vigente y los tres arreglos con sus evidencias
    Y mientras falta el dictamen no se pide intervención humana ni se emite el aviso de bloqueo humano
    Y al retomar el cierre con la misma evidencia se conserva una única solicitud para ese grupo

  @B-ADV-0036 @CA-3 @CA-4 @CA-5 @CA-8
  Esquema del escenario: El dictamen determina el siguiente paso del bug de cierre
    Dado que un grupo agotó tres recaídas en dificil y el diagnóstico incluye los intentos y sus evidencias
    Cuando Hades asigna el destino <destino> con la decisión «<decision>»
    Entonces el bug conserva su ID, el destino y la decisión
    Y el siguiente paso es <paso>
    Y respecto a la persona se observa <intervencion>

    Ejemplos:
      | destino        | decision                                                                               | paso                                           | intervencion                                         |
      | desarrollador  | Aplicar la migración antes de cargar los pedidos de prueba                             | bug-fix con esa estrategia y el bug planned    | ninguna pregunta ni aviso de bloqueo humano          |
      | especificador  | Aclarar si la moneda se hereda del pedido o del cliente                                | especificar con esa contradicción documentada  | ninguna pregunta ni aviso de bloqueo humano          |
      | humano         | ¿Puedes renovar el certificado de pruebas? Solo su titular puede emitir el reemplazo.  | blocked con pendiente_de humano                | una pregunta persistida con ese texto y su motivo    |

  @B-ADV-0036 @CA-2 @CA-6
  Escenario: Una causa independiente que aparece tras el arreglo dispone de su propio presupuesto
    Dado un bug en dificil con dos recaídas por falta de «moneda» en la consulta de pedidos
    Cuando el siguiente cierre confirma que la consulta pasa y falla por primera vez la firma de facturas por certificado caducado
    Entonces el mismo ID conserva las dos recaídas de pedidos y registra cero recaídas de firma
    Y al volver a fallar solo la firma después de su primer arreglo registra una recaída de firma sin solicitar diagnóstico
    Y si después reaparece la columna ausente tras otro arreglo de pedidos, pedidos alcanza tres y se solicita su único diagnóstico

  @B-ADV-0036 @CA-2 @CA-5 @CA-7
  Escenario: La estrategia revisada se agota y se aplica la conclusión de Hades
    Dado que Hades autorizó un intento de corregir la cadena de confianza con el certificado disponible
    Y dispuso que, si seguía caducado, solo su titular podría renovar el certificado y dejó la pregunta «¿Puedes renovarlo?»
    Cuando la verificación del arreglo confirma la misma caducidad
    Entonces el diagnóstico terminal del grupo enumera los arreglos, sus evidencias y el resultado del último intento
    Y el bug queda blocked para el humano con la pregunta y el motivo que indicó Hades
    Y al retomar ese cierre no se repite el diagnóstico, el arreglo ni la pregunta

  @B-ADV-0036 @CA-2 @CA-5 @CA-7
  Escenario: El primer dictamen acredita que hace falta intervenir antes de otro arreglo
    Dado que tres arreglos en dificil conservaron sus evidencias de rechazo de firma por certificado revocado
    Y la autoridad emisora confirma la revocación irreversible y que solo el titular puede emitir el reemplazo
    Cuando el primer dictamen de Hades cita esas evidencias y pide al humano «¿Puedes emitir un certificado de pruebas nuevo?»
    Entonces el bug queda blocked para el humano con esa pregunta, el motivo, los tres intentos y sus evidencias
    Y al retomar el cierre sin el certificado nuevo hay una sola pregunta, un solo diagnóstico y ningún cuarto arreglo

  @B-ADV-0012
  Esquema del escenario: Una tarea atascada queda aislada y permite avanzar a otra independiente
    Dado una release con un <paso> dificil sin progreso y otra tarea independiente
    Y una tercera tarea depende de la atascada
    Y el límite de intentos sin progreso está configurado con "--reintentos=2"
    Cuando la atascada alcanza 2 intentos sin progreso y no puede promocionar
    Entonces queda blocked con pendiente_de humano
    Y su motivo conserva los 2 intentos, la dificultad dificil y los últimos 2000 caracteres de salida
    Y el motivo queda en la revisión humana de la versión y se avisa por Telegram
    Y el bucle completa la tarea independiente sin ejecutar la dependiente
    Y al terminar las elegibles informa del bloqueo de versión

    Ejemplos:
      | paso     |
      | task-dev |
      | bug-fix  |

  @B-ADV-0012
  Escenario: La promoción disponible precede al bloqueo local
    Dado una tarea media sin progreso
    Y el límite de intentos sin progreso está configurado con "--reintentos=2"
    Y la tarea alcanza 2 intentos sin progreso
    Cuando el bucle puede promocionarla a dificil
    Entonces la promociona y vuelve a intentarla antes de bloquearla

  @B-ADV-0013
  Esquema del escenario: Un análisis se recupera en el primer perfil que consigue avanzar
    Dado la configuración común de perfiles B-ADV-0013 con "--reintentos=2"
    Y work-plan pendiente sin argumento en un proyecto con requisitos y plataforma aprobados
    Y los perfiles anteriores a <exitoso> no producen progreso y <exitoso> completa el plan
    Cuando el bucle ejecuta work-plan mediante arneses simulados
    Entonces las ejecuciones de work-plan son exactamente <secuencia> en ese orden
    Y cada cambio de perfil inicia una sesión nueva
    Y no ejecuta los perfiles posteriores al exitoso ni repite la reserva duplicada
    Y continúa con el siguiente paso elegible sin bloquear tareas ni parar por falta de progreso

    Ejemplos:
      | exitoso                    | secuencia                                                                                                          |
      | claude/escalado-demo/high   | codex/base-demo/medium ×2 → codex/superior-demo/high ×2 → claude/escalado-demo/high ×1                                    |
      | agy/reserva-demo/medium     | codex/base-demo/medium ×2 → codex/superior-demo/high ×2 → claude/escalado-demo/high ×2 → agy/reserva-demo/medium ×1        |

  @B-ADV-0013
  Esquema del escenario: Agotar un análisis local permite completar otra tarea elegible
    Dado la configuración común de perfiles B-ADV-0013 con "--reintentos=2"
    Y una release con <paso> pendiente para B-DEMO-0001 de dificultad media
    Y T-DEMO-0002 planned sin dependencias es elegible y su arnés simulado la completa
    Y T-DEMO-0003 planned depende de B-DEMO-0001
    Cuando ningún perfil consigue progreso en <paso> para B-DEMO-0001
    Entonces ejecuta exactamente codex/base-demo/medium ×2 → codex/superior-demo/high ×2 → claude/escalado-demo/high ×2 → agy/reserva-demo/medium ×2
    Y inicia una sesión nueva al cambiar de perfil y no repite la reserva duplicada
    Y solo B-DEMO-0001 queda blocked con pendiente_de humano
    Y la tarea, la revisión de versión y los avisos de consola y Telegram simulado identifican <paso>, B-DEMO-0001 y esos cuatro perfiles en orden con 2 intentos cada uno
    Y completa T-DEMO-0002 sin ejecutar ni modificar T-DEMO-0003
    Y solo tras terminar las elegibles informa del bloqueo de versión

    Ejemplos:
      | paso          |
      | especificar   |
      | revisar-tarea |

  @B-ADV-0013
  Esquema del escenario: Un análisis global solo para tras agotar toda su cadena
    Dado la configuración común de perfiles B-ADV-0013 con "--reintentos=2"
    Y un proyecto cuyo siguiente paso elegible es <paso> con argumento <argumento>
    Cuando ningún perfil consigue progreso en ese paso
    Entonces ejecuta exactamente codex/base-demo/medium ×2 → codex/superior-demo/high ×2 → claude/escalado-demo/high ×2 → agy/reserva-demo/medium ×2
    Y inicia una sesión nueva al cambiar de perfil y no repite la reserva duplicada
    Y para indicando <paso>, <argumento> y esos cuatro perfiles en orden con 2 intentos cada uno
    Y no modifica el estado de ninguna tarea

    Ejemplos:
      | paso                  | argumento |
      | work-plan             | vacío     |
      | calcular-dependencias | vacío     |
      | revisar-version       | v0.1      |
      | revisar-deuda         | v0.1      |
      | aplicar-producto      | v0.1      |

  @B-ADV-0013
  Esquema del escenario: Intercalar otro contexto conserva recuperaciones independientes
    Dado la configuración común de perfiles B-ADV-0013 con "--reintentos=2"
    Y el selector simulado permite intercalar pares elegibles sin cambiar la firma de progreso de ninguno
    Y especificar B-DEMO-0001 ha ejecutado base-demo dos veces y superior-demo una vez sin progreso
    Cuando el selector elige <otro_paso> con argumento <otro_argumento> durante una ejecución sin progreso
    Y después vuelve a especificar B-DEMO-0001
    Entonces el otro par ejecuta codex/base-demo/medium por primera vez
    Y B-DEMO-0001 ejecuta codex/superior-demo/high por segunda vez
    Y su siguiente ejecución usa claude/escalado-demo/high por primera vez
    Y al volver al otro par este ejecuta codex/base-demo/medium por segunda vez antes de cambiar de perfil
    Y ningún par queda bloqueado por los intentos consumidos por el otro

    Ejemplos:
      | otro_paso     | otro_argumento |
      | especificar   | B-DEMO-0002    |
      | revisar-tarea | B-DEMO-0001    |

  @B-ADV-0013
  Escenario: El progreso reinicia solo la recuperación del par que avanzó
    Dado la configuración común de perfiles B-ADV-0013 con "--reintentos=2"
    Y especificar B-DEMO-0001 y especificar B-DEMO-0002 han agotado cada uno sus dos intentos base-demo
    Cuando especificar B-DEMO-0001 avanza con su primer intento superior-demo
    Y posteriormente vuelve a necesitar especificar con el mismo ID por un nuevo hallazgo
    Entonces sus dos primeras ejecuciones sin progreso son codex/base-demo/medium
    Y su tercera ejecución usa codex/superior-demo/high en una sesión nueva
    Y al reanudar B-DEMO-0002 su siguiente ejecución sigue siendo codex/superior-demo/high por primera vez

  @B-ADV-0013
  Escenario: La recarga conserva el perfil pendiente y sus intentos parciales
    Dado la configuración común de perfiles B-ADV-0013 con "--reintentos=2"
    Y especificar B-DEMO-0001 ha ejecutado base-demo dos veces y superior-demo una vez sin progreso
    Y especificar B-DEMO-0002 ha ejecutado base-demo una vez sin progreso
    Cuando el motor adopta cooperativamente una versión compatible entre pasos
    Entonces B-DEMO-0001 reanuda con codex/superior-demo/high por segunda vez
    Y si sigue sin progreso su siguiente ejecución es claude/escalado-demo/high por primera vez
    Y B-DEMO-0002 reanuda con codex/base-demo/medium por segunda vez
    Y si sigue sin progreso su siguiente ejecución es codex/superior-demo/high por primera vez
    Y la recarga no vuelve a perfiles agotados ni concede intentos adicionales

  @B-ADV-0048
  Esquema del escenario: Una reserva entrega el rechazo y Artemisa recibe la investigación técnica
    Dado que Gemini tiene una marca de cuota vigente y Hades usa su reserva Codex
    Y <disponibilidad>
    Cuando su respuesta final propia declara «**Veredicto formal: RECHAZADO. Media: 7,75/10.**»
    Y el fallo persiste y la solicitud asigna expresamente a desarrollo una intervención distinta
    Entonces se registra un rechazo y el siguiente bug-fix de Artemisa <resultado>
    Y conserva el rojo, las evidencias, el contador y la cuota de Gemini

    Ejemplos:
      | disponibilidad | resultado |
      | Artemisa tiene un perfil con cuota | recibe la solicitud y el mandato de aislar y acreditar la corrección del cierre |
      | todos los perfiles de Artemisa están sin cuota al entregar el encargo | espera su propia cuota y al relanzar recibe la misma solicitud y el mismo mandato |

  @B-ADV-0048
  Escenario: Una cita del rechazo o una entrega sin dictamen siguen pendientes
    Cuando la única declaración de rechazo está dentro de una cita o de un ejemplo, o la entrega carece de dictamen
    Entonces esa llamada no acredita una revisión ni permite entregar una intervención basada solo en ella

  @B-ADV-0048
  Escenario: Retomar el bloqueo histórico de Afinn con todos los perfiles de Artemisa sin cuota
    Dado el bug bloqueado de la solicitud activa con su hallazgo C1 rechazado y enrutado a Artemisa
    Cuando todos los perfiles de Artemisa carecen de cuota y la espera supera el límite del proceso
    Entonces el aviso identifica el bug-fix, el bug y la cuota del perfil de Artemisa
    Y al relanzar con cuota se entrega la misma investigación con su condición de salida
    Y devolver el mismo impedimento no abre una pregunta ni autoriza otra entrega ni completa el bug
    Y un segundo arranque después de devolver ese impedimento conserva la parada técnica

  @B-ADV-0048
  Escenario: Un mantenedor escrito sin asignación vigente conserva el bloqueo explicado
    Dado un bloqueo técnico con un nombre libre de mantenedor
    Cuando el informe vigente no acredita una asignación interna de la solicitud activa
    Entonces el estado indica qué asignación falta y conserva la ficha y el historial
