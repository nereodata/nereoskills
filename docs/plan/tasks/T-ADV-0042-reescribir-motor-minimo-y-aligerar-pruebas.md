---
id: T-ADV-0042
title: "Reescribir desde cero el motor de orquestación a su núcleo mínimo y reducir la suite a segundos"
type: infra
weight: 10
dificultad: dificil
version: "v1.3.0"
status: completed
depende_de: []
created_at: 2026-11-14
updated_at: 2026-11-14
---

# T-ADV-0042: Reescribir desde cero el motor de orquestación a su núcleo mínimo y reducir la suite a segundos

## 🎯 Objetivo de Negocio
Eliminar el sobrepeso histórico del motor de orquestación (~10.080 líneas de código defensivo y agentes intermediarios que duplicaban tiempo y tokens en cada revisión y cierre) y de su batería de pruebas (`~501s`), reemplazándolos desde cero por un núcleo mínimo, directo y fácil de mantener, conservando intactos el instalador/sincronizador de Adevv y los comandos operativos de CLI y Telegram.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Núcleo mínimo desde cero):** El subsistema de orquestación se reduce a módulos cohesivos pequeños (`orquestar.py`, `perfiles.py`, `intervencion.py`, `metricas.py`, `revisiones.py`, `contexto_ejecucion.py`), eliminando 42 archivos obsoletos (~18.000+ líneas totales entre código redundante como `chequeos.py`, `diagnostico_suite.py`, `decision_item.py`, `llamadas.py`, `calidad.py` y 29 ficheros `test_*.py` que se estaban empaquetando dentro de `skills/`).
- [x] **CA-M-2 (Control básico de modelos, dificultad y cuotas):** Mantiene la selección por rol y dificultad (`sencilla`/`media`/`dificil`), `perfil` explícito en ficha y conmutación automática a `reserva` ante agotamiento de cuota, acceso denegado o arnés ausente, con espera acotada solo cuando ningún candidato tiene cuota.
- [x] **CA-M-3 (Métricas reales):** Conserva el registro en `orquestar_metricas.jsonl` (duración, tokens de entrada/caché/salida/razonamiento, modelo, veredicto y coste estimado) y su consulta en CLI (`--metricas`, `adevv metricas`, `adevv agentes`) y Telegram (`/metricas`, `/agentes`).
- [x] **CA-M-4 (Cero «agentes secretarios» y caché por huella de producto):** `revisar-plataforma`, `revisar-tarea` (solo en superficies críticas o informe previo rechazado) y `revisar-version` invocan directamente a Hades desde Python y confirman el `git commit` sin envolver la llamada en Artemisa/Atenea; ante `RECHAZADO` reabren para corrección con tope `--reintentos`. Las verificaciones (`--verificar` y suite de cierre) se cachean por `huella_producto` (los commits que solo tocan `docs/plan/` o `docs/review/` no repiten la suite).
- [x] **CA-M-5 (Compatibilidad CLI, release y Telegram):** Siguen funcionando `adevv orquestar` (`--estado`, `--parar`, `--fondo`, `--metricas`, `--verificar`, `--agente`, `--preguntas`, `--responder`), `adevv release` (`release_tools.py`), recarga cooperativa entre versiones (`recargar_version`) y `skills/telegram_gateway/gateway.py`.
- [x] **CA-M-6 (Suite aligerada):** `tests/test_orquestar.py` pasa en `< 1s` (`0.99s` frente a los `300+s` anteriores) y la suite completa `python -m unittest discover -s tests` (`148` tests incluyendo integración real de subprocesos CLI, actualizador, release y gateway en Windows) baja de `501s` a `~45s` (>11x más rápida) gracias a repositorios plantilla reutilizables en `setUpClass`, ejecución en proceso de validaciones puras y consulta perezosa de procesos vivos en Windows (`adevv/cli.py`, `adevv/sync.py`), con `ruff check` y `test_instructions_cleanliness.py` limpios.
