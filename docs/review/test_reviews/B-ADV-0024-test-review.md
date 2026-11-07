**Veredicto:** APROBADO

# Revisión de pruebas: B-ADV-0024 (Ronda 2)

- **Artefactos auditados:**
  - `skills/telegram_gateway/test_reservas.py` (líneas 178–226)
  - `docs/review/test_reviews/B-ADV-0024-red.md`
- **Especificación de referencia:** `skills/telegram_gateway/features/telegram_gateway.feature` (escenarios `@B-ADV-0024`, líneas 153–171)
- **Revisor:** Hades (`/review-test`, modo orquestado)

## 1. Puntuaciones

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Cobertura** | 9/10 | Cubre íntegramente los dos escenarios `@B-ADV-0024`: clasificación como `supuesta` de 300 s, omisión a las `12:04:59` con respuesta de `claude/m2`, sondeo a las `12:05:00` con registro de `cuota_recuperada`, y aviso de créditos una sola vez por episodio al repetir el fallo tras los 300 s. |
| **Aserciones** | 9/10 | Comprueban valores reales y observables en métricas (`cuota_tipo`, `cuota_origen`, `cuota_espera_s`, `cuota_recuperada`), arnés invocado (`self.launch.call_args.args[2]`), recuento de lanzamientos (`self.launch.call_count == 2`) y no duplicación del aviso. Ninguna se cumple por construcción. |
| **Rojo correcto** | 9/10 | La evidencia en `B-ADV-0024-red.md` acredita que las 2 pruebas nuevas fallan limpiamente por aserción (`None != 'supuesta'` y falta del aviso `'Sin créditos en codex...'`). |
| **Estabilidad** | 10/10 | Uso aislado de directorio temporal, reloj fijo (`motor.ahora`) y mocks de proceso/ejecutable sin red ni estado global. |
| **Media** | **9.25/10** | Supera el umbral de aprobación (> 8) sin hallazgos 🔴 ni 🟠. |

## 2. Seguimiento de hallazgos anteriores

| ID | Severidad | Estado | Verificación |
| :--- | :---: | :---: | :--- |
| **H-01** | 🟠 ALTA | `resuelto` | En `test_creditos_aviso_unico_por_episodio_en_gateway` (líneas 220–226), el segundo mensaje se envía a las `12:05:00+00:00` (vencidos los 300 s), verifica que se realiza el segundo lanzamiento (`self.assertEqual(self.launch.call_count, 2)`) con fallo repetido de créditos y comprueba `self.aviso.assert_not_called()`. |
| **H-02** | 🔵 BAJA | `resuelto` | En `test_cuota_sin_hora_clasificada_como_supuesta_sondeo_y_recuperacion` (líneas 180–198), se configura y verifica la reserva `claude/m2` en correspondencia exacta con el escenario Gherkin. |

## 3. Hallazgos nuevos

Sin hallazgos nuevos.
