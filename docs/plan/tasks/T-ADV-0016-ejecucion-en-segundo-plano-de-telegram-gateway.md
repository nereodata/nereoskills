---
id: T-ADV-0016
title: "Ejecución en segundo plano de adevv telegram (--fondo, --parar) y auto-arranque desde orquestar"
type: funcional
weight: 400
dificultad: media
version: "v0.4.0"
status: completed
depende_de: ["T-ADV-0015"]
origen: "Gestión desatendida del gateway de Telegram sin ocupar una terminal dedicada"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0016: Ejecución en segundo plano de adevv telegram (--fondo, --parar) y auto-arranque desde orquestar

## 🎯 Objetivo de Negocio
Permitir que el gateway de Telegram se gestione en segundo plano con `adevv telegram --fondo` y `adevv telegram --parar` igual que el bucle, que `adevv/processes.py` no confunda el proceso del gateway con un bucle de orquestación activo al actualizar/sincronizar, y que `adevv orquestar` levante automáticamente el gateway en segundo plano cuando el proyecto tenga credenciales de Telegram configuradas.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (`--fondo` y `--parar` en `gateway.py`):** `skills/telegram_gateway/gateway.py` añade `--fondo` (lanza el gateway desacoplado escribiendo su PID en `telegram.pid` y salida en `telegram.log`, verificando que no haya ya un `telegram.pid` vivo) y `--parar` (señaliza parada mediante `telegram.parar` o termina el proceso registrado y limpia `telegram.pid` / `telegram.parar`). `telegram.pid`, `telegram.log` y `telegram.parar` se incluyen en `PROPIOS` de `orquestar.py` para quedar excluidos de git.
- [x] **CA-M-2 (Auto-arranque desde `orquestar.py`):** Al iniciar `bucle()` o `en_fondo()` en `skills/orquestar/orquestar.py` (en ejecución real, no en `--estado`), si `telegram(root)` devuelve credenciales válidas y no hay un `telegram.pid` con proceso vivo en `root`, lanza automáticamente el gateway en segundo plano (`gateway.py --fondo` o función equivalente) sin bloquear ni abortar el bucle si falla.
- [x] **CA-M-3 (Compatibilidad con clasificación de procesos de gateway):** En `skills/telegram_gateway/gateway.py`, `--fondo` lanza el subproceso invocando `gateway.py` para que `adevv/processes.py` (que ya clasifica `gateway.py` y `adevv telegram` como `"gateway"` y no como `"bucle"` sin requerir modificar `adevv/processes.py`, conforme a `DEC-P09`) no reporte el gateway en escucha como «bucle en marcha» ni bloquee actualizaciones o sincronización de arneses.
- [x] **CA-M-4 (Pruebas y documentación):** Pruebas unitarias en `skills/telegram_gateway/test_gateway_fondo.py` (o en `tests/test_telegram_gateway.py` y `tests/test_orquestar.py`, conforme a `DEC-P09` para operar dentro de `skills/`); documentación actualizada en `skills/telegram_gateway/SKILL.md` y `skills/orquestar/SKILL.md`.

## Triaje
- Subfase A: [EXEC] Escenarios de ciclo de vida y autoarranque en el feature existente de Telegram.
- Subfase B: [EXEC] Propiedad del PID, parada cooperativa y arranque opcional desde el motor (DEC-P09).
- Subfase C1: [EXEC] Pruebas aisladas de PID, procesos, polling y autoarranque en skills/telegram_gateway/test_gateway_fondo.py.
- Subfase C2: [EXEC] Gateway, PROPIOS y puntos de entrada del bucle; sin modificar adevv/processes.py.
- Subfase D: [EXEC] Hades sobre el delta completo.
- Subfase E: [EXEC] Skills de gateway y orquestar, diseño y revisión de versión; changelog delegado a /release.
- Subfase F: [EXEC] Cierre y commit.
- Verificación al cierre: `python -m unittest discover -s skills/telegram_gateway -p test_gateway*.py`, `python -m unittest discover -s tests -p test_telegram_gateway.py` y `python -m unittest discover -s tests -p test_orquestar.py -k AvisosTelegramTests`: ciclo de vida, control remoto, entradas del motor y regresión de gateway/avisos. La clase antigua de avisos simula iniciar_gateway en su fixture para no lanzar procesos con sus credenciales ficticias; no cambia sus aserciones. Compilación Python del delta y `git diff --check` mediante --verificar. No hay linter, tipado ni escáner de secretos configurados; inspección del delta sin credenciales ni dependencias nuevas.

## Resultado y decisiones sin preguntar
- Implementados --fondo/--parar, PID vivo/obsoleto, salida a telegram.log y parada cooperativa con limpieza por propietario. El hijo invoca gateway.py, compatible con la clasificación existente, sin tocar adevv/processes.py.
- Autoarranque opcional desde las dos entradas del bucle; sin arranque en consultas ni con telegram:false o credenciales incompletas. Fallos del lanzador no abortan el bucle.
- Rojo inicial: 15 pruebas, 4 fallos y 15 errores por capacidades ausentes (incluye subtests); evidencia en %TEMP%/T-ADV-0016-red.txt. Verde: 52 pruebas del triaje (26 gateway/control/lifecycle, 19 gateway existente, 7 avisos), compilación y whitespace verificados con adevv orquestar --verificar. Hades reutilizó evidencia del árbol 4415deab89.
- Hades: especificación APROBADO 9.4/10, pruebas APROBADO 9.6/10 y código APROBADO 9.8/10; observaciones bajas con destino descartar aplicadas. Sin deuda ni bloqueos.
- Diseño y validación humana diferida documentados en docs/design/T-ADV-0016-design.md y docs/review/versions/v0.4-revision.md. Changelog delegado a /release. Pruebas sin red, modelos ni procesos gateway reales.
