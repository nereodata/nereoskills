---
id: T-ADV-0025
title: "Limpieza de deuda menor descartada en las revisiones de v0.3 a v0.6"
type: funcional
weight: 300
dificultad: sencilla
version: "v1.0.0"
status: completed
depende_de: []
origen: "Hallazgos 🔵 con destino descartar en docs/review/versions/v0.4-arquitectura.md, v0.5-arquitectura.md y v0.6-arquitectura.md"
created_at: 2026-10-26
updated_at: 2026-10-27
---

# T-ADV-0025: Limpieza de deuda menor descartada en las revisiones de v0.3 a v0.6

## 🎯 Objetivo de Negocio
Antes de etiquetar la v1.0, eliminar los detalles de mantenimiento que Hades fue descartando por ser menores, empezando por uno que es un fallo latente.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Versión de respaldo):** `version_adevv()` ya no devuelve un literal fijo. Usa la versión de `pyproject.toml` o `task_config.yaml`, con `desconocida` como último recurso; pruebas cubren fuentes, precedencia y manifiesto malformado.
- [x] **CA-M-2 (Propiedad de PID):** la propiedad y la vida del PID se comprueban mediante helpers comunes parametrizados; la matriz cubre simétricamente `telegram.pid` y `orquestar.pid`.
- [x] **CA-M-3 (Ruta de versiones):** `directorio_version_almacen` es el único resolver de `ADEVV_HOME/versions/<ver>` usado por `version_adevv` y `version_activa_distinta`.
- [x] **CA-M-4 (Restos de compatibilidad):** se elimina `detalle_estado(root, e)` y las pruebas pasan a `informe_agentes`; las claves de versión y lectura JSONL se centralizan en `metricas.py`.
- [ ] **CA-M-5 (Sin cambio de comportamiento):** no se ejecuta aquí la suite completa; queda reservada al bucle al cerrar v1.0. Las pruebas del delta y revisiones no muestran cambios visibles salvo el respaldo de CA-M-1.

## Triaje de alcance
- **Base de calidad:** `0f287d4` (HEAD antes de comenzar T-ADV-0025).
- **A · Definición:** [SKIP] Los criterios de aceptación fijan el delta de mantenimiento; no se añade comportamiento nuevo de usuario ni un escenario funcional independiente.
- **B · Diseño:** [EXEC] Extraer la resolución de directorio de versiones, compartir utilidades de PID entre los dos motores y centralizar la normalización de versiones/métricas.
- **C1 · Pruebas:** [EXEC] Añadir regresiones para fallback de versión (incluido YAML tras TOML malformado), propiedad/vida de ambos PID, resolución de almacén compartida, lectura JSONL con separador Unicode y retirada/adaptación de utilidades heredadas.
- **C2 · Implementación:** [EXEC] Aplicar solo las extracciones y retiradas pedidas por CA-M-1..4, preservando salidas salvo el fallback de CA-M-1.
- **D · QA:** [EXEC] Revisión Hades del delta de producción tras ejecutar los comandos de verificación anotados.
- **E · Documentación:** [SKIP] No cambian instrucciones de usuario; el fallback queda cubierto por la prueba que lee los manifiestos actuales.
- **F · Cierre:** [EXEC] Actualizar revisión de versión, marcar tarea completada y crear commit semántico.
- **Verificación al cierre:** `python -m unittest skills.orquestar.test_deuda_menor skills.orquestar.test_firma_telegram skills.orquestar.test_recarga skills.orquestar.test_metricas skills.orquestar.test_estado_agentes skills.telegram_gateway.test_gateway_fondo` cubre fallback y resolución de versiones, métricas, helper retirado, PID compartido y consumidores afectados. También `python -m py_compile skills/orquestar/orquestar.py skills/orquestar/metricas.py skills/telegram_gateway/gateway.py` y `git diff --check` para sintaxis y formato del delta.
- **Calidad:** `python skills/orquestar/orquestar.py --calidad --base 0f287d4` comprueba formato y lint en los ficheros del delta según lo declarado/deducido por el proyecto; omite ambas etapas con motivo porque no hay herramientas configuradas.

## Cierre de desarrollo
- Hades review-test: **APROBADO 9,00/10**, sin hallazgos pendientes; reporte en `docs/review/test_reviews/T-ADV-0025-test-review.md`.
- Hades review-code: **APROBADO 9,00/10**, sin hallazgos pendientes; reporte en `docs/review/code_reviews/T-ADV-0025-code-review.md`.
- H-01..H-07 fueron resueltos por el desarrollador. No queda deuda nueva.
- CA-M-5 se delega explícitamente al cierre de versión, conforme a la regla de que la suite completa la ejecuta el bucle.
