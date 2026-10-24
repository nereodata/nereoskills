---
id: T-ADV-0018
title: "Auto-recarga automática del bucle y del gateway de Telegram al cambiar la versión activa de Adevv"
type: funcional
weight: 100
dificultad: media
version: "v0.5.0"
status: completed
depende_de: []
origen: "Evitar tener que reiniciar manualmente bucles o gateways en otros proyectos tras instalar una nueva versión de Adevv"
created_at: 2026-10-24
updated_at: 2026-10-24
---

# T-ADV-0018: Auto-recarga automática del bucle y del gateway de Telegram al cambiar la versión activa de Adevv

## 🎯 Objetivo de Negocio
Lograr que cuando se instale o active una nueva versión de Adevv en `~/.adevv/active.json`, todos los procesos `gateway.py` (en escucha de Telegram) y `orquestar.py` (entre pasos del bucle) que estén corriendo en cualquier proyecto desde una versión anterior en `~/.adevv/versions/<X.Y.Z>/` detecten el cambio y se reemplacen cooperativamente por el script de la nueva versión activa entre ciclos (conforme a `DEC-P10`, sin modificar `adevv/updater.py` ni el escenario `@CA-F03-05` de `tests/features/actualizacion_automatica.feature`) sin requerir reinicio manual ni interrumpir un paso o mensaje en mitad de su ejecución.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Detección de versión más nueva en `orquestar.py` y `gateway.py`):** Se añade en los motores de `skills/` (`skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py`, conforme a `DEC-P09`/`DEC-P10`) una función auxiliar que compara el directorio de versión desde el que se está ejecutando el script actual (`Path(__file__).resolve().parents[2]`, cuando reside dentro de `~/.adevv/versions/<ver>/` o `$ADEVV_HOME/versions/<ver>/`) con el directorio de la versión activa indicada en `~/.adevv/active.json`. Si existe una versión activa distinta cuyo script homólogo (`skills/orquestar/orquestar.py` o `skills/telegram_gateway/gateway.py`) existe en disco, devuelve la ruta del nuevo script y la nueva versión.
- [x] **CA-M-2 (Auto-reemplazo cooperativo del gateway entre vueltas de polling):** En `escuchar()` de `skills/telegram_gateway/gateway.py`, al inicio de cada vuelta de polling (cuando no hay ningún mensaje en procesamiento y antes de pedir `actualizaciones`), si detecta que la versión activa en `~/.adevv/active.json` ha cambiado respecto a la versión en ejecución, lanza o reemplaza el proceso hacia el nuevo `gateway.py` conservando `sys.argv[1:]` y el `root` del proyecto (actualizando `telegram.pid` si aplica) y termina limpiamente el proceso antiguo registrándolo en el log (`[gateway] recargado a versión X.Y.Z`). Durante la instalación y la petición en curso, el proceso mantiene intactos los archivos de su versión (`DEC-P01`, `RF-F03-08`, `CA-F03-05`, `DEC-P10`).
- [x] **CA-M-3 (Auto-reemplazo cooperativo del bucle entre pasos):** En `bucle()` de `skills/orquestar/orquestar.py`, al inicio de cada iteración antes de calcular o ejecutar el siguiente paso (nunca a mitad de un paso), si detecta que la versión activa en `~/.adevv/active.json` ha cambiado respecto a la versión en ejecución, transfiere la ejecución al nuevo `orquestar.py` conservando `sys.argv[1:]` y `orquestar.pid` y registrándolo en la salida (`[orquestar] recargado a versión X.Y.Z`).
- [x] **CA-M-4 (Pruebas unitarias y documentación en `skills/`):** Pruebas unitarias en `skills/orquestar/test_recarga.py` y `skills/telegram_gateway/test_recarga_gateway.py` (ejecutables con `adevv orquestar --verificar "python -m unittest skills/orquestar/test_recarga.py skills/telegram_gateway/test_recarga_gateway.py"`, sin tocar `adevv/` ni `tests/features/`, conforme a `DEC-P09`/`DEC-P10`) verifican que tanto `bucle()` entre pasos como `escuchar()` entre ciclos de polling detectan el cambio de versión activa y delegan al script nuevo sin perder argumentos ni estado; se actualiza `SKILL.md` en ambas skills.

## 🔬 Triaje de Alcance
- **Subfase A: Definición** → `[SKIP]` Lógica interna de auto-recarga cooperativa entre iteraciones en `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py` con contrato completo en `CA-M-1`..`CA-M-4` y respaldo arquitectónico en `DEC-P10` (compatible con `DEC-P01`, `RF-F03-08` y `@CA-F03-05` de `tests/features/actualizacion_automatica.feature`); se verifica mediante pruebas unitarias en `skills/orquestar/test_recarga.py` y `skills/telegram_gateway/test_recarga_gateway.py`.
- **Subfase B: Diseño** → `[EXEC]` Documento `docs/design/T-ADV-0018-design.md` con el mecanismo de detección de `~/.adevv/active.json` y transferencia limpia de proceso/PID entre iteraciones en Windows y POSIX.
- **Subfase C1: Pruebas (Red Phase)** → `[EXEC]` Pruebas unitarias en `skills/orquestar/test_recarga.py` y `skills/telegram_gateway/test_recarga_gateway.py` para detección de cambio de versión activa, transferencia de argumentos/PID y continuidad cuando la versión no cambia o el script homólogo no existe.
- **Subfase C2: Implementación (Green Phase)** → `[EXEC]` Implementación en `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py` dentro de las rutas autorizadas `skills/`.
- **Subfase D: QA** → `[EXEC]` Revisión de Hades (`/review-code`) sobre el delta completo con `adevv orquestar --agente hades`.
- **Subfase E: Documentación** → `[EXEC]` Documentación de la auto-recarga al cambiar de versión activa en `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md`.
- **Subfase F: Cierre** → `[EXEC]` Cierre de tarea y commit semántico.
- **Verificación al cierre:** `python -m unittest skills/orquestar/test_recarga.py skills/telegram_gateway/test_recarga_gateway.py`
