# F-03 · Actualización automática
- Prioridad: Must · Ola: A · Recorridos: R2 · Depende de: F-01, F-05
- Propósito: que una versión publicada llegue sola a la máquina en la siguiente orden `adevv`, sin romper nunca un bucle en marcha, sin esperar a la red más de unos segundos y sin quedar a medias.

La tabla de resultados, su precedencia, sus mensajes y las definiciones (versión publicada, versión nueva, proceso de Adevv en marcha) están en `requirements.md §4` y forman parte de esta funcionalidad.

## Requisitos

**Comprobación**
- **RF-F03-01** Cuando arranque cualquier orden `adevv`, el sistema deberá evaluar la comprobación de actualización antes de la acción de la orden y aplicar el primer resultado de la tabla de `§4` que se cumpla.
- **RF-F03-02** El sistema deberá consultar las versiones solo en el origen fijo del paquete (no configurable por proyecto) y considerar solo versiones publicadas, nunca una rama.
- **RF-F03-03** El sistema deberá hacer la consulta sin pedir nada al usuario (sin ventanas ni preguntas de credenciales) y abandonarla a los 5 s; cualquier fallo de la consulta da `SIN_RED` con su causa.
- **RF-F03-04** El sistema deberá guardar en el estado de actualización los datos que la tabla usa, según la columna «¿Cuenta como comprobación del día?», y el último resultado `APLICADA` o `FALLIDA` con su fecha.
- **RF-F03-05** Si la configuración de usuario desactiva la actualización automática, entonces el sistema no deberá consultar la red salvo en `adevv actualizar`.

**Bucles en marcha**
- **RF-F03-06** Cuando haya una versión nueva elegible, el sistema deberá instalarla aunque haya bucles en marcha, conmutar `active.json` atómicamente y avisar que los motores desde v0.5.0 la tomarán al terminar su paso actual si admite sus opciones; si no, siguen con su versión y lo avisan (desde v1.0.0) (`RF-F03-14`); los anteriores requieren reinicio manual. Solo se aplaza la copia a destinos globales según RF-F01-11. No se guardan nuevos aplazamientos de instalación; los heredados se consumen sin esperar bucles.

- **RF-F03-14** Cuando un bucle o un gateway en marcha vaya a recargar la versión activa entre pasos o vueltas de polling, solo deberá hacerlo si el motor de destino admite la recarga (versión desde v0.5.0) y acepta todas las opciones con que se lanzó el proceso. Si no, deberá seguir con su versión sin ceder `orquestar.pid` ni `telegram.pid` y avisar una sola vez por versión activa, en su log y por Telegram (evento `respuesta`): «La X.Y.Z activa no puede recargar este <bucle|gateway> (<causa>); sigue con la A.B.C. Reinícialo para usarla.», con causa «anterior a v0.5» o «no admite <opciones>». Si `active.json` pasa después a una versión compatible, la recarga sigue la regla general. Esta protección la aplican los motores desde v1.0.0; los motores ya publicados de 0.5.0 a 0.6.1 no la tienen.

**Aplicación**
- **RF-F03-07** Cuando se aplique una actualización, el sistema deberá instalar desde el origen fijo el commit al que apuntaba la etiqueta en la consulta, comprobar que la versión instalada es la de la etiqueta, sincronizar los destinos (`F-01`) y ejecutar la acción de la orden que la disparó con la versión nueva; si la instalación falla, no termina en ≤ 180 s o la versión no coincide, deberá ejecutar la acción con la versión anterior, intacta, y guardar la versión como fallida.
- **RF-F03-08** El sistema no deberá modificar durante la instalación ningún archivo que use un proceso de Adevv en marcha, incluida la propia orden y los gateways (que siguen con su versión durante la instalación y la operación en curso, y hasta reiniciarse en versiones anteriores a `v0.5.0`, sin perjuicio de la auto-recarga cooperativa entre ciclos de los motores en `skills/` a partir de `v0.5.0` según `DEC-P10`), ni lanzar un bucle o un gateway antes de que la instalación haya terminado o fallado.
- **RF-F03-09** Si la sincronización de algún destino falla tras instalar, entonces la versión instalada deberá quedar en la nueva, el destino `DESFASADO` (se reintenta según `RF-F01-11`) y el mensaje de `APLICADA` deberá añadir «Arneses sin sincronizar: <arnés>: <causa>.».

