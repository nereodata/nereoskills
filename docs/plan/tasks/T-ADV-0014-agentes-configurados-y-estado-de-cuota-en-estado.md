---
id: T-ADV-0014
title: "Mostrar agentes configurados para la tarea actual y estado de cuota en /estado"
type: funcional
weight: 200
dificultad: media
version: "v0.4.0"
status: planned
depende_de: ["B-ADV-0002"]
origen: "Visibilidad en /estado y --estado de los modelos activos por tarea y la ventana de cuota"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0014: Mostrar agentes configurados para la tarea actual y estado de cuota en /estado

## 🎯 Objetivo de Negocio
Enriquecer tanto `adevv orquestar --estado` (`resumen()`) como el comando `/estado` de Telegram (`parte()`) para que informen de un vistazo qué agentes/modelos (y reservas) están configurados para ejecutar y revisar el paso/tarea actual según su dificultad, así como el estado de cuota de cada modelo y el consumo acumulado en la ventana reciente.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Agentes configurados para el paso/tarea actual):** Tanto `parte(root)` como `resumen(root)` en `skills/orquestar/orquestar.py`, cuando el estado actual es `('PASO', paso, arg, ...)`, resuelven la `dificultad` de `arg` (si aplica) y muestran el rol ejecutor (`artemisa` o `atenea`) con su `harness/model (effort)` efectivo (indicando si está en `escalada` y sus modelos de `reserva` si están definidos) y la configuración efectiva de `hades` para ese paso/dificultad.
- [ ] **CA-M-2 (Estado de cuota y ventana reciente por modelo):** `parte(root)` y `resumen(root)` inspeccionan `orquestar.espera` y los registros recientes de `orquestar_metricas.jsonl` (ventana de las últimas 5 horas) para mostrar el estado de cuota y uso reciente por modelo/arnés: si algún modelo registró agotamiento de cuota cuya espera (`fecha + espera_s` o `orquestar.espera`) aún no ha vencido, indica hasta qué hora está agotado y cuántos minutos restan; además resume los tokens consumidos en la ventana activa de 5 h por modelo.
- [ ] **CA-M-3 (Pruebas unitarias y documentación):** `tests/test_orquestar.py` valida que `parte()` y `resumen()` incluyen los agentes efectivos del paso actual (con dificultad y reservas) y el estado/restante de cuota cuando hay eventos de cuota recientes; `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md` reflejan la nueva información de `/estado`.
