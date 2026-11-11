# Diseño Técnico: B-ADV-0033 — Enrutado fiel de hallazgos de Hades

## Cambios

- **[MODIFY]** `skills/orquestar/intervencion.py`: centraliza destinos válidos, extrae el destino declarado, actualiza tarea y revisión de versión para `artemisa` y `especificador`, y solo crea una pregunta para `humano`.
- **[MODIFY]** `skills/orquestar/orquestar.py`: expone `--enrutar-hallazgo`, lo transmite en el mandato de los pasos y entrega la salida al detector como salvaguarda.
- **[MODIFY]** `tests/test_orquestar.py` y `skills/orquestar/features/orquestacion.feature`: fijan la regresión de los tres destinos.

## Mapa de impacto

- Llamantes: `detectar_bloqueo()` y la CLI de `orquestar` usan el nuevo enrutador. `estado()` ya procesa `pendiente_de: especificador` mediante el paso `especificar`; `artemisa` vuelve a `planned` y retoma el paso de desarrollo existente.
- Pruebas: la cobertura previa de preguntas humanas conserva su contrato; se añade una regresión específica para evitar entradas humanas de los otros destinos.
- Decisiones contradichas: ninguna.
- Camino caliente: una búsqueda regular acotada sobre el contexto del hallazgo, sin I/O adicional salvo la anotación que ya requiere todo cambio de estado.

## Testeabilidad

El enrutador recibe destino y contexto explícitos. Las pruebas validan frontmatter, ausencia/presencia de pregunta y trazabilidad en la revisión de versión sin invocar arneses.

## Reanudación H-01/H-02 (v1.1.2)

El detector resuelve el destino sobre las fuentes completas antes de recortar la evidencia persistida a 4000 caracteres. Prevalece la última declaración reconocida de la salida del paso; sin ella, la última declaración de la sección final de la tarea. Esta regla permite que una decisión posterior sustituya a una anterior. El estado humano solo es el fallback si ninguna fuente declara un destino reconocido.

La extracción admite las marcas Markdown de énfasis y código alrededor de la etiqueta y del valor (`Destino:`, `**Destino**:`, `**Destino:**`, `` `Destino`: `especificador` ``, `_Destino_:`), sin cambiar el contrato de los tres destinos. La evidencia de enrutado conserva el destino elegido en su campo estructurado aunque el fragmento de contexto se recorte. No requiere dependencias ni una DEC de arquitectura nueva.

El único consumidor de destino_hallazgo es detectar_bloqueo; necesita la nueva selección de la última declaración en ambas fuentes. La llamada del bucle en orquestar.py conserva su firma. No se invalidan pruebas previas. RT-02 comprueba el campo Destino persistido tanto en tarea como en revisión de versión, incluso con evidencia recortada.