**Orden manual y vuelta atrás**
- **RF-F03-10** Cuando se ejecute `adevv actualizar`, el sistema deberá hacer la comprobación forzada (sin las filas «auto»), olvidar la versión fallida, reactivar la actualización automática si estaba desactivada (y decirlo) y aplicar la última versión publicada si es mayor que la instalada.
- **RF-F03-11** `adevv actualizar X.Y.Z` no hace la comprobación de `RF-F03-01`: solo consulta la lista de versiones publicadas para validar X.Y.Z. Cuando X.Y.Z sea una versión publicada distinta de la instalada, el sistema deberá instalarla; si es menor que la última publicada, deberá además desactivar la actualización automática y decirlo: «Actualización automática desactivada; `adevv actualizar` la reactiva.». Con bucles en marcha deberá instalar igualmente, conservar las versiones en uso y avisar de la recarga entre pasos desde v0.5.0 si el destino admite la recarga y las opciones de cada proceso (`RF-F03-14`) y del reinicio manual de motores anteriores o hacia destinos anteriores a v0.5.0; las copias globales se aplazan según RF-F01-11. Si X.Y.Z es la instalada: «Adevv X.Y.Z ya está instalado.», sin cambios. Si la consulta falla: «No se pudo consultar <origen>: <causa>. Sigues con la X.Y.Z.», sin cambios.
- **RF-F03-12** Si `X.Y.Z` no es una versión publicada, entonces `adevv actualizar X.Y.Z` deberá terminar sin cambios con «X.Y.Z no es una versión publicada. Publicadas: <las 5 mayores, de mayor a menor>.».

**Avisos**
- **RF-F03-13** El sistema deberá escribir los avisos de actualización en la salida de errores, en una línea, para no alterar la salida de la orden; la skill `/orquestar` (y los workflows y adaptadores que la invocan) deberá reenviar al usuario cualquier aviso de Adevv que reciba.

## Ejemplos de la ventana de comprobación

Comprobación automática; instalada 0.1.0; publicada 0.2.0 salvo que se diga; sin bucles en marcha salvo que se diga; con red salvo que se diga.

| # | Estado guardado | Ahora | En marcha | Resultado | Por qué |
|---|---|---|---|---|---|
| E1 | última contada lun 09:00 | mar 08:59 | — | `ESPERA` | 23 h 59 min < 24 h |
| E2 | última contada lun 09:00 | mar 09:00 | — | `APLICADA` | 24 h no es < 24 h |
| E3 | último `SIN_RED` lun 10:00; última contada dom 09:00 | lun 10:59 | — | `ESPERA` | 59 min < 1 h |
| E4 | último `SIN_RED` lun 10:00; última contada dom 09:00 | lun 11:00 | — | `APLICADA` | 1 h no es < 1 h; 26 h ≥ 24 h desde la contada |
| E5 | fallida 0.2.0; última contada lun 10:00 | lun 15:59 | — | `ESPERA` | 5 h 59 min < 24 h |
| E6 | fallida 0.2.0; última contada lun 10:00 | mar 10:00 | — | `AL_DIA` | 0.2.0 no es mayor que la fallida |
| E7 | fallida 0.2.0; última contada lun 10:00; publicada 0.2.1 | mar 10:00 | — | `APLICADA` (0.2.1) | 0.2.1 > 0.2.0 fallida |
| E8 | aplazada 0.2.0; aviso lun 09:00 | lun 12:00 | bucle | `APLICADA` | consume aplazamiento heredado sin esperar bucles |
| E9 | aplazada 0.2.0; aviso lun 09:00 | lun 12:00 | — | `APLICADA` | aplazada: no espera 24 h |
| E10 | aplazada 0.2.0; aviso lun 09:00 | mar 09:00 | bucle | `APLICADA` | consume aplazamiento heredado sin esperar bucles |
| E11 | aplazada 0.2.0 | lun 12:00 | gateway | `APLICADA` + aviso de reinicio manual | gateway 0.1.0: no aplaza y requiere reinicio manual |
| E12 | aplazada 0.2.0 | lun 12:00, sin red | — | `SIN_RED` | la instalación no puede descargar |
| E13 | última contada hace 8 días; último `SIN_RED` hace 2 h; último aviso sin red hace 25 h | sin red | — | `SIN_RED` con aviso | 8 días ≥ 7; 25 h ≥ 24 h |

## Casos límite

