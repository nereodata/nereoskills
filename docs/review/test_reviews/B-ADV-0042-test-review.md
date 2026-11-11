# B-ADV-0042 · Revisión independiente de pruebas

**Veredicto: APROBADO**
**Media: 9,25/10**

## Alcance y evidencia

Revisión estática del delta completo suministrado de `tests/test_orquestar.py`, contrastado con el criterio de aceptación de B-ADV-0042. Se evalúan exclusivamente las pruebas y su preparación de estados, sin revisar producción.

Se utiliza el mandato adjunto de Hades y `/review-test`: la herramienta local no permitió abrir los archivos indicados. No se modificó el checkout ni se ejecutaron pruebas.

Evidencia acreditada para el árbol `cb9d269afdc697c93aaa61328161a641552aec63`:

- Compilación del archivo de pruebas en verde.
- Ejecución Linux del nuevo caso en rojo por el comportamiento esperado: el descendiente permanece vivo en estado `S`, después de retornar la captura.
- La aserción del resultado completo del padre se supera antes de comprobar el descendiente.

## Puntuaciones

| Criterio | Nota | Evaluación |
|---|---:|---|
| Cobertura | 9/10 | Reproduce un hijo real de larga duración, con ambas salidas redirigidas, mientras el padre emite JSON válido y termina. Comprueba conservación del resultado y terminación del hijo. |
| Aserciones | 9/10 | Compara código, stdout, stderr y ambos indicadores; consulta además el estado real del descendiente. La limpieza del `finally` ocurre después de las comprobaciones y no puede convertir el fallo en éxito. |
| Rojo correcto | 10/10 | La ejecución Linux falla concretamente porque el hijo sigue vivo; alcanza las aserciones sin errores de sintaxis, imports o preparación. |
| Estabilidad | 9/10 | Usa un directorio de prueba, PID explícito y espera acotada con reloj monotónico. Admite la entrega asíncrona de la señal y distingue un zombi de un proceso que continúa ejecutándose. |

La extracción de `comprobar_hijo_terminado` conserva las comprobaciones del caso preexistente.

## Hallazgos

Ninguno.

## Limitaciones

El dictamen acredita la calidad de las pruebas, no la corrección del arreglo. La evidencia Linux corresponde al rojo previo a la corrección. No se aportan resultados de lint o formato, cuyas herramientas constan como ausentes, ni de ejecución del conjunto completo de `SubprocesoColgadoTests`. Estas limitaciones no invalidan el rojo dirigido presentado ni requieren repetir la compilación acreditada.
