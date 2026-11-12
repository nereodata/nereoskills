# B-ADV-0045 · Revisión de pruebas C1

**Veredicto: APROBADO** · Media **9,25/10**. Sin hallazgos críticos ni altos.

Se revisaron los seis casos de `EntornoRolTests` en `skills/orquestar/test_codex_resume_usage.py` frente al triaje C1 y los criterios de la ficha. La entrada es `motor.agente` para Hades. El doble de subproceso captura una copia del entorno efectivo y el comando de cada intento.

| Criterio | Nota | Evidencia |
| --- | ---: | --- |
| Cobertura | 9/10 | Cubre sesión nueva, reanudación con el identificador previo y recuperación tras código 1. En recuperación exige exactamente dos lanzamientos, primero reanudado y después nuevo. Los controles cubren Windows sin marca, Codex en POSIX y Claude en Windows. |
| Aserciones | 8/10 | Compara el entorno completo del hijo con el esperado, incluido el valor de cada variable conservada. Comprueba el entorno del padre al regresar, los argumentos de sandbox y aprobación y la ausencia de los indicadores que omiten el aislamiento o la validación del checkout. Los dos detalles siguientes limitan la precisión del doble. |
| Rojo correcto | 10/10 | El rojo anterior a C2 recogido en la ficha y aportado para esta revisión registra tres fallos de aserción por la marca heredada, tres controles verdes y cero errores. En recuperación, el primer entorno incorrecto detiene el bucle de aserciones. El test también exige el entorno correcto del segundo intento para pasar. |
| Estabilidad | 10/10 | Cada caso prepara un directorio temporal y un entorno conocido. La plataforma, la sesión y los códigos de salida están controlados. Los gestores de contexto restauran el estado al terminar. |

## Hallazgos

- 🟡 **Preservación del padre durante el lanzamiento** (`lanzar_rol`, líneas 38–40 y 59). Una implementación que retirase la marca de `os.environ` y la repusiera al volver del subproceso pasaría la prueba. Mientras tanto, otro lanzamiento podría heredar el entorno alterado. **Destino: resolver**. Comparar también `dict(os.environ)` con `self.padre` dentro de `proceso`, en cada intento.
- 🔵 **Herencia implícita del entorno** (`lanzar_rol`, línea 39). El doble accede a `kwargs['env']`. En los controles de alcance, una llamada válida que omita ese argumento heredaría el entorno del padre y el doble produciría un `KeyError`. **Destino: resolver**. Leer `kwargs.get('env')` y usar `os.environ` cuando el valor sea `None`, conservando el significado de un diccionario vacío.

## Evidencia y alcance

SHA256 calculado por Hades con `Get-FileHash -Algorithm SHA256` sobre los bytes de `task_config.yaml` del checkout: `8121DE183AD6A2E5C42ED3338B1F2182930EF4EEF20CF5D2BE0B9157B12E50B8`.

La evidencia aportada incluye `git diff --check` limpio. Formato y lint se omitieron por falta de herramientas. El rojo fue dirigido a la clase, sin ejecución de la suite completa. Esta lectura y la escritura del informe se realizaron con el control temporal del entorno de C1. La aceptación del lanzador corregido queda para D mediante la entrada real `--agente hades` en sesión nueva y reanudada. La ficha conserva también la verificación conjunta con B-ADV-0044.
