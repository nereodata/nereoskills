# B-ADV-0011 — Revisión de pruebas (ampliación tras revisión de código)

**Veredicto: APROBADO**

Modo orquestado. Skill instalada `review-test` releída. Se revisan exclusivamente el reloj determinista, la preparación de cuota previa y los cuatro casos añadidos a `skills/orquestar/test_fallos_arnes.py` desde la aprobación anterior. Los diez casos aprobados y la adaptación de agente/gateway de `test_arnes_ausente.py` conservan su aprobación; no se reabren sus revisiones.

No se ha leído producción ni diseño, modificado pruebas, ejecutado tests o compilación, lanzado suites completas ni realizado commits. Esta aprobación juzga las pruebas nuevas; no cierra por sí misma los hallazgos de revisión de código.

## Evidencia reutilizada

- Árbol `9b5427249edb47e7125e8f86e5865c0b6a8e31e6`: 14 pruebas verdes según la salida entregada. `orquestar_evidencias.jsonl` confirma código 0 tanto para `python -m unittest discover -s skills/orquestar -p test_fallos_arnes.py` como para la compilación sintáctica de los dos archivos de pruebas. No se repiten.
- RED de la ampliación: `B-ADV-0011-red.txt` documenta 13 pruebas y tres fallos antes de corregir: ausencia de espera para la cuota omitida, retorno 2 en vez de 0 al recuperar el omitido y modelos `[None, None]`. La evidencia de `--verificar` confirma retorno 1 en `4b417b8f24fdff3b6aca7a6f0a58c7e9461e9390`.
- El cuarto caso, de recuperación persistentemente fallida y acotada, se valora por lectura como protección adicional. No se le atribuye una ejecución RED no documentada.
- Sin linter/tipador configurados, según el contexto entregado. Se acepta la evidencia sintáctica existente sin comprobaciones duplicadas.

## Puntuaciones

| Criterio | Nota | Motivo |
| --- | --- | --- |
| Cobertura | 9/10 | Los cuatro casos distinguen selección de cuota más temprana, recuperación durante reintentos, agotamiento acotado y perfiles sin consumo. |
| Aserciones | 9/10 | Comprueban la espera elegida, perfiles ejecutados, resultado, registro final e identidad de modelos sin introducir consumo ficticio. |
| Rojo correcto | 9/10 | Los tres fallos documentados corresponden a las carencias funcionales señaladas. Las aserciones no se satisfacen mediante los datos de preparación por sí solos. |
| Estabilidad | 9/10 | Instante UTC fijo, reloj monotónico simulado, avance explícito durante esperas y ejecutables simulados eliminan dependencia del reloj real y del PATH. Los parches y temporales se limpian por prueba. |

**Media: 9,0/10.** Sin hallazgos críticos ni altos.

## Evaluación del delta nuevo

| Caso | Evaluación |
| --- | --- |
| `test_compara_cuota_omitida_y_cuota_del_paso` | Prepara cuota previa del principal de 120 segundos, una cuota posterior más larga y un fallo de red, con límite de espera de media hora. Exige la espera de 120 segundos, la secuencia reserva/tercero y el registro final asociado al principal. El retorno 2 responde a la interrupción simulada de la espera, no es la única aserción de resultado. |
| `test_reconsidera_omitido_recuperado_durante_reintentos` | La cuota previa caduca a los 30 segundos y la espera simulada avanza el reloj. La secuencia reserva/reserva/principal y el retorno exitoso discriminan que el perfil recuperado vuelva a ejecutarse. Solo permite una espera. |
| `test_recuperado_persistente_no_reinicia_perfiles` | Ante fallos persistentes exige reserva/reserva/principal/principal, dos esperas y retorno terminal. La secuencia finita de respuestas y las aserciones detectan reinicios de perfiles ya agotados. |
| `test_fallos_sin_consumo_identifican_modelo` | Principal y reserva comparten arnés y tienen modelos distintos; los resultados solo aportan duración. Exige exactamente las identidades principal/reserva en las filas, sin señal de cuota ni campo de consumo inventado. |

Los auxiliares nuevos registran la cuota previa en el almacenamiento de métricas y dejan que la lógica bajo prueba seleccione los perfiles. No simulan el resultado de selección ni generan las identidades de modelo que luego se comprueban.

## Hallazgos anteriores y nuevos

H-01 a H-04 de la revisión de pruebas anterior permanecen **resueltos**, con enrutamiento histórico `para: desarrollador`, `destino: resolver`, cerrado. El delta añadido no invalida sus correcciones.

**Hallazgos nuevos: ninguno.** No queda trabajo que enrutar desde esta revisión de pruebas. La comprobación de las correcciones de producción corresponde a la reevaluación de código.

## Instantánea revisada

SHA-256:

- `skills/orquestar/test_fallos_arnes.py`: `4E6B3715BC6EE9D16FD4512BD9D99B3AFE95D4163C476A7DF4192EC229F0AD91`.
- `skills/orquestar/test_arnes_ausente.py`: `E8D70DF749D6E82C4C136EAC64325DAE7CD86FF02E1E8AE51653F30BAF416797`.
