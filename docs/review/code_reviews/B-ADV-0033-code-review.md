**Veredicto:** RECHAZADO

# B-ADV-0033 — Revisión de código


## Alcance y limitaciones

Revisión del delta de `314f3d8df8660f4057e2723a41f9c992e76c0c05` respecto de `9a143486c663f2afe2bbe4e7ef3a30743c65532a`, exclusivamente para B-ADV-0033:

- Enrutado en `skills/orquestar/intervencion.py`.
- Wrapper y carga del módulo.
- Prompt de los pasos.
- Selección de ramas hotfix.
- CLI `--enrutar-hallazgo`.
- Llamada a `detectar_bloqueo` desde `orquestar.py`.

Se contrastaron el diff y el contexto actual adjuntos con la ficha y el diseño aportados. B-ADV-0032, las pruebas como código de producción y `dist/` quedan excluidos. No se modificó producción ni se realizaron commits.

No fue posible leer directamente el árbol, el agente Hades ni la skill instalada: la consola y el kernel de lectura fallaron con `registered Core launch requires an installed app`. Se aplicó el contenido de review-code adjunto. La correspondencia de los artefactos con el árbol se toma de la declaración del invocante; no se afirma una comprobación independiente del checkout.

Los hallazgos se deducen por lectura del código suministrado, sin ejecutar pruebas adicionales.

## Análisis estático

| Comprobación | Evidencia y resultado |
| --- | --- |
| Errores del diff | Evidencia aportada para el árbol `0f6e0402a3`: `git diff --check 9a143486c663f2afe2bbe4e7ef3a30743c65532a`, mediante `--verificar`, código 0. Reutilizada; no relanzada. |
| Regresión autorizada | Evidencia aportada mediante `--verificar`: `python -m unittest tests.test_orquestar.HallazgosHadesRoutingTests`, 1 test OK, 0,025 s. Reutilizada; no relanzada. |
| Formato y lint | Evidencia aportada de `--calidad --base 9a143486c663f2afe2bbe4e7ef3a30743c65532a`: ambos OMITIDOS por ausencia de herramientas. Omisión justificada; no equivale a ejecución en verde. |
| Base de calidad | La ficha no registró `base_calidad`; se utiliza como referencia el padre de implementación indicado por el invocante. |
| Tipado y seguridad automatizada | Sin herramientas configuradas, según el invocante; no ejecutados. |
| Secretos | Inspección por lectura del delta incluido en el alcance: no se observan credenciales ni secretos literales añadidos. No constituye un escaneo del repositorio. |
| Dependencias | Sin dependencias nuevas en el alcance aportado. Auditoría: N/A. |
| Suite completa | No ejecutada, conforme al triaje y al mandato. |

## Puntuaciones

| Dimensión | Puntuación | Motivo |
| --- | --- | --- |
| Corrección | 5/10 | La vía explícita conserva los destinos, pero la salvaguarda puede convertir un destino declarado en pregunta humana. |
| Seguridad | 9/10 | No se observan secretos añadidos ni ejecución del contexto como código. |
| Conformidad | 6/10 | La estructura sigue el diseño; los casos descritos incumplen la conservación del destino. |
| Calidad | 8/10 | Wrapper y enrutador claros; la extracción textual presenta limitaciones relevantes. |
| Eficiencia | 9/10 | Búsqueda acotada y escrituras limitadas a los artefactos previstos. |
| Documentación | 8/10 | API documentada y mandato operativo; la garantía descrita excede el comportamiento de la salvaguarda. |

**Media: 7,50/10.** Existen dos hallazgos de severidad alta.

## Hallazgos

### H-01 — 🟠 ALTA: truncar antes de extraer el destino puede crear la pregunta humana prohibida

**Para:** desarrollador (Artemisa).  
**Destino:** resolver.  
**Ubicación:** `skills/orquestar/intervencion.py`, función `detectar_bloqueo`, construcción de `contexto` y llamada a `enrutar_hallazgo`; integración desde `bucle` en `orquestar.py`.

**Evidencia**

Se construye:

```python
contexto = (
    tarea.read_text(encoding='utf-8').rsplit('\n## ', 1)[-1]
    + '\n' + (salida or '')
)[-4000:]
destino = destino_hallazgo(contexto)
enrutar_hallazgo(..., destino or 'humano', ...)
```

