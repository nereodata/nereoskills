---
id: T-ADV-0042
title: "Reescribir desde cero el motor de orquestación a su núcleo mínimo y reducir la suite a segundos"
type: infra
weight: 10
dificultad: dificil
version: "v1.3.0"
status: in_progress
depende_de: []
created_at: 2026-11-14
updated_at: 2026-11-14
---

# T-ADV-0042: Reescribir desde cero el motor de orquestación a su núcleo mínimo y reducir la suite a segundos

## 🎯 Objetivo de Negocio
Eliminar el sobrepeso histórico del motor de orquestación (~10.000 líneas de código defensivo y agentes intermediarios que duplican tiempo y tokens en cada revisión y cierre) y de su batería de pruebas (`~500s`), reemplazándolos desde cero por un núcleo mínimo, directo y fácil de mantener, conservando intactos el instalador/sincronizador de Adevv y los comandos operativos de CLI y Telegram.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Núcleo mínimo desde cero):** El subsistema de orquestación se reduce a módulos cohesivos pequeños (~1.000–1.300 líneas en total frente a las ~10.080 actuales), eliminando subsistemas redundantes (`chequeos.py` de 2.091 líneas, `diagnostico_suite.py`, `decision_item.py`, `llamadas.py`, recargas calientes innecesarias y el parser HTML casero de `revisiones.py`).
- [ ] **CA-M-2 (Control básico de modelos, dificultad y cuotas):** Mantiene la selección por rol y dificultad (`sencilla`/`media`/`dificil`), `perfil` explícito en ficha y conmutación automática a `reserva` ante agotamiento de cuota, acceso denegado o arnés ausente, con espera acotada solo cuando ningún candidato tiene cuota.
- [ ] **CA-M-3 (Métricas reales):** Conserva el registro en `orquestar_metricas.jsonl` (duración, tokens de entrada/caché/salida/razonamiento, modelo, veredicto y coste estimado) y su consulta en CLI (`--metricas`) y Telegram (`/metricas`, `/agentes`).
- [ ] **CA-M-4 (Cero «agentes secretarios» y caché por huella de producto):** `revisar-plataforma`, `revisar-tarea` (solo en `critical_paths`) y `revisar-version` invocan directamente a Hades desde Python y confirman el `git commit` sin envolver la llamada en Artemisa/Atenea; ante `RECHAZADO` reabren para corrección con tope `--reintentos`. Las verificaciones (`--verificar` y suite de cierre) se cachean por `huella_producto` (los commits que solo tocan `docs/plan/` o `docs/review/` no repiten la suite).
- [ ] **CA-M-5 (Compatibilidad CLI, release y Telegram):** Siguen funcionando `adevv orquestar` (`--estado`, `--parar`, `--fondo`, `--metricas`, `--verificar`, `--agente`, `--preguntas`, `--responder`), `adevv release` (`release_tools.py`) y `skills/telegram_gateway/gateway.py` (`/estado`, `/agentes`, `/metricas`, `/tarea`, `/bug`, `/preguntas`, `/responder`, `/desbloquear`, `/lanzar`, `/parar`, `/cerrar` y conversación libre).
- [ ] **CA-M-6 (Suite completa ultrarrápida):** `python -m unittest discover -s tests` pasa en verde en `< 15s` (frente a los `~500s` previos), sin crear cientos de repositorios Git redundantes por test, con `ruff check` y `test_instructions_cleanliness.py` limpios.