| Caso | Comportamiento |
|---|---|
| Un paso del bucle ejecuta `adevv orquestar --verificar` | `DENTRO_DE_ORQUESTACION`: ni consulta ni instala |
| El gateway lleva días en marcha | No impide la actualización; sigue con su versión durante la instalación y la operación en curso (y hasta reiniciarse en versiones anteriores a `v0.5.0`, o hasta su auto-recarga cooperativa entre vueltas de polling desde `v0.5.0` según `DEC-P10`) y el aviso distingue recarga cooperativa desde v0.5.0 y reinicio manual de anteriores |
| `adevv --version` abierto en otra consola | Tipo `otro`: no aplaza; sigue con su versión |
| Bucle lanzado desde el antiguo submódulo o la copia congelada | Cuenta como bucle en marcha (su línea de órdenes ejecuta `orquestar.py`) |
| PID reutilizado por otro programa en `orquestar.pid` | No cuenta: un proceso cuenta por lo que ejecuta, no por el archivo |
| El repositorio de origen pide credenciales | No aparece ninguna ventana; `SIN_RED` con causa «credenciales» |
| Etiquetas `v0.2.0-rc1` o `v0.3.0` ligera | No son versiones publicadas: se ignoran |
| Etiqueta `v0.3.0` cuyo paquete dice 0.2.9 | `FALLIDA` («la versión instalada no es 0.3.0»); no se reintenta hasta otra versión o `adevv actualizar` |
| Instalación de desarrollo | `DESARROLLO`; `adevv actualizar` sí instala la última publicada y pasa a origen `publicada` |
| Comparación `0.10.0` frente a `0.9.3` | `0.10.0` es mayor |
| Volver atrás con bucles o gateways desde v1.0 en marcha hacia una versión anterior a v0.5, o hacia una que no acepta sus opciones | Se instala igualmente; los procesos siguen con su versión, no ceden su PID y avisan una vez de que hace falta reiniciarlos (`RF-F03-14`) |
| La orden que dispara la actualización es `adevv orquestar --fondo` | El bucle se lanza después de instalar, ya con la versión nueva (o con la anterior si falló) |

## Criterios de aceptación

