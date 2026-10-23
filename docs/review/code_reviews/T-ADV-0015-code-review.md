# Revisión de Código: T-ADV-0015

- **Tarea**: `docs/plan/tasks/T-ADV-0015-control-remoto-bucle-y-metricas-en-telegram.md`
- **Diseño de referencia**: `docs/design/T-ADV-0015-design.md`
- **Archivos de producción revisados**:
  - `skills/telegram_gateway/gateway.py`
  - `skills/telegram_gateway/SKILL.md`
  - `skills/orquestar/orquestar.py`
  - `skills/orquestar/metricas.py`
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.7 / 10**

## Análisis Estático y Evidencias Verificadas

- **Compilación Python (`py_compile`)**: ✅ En verde sobre el árbol `6085703d6f` (`skills/telegram_gateway/gateway.py`, `skills/telegram_gateway/test_gateway_control.py`, `skills/orquestar/orquestar.py`, `skills/orquestar/metricas.py`).
- **Formato y whitespace (`git diff --check`)**: ✅ En verde sobre el árbol `6085703d6f`.
- **Pruebas verificadas en `orquestar_evidencias.jsonl`**: ✅ 11 pruebas nuevas en `test_gateway_control.py`, 19 pruebas de regresión en `tests/test_telegram_gateway.py` y 10 pruebas en `skills/orquestar/test_metricas.py`.
- **Secretos y dependencias**: ✅ Sin secretos ni credenciales expuestas en el delta; sin cambios en manifiestos ni dependencias.
- **Linter / tipado estático**: N/A (no configurados en el proyecto).

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Corrección** | 9.5/10 | `/parar` y `/stop` verifican `orquestar.pid`, invocan `motor.excluir(root)` y crean `orquestar.parar` sin borrar el PID; `/lanzar` y `/run` evitan duplicar procesos con `orquestar.pid` activo, consultan el estado previsto, invocan `motor.en_fondo(root, argumentos=[])` aislando `sys.argv` del gateway y capturan `SystemExit` ante condiciones de carrera; `/metricas` y `/metrics` delegan en `metricas.consultar` con filtro por defecto `ultima` y tratan `ValueError`/`OSError` sin resultados parciales. |
| **Seguridad** | 10/10 | La comprobación de usuario autorizado precede a cualquier lectura o escritura en disco; `en_fondo` ejecuta `subprocess.Popen` con lista de argumentos fija (`argumentos=[]` desde Telegram) sin `shell=True`, impidiendo inyección de argumentos o comandos. |
| **Conformidad** | 10/10 | Fiel al triaje de `T-ADV-0015`, al diseño `docs/design/T-ADV-0015-design.md` y a `DEC-P09` (cambios de código acotados a `skills/`). |
| **Calidad** | 9.5/10 | Extracción limpia de `consultar(root, items, filtro)` en `metricas.py` y parámetro opcional `argumentos=None` en `en_fondo`, sin duplicar lógica entre CLI y gateway. |
| **Eficiencia** | 9.5/10 | Lectura y agregación lineal bajo demanda sin procesos adicionales ni bloqueos en el bucle de escucha. |
| **Documentación** | 10/10 | Docstrings actualizados en funciones y módulo, constante `AYUDA` alineada y documentación completa de `/lanzar`, `/parar` y `/metricas` en `skills/telegram_gateway/SKILL.md`. |

## Hallazgos

### 🔵 BAJA — Espacio final cuando el estado previsto no tiene paso ni identificador
- **Ubicación**: `skills/telegram_gateway/gateway.py` (líneas 242-243).
- **para**: `desarrollador`
- **destino**: `descartar`
- **Detalle**: Cuando `estado[1:3]` es `(None, None)` (por ejemplo, si el estado devuelto es `FIN` o `ESPERA`), `paso` resulta `''` y la cadena formateada `f'... Siguiente estado previsto: {estado[0]} {paso}'` incluye un espacio en blanco al final. Es puramente cosmético.
