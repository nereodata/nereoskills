---
id: B-ADV-0005
title: "Un arnés no encontrado en el PATH para el bucle en vez de avisar y conmutar a la siguiente reserva"
type: bug
weight: 50
dificultad: media
version: "v1.0.0"
status: in_progress
depende_de: []
created_at: 2026-10-26
updated_at: 2026-10-26
---

# B-ADV-0005: Un arnés no encontrado en el PATH para el bucle en vez de avisar y conmutar a la siguiente reserva

## 🎯 Descripción del Fallo

**Causa raíz**: cuando el ejecutable del arnés configurado (perfil principal o reserva) no se encuentra, `orquestar.py` termina con `sys.exit(...)` en lugar de tratarlo como un fallo recuperable de esa configuración:

- `comando()` (`skills/orquestar/orquestar.py:1055`), usado por `ejecutar()` en el bucle de pasos con reservas (`configs_a_probar`, ~línea 2101).
- Bucle de agentes con reservas (`skills/orquestar/orquestar.py:1278`).
- El gateway de Telegram tiene el mismo patrón (`skills/telegram_gateway/gateway.py:163`, `RuntimeError`).

**Comportamiento observado**: si p. ej. `codex` no está instalado o no está en el PATH, el bucle desatendido se detiene por completo aunque haya reservas con otros arneses disponibles.

**Comportamiento esperado**:
1. Si el arnés de una configuración no se encuentra, se emite un warning por consola (`[orquestar] no se encuentra el arnés "X"; conmutando a reserva...`) y se registra en métricas.
2. El mismo warning se envía por Telegram con `avisar()` (nuevo evento, filtrable como el resto).
3. Se pasa a la siguiente reserva, igual que al agotar cuota. La sesión anterior no se reutiliza si el arnés cambia.
4. Solo si **ninguna** configuración tiene un arnés disponible, el paso falla con un mensaje claro (y aviso por Telegram) en lugar de un `sys.exit` silencioso a mitad de reservas.

Fuera de alcance: el modo `--cmd` explícito (sin reservas) puede seguir abortando.

## 📋 Reproducir
1. En `orchestration.json`, configurar un rol con `harness: "codex"` y una `reserva` con `harness: "claude"`.
2. Quitar `codex` del PATH (o renombrar el ejecutable).
3. Lanzar `/orquestar` hasta un paso de ese rol.
4. Observado: el bucle termina con `No se encuentra el arnés "codex" en el PATH.`. Esperado: warning (consola + Telegram) y ejecución con la reserva `claude`.

## 📋 Evidencias
- `skills/orquestar/orquestar.py:1055` y `:1278` — `sys.exit` dentro del flujo con reservas.
- `skills/telegram_gateway/gateway.py:163` — mismo patrón en el gateway.

## Triaje (modo orquestado)
- Subfase A: Definición [EXEC]: contrato de reservas ante ejecutable ausente en pasos, agentes y gateway; evento Telegram `arnes`.
- Subfase B: Diseño [EXEC]: señal recuperable común y conservación de cuota/sesión.
- Subfase C1: Pruebas [EXEC]: regresiones aisladas en skills, sin arneses ni Telegram reales.
- Subfase C2: Corrección [EXEC]: motor y conversación del gateway.
- Subfase D: QA [EXEC]: Hades sobre el delta completo.
- Subfase E: Documentación [EXEC]: instrucciones de orquestar y gateway; notas de versión.
- Subfase F: Cierre [EXEC]: completed y commit en release/v1.0.
- Verificación al cierre: `python -m unittest discover -s skills/orquestar -p test_arnes_ausente.py` y regresiones `python -m unittest discover -s skills/orquestar -p test_cuota_vigente.py`, `python -m unittest discover -s tests -p test_orquestar.py`, `python -m unittest discover -s tests -p test_telegram_gateway.py`; ejercitan reservas, sesiones y cuota de los consumidores afectados. Estático: compilación de los módulos del delta y `git diff --check`; no hay linter/tipado configurado ni cambios de dependencias.
- DEC: se trabaja en la release activa, sin hotfix ni HITL. Ausencia no equivale a cuota: no crea esperas. Si hubo cuota en otra configuración disponible, se conserva la señal de cuota aunque la última reserva falte.

## Resolución del especificador (2026-10-26)
- H-01: cadena principal codex ausente → primera reserva claude ausente → segunda reserva agy disponible, para paso, agente Hades y conversación del gateway. Cada ausencia exige warning, métrica y aviso `arnes` propios; la petición debe llegar a la segunda reserva.
- H-02: las métricas identifican flujo, posición, arnés y modelo del intento ausente; todos sus contadores de tokens y coste son cero, sin agotamiento ni recuperación de cuota atribuibles a ese intento. El instante de recuperación del principal debe conservarse exactamente en `2026-10-26T18:00:00Z`.
- DEC-ESP-01: recuperar solo la propuesta BDD de `wip/B-ADV-0005` (`651864f`) y ampliarla sin reducir escenarios. Se descarta integrar las pruebas o producción durante este paso: pertenecen a Artemisa. El WIP y su reproducción roja se conservan para retomar bug-fix; no constituyen evidencia verde del árbol actual.
- DEC-ESP-02: ausencia no equivale a cuota. Se concreta el evento filtrable `arnes`, con un aviso por configuración ausente, y el consumo nulo observable sin imponer nombres internos de campos. Se descarta una métrica genérica sin atribución porque no discrimina H-02.
- Especificación: `skills/orquestar/features/orquestacion.feature`. No se necesita recurso externo ni respuesta humana.
