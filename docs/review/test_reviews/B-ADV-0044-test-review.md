**Veredicto:** APROBADO

# B-ADV-0044 · Reevaluación C1 de las pruebas de D30

**Media 9,75/10.** La regresión reproduce las dos consecuencias de D30. Con el `script` multilínea, la métrica de Hades atribuye a Claude la aprobación citada y el preflight permite cerrar la ficha pese al rechazo propio. El control de una línea pasa en ambos consumidores.

## Reproducción y control

Las dos pruebas usan el mismo texto de informe. «Incluye esta plantilla» continúa el párrafo citado. La aprobación sigue a `</script>` y una línea vacía la separa del rechazo propio. La única diferencia entre las entradas son los dos saltos de línea que rodean al JSON `{}`.

| Entrada | Dictamen del proveedor | Preflight de la versión |
|---|---|---|
| Reproducción con `{}` en su propia línea | La única métrica de Hades contiene `('claude', 'APROBADO')`. La aserción esperaba `('claude', 'RECHAZADO')` y falló antes de comprobar las llamadas efectivas. | `pendientes_cierre` devolvió `[]` tras confirmar el informe canónico junto con la ficha completada. |
| Control con el `script` en una línea | El arnés observó una sola llamada a Claude con el modelo `principal` y una única métrica de Hades con `RECHAZADO`. | `pendientes_cierre` identificó `B-DEMO-0001` por «informe rechazado». |

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Ambas entradas recorren `motor.agente` y `pendientes_cierre` en subpruebas separadas. El fallo en las métricas deja observable la decisión de cierre. |
| Aserciones | 9/10 | Se comprueban el dictamen registrado, el proveedor y el modelo llamados. El preflight exige que el ID y el motivo aparezcan en la misma entrada mediante subcadenas. |
| Rojo correcto | 10/10 | Los dos fallos son de aserción y muestran los efectos previstos en D30. El control alcanza las mismas comprobaciones con la misma preparación. |
| Estabilidad | 10/10 | Cada prueba crea su propio repositorio Git temporal, aísla su configuración y simula respuestas fijas de los proveedores. Las expectativas son independientes del reloj y del orden de ejecución. |

## Estado de los hallazgos

- **Anteriores de C1.** H1–H4 y N1–N10 siguen resueltos. El delta añade la reproducción y el control de D30.
- **Anteriores de producto.** D27–D29 constan como resueltos en la revisión D anterior.
- **D30 · 🟠 Alta.** La reproducción solicitada queda cubierta en C1. El defecto de producto persiste. Destinataria: Artemisa (`desarrollador`). Destino: `resolver` en C2. En ambas presentaciones, el principal debe registrar su rechazo en una sola llamada y el preflight debe mantener pendiente la ficha por «informe rechazado».
- **Nuevos en C1.** Ninguno.

## Evidencia

El delta de pruebas desde `489edd627f4a5743e15e8b714ecbad45ca292a44` coincide con el adjunto. Se reutilizó la evidencia del árbol `e7e74007e1c5a6458b96a60a6f79623e4f4a8ed8`. La ejecución focalizada registró `FF.`, dos métodos en 2,186 s y dos fallos de aserción en el método multilínea (código 1). Ruff selectivo (`E9,F63,F7,F82`) pasó sobre `skills/orquestar/test_progreso.py` con código 0. El proyecto carece de tipador configurado.
