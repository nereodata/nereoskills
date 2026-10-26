# Test Review: T-ADV-0021

- **Veredicto**: APROBADO
- **Media**: 9.5 / 10

## Puntuaciones

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Cobertura** | 9.5/10 | Cubre íntegramente CA-M-1..3, DEC-T21-01 y DEC-T21-02 (con A: Definición en SKIP por ser corrección técnica interna): salto a reserva en invocaciones consecutivas de `agente()`, límites de expiración y fechas futuras, reservas intermedias agotadas, conservación de la última configuración si todas están agotadas, titular sin reservas sin leer el JSONL, clave `(harness, model \| 'predeterminado')`, selección en `bucle()` respetando la conservación de la selección previa con `--harness` y `--cmd`, y exclusión de rebotes (`cuota_espera_s`, `sin_cuota`, `modelos: {}`) en `metricas.agregar()` preservando rechazos, tokens y coste. |
| **Aserciones** | 9.5/10 | Comprueban el comportamiento observable sobre `agente()`, `bucle()` y `metricas.agregar()`, incluyendo conteo exacto de lecturas de `consumo_cuotas`, persistencia en JSONL y compatibilidad con `modelos` ausente o `None`. Ninguna aserción se cumple por construcción. |
| **Rojo correcto** | 9.0/10 | Evidencia verificada en `docs/review/test_reviews/T-ADV-0021-red.md` (`adevv orquestar --verificar`): 8 fallos de aserción y 0 errores de sintaxis, importación o fixtures, más `py_compile` en código 0. |
| **Estabilidad** | 10/10 | Pruebas deterministas con directorio temporal aislado, reloj fijo (`ahora`), entorno limpio y doblaje completo de procesos externos y pasarela. |

## Reevaluación de hallazgos previos

- **[H-01] Expectativa en `test_bucle_omite_cuota_y_respeta_harness_forzado_y_cmd` con `--harness codex`**: **resuelto**. Sincronizados `DEC-T21-02` (`docs/plan/tasks/T-ADV-0021-salto-cuota-vigente-y-exclusion-rebotes-hades.md`, línea 38), `docs/design/T-ADV-0021-design.md` (línea 7) y el docstring de la prueba: con `--harness` o `--cmd` explícitos, `bucle()` conserva la selección anterior porque `comando()` solo aplica `con_modelo` cuando el arnés configurado coincide con el forzado (si difieren, ejecuta `predeterminado` en lugar de `titular`, sin clave fiable para filtrar por cuota). Por tanto, el subcaso `('codex', None, 'codex', 'titular')` espera correctamente `'titular'`.

## Hallazgos nuevos

Ninguno.
