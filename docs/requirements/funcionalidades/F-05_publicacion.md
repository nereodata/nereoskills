# F-05 · Publicación de versiones sin contenido interno
- Prioridad: Must · Ola: A · Recorridos: R4 · Depende de: —
- Propósito: que cerrar una versión de Adevv con `/release` produzca una versión publicada que se instala sin backlog, tests ni documentación interna, cuyo número coincide siempre con el de la etiqueta y que no cambia una vez publicada.

## Requisitos

- **RF-F05-01** El paquete deberá contener solo el contenido distribuible definido por lista blanca: `skills/**`, `agents/**`, `workflows/**` y el código del paquete. Nunca deberá contener `docs/`, `tests/`, `.github/`, `task_config.yaml`, `orchestration.json`, `__pycache__`, archivos `*.pid`, `*.log` o `*.jsonl`, ni enlaces o junctions.
- **RF-F05-03** La suite de Adevv deberá incluir una prueba que construye el paquete, lista su contenido y falla si algún archivo queda fuera de la lista blanca o coincide con lo prohibido en `RF-F05-01`.
- **RF-F05-05** Si en el repositorio de Adevv la versión del paquete no coincide con la de la etiqueta que se va a publicar, o esa etiqueta ya existe en el origen, entonces la publicación deberá fallar antes de crear o empujar la etiqueta, con «La versión del paquete (A.B.C) no coincide con vX.Y.Z.» o «vX.Y.Z ya está publicada: publica vX.Y.(Z+1).».
- **RF-F05-06** La publicación deberá crear una etiqueta anotada `vX.Y.Z` en un commit alcanzable desde `main` del origen fijo; es lo único que el sistema considera versión publicada (`requirements.md §4`).
- **RF-F05-07** La versión del paquete deberá subir con `/release` junto con `project.version`, sin pasos manuales.

_Retirados en la revisión:_ `RF-F05-02` (construir desde el commit) y `RF-F05-04` (manifiesto en `task_config.yaml`) pasan a `requirements.md §6` como restricciones técnicas; el comportamiento observable queda en `RF-F05-01`, `RF-F05-05` y `RF-F05-07`. Ver `ciclo/revision.md`.

## Casos límite

| Caso | Comportamiento |
|---|---|
| Árbol con `orquestar.pid`, `orquestar.log` y la junction `.agents` sin versionar | No entran (`RF-F05-01`) |
| Un `__pycache__` versionado por error dentro de `skills/` | La prueba de `RF-F05-03` falla |
| `pyproject` en 0.1.0 y etiqueta `v0.2.0` | La publicación falla con el mensaje de versión |
| Se quiere corregir una versión ya publicada | Se publica Z+1; la etiqueta publicada no se mueve |
| `/release` en un proyecto consumidor | Sin cambios de comportamiento: `RF-F05-05` solo aplica al repositorio de Adevv |

## Criterios de aceptación

```gherkin
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
```

**Otras verificaciones:** ninguna; todos los RF tienen CA.
