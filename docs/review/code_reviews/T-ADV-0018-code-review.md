# Revisión de Código: T-ADV-0018

- **Tarea**: `docs/plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md`
- **Diseño**: `docs/design/T-ADV-0018-design.md`
- **Arquitectura**: `docs/requirements/platform_plan.md` (`DEC-P10`)
- **Archivos revisados**: `skills/orquestar/orquestar.py`, `skills/telegram_gateway/gateway.py`, `skills/orquestar/SKILL.md`, `skills/telegram_gateway/SKILL.md`
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.67 / 10**. Sin hallazgos críticos ni altos.

## Análisis estático

- **Compilación y formato**: compilación de `skills/orquestar/orquestar.py`, `skills/telegram_gateway/gateway.py` y sus módulos de prueba, así como `git diff --check`, verificados en verde con `adevv orquestar --verificar`.
- **Linter / tipado / dependencias**: N/A (proyecto stdlib sin linter/tipado configurado ni cambios de manifiestos o dependencias).
- **Seguridad del delta**: sin secretos, credenciales ni invocaciones de shell (`shell=False`).

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| Corrección | 9 | Detección acotada a `ADEVV_HOME/versions/<X.Y.Z>/`, publicación atómica del PID del hijo con reversión (`terminate`/`wait`) si falla `os.replace`, consumo de `ADEVV_RECARGA` tras confirmar la propiedad del PID, preservación de estado (`n`, `sin_progreso`, `esperado` en `bucle`; `desde` en `escuchar`), prioridad de `PARADA` y limpieza en `finally` condicionada al PID propietario. |
| Seguridad | 10 | Validación estricta de versión (`\d+\.\d+\.\d+`), comprobación `is_relative_to(home / 'versions' / version)`, ejecución sin shell y eliminación inmediata de `ADEVV_RECARGA` del entorno del hijo al arrancar. |
| Conformidad | 10 | Cumple íntegramente `CA-M-1`..`CA-M-4`, el triaje de `T-ADV-0018`, `docs/design/T-ADV-0018-design.md` y `DEC-P10`, operando únicamente dentro de `skills/` sin tocar `adevv/` ni `tests/features/`. |
| Calidad | 10 | Código claro y conciso; `gateway.py` reutiliza las funciones de `motor` (`orquestar.py`) sin duplicar lógica. |
| Eficiencia | 9 | Coste por ciclo limitado a una lectura local de `active.json` y comprobación de ruta en disco, sin red ni enumeración de procesos del SO. |
| Documentación | 10 | Docstrings concisos en las tres funciones nuevas y actualización fiel de `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md`. |

## Hallazgos

### 🔵 BAJA — Lectura del PID en el bucle de espera de `recibir_recarga` sin capturar `OSError` transitorio

- **Ubicación**: `skills/orquestar/orquestar.py:123-126`
- **Destino**: `descartar`
- **para**: `desarrollador`
- **Detalle**: En `recibir_recarga`, el bucle de espera ejecuta `(root / pid_file).read_text(encoding='utf-8')` sin capturar `OSError`. Aunque el archivo de PID ya existe antes de lanzar el hijo y `os.replace` es atómico, en Windows una lectura concurrente en el instante exacto del reemplazo podría recibir un `PermissionError` transitorio en lugar de reintentar en la siguiente iteración de 50 ms. Riesgo práctico despreciable.
