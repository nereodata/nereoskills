# Revisión de Código: T-ADV-0014

- **Tarea**: `docs/plan/tasks/T-ADV-0014-agentes-configurados-y-estado-de-cuota-en-estado.md`
- **Diseño de referencia**: `docs/design/T-ADV-0014-design.md`
- **Archivos de producción revisados**:
  - `skills/orquestar/orquestar.py`
  - `skills/orquestar/SKILL.md`
  - `skills/telegram_gateway/SKILL.md`
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.6 / 10**

## Análisis Estático y Evidencias Verificadas

- **Compilación Python (`py_compile`)**: ✅ En verde sobre el árbol `585fe04fda` (`skills/orquestar/orquestar.py` y `skills/orquestar/test_estado_agentes.py`).
- **Formato y whitespace (`git diff --check`)**: ✅ En verde sobre el árbol `585fe04fda`.
- **Pruebas verificadas en `orquestar_evidencias.jsonl`**: ✅ 8 tests nuevos en `test_estado_agentes.py`, más regresiones `ReservaCuotaTests` (5), `RolesTests` (5), `EscaladaTests` (13) y `test_status` del gateway (1).
- **Secretos y dependencias**: ✅ Sin secretos ni credenciales expuestas en el delta; sin cambios de manifiestos ni nuevas dependencias.
- **Linter / tipado estático**: N/A (no configurados en el proyecto).

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Corrección** | 9.5/10 | `detalle_estado()`, `fecha_estado()` y `perfil_estado()` resuelven correctamente dificultad, rol ejecutor (`artemisa`/`atenea`), escalada, ajustes de `hades`, reservas heredadas, ventana móvil inclusiva de 5 h con conversión a zona local, suma de tokens sin duplicar `razonamiento`, persistencia de `modelo_cuota`/`cuota_espera_s` al conmutar a reserva, retrocompatibilidad con `sin_cuota`/`espera_s` y separación de la espera global. `leer_metricas()` tolera líneas en escritura o truncadas. |
| **Seguridad** | 10/10 | Sin credenciales expuestas, sin ejecución de subprocesos adicionales ni mutación de estado durante las consultas `--estado` y `/estado`. |
| **Conformidad** | 10/10 | Fiel al triaje de `T-ADV-0014`, a `docs/design/T-ADV-0014-design.md` y a `DEC-P09` (modificaciones de código acotadas a `skills/`). |
| **Calidad** | 9.5/10 | Código conciso, cohesivo y alineado con el estilo de `orquestar.py`, reutilizando `leer_metricas()` en `rechazos()`, `detalle_estado()`, `resumen()` y `parte()` sin duplicar lógica entre CLI y Telegram. |
| **Eficiencia** | 9.5/10 | Un único recorrido lineal de `orquestar_metricas.jsonl` para construir el resumen de ventana y cuotas; sin bloqueos ni operaciones de red. |
| **Documentación** | 9.5/10 | Docstrings claros en las funciones nuevas y actualización fiel de `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md`. |

## Hallazgos

### 🔵 BAJA — Tolerancia defensiva si `hades` se configurase como booleano en `orchestration.json`
- **Ubicación**: `skills/orquestar/orquestar.py` (línea 1421).
- **para**: `desarrollador`
- **destino**: `descartar`
- **Detalle**: `ajustes(config(root).get('hades', {}), paso, dificultad=dificultad)` asume que `hades` es un diccionario cuando está presente (igual que hacen `construir_prompt_agente` y `agente` en las líneas 144 y 1069). Si en algún proyecto se definiese `"hades": false` en `orchestration.json`, `config(root).get('hades', {})` devolvería `False`. Es un caso hipotético fuera del esquema documentado de roles en `SKILL.md`.
