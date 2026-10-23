# Revisión de Pruebas: T-ADV-0017

- **Tarea**: `docs/plan/tasks/T-ADV-0017-canal-limpio-de-prompts-en-subagentes.md`
- **Archivo revisado**: `skills/orquestar/test_agente_prompt.py`
- **Referencia**: CA-M-1..CA-M-3, triaje C1 y contrato de `docs/design/T-ADV-0017-design.md`. Sin `.feature`, conforme al triaje.
- **Ronda**: Reevaluación de las correcciones al informe anterior.
- **Veredicto**: **APROBADO**
- **Puntuación media**: **8.75 / 10**. Sin hallazgos críticos ni altos.

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| Cobertura | 9 | Los 16 tests cubren las fuentes y su prioridad, stdin válido, rechazo de blancos, exclusión git, seguimiento, limpieza normal y excepcional, preservación de rastreados, subcarpetas y externos, y rutas relativas en raíz. |
| Aserciones | 9 | Verifican texto y argumentos del agente, ausencia de invocación ante blancos, existencia del temporal durante la ejecución, desaparición posterior, propagación de SystemExit con código 2 y conservación del contenido externo. |
| Rojo correcto | 9 | El resumen aportado es coherente con contratos pendientes de implementar. El parche del helper diseñado requiere que este exista y puede impedir alcanzar algunas asercciones en esta fase; no es un defecto del fixture. Sin trazas completas, no se puede atribuir individualmente cada fallo/error del resumen. |
| Estabilidad | 8 | Temporales aislados y limpieza registrada, sin reloj ni red; agente y seguimiento simulados. La protección frente a lecturas accidentales de stdin solo se aplica a tres casos; los restantes caminos de prompt/archivo conservan una dependencia evitable de la entrada del ejecutor. |

## Reevaluación de hallazgos anteriores

| Hallazgo anterior | Estado | Evidencia en las pruebas actuales |
| :--- | :--- | :--- |
| ALTA — Prioridad de fuentes y fallback válido | **resuelto** | Líneas 54-128: prompt directo, combinación de prompt y archivo con textos distintos, archivo sin lectura de stdin, stdin válido con paso exacto del texto y rechazo de blancos directos/de archivo sin invocar al agente. Los tres primeros casos protegen stdin con una excepción. |
| ALTA — Orden de limpieza y salida por cuota | **resuelto** | Líneas 130-185: los side_effect comprueban existencia durante la ejecución; se comprueba borrado posterior tanto en retorno normal como ante RuntimeError y SystemExit. Este último debe propagarse con código 2, por lo que un error de argparse no satisface el caso. |
| ALTA — Preservación de ficheros externos | **resuelto** | Líneas 187-233: preservación de rastreados y subcarpetas; temporal externo independiente con contenido conservado y mandato recibido por el agente. Los casos de raíz usan argumentos relativos con cwd simulado al proyecto temporal. |

## Hallazgos nuevos

### 🟡 MEDIA — Protección incompleta de stdin en caminos de prompt/archivo

- **Ubicación**: `skills/orquestar/test_agente_prompt.py:105` y casos de archivo desde la línea 116, excepto el caso de prioridad de la línea 79.
- **Destino**: `resolver`.
- **para**: `desarrollador`.
- **Detalle**: Los casos de mandato directo en blanco y varios casos de archivo dejan `sys.stdin.read` sin simular. Si una regresión intenta recurrir a stdin tras un mandato en blanco o lee stdin anticipadamente, estas pruebas pueden consumir entrada del ejecutor, fallar de forma distinta según el entorno o bloquearse. El caso específico de prioridad de archivo ya detecta esa lectura, de modo que esto no deja una laguna alta de cobertura funcional, pero reduce la estabilidad del resto de la suite.
- **Corrección sugerida**: Extender el parche `sys.stdin.read` con `side_effect=AssertionError(...)` a todos los casos que proporcionan `--prompt` o `--prompt-file`, manteniendo stdin simulado con contenido solo en sus propios casos de fallback/validación.

## Evidencia y alcance

Revisión estática del archivo de pruebas y sus estados preparados, contrastada con tarea, contrato de diseño e informe anterior. No se ha leído código de producción ni ejecutado pruebas. No se dispone de un diff contra la ronda anterior; se ha contrastado el archivo actual con los hallazgos documentados.

Salida de rojo suministrada por el invocante:

```text
Ran 16 tests in 0.184s
FAILED (failures=3, errors=10)
```

El resumen acredita una ejecución roja declarada, sin permitir diagnosticar cada error. Los casos que parchean el helper todavía pendiente pueden fallar antes de alcanzar las aserciones de comportamiento; estas deberán alcanzarse al implementar. La aprobación evalúa la calidad de las pruebas, no certifica una implementación en verde.

El fixture `.git` es simulado y el seguimiento se controla mediante mocks; la prueba de `exclude` comprueba escritura real en un directorio temporal, sin constituir una integración con git real. No se aportan resultados de comprobaciones estáticas; la tarea declara que no hay linter/tipado configurados. No se modifica código ni pruebas durante esta revisión.