```gherkin
@CA-F03-01 @RF-F03-01 @RF-F03-04 @RF-F03-06 @RF-F03-07
Esquema del escenario: Ventana de comprobación
  Dado Adevv 0.1.0 instalado y publicadas "<publicadas>"
  Y el estado de actualización "<estado>"
  Y en marcha "<en marcha>"
  Cuando a las "<ahora>" ejecuto "adevv orquestar --estado" fuera de un bucle y con red
  Entonces el resultado de la comprobación es "<resultado>"

  Ejemplos:
    | publicadas  | estado                                              | ahora     | en marcha | resultado |
    | 0.2.0       | última contada lun 09:00                            | mar 08:59 | nada      | ESPERA    |
    | 0.2.0       | última contada lun 09:00                            | mar 09:00 | nada      | APLICADA  |
    | 0.2.0       | último SIN_RED lun 10:00, última contada dom 09:00  | lun 10:59 | nada      | ESPERA    |
    | 0.2.0       | último SIN_RED lun 10:00, última contada dom 09:00  | lun 11:00 | nada      | APLICADA  |
    | 0.2.0       | fallida 0.2.0, última contada lun 10:00             | lun 15:59 | nada      | ESPERA    |
    | 0.2.0       | fallida 0.2.0, última contada lun 10:00             | mar 10:00 | nada      | AL_DIA    |
    | 0.2.0 0.2.1 | fallida 0.2.0, última contada lun 10:00             | mar 10:00 | nada      | APLICADA  |
    | 0.2.0       | aplazada 0.2.0, aviso lun 09:00                     | lun 12:00 | bucle     | APLICADA  |
    | 0.2.0       | aplazada 0.2.0, aviso lun 09:00                     | lun 12:00 | nada      | APLICADA  |
    | 0.2.0       | aplazada 0.2.0, aviso lun 09:00                     | lun 12:00 | gateway   | APLICADA  |

@CA-F03-02 @RF-F03-07
Escenario: Actualización aplicada al lanzar
  Dado Adevv 0.1.0 instalado, la 0.2.0 publicada, sin bucles en marcha y sin comprobación en 24 h
  Cuando ejecuto "adevv orquestar --estado"
  Entonces la salida de errores muestra "Adevv actualizado de 0.1.0 a 0.2.0. Reinicia las sesiones abiertas de los arneses para usar las skills nuevas."
  Y el estado lo calcula la 0.2.0
  Y "adevv --version" informa 0.2.0 con los destinos sincronizados con la 0.2.0

@CA-F03-03 @RF-F03-06
Escenario: Instalar con un bucle en marcha en otro proyecto
  Dado Adevv 0.5.0 instalado, la 0.6.1 publicada, sin comprobación en 24 h y un bucle de 0.5.0 en marcha en "C:\SW\Afinn"
  Cuando ejecuto "adevv orquestar --estado" en otro proyecto
  Entonces queda instalada la 0.6.1 y active.json apunta a la 0.6.1
  Y el aviso indica que los bucles en marcha la tomarán al terminar su paso actual
  Cuando el bucle de Afinn termina su paso actual
  Entonces se recarga con la 0.6.1 sin interrumpir el paso y sus archivos anteriores permanecen intactos
  Y los destinos compartidos no cambian mientras haya bucles

@CA-F03-04 @RF-F03-06
Escenario: Un bucle anterior a la migración no impide instalar
  Dado un bucle anterior a v0.5.0 en marcha lanzado con "python .agents/skills/orquestar/orquestar.py" en un proyecto
  Y la 0.2.0 publicada
  Cuando ejecuto "adevv actualizar"
  Entonces queda instalada la 0.2.0 sin modificar los archivos del bucle antiguo
  Y se informa que los motores anteriores a v0.5 requieren reinicio manual

@CA-F03-05 @RF-F03-08
Escenario: Un gateway abierto no impide actualizar ni se rompe
  Dado Adevv 0.5.0 instalado, la 0.6.1 publicada y un gateway de 0.5.0 en marcha en "C:\SW\Adevv"
  Cuando ejecuto "adevv actualizar"
  Entonces queda instalada la 0.6.1
  Y el gateway sigue respondiendo con la 0.5.0
  Y el gateway toma la 0.6.1 entre vueltas de polling sin cortar la respuesta en curso
  Y el aviso explica la recarga cooperativa y el reinicio manual de motores anteriores a v0.5

@CA-F03-06 @RF-F03-02 @RF-F03-03
Escenario: Sin red o sin credenciales
  Dado que el origen no responde en 5 segundos
  Cuando ejecuto "adevv orquestar --estado"
  Entonces la orden sigue con la versión instalada tras esperar como mucho 5 segundos a la red
  Y no aparece ninguna petición de credenciales

@CA-F03-07 @RF-F03-02
Escenario: Solo cuentan las versiones publicadas
  Dado Adevv 0.1.0 instalado
  Y en el origen las etiquetas "v0.2.0-rc1", "v0.3.0" ligera y "v0.2.1" anotada
  Cuando ejecuto "adevv actualizar"
  Entonces se instala la 0.2.1

@CA-F03-08 @RF-F03-07
Escenario: Fallo de instalación
  Dado Adevv 0.1.0 instalado y la 0.2.0 publicada pero imposible de instalar
  Cuando ejecuto "adevv orquestar --fondo"
  Entonces la salida de errores muestra "No se pudo actualizar a 0.2.0: <causa>. Sigues con la 0.1.0. Reintenta con `adevv actualizar`."
  Y el bucle se lanza con la 0.1.0 después del intento
  Y "adevv --version" informa 0.1.0 con los destinos sincronizados

@CA-F03-09 @RF-F03-07
Escenario: La etiqueta no coincide con la versión del paquete
  Dado Adevv 0.1.0 instalado y la etiqueta anotada "v0.3.0" cuyo paquete declara 0.2.9
  Cuando ejecuto "adevv actualizar"
  Entonces el resultado es "FALLIDA" con la causa "la versión instalada no es 0.3.0"
  Y sigue instalada la 0.1.0

@CA-F03-10 @RF-F03-09
Escenario: Instalada pero un arnés sin sincronizar
  Dado que al aplicar la 0.2.0 Codex tiene bloqueado un archivo de su destino
  Cuando termina la actualización
  Entonces la versión instalada es 0.2.0 y Codex queda "DESFASADO"
  Y el mensaje añade "Arneses sin sincronizar: Codex: <causa>."

@CA-F03-11 @RF-F03-05
Escenario: Actualización desactivada
  Dado la actualización automática desactivada en la configuración de usuario
  Cuando ejecuto cualquier orden "adevv" que no sea "adevv actualizar"
  Entonces no se consulta la red

@CA-F03-12 @RF-F03-11 @RF-F03-10
Escenario: Volver atrás y reactivar
  Dado Adevv 0.3.0 instalado, sin bucles en marcha y publicadas la 0.2.1 y la 0.3.0
  Cuando ejecuto "adevv actualizar 0.2.1"
  Entonces queda instalada la 0.2.1
  Y el mensaje dice "Actualización automática desactivada; `adevv actualizar` la reactiva."
  Y 24 horas después una orden "adevv" no consulta la red
  Cuando se publica la 0.3.1 y ejecuto "adevv actualizar"
  Entonces se instala la 0.3.1 y la actualización automática queda activa

@CA-F03-13 @RF-F03-11
Escenario: Volver atrás con un bucle en marcha
  Dado Adevv 0.6.1 instalado, publicadas la 0.5.0 y la 0.6.1, y un bucle de 0.6.1 en marcha en "C:\SW\Afinn"
  Cuando ejecuto "adevv actualizar 0.5.0"
  Entonces queda instalada la 0.5.0 y se desactiva la actualización automática
  Y el bucle mantiene su paso actual y recarga la 0.5.0 al terminarlo
  Y los destinos compartidos permanecen intactos

@B-ADV-0021 @CA-F03-17 @RF-F03-14 @RF-F03-11
Escenario: Volver atrás a un motor sin recarga con un bucle en marcha
  Dado Adevv 1.0.0 instalado, publicadas la 0.4.0 y la 1.0.0, y un bucle y un gateway de 1.0.0 en marcha en "C:\SW\Afinn"
  Cuando ejecuto "adevv actualizar 0.4.0"
  Entonces queda instalada la 0.4.0 y el aviso dice "La 0.4.0 no admite recarga: reinicia a mano los bucles y gateways en marcha para usarla; los de v0.5.0 a v0.6.1 se detendrán al terminar su paso o respuesta actual."
  Y el aviso identifica el bucle y el gateway de "C:\SW\Afinn"
  Cuando el bucle de Afinn termina su paso actual
  Entonces sigue en marcha con la 1.0.0 y "orquestar.pid" conserva su PID
  Y su log y Telegram avisan una sola vez "La 0.4.0 activa no puede recargar este bucle (anterior a v0.5); sigue con la 1.0.0. Reinícialo para usarla."
  Y "adevv orquestar --estado" muestra el bucle vivo
  Cuando el gateway termina su vuelta de polling
  Entonces sigue respondiendo con la 1.0.0 y "telegram.pid" conserva su PID
  Y su log y Telegram avisan una sola vez "La 0.4.0 activa no puede recargar este gateway (anterior a v0.5); sigue con la 1.0.0. Reinícialo para usarla."

@B-ADV-0021 @CA-F03-18 @RF-F03-14 @RF-F03-11
Escenario: El motor de destino no acepta las opciones del proceso en marcha
  Dado Adevv 1.0.0 instalado, publicadas la 0.6.1 y la 1.0.0, un bucle de 1.0.0 en marcha lanzado con "--calidad" y un gateway de 1.0.0 en marcha
  Y el bucle de la 0.6.1 no admite "--calidad"
  Cuando ejecuto "adevv actualizar 0.6.1"
  Entonces queda instalada la 0.6.1 y el aviso dice "Los motores desde v0.5.0 tomarán la versión activa al terminar su paso o respuesta actual si admite sus opciones; si no, siguen con su versión y lo avisan (desde v1.0.0). Los anteriores requieren reinicio manual."
  Cuando el bucle termina su paso actual y el gateway termina su vuelta de polling
  Entonces el bucle sigue con la 1.0.0 y avisa una sola vez "La 0.6.1 activa no puede recargar este bucle (no admite --calidad); sigue con la 1.0.0. Reinícialo para usarla."
  Y el gateway, cuyas opciones sí acepta la 0.6.1, recarga la 0.6.1
  Cuando se publica la 1.0.1, que admite "--calidad", y ejecuto "adevv actualizar"
  Entonces el bucle recarga la 1.0.1 al terminar su paso actual

@CA-F03-14 @RF-F03-12
Escenario: Versión inexistente
  Dado Adevv 0.1.0 instalado y las versiones publicadas 0.1.0 y 0.2.0
  Cuando ejecuto "adevv actualizar 0.9.0"
  Entonces nada cambia y el mensaje es "0.9.0 no es una versión publicada. Publicadas: 0.2.0, 0.1.0."

@CA-F03-15 @RF-F03-01
Escenario: Dentro de un paso del bucle no se comprueba
  Dado un paso de un bucle en marcha
  Cuando ese paso ejecuta "adevv orquestar --verificar"
  Entonces no se consulta la red ni se instala nada

@CA-F03-16 @RF-F03-13
Escenario: Los avisos no alteran la salida de la orden
  Dado que una orden "adevv orquestar --estado" aplica una actualización
  Entonces el aviso aparece solo en la salida de errores
  Y la salida estándar es la del estado
```

**Otras verificaciones:** `RF-F03-08` se verifica además con una prueba de integración en Windows: con un bucle de prueba y un gateway de la versión instalada en marcha, se fuerza la aplicación y se comprueba que ambos siguen y que los archivos que usan no han cambiado. Las filas `DESARROLLO`, E8, E10, E12 y E13 se verifican con pruebas unitarias de la tabla.
