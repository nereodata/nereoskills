---
id: B-ADV-0021
title: "Volver atrás con bucles en marcha a un motor sin recarga mata el bucle en silencio"
type: bug
weight: 10
dificultad: media
version: "v1.0.0"
status: completed
depende_de: []
origen: "revisar-version v1.0 (docs/review/versions/v1.0-arquitectura.md), H-01 🟠 y H-07 🟡"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0021: Volver atrás con bucles en marcha a un motor sin recarga mata el bucle en silencio

## 🎯 Descripción del Fallo

**Causa raíz:** DEC-P13 (B-ADV-0009) permite instalar y conmutar `active.json` con bucles en marcha y extiende la recarga cooperativa de DEC-P10 a cualquier destino, también a los que no implementan el protocolo de recarga (anteriores a 0.5.0) o no aceptan los argumentos del proceso en marcha. `version_activa_distinta` (`skills/orquestar/orquestar.py`, hacia las líneas 180–197) no exige versión mínima y `recargar_version` (línea ~200) lanza el sucesor sin comprobarlo.

**Comportamiento observado:**
1. Con un bucle 1.0.0 en marcha (`adevv orquestar --fondo`), `adevv actualizar 0.4.0` instala y conmuta `active.json` a 0.4.0. El aviso dice «Los bucles desde v0.5 tomarán la versión al terminar su paso actual».
2. Al acabar el paso, el bucle lanza `~/.adevv/versions/0.4.0/skills/orquestar/orquestar.py`, escribe el PID del hijo en `orquestar.pid` y el padre termina con 0.
3. El motor 0.4.0 no conoce `ADEVV_RECARGA`: encuentra `orquestar.pid` y sale con «Ya hay un bucle en marcha». El bucle queda muerto sin aviso por Telegram y con un PID huérfano. Al gateway (`etiqueta='gateway'`) le pasa lo mismo.
4. Variante en 0.5–0.6.1: si el bucle se lanzó con una opción nueva de 1.0 (`--reintentos-arnes`, `--cuota-reset`, `--calidad`), el `argparse` del motor anterior rechaza los argumentos reenviados y el bucle también muere.

**Comportamiento esperado:** DEC-P13 y RF-F03-11 fijan una política explícita para la vuelta atrás con procesos en marcha cuando el destino no implementa la recarga o no acepta los argumentos. Por ejemplo: no recargar y avisar de que hace falta reiniciar a mano, rechazar ese caso, o recargar solo hacia versiones que declaren el protocolo. El bucle y el gateway nunca mueren en silencio. El aviso de `mensaje_actualizacion` y el README (línea ~25) dicen la verdad.

**Incluye H-07 (🟡, especificador):** §2 (opción 3, líneas 43–45) y DEC-P02 (línea 178) de `platform_plan.md` siguen describiendo una sincronización y una limpieza de versiones antiguas incondicionales. Con DEC-P13, `sincronizacion_bloqueada()` corta también `limpiar_versiones_antiguas`. DEC-P13 debe declarar que DEC-P02 también se difiere y cuándo se reintenta, y §2 debe remitir a DEC-P13.

