# Revisión de Pruebas: T-ADV-0016

- **Tarea**: `docs/plan/tasks/T-ADV-0016-ejecucion-en-segundo-plano-de-telegram-gateway.md`
- **Archivos de pruebas**: `skills/telegram_gateway/test_gateway_fondo.py` y `tests/test_orquestar.py` (`AvisosTelegramTests.setUp`)
- **Especificación de referencia**: `tests/features/telegram_gateway.feature` (`@T-ADV-0016`, líneas 184-225) y `docs/design/T-ADV-0016-design.md`
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.6 / 10**

## Reevaluación / Ampliación de alcance (Ronda 2)

- **Delta revisado**: Adición de `self.enterContext(patch.object(motor, 'iniciar_gateway'))` en `tests/test_orquestar.py::AvisosTelegramTests.setUp` (línea 221) y alineación del comando de verificación en el triaje de `T-ADV-0016` (`-k AvisosTelegramTests`).
- **Evaluación del delta**: `AvisosTelegramTests` ejecuta `motor.bucle()` inyectando credenciales ficticias (`CREDENCIALES`) para probar el envío de avisos HTTP; al añadirse el autoarranque del gateway en `bucle()`, aislar `motor.iniciar_gateway` en el `setUp` de esa clase evita lanzar subprocesos reales de `gateway.py --fondo` durante los 7 tests de regresión de avisos, sin alterar ninguna de sus aserciones ni debilitar la cobertura (ya que la invocación de `iniciar_gateway` desde `bucle` y `en_fondo` y su comportamiento interno están probados explícitamente en `test_gateway_fondo.py`).
- **Estado de hallazgos previos**:
  - 🔵 BAJA — Retorno no cero del subproceso en `iniciar_gateway` cuando ya hay un gateway vivo: `descartar` (sin cambios).

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Cobertura** | 9.5/10 | Los 15 tests de `test_gateway_fondo.py` cubren todos los escenarios operativos de `@T-ADV-0016` y el diseño (`--fondo`, clasificación como `'gateway'` por `_clasificar_linea_comandos`, no duplicación con PID vivo, recuperación de marcas inválidas/muertas, reversión ante fallo de `Popen`, `--parar` sin credenciales conservando `orquestar.pid` y `telegram.pid` vivo, limpieza idempotente con gateway parado, parada cooperativa antes del polling y entre mensajes, propiedad del PID en primer plano y en `--gestionado`, limpieza en `finally` ante excepción, autoarranque desde `en_fondo` y `bucle` con `timeout=10` y tolerancia a `OSError`, omisión en `--estado` / sin credenciales / `telegram: false`, y exclusión real en Git mediante `PROPIOS`), complementados por las 7 pruebas de regresión de `AvisosTelegramTests`. |
| **Aserciones** | 9.5/10 | Comprueban efectos observables y contratos reales en `test_gateway_fondo.py` y conservan intactas todas las aserciones de regresión en `AvisosTelegramTests`. |
| **Rojo correcto** | 9.5/10 | Los 15 tests nuevos fallaron en rojo en `%TEMP%/T-ADV-0016-red.txt` por las capacidades aún no implementadas antes del desarrollo y pasan en verde (15/15) junto con las 7 pruebas de `AvisosTelegramTests` tras aislar la frontera. |
| **Estabilidad** | 10/10 | Totalmente deterministas: el aislamiento de `motor.iniciar_gateway` en `AvisosTelegramTests.setUp` impide que los tests de avisos con credenciales simuladas lancen subprocesos reales del gateway en segundo plano. |

## Hallazgos

### 🔵 BAJA — Retorno no cero del subproceso en `iniciar_gateway` cuando ya hay un gateway vivo
- **Ubicación**: `skills/telegram_gateway/test_gateway_fondo.py` (líneas 171-183).
- **para**: `desarrollador`
- **destino**: `descartar`
- **Detalle**: `test_autoarranque_frontera_y_fallo_tolerado` verifica el camino con `returncode = 0` y la excepción `OSError`, mientras que la no duplicación con PID vivo se prueba directamente sobre `gateway.en_fondo` en `test_pid_vivo_no_duplica`. Como `iniciar_gateway` delega en `gateway.py --fondo` sin `check=True`, ambos tests en conjunto cubren el contrato sin necesidad de añadir otro caso.
