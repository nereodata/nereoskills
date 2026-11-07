# Code Review: B-ADV-0027 — `reintentos_acumulados` sube la dificultad en tareas multiturno con progreso y deshace las bajadas manuales en el Markdown

- **Veredicto**: **APROBADO** (media **9.3 / 10**)
- **Archivos auditados**:
  - `skills/orquestar/orquestar.py`

## Análisis estático
- `git diff --check`: limpio en `orquestar_evidencias.jsonl` para el árbol `d5607c03c62cd692331ff53c4783ac13664545f2`.
- Formato y lint del delta (`adevv orquestar --calidad --base 80a482d04a24e15ab3e55a65efae784053a22940`): ejecutado sin escritura; etapas de formato y lint omitidas justificadamente por ausencia de herramientas configuradas en `task_config.yaml`.
- Verificación del triaje (`python -m unittest tests.test_orquestar.DificultadTests tests.test_orquestar.BloqueoSinProgresoTests`): 14 pruebas en verde en `orquestar_evidencias.jsonl` sobre el mismo árbol (`d5607c03c62cd692331ff53c4783ac13664545f2`).
- Tipado, linter y escáner de secretos: N/A (sin herramientas configuradas; sin secretos expuestos ni cambios de dependencias).

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Corrección** | 9 / 10 | `reintentos_acumulados` reinicia `pasos` cuando un paso registra `progreso: True` o Hades emite `APROBADO`; `sincronizar_dificultad` detecta bajadas manuales en el frontmatter respecto a la última dificultad en métricas y persiste un evento de promoción manual que resetea contadores y fija la nueva base. |
| **Seguridad** | 10 / 10 | Sin credenciales, inyecciones ni superficie externa nueva; lectura de métricas centralizada en `leer_metricas`. |
| **Conformidad** | 10 / 10 | Totalmente alineado con el triaje de `B-ADV-0027` y la arquitectura de `skills/orquestar/orquestar.py`; incorpora además las mejoras H-01 y H-02 señaladas en `/review-test`. |
| **Calidad** | 9 / 10 | Código limpio y consistente con el estilo del módulo; reemplaza el parseo manual de JSONL en `reintentos_acumulados` por `leer_metricas(root)`. |
| **Eficiencia** | 9 / 10 | Reutiliza `despues = firma(root, a.docs)` al cierre del turno en `bucle()`, evitando llamadas repetidas a `git` y `arbol`. |
| **Documentación** | 9 / 10 | Docstrings precisos en las funciones nuevas (`nivel_dificultad`, `sincronizar_dificultad`); sin comentarios superfluos ni documentación de usuario invalidada. |
| **Media** | **9.3 / 10** | **APROBADO** (sin hallazgos 🔴 ni 🟠) |

---

## Hallazgos

- **[H-01] 🔵 BAJA (`para: desarrollador`, `destino: descartar`) — Doble invocación a `sincronizar_dificultad` desde `comprobar_promocion` y guarda redundante `if not dif_md:`** (`skills/orquestar/orquestar.py:946-947`, `1486`, `1494`):
  `comprobar_promocion` llama a `sincronizar_dificultad(root, iid)` al inicio y a continuación invoca `reintentos_acumulados(root, iid)`, que vuelve a ejecutar `sincronizar_dificultad(root, iid)`. Además, `dificultad_de(root, iid)` siempre devuelve `'sencilla'`, `'media'` o `'dificil'`, por lo que `if not dif_md:` nunca se activa. El impacto es despreciable y no requiere cambios adicionales.
