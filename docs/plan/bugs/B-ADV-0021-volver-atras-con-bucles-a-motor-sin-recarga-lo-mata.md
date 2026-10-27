---
id: B-ADV-0021
title: "Volver atrás con bucles en marcha a un motor sin recarga mata el bucle en silencio"
type: bug
weight: 10
dificultad: media
version: "v1.0.0"
status: blocked
pendiente_de: especificador
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

## 📋 Reproducir
1. Lanzar `adevv orquestar --fondo` con el motor 1.0.0.
2. Ejecutar `adevv actualizar 0.4.0`.
3. Esperar al final del paso en curso: `orquestar.log` muestra «Ya hay un bucle en marcha» y `adevv orquestar --estado` indica que no hay bucle vivo, con `orquestar.pid` presente.

## 📋 Evidencias
- `docs/review/versions/v1.0-arquitectura.md`, hallazgos H-01 y H-07.
