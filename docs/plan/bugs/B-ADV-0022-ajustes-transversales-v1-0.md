---
id: B-ADV-0022
title: "Ajustes transversales v1.0: PID huérfano en /cerrar y altas, salida de verificaciones en métricas, CHANGELOG, frontmatter y motivo de espera"
type: bug
weight: 50
dificultad: media
version: "v1.0.0"
status: planned
depende_de: [B-ADV-0021]
origen: "revisar-version v1.0 (docs/review/versions/v1.0-arquitectura.md), hallazgos 🟡/🔵 con destino resolver: H-04, H-05, H-06, H-09 y H-12"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0022: Ajustes transversales v1.0

## 🎯 Descripción del Fallo

Hallazgos de la revisión transversal de v1.0 con destino `resolver`, que se corrigen antes de cerrar la versión:

1. **H-04 🟡 · `/cerrar` y las altas por Telegram toman un `orquestar.pid` huérfano por un bucle vivo.** `skills/telegram_gateway/cierre_version.py` (línea ~42, `validar()`) y `gateway.py` (líneas ~283, 289 y 308, `responder()`) usan `(root / motor.PID).exists()` en vez de `motor.pid_vivo(root)`. Tras una caída del bucle o un reinicio, `/cerrar vX.Y confirmo` responde «Existe un PID del bucle» mientras `/estado` dice «parado», y `/tarea` deja el alta en el buzón sin registrar. **Esperado:** usar `motor.pid_vivo(root)` y cambiar «sin PID» por «sin bucle vivo» en `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md`.
2. **H-05 🟡 · La salida de cada verificación se copia en `orquestar_metricas.jsonl`.** En `verificar()` (`orquestar.py`, línea ~2143), `registrar(root, {..., **fila})` duplica la `salida` (hasta 32 KiB) que añadió B-ADV-0006, y el fichero se relee varias veces por paso y cada 30 s durante la espera de cuota. **Esperado:** excluir `salida` de la fila de métricas; `registrar_fallo_suite` ya la lee de la evidencia.
3. **H-06 🟡 · Al CHANGELOG de 1.0.0 le faltan entregas visibles para el usuario:** T-ADV-0023 (`/cerrar vX.Y [confirmo]`), T-ADV-0025, B-ADV-0010, B-ADV-0014, B-ADV-0016, B-ADV-0017, B-ADV-0019 y B-ADV-0021 (cuando se resuelva). Hay que regularizar también las líneas en blanco del bloque «Corregido».
4. **H-09 🔵 · Reescritura de claves del frontmatter duplicada.** `bloquear_sin_progreso` (línea ~2162) y `registrar_fallo_suite` (línea ~2238) repiten el `re.sub(rf'^{clave}:…')` con separadores de cabecera distintos (`re.split(r'\n---[ \t]*(?:\n|$)')` frente a `split('\n---\n', 1)`). **Esperado:** un único helper.
5. **H-12 🔵 · `/estado` dice «esperando cuota» durante la espera por fallo del arnés.** `esperar(..., motivo='fallo del arnés')` (B-ADV-0011) escribe `orquestar.espera` igual que la espera de cuota, y `parte()` (líneas ~1923 y 2531) siempre muestra «esperando cuota hasta HH:MM». **Esperado:** guardar el motivo y mostrarlo.

## 📋 Reproducir
1. H-04: dejar un `orquestar.pid` con un PID muerto y enviar `/cerrar v1.0 confirmo` o `/tarea …` por Telegram.
2. H-05: ejecutar `adevv orquestar --verificar "<comando con salida>"` y comprobar que la última fila de `orquestar_metricas.jsonl` contiene `salida`.
3. H-12: forzar una espera por fallo del arnés y consultar `adevv orquestar --estado`.

## 📋 Evidencias
- `docs/review/versions/v1.0-arquitectura.md`, hallazgos H-04, H-05, H-06, H-09 y H-12.
