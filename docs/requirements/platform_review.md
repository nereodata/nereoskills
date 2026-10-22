**Veredicto:** APROBADO

# Revisión de Arquitectura (`/review-design`) · Plan de Plataforma de Adevv

- **Artefacto auditado:** [`platform_plan.md`](platform_plan.md) (`DEC-P01` a `DEC-P08`)
- **Contraste:** [`requirements.md`](requirements.md), [`req_analysis.md`](req_analysis.md), [`F-01`](funcionalidades/F-01_instalacion_y_sincronizacion.md), [`F-02`](funcionalidades/F-02_uso_sin_rutas.md), [`F-03`](funcionalidades/F-03_actualizacion_automatica.md), [`F-04`](funcionalidades/F-04_migracion.md) y [`F-05`](funcionalidades/F-05_publicacion.md).

---

## Puntuaciones

| Criterio | Nota | Justificación |
|---|---|---|
| **Cobertura** | **10 / 10** | Cubre la totalidad de los requisitos funcionales (`F-01`..`F-05`), las preguntas abiertas (`PQ-01`..`PQ-04`), los supuestos (`SUP-01`..`SUP-08`) y las restricciones de `requirements.md §6`, con datos empíricos comprobados en la máquina (versiones de Python, Git y arneses, ausencia de `PyYAML` y `uv` en el entorno base, carpetas reales de Claude Code, Codex y Antigravity). |
| **Proporción** | **10 / 10** | Stack mínimo y sin sobreingeniería para una herramienta de un único usuario: librería estándar de Python ≥ 3.11, backend PEP 517 ligero en el propio árbol, parser YAML acotado con delegación a `PyYAML` si existe, y persistencia en JSON bajo `~/.adevv/` con reemplazo atómico. |
| **Estructura** | **9 / 10** | Capas bien delimitadas en `adevv/`, grafo de dependencias unidireccional y 4 reglas de arquitectura explícitas y verificables que preservan la unicidad de `orquestar.py`, `gateway.py` y los scripts de `release` (`NO-04`). |
| **Testeabilidad** | **10 / 10** | La estrategia de pruebas aísla la lógica pura mediante reloj inyectable y `ADEVV_HOME` temporal, prueba Git contra repositorios `bare` locales (`ADEVV_ORIGIN_URL`) sin red, inspecciona estáticamente el paquete construido frente a la lista blanca y verifica procesos reales en Windows. |
| **Coherencia** | **9 / 10** | Las decisiones `DEC-P01` a `DEC-P08` son consistentes entre sí y resuelven sin contradicciones la tensión entre bloqueo de ejecutables en Windows, gateways perpetuos (`DEC-03`, `RF-F03-08`) y ejecución síncrona con la versión recién instalada (`RF-F03-07`, `CA-F03-02`). |
| **Media** | **9,6 / 10** | **APROBADO** (media > 8, 0 🔴, 0 🟠). |

---

## Hallazgos

### 🔵 BAJA

1. **[H-01] Delegación a la versión activa también para sincronizar tras actualizar (`DEC-P01`, §2 Opción 3)**
   - **Dónde:** `platform_plan.md` (§2 Opción 3, paso 3; `DEC-P01`).
   - **Observación:** El paso 3 de la Opción 3 describe que el punto de entrada evalúa la tabla de actualización, instala `A.B.C`, sincroniza los destinos y luego despacha la acción cargando los módulos de `~/.adevv/versions/<V>/`. Conviene explicitar que el despachador carga el código desde la versión activa (`active.json`) desde el arranque y que, tras conmutar `active.json` a una versión nueva `A.B.C`, la sincronización de destinos (`F-01`) se ejecuta ya con el `adevv/sync.py` (y el mapa `DESTINOS`) de `A.B.C`, no con el del paquete base inicial (`0.1.0`). Así, si una versión futura cambia `DESTINOS` o las reglas de sincronización (p. ej. al confirmar o ajustar carpetas de un arnés, `RF-F01-03`), la actualización aplica inmediatamente las reglas de la versión nueva.
   - **destino:** `resolver` *(resuelto en `platform_plan.md` §2 Opción 3)*

2. **[H-02] Incluir el patrón `../` de `CA-F01-03` en la regla de inspección de destinos (§4 Regla 4 y §5)**
   - **Dónde:** `platform_plan.md` (§4 Regla 4 y §5 «Inspección estática y de paquete construido»).
   - **Observación:** La regla 4 de capas y la fila «Inspección estática y de paquete construido» de §5 listan la ausencia de `.agents/`, `python .../*.py` y `skills/<n>/scripts`, pero en `F-01` (`CA-F01-03`) se exige además verificar que ningún archivo escrito en los destinos contenga rutas relativas que empiecen por `../`. Añadir `../` explícitamente en §4/§5 evita que pase desapercibido al diseñar las pruebas de `F-01`.
   - **destino:** `resolver` *(resuelto en `platform_plan.md` §4 Regla 4 y §5)*
