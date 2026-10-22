| RF | F | CA | Resumen |
|---|---|---|---|
| RF-F01-01 | F-01 | CA-F01-01 | El README deberá documentar una sola orden que instala una versión publicada fij |
| RF-F01-03 | F-01 | CA-F01-01 CA-F01-02 CA-F01-13 | Cuando se ejecute adevv instalar, el sistema deberá escribir los archivos de ins |
| RF-F01-04 | F-01 | CA-F01-03 | El sistema deberá resolver al escribir las rutas que los adaptadores y workflows |
| RF-F01-05 | F-01 | CA-F01-04 CA-F01-06 CA-F01-07 | El sistema deberá guardar, por destino, la ruta relativa y la huella de cada arc |
| RF-F01-06 | F-01 | CA-F01-04 CA-F01-05 | Si una ruta que el contenido necesita ya existe y no está en el registro, o está |
| RF-F01-07 | F-01 | CA-F01-08 | Cuando un archivo del registro ya no forme parte del contenido de la versión ins |
| RF-F01-09 | F-01 | CA-F01-09 | Si un destino no tiene registro o no se puede leer, entonces el sistema no deber |
| RF-F01-11 | F-01 | CA-F01-10 CA-F01-11 | Cuando arranque cualquier orden adevv fuera de un paso de bucle, sin bucles en m |
| RF-F01-12 | F-01 | CA-F01-12 | Cuando se ejecute adevv --version, el sistema deberá mostrar la versión instalad |
| RF-F01-13 | F-01 | CA-F01-04 | Cuando se lance un bucle y algún destino usado por un rol del proyecto esté INCO |
| RF-F02-01 | F-02 | CA-F02-01 CA-F02-02 CA-F02-05 | El sistema deberá ofrecer adevv orquestar <args> con los mismos argumentos y el  |
| RF-F02-03 | F-02 | CA-F02-03 | El sistema deberá citar en los prompts que pasa a los arneses (pasos del bucle y |
| RF-F02-05 | F-02 | CA-F02-04 CA-F02-05 | Los archivos de instrucciones del contenido distribuible (skills, agentes, adapt |
| RF-F02-06 | F-02 | CA-F02-06 | Si orchestration.json no define instructions para un rol, el sistema deberá usar |
| RF-F02-07 | F-02 | CA-F02-07 | Cuando se lance un bucle (adevv orquestar sin --estado, --parar, --verificar, -- |
| RF-F02-08 | F-02 | CA-F02-08 CA-F02-09 | Cuando se lance un bucle en una carpeta que contiene docs/requirements/requireme |
| RF-F02-09 | F-02 | CA-F02-10 | Cuando el bucle trabaje sobre el repositorio fuente de Adevv, el prompt de cada  |
| RF-F03-01 | F-03 | CA-F03-01 CA-F03-15 | Cuando arranque cualquier orden adevv, el sistema deberá evaluar la comprobación |
| RF-F03-02 | F-03 | CA-F03-06 CA-F03-07 | El sistema deberá consultar las versiones solo en el origen fijo del paquete (no |
| RF-F03-03 | F-03 | CA-F03-06 | El sistema deberá hacer la consulta sin pedir nada al usuario (sin ventanas ni p |
| RF-F03-04 | F-03 | CA-F03-01 | El sistema deberá guardar en el estado de actualización los datos que la tabla u |
| RF-F03-05 | F-03 | CA-F03-11 | Si la configuración de usuario desactiva la actualización automática, entonces e |
| RF-F03-06 | F-03 | CA-F03-01 CA-F03-03 CA-F03-04 | Mientras haya algún bucle en marcha, el sistema no deberá instalar ninguna versi |
| RF-F03-07 | F-03 | CA-F03-01 CA-F03-02 CA-F03-08 CA-F03-09 | Cuando se aplique una actualización, el sistema deberá instalar desde el origen  |
| RF-F03-08 | F-03 | CA-F03-05 | El sistema no deberá modificar durante la instalación ningún archivo que use un  |
| RF-F03-09 | F-03 | CA-F03-10 | Si la sincronización de algún destino falla tras instalar, entonces la versión i |
| RF-F03-10 | F-03 | CA-F03-12 | Cuando se ejecute adevv actualizar, el sistema deberá hacer la comprobación forz |
| RF-F03-11 | F-03 | CA-F03-12 CA-F03-13 | adevv actualizar X.Y.Z no hace la comprobación de RF-F03-01: solo consulta la li |
| RF-F03-12 | F-03 | CA-F03-14 | Si X.Y.Z no es una versión publicada, entonces adevv actualizar X.Y.Z deberá ter |
| RF-F03-13 | F-03 | CA-F03-16 | El sistema deberá escribir los avisos de actualización en la salida de errores,  |
| RF-F04-01 | F-04 | CA-F04-01 CA-F04-03 CA-F04-05 | Cuando se ejecute adevv migrar en la raíz de un proyecto, el sistema deberá diag |
| RF-F04-02 | F-04 | CA-F04-01 CA-F04-02 CA-F04-04 | El sistema deberá contar como pendiente: la entrada .agents en .gitmodules; la c |
| RF-F04-03 | F-04 | CA-F04-01 CA-F04-03 CA-F04-04 | Son archivos en uso, en la raíz del proyecto: AGENTS.md, CLAUDE.md, GEMINI.md, R |
| RF-F04-06 | F-04 | — | El README de Adevv deberá documentar los pasos de migración en este orden: parar |
| RF-F05-01 | F-05 | CA-F05-01 | El paquete deberá contener solo el contenido distribuible definido por lista bla |
| RF-F05-03 | F-05 | CA-F05-01 CA-F05-02 | La suite de Adevv deberá incluir una prueba que construye el paquete, lista su c |
| RF-F05-05 | F-05 | CA-F05-03 CA-F05-04 | Si en el repositorio de Adevv la versión del paquete no coincide con la de la et |
| RF-F05-06 | F-05 | CA-F05-05 | La publicación deberá crear una etiqueta anotada vX.Y.Z en un commit alcanzable  |
| RF-F05-07 | F-05 | CA-F05-05 | La versión del paquete deberá subir con /release junto con project.version, sin  |
