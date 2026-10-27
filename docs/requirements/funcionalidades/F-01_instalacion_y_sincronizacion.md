# F-01 · Instalación y sincronización con los arneses
- Prioridad: Must · Ola: A · Recorridos: R0, R2 · Depende de: F-05
- Propósito: instalar Adevv una vez por máquina con una sola orden y dejar sus skills, agentes y workflows donde los busca cada arnés, sin tocar lo que no es de Adevv y sin dejar cambios en los proyectos.

## Requisitos

**Instalación**
- **RF-F01-01** El README deberá documentar una sola orden que instala una versión publicada fija desde el origen fijo (nunca por nombre desde un índice público de paquetes ni desde una rama) y ejecuta `adevv instalar`; `adevv instalar` deberá hacer antes la comprobación de `requirements.md §4` sin la fila 4 (`ESPERA`), de modo que, con la actualización automática activa, al terminar quede instalada la última versión publicada y sincronizados los destinos si no hay bucles; con la actualización automática desactivada (p. ej. tras una vuelta atrás) no consulta la red ni cambia de versión.

**Sincronización (`adevv instalar`)**
- **RF-F01-03** Cuando se ejecute `adevv instalar`, el sistema deberá escribir los archivos de instrucciones de la versión instalada (skills sin código, agentes, adaptadores de ese arnés y workflows, según lo que cada arnés lea) solo en las carpetas confirmadas de cada destino cuyo estado no sea `NO_DETECTADO` ni `DESACTIVADO`, y mostrar por destino qué escribió («Claude Code: 24 skills, 5 agentes» / «sin cambios» / «no detectado»).
- **RF-F01-04** El sistema deberá resolver al escribir las rutas que los adaptadores y workflows necesitan (a skills y agentes instalados), de modo que ningún archivo escrito en un destino cite una ruta relativa que empiece por `.agents/` ni una ruta relativa a un proyecto.
- **RF-F01-05** El sistema deberá guardar, por destino, la ruta relativa y la huella de cada archivo que escriba, y la versión sincronizada solo si la sincronización terminó sin errores. Solo deberá escribir o borrar rutas de ese registro o rutas nuevas que no existan; nunca fuera de las carpetas del destino (una ruta del registro que, resuelta, quede fuera se ignora y se informa), nunca en entradas cuyo nombre empiece por `.` y nunca siguiendo enlaces.
- **RF-F01-06** Si una ruta que el contenido necesita ya existe y no está en el registro, o está pero su huella no coincide con la registrada (editada a mano), entonces el sistema no deberá tocarla, deberá dejar el destino `INCOMPLETO` y listar los conflictos (máximo 20 líneas más el total). Con `adevv instalar --forzar`, deberá sobrescribir los archivos del registro editados a mano, nunca los ajenos.
- **RF-F01-07** Cuando un archivo del registro ya no forme parte del contenido de la versión instalada y su huella coincida, el sistema deberá borrarlo; una carpeta solo se borra si queda vacía, nunca de forma recursiva.
- **RF-F01-09** Si un destino no tiene registro o no se puede leer, entonces el sistema no deberá borrar nada en ese destino y deberá adoptar en el registro los archivos existentes cuya huella coincida con la del contenido (así una copia previa idéntica no cuenta como conflicto).

**Coherencia y estado**
- **RF-F01-11** Cuando arranque cualquier orden `adevv` fuera de un paso de bucle, sin bucles en marcha, y algún destino esté `DESFASADO`, el sistema deberá resincronizarlo antes de la acción de la orden y avisar en una línea: «<Arnés> sincronizado con la X.Y.Z.». Con bucles en marcha no deberá tocarlo y deberá avisar como mucho una vez cada 24 h: «<Arnés> sigue con la A.B.C; se sincronizará cuando no haya bucles en marcha: <lista>.». `adevv instalar`, también con `--forzar`, y la instalación de una versión siguen la misma regla: no escriben archivos ni registros globales mientras haya bucles. Esto no aplaza la instalación ni la recarga del motor, cuyos mandatos usan rutas absolutas al almacén versionado.
- **RF-F01-12** Cuando se ejecute `adevv --version`, el sistema deberá mostrar la versión instalada y su origen (`desarrollo` si lo es), el estado de cada destino con el texto de `requirements.md §4`, si la actualización automática está activa, la última comprobación con su resultado y el último `APLICADA`/`FALLIDA` con su fecha.
- **RF-F01-13** Cuando se lance un bucle y algún destino usado por un rol del proyecto esté `INCOMPLETO` o `DESFASADO`, el sistema deberá avisar en una línea («<Arnés> sin sincronizar: <causa>. El bucle usa la instalación; revisa con `adevv instalar`.») y seguir: el bucle no depende de los destinos (`RF-F02-03`).

_Retirados en la revisión:_ `RF-F01-02` (aviso de PATH: lo da el instalador y lo documenta el README), `RF-F01-08` (solo lectura: duplicaba `RF-F01-06` y rompía `RF-F01-07` en Windows), `RF-F01-10` (escritura atómica: pasa a `§6` como restricción técnica). Ver `ciclo/revision.md`.

## Casos límite

| Caso | Comportamiento |
|---|---|
| Arnés no instalado (no existe su carpeta base) | Destino `NO_DETECTADO`; no se crea nada; se dice en el resumen |
| Existe `~/.gemini/antigravity`, pero la versión no tiene carpetas confirmadas para Antigravity | `NO_DETECTADO` («sin confirmar»); no se crea `skills/` por suposición |
| Carpeta ajena en el destino (`~/.claude/skills/synced`, `~/.codex/skills/.system`) | No se toca (no está en el registro; `.system` empieza por `.`) |
| Skill del usuario con el mismo nombre que una de Adevv | Conflicto: no se sobrescribe; destino `INCOMPLETO` con su ruta; los bucles se lanzan con aviso |
| Archivo de Adevv editado a mano | Conflicto; `--forzar` lo sobrescribe |
| La versión nueva retira una skill y el usuario dejó una nota dentro de su carpeta | Se borran los archivos del registro; la carpeta queda con la nota |
| Antigravity abierto bloquea un archivo | Error: el registro no guarda versión → `DESFASADO`; la siguiente orden sin bucles en marcha lo reintenta |
| Primera instalación con una copia previa idéntica de las skills (p. ej. enlaces del submódulo resueltos) | Se adoptan las que coinciden; las distintas son conflicto |
| Se ejecuta `adevv instalar` dos veces seguidas | La segunda no cambia nada y dice «sin cambios» por destino |

## Criterios de aceptación

```gherkin
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
```

**Otras verificaciones:** ninguna; todos los RF vigentes tienen CA.
