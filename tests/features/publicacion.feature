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
