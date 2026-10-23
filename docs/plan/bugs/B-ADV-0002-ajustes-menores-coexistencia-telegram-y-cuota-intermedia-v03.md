---
id: B-ADV-0002
title: "Ajustes menores transversales v0.3: coexistencia de clave telegram en orchestration.json y marca sin_cuota en intento intermedio de paso"
type: bug
weight: 100
dificultad: sencilla
version: "v0.4.0"
status: completed
created_at: 2026-10-23
updated_at: 2026-10-23
origen: "revisar-version v0.3 (docs/review/versions/v0.3-arquitectura.md)"
---

# B-ADV-0002: Ajustes menores transversales v0.3: coexistencia de clave telegram en orchestration.json y marca sin_cuota en intento intermedio de paso

## 🎯 Descripción del Fallo

La revisión transversal de código y arquitectura de `v0.3` ([`docs/review/versions/v0.3-arquitectura.md`](../../review/versions/v0.3-arquitectura.md), veredicto `APROBADO` con media `9.67/10` y 0 hallazgos 🔴/🟠) señaló dos mejoras menores (`🟡 MEDIA` y `🔵 BAJA`) que se registran como deuda para su resolución por Artemisa sin modificar código de producción desde el rol de análisis (`Atenea`):

1. **[🟡 MEDIA] Coexistencia de `"telegram"` en `orchestration.json` entre avisos de eventos (`orquestar.py`) y modelo conversacional (`gateway.py`)**:
   - **Causa raíz**: En `skills/orquestar/orquestar.py` (`telegram()`), la clave `"telegram"` de `orchestration.json` admite el booleano `false` (para apagar avisos) o un diccionario de filtro `{"eventos": [...]}` sin claves de modelo. En `skills/telegram_gateway/gateway.py` (`conversar()`, líneas 167–173), se asigna `cfg = cfg_todo['telegram']` si la clave existe y se invoca `cfg.get('harness', 'claude')`.
   - **Comportamiento observado vs esperado**: Si `"telegram"` vale `false`, `cfg.get` lanza `AttributeError`; y si `"telegram"` solo declara `{"eventos": [...]}`, no hereda `harness`/`model`/`effort` de `"atenea"`. Se espera fusionar `{**cfg_atenea, **cfg_tg}` comprobando `isinstance(..., dict)`.

2. **[🔵 BAJA] Intento de paso intermedio agotado por cuota y conmutado a reserva suma en `reintentos_acumulados`**:
   - **Causa raíz**: En `skills/orquestar/orquestar.py` (`bucle()`, líneas 1620–1623), cuando el intento de paso falla por cuota propia (`cuota_propia is not None`) y existe una `reserva` disponible (`hay_mas_reservas`), la métrica intermedia del paso se registra sin `'sin_cuota': True`.
   - **Comportamiento observado vs esperado**: `reintentos_acumulados()` (línea 806) cuenta cada entrada `tipo == 'paso'` con `not f.get('sin_cuota')`, por lo que ese intento fallido por cuota computa hacia la subida de dificultad. Añadir `'sin_cuota': True` al registro intermedio de paso evita contabilizar fallos de cuota como reintentos de dificultad.

## 📋 Triaje de Alcance

- [x] **Subfase A: Definición** [SKIP]: Ajustes técnicos internos derivados de revisión de arquitectura v0.3; no alteran requisitos ni especificaciones funcionales externas.
- [x] **Subfase B: Diseño** [SKIP]: Solución directa y localizada sin alternativas complejas ni impacto en la arquitectura de capas.
- [x] **Subfase C1: Pruebas** [EXEC]: Tests unitarios en `tests/test_telegram_gateway.py` y `tests/test_orquestar.py` para capturar ambos escenarios antes del fix (revisión de Hades APROBADO 10.0/10 en `docs/review/test_reviews/B-ADV-0002-test-review.md`).
- [x] **Subfase C2: Corrección** [EXEC]: Fusión segura `{**cfg_atenea, **cfg_tg}` comprobando `isinstance(..., dict)` en `gateway.py` y marcado de `sin_cuota: True` en intento intermedio de `orquestar.py`.
- [x] **Subfase D: QA** [EXEC]: Revisión de código por Hades APROBADO 10.0/10 en `docs/review/code_reviews/B-ADV-0002-code-review.md`.
- [x] **Subfase E: Documentación** [SKIP]: No afecta guías de usuario ni manuales externos.
- [x] **Subfase F: Cierre** [EXEC]: Cierre del bug y commit semántico `fix(B-ADV-0002)`.

**Verificación al cierre**: `python -m unittest tests/test_telegram_gateway.py tests/test_orquestar.py` (ejercita la coexistencia de configuración en gateway y la gestión de métricas de cuota/reintentos en orquestar).

## 📋 Reproducir

1. Configurar `"telegram": false` o `"telegram": {"eventos": ["version"]}` junto con `"atenea": {"harness": "codex"}` en `orchestration.json` e invocar `conversar()` en `skills/telegram_gateway/gateway.py`.
2. Configurar un rol con `reserva` en `orchestration.json`, provocar un fallo por cuota en el modelo primario seguido de conmutación a la reserva en `bucle()`, y consultar `reintentos_acumulados(root, iid)`.

## 📋 Evidencias

- Reporte transversal de Hades: [`docs/review/versions/v0.3-arquitectura.md`](../../review/versions/v0.3-arquitectura.md)
