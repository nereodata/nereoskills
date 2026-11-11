---
id: B-ADV-0039
title: "La cuota agotada de una reserva detiene el bucle después de que otro arnés complete el paso"
type: bug
weight: 20
dificultad: media
version: "v1.1.2"
status: planned
depende_de: []
created_at: 2026-11-11
updated_at: 2026-11-11
---

# B-ADV-0039 · La cuota de una reserva detiene un paso completado

## Fallo observado

En Aprexx, con Adevv 1.1.1, Claude informó de que la organización había deshabilitado el acceso por suscripción. Hades registró falta de cuota en agy/Gemini y después ejecutó varias revisiones con Codex con código 0. El paso `bug-fix B-APX-CTX-0036` terminó con progreso y el bug quedó `completed` en el commit `93fd8005`. El bucle paró por cuota aun así.

## Evidencias

- En `C:\Users\Iván Moreno\SW\Aprexx\orquestar_metricas.jsonl`, el 2026-11-11 a las 07:14:36, Hades registró `agy/gemini-4-argon`, código 3, `sin_cuota=true` y `cuota_espera_s=260910`. Hay ejecuciones posteriores de Hades con Codex y código 0, incluida la de las 08:27:00.
- A las 08:30:03, la fila del paso principal identifica `codex/gpt-6.1-sol`, `codigo=0` y `progreso=true`, junto con `sin_cuota=true` y `espera_s=260910`.
- En `C:\Users\Iván Moreno\SW\Aprexx\orquestar.log`, la línea 1371 informa del cierre en `93fd8005` y la 1376 registra la parada «el arnés terminó con código 1 (sin cuota tras esperar 0 h (--espera-max))».

## Hipótesis a confirmar durante el diagnóstico

En `skills/orquestar/orquestar.py`, revisar cómo el bucle delimita las filas nuevas al ejecutar un paso, selecciona una espera de agente y registra el resultado con el arnés y modelo principales. Contrastar el orden de escritura de las métricas con las invocaciones de Hades, la reserva que terminó cada revisión y la evidencia de cierre en disco. La coincidencia de los 260910 segundos orienta el diagnóstico, pero por sí sola no identifica la ruta que propagó la marca.

## Reproducción y regresiones de aceptación

1. Simular la secuencia completa con `--espera-max 0`: Claude falla por acceso de suscripción, agy/Gemini agota cuota y Codex termina la revisión requerida. Con informe de revisión, bug completado, commit y salida 0 del paso, el bucle debe seleccionar el siguiente trabajo sin esperar ni devolver un error de cuota.
2. Cubrir también una invocación de subagente cuyo primer intento agota cuota y cuya reserva completa la misma revisión. El paso que la invocó debe conservar su resultado satisfactorio. Ninguna métrica debe imputar el agotamiento de Gemini al arnés o al modelo de Codex.
3. Probar el caso de contraste en el que sigue faltando una revisión obligatoria por cuota. Incluso si hubo progreso o se completó otra revisión, el bucle debe conservar el impedimento y comunicar el proveedor, el modelo y el motivo reales.
4. Verificar tras la recuperación que el historial conserva el fallo de acceso de Claude, el agotamiento y la espera de Gemini, las ejecuciones de Codex y el consumo registrado de cada intento. El agotamiento puede seguir vigente para Gemini sin bloquear trabajo ya completado mediante una reserva.
