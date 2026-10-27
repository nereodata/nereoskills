# Revisión de especificación — B-ADV-0009

**Veredicto: APROBADO. Media: 9/10.** Sin hallazgos pendientes.

## Alcance y método

Revisión de cero, en modo orquestado, aplicando Hades y `/review-spec` de `C:/Users/Iván Moreno/.adevv/versions/0.6.1/` e ignorando el modelo del frontmatter. Fecha: 2026-10-27.

Objeto revisado: la especificación autorizada en HEAD `61d13d192f490368c9faac1d939f41202d523a38`, incorporada mediante `95b3d0b` (`docs(plan): especificar B-ADV-0009 y desbloquear desarrollo`). Se cotejó el delta de ese commit con su padre y se leyó el contrato resultante, limitado al triaje de definición del bug:

- `docs/requirements/requirements.md`: CE-3 y contratos relacionados de R2 y §4.
- `docs/requirements/funcionalidades/F-01_instalacion_y_sincronizacion.md`: instalación y protección de copias globales, especialmente RF-F01-11.
- `docs/requirements/funcionalidades/F-03_actualizacion_automatica.md`: instalación con procesos vivos, consumo de aplazamientos heredados, avisos y vuelta atrás.
- `tests/features/actualizacion_automatica.feature`.
- `tests/features/instalacion_y_sincronizacion.feature`.

Se leyeron el alcance y triaje del bug y el informe existente para identificar H1–H3; su aprobación previa no se toma como prueba del veredicto actual. Los cinco artefactos revisados coinciden con HEAD. La sustitución de los escenarios de aplazamiento está expresamente autorizada por el apartado «Alcance (decisión humana)» del bug. Los escenarios ajenos al delta solo se usan como contexto de contratos que deben conservarse.

No se ha consultado implementación, diseño ni tests unitarios. No se han ejecutado pruebas ni suite completa. La comprobación es documental; no certifica funcionamiento. La evidencia histórica de `git diff --check` del informe anterior no se atribuye al árbol actual ni a este informe nuevo. No se considera necesario ejecutar una verificación adicional para resolver el juicio semántico de esta revisión.

## Comprobaciones obligatorias

| Criterio | Resultado | Evidencia y valoración |
| --- | --- | --- |
| No regresión | ✅ | El delta sustituye los contratos de aplazamiento y ajusta los avisos y precondiciones de recarga dentro del alcance autorizado. Conserva los escenarios de errores, credenciales, desactivación, versiones inexistentes y órdenes dentro del paso. No elimina escenarios ajenos al bug. |
| Coherencia | ✅ | CE-3, R2, RF-F03-06/11 y RF-F01-11 permiten instalar con bucles y reservan el aplazamiento para archivos y registros globales. La fila 7 es transversal y permite llegar a APLICADA/FALLIDA. RF-F03-07 remite a F-01 para la sincronización, por lo que se aplica su guarda. La recarga se distingue del reinicio manual anterior a v0.5.0. |
| Trazabilidad | ✅ | Las CA modificadas CA-F03-01/03/04/05/13 existen en F-03 y corresponden a los contratos que el bug autoriza cambiar. Las adiciones trazan directamente RF-F03-06, RF-F03-08 y RF-F01-11; no inventan CA del bug. CA-F01-10/11 conservan la resincronización posterior y la protección con bucles vivos. |
| Delta real | ✅ | Se especifica instalar sin esperar al fin de los bucles, consumir aplazamientos heredados, reutilizar una versión en uso sin sobrescribirla y proteger las copias incluso con órdenes explícitas y `--forzar`. El esquema nuevo de F-01 añade esas variantes al caso previo de consulta de versión. |

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Claridad | 9/10 | Distingue versión activa, motor en ejecución y destinos globales; expresa cuándo cambia cada uno y qué aviso corresponde. |
| Completitud | 9/10 | Cubre actualización automática y manual con bucles, gateway, motor antiguo, rollback compatible, aplazamiento heredado y sincronización tras terminar el último bucle. Conserva las salidas normativas de fallo y falta de red. |
| Testeabilidad | 9/10 | Usa versiones concretas, puntero activo, conservación de archivos y registros y límites observables entre pasos/polling. El origen controlado del esquema evita una versión final dependiente de publicaciones externas. |
| Estructura | 9/10 | Los escenarios permanecen en los archivos de sus funcionalidades; las variantes de órdenes que protegen copias comparten un esquema. |