El recorte sucede antes de resolver el destino.

**Caso concreto**

Una tarea queda `blocked` con `pendiente_de: humano` por el error que la salvaguarda pretende recuperar. Su última sección contiene `Destino: especificador`. El paso devuelve más de 4000 caracteres posteriores sin repetir el destino y no existe una pregunta pendiente.

El recorte elimina íntegramente el destino de la tarea. La extracción devuelve vacío y `solicitar` crea una entrada humana. Una salida con el destino al principio y suficiente texto posterior presenta el mismo problema.

**Impacto**

El tamaño de la salida determina el destinatario. Se reproduce el bloqueo humano indebido que B-ADV-0033 debe impedir, aunque el destino esté declarado en los artefactos recibidos.

**Contrato afectado**

Criterio de aceptación 1 y salvaguarda de destino explícito en contexto o salida descrita en la resolución.

**Corrección requerida**

Resolver el destino sobre las fuentes pertinentes antes de recortar la evidencia que se conserva. Definir precedencia para declaraciones contradictorias sin convertir la pérdida causada por el recorte en autorización de intervención humana.

**Comprobación propuesta**

Contexto con destino especificador en la tarea y salida larga sin destino: debe conservarse `pendiente_de: especificador` sin crear pregunta. No se ejecutó ni añadió esta comprobación durante la revisión.

### H-02 — 🟠 ALTA: la extracción no reconoce destinos explícitos con la etiqueta Markdown resaltada

**Para:** desarrollador (Artemisa).  
**Destino:** resolver.  
**Ubicación:** `skills/orquestar/intervencion.py`, expresión regular de `destino_hallazgo` y fallback de `detectar_bloqueo`.

**Evidencia**

El patrón exige que tras `destino` haya únicamente espacios antes de `:`, `=` o `|`:

```python
r'\bdestino\s*(?::|=|\|)\s*[*`_ ]*(artemisa|especificador|humano)\b'
```

Admite marcas Markdown alrededor del valor, pero no después de la etiqueta y antes del separador.

**Caso concreto**

Con tarea `blocked` / `pendiente_de: humano`, sin pregunta pendiente y sección final:

```markdown
**Destino**: especificador
```

El patrón no coincide: encuentra `**` donde espera espacios o separador. `destino_hallazgo` devuelve vacío y el detector utiliza `humano`, creando una pregunta persistente. La etiqueta entre backticks presenta el mismo resultado.

**Impacto**

Una declaración inequívoca en un informe Markdown puede terminar en intervención humana por su presentación. Ni el diseño ni la ficha aportados limitan la salvaguarda a etiquetas sin formato.

No se afirma haber verificado el formato del agente instalado, cuya lectura no fue posible.

**Contrato afectado**

Conservación del destino declarado por Hades y criterio de aceptación 1.

**Corrección requerida**

Establecer y soportar el formato de declaración producido por los informes y el contexto del paso, incluyendo el resaltado de la etiqueta, o consumir una representación estructurada validada. Un detalle de formato no debe degradar silenciosamente un destino explícito a humano.

**Comprobación propuesta**

Las declaraciones con etiqueta simple, resaltada y entre backticks deben conservar el mismo destino y no crear preguntas. No se ejecutaron ni añadieron pruebas durante esta revisión.

## Conformidad con diseño y arquitectura

La CLI y el wrapper delegan al enrutador compartido. `artemisa` pasa a `planned`; `especificador` pasa a `blocked` con su responsable; solo la rama `humano` llama a `solicitar`. La selección de `hotfix/v*` permite alcanzar el paso existente `especificar`.

En el alcance aportado se mantienen Python >=3.11, biblioteca estándar y separación entre motor e intervención. No se observa una desviación de capas que requiera una DEC.

Los defectos se concentran en la salvaguarda que interpreta la tarea y la salida del paso. Ambos tienen una entrada concreta y un camino directo hasta `solicitar`; deben resolverse antes de aprobar B-ADV-0033. Las evidencias verdes aportadas se conservan sin atribuirles cobertura sobre estos casos no verificados.
