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
