---
id: B-ADV-0003
title: "Aislamiento de iniciar_gateway en tests de bucle, PATH de usuario en subprocesos y colisión 409 en gateway.py"
type: bug
weight: 50
dificultad: sencilla
version: "v0.6.0"
status: completed
depende_de: []
created_at: 2026-10-24
updated_at: 2026-10-25
---

# B-ADV-0003: Aislamiento de iniciar_gateway en tests de bucle, PATH de usuario en subprocesos y colisión 409 en gateway.py

## 🎯 Descripción del Fallo

Durante el uso en producción del gateway de Telegram en múltiples proyectos simultáneos (`Adevv`, `Adayy`, `Afinn`), se han detectado tres anomalías que provocan que el bot de Telegram deje de responder o entre en conflicto:

1. **Fuga de subprocesos `gateway.py --fondo` al ejecutar tests que llaman a `motor.bucle()` (`tests/test_orquestar.py`)**:
   - **Causa raíz**: En `skills/orquestar/orquestar.py`, `bucle(a, root)` invoca `iniciar_gateway(root)` al arrancar (salvo cuando `a.estado` es `True`). En `tests/test_orquestar.py`, solo `AvisosTelegramTests.setUp` mockea `motor.iniciar_gateway`, mientras que `OrquestarRegressionTests`, `EscaladaTests`, `DificultadTests` y `ReservaCuotaTests` llaman a `motor.bucle(...)` sin mockear `iniciar_gateway` ni aislar `TELEGRAM_BOT_TOKEN` / `TELEGRAM_ALLOWED_USER_IDS` del entorno o del directorio actual. Si existen credenciales en el entorno al correr la suite de cierre de versión (`python -m unittest discover -s tests`), los tests lanzan procesos reales `gateway.py --fondo` en carpetas temporales `%TEMP%\tmp...` con el mismo token del proyecto, compitiendo por `getUpdates` contra el gateway real.
   - **Comportamiento esperado**: Ningún test unitario de `tests/test_orquestar.py` (ni de `skills/`) debe cruzar la frontera de procesos reales de `iniciar_gateway` salvo los tests que prueban explícitamente `iniciar_gateway` con `subprocess.run` simulado.

2. **Pérdida de rutas del `PATH` de usuario en Windows al lanzar el gateway desde entornos con `PATH` recortado**:
   - **Causa raíz**: Cuando el gateway o el bucle se lanza en segundo plano desde un IDE o proceso padre en Windows cuyo `PATH` de proceso no incluye el `Path` de usuario del registro (`~/.local/bin`, `%APPDATA%\npm`, `%LOCALAPPDATA%\OpenAI\Codex\bin\...`), `shutil.which('claude')` o `shutil.which('codex')` devuelve `None` dentro de `gateway.py::invocar()` y lanza `RuntimeError('No se encuentra el arnés "claude" en el PATH.')`.
   - **Comportamiento esperado**: En Windows (`os.name == 'nt'`), al resolver el ejecutable de un arnés en `orquestar.py` / `gateway.py` (si `shutil.which` no lo encuentra en el `PATH` actual), completar o consultar las rutas habituales de instalación de usuario (`~/.local/bin`, `%APPDATA%\npm`, `%LOCALAPPDATA%\agy\bin`) o el `Path` de usuario de Windows para no fallar cuando el proceso padre tiene un `PATH` parcial.

3. **Detección y manejo de conflicto `HTTP 409 Conflict` en `gateway.py::actualizaciones()`**:
   - **Causa raíz**: Cuando por accidente se lanza un segundo proceso de `gateway.py` con el mismo `TELEGRAM_BOT_TOKEN` (p. ej. uno en primer plano y otro en `--fondo`, o en dos carpetas distintas con el mismo `.env`), la API de Telegram devuelve `HTTPError 409 Conflict` a ambos procesos de forma indefinida cada pocos segundos, registrando solo `[gateway] sin respuesta de Telegram (HTTPError)` y dejando ambos bots inutilizados.
   - **Comportamiento esperado**: Si `urllib.request.urlopen` en `actualizaciones()` captura un `HTTPError` con código `409`, registrar explícitamente en el log `[gateway] conflicto 409 en Telegram: otra instancia está escuchando con el mismo token` (y tras varios `409` consecutivos o si no es propietario de `telegram.pid`, detener la escucha duplicada limpiamente).

## 📋 Reproducir

1. Definir `TELEGRAM_BOT_TOKEN` y `TELEGRAM_ALLOWED_USER_IDS` en el entorno y ejecutar `python -m unittest discover -s tests` → las clases `OrquestarRegressionTests`, `EscaladaTests`, `DificultadTests` y `ReservaCuotaTests` ejecutan `iniciar_gateway(self.root)` real.
2. Lanzar `gateway.py --fondo` desde un proceso en Windows sin `~/.local/bin` en `os.environ['PATH']` y enviar un mensaje de conversación libre a un proyecto cuyo rol `atenea` usa `claude` → responde `No he podido procesarlo; mira el log del gateway.` con `RuntimeError('No se encuentra el arnés "claude" en el PATH.')`.
3. Tener dos procesos `gateway.py` usando el mismo `TELEGRAM_BOT_TOKEN` → `telegram.log` se llena de `[gateway] sin respuesta de Telegram (HTTPError)` por conflicto `409`.

## 📋 Evidencias

- `C:\Users\Iván Moreno\SW\Adayy\repo\telegram.log`: 94 entradas consecutivas de `[gateway] sin respuesta de Telegram (HTTPError)` y `RuntimeError('No se encuentra el arnés "claude" en el PATH.')`.

## 📋 Triaje de Alcance

- **Subfase A: Definición** → `[SKIP]` (No altera requisitos de usuario de la especificación BDD; es robustez técnica interna y aislamiento de tests).
- **Subfase B: Diseño** → `[SKIP]` (Solución técnica localizada y sin nuevas decisiones arquitecturales en orquestar.py y gateway.py).
- **Subfase C1: Pruebas** → `[EXEC]` (Tests unitarios para aislamiento de iniciar_gateway en bucle, búsqueda en PATH de usuario en Windows y detección de colisión 409).
- **Subfase C2: Corrección** → `[EXEC]` (Aislar tests de test_orquestar.py, implementar buscar_ejecutable en orquestar.py y gateway.py, y gestionar 409 con detección de propietario de PID y corte limpio tras conflictos).
- **Subfase D: QA** → `[EXEC]` (Revisión aislada de Hades /review-code sobre el delta).
- **Subfase E: Documentación** → `[SKIP]` (Comportamiento interno sin cambios de comandos ni opciones de usuario).
- **Subfase F: Cierre** → `[EXEC]` (Commit semántico y cierre del bug).
- **Verificación al cierre**: `python -m unittest tests/test_telegram_gateway.py tests/test_orquestar.py skills/orquestar/test_estado_agentes.py` (ejercita la suite de gateway y las suites de orquestador afectadas por el aislamiento y resolución de ejecutables).
