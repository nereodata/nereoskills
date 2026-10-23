# Revisión de Código: T-ADV-0016

- **Tarea**: `docs/plan/tasks/T-ADV-0016-ejecucion-en-segundo-plano-de-telegram-gateway.md`
- **Diseño de referencia**: `docs/design/T-ADV-0016-design.md` y `DEC-P09` (`docs/requirements/platform_plan.md`)
- **Archivos de producción revisados**:
  - `skills/telegram_gateway/gateway.py`
  - `skills/telegram_gateway/SKILL.md`
  - `skills/orquestar/orquestar.py`
  - `skills/orquestar/SKILL.md`
  - `docs/review/versions/v0.4-revision.md`
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.8 / 10**

## Análisis Estático y Evidencias Verificadas

- **Compilación Python (`py_compile`)**: ✅ En verde sobre el árbol `4415deab89` (`skills/telegram_gateway/gateway.py`, `skills/telegram_gateway/test_gateway_fondo.py`, `skills/orquestar/orquestar.py`, `tests/test_orquestar.py`).
- **Formato y whitespace (`git diff --check`)**: ✅ En verde sobre el árbol `4415deab89`.
- **Pruebas verificadas (`adevv orquestar --verificar`)**: ✅ En verde sobre el árbol `4415deab89`:
  - `python -m unittest discover -s skills/telegram_gateway -p test_gateway*.py` (26 tests OK)
  - `python -m unittest discover -s tests -p test_telegram_gateway.py` (19 tests OK)
  - `python -m unittest discover -s tests -p test_orquestar.py -k AvisosTelegramTests` (7 tests OK)
- **Secretos y dependencias**: ✅ Sin secretos ni credenciales expuestas en el delta ni en argumentos de subprocesos; sin dependencias externas nuevas.
- **Linter / tipado estático**: N/A (no configurados en el proyecto).

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Corrección** | 9.8/10 | `pid_vivo` comprueba el estado real del proceso sin señales destructivas (`OpenProcess` con `PROCESS_QUERY_LIMITED_INFORMATION` + `GetExitCodeProcess == 259` en Windows y `os.kill(pid, 0)` en POSIX); `reservar` usa creación exclusiva (`'x'`), recupera marcas muertas/inválidas y limpia `telegram.parar` obsoleto; `en_fondo` publica el PID hijo y revierte la reserva ante cualquier fallo; `--gestionado` sincroniza la publicación del PID antes de escuchar; `limpiar` verifica propiedad del PID antes de borrar marcas en `finally`; `escuchar` respeta `telegram.parar` antes del polling y entre mensajes sin cortar una conversación en curso; `iniciar_gateway` no bloquea ni aborta el bucle si falla. |
| **Seguridad** | 10/10 | Ninguna credencial viaja por línea de comandos (`--root` y `--gestionado`), las llamadas a `subprocess.Popen` y `subprocess.run` usan listas de argumentos sin `shell=True`, y los avisos de error usan `type(error).__name__` sin exponer tokens. |
| **Conformidad** | 10/10 | Cumple íntegramente `CA-M-1` a `CA-M-4`, el triaje de `T-ADV-0016`, `docs/design/T-ADV-0016-design.md` y `DEC-P09`: código de producción restringido a `skills/`, subproceso invocado explícitamente como `gateway.py` (clasificado como `'gateway'` por `adevv/processes.py` sin modificarlo) y las tres marcas añadidas a `PROPIOS`. |
| **Calidad** | 9.5/10 | Funciones cohesivas (`pid_vivo`, `reservar`, `limpiar`, `en_fondo`, `parar`, `iniciar_gateway`), manejo explícito de recursos y descriptores (`CloseHandle` en `finally` y `with open`), sin código muerto ni duplicación. |
| **Eficiencia** | 9.5/10 | Comprobación ligera de archivo por iteración/mensaje en `escuchar`, consulta de proceso acotada al arranque/parada y `timeout=10` en el autoarranque desde `orquestar.py`. |
| **Documentación** | 10/10 | Docstrings claros en todas las funciones añadidas, `skills/telegram_gateway/SKILL.md` y `skills/orquestar/SKILL.md` actualizados sin patrones prohibidos por `RF-F01-04`, y entrega documentada en `docs/review/versions/v0.4-revision.md`. |

## Hallazgos

### 🔵 BAJA — Doble comprobación de `pid_vivo` al ejecutar `--fondo` desde `main()`
- **Ubicación**: `skills/telegram_gateway/gateway.py` (líneas 410-414 y 318-320).
- **para**: `desarrollador`
- **destino**: `descartar`
- **Detalle**: En `main()`, la rama `if a.fondo:` consulta `pid_vivo(root)` para devolver `0` de forma idempotente cuando ya hay un gateway vivo (útil para que `iniciar_gateway` no reporte fallo si el gateway ya estaba activo), mientras que `en_fondo(root)` vuelve a comprobarlo dentro de `reservar(root)` ante colisión `FileExistsError` y sale con código distinto de cero. Ambas comprobaciones son complementarias (salida amistosa en CLI/autoarranque más guarda atómica contra condición de carrera en `reservar`), por lo que se descarta cualquier cambio.
