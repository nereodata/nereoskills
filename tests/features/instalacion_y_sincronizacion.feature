# language: es
Característica: Instalación y sincronización con los arneses
  Como usuario de Adevv
  Quiero instalar Adevv una sola vez por máquina y sincronizar sus skills, agentes y workflows en los arneses
  Para poder utilizarlos globalmente sin ensuciar los proyectos locales y protegiendo mis archivos personales

  @CA-F01-01 @RF-F01-01 @RF-F01-03
  Escenario: Primera instalación en una máquina con Claude Code y Codex
    Dado una máquina sin Adevv con las carpetas base de Claude Code y Codex y sin la de Antigravity
    Y las versiones publicadas 0.1.0 y 0.1.1
    Cuando ejecuto la orden de instalación del README, que fija la 0.1.0
    Entonces "adevv --version" informa "0.1.1"
    Y los destinos Claude Code y Codex quedan "SINCRONIZADO" con la 0.1.1
    Y el destino Antigravity queda "NO_DETECTADO" y su carpeta no se ha creado

  @CA-F01-02 @RF-F01-03
  Escenario: Destino sin carpetas confirmadas
    Dado que existe la carpeta base de Antigravity y la versión instalada no tiene carpetas confirmadas para Antigravity
    Cuando ejecuto "adevv instalar"
    Entonces no se crea ninguna carpeta dentro de la de Antigravity
    Y "adevv --version" muestra "Antigravity: sin confirmar"

  @CA-F01-03 @RF-F01-04
  Escenario: Lo escrito en los destinos no cita rutas de proyecto
    Dado Adevv 0.1.0 sincronizado en Claude Code y Codex
    Cuando busco en todos los archivos del registro de ambos destinos rutas relativas que empiecen por ".agents/" o "../"
    Entonces no hay ninguna coincidencia
    Y los adaptadores de Codex citan la ruta absoluta de los agentes instalados

  @CA-F01-04 @RF-F01-05 @RF-F01-06 @RF-F01-13
  Escenario: Una skill ajena con el mismo nombre no se sobrescribe
    Dado que en el destino de Claude Code existe la skill "commit" que no está en el registro
    Cuando ejecuto "adevv instalar"
    Entonces la skill "commit" existente no cambia
    Y el destino Claude Code queda "INCOMPLETO" listando la ruta de "commit"
    Y el resto de skills de Adevv quedan escritas
    Cuando lanzo un bucle en un proyecto cuyos roles usan "claude"
    Entonces el bucle se lanza y la salida de errores avisa de que Claude Code no está sincronizado

  @CA-F01-05 @RF-F01-06
  Escenario: Archivo de Adevv editado a mano
    Dado Adevv sincronizado en Claude Code
    Y que he editado a mano la skill "orquestar" en ese destino
    Cuando ejecuto "adevv instalar"
    Entonces la skill editada no cambia y el destino queda "INCOMPLETO"
    Cuando ejecuto "adevv instalar --forzar"
    Entonces la skill vuelve al contenido de la versión instalada y el destino queda "SINCRONIZADO"

  @CA-F01-06 @RF-F01-05
  Escenario: Las carpetas ajenas y ocultas no se tocan
    Dado que existen "~/.claude/skills/synced" y "~/.codex/skills/.system"
    Cuando ejecuto "adevv instalar" y después instalo una versión anterior
    Entonces el contenido de ambas carpetas es idéntico al de antes

  @CA-F01-07 @RF-F01-05
  Escenario: Una ruta del registro que sale del destino se ignora
    Dado un registro de Codex con la ruta "..\..\proyecto\nota.md"
    Cuando se sincroniza una versión que ya no la contiene
    Entonces "nota.md" no se borra
    Y el resumen informa de la ruta ignorada

  @CA-F01-08 @RF-F01-07
  Escenario: Se borra una skill que la versión nueva ya no trae
    Dado Adevv 0.1.0 sincronizado con la skill "seo-audit"
    Y un archivo "notas.txt" mío dentro de la carpeta de "seo-audit"
    Y la versión 0.2.0 sin "seo-audit"
    Cuando se instala y sincroniza la 0.2.0
    Entonces los archivos de Adevv de "seo-audit" desaparecen del destino y del registro
    Y "notas.txt" sigue en su carpeta

  @CA-F01-09 @RF-F01-09
  Esquema del escenario: Destino sin registro o con registro ilegible
    Dado que el registro del destino Codex <situación>
    Y que en Codex existen copias idénticas de 20 skills de Adevv y una "orquestar" distinta
    Cuando ejecuto "adevv instalar"
    Entonces no se borra ningún archivo del destino Codex
    Y las 20 skills idénticas quedan en el registro
    Y "orquestar" aparece como conflicto

    Ejemplos:
      | situación      |
      | no existe      |
      | está corrupto  |

  @CA-F01-10 @RF-F01-11
  Escenario: Resincronización al desfasarse, sin bucles en marcha
    Dado Adevv 0.2.0 sincronizado en Claude Code
    Y que el paquete se ha reinstalado a mano en la 0.1.0
    Y la actualización automática desactivada en la configuración de usuario
    Y ningún bucle en marcha
    Cuando ejecuto cualquier orden "adevv"
    Entonces antes de su acción el destino Claude Code se sincroniza con la 0.1.0
    Y se muestra "Claude Code sincronizado con la 0.1.0."

  @CA-F01-11 @RF-F01-11
  Escenario: No se resincroniza con un bucle en marcha
    Dado Adevv 0.1.0 instalado y Claude Code sincronizado con la 0.2.0
    Y un bucle en marcha en "C:\SW\Afinn"
    Cuando ejecuto "adevv --version" en otra consola
    Entonces los archivos del destino Claude Code no cambian
    Y se muestra "Claude Code sigue con la 0.2.0; se sincronizará cuando no haya bucles en marcha: bucle en C:\SW\Afinn."

  @CA-F01-12 @RF-F01-12
  Escenario: Ver qué versión hay en cada arnés
    Dado Adevv 0.2.0 sincronizado en Claude Code y Codex, Antigravity no detectado, la última comprobación hace 3 h al día y la 0.2.0 aplicada el día 20
    Cuando ejecuto "adevv --version"
    Entonces veo "Adevv 0.2.0", "Claude Code 0.2.0", "Codex 0.2.0", "Antigravity: no detectado", "actualización automática: sí", "última comprobación: hace 3 h (al día)" y "actualizado a 0.2.0 el día 20"

  @CA-F01-13 @RF-F01-03
  Escenario: Sincronizar dos veces no cambia nada
    Dado Adevv sincronizado en todos los destinos detectados
    Cuando ejecuto "adevv instalar"
    Entonces cada destino informa "sin cambios"
