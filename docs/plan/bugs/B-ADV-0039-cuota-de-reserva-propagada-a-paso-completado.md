---
id: B-ADV-0039
title: "La cuota agotada de una reserva detiene el bucle después de que otro arnés complete el paso"
type: bug
weight: 20
dificultad: dificil
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

## Triaje

- base_calidad: cafcd0f31c8ce95342bb3e4108d78d1d2f49e27c
- A: [SKIP] El contrato de recuperación y sus cuatro regresiones ya están descritos en esta incidencia; no cambia requisitos.
- B: [SKIP] Corrección local del consumo de métricas, sin decisión arquitectónica nueva.
- C1: [EXEC] Regresiones del bucle con agentes reales y proveedores simulados: reserva en la misma revisión, revisión pendiente independiente e historial por proveedor.
- C2: [EXEC] Correlacionar los intentos de cada invocación y consumir únicamente sus cuotas pendientes; no imputarlas al perfil principal.
- D: [EXEC] Hades revisa pruebas y delta completo.
- E: [EXEC] Aclaración mínima del contrato de métricas en la skill del orquestador y revisión de versión.
- F: [EXEC] Cierre y commit tras aprobaciones.
- Verificación al cierre: `python -m unittest discover -s skills/orquestar -p test_fallos_arnes.py` y `python -m unittest discover -s skills/orquestar -p test_acceso_agente.py`; ejercitan recuperación del paso y reservas del revisor. Chequeos: `git diff --check` y calidad del delta; no hay lint/tipado configurados ni cambios de dependencias.
- Diagnóstico: el bucle busca cualquier fila nueva de agente con sin_cuota sin distinguir invocación ni recuperación posterior, y añade esa espera a la fila del perfil principal.

- Ampliación dirigida del triaje: `python -m unittest tests.test_orquestar.ReservaCuotaTests` y `python -m unittest discover -s skills/orquestar -p test_arnes_ausente.py`, porque el resumen de espera cambia el registro terminal de reservas agotadas/ausentes.

- Regresión histórica ajustada: los tres intentos conservan su fila; una cuarta fila sin consumo resume la espera mínima con su proveedor real. Antes esperaba el resumen fusionado con el último proveedor, que precisamente causaba la atribución incorrecta.

## Revisión intermedia de Hades

- C1/T1 (alta, desarrollador): distinguir cierre efectivo de progreso parcial commiteado, incluso con árbol limpio. Se añade contraste con estado in_progress real y falta de informe canónico.
- C2 (media, desarrollador, resolver): conservar vencimiento original al resumir cuotas; nuevo reloj simulado avanza 4000 segundos entre reservas y exige esperar cero por la primera recuperación ya vencida.
- La verificación dirigida de fallos_arnes pasa a 20 pruebas. La compilación de los tres archivos Python del delta se acredita mediante --verificar. Sin cambios de requisitos, arquitectura, dependencias ni perfiles.

## Estado al terminar este intento

El motor ordenó detener las correcciones tras dos rechazos seguidos de Hades y commitear el trabajo sin completar el bug. Se conserva `status: in_progress` y la base de calidad original.

- review-test final RECHAZADO 8/10: T1 ya resuelto; T2 pendiente, corregir la aserción que exige borrar la marca vencida. Debe verificar el vencimiento original y la ausencia entre cuotas vigentes de consumo_cuotas.
- review-code RECHAZADO: C1 pendiente en producción (no equiparar commit parcial limpio con cierre efectivo); C2 pendiente en producción (preservar vencimiento original y descontar tiempo de reservas al resumir).
- Última verificación de fallos_arnes: 20 pruebas, dos fallos funcionales esperados en RED de C1/C2. No se aplicaron correcciones posteriores a la orden de parada. Antes de añadir esos contrastes estaban verdes las 46 pruebas dirigidas (18+14+9+5).
- Reanudación: corregir T2, obtener review-test aprobado, implementar C1/C2 y repetir las verificaciones del triaje y review-code. La suite completa corresponde al bucle al cerrar versión.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades asignó T2, C1 y C2 al desarrollador. Artemisa retoma la prueba de vencimiento y las correcciones de cierre efectivo y espera restante.

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades rechaza review-test (8/10): falta verificar que el paso principal registra solo sus 11 tokens y no duplica el consumo de Opus, Gemini ni GPT. Artemisa reanuda la corrección de las aserciones.

Al reanudar, comparar también los vencimientos del contraste temporal con la fecha y la duración registradas en cada intento original. Las duraciones incluyen el margen de 120 segundos del analizador. Las aserciones posteriores al primer fallo aún no llegaron a ejecutarse. C1 y C2 siguen pendientes en producción.
