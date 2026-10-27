---
id: B-ADV-0016
title: "espera_cuota() no entiende «Resets in 56h48m9s» y vuelve a probar el modelo agotado cada 30 minutos"
type: bug
weight: 20
dificultad: sencilla
version: "v1.0.0"
status: completed
depende_de: []
origen: "Diagnóstico del chat de Telegram (2026-10-27): Antigravity sin cuota durante ~56 h"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0016: espera_cuota() no entiende «Resets in 56h48m9s» y vuelve a probar el modelo agotado cada 30 minutos

## 🎯 Descripción del Fallo

**Causa raíz**: en `espera_cuota()` (`skills/orquestar/orquestar.py`, hacia la línea 1519), la expresión `(?:try again|retry|resets?) in\s+(?:(\d+)\s*(?:hours?|hrs?|h)\b)?\s*(?:(\d+)\s*(?:minutes?|mins?|m)\b)?` exige un límite de palabra (`\b`) tras `h` y tras `m`. En el formato compacto `56h48m9s` no lo hay, así que no reconoce nada y se aplica el valor por defecto de 1800 s.

**Comportamiento observado**: Antigravity responde, con código 3, `Individual quota reached. Please upgrade your subscription to increase your limits. Resets in 56h48m9s.` y `AGY_ERROR: {"status":"RESOURCE_EXHAUSTED","error_code":429,…}`. `espera_cuota()` devuelve 1800. Durante 56 horas, el bucle (`configuraciones_con_cuota()`) y el chat de Telegram dan el modelo por disponible cada 30 minutos y gastan un intento fallido antes de pasar a la reserva.

**Comportamiento esperado**:
1. Reconoce el formato compacto con días, horas, minutos y segundos (`2d3h`, `56h48m9s`, `48m9s`, `9s`), además de los que ya reconoce, como «2h 13m» o «try again in 5 minutes».
2. La espera calculada se registra en las métricas (`cuota_espera_s`), de modo que `consumo_cuotas()` deja el modelo apartado hasta la hora real de recuperación.
3. Si la salida es el JSON de error de Antigravity (`RESOURCE_EXHAUSTED`), la detección sigue funcionando aunque el texto cambie.
4. Pruebas unitarias con estas salidas reales.

## 📋 Reproducir
```python
import orquestar as m
m.espera_cuota('Individual quota reached. Resets in 56h48m9s.')  # 1800; esperado ≈ 204489 + margen
```

## Triaje
- [SKIP] A Definición: sin requisito nuevo.
- [SKIP] B Diseño: cambio local de una expresión regular.
- [EXEC] C1 Pruebas: duraciones compactas y JSON `RESOURCE_EXHAUSTED` (`tests/test_orquestar.py`).
- [EXEC] C2 Corrección: `espera_cuota()` con d/h/m/s sin ``; `resource_exhausted` en `CUOTA`.
- [EXEC] D QA: Hades `/review-code`.
- [SKIP] E Documentación: sin manual afectado.
- [EXEC] F Cierre.
- Verificación: `python -m unittest tests.test_orquestar` (módulo del motor modificado).
- `cuota_espera_s` ya se registra desde el valor devuelto por `espera_cuota()` (líneas 1422, 2471).
