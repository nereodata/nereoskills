# Code Review: B-ADV-0028 — `/estado` en Telegram no indica por separado las tareas y los bugs de la versión

- **Veredicto**: **APROBADO** (media **9.8 / 10**)
- **Archivos auditados**:
  - `skills/orquestar/orquestar.py`
  - `docs/plan/bugs/B-ADV-0028-estado-telegram-no-desglosa-tareas-y-bugs-de-la-version.md`

## Análisis estático
- Verificación del triaje (`python -m unittest tests.test_telegram_gateway`): 25 pruebas en verde en `orquestar_evidencias.jsonl` sobre el árbol actual (`db8d9282a1b2f80f7fec5e860cfce1718c98398d`).
- Formato y lint del delta (`adevv orquestar --calidad --base c6ecf75e57cf0edb6751cd9c22179f323bd5bd7d`): ejecutado sin escritura; etapas de formato y lint omitidas justificadamente por ausencia de herramientas configuradas en `task_config.yaml`.
- Higiene del diff y análisis de seguridad/tipado: limpio; sin secretos expuestos, cambios de manifiestos ni superficie externa nueva.

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Corrección** | 10 / 10 | `parte()` deduplica y ordena las versiones abiertas por `vkey`, agrupa en `suyas` todos los ítems con la misma clave numérica (`vX.Y` y `vX.Y.0`), elige la etiqueta de versión más específica y desglosa por separado tareas (`task-dev`) y bugs (`bug-fix`) cerrados/totales, conservando el listado de ítems en curso y bloqueados. |
| **Seguridad** | 10 / 10 | Sin credenciales, inyecciones ni llamadas externas nuevas; solo agrega y formatea datos ya cargados por `backlog(root)`. |
| **Conformidad** | 10 / 10 | Cumple íntegramente el triaje de `B-ADV-0028` y unifica el criterio de agrupación de versiones por `vkey` con el de `estado()`. |
| **Calidad** | 9 / 10 | Código conciso, legible y alineado con el estilo de `skills/orquestar/orquestar.py`. |
| **Eficiencia** | 10 / 10 | Recorrido lineal en memoria sobre los ítems del backlog sin operaciones adicionales de E/S ni subprocesos. |
| **Documentación** | 10 / 10 | El docstring de `parte()` y las guías de `/telegram-gateway` y `/orquestar` permanecen vigentes y coherentes con el comportamiento. |
| **Media** | **9.8 / 10** | **APROBADO** (sin hallazgos 🔴 ni 🟠) |

---

## Hallazgos

- **[H-01] 🔵 BAJA (`para: desarrollador`, `destino: descartar`) — Construcción de listas intermedias para conteo y doble evaluación de `cuenta(...)` en `parte()`** (`skills/orquestar/orquestar.py:2699-2705`):
  `cuenta_t("completed")` y `cuenta_b("completed")` construyen listas de IDs únicamente para aplicar `len(...)`, y `cuenta('in_progress')` / `cuenta('blocked')` se evalúan dos veces en el condicional ternario (igual que en la implementación previa). Dado el tamaño reducido del backlog de una versión, el impacto es despreciable y no requiere cambios.
