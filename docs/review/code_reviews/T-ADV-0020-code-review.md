# Code Review: T-ADV-0020

- **Veredicto**: APROBADO
- **Media**: 9.6 / 10

## Análisis estático

- `git diff --check`: en verde sobre el árbol verificado (`f8147b72d3`).
- `python -m compileall -q skills/orquestar skills/telegram_gateway`: en verde.
- Suite de triaje (`30 tests` en `test_informe_agentes.py`, `test_estado_agentes.py`, `test_agentes.py`, `test_gateway_control.py` y `test_firma_gateway.py`): en verde.
- Linter / tipador / auditoría de dependencias: N/A (sin configuración de linter/tipador y sin cambios en manifiestos ni dependencias).

## Puntuaciones

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Corrección** | 9.5 / 10 | Cumple CA-M-1..4: `parte()` y `resumen()` dejan de incluir el bloque de agentes; `informe_agentes()` enumera los roles (`artemisa`, `hades`, `atenea`, `clio`, `cronos`, `development`), sus variantes (`base`, `dificultad`, `paso`, `escalada`) y reservas incluso en `FIN`/`PARAR`; aplica la precedencia de cuota (agotamiento vigente > `rate_limits.primary` nativo de Codex > ventana móvil de 5 h) con validación numérica (`numero_cuota`) y protección ante `OverflowError` y JSONL truncado. |
| **Seguridad** | 10 / 10 | Lectura local de solo consulta línea a línea, sin inyecciones, credenciales ni efectos laterales sobre archivos de señal (`PID`, `ESPERA`) cuando se invoca `--agentes` / `--agents` o `/agentes` / `/agents`. |
| **Conformidad** | 10 / 10 | Alineado con `docs/design/T-ADV-0020-design.md`, el triaje de la tarea y las decisiones `DEC-P09`/`DEC-P10` (biblioteca estándar y cambios acotados a `skills/`). |
| **Calidad** | 9.5 / 10 | Extracción limpia de `consumo_cuotas()` reutilizada por `informe_agentes()` y `detalle_estado()`, funciones breves y nombres coherentes con el resto de `orquestar.py` y `gateway.py`. |
| **Eficiencia** | 9.5 / 10 | `parte()` y `resumen()` dejan de leer métricas de ventana de 5 h; `cuota_codex()` lee sesiones de forma perezosa línea a línea y solo se invoca cuando existen perfiles del arnés `codex`. |
| **Documentación** | 9.5 / 10 | Docstrings concisos en todas las funciones añadidas y actualización fiel de `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md`. |

## Hallazgos

- **[🔵 BAJA] Tolerancia a valores `null` explícitos en subbloques `dificultad` / `pasos`** (`skills/orquestar/orquestar.py`, `perfiles_agentes`, líneas 1576-1580) — `destino: descartar`
  `base.get('dificultad', {})` y `base.get('pasos', {})` devuelven `None` si la clave existe con valor `null` en `orchestration.json`; usar `(base.get('dificultad') or {})` sería ligeramente más defensivo, aunque el resto del motor ya asume diccionarios válidos en esas claves.
