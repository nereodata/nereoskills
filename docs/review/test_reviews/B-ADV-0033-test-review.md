# B-ADV-0033 — Revisión de pruebas

**Veredicto:** RECHAZADO

**Modo:** orquestado.
**Alcance:** clase `HallazgosHadesRoutingTests` de `tests/test_orquestar.py`, reanudación H-01/H-02 respecto a `e37c0f41b61271d57e69ef849cfd7203f991b48e`.

Revisión realizada exclusivamente sobre los adjuntos proporcionados como copia del checkout actual. No se ha consultado producción ni usado herramientas locales, cuyo entorno presenta el error `registered Core launch requires an installed app`. Esta limitación no constituye un defecto del producto. No se han modificado archivos, ejecutado pruebas ni creado commits.

## Puntuaciones

| Dimensión | Nota | Evaluación |
|---|---:|---|
| Cobertura | 7 | Cubre recorte, variantes Markdown y precedencia de salida; falta discriminar la última declaración de la tarea. |
| Aserciones | 9 | Comprueban ausencia de solicitud humana, estado persistido y selección del flujo esperado. |
| Rojo correcto | 9 | La evidencia aportada identifica llamadas indebidas a `solicitar`, coherentes con las regresiones buscadas. |
| Estabilidad | 9 | Directorio temporal por prueba y dependencias externas sustituidas; sin esperas ni servicios reales en los casos añadidos. |

**Media: 8,5/10.** Existe un hallazgo de severidad alta que impide aprobar.

## Evidencia considerada

El invocante aporta la ejecución mediante `--verificar` de:

```text
python -m unittest tests.test_orquestar.HallazgosHadesRoutingTests
Ran 4 tests
FAILED (failures=6)
```

Los seis fallos corresponden a solicitudes humanas indebidas en los dos casos de evidencia larga, la precedencia con salida larga y las etiquetas `**Destino**`, `` `Destino` `` y `_Destino_`. La variante `**Destino:**` ya pasa.

Este RED respalda que las pruebas detectan las regresiones indicadas; no es por sí mismo motivo de rechazo de las pruebas. No se ha reproducido la ejecución ni inspeccionado el registro local. No hay lint ni tipado configurados, según el contexto recibido.

## Hallazgos

### RT-01 — 🟠 ALTA — Falta una prueba que discrimine la última declaración de la tarea

- **Estado:** nuevo hallazgo de esta revisión de pruebas.
- **Para:** desarrollador.
- **Destino:** resolver.
- **Ubicación:** `test_detector_prioriza_ultima_declaracion_de_salida_sobre_tarea` y casos de detección sobre la tarea.

El contrato de reanudación exige seleccionar la **última declaración de la salida**, si existe; en su ausencia, la **última declaración de la tarea**.

La prueba de precedencia contiene dos declaraciones contradictorias en la salida y una sola en la tarea. Por tanto, discrimina correctamente la última declaración de salida y su prioridad sobre la tarea. Sin embargo, todos los casos que resuelven el destino desde la tarea contienen una única declaración.

Una implementación que elija correctamente la última declaración de salida, pero use la primera declaración de la tarea cuando no haya destino en la salida, podría superar todos los casos aportados y vulnerar el contrato.

**Corrección requerida:** añadir un caso sin declaración de destino en la salida y con dos declaraciones contradictorias en la tarea. Por ejemplo, `Destino: humano` seguido de `Destino: especificador`. Comprobar que no se llama a `solicitar`, que no aparecen preguntas humanas y que la tarea queda `blocked` con `pendiente_de: especificador`.

## Reevaluación de H-01/H-02

Los identificadores H-01/H-02 recibidos corresponden a hallazgos previos de código. Aquí se evalúa únicamente su cobertura por las pruebas:

| Aspecto | Resultado |
|---|---|
| H-01: conservar destino antes del recorte | Cubierto por declaraciones al inicio de tarea o salida y evidencia de 5000 caracteres. |
| H-01: última declaración de salida prevalece sobre tarea | Cubierto con destinos contradictorios y salida larga. |
| H-01: última declaración de tarea cuando no hay destino en salida | Pendiente: RT-01. |
| H-02: admitir etiquetas Markdown | Cubierto por las cinco variantes aportadas, con aserciones contra la escalada humana. |

No se emite juicio sobre la resolución de producción de H-01/H-02. Para aprobar las pruebas debe cerrarse RT-01; no se requiere ejecutar la suite completa.