## ✅ Especificación (paso `especificar`, 2026-10-27)
Política elegida (DEC-P13, «Recarga solo hacia motores compatibles»): **recargar solo hacia destinos que admitan la recarga (desde v0.5.0) y acepten todas las opciones del proceso; si no, seguir con la versión actual, conservar el PID y avisar una vez por versión activa** en el log y por Telegram (evento `respuesta`). Se descartan rechazar la instalación (contradice RF-F03-11) y el protocolo de confirmación del sucesor (no lo implementan las versiones ya publicadas).
- **Requisitos:** nuevo RF-F03-14; RF-F03-06 y RF-F03-11, R2 y la fila 8 de `requirements.md §4` ajustan el aviso de instalación: promete la recarga solo si el destino admite las opciones y, si el destino es anterior a v0.5.0, pide reinicio manual y advierte que los motores de 0.5.0 a 0.6.1 se detendrán.
- **Escenarios:** `@CA-F03-17` (volver atrás a 0.4.0 con bucle y gateway de 1.0.0) y `@CA-F03-18` (destino 0.6.1 que no admite `--calidad`; recarga posterior a 1.0.1), en F-03 y `tests/features/actualizacion_automatica.feature`.
- **H-07:** §2 opción 3 remite a DEC-P13; DEC-P02 y DEC-P13 declaran que la limpieza de versiones antiguas se difiere con bucles o pasos y se reintenta en la primera orden `adevv` fuera de pasos y sin bucles, junto a las copias de RF-F01-11, aunque no haya destinos `DESFASADO`.
- **Qué toca en el código:** `recargar_version`/`version_activa_distinta` (bucle y gateway), aviso único por versión activa, `updater.mensaje_actualizacion`, reintento de `limpiar_versiones_antiguas` en el punto de reintento de RF-F01-11, `README.md` (línea ~25) y `skills/orquestar/SKILL.md` («Recarga automática»).
- **Límite declarado:** la protección solo la tienen los motores desde 1.0.0.
- **Hades `/review-spec`:** RECHAZADO en la primera ronda (🟠 aviso de instalación no veraz cuando el destino no admite las opciones; 🟡 gateway sin escenario, aviso para 0.5.0–0.6.1, DEC-P13 «sin cambios»; 🔵 trazabilidad), corregido; **APROBADO 9/10** en la segunda. 🔵 H-06 (etiqueta de CA-F03-18) resuelto; 🔵 H-07 (título de CA-F03-17) descartado. Reporte: [B-ADV-0021-spec-review.md](../../review/spec_reviews/B-ADV-0021-spec-review.md).

## 📋 Reproducir
1. Lanzar `adevv orquestar --fondo` con el motor 1.0.0.
2. Ejecutar `adevv actualizar 0.4.0`.
3. Esperar al final del paso en curso: `orquestar.log` muestra «Ya hay un bucle en marcha» y `adevv orquestar --estado` indica que no hay bucle vivo, con `orquestar.pid` presente.

## 📋 Evidencias
- `docs/review/versions/v1.0-arquitectura.md`, hallazgos H-01 y H-07.

## 🧭 Triaje (bug-fix, 2026-10-27)
- **Causa raíz confirmada:** `recargar_version` cedía el PID al sucesor sin comprobar que admite la recarga ni las opciones del proceso.
- Subfase A: Definición → `[SKIP]` (especificada en el paso `especificar`: RF-F03-14, @CA-F03-17/18, Hades 9/10).
- Subfase B: Diseño → `[SKIP]` (DEC-P13 ya fija la política; comprobación previa en el proceso que recarga).
- Subfase C1: Pruebas → `[EXEC]` (`skills/orquestar/test_recarga.py`, `tests/test_updater.py`): destino anterior a v0.5, destino sin opción, aviso único, recarga posterior, aviso de instalación y reintento de limpieza.
- Subfase C2: Corrección → `[EXEC]` (`orquestar.py`: `causa_sin_recarga`/`avisar_sin_recarga`; `updater.mensaje_actualizacion`; `cli._resincronizar_desfasados_al_arrancar`; README y SKILL de orquestar).
- Subfase D: QA → `[EXEC]` (Hades `/review-code` sobre el delta).
- Subfase E: Documentación → `[EXEC]` (README y SKILL, inline).
- Subfase F: Cierre → `[EXEC]`.
- **Verificación al cierre:** `python -m unittest tests.test_updater skills.orquestar.test_recarga skills.telegram_gateway.test_recarga_gateway skills.orquestar.test_deuda_menor tests.test_cli_commands tests.test_sync tests.test_telegram_gateway`: ejercita la recarga del motor y del gateway, el aviso de instalación y el reintento de limpieza.

## ✅ Resolución
- `recargar_version` comprueba antes de ceder el PID (`causa_sin_recarga`): destino anterior a v0.5.0 o sin alguna opción del proceso → sigue con su versión, conserva el PID y avisa una vez por versión activa (log y Telegram, evento `respuesta`). Cubre bucle y gateway.
- `mensaje_actualizacion` usa las frases de RF-F03-06/11 y @CA-F03-17/18 y nombra los procesos en « En marcha: …».
- La limpieza de versiones antiguas (DEC-P02) se reintenta en la primera orden sin bucles ni pasos; sale antes si no hay versiones antiguas ni puntero activo.
- Hades `/review-code`: RECHAZADO 8,2 (🟠 aviso de instalación) → APROBADO 9,0. Reporte: [B-ADV-0021-code-review.md](../../review/code_reviews/B-ADV-0021-code-review.md).
