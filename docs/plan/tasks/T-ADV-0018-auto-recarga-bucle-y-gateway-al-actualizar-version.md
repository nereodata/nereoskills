---
id: T-ADV-0018
title: "Auto-recarga automática del bucle y del gateway de Telegram al cambiar la versión activa de Adevv"
type: funcional
weight: 100
dificultad: media
version: "v0.5.0"
status: blocked
pendiente_de: especificador
depende_de: []
origen: "Evitar tener que reiniciar manualmente bucles o gateways en otros proyectos tras instalar una nueva versión de Adevv"
created_at: 2026-10-24
updated_at: 2026-10-24
---

# T-ADV-0018: Auto-recarga automática del bucle y del gateway de Telegram al cambiar la versión activa de Adevv

## 🎯 Objetivo de Negocio
Lograr que cuando se instale o active una nueva versión de Adevv en `~/.adevv/active.json`, todos los procesos `gateway.py` (en escucha de Telegram) y `orquestar.py` (entre pasos del bucle) que estén corriendo en cualquier proyecto desde una versión anterior en `~/.adevv/versions/<X.Y.Z>/` detecten el cambio y se reemplacen automáticamente por el script de la nueva versión activa sin requerir reinicio manual ni interrumpir un paso o mensaje en mitad de su ejecución.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Detección de versión más nueva en `orquestar.py` y `gateway.py`):** Se añade una función auxiliar que compara el directorio de versión desde el que se está ejecutando el script actual (`Path(__file__).resolve().parents[2]`, cuando reside dentro de `~/.adevv/versions/<ver>/`) con `get_active_version_dir()` de `~/.adevv/active.json`. Si existe una versión activa distinta cuyo script homólogo (`skills/orquestar/orquestar.py` o `skills/telegram_gateway/gateway.py`) existe en disco, devuelve la ruta del nuevo script y la nueva versión.
- [ ] **CA-M-2 (Auto-reemplazo del gateway entre vueltas de polling):** En `escuchar()` de `skills/telegram_gateway/gateway.py`, al inicio de cada vuelta de polling (cuando no hay ningún mensaje en procesamiento y antes de pedir `actualizaciones`), si detecta que la versión activa en `~/.adevv/active.json` ha cambiado respecto a la versión en ejecución, lanza o reemplaza el proceso hacia el nuevo `gateway.py` conservando `sys.argv[1:]` y el `root` del proyecto (actualizando `telegram.pid` si aplica) y termina limpiamente el proceso antiguo registrándolo en el log (`[gateway] recargado a versión X.Y.Z`).
- [ ] **CA-M-3 (Auto-reemplazo del bucle entre pasos):** En `bucle()` de `skills/orquestar/orquestar.py`, al inicio de cada iteración antes de calcular o ejecutar el siguiente paso (nunca a mitad de un paso), si detecta que la versión activa en `~/.adevv/active.json` ha cambiado respecto a la versión en ejecución, transfiere la ejecución al nuevo `orquestar.py` conservando `sys.argv[1:]` y `orquestar.pid` y registrándolo en la salida (`[orquestar] recargado a versión X.Y.Z`).
- [ ] **CA-M-4 (Desbloqueo de sincronización/actualización frente a versiones antiguas):** Pruebas unitarias en `skills/orquestar/` y `skills/telegram_gateway/` verifican que tanto `bucle()` entre pasos como `escuchar()` entre ciclos de polling detectan el cambio de versión activa y delegan al script nuevo sin perder argumentos ni estado.

## Bloqueo de especificación (modo orquestado)
Hades `/review-spec`: **RECHAZADO**, hallazgo crítico `para: especificador`, `destino: resolver`. La recarga automática solicitada requiere conciliar CA-M-2/CA-M-3 con CA-F03-05/RF-F03-08/DEC-P01 y respaldar el alcance de v0.5 en `skills/` antes de implementar. No se requiere intervención humana. Instrucciones concretas en `docs/review/spec_reviews/T-ADV-0018-spec-review.md` y `docs/review/versions/v0.5-revision.md`.

El intento y su triaje se conservan en `wip/T-ADV-0018` (`5b335bd`); no hay cambios de producción. Verificación de este cierre documental: `git diff --cached --check` mediante `adevv orquestar --verificar`. Las pruebas funcionales previstas en WIP no se ejecutaron porque todavía no existen; tampoco se ejecutó la suite completa. El siguiente paso del bucle es `especificar`, no otra ejecución de desarrollo sin resolver el contrato.
