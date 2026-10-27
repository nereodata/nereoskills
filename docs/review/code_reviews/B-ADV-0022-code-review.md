# Code Review: B-ADV-0022 — Ajustes transversales v1.0

- **Delta**: `git diff HEAD` sobre `e9ab361` (árbol `3f6c28b088`) más `skills/orquestar/test_ajustes_transversales.py` (nuevo, revisado por `/review-test`).
- **Alcance**: H-04, H-05, H-06, H-09 y H-12 de `docs/plan/bugs/B-ADV-0022-ajustes-transversales-v1-0.md`.
- **Veredicto**: ✅ **APROBADO** (media 9,0; sin 🔴 ni 🟠).

## Análisis estático
- Verificación en verde reutilizada: `orquestar_evidencias.jsonl`, 2026-10-27T11:51:43, árbol `3f6c28b088`, código 0 (9 módulos: `test_ajustes_transversales`, `test_estado_agentes`, `test_cuota_supuesta`, `test_metricas`, `test_informe_agentes`, `test_deuda_menor`, `test_cierre_version`, `test_gateway_control`, `test_gateway_fondo`). No se relanza.
- `git diff --check HEAD`: limpio (solo avisos LF→CRLF de Git, sin errores de espacios).
- Sin secretos, sin manifiestos de dependencias tocados.

## Puntuaciones
| Criterio | Nota |
|---|---|
| Corrección | 9 |
| Seguridad | 10 |
| Conformidad | 9 |
| Calidad | 9 |
| Eficiencia | 10 |
| Documentación | 7 |
| **Media** | **9,0** |

## Comprobaciones por hallazgo
- **H-04**: `cierre_version.validar()` y `gateway.responder()` (`/parar`, `/lanzar`, altas) usan `motor.pid_vivo(root)`, que ignora PID inválidos o muertos. No queda ningún `(root / motor.PID).exists()` en el código del gateway. `/parar` con PID huérfano ya no deja una `orquestar.parar` pendiente, lo cual es coherente. «sin PID» pasa a «sin bucle vivo» en las dos SKILL.md.
- **H-05**: `verificar()` sigue escribiendo la `salida` en la evidencia y la quita de la fila de métricas. `registrar_fallo_suite` la sigue leyendo de la evidencia.
- **H-06**: el CHANGELOG 1.0.0 añade T-ADV-0023, T-ADV-0025, B-ADV-0010/14/16/17/19/21/22, y el bloque «Corregido» queda sin líneas en blanco intermedias.
- **H-09**: `reescribir_frontmatter` unifica la cabecera con el separador tolerante (`\n---[ \t]*(?:\n|$)`). En `registrar_fallo_suite` el cambio frente a `split('\n---\n')` solo amplía lo que se acepta: el `---` de apertura en la posición 0 no coincide, y una cabecera sin cierre sigue fallando igual (ValueError al desempaquetar).
- **H-12**: `esperar()` escribe `hora\nmotivo`. `leer_espera()` acepta el formato antiguo de una línea (el motivo por defecto es `sin cuota`) y una marca ilegible (`OSError`/`ValueError`, que incluye `UnicodeDecodeError`). `parte()` muestra el motivo e `informe_agentes()` reutiliza el lector. `--cuota-reset`/limpieza solo borran el fichero, así que el cambio de formato no les afecta.

## Hallazgos

### 🟡 MEDIA — `skills/orquestar/SKILL.md:118` queda falso tras H-12 · destino: `resolver` · para: desarrollador
Dice que `--estado` muestra «esperando cuota hasta…». Ahora `parte()` muestra «esperando (sin cuota) hasta HH:MM» o «esperando (fallo del arnés) hasta HH:MM». **Qué hacer:** cambiar la frase a «esperando (motivo) hasta…» y citar los dos motivos.

### 🟡 MEDIA — `skills/telegram_gateway/SKILL.md:20-21` contradice H-04 · destino: `resolver` · para: desarrollador
`/lanzar` y `/parar` siguen documentados como «Si existe `orquestar.pid`…», pero ahora deciden por el bucle vivo: con un PID huérfano, `/lanzar` arranca y `/parar` responde «ya está parado». **Qué hacer:** sustituir «existe `orquestar.pid`» por «hay un bucle vivo» en las dos viñetas. La línea 30 (contexto seguro del asistente) tiene la misma redacción, ya anterior al delta y con el código usando `pid_vivo`. Se puede alinear en el mismo cambio.

### 🔵 BAJA — Nombre del helper · destino: `descartar`
`reescribir_frontmatter` devuelve `(cabecera, cuerpo)` y deja que cada llamador vuelva a unirlos con `'\n---\n'`. El nombre sugiere que devuelve el texto ya reescrito. Es cosmético; el docstring lo aclara.
