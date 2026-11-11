**Veredicto:** APROBADO

# B-ADV-0033 — Reevaluación de código H-01/H-02

**Media: 9,00/10.** Sin hallazgos críticos ni altos.

## Alcance y limitaciones

Revisión estática independiente del delta exacto de reanudación adjunto para el árbol identificado por el invocante como `eea5e845d1`.

Se revisaron los cambios de producción en `skills/orquestar/intervencion.py` y su conformidad con el diseño, el plan de plataforma y la documentación modificada. El contexto completo del enrutador se utilizó para comprobar la integración. Las pruebas se toman como evidencia, sin repetir `/review-test`. No se amplía la revisión a otros bugs incorporados desde `base_calidad`.

El acceso local permanece indisponible por `registered Core launch requires an installed app`. Conforme al mandato, no se reintentaron lecturas ni ejecuciones. La correspondencia entre adjuntos y checkout se acepta de la declaración del invocante; no se afirma una comprobación independiente del disco.

No se modificó producción, no se ejecutaron pruebas, no se hicieron commits ni se delegó. El informe se devuelve para transcripción por la misma limitación de acceso.

## Análisis estático y verificación

| Comprobación | Evidencia y tratamiento |
|---|---|
| Regresión específica | Evidencia aportada mediante `adevv orquestar --verificar`: `python -m unittest tests.test_orquestar.HallazgosHadesRoutingTests`, **5 tests OK**. Reutilizada sin repetir. |
| Integridad del diff | Evidencia aportada mediante `--verificar`: `git diff --check HEAD`, **código 0**. Reutilizada sin repetir. |
| Formato y lint | Ejecución aportada de `--calidad --base e37c0f41b61271d57e69ef849cfd7203f991b48e --aplicar`: etapas omitidas por ausencia de herramientas, sin cambios. No equivale a herramientas ejecutadas en verde. |
| Calidad sin escritura | No ejecutada por indisponibilidad del acceso local. Omisión declarada; no se atribuye al comando con `--aplicar` equivalencia con esta ejecución. |
| Tipado y scanner de secretos | Sin configuración, según el invocante. No ejecutados. |
| Inspección de seguridad | No se observan secretos añadidos, evaluación del texto como código ni nuevas vías de ejecución en el delta adjunto. |
| Dependencias | Sin dependencias ni manifiestos modificados. Auditoría de dependencias: N/A. |
| Suite completa | No ejecutada, conforme al mandato. |

## Puntuaciones

| Dimensión | Puntuación | Motivo |
|---|---:|---|
| Corrección | 9/10 | Resuelve sobre fuentes completas, aplica la precedencia documentada y conserva el fallback humano únicamente cuando no encuentra destino reconocido. |
| Seguridad | 9/10 | Mantiene la validación cerrada de destinos; el texto se interpreta como datos. |
| Conformidad | 9/10 | Implementa el contrato actualizado de H-01/H-02 sin alterar interfaces ni introducir desviaciones arquitectónicas. |
| Calidad | 9/10 | Corrección localizada, legible y sin duplicar el enrutado o la persistencia existentes. |
| Eficiencia | 9/10 | Búsquedas lineales sobre las fuentes disponibles, sin nuevas lecturas de disco ni dependencias. |
| Documentación | 9/10 | Docstring, diseño y changelog describen la selección de la última declaración y su precedencia entre fuentes. |

## Reevaluación de hallazgos anteriores

### H-01 — RESUELTO

El destino se calcula antes del recorte:

```python
destino = destino_hallazgo(salida) or destino_hallazgo(seccion)
contexto = (seccion + '\n' + (salida or ''))[-4000:]
```

La extracción devuelve la última coincidencia reconocida de cada fuente. Por tanto, prevalece la última declaración de la salida; en su ausencia, la última de la sección final de la tarea.

El recorte afecta exclusivamente al contexto conservado. El destino seleccionado se entrega por separado al enrutador y se persiste en el campo `Destino` de tarea y revisión. Una fuente larga ya no elimina la decisión utilizada para enrutar.

**Responsable anterior:** desarrollador / Artemisa.
**Destino:** resuelto; sin acción pendiente.

### H-02 — RESUELTO

El patrón admite marcas de énfasis y código alrededor de la etiqueta y del valor, incluidos los formatos exigidos por el diseño: etiqueta simple, `**Destino**:`, `**Destino:**`, etiqueta entre backticks y `_Destino_:`.

Los valores reconocidos continúan limitados a `artemisa`, `especificador` y `humano`. La normalización conserva la aceptación sin distinguir mayúsculas.

**Responsable anterior:** desarrollador / Artemisa.
**Destino:** resuelto; sin acción pendiente.

## Conformidad e integración

El delta conserva la firma del detector y delega en el enrutador existente. Los destinos técnicos siguen actualizando tarea y revisión; `humano` continúa usando `solicitar`. No cambia el contrato de preguntas persistidas ni las guardas previas del detector.

La modificación permanece en el motor existente, utiliza biblioteca estándar y no introduce dependencias inversas ni decisiones que requieran una DEC nueva.

## Hallazgos nuevos

Ninguno en el delta revisado.