**Media: (9 + 9 + 9 + 9) / 4 = 9/10**, superior a 8; sin hallazgos críticos ni altos.

## Reevaluación y enrutado de hallazgos anteriores

| Hallazgo | Gravedad anterior | Estado actual | Para | Destino |
| --- | --- | --- | --- | --- |
| H1 — Recarga exigida a versiones sin esa capacidad | 🔴 CRÍTICO | Resuelto | `especificador` | `resolver`: corrección satisfecha, sin acción pendiente |
| H2 — Tabla normativa y avisos incompatibles con instalar con bucles | 🔴 CRÍTICO | Resuelto | `especificador` | `resolver`: corrección satisfecha, sin acción pendiente |
| H3 — Versión final del esquema dependiente del origen | 🟡 MEDIA | Resuelto | `especificador` | `resolver`: corrección satisfecha, sin acción pendiente |

### H1 — Resuelto

CA-F03-03 y CA-F03-05 parten de motores 0.5.0 y adoptan 0.6.1; CA-F03-13 vuelve de 0.6.1 a 0.5.0. Esas precondiciones son compatibles con la recarga desde v0.5.0 y preservan el paso o respuesta en curso. CA-F03-04 distingue explícitamente el motor antiguo y exige aviso de reinicio manual, sin modificar sus archivos. Las copias Gherkin de F-03 mantienen esas expectativas. El escenario de reutilización de 0.1.0 solo exige conmutar el puntero y no sobrescribir su carpeta; no exige recarga a ese motor antiguo.

### H2 — Resuelto

La precedencia de §4 declara que la fila 7 no es un resultado terminal. Las filas 8/9 admiten instalación con o sin bucles y mantienen las salidas APLICADA/FALLIDA; SIN_RED conserva su tratamiento propio. El texto de consumo heredado exige intentar instalar sin volver a consultar la lista y borra el aplazamiento tras APLICADA/FALLIDA o instalar otra versión, sin producir nuevos aplazamientos de instalación.

El aviso de APLICADA sustituye la petición de reiniciar sesiones por la indicación de copias pendientes cuando hay bucles. Distingue recarga cooperativa y reinicio manual y pide identificar los procesos. E8/E10, E11 y los escenarios modificados no contradicen esas reglas. La protección de archivos y registros globales se conserva también en `instalar --forzar`; la instalación y el cambio de puntero pueden completarse sin esa copia.

### H3 — Resuelto

El esquema «Ninguna copia global pisa un paso vivo» fija un origen controlado accesible cuya última publicada es 0.2.0. Sus tres órdenes (`instalar`, `instalar --forzar`, `actualizar`) deben mantener archivos y registros en 0.1.0 mientras existe un bucle. Tras terminar el último, `--version` debe sincronizar con 0.2.0. Las dos fases tienen un resultado verificable sin depender de nuevas publicaciones del origen real.

## Hallazgos nuevos y salida orquestada

Ninguno. No hay hallazgos para `desarrollador`, `especificador` o `humano`, ni deuda que registrar o descartar. La especificación del alcance revisado queda aprobada; las fases posteriores deberán acreditar su cumplimiento mediante sus propias revisiones y verificaciones.

Esta actuación solo sustituye el informe. No modifica requisitos, escenarios ni estados, y no crea commit. Se conserva el cambio previo del árbol que sitúa el bug en `in_progress`.
