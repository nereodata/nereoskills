# F-02 · Adevv desde cualquier proyecto sin rutas
- Prioridad: Must · Ola: A · Recorridos: R0, R1, R4 · Depende de: F-01
- Propósito: que el bucle, Hades, la verificación, el gateway y los scripts de las skills se lancen igual en cualquier proyecto, desde cualquiera de los tres arneses, sin rutas al submódulo; y que el bucle sobre el propio repositorio de Adevv use la versión instalada.

## Requisitos

**Órdenes**
- **RF-F02-01** El sistema deberá ofrecer `adevv orquestar <args>` con los mismos argumentos y el mismo comportamiento que hoy `orquestar.py` (lanzar en primer plano o en segundo plano con `--fondo`, `--estado`, `--parar`, `--verificar`, `--agente`, `--aviso-prueba` y el resto de opciones), `adevv telegram <args>` con los del gateway, y `adevv release manifiestos|completitud|changelog <args>` con los de los tres scripts de `/release`. Con `--fondo`, el bucle lanzado deberá recibir los mismos argumentos y seguir vivo tras arrancar.

**Lo que el motor dice a los arneses**
- **RF-F02-03** El sistema deberá citar en los prompts que pasa a los arneses (pasos del bucle y roles lanzados con `--agente`) las skills y los agentes por la ruta absoluta de la versión en uso, entre comillas, y los scripts solo como órdenes `adevv …`; deberá funcionar aunque el proyecto y la instalación estén en unidades distintas.
- **RF-F02-05** Los archivos de instrucciones del contenido distribuible (skills, agentes, adaptadores, workflows y plantillas; no el código del paquete) no deberán contener rutas relativas que empiecen por `.agents/`, invocaciones de scripts por ruta (`python …/*.py`) ni rutas a `skills/<nombre>/scripts`; los que hoy lo hacen deberán citar las órdenes `adevv …` o la skill por su nombre (`/nombre`).
- **RF-F02-06** Si `orchestration.json` no define `instructions` para un rol, el sistema deberá usar el agente instalado de ese rol; si la define y el archivo no existe, entonces deberá parar antes de lanzar nada con «orchestration.json: <rol>.instructions apunta a <ruta>, que no existe.».

**Proyectos**
- **RF-F02-07** Cuando se lance un bucle (`adevv orquestar` sin `--estado`, `--parar`, `--verificar`, `--agente` ni `--aviso-prueba`) y el proyecto tenga elementos locales que ocultan los instalados, el sistema no deberá lanzarlo y deberá listarlos: «Este proyecto tiene skills, agentes o workflows propios que ocultan los de Adevv: <rutas>. Bórralos o renómbralos.». Son locales: `.claude/skills/<n>/`, `.claude/agents/<n>.md`, `.codex/skills/<n>/`, `.codex/agents/<n>.toml`, `.agents/skills/<n>/`, `.agent/skills/<n>/` y `.agent/workflows/<n>.md`; ocultan cuando `<n>` coincide con el nombre de carpeta o el `name` de un elemento distribuible. Tampoco deberá lanzarlo si existe `.agents` o su entrada en `.gitmodules`: «Este proyecto aún usa el submódulo .agents: sigue los pasos de migración del README.».
- **RF-F02-08** Cuando se lance un bucle en una carpeta que contiene `docs/requirements/requirements.md`, no está dentro de ningún repositorio git y no es la carpeta personal ni la raíz de una unidad, el sistema deberá crear lo que falte (repositorio git con un commit inicial que solo lleva `task_config.yaml` y `.gitignore`; `task_config.yaml` mínimo) y decirlo en una línea antes de seguir. El `task_config.yaml` mínimo tiene `project.name` = nombre de la carpeta, `project.prefix` = prefijo, `project.version: "v0.0.0"`, `levels.master` con `path: docs/plan/`, carpetas `tasks/` y `bugs/` e `id_prefix` = prefijo, y sin `validation`. El prefijo son las tres primeras letras `A-Z` del nombre de la carpeta tras quitar tildes y diacríticos (`Ñ`→`N`), en mayúsculas, saltando espacios, cifras y signos; si tiene menos de tres, `PRJ`. Si la carpeta está dentro de un repositorio cuya raíz es otra, deberá parar sin crear nada: «Estás en una subcarpeta de <raíz>: lanza /orquestar desde la raíz.». Sin `requirements.md` no deberá crear nada (el bucle para como hoy: «Falta task_config.yaml en la raíz del proyecto.»).
- **RF-F02-09** Cuando el bucle trabaje sobre el repositorio fuente de Adevv, el prompt de cada paso deberá indicar que las skills y agentes citados son la versión instalada y que los cambios se hacen en `skills/`, `agents/` y `workflows/` del árbol.

_Retirados o fusionados en la revisión:_ `RF-F02-02` (en `RF-F02-01`), `RF-F02-04` (en `RF-F02-03`), `RF-F02-08b` (en `RF-F02-08`). Ver `ciclo/revision.md`.

## Casos límite

| Caso | Comportamiento |
|---|---|
| Proyecto en `D:\proyectos\X`, instalación en `C:` | Prompts con rutas absolutas; ningún error de ruta relativa |
| `.claude/skills/orquestar` en el proyecto (enlace al antiguo submódulo, roto o no) | `RF-F02-07`: no lanza el bucle y lo lista |
| `.claude/skills/mi-skill` propia sin nombre de Adevv | Se ignora |
| `adevv orquestar --estado` con elementos locales que ocultan, o con el submódulo | Responde normal (`RF-F02-07` solo afecta a lanzar) |
| Carpeta "Mi app" con `requirements.md`, sin git ni `task_config.yaml` | Crea ambos con prefijo `MIA` y lo dice |
| Carpeta "Q1" | Prefijo `PRJ` (una sola letra) |
| Carpeta "Ñandú" | Prefijo `NAN` |
| `/orquestar` desde `C:\Users\Iván Moreno` o `C:\` | No crea nada; el bucle para como hoy |
| `/orquestar` desde `C:\SW\Afinn\docs` | Para: «Estás en una subcarpeta de C:\SW\Afinn: lanza /orquestar desde la raíz.» |
| `instructions` del rol `hades` apunta a `.agents/agents/hades.md` inexistente | Para antes de lanzar con el mensaje de `RF-F02-06` |
| Hades configurado con `agy` | Igual que hoy: los roles con `--agente` admiten `claude` o `codex` (NO-04) |
| El repositorio de Adevv tiene `skills/` en la raíz | No es un elemento local de ningún arnés: no oculta nada |

## Criterios de aceptación

```gherkin
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
  Y su prompt indica que los cambios se hacen en "skills/", "agents/" y "workflows/" del árbol
```

**Otras verificaciones:** ninguna; todos los RF vigentes tienen CA.
